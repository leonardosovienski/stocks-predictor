"""H4 — sizing por volatility targeting: pesos 1/vol, custo por turnover de
pesos, walk-forward ponderado e o veredito de 3 critérios (IC + DSR + drawdown).

Valida a MAQUINARIA em sintético; o veredito real é da rodada única
pré-registrada (2026-07-18). O caminho equiponderado de H1/H2 tem regressão na
própria suíte antiga (não passa por portfolio_fn).
"""
import datetime

import pytest

import backtest
import cotahist
import db
import execution
import factor
import portfolio
import trials_gate


# ---------- pesos inversos à vol ----------

def test_inverse_vol_weights_known_values():
    w = portfolio.inverse_vol_weights({"A": 0.01, "B": 0.02})
    assert w["A"] == pytest.approx(2 / 3)
    assert w["B"] == pytest.approx(1 / 3)
    assert sum(w.values()) == pytest.approx(1.0)


def test_inverse_vol_weights_drops_undefined_vol():
    w = portfolio.inverse_vol_weights({"A": 0.01, "B": 0.0, "C": None, "D": -0.1})
    assert set(w) == {"A"} and w["A"] == pytest.approx(1.0)
    assert portfolio.inverse_vol_weights({}) == {}
    assert portfolio.inverse_vol_weights({"B": 0.0}) == {}


# ---------- custo por turnover de pesos ----------

def test_weighted_turnover_cost_first_book_pays_one_side():
    cost = execution.weighted_turnover_cost({}, {"A": 0.6, "B": 0.4}, 0.0018)
    assert cost == pytest.approx(0.0018)          # Σw=1 entrando -> 1 lado inteiro


def test_weighted_turnover_cost_no_change_is_free():
    w = {"A": 0.5, "B": 0.5}
    assert execution.weighted_turnover_cost(w, dict(w), 0.0018) == 0.0


def test_weighted_turnover_cost_partial_rebalance():
    prev = {"A": 0.5, "B": 0.5}
    curr = {"A": 0.25, "B": 0.25, "C": 0.5}
    # |Δ| = 0.25 + 0.25 + 0.5 = 1.0
    assert execution.weighted_turnover_cost(prev, curr, 0.0018) == pytest.approx(0.0018)


# ---------- walk-forward ponderado + run_h4 end-to-end em sintético ----------

def _dates(n, start=(2016, 7, 1)):
    base = datetime.date(*start)
    return [(base + datetime.timedelta(days=i)).strftime("%Y%m%d") for i in range(n)]


def _synthetic_conn(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    tickers = [f"T{c}{c}{c}3" for c in "ABCDEFGHIJKL"]
    cotahist.load_prices(conn, cotahist.synthetic_cotahist(tickers, _dates(900), seed=11),
                         "COTAHIST_SYNTH.TXT")
    return conn


def test_walk_forward_weighted_produces_paired_series(tmp_path):
    from config import load_config
    cfg = load_config()
    conn = _synthetic_conn(tmp_path)
    strat, bench = backtest.walk_forward(
        conn, cfg,
        portfolio_fn=lambda sub, asof: portfolio.inverse_vol_weights(
            factor.vol_signals(sub, asof, 252)))
    conn.close()
    assert len(strat) > 60 and len(strat) == len(bench)


def test_run_h4_smoke(tmp_path, capsys):
    from config import load_config
    cfg = load_config()
    cfg["bootstrap"] = {"n_boot": 300, "block_length": 21, "confidence": 0.95, "seed": 42}

    conn = _synthetic_conn(tmp_path)
    tp = tmp_path / "trials.json"
    trials_gate.attest(cfg, trials_path=tp)
    trials_gate.register_baseline_trials(cfg, trials_path=tp)
    v = backtest.run_h4(cfg, conn, trials_path=tp)
    conn.close()

    assert "H4:" in capsys.readouterr().out
    assert v["n"] > 60 and v.get("n_trials") == 3       # DSR descontou H1+H2+H4
    assert v.get("dsr") is not None and 0.0 <= v["dsr"] <= 1.0
    assert v["maxdd_strat"] is not None and v["maxdd_bench"] is not None
    # critério (iii): se o maxDD da estratégia for pior, o veredito TEM que reprovar
    if v["maxdd_strat"] > v["maxdd_bench"]:
        assert "maxDD" in v["veredito"]


# ---------- lacre por máquina da H4 ----------

def test_h4_frozen_config_hash_golden():
    """Mexeu num param [H4-FROZEN] -> quebra alto AQUI (pré-registro 2026-07-18)."""
    from config import h4_frozen_config_hash, load_config
    assert h4_frozen_config_hash(load_config()) == "5ef902a7765eda90"


def test_h4_frozen_hash_ignores_operational_params():
    from config import h4_frozen_config_hash, load_config
    cfg = load_config()
    base = h4_frozen_config_hash(cfg)
    cfg["data"]["db_path"] = "outro.db"
    cfg["bootstrap"]["seed"] = 999
    assert h4_frozen_config_hash(cfg) == base
    cfg["h4_weighting"]["vol_lookback_days"] = 63    # tocar num FROZEN muda o lacre
    assert h4_frozen_config_hash(cfg) != base
