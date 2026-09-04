"""M1 — parser posicional COTAHIST + gerador sintético + carga em prices_raw.

O golden test constrói a linha com posições EXPLÍCITAS do layout oficial da B3 (não as
constantes do parser) — quebra a circularidade: valida as fatias do parser contra o doc.
"""
import zipfile

import pytest

import cotahist
import db
import ingest_cotahist


def _golden_line():
    buf = [" "] * 245

    def put(s1, text):
        buf[s1 - 1:s1 - 1 + len(text)] = list(text)

    put(1, "01"); put(3, "20240102"); put(11, "02")
    put(13, "PETR4".ljust(12)); put(25, "010")
    put(57, "0000000002850")          # PREABE 28.50
    put(70, "0000000002900")          # PREMAX 29.00
    put(83, "0000000002800")          # PREMIN 28.00
    put(109, "0000000002880")         # PREULT 28.80
    put(153, "000000000000350000")    # QUATOT 350000
    put(171, "000000000001000000")    # VOLTOT 10000.00
    put(211, "0000001")               # FATCOT 1
    return "".join(buf)


def test_parse_golden_line_against_official_positions():
    rec = cotahist.parse_line(_golden_line())
    assert rec["date"] == "2024-01-02"
    assert rec["ticker"] == "PETR4"
    assert rec["bdi_code"] == "02"
    assert rec["market_type"] == "010"
    assert (rec["open"], rec["high"], rec["low"], rec["close"]) == (28.50, 29.00, 28.00, 28.80)
    assert rec["qty"] == 350000
    assert rec["volume_fin"] == 10000.00
    assert rec["quote_factor"] == 1


def test_parse_ignores_non_type01():
    assert cotahist.parse_line("99TRAILER") is None
    assert cotahist.parse_line("00HEADER") is None


def test_synthetic_round_trips_and_is_245_bytes():
    lines = cotahist.synthetic_cotahist(["PETR4", "VALE3"], ["20240102", "20240103", "20240104"], seed=1)
    assert len(lines) == 6 and all(len(l) == 245 for l in lines)
    recs = [cotahist.parse_line(l) for l in lines]
    assert all(r is not None for r in recs)
    assert {r["ticker"] for r in recs} == {"PETR4", "VALE3"}
    assert all(r["high"] >= r["close"] >= 0 and r["high"] >= r["low"] for r in recs)


def test_synthetic_deterministic_with_seed():
    assert (cotahist.synthetic_cotahist(["PETR4"], ["20240102"], seed=7)
            == cotahist.synthetic_cotahist(["PETR4"], ["20240102"], seed=7))


def test_load_into_prices_raw_idempotent(tmp_path):
    conn = db.get_connection(tmp_path / "stocks.db")
    lines = cotahist.synthetic_cotahist(["PETR4", "VALE3", "ITUB4"], ["20240102", "20240103"], seed=3)
    assert cotahist.load_prices(conn, lines, "COTAHIST_SYNTH.TXT") == 6
    assert conn.execute("SELECT COUNT(*) FROM prices_raw").fetchone()[0] == 6
    cotahist.load_prices(conn, lines, "COTAHIST_SYNTH.TXT")        # recarregar não duplica
    assert conn.execute("SELECT COUNT(*) FROM prices_raw").fetchone()[0] == 6
    conn.close()


def test_load_filtra_avista_lote_padrao(tmp_path):
    """Real: o COTAHIST traz opções/termo/fracionário; só ação à-vista lote-padrão
    (mkt=010,bdi=02) entra em prices_raw. O resto é descartado no ingest."""
    conn = db.get_connection(tmp_path / "s.db")
    avista = cotahist._pack("2024-01-02", "PETR4", "02", "010", 28.5, 29, 28, 28.8, 1000, 28800, 1)
    opcao = cotahist._pack("2024-01-02", "PETRA123", "78", "070", 1.2, 1.3, 1.1, 1.25, 500, 625, 1)
    fracionario = cotahist._pack("2024-01-02", "PETR4F", "96", "010", 28.5, 29, 28, 28.8, 3, 86, 1)
    assert cotahist.load_prices(conn, [avista, opcao, fracionario], "COTAHIST_A2024.TXT") == 1
    tickers = [r[0] for r in conn.execute("SELECT ticker FROM prices_raw")]
    assert tickers == ["PETR4"]
    # avista_only=False carrega tudo (escape hatch explícito)
    assert cotahist.load_prices(conn, [opcao], "OUTRO.TXT", avista_only=False) == 1
    conn.close()


def test_parse_cotahist_from_zip(tmp_path):
    """Caminho do arquivo real: TXT dentro de ZIP (latin-1) → prices_raw."""
    lines = cotahist.synthetic_cotahist(["PETR4"], ["20240102", "20240103"], seed=2)
    txt = tmp_path / "COTAHIST_A2024.TXT"
    txt.write_text("\n".join(lines), encoding="latin-1")
    zp = tmp_path / "COTAHIST_A2024.ZIP"
    with zipfile.ZipFile(zp, "w") as z:
        z.write(txt, arcname="COTAHIST_A2024.TXT")
    n = ingest_cotahist.parse_cotahist(str(zp), db_path=str(tmp_path / "s.db"))
    assert n == 2


def test_parse_cotahist_picks_cotahist_named_txt_over_companion(tmp_path):
    """Achado de varredura 2026-09-04: `next(... .TXT)` pegava o primeiro
    .TXT do zip por sorte — um README/layout .TXT companheiro (nome
    diferente) não podia ser escolhido no lugar do arquivo de cotação real."""
    lines = cotahist.synthetic_cotahist(["PETR4"], ["20240102"], seed=3)
    zp = tmp_path / "COTAHIST_A2024.ZIP"
    with zipfile.ZipFile(zp, "w") as z:
        z.writestr("AAA_LEIAME.TXT", "layout doc, não é cotação\n")   # ordena antes
        z.writestr("COTAHIST_A2024.TXT", "\n".join(lines))
    n = ingest_cotahist.parse_cotahist(str(zp), db_path=str(tmp_path / "s.db"))
    assert n == 1


def test_pick_cotahist_txt_fails_loud_on_ambiguous_names():
    with pytest.raises(ValueError, match="ambíguo"):
        ingest_cotahist._pick_cotahist_txt(["A.TXT", "B.TXT"])
    with pytest.raises(ValueError, match="ambíguo"):
        ingest_cotahist._pick_cotahist_txt(["COTAHIST_A.TXT", "COTAHIST_B.TXT"])


def test_parse_cotahist_fails_loud_on_zero_quote_lines(tmp_path):
    """Se o .TXT escolhido não tem NENHUM registro tipo 01 (arquivo errado,
    vazio, ou layout mudou), a carga não pode "suceder" retornando 0 em
    silêncio — achado de varredura 2026-09-04."""
    zp = tmp_path / "COTAHIST_A2024.ZIP"
    with zipfile.ZipFile(zp, "w") as z:
        z.writestr("COTAHIST_A2024.TXT", "99TRAILER\n")   # só trailler, 0 tipo 01
    with pytest.raises(ValueError, match="0 linhas"):
        ingest_cotahist.parse_cotahist(str(zp), db_path=str(tmp_path / "s.db"))
