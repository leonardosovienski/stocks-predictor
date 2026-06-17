"""M1 — parser posicional COTAHIST + gerador sintético + carga em prices_raw.

O golden test constrói a linha com posições EXPLÍCITAS do layout oficial da B3 (não as
constantes do parser) — quebra a circularidade: valida as fatias do parser contra o doc.
"""
import zipfile

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
