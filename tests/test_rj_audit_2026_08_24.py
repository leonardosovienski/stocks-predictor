"""Testes de regressão da auditoria 2026-08-24 (branch audit/2026-08-24-fixes).

Cada teste aqui reproduz um bug confirmado da auditoria no código do domínio
RJ e trava a correção — sem tocar valores [RJ-FROZEN], as 8 famílias
pré-registradas ou o FDR BH alpha=0.10.
"""
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

import rj_families as families
import rj_families_next as nextgen


# --- Bug A: fallback `known_at or event_date` = lookahead informacional -----

def test_ownership_event_without_known_at_is_not_eligible():
    """Protocolo §8/§10: event_date NÃO é known_at. Evento sem known_at
    válido não pode contar como sinal — antes da correção contava (lookahead)."""
    events = [{"event_type": "investidor_5pct", "event_date": "2020-05-10",
               "known_at": None}]
    assert families.ownership(events, "2020-05-20") == 0
    events2 = [{"event_type": "investidor_5pct", "event_date": "2020-05-10"}]
    assert families.ownership(events2, "2020-05-20") == 0
    # known_at válido dentro da janela continua sinalizando
    ok = [{"event_type": "investidor_5pct", "event_date": "2020-05-10",
           "known_at": "2020-05-12"}]
    assert families.ownership(ok, "2020-05-20") == 1


def test_info_trigger_event_without_known_at_is_not_eligible():
    events = [{"event_type": "fato_relevante", "event_date": "2020-05-10",
               "known_at": None}]
    assert families.info_trigger(events, "2020-05-15") == 0
    ok = [{"event_type": "fato_relevante", "event_date": "2020-05-10",
           "known_at": "2020-05-11"}]
    assert families.info_trigger(ok, "2020-05-15") == 1


def test_equity_issuance_event_without_known_at_is_not_eligible():
    events = [{"event_type": "aumento_capital", "event_date": "2020-05-10",
               "known_at": None}]
    assert nextgen.equity_issuance(events, "2020-05-20") == 0


def test_ownership_invalid_trough_date_is_unavailable_not_zero():
    """Fundo inválido = dado INDISPONÍVEL (None), nunca 0 — zero seria
    'sabemos que não houve evento', que é exatamente o que não sabemos."""
    assert families.ownership([], "nao-e-data") is None
    assert families.info_trigger([], "2020-13-99") is None
    assert nextgen.equity_issuance([], "lixo") is None


# --- Bug B: fila de revisão humana (approved_by IS NOT NULL, fail-closed) ---

import db
import ingest_cvm
import rj_pipeline as pipeline


def _universe_row(conn, ticker, approved):
    conn.execute(
        "INSERT INTO rj_universe(ticker, company_name, rj_request_date, source,"
        " approved_by) VALUES(?,?,?,?,?)",
        (ticker, f"{ticker} SA", "2020-01-10", "synthetic", approved))


def test_pipeline_ignores_universe_rows_pending_approval(tmp_path):
    """Regra 5 (fila de revisão humana): linha de rj_universe sem approved_by
    NÃO pode entrar na análise — fail-closed, não fail-open."""
    conn = db.get_connection(tmp_path / "t.db")
    _universe_row(conn, "PEND3", approved=None)
    _universe_row(conn, "APRV3", approved="revisor")
    tickers = {r[0] for r in conn.execute(
        "SELECT ticker FROM rj_universe WHERE approved_by IS NOT NULL")}
    assert tickers == {"APRV3"}
    built = pipeline.build_episodes(conn, _minimal_cfg(), "2020-02-01")
    seen = {ep["ticker"] for ep in built["episodes"]} | set(built["excluded"])
    assert "PEND3" not in seen


def test_pipeline_ignores_events_pending_approval(tmp_path):
    conn = db.get_connection(tmp_path / "t.db")
    _universe_row(conn, "APRV3", approved="revisor")
    conn.execute(
        "INSERT INTO rj_events(ticker, event_date, known_at, event_type,"
        " source, approved_by) VALUES(?,?,?,?,?,?)",
        ("APRV3", "2020-01-12", "2020-01-12", "fato_relevante", "cvm", None))
    conn.commit()
    events = pipeline._load_events(conn, "APRV3")
    assert events == []


def _minimal_cfg():
    return {"rally": {"threshold_pct": 0.50,
                      "primary_window_trading_days": 60,
                      "secondary_window_trading_days": 252,
                      "point_in_time_backward_lookback_days": 40}}


def test_ingest_cvm_inserts_events_pending_approval(tmp_path, monkeypatch):
    """Ingest CVM grava com approved_by NULL (pendente de revisão) — nunca
    auto-aprovado."""
    conn = db.get_connection(tmp_path / "t.db")
    _universe_row(conn, "AMER3", approved="revisor")
    csv_text = ("CNPJ_Companhia;Nome_Companhia;Data_Referencia;Data_Entrega;"
                "Categoria;Tipo;Assunto;Link_Download\n"
                "00.000.000/0001-91;AMERICANAS S.A.;2023-01-10;2023-01-11;"
                "Fato Relevante;Fato Relevante;Pedido de RJ;http://x\n")
    monkeypatch.setattr(ingest_cvm, "download_zip",
                        lambda url, timeout=300: _zip(csv_text))
    n = ingest_cvm.ingest_ipe_year(
        conn, 2023, companies={"americanas_s.a."},
        ticker_of={"americanas_s.a.": "AMER3"})
    assert n == 1
    row = conn.execute(
        "SELECT approved_by FROM rj_events WHERE ticker='AMER3'").fetchone()
    assert row[0] is None


import io
import zipfile


def _zip(csv_text: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("ipe_cia_aberta_2023.csv", csv_text)
    return buf.getvalue()


# --- Bug C: parse vazio / zip ambíguo / datas malformadas (CVM) --------------

_IPE_HEADER = ("CNPJ_Companhia;Nome_Companhia;Data_Referencia;Data_Entrega;"
               "Categoria;Tipo;Assunto;Link_Download\n")


def test_parse_ipe_empty_csv_raises():
    """Regra 4: CSV vazio (só cabeçalho, ou nem isso) não pode retornar 0
    eventos silenciosamente — é falha de layout/fonte, não 'sem fatos'."""
    with pytest.raises(ValueError, match="0 linhas"):
        ingest_cvm.parse_ipe_rows([_IPE_HEADER.strip().split(";")])
    with pytest.raises(ValueError, match="0 linhas"):
        ingest_cvm.parse_ipe_rows(iter([]))


def test_parse_ipe_company_filter_emptying_everything_raises():
    """Filtro de companhias que esvazia TUDO: fail-loud (provável erro de
    mapeamento de nomes), não zero silencioso."""
    rows = [ _IPE_HEADER.strip().split(";"),
             ["00", "AMERICANAS S.A.", "2023-01-10", "2023-01-11",
              "Fato Relevante", "Fato Relevante", "RJ", "http://x"]]
    with pytest.raises(ValueError, match="filtro de companhias"):
        ingest_cvm.parse_ipe_rows(rows, companies={"outra_s.a."})


def test_parse_ipe_malformed_dates_raise_with_count():
    rows = [_IPE_HEADER.strip().split(";"),
            ["00", "A S.A.", "2023-01-10", "11/01/2023", "F", "F", "s", "l"],
            ["00", "B S.A.", "2023-01-10", "2023-13-40", "F", "F", "s", "l"]]
    with pytest.raises(ValueError, match="2"):
        ingest_cvm.parse_ipe_rows(rows)


def test_open_zip_csv_ambiguous_match_raises():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("ipe_cia_aberta_2023.csv", "a;b\n1;2\n")
        zf.writestr("ipe_cia_aberta_2023_extra.csv", "a;b\n3;4\n")
    with pytest.raises(ValueError, match="2 CSVs"):
        list(ingest_cvm._open_zip_csv(buf.getvalue(), "ipe_cia_aberta"))
