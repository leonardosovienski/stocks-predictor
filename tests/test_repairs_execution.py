"""Mechanical hand-computed controls; no protected empirical return series."""

import copy
import math

import pytest

import adjust
import backtest
import cash_events
import db
import simulation
from tests.test_repairs_cvm import add_price


DAYS = ["2024-01-31", "2024-02-01", "2024-02-02"]


def test_next_open_excludes_pre_entry_gap_and_next_close_excludes_intraday():
    bars = {"A": {DAYS[0]: (100, 100), DAYS[1]: (200, 220), DAYS[2]: (220, 242)}}
    target = {DAYS[0]: {"A": 1}}
    opened = simulation.simulate_portfolio(DAYS, bars, target, cost_per_side=0)
    closed = simulation.simulate_portfolio(DAYS, bars, target, cost_per_side=0, price_mode="next_close")
    assert opened["returns"] == pytest.approx([0, 0.1, 0.1])
    assert closed["returns"] == pytest.approx([0, 0, 0.1])
    assert all(t["exec_date"] > t["signal_date"] for t in opened["executions"])


def test_quantities_are_held_instead_of_daily_equal_weight_reset():
    bars = {"A": {DAYS[1]: (100, 200), DAYS[2]: (200, 100)}, "B": {DAYS[1]: (100, 100), DAYS[2]: (100, 100)}}
    r = simulation.simulate_portfolio(DAYS, bars, {DAYS[0]: {"A": 0.5, "B": 0.5}}, cost_per_side=0)
    assert r["nav"] == pytest.approx([1, 1.5, 1])
    assert len(r["executions"]) == 2
    assert r["holdings"] == pytest.approx({"A": 0.005, "B": 0.005})


def test_monthly_resize_same_names_pays_cost_on_weight_drift():
    dates = DAYS + ["2024-02-29", "2024-03-01"]
    bars = {"A": {d: (100, 100) for d in dates}, "B": {d: (100, 100) for d in dates}}
    bars["A"][dates[3]] = (100, 200)
    bars["A"][dates[4]] = (200, 200)
    r = simulation.simulate_portfolio(
        dates, bars, {dates[0]: {"A": 0.5, "B": 0.5}, dates[3]: {"A": 0.5, "B": 0.5}}, cost_per_side=0.01
    )
    last = [e for e in r["executions"] if e["exec_date"] == dates[-1]]
    assert len(last) == 2 and sum(e["cost"] for e in last) > 0
    assert last[0]["quantity"] < 0 and last[1]["quantity"] > 0
    assert all(e["cash_after"] >= 0 for e in r["executions"])


def test_missing_open_delays_only_that_order_and_retains_cash():
    bars = {"A": {DAYS[1]: (100, 100), DAYS[2]: (100, 100)}, "B": {DAYS[2]: (100, 100)}}
    r = simulation.simulate_portfolio(DAYS, bars, {DAYS[0]: {"A": 0.5, "B": 0.5}}, cost_per_side=0)
    fills = {e["ticker"]: e for e in r["executions"]}
    assert fills["A"]["exec_date"] == DAYS[1] and fills["B"]["exec_date"] == DAYS[2]
    assert fills["A"]["cash_after"] == 0.5
    assert r["nav"] == pytest.approx([1, 1, 1])


def test_stale_name_keeps_weight_and_recovers_full_gap():
    dates = DAYS + ["2024-02-05"]
    bars = {
        "A": {DAYS[1]: (100, 100), dates[-1]: (50, 50)},
        "B": {DAYS[1]: (100, 100), DAYS[2]: (100, 200), dates[-1]: (200, 200)},
    }
    r = simulation.simulate_portfolio(dates, bars, {DAYS[0]: {"A": 0.5, "B": 0.5}}, cost_per_side=0)
    assert r["nav"] == pytest.approx([1, 1, 1.5, 1.25])
    assert r["stale_marks"] == [(DAYS[2], "A", DAYS[1])]
    with pytest.raises(ValueError, match="incomplete final valuation"):
        simulation.simulate_portfolio(DAYS, bars, {DAYS[0]: {"A": 0.5, "B": 0.5}}, cost_per_side=0)


def test_empty_target_sells_existing_holdings_with_exit_cost():
    dates = DAYS + ["2024-02-05"]
    bars = {"A": {d: (100, 100) for d in dates}}
    r = simulation.simulate_portfolio(dates, bars, {DAYS[0]: {"A": 1}, DAYS[2]: {}}, cost_per_side=0.01)
    assert r["holdings"] == {}
    assert r["nav"][-1] == pytest.approx(0.99 / 1.01)
    assert len(r["executions"]) == 2


def test_future_prices_cannot_change_past_executions_or_nav():
    bars = {"A": {d: (100, 100) for d in DAYS}}
    changed = copy.deepcopy(bars)
    changed["A"][DAYS[-1]] = (900, 1000)
    a = simulation.simulate_portfolio(DAYS, bars, {DAYS[0]: {"A": 1}}, cost_per_side=0.002)
    b = simulation.simulate_portfolio(DAYS, changed, {DAYS[0]: {"A": 1}}, cost_per_side=0.002)
    assert a["executions"] == b["executions"]
    assert a["nav"][:-1] == b["nav"][:-1]


def test_worst_price_and_doubled_cost_are_effective_controls():
    dates = DAYS + ["2024-02-05"]
    bars = {"A": {d: (100, 110) for d in dates}}
    target = {DAYS[0]: {"A": 1}, DAYS[2]: {}}
    opened = simulation.simulate_portfolio(dates, bars, target, cost_per_side=0.002)
    closed = simulation.simulate_portfolio(dates, bars, target, cost_per_side=0.002, price_mode="next_close")
    worst = simulation.simulate_portfolio(dates, bars, target, cost_per_side=0.002, price_mode="worst")
    doubled = simulation.simulate_portfolio(dates, bars, target, cost_per_side=0.004)
    assert worst["nav"][-1] < min(opened["nav"][-1], closed["nav"][-1])
    assert doubled["nav"][-1] < opened["nav"][-1]


def event_csv(rows):
    return ("ticker,event_id,ex_date,payment_date,value_per_share,source\n" + "\n".join(rows) + "\n").encode()


def coverage(ticker="AAAA3", start="2024-01-01", end="2024-12-31"):
    return [{"ticker": ticker, "start_date": start, "end_date": end, "source": "synthetic verified fixture"}]


def test_cash_entitlement_ex_date_and_payment_do_not_create_double_return():
    dates = DAYS + ["2024-02-05"]
    bars = {"A": {DAYS[1]: (100, 100), DAYS[2]: (95, 95), dates[-1]: (95, 95)}}
    r = simulation.simulate_portfolio(
        dates, bars, {DAYS[0]: {"A": 1}}, cost_per_side=0, cash_events={"A": [(DAYS[2], dates[-1], 5)]}
    )
    assert r["nav"] == pytest.approx([1, 1, 1, 1])
    assert r["cash"] == pytest.approx(0.05)
    buyer = simulation.simulate_portfolio(
        dates, bars, {DAYS[1]: {"A": 1}}, cost_per_side=0, cash_events={"A": [(DAYS[2], dates[-1], 5)]}
    )
    assert buyer["cash"] == 0


def test_total_return_sums_same_ex_date_cash_before_split_adjustments(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    for day, price in zip(DAYS, [100, 90, 45]):
        add_price(conn, day=day, opening=price, closing=price)
    conn.execute(
        "INSERT INTO adjustments(ticker,ex_date,factor,type,source,approved_by)"
        " VALUES ('AAAA3',?,0.5,'split','fixture','tester')",
        (DAYS[2],),
    )
    payload = event_csv([f"AAAA3,1,{DAYS[1]},{DAYS[2]},4,fixture", f"AAAA3,2,{DAYS[1]},{DAYS[2]},6,fixture"])
    assert cash_events.import_verified_events(conn, payload, coverage()) == 2
    assert cash_events.import_verified_events(conn, payload, coverage()) == 0
    dates, index = adjust.total_return_series(conn, "AAAA3")
    assert dates == DAYS
    assert index == pytest.approx([100, 100, 100])
    # A future split cannot change the prefix of the total-return signal.
    assert adjust.total_return_series(conn, "AAAA3", asof=DAYS[1])[1] == pytest.approx([100, 100])


def test_unverified_legacy_dividends_and_missing_coverage_fail_closed(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    for day in DAYS:
        add_price(conn, day=day)
    conn.execute(
        "INSERT INTO dividends(ticker,ex_date,value_per_share,source) VALUES ('AAAA3',?,1,'CVM FRE 2023')",
        (DAYS[1],),
    )
    with pytest.raises(ValueError, match="missing verified"):
        adjust.total_return_series(conn, "AAAA3")
    cash_events.import_verified_events(conn, event_csv([]), coverage())
    assert adjust.total_return_series(conn, "AAAA3")[1] == [10, 10, 10]


@pytest.mark.parametrize(
    "row",
    [
        "AAAA3,1,2201-01-01,2201-02-01,1,fixture",
        "AAAA3,1,2024-02-01,2024-01-01,1,fixture",
        "AAAA3,1,2024-02-01,2024-02-01,NaN,fixture",
        "AAAA3,1,2024-02-31,2024-03-01,1,fixture",
    ],
)
def test_invalid_cash_events_do_not_partially_write(tmp_path, row):
    conn = db.get_connection(tmp_path / "s.db")
    with pytest.raises(ValueError):
        cash_events.import_verified_events(conn, event_csv([row]), coverage())
    assert conn.execute("SELECT COUNT(*) FROM cash_events").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM cash_event_coverage").fetchone()[0] == 0


def test_duplicate_cash_event_is_rejected_before_writing(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    row = "AAAA3,1,2024-02-01,2024-02-01,1,fixture"
    with pytest.raises(ValueError, match="duplicate event"):
        cash_events.import_verified_events(conn, event_csv([row, row]), coverage())
    assert conn.execute("SELECT COUNT(*) FROM cash_events").fetchone()[0] == 0


def test_corrected_walk_forward_uses_same_execution_for_equal_target_and_benchmark(tmp_path, monkeypatch):
    conn = db.get_connection(tmp_path / "s.db")
    days = ["2024-01-30", "2024-01-31", "2024-02-01", "2024-02-29", "2024-03-01"]
    for i, day in enumerate(days):
        add_price(conn, "AAAA3", day, 10 + i, 11 + i)
        add_price(conn, "BBBB3", day, 20 + i, 21 + i)
    monkeypatch.setattr(adjust, "require_scanned", lambda conn: None)
    import universe

    monkeypatch.setattr(universe, "select_universe", lambda *args, **kwargs: ["AAAA3", "BBBB3"])
    observed = []

    def pf(sub, asof):
        assert all(all(d <= asof for d in ds) for ds, ps in sub.values())
        observed.append(asof)
        return {"AAAA3": 0.5, "BBBB3": 0.5}

    cfg = {"backtest": {"test_start": days[0]}, "execution": {"price": "next_open"}, "universe": {}}
    strat, bench = backtest.walk_forward(conn, cfg, portfolio_fn=pf)
    assert observed == ["2024-01-31", "2024-02-29"]
    assert strat == bench and len(strat) == len(days)
    assert all(math.isfinite(r) for r in strat)
    cfg["backtest"]["purge_embargo_months"] = 1
    with pytest.raises(ValueError, match="requires explicit train_end"):
        backtest.walk_forward(conn, cfg, portfolio_fn=pf)
    cfg["backtest"]["train_end"] = "2023-12-31"
    observed.clear()
    strat, bench = backtest.walk_forward(conn, cfg, portfolio_fn=pf)
    assert observed == ["2024-02-29"]
    assert len(strat) == 3 and strat == bench


@pytest.mark.parametrize("number", [17, 18, 19])
def test_cli_protected_gate_precedes_connection_and_registration(monkeypatch, number):
    import main

    def forbidden():
        raise AssertionError("protected CLI must not open or migrate a database")

    monkeypatch.setattr(main, "_conn", forbidden)
    assert main.cmd_backtest_hn([str(number)]) == 2
