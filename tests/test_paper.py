"""M6 — paper ledger forward: registro EVAL antes do futuro + RISK write-once."""
import datetime

import cotahist
import db
import paper

_CFG = {
    "universe": {"top_n": 60, "lookback_trading_days": 126, "min_history_days": 252},
    "factor": {"lookback_days": 252, "skip_days": 21},
    "execution": {"b3_fee_pct": 0.0003, "spread_slippage_pct": 0.0015},
}


def _load(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    base = datetime.date(2016, 7, 1)
    dates = [(base + datetime.timedelta(days=i)).strftime("%Y%m%d") for i in range(700)]
    tickers = [f"T{c}{c}{c}3" for c in "ABCDEFGHIJKL"]
    cotahist.load_prices(conn, cotahist.synthetic_cotahist(tickers, dates, seed=5), "SYNTH.TXT")
    return conn


def test_record_forward_writes_eval_part(tmp_path):
    conn = _load(tmp_path)
    n = paper.record_forward(conn, _CFG, asof="2018-01-31", run_id="run_paper")
    assert n > 0
    rows = conn.execute(
        "SELECT conviction_band, frozen_mode, exec_price FROM decisions WHERE run_id='run_paper'"
    ).fetchall()
    assert rows and all(r["frozen_mode"] == 1 for r in rows)
    assert all(r["exec_price"] is None for r in rows)              # RISK ainda vazia (anti-tautologia)
    assert any(r["conviction_band"] == "quintil_superior" for r in rows)
    conn.close()


def test_settle_fills_exec_write_once(tmp_path):
    conn = _load(tmp_path)
    paper.record_forward(conn, _CFG, asof="2018-01-31", run_id="run_paper")
    filled = paper.settle_executions(conn, _CFG)
    assert filled > 0
    row = conn.execute(
        "SELECT exec_date, exec_price FROM decisions "
        "WHERE run_id='run_paper' AND exec_price IS NOT NULL LIMIT 1").fetchone()
    assert row["exec_date"] > "2018-01-31"                          # D+1 após o asof
    first_price = row["exec_price"]
    # segunda liquidação não reescreve (write-once via COALESCE)
    assert paper.settle_executions(conn, _CFG) == 0
    same = conn.execute(
        "SELECT exec_price FROM decisions WHERE run_id='run_paper' AND exec_date IS NOT NULL "
        "LIMIT 1").fetchone()
    assert same["exec_price"] == first_price
    conn.close()
