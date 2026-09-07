import json
from pathlib import Path

import pytest

import db
import simulation
import stock_events


DAYS = ["2025-11-25", "2025-11-26", "2025-11-27", "2025-11-28", "2025-12-01", "2025-12-02"]


def test_real_bonus_import_is_idempotent_and_conflicts_rollback(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    payload = (Path(__file__).parent / "fixtures/real_integration/bonus-events.json").read_bytes()
    assert stock_events.import_bonus_events(conn, payload) == 3
    assert stock_events.import_bonus_events(conn, payload) == 0
    rows = json.loads(payload)
    rows.insert(0, {**rows[0], "ticker": "TEST3"})
    rows[-1]["credit_date"] = "2025-12-03"
    with pytest.raises(ValueError, match="conflicting immutable"):
        stock_events.import_bonus_events(conn, json.dumps(rows).encode())
    assert conn.execute("SELECT COUNT(*) FROM stock_bonus_events").fetchone()[0] == 3
    assert stock_events.bonus_events(conn, "ENGI11", DAYS[-1]) == [("2025-11-28", "2025-12-02", 0.1)]


def test_bonus_nav_is_recognized_on_ex_but_new_shares_cannot_be_sold_before_credit():
    bars = {"A": {d: (110 if d < DAYS[3] else 100,) * 2 for d in DAYS}}
    settings = dict(cost_per_side=0, initial_cash=11000, stock_events={"A": [(DAYS[3], DAYS[-1], 0.1)]})
    result = simulation.simulate_portfolio(DAYS, bars, {DAYS[0]: {"A": 1}, DAYS[2]: {}}, **settings)
    assert result["nav"] == pytest.approx([11000] * 6)
    assert [(e["exec_date"], e["quantity"]) for e in result["executions"]] == [(DAYS[1], 100), (DAYS[3], -100)]
    assert result["holdings"] == {"A": 10}
    assert result["stock_deliveries"] == [(DAYS[-1], "A", 10)]
    before_credit = simulation.simulate_portfolio(DAYS[:-1], bars, {DAYS[0]: {"A": 1}, DAYS[2]: {}}, **settings)
    assert before_credit["holdings"] == {}
    assert before_credit["stock_receivables"] == [("A", DAYS[-1], 10)]


def test_cash_before_bonus_uses_original_quantity_even_during_quote_gap():
    bars = {"A": {DAYS[0]: (110, 110), DAYS[1]: (110, 110), DAYS[-1]: (100, 100)}}
    result = simulation.simulate_portfolio(
        [DAYS[0], DAYS[1], DAYS[-1]], bars, {DAYS[0]: {"A": 1}}, initial_cash=11000,
        cost_per_side=0, stock_events={"A": [(DAYS[3], DAYS[-1], 0.1)]},
        cash_events={"A": [(DAYS[2], "2025-12-19", 0.7)]},
    )
    assert result["holdings"] == {"A": 110}
    assert result["receivables"] == [("2025-12-19", 70)]
    assert result["nav"][-1] == 11070


def test_purchase_on_ex_does_not_receive_bonus():
    bars = {"A": {d: (100, 100) for d in DAYS}}
    result = simulation.simulate_portfolio(DAYS, bars, {DAYS[2]: {"A": 1}}, cost_per_side=0,
                                          stock_events={"A": [(DAYS[3], DAYS[-1], 0.1)]})
    assert result["stock_entitlements"] == []


def test_bonus_with_no_quote_keeps_economic_mark_and_does_not_create_profit():
    bars = {"A": {DAYS[0]: (110, 110), DAYS[1]: (110, 110), DAYS[-1]: (100, 100)}}
    result = simulation.simulate_portfolio(DAYS, bars, {DAYS[0]: {"A": 1}}, cost_per_side=0,
                                          stock_events={"A": [(DAYS[3], DAYS[-1], 0.1)]})
    assert result["nav"] == pytest.approx([1] * 6)


def test_lot_rounding_keeps_cash_and_pays_only_actual_trade_cost():
    bars = {"A": {d: (12, 12) for d in DAYS}}
    result = simulation.simulate_portfolio(DAYS, bars, {DAYS[0]: {"A": 1}}, initial_cash=5000,
                                          quantity_step=100, cost_per_side=0.002)
    assert result["holdings"] == {"A": 400}
    assert len(result["executions"]) == 1
    assert result["cash"] == pytest.approx(190.4)
    assert result["nav"][-1] == pytest.approx(4990.4)


def test_adverse_buy_completes_its_budget_and_does_not_turn_into_a_later_sale():
    bars = {"A": {d: (100, 110) if d <= DAYS[1] else (120, 120) for d in DAYS}}
    result = simulation.simulate_portfolio(DAYS, bars, {DAYS[0]: {"A": 1}}, initial_cash=5000,
                                          cost_per_side=0.0018, price_mode="worst")
    assert len(result["executions"]) == 1
    assert result["pending_orders"] == {}
    assert result["holdings"]["A"] == pytest.approx(5000 / (110 * 1.0018))


def test_board_lot_setting_does_not_silently_sell_bonus_odd_lots():
    bars = {"A": {d: (100, 100) for d in DAYS}}
    with pytest.raises(ValueError, match="odd lots"):
        simulation.simulate_portfolio(
            DAYS, bars, {DAYS[0]: {"A": 1}, DAYS[-2]: {}}, initial_cash=10000,
            cost_per_side=0, quantity_step=100, stock_events={"A": [(DAYS[3], DAYS[-1], 0.1)]},
        )
