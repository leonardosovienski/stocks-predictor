"""H12 — fator de qualidade, margem líquida isolada (pré-registro 2026-09-04).

Mesma maquinaria de H7/H9/H10 (universo/custos/pareamento/pedágio/embargo de
divulgação); o sinal é margem líquida (quintil SUPERIOR) em vez de ROE ou
alavancagem. 3ª variável contábil independente da DFP — receita já vinha na
DRE parseada desde a H7, só não era extraída (sem ingestão nova).
"""
import datetime

import backtest
import cotahist
import db
import factor
import trials_gate


def _dates(n, start=(2016, 7, 1)):
    base = datetime.date(*start)
    return [(base + datetime.timedelta(days=i)).strftime("%Y%m%d") for i in range(n)]


def _synthetic_conn(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    tickers = [f"T{c}{c}{c}3" for c in "ABCDEFGHIJKL"]
    cotahist.load_prices(conn, cotahist.synthetic_cotahist(tickers, _dates(900), seed=11),
                         "COTAHIST_SYNTH.TXT")
    # margem sintética, um valor por ticker, ref_date bem antes da janela de
    # teste (2016-12-31) para que o embargo de 90 dias já tenha vencido em
    # qualquer rebalance de 2018+ usado pelo smoke.
    for i, t in enumerate(tickers):
        margin = 0.05 + 0.01 * i
        receita = 1000.0
        lucro = receita * margin
        conn.execute(
            "INSERT INTO fundamentals(ticker, ref_date, receita_liquida,"
            " lucro_liquido, net_margin, source) VALUES (?,?,?,?,?,?)",
            (t, "2016-12-31", receita, lucro, margin, "CVM DFP 2016 (sintético)"))
    conn.commit()
    return conn


def test_run_h12_smoke(tmp_path, capsys):
    from config import load_config
    cfg = load_config()
    cfg["bootstrap"] = {"n_boot": 300, "block_length": 21, "confidence": 0.95, "seed": 42}

    conn = _synthetic_conn(tmp_path)
    tp = tmp_path / "trials.json"
    trials_gate.attest(cfg, trials_path=tp)
    trials_gate.register_baseline_trials(cfg, trials_path=tp)     # h1 + h2 no tmp
    v = backtest.run_h12(cfg, conn, trials_path=tp)
    conn.close()

    assert "H12:" in capsys.readouterr().out
    assert v["n"] > 60 and v.get("n_trials") == 3     # h1 + h2 + h12 neste registro tmp
    assert v.get("dsr") is not None and 0.0 <= v["dsr"] <= 1.0


def test_h12_frozen_config_hash_golden():
    """Mexeu num param [H12-FROZEN] -> quebra alto AQUI (pré-registro 2026-09-04)."""
    from config import h12_frozen_config_hash, load_config
    assert h12_frozen_config_hash(load_config()) == "73444111b8bd969f"


def test_h12_frozen_hash_ignores_operational_params():
    from config import h12_frozen_config_hash, load_config
    cfg = load_config()
    base = h12_frozen_config_hash(cfg)
    cfg["data"]["db_path"] = "outro.db"
    cfg["bootstrap"]["seed"] = 999
    assert h12_frozen_config_hash(cfg) == base
    cfg["h12_factor"]["disclosure_embargo_days"] = 5   # tocar num FROZEN muda o lacre
    assert h12_frozen_config_hash(cfg) != base


def test_net_margin_signals_embargo_blocks_early_asof(tmp_path):
    """Mesmo ponto central de H7/H9, agora para margem: sem o embargo,
    `ref_date` sozinho vazaria dado contábil antes da publicação real."""
    conn = db.get_connection(tmp_path / "s.db")
    conn.execute(
        "INSERT INTO fundamentals(ticker, ref_date, receita_liquida,"
        " lucro_liquido, net_margin, source) VALUES (?,?,?,?,?,?)",
        ("AAAA3", "2020-12-31", 1000.0, 150.0, 0.15, "CVM DFP 2020"))
    conn.commit()

    too_early = factor.net_margin_signals(conn, ["AAAA3"], "2021-03-01", disclosure_embargo_days=90)
    assert "AAAA3" not in too_early    # 60 dias após ref_date, embargo de 90 ainda não venceu

    after_embargo = factor.net_margin_signals(conn, ["AAAA3"], "2021-04-01", disclosure_embargo_days=90)
    assert after_embargo["AAAA3"] == 0.15   # 91 dias após ref_date, embargo já venceu


def test_net_margin_signals_picks_most_recent_eligible_ref_date(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    conn.execute(
        "INSERT INTO fundamentals(ticker, ref_date, receita_liquida,"
        " lucro_liquido, net_margin, source) VALUES (?,?,?,?,?,?)",
        ("AAAA3", "2019-12-31", 1000.0, 100.0, 0.10, "CVM DFP 2019"))
    conn.execute(
        "INSERT INTO fundamentals(ticker, ref_date, receita_liquida,"
        " lucro_liquido, net_margin, source) VALUES (?,?,?,?,?,?)",
        ("AAAA3", "2020-12-31", 1000.0, 150.0, 0.15, "CVM DFP 2020"))
    conn.commit()
    # ambas elegíveis em 2021-06-01 (embargo 90d vencido pras duas) -> a mais recente vence
    v = factor.net_margin_signals(conn, ["AAAA3"], "2021-06-01", disclosure_embargo_days=90)
    assert v["AAAA3"] == 0.15
