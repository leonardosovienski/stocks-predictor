"""Testes dos ingestores: snapshots da lista B3 (anti-viés de sobrevivência
do universo) e parsers dos dados abertos da CVM (IPE/FRE)."""
import io
import pathlib
import sys
import zipfile

import pytest

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "stocks_predictor"))

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
    # latin-1: mesma codificação real dos arquivos da CVM que _open_zip_csv
    # espera — conteúdo acentuado (ex.: "ÚLTIMO") escrito como UTF-8 aqui
    # viraria mojibake na leitura e quebraria comparações por palavra-chave.
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(name, content.encode("latin-1"))
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


# --- parser DFP (fundamentos, H7) --------------------------------------------

_DFP_HEADER = "CNPJ_CIA;DENOM_CIA;ORDEM_EXERC;DT_REFER;CD_CONTA;DS_CONTA;VL_CONTA\n"


def test_parse_dfp_drops_penultimo_comparison_column():
    csv_text = (_DFP_HEADER +
                "00.000/0001-91;EMPRESA S.A.;ÚLTIMO;2023-12-31;1;Ativo Total;1000000\n"
                "00.000/0001-91;EMPRESA S.A.;PENÚLTIMO;2022-12-31;1;Ativo Total;900000\n")
    rows = ingest_cvm._open_zip_csv(
        _zip_of("dfp_cia_aberta_BPA_con_2023.csv", csv_text), "bpa_con")
    out = ingest_cvm.parse_dfp_statement_rows(rows, "BPA_con")
    assert len(out) == 1 and out[0]["ref_date"] == "2023-12-31"


def test_parse_dfp_fail_loud_without_value_column():
    csv_text = "CNPJ_CIA;DENOM_CIA;ORDEM_EXERC;DT_REFER;CD_CONTA;DS_CONTA\nx;y;ÚLTIMO;2023-12-31;1;Ativo Total\n"
    rows = ingest_cvm._open_zip_csv(
        _zip_of("dfp_cia_aberta_BPA_con_2023.csv", csv_text), "bpa_con")
    with pytest.raises(ValueError, match="value"):
        ingest_cvm.parse_dfp_statement_rows(rows, "BPA_con")


def test_compute_fundamentals_leverage_excludes_equity_from_passivo_total():
    # Ativo Total = Passivo Total (identidade contábil do plano CVM: CD "2"
    # já inclui o PL) — leverage tem que descontar o PL, não usar 1:1.
    bpa = [{"company": "EMPRESA S.A.", "ref_date": "2023-12-31",
            "account_code": "1", "account_desc": "Ativo Total", "value": 1_000_000.0}]
    bpp = [
        {"company": "EMPRESA S.A.", "ref_date": "2023-12-31",
         "account_code": "2", "account_desc": "Passivo Total", "value": 1_000_000.0},
        {"company": "EMPRESA S.A.", "ref_date": "2023-12-31",
         "account_code": "2.03", "account_desc": "Patrimônio Líquido Consolidado",
         "value": 400_000.0},
    ]
    dre = [{"company": "EMPRESA S.A.", "ref_date": "2023-12-31",
            "account_code": "3.11", "account_desc": "Lucro/Prejuízo Consolidado do Período",
            "value": 50_000.0}]
    out = ingest_cvm.compute_fundamentals(bpa, bpp, dre)
    assert len(out) == 1
    f = out[0]
    assert f["roe"] == pytest.approx(50_000.0 / 400_000.0)
    # leverage = (passivo_total - PL) / ativo = (1_000_000 - 400_000) / 1_000_000
    assert f["leverage"] == pytest.approx(0.6)


def test_compute_fundamentals_skips_company_missing_any_account():
    bpa = [{"company": "X S.A.", "ref_date": "2023-12-31",
            "account_code": "1", "account_desc": "Ativo Total", "value": 100.0}]
    bpp = []    # sem passivo/PL -> não entra
    dre = [{"company": "X S.A.", "ref_date": "2023-12-31",
            "account_code": "3.11", "account_desc": "Lucro/Prejuízo do Período",
            "value": 10.0}]
    assert ingest_cvm.compute_fundamentals(bpa, bpp, dre) == []


def test_compute_fundamentals_net_margin_independent_of_roe_leverage():
    # H12 (pré-registro 2026-09-04): empresa com receita+lucro resolvidos
    # mas SEM PL (roe/leverage indisponíveis) ainda ganha net_margin — os
    # dois grupos de contas são independentes, um não bloqueia o outro.
    bpa = [{"company": "X S.A.", "ref_date": "2023-12-31",
            "account_code": "1", "account_desc": "Ativo Total", "value": 100.0}]
    bpp = []    # sem passivo/PL -> roe/leverage ficam None
    dre = [
        {"company": "X S.A.", "ref_date": "2023-12-31",
         "account_code": "3.01", "account_desc": "Receita de Venda de Bens e/ou Serviços",
         "value": 500.0},
        {"company": "X S.A.", "ref_date": "2023-12-31",
         "account_code": "3.11", "account_desc": "Lucro/Prejuízo Consolidado do Período",
         "value": 50.0},
    ]
    out = ingest_cvm.compute_fundamentals(bpa, bpp, dre)
    assert len(out) == 1
    f = out[0]
    assert f["roe"] is None and f["leverage"] is None
    assert f["receita_liquida"] == pytest.approx(500.0)
    assert f["net_margin"] == pytest.approx(0.1)


def test_compute_fundamentals_net_margin_none_when_revenue_missing():
    # roe/leverage resolvem normalmente (as 4 contas originais presentes),
    # mas sem receita na DRE -> net_margin fica None, não quebra o resto.
    bpa = [{"company": "EMPRESA S.A.", "ref_date": "2023-12-31",
            "account_code": "1", "account_desc": "Ativo Total", "value": 1_000_000.0}]
    bpp = [
        {"company": "EMPRESA S.A.", "ref_date": "2023-12-31",
         "account_code": "2", "account_desc": "Passivo Total", "value": 1_000_000.0},
        {"company": "EMPRESA S.A.", "ref_date": "2023-12-31",
         "account_code": "2.03", "account_desc": "Patrimônio Líquido Consolidado",
         "value": 400_000.0},
    ]
    dre = [{"company": "EMPRESA S.A.", "ref_date": "2023-12-31",
            "account_code": "3.11", "account_desc": "Lucro/Prejuízo Consolidado do Período",
            "value": 50_000.0}]
    out = ingest_cvm.compute_fundamentals(bpa, bpp, dre)
    assert len(out) == 1
    f = out[0]
    assert f["roe"] == pytest.approx(50_000.0 / 400_000.0)
    assert f["receita_liquida"] is None and f["net_margin"] is None


def test_ingest_dfp_year_writes_fundamentals(conn, monkeypatch):
    bpa_csv = (_DFP_HEADER +
              "00.000/0001-91;EMPRESA S.A.;ÚLTIMO;2023-12-31;1;Ativo Total;1000000\n")
    bpp_csv = (_DFP_HEADER +
              "00.000/0001-91;EMPRESA S.A.;ÚLTIMO;2023-12-31;2;Passivo Total;1000000\n"
              "00.000/0001-91;EMPRESA S.A.;ÚLTIMO;2023-12-31;2.03;"
              "Patrimônio Líquido Consolidado;400000\n")
    dre_csv = (_DFP_HEADER +
              "00.000/0001-91;EMPRESA S.A.;ÚLTIMO;2023-12-31;3.11;"
              "Lucro/Prejuízo Consolidado do Período;50000\n")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("dfp_cia_aberta_BPA_con_2023.csv", bpa_csv.encode("latin-1"))
        zf.writestr("dfp_cia_aberta_BPP_con_2023.csv", bpp_csv.encode("latin-1"))
        zf.writestr("dfp_cia_aberta_DRE_con_2023.csv", dre_csv.encode("latin-1"))
    zbytes = buf.getvalue()
    monkeypatch.setattr(ingest_cvm, "download_zip", lambda url, timeout=300: zbytes)

    n = ingest_cvm.ingest_dfp_year(conn, 2023, ticker_of={"empresa_s.a.": "EMPR3"})
    assert n == 1
    row = conn.execute(
        "SELECT ticker, ref_date, roe, leverage, source FROM fundamentals").fetchone()
    assert row["ticker"] == "EMPR3" and row["ref_date"] == "2023-12-31"
    assert row["roe"] == pytest.approx(0.125)
    assert row["leverage"] == pytest.approx(0.6)
    assert row["source"] == "CVM DFP 2023"

    # re-executar o mesmo ano não duplica (UNIQUE ticker+ref_date+source)
    n2 = ingest_cvm.ingest_dfp_year(conn, 2023, ticker_of={"empresa_s.a.": "EMPR3"})
    assert n2 == 0
    assert conn.execute("SELECT COUNT(*) FROM fundamentals").fetchone()[0] == 1


def test_ingest_dfp_year_accepts_prefetched_zbytes_without_downloading(conn, monkeypatch):
    # ON+PN da mesma empresa: 2ª chamada reusa o mesmo zip já baixado, sem
    # rebaixar (achado de varredura 2026-09-04, tools/ingest_h7_real.py).
    bpa_csv = (_DFP_HEADER +
              "00.000/0001-91;EMPRESA S.A.;ÚLTIMO;2023-12-31;1;Ativo Total;1000000\n")
    bpp_csv = (_DFP_HEADER +
              "00.000/0001-91;EMPRESA S.A.;ÚLTIMO;2023-12-31;2;Passivo Total;1000000\n"
              "00.000/0001-91;EMPRESA S.A.;ÚLTIMO;2023-12-31;2.03;"
              "Patrimônio Líquido Consolidado;400000\n")
    dre_csv = (_DFP_HEADER +
              "00.000/0001-91;EMPRESA S.A.;ÚLTIMO;2023-12-31;3.11;"
              "Lucro/Prejuízo Consolidado do Período;50000\n")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("dfp_cia_aberta_BPA_con_2023.csv", bpa_csv.encode("latin-1"))
        zf.writestr("dfp_cia_aberta_BPP_con_2023.csv", bpp_csv.encode("latin-1"))
        zf.writestr("dfp_cia_aberta_DRE_con_2023.csv", dre_csv.encode("latin-1"))
    zbytes = buf.getvalue()

    def _fail_download(*a, **k):
        raise AssertionError("download_zip não deveria ser chamado quando zbytes é passado")
    monkeypatch.setattr(ingest_cvm, "download_zip", _fail_download)

    n = ingest_cvm.ingest_dfp_year(conn, 2023, ticker_of={"empresa_s.a.": "EMPR3"},
                                   zbytes=zbytes)
    assert n == 1
    n2 = ingest_cvm.ingest_dfp_year(conn, 2023, ticker_of={"empresa_s.a.": "EMPR4"},
                                    zbytes=zbytes)
    assert n2 == 1
    assert conn.execute("SELECT COUNT(*) FROM fundamentals").fetchone()[0] == 2


def test_ingest_dfp_year_backfills_revenue_on_preexisting_row(conn, monkeypatch):
    # Achado H12/H13 (2026-09-04): uma linha já ingerida ANTES da migração
    # 0010_fundamentals_revenue (receita_liquida/net_margin NULL) precisa
    # ganhar esses valores ao reingerir o mesmo ano — INSERT OR IGNORE puro
    # nunca faria isso (a linha já existe, seria ignorada pra sempre).
    conn.execute(
        "INSERT INTO fundamentals(ticker, ref_date, ativo_total, passivo_total,"
        " patrimonio_liquido, lucro_liquido, roe, leverage, source)"
        " VALUES (?,?,?,?,?,?,?,?,?)",
        ("EMPR3", "2023-12-31", 1_000_000.0, 1_000_000.0, 400_000.0, 50_000.0,
         0.125, 0.6, "CVM DFP 2023"))
    conn.commit()

    bpa_csv = (_DFP_HEADER +
              "00.000/0001-91;EMPRESA S.A.;ÚLTIMO;2023-12-31;1;Ativo Total;1000000\n")
    bpp_csv = (_DFP_HEADER +
              "00.000/0001-91;EMPRESA S.A.;ÚLTIMO;2023-12-31;2;Passivo Total;1000000\n"
              "00.000/0001-91;EMPRESA S.A.;ÚLTIMO;2023-12-31;2.03;"
              "Patrimônio Líquido Consolidado;400000\n")
    dre_csv = (_DFP_HEADER +
              "00.000/0001-91;EMPRESA S.A.;ÚLTIMO;2023-12-31;3.01;"
              "Receita de Venda de Bens e/ou Servicos;500000\n"
              "00.000/0001-91;EMPRESA S.A.;ÚLTIMO;2023-12-31;3.11;"
              "Lucro/Prejuízo Consolidado do Período;50000\n")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("dfp_cia_aberta_BPA_con_2023.csv", bpa_csv.encode("latin-1"))
        zf.writestr("dfp_cia_aberta_BPP_con_2023.csv", bpp_csv.encode("latin-1"))
        zf.writestr("dfp_cia_aberta_DRE_con_2023.csv", dre_csv.encode("latin-1"))
    zbytes = buf.getvalue()
    monkeypatch.setattr(ingest_cvm, "download_zip", lambda url, timeout=300: zbytes)

    n = ingest_cvm.ingest_dfp_year(conn, 2023, ticker_of={"empresa_s.a.": "EMPR3"})
    assert n == 1   # backfill conta como mudança
    row = conn.execute(
        "SELECT roe, leverage, receita_liquida, net_margin FROM fundamentals"
        " WHERE ticker='EMPR3'").fetchone()
    assert row["roe"] == pytest.approx(0.125) and row["leverage"] == pytest.approx(0.6)
    assert row["receita_liquida"] == pytest.approx(500_000.0)
    assert row["net_margin"] == pytest.approx(0.1)
    assert conn.execute("SELECT COUNT(*) FROM fundamentals").fetchone()[0] == 1  # sem duplicar

    # rodar de novo não recontabiliza (já preenchido, idempotência preservada)
    n2 = ingest_cvm.ingest_dfp_year(conn, 2023, ticker_of={"empresa_s.a.": "EMPR3"})
    assert n2 == 0


def test_ingest_dfp_year_skips_unmapped_company(conn, monkeypatch):
    bpa_csv = (_DFP_HEADER +
              "00.000/0001-91;SEM MAPA S.A.;ÚLTIMO;2023-12-31;1;Ativo Total;1000000\n")
    bpp_csv = (_DFP_HEADER +
              "00.000/0001-91;SEM MAPA S.A.;ÚLTIMO;2023-12-31;2;Passivo Total;1000000\n"
              "00.000/0001-91;SEM MAPA S.A.;ÚLTIMO;2023-12-31;2.03;"
              "Patrimônio Líquido Consolidado;400000\n")
    dre_csv = (_DFP_HEADER +
              "00.000/0001-91;SEM MAPA S.A.;ÚLTIMO;2023-12-31;3.11;"
              "Lucro/Prejuízo Consolidado do Período;50000\n")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("dfp_cia_aberta_BPA_con_2023.csv", bpa_csv.encode("latin-1"))
        zf.writestr("dfp_cia_aberta_BPP_con_2023.csv", bpp_csv.encode("latin-1"))
        zf.writestr("dfp_cia_aberta_DRE_con_2023.csv", dre_csv.encode("latin-1"))
    zbytes = buf.getvalue()
    monkeypatch.setattr(ingest_cvm, "download_zip", lambda url, timeout=300: zbytes)

    n = ingest_cvm.ingest_dfp_year(conn, 2023, ticker_of={})   # mapa vazio
    assert n == 0
    assert conn.execute("SELECT COUNT(*) FROM fundamentals").fetchone()[0] == 0


# --- parser FRE dividendos/capital (H11, retorno total) -----------------------

def test_to_float_requires_explicit_format():
    with pytest.raises(ValueError, match="fmt"):
        ingest_cvm._to_float("1.234", fmt="xx")


def test_to_float_en_is_plain_decimal_point():
    # fmt="en": ponto é decimal, NUNCA milhar — "450.000" é 450.0, não 450000.
    assert ingest_cvm._to_float("450.000", fmt="en") == pytest.approx(450.0)
    assert ingest_cvm._to_float("1234.56", fmt="en") == pytest.approx(1234.56)
    assert ingest_cvm._to_float("", fmt="en") is None
    assert ingest_cvm._to_float("n/a", fmt="en") is None


def test_to_float_br_is_thousands_dot_decimal_comma():
    # fmt="br": mesma convenção de parse_fre_float_rows — "450.000,00" é
    # 450000.0. Nunca confundível com fmt="en" porque o chamador escolhe,
    # não uma tentativa-e-erro que possa interpretar "450.000" errado.
    assert ingest_cvm._to_float("450.000,00", fmt="br") == pytest.approx(450_000.0)
    assert ingest_cvm._to_float("1.234.567", fmt="br") == pytest.approx(1_234_567.0)
    assert ingest_cvm._to_float("", fmt="br") is None
    assert ingest_cvm._to_float("n/a", fmt="br") is None


_FRE_DIV_HEADER = ("CNPJ_Companhia;Nome_Companhia;Data_Pagamento_Dividendo;"
                   "Categoria;Montante\n")


def test_parse_fre_dividend_rows_sums_by_pay_date_downstream():
    csv_text = (_FRE_DIV_HEADER +
               "00.000/0001-91;EMPRESA S.A.;2023-04-10;Dividendo Obrigatório;1234.56\n"
               "00.000/0001-91;EMPRESA S.A.;2023-04-10;Outros;100.00\n")
    rows = ingest_cvm._open_zip_csv(
        _zip_of("fre_cia_aberta_distribuicao_dividendos_classe_acao_2023.csv", csv_text),
        "distribuicao_dividendos_classe_acao")
    out = ingest_cvm.parse_fre_dividend_rows(rows)
    assert len(out) == 2
    assert {r["amount"] for r in out} == {1234.56, 100.0}
    assert all(r["cnpj"] == "00.000/0001-91" and r["pay_date"] == "2023-04-10" for r in out)


def test_parse_fre_dividend_rows_drops_rows_without_pay_date():
    csv_text = (_FRE_DIV_HEADER +
               "00.000/0001-91;EMPRESA S.A.;;Dividendo Obrigatório;1234.56\n")
    rows = ingest_cvm._open_zip_csv(
        _zip_of("fre_cia_aberta_distribuicao_dividendos_classe_acao_2023.csv", csv_text),
        "distribuicao_dividendos_classe_acao")
    assert ingest_cvm.parse_fre_dividend_rows(rows) == []


def test_parse_fre_dividend_rows_fail_loud_without_amount_column():
    csv_text = "CNPJ_Companhia;Nome_Companhia;Data_Pagamento_Dividendo\nx;y;2023-01-01\n"
    rows = ingest_cvm._open_zip_csv(
        _zip_of("fre_cia_aberta_distribuicao_dividendos_classe_acao_2023.csv", csv_text),
        "distribuicao_dividendos_classe_acao")
    with pytest.raises(ValueError, match="amount"):
        ingest_cvm.parse_fre_dividend_rows(rows)


_FRE_CAPITAL_HEADER = ("CNPJ_Companhia;Data_Referencia;"
                       "Quantidade_Total_Acoes_Circulacao\n")


def test_open_fre_distribuicao_capital_main_picks_non_classe_acao_file():
    # o zip real tem os dois arquivos com "distribuicao_capital" no nome —
    # `_open_fre_distribuicao_capital_main` tem que escolher só o principal.
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("fre_cia_aberta_distribuicao_capital_2023.csv",
                   (_FRE_CAPITAL_HEADER +
                    "00.000/0001-91;2023-12-31;450.000,00\n").encode("latin-1"))
        zf.writestr("fre_cia_aberta_distribuicao_capital_classe_acao_2023.csv",
                   "Nome_Classe;Quantidade\nON;999999\n".encode("latin-1"))
    rows = ingest_cvm._open_fre_distribuicao_capital_main(buf.getvalue())
    out = ingest_cvm.parse_fre_capital_total_rows(rows)
    assert out == {"00.000/0001-91": pytest.approx(450_000.0)}


def test_parse_fre_capital_total_rows_keeps_latest_ref_date_per_cnpj():
    csv_text = (_FRE_CAPITAL_HEADER +
               "00.000/0001-91;2022-12-31;100.000,00\n"
               "00.000/0001-91;2023-12-31;450.000,00\n")
    rows = ingest_cvm._open_zip_csv(
        _zip_of("fre_cia_aberta_distribuicao_capital_2023.csv", csv_text),
        "distribuicao_capital")
    out = ingest_cvm.parse_fre_capital_total_rows(rows)
    assert out == {"00.000/0001-91": pytest.approx(450_000.0)}


def _fre_year_zip(div_csv: str, capital_csv: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("fre_cia_aberta_distribuicao_dividendos_classe_acao_2023.csv",
                   div_csv.encode("latin-1"))
        zf.writestr("fre_cia_aberta_distribuicao_capital_2023.csv",
                   capital_csv.encode("latin-1"))
    return buf.getvalue()


def test_ingest_fre_dividends_year_writes_value_per_share(conn, monkeypatch):
    div_csv = (_FRE_DIV_HEADER +
              "00.000/0001-91;EMPRESA S.A.;2023-04-10;Dividendo Obrigatório;450000.00\n")
    capital_csv = (_FRE_CAPITAL_HEADER + "00.000/0001-91;2023-12-31;900.000,00\n")
    zbytes = _fre_year_zip(div_csv, capital_csv)
    monkeypatch.setattr(ingest_cvm, "download_zip", lambda url, timeout=300: zbytes)

    n = ingest_cvm.ingest_fre_dividends_year(
        conn, 2023, ticker_of={"empresa_s.a.": "EMPR3"})
    assert n == 1
    row = conn.execute(
        "SELECT ticker, ex_date, value_per_share, source FROM dividends").fetchone()
    assert row["ticker"] == "EMPR3" and row["ex_date"] == "2023-04-10"
    assert row["value_per_share"] == pytest.approx(450_000.0 / 900_000.0)
    assert row["source"] == "CVM FRE 2023"

    # re-executar não duplica (UNIQUE ticker+ex_date+source)
    n2 = ingest_cvm.ingest_fre_dividends_year(
        conn, 2023, ticker_of={"empresa_s.a.": "EMPR3"})
    assert n2 == 0
    assert conn.execute("SELECT COUNT(*) FROM dividends").fetchone()[0] == 1


def test_ingest_fre_dividends_year_skips_company_without_reliable_share_total(conn, monkeypatch):
    # sem total de ações confiável (companhia ausente do FRE de capital):
    # sem dado inventado — nada é gravado, não um valor-por-ação chutado.
    div_csv = (_FRE_DIV_HEADER +
              "00.000/0001-91;EMPRESA S.A.;2023-04-10;Dividendo Obrigatório;450000.00\n")
    capital_csv = _FRE_CAPITAL_HEADER    # nenhuma companhia
    zbytes = _fre_year_zip(div_csv, capital_csv)
    monkeypatch.setattr(ingest_cvm, "download_zip", lambda url, timeout=300: zbytes)

    n = ingest_cvm.ingest_fre_dividends_year(
        conn, 2023, ticker_of={"empresa_s.a.": "EMPR3"})
    assert n == 0
    assert conn.execute("SELECT COUNT(*) FROM dividends").fetchone()[0] == 0


def test_ingest_fre_dividends_year_skips_unmapped_company(conn, monkeypatch):
    div_csv = (_FRE_DIV_HEADER +
              "00.000/0001-91;SEM MAPA S.A.;2023-04-10;Dividendo Obrigatório;450000.00\n")
    capital_csv = (_FRE_CAPITAL_HEADER + "00.000/0001-91;2023-12-31;900.000,00\n")
    zbytes = _fre_year_zip(div_csv, capital_csv)
    monkeypatch.setattr(ingest_cvm, "download_zip", lambda url, timeout=300: zbytes)

    n = ingest_cvm.ingest_fre_dividends_year(conn, 2023, ticker_of={})
    assert n == 0
    assert conn.execute("SELECT COUNT(*) FROM dividends").fetchone()[0] == 0
