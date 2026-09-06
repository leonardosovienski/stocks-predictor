"""H17 — accruals / qualidade do lucro (pré-registro 2026-09-04, Sloan 1996).

Mesma maquinaria de H7/H9/H12/H13 (universo/custos/pareamento/pedágio/embargo
de divulgação); o que é NOVO é a FONTE: a DFC-MI consolidada, primeira
demonstração ingerida desde o M2. Direção pré-registrada: quintil INFERIOR
(lucro lastreado em caixa).
"""
import datetime

import backtest
import cotahist
import db
import factor
import ingest_cvm
import trials_gate


def _dates(n, start=(2016, 7, 1)):
    base = datetime.date(*start)
    return [(base + datetime.timedelta(days=i)).strftime("%Y%m%d") for i in range(n)]


def _synthetic_conn(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    tickers = [f"T{c}{c}{c}3" for c in "ABCDEFGHIJKL"]
    cotahist.load_prices(conn, cotahist.synthetic_cotahist(tickers, _dates(900), seed=11),
                         "COTAHIST_SYNTH.TXT")
    # accruals sintéticos, ref_date bem antes da janela de teste para que o
    # embargo de 90 dias já tenha vencido em qualquer rebalance de 2018+.
    for i, t in enumerate(tickers):
        ativo, lucro = 1000.0, 100.0
        fco = 120.0 - 5.0 * i          # accrual crescente com i
        conn.execute(
            "INSERT INTO fundamentals(ticker, ref_date, ativo_total, lucro_liquido,"
            " fluxo_caixa_operacional, accruals, source) VALUES (?,?,?,?,?,?,?)",
            (t, "2016-12-31", ativo, lucro, fco, (lucro - fco) / ativo,
             "CVM DFP 2016 (sintético)"))
    conn.commit()
    return conn


def test_run_h17_smoke(tmp_path, capsys):
    from config import load_config
    cfg = load_config()
    cfg["bootstrap"] = {"n_boot": 300, "block_length": 21, "confidence": 0.95, "seed": 42}

    conn = _synthetic_conn(tmp_path)
    tp = tmp_path / "trials.json"
    trials_gate.attest(cfg, trials_path=tp)
    trials_gate.register_baseline_trials(cfg, trials_path=tp)
    v = backtest.run_h17(cfg, conn, trials_path=tp)
    conn.close()

    assert "H17:" in capsys.readouterr().out
    assert v["n"] > 60 and v.get("n_trials") == 3
    assert v.get("dsr") is not None and 0.0 <= v["dsr"] <= 1.0


def test_h17_frozen_config_hash_golden():
    """Mexeu num param [H17-FROZEN] -> quebra alto AQUI (pré-registro 2026-09-04).

    Lacre RE-EMITIDO em 2026-09-06 (`aece696b814c0fd9` -> `e6cf9bd7454750c3`):
    entrou `known_at_policy: observed`. Legítimo porque a H17 NUNCA rodou —
    revisão de pré-registro, não mover a trave. Ver HANDOFF."""
    from config import h17_frozen_config_hash, load_config
    assert h17_frozen_config_hash(load_config()) == "e6cf9bd7454750c3"


def test_h17_frozen_hash_ignores_operational_params():
    from config import h17_frozen_config_hash, load_config
    cfg = load_config()
    base = h17_frozen_config_hash(cfg)
    cfg["data"]["db_path"] = "outro.db"
    cfg["bootstrap"]["seed"] = 999
    assert h17_frozen_config_hash(cfg) == base
    cfg["h17_factor"]["disclosure_embargo_days"] = 5
    assert h17_frozen_config_hash(cfg) != base


def test_h17_direction_is_bottom_quintile():
    """A direção é PRÉ-REGISTRADA (accrual baixo = lucro em caixa). Se alguém
    trocar para "top" depois de ver um resultado ruim, quebra aqui."""
    from config import load_config
    assert load_config()["h17_portfolio"]["quantile"] == "bottom_quintile"


def test_accruals_signals_embargo_blocks_early_asof(tmp_path):
    """Mesmo ponto central de H7/H9/H12: sem o embargo, `ref_date` sozinho
    vazaria dado contábil antes da publicação real."""
    conn = db.get_connection(tmp_path / "s.db")
    conn.execute(
        "INSERT INTO fundamentals(ticker, ref_date, ativo_total, lucro_liquido,"
        " fluxo_caixa_operacional, accruals, source) VALUES (?,?,?,?,?,?,?)",
        ("AAAA3", "2020-12-31", 1000.0, 100.0, 60.0, 0.04, "CVM DFP 2020"))
    conn.commit()

    assert "AAAA3" not in factor.accruals_signals(
        conn, ["AAAA3"], "2021-03-01", disclosure_embargo_days=90)
    assert factor.accruals_signals(
        conn, ["AAAA3"], "2021-04-01", disclosure_embargo_days=90)["AAAA3"] == 0.04


def test_compute_fundamentals_derives_accruals_from_dfc():
    """(lucro − FCO)/ativo, com a conta 6.01 vinda da DFC-MI."""
    def row(code, desc, value, statement):
        return {"company": "CIA X", "cnpj": "1", "ref_date": "2020-12-31",
                "account_code": code, "account_desc": desc, "value": value,
                "statement": statement}
    bpa = [row("1", "Ativo Total", 1000.0, "BPA_con")]
    bpp = [row("2", "Passivo Total", 1000.0, "BPP_con"),
           row("2.03", "Patrimonio Liquido Consolidado", 400.0, "BPP_con")]
    dre = [row("3.11", "Lucro do Periodo", 100.0, "DRE_con")]
    dfc = [row("6.01", "Caixa Liquido Atividades Operacionais", 70.0, "DFC_MI_con")]

    out = ingest_cvm.compute_fundamentals(bpa, bpp, dre, dfc)
    assert len(out) == 1
    assert out[0]["fluxo_caixa_operacional"] == 70.0
    assert abs(out[0]["accruals"] - 0.03) < 1e-12     # (100-70)/1000


def test_compute_fundamentals_without_dfc_keeps_accruals_none():
    """Chamador antigo (sem DFC) segue funcionando — H7/H9/H12/H13 intocadas."""
    def row(code, desc, value, statement):
        return {"company": "CIA X", "cnpj": "1", "ref_date": "2020-12-31",
                "account_code": code, "account_desc": desc, "value": value,
                "statement": statement}
    bpa = [row("1", "Ativo Total", 1000.0, "BPA_con")]
    bpp = [row("2", "Passivo Total", 1000.0, "BPP_con"),
           row("2.03", "Patrimonio Liquido Consolidado", 400.0, "BPP_con")]
    dre = [row("3.11", "Lucro do Periodo", 100.0, "DRE_con")]

    out = ingest_cvm.compute_fundamentals(bpa, bpp, dre)
    assert len(out) == 1
    assert out[0]["accruals"] is None
    assert out[0]["fluxo_caixa_operacional"] is None
    assert out[0]["roe"] == 0.25          # 100/400, inalterado


def test_accruals_none_when_ativo_total_non_positive():
    """Denominador inválido -> None, nunca ratio fabricado."""
    def row(code, desc, value, statement):
        return {"company": "CIA X", "cnpj": "1", "ref_date": "2020-12-31",
                "account_code": code, "account_desc": desc, "value": value,
                "statement": statement}
    bpa = [row("1", "Ativo Total", 0.0, "BPA_con")]
    bpp = [row("2", "Passivo Total", 0.0, "BPP_con"),
           row("2.03", "Patrimonio Liquido Consolidado", 0.0, "BPP_con")]
    dre = [row("3.11", "Lucro do Periodo", 100.0, "DRE_con")]
    dfc = [row("6.01", "Caixa Liquido Atividades Operacionais", 70.0, "DFC_MI_con")]

    out = ingest_cvm.compute_fundamentals(bpa, bpp, dre, dfc)
    assert out[0]["accruals"] is None
