"""M4 — momentum 12-1, carteira quintil, execução D+1 + ANTI-LOOKAHEAD (exec_ts > signal_ts)."""
import datetime

import execution
import factor
import portfolio


def _daily(n):
    base = datetime.date(2022, 1, 3)
    return [(base + datetime.timedelta(days=i)).isoformat() for i in range(n)]


def test_momentum_12_1_matches_window():
    dates = _daily(300)
    closes = [100.0 * (1.001 ** i) for i in range(300)]
    asof = dates[280]
    m = factor.momentum_12_1(dates, closes, asof, lookback=252, skip=21)
    esperado = 1.001 ** (252 - 21) - 1.0          # close[280-21]/close[280-252]-1
    assert abs(m - esperado) < 1e-6


def test_momentum_none_without_history():
    dates = _daily(100)
    closes = [100.0] * 100
    assert factor.momentum_12_1(dates, closes, dates[50], lookback=252, skip=21) is None


def test_portfolio_top_quintile_equal_weight():
    sig = {f"T{i}": float(i) for i in range(10)}   # T9 maior
    p = portfolio.select_portfolio(sig, quantile=0.2)
    assert set(p) == {"T8", "T9"}                  # top 20% de 10 = 2
    assert all(abs(w - 0.5) < 1e-9 for w in p.values())


def test_portfolio_is_long_only_top():
    sig = {"A": -0.5, "B": 0.1, "C": 0.3, "D": 0.9, "E": 0.5}
    p = portfolio.select_portfolio(sig, quantile=0.2)   # round(5*0.2)=1 -> só o maior
    assert set(p) == {"D"}


def test_execution_strictly_after_signal_antilookahead():
    dates = ["2024-01-31", "2024-02-01", "2024-02-02"]
    opens = [10.0, 10.5, 10.7]
    exec_date, exec_price = execution.next_open_after(dates, opens, "2024-01-31")
    assert (exec_date, exec_price) == ("2024-02-01", 10.5)
    assert exec_date > "2024-01-31"                # exec_ts > signal_ts: anti-lookahead


def test_execution_no_future_is_none():
    assert execution.next_open_after(["2024-01-31"], [10.0], "2024-01-31") is None


def test_net_return_applies_roundtrip_cost():
    r = execution.net_return(10.0, 11.0, 0.0003, 0.0015)
    assert abs(r - (0.10 - 0.0036)) < 1e-9          # 0.36% ida-e-volta
