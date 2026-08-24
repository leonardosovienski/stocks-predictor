"""Testes dos ingestores: snapshots da lista B3 (anti-viés de sobrevivência
do universo) e parsers dos dados abertos da CVM (IPE/FRE)."""
import io
import pathlib
import sys
import zipfile

import pytest

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

import db
import ingest_cvm
import ingest_rj_universe as ing


@pytest.fixture()
def conn(tmp_path):
    return db.get_connection(tmp_path / "t.db")


# --- snapshots B3 ------------------------------------------------------------

def test_parse_b3_html_extracts_tickers():
    html = """<table><tr><th>Ticker</th><th>Empresa</th></tr>
    <tr><td>AMER3</td><td>Americanas S.A.</td></tr>
    <tr><td>OIBR3</td><td>Oi S.A.</td></tr>
    <tr><td>não é ticker</td><td>outra coisa</td></tr></table>"""
    rows = ing.parse_b3_rj_list_html(html)
    tickers = {r["ticker"] for r in rows}
    assert tickers == {"AMER3", "OIBR3"}
    assert all(len(r["company_name"]) > 3 for r in rows)


def test_snapshots_append_only_and_diff(conn):
    ing.save_snapshot(conn, [{"ticker": "AMER3", "company_name": "Americanas"}],
                      "2023-01-20", source="b3_live")
    ing.save_snapshot(conn, [{"ticker": "AMER3", "company_name": "Americanas"},
                             {"ticker": "OIBR3", "company_name": "Oi"}],
                      "2023-06-01", source="b3_live")
    # idempotente: regravar o mesmo retrato não duplica
    ing.save_snapshot(conn, [{"ticker": "AMER3", "company_name": "Americanas"}],
                      "2023-01-20", source="b3_live")
    n = conn.execute("SELECT COUNT(*) FROM rj_universe_snapshots").fetchone()[0]
    assert n == 3
    diff = ing.diff_snapshots(conn)
    assert diff["entries"] == [{"date": "2023-06-01", "ticker": "OIBR3"}]
    assert diff["exits"] == []


def test_propose_universe_rows_marks_pending_review(conn):
    ing.save_snapshot(conn, [{"ticker": "AMER3", "company_name": "Americanas"}],
                      "2023-01-20")
    conn.execute("INSERT INTO rj_universe(ticker, company_name,"
                 " rj_request_date, source) VALUES('OIBR3','Oi','2020-01-01','manual')")
    ing.save_snapshot(conn, [{"ticker": "AMER3", "company_name": "Americanas"},
                             {"ticker": "OIBR3", "company_name": "Oi"}],
                      "2023-06-01")
    props = {p["ticker"]: p for p in ing.propose_universe_rows(conn)}
    assert props["AMER3"]["status"] == "pendente_revisao"
    assert props["OIBR3"]["status"] == "ja_no_universo"
    assert props["AMER3"]["rj_request_date_candidate"] == "2023-01-20"


def test_ingest_fail_loud_on_empty_parse(conn, monkeypatch):
    # página sem nenhum ticker (layout mudou): NADA pode ser gravado
    monkeypatch.setattr(ing, "fetch_url",
                        lambda url, timeout=60: b"<html><body>nada</body></html>")
    with pytest.raises(ValueError, match="0 tickers"):
        ing.ingest_b3_snapshot(conn, "2026-08-24")
    n = conn.execute("SELECT COUNT(*) FROM rj_universe_snapshots").fetchone()[0]
    assert n == 0


# --- parsers CVM --------------------------------------------------------------

def _zip_of(name: str, content: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(name, content)
    return buf.getvalue()


def test_parse_ipe_known_at_is_delivery_date():
    csv_text = ("CNPJ_Companhia;Nome_Companhia;Data_Referencia;Data_Entrega;"
                "Categoria;Tipo;Assunto;Link_Download\n"
                "00.000.000/0001-91;AMERICANAS S.A.;2023-01-10;2023-01-11;"
                "Fato Relevante;Fato Relevante;Pedido de RJ;http://x\n")
    rows = ingest_cvm._open_zip_csv(_zip_of("ipe_cia_aberta_2023.csv", csv_text),
                                    "ipe_cia_aberta")
    events = ingest_cvm.parse_ipe_rows(rows)
    assert len(events) == 1
    assert events[0]["known_at"] == "2023-01-11"     # entrega, não referência
    assert events[0]["event_date"] == "2023-01-10"


def test_parse_ipe_fail_loud_without_delivery_column():
    csv_text = "Nome_Companhia;Assunto\nX S.A.;algo\n"
    rows = ingest_cvm._open_zip_csv(_zip_of("ipe_cia_aberta_2023.csv", csv_text),
                                    "ipe_cia_aberta")
    with pytest.raises(ValueError, match="data de entrega"):
        ingest_cvm.parse_ipe_rows(rows)


def test_parse_fre_float_brazilian_numbers():
    csv_text = ("Nome_Companhia;Data_Referencia;Quantidade_Total_Acoes;"
                "Quantidade_Acoes_Circulacao\n"
                "EMPRESA S.A.;31/12/2023;1.000.000,00;450.000,00\n")
    rows = ingest_cvm._open_zip_csv(
        _zip_of("fre_cia_aberta_distribuicao_capital_2023.csv", csv_text),
        "distribuicao_capital")
    out = ingest_cvm.parse_fre_float_rows(rows)
    assert out[0]["free_float"] == pytest.approx(450_000.0)
    assert out[0]["shares_outstanding"] == pytest.approx(1_000_000.0)


def test_build_ticker_map_marks_unmapped():
    m = ingest_cvm.build_ticker_map(["AMERICANAS S.A.", "OI S.A."],
                                    known={"oi_s.a.": "OIBR3"})
    assert m["oi_s.a."] == "OIBR3"
    assert m["americanas_s.a."] is None    # pendente de revisão humana
