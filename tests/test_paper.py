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


def test_settle_ignores_non_spot_rows(tmp_path):
    """Regressão (revisão 2026-07-18): linha de derivativo (mkt 070) carregada num
    banco com avista_only=False NÃO pode virar preço de execução do paper.

    Cenário determinístico: asof = ÚLTIMO pregão à vista do banco; a única linha
    posterior é uma opção a 0,01. Sem o filtro de leitura, o settle liquidaria a
    0,01; com ele, corretamente NÃO liquida (não há D+1 à vista ainda)."""
    conn = _load(tmp_path)
    last_spot = conn.execute("SELECT MAX(date) FROM prices_raw").fetchone()[0]
    paper.record_forward(conn, _CFG, asof=last_spot, run_id="run_paper")
    tk = conn.execute(
        "SELECT ticker FROM decisions WHERE run_id='run_paper' LIMIT 1").fetchone()[0]
    conn.execute(
        "INSERT INTO prices_raw(date,ticker,bdi_code,market_type,open,high,low,close,"
        "volume_fin,qty,quote_factor,source_file) "
        "VALUES(date(?, '+1 day'),?, '78','070',0.01,0.01,0.01,0.01,1,1,1,'OPCOES.TXT')",
        (last_spot, tk))
    conn.commit()
    paper.settle_executions(conn, _CFG)
    row = conn.execute(
        "SELECT exec_price FROM decisions WHERE run_id='run_paper' AND ticker=?",
        (tk,)).fetchone()
    assert row["exec_price"] is None
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
