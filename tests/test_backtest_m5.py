"""M5 — walk-forward + pedágio de 2 lentes, end-to-end sobre dados sintéticos.

Verifica a MAQUINARIA (gera séries pareadas, o pedágio roda e devolve veredito). Não
asserta o veredito da H1: dado sintético é random walk, então "não comprovada" é o
esperado — o que importa é o instrumento funcionar sem lookahead.
"""
import datetime

import backtest
import cotahist
import db


def _dates(n, start=(2016, 7, 1)):
    base = datetime.date(*start)
    return [(base + datetime.timedelta(days=i)).strftime("%Y%m%d") for i in range(n)]


_CFG = {
    "factor": {"lookback_days": 252, "skip_days": 21},
    "universe": {"top_n": 60, "lookback_trading_days": 126, "min_history_days": 252},
    "portfolio": {},
    "execution": {"b3_fee_pct": 0.0003, "spread_slippage_pct": 0.0015},
    "backtest": {"test_start": "2018-01-01"},
    "bootstrap": {"n_boot": 500, "block_length": 21, "confidence": 0.95, "seed": 42},
}


def _load(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    tickers = [f"T{c}{c}{c}3" for c in "ABCDEFGHIJKL"]      # 12 prefixos distintos
    lines = cotahist.synthetic_cotahist(tickers, _dates(900), seed=11)
    cotahist.load_prices(conn, lines, "COTAHIST_SYNTH.TXT")
    return conn


def test_walk_forward_produces_paired_series(tmp_path):
    conn = _load(tmp_path)
    strat, bench = backtest.walk_forward(conn, _CFG)
    assert len(strat) > 60 and len(strat) == len(bench)   # diária, pareada, > 2*bloco
    conn.close()


def test_judge_runs_the_two_lens_toll(tmp_path):
    conn = _load(tmp_path)
    strat, bench = backtest.walk_forward(conn, _CFG)
    v = backtest.judge(strat, bench, _CFG)
    assert v["n"] == len(strat)
    assert v["psr"] is None or 0.0 <= v["psr"] <= 1.0
    lo, hi = v["sharpe_diff_ci"]
    assert lo is not None and hi is not None and lo <= hi   # o pedágio devolveu um IC
    assert v["veredito"] in ("COMPROVADA", "não comprovada (IC cruza 0 / negativo)")


def test_run_smoke(tmp_path, capsys, monkeypatch):
    # Isola a telemetria: run() emite 'backtest_completed' via emit_event, cujo destino
    # default é events.jsonl na cwd. Sem este redirecionamento o teste sujaria a árvore
    # de trabalho (predictor-stocks/events.jsonl) a cada execução.
    monkeypatch.setenv("PREDICTOR_EVENTS_PATH", str(tmp_path / "events.jsonl"))
    conn = _load(tmp_path)
    v = backtest.run(_CFG, conn)
    assert "H1:" in capsys.readouterr().out and "veredito" in v
    conn.close()
    assert (tmp_path / "events.jsonl").exists()   # o evento foi emitido (no destino isolado)
