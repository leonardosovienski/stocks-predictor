"""Accounting invariants; these synthetic paths are not strategy observations."""
from copy import deepcopy
from decimal import Decimal as D

import pytest

from retail_cash import Holding, RetailBook, execution_readiness, integer_targets, ordinary_month_tax, trade_value


def quote(day="2020-01-03", isin="TEST", standard="10", fractional="10.20"):
    return dict(date=day, isin=isin, standard=standard, fractional=fractional)


def book(capital=2000):
    return RetailBook(capital, "2020-01-03")


def test_actual_lot_mix_and_signal_day_integer_sizing():
    assert trade_value(123, quote()) == D("1234.60")
    assert trade_value(7, {"standard": "25"}, lot=1) == 175
    assert integer_targets(1000, {"A": "30", "B": "70"}) == {"A": 16, "B": 7}
    with pytest.raises(KeyError):
        trade_value(1, {"standard": 10})


@pytest.mark.parametrize("bad", [True, -1, 1.5])
def test_noninteger_share_orders_rejected(bad):
    with pytest.raises(ValueError):
        trade_value(bad, quote())


@pytest.mark.parametrize("change", [{"date": "2020-01-02"}, {"isin": "OTHER"}])
def test_quote_cannot_cross_date_or_security(change):
    b = book()
    with pytest.raises(ValueError):
        b.order("A", "TEST", 1, {**quote(), **change}, "2020-01-02", "2020-01-07")
    assert not b.positions and not b.pending


def test_same_day_signal_cannot_trade_at_earlier_open():
    with pytest.raises(ValueError, match="after its signal"):
        book().order("A", "TEST", 1, quote(), "2020-01-03", "2020-01-07")


def test_rebalance_retains_shares_and_only_charges_quantity_change():
    b = book()
    ids = {"A": {"isin": "TEST"}}
    b.rebalance({"A": 100}, {"A": quote()}, ids, "2020-01-02", "2020-01-07", ".001")
    b.advance("2020-01-07")
    assert b.cash == 999
    assert b.rebalance({"A": 100}, {}, {}, "2020-01-06", "2020-01-09", ".001") == []
    rows = b.rebalance({"A": 103}, {"A": quote("2020-01-07")}, ids, "2020-01-06", "2020-01-09", ".001")
    assert len(rows) == 1 and rows[0]["quantity"] == 3
    assert rows[0]["costs"] == D(".03060")


def test_missing_later_quote_rolls_back_entire_rebalance():
    b = book()
    before = deepcopy(b.__dict__)
    with pytest.raises(KeyError):
        b.rebalance({"A": 3, "B": 3}, {"A": quote()}, {"A": {"isin": "TEST"}, "B": {"isin": "B"}},
                    "2020-01-02", "2020-01-07")
    assert b.__dict__ == before


def test_opening_gap_shrinks_unfunded_order_without_borrowing():
    b = book(100)
    rows = b.rebalance(integer_targets(100, {"A": 10}), {"A": quote(fractional=12)},
                       {"A": {"isin": "TEST"}}, "2020-01-02", "2020-01-07", 0)
    assert rows[0]["quantity"] == 8
    b.advance("2020-01-07")
    assert b.cash == 4


def test_later_sale_proceeds_do_not_fund_earlier_settlement():
    b = book(0)
    b.pending = [{"date": "2020-01-08", "amount": D(100)}]
    assert not b.fundable(100, "2020-01-07")
    assert b.fundable(100, "2020-01-08")
    b.pending.append({"date": "2020-01-07", "amount": D(-100)})
    before = deepcopy(b.__dict__)
    with pytest.raises(ValueError, match="deficit"):
        b.advance("2020-01-09")
    assert b.__dict__ == before


def test_dividend_survives_sale_and_is_unavailable_on_payment_date():
    b = book(0)
    b.positions["A"] = Holding("TEST", 10, D(100))
    assert b.entitlement("d1", "A", "TEST", b.day, "2020-01-08", "2020-01-09", ".85") == D("8.50")
    assert not b.fundable(1, "2020-01-10")
    b.order("A", "TEST", -10, quote(), "2020-01-02", "2020-01-07", 0)
    b.advance("2020-01-08")
    assert b.cash == 102 and b.rights["d1"]["net"] == D("8.50")
    b.advance("2020-01-09")
    assert b.cash == D("110.50") and not b.rights
    with pytest.raises(ValueError, match="duplicate"):
        b.entitlement("d1", "A", "TEST", b.day, "2020-01-10", "2020-01-13", 1)


def test_ex_day_buyer_gets_no_prior_entitlement_and_wrong_order_fails():
    b = book()
    assert b.entitlement("old", "A", "TEST", b.day, "2020-01-08", "2020-01-09", 1) == 0
    b.order("A", "TEST", 1, quote(), "2020-01-02", "2020-01-07")
    with pytest.raises(ValueError, match="before ex-day"):
        b.entitlement("late", "A", "TEST", b.day, "2020-01-08", "2020-01-09", 1)


def test_cash_advance_uses_chronology_across_rights_and_debits():
    b = book(0)
    b.positions["A"] = Holding("TEST", 10, D(100))
    b.entitlement("d1", "A", "TEST", b.day, "2020-01-06", "2020-01-07", 1)
    b.pending = [{"date": "2020-01-08", "amount": D(-10)}]
    b.advance("2020-01-09")
    assert b.cash == 0 and not b.rights and not b.pending


def sale(gross, gain, tax_class="equity", **kw):
    return dict(date="2020-01-08", isin="TEST", quantity=-1, gross=gross, gain=gain, tax_class=tax_class, **kw)


def test_tax_uses_sales_not_purchase_turnover_and_threshold_is_inclusive():
    rows = [sale(20000, 1000), {**sale(9000, 0), "quantity": 1, "date": "2020-01-03"}]
    result = ordinary_month_tax(rows, prior_loss=200)
    assert result["tax"] == 0 and result["loss_carry"] == 200 and result["equity_sales"] == 20000
    assert ordinary_month_tax([sale("20000.01", 1000)], prior_loss=200)["tax"] == 120


def test_small_sale_losses_carry_and_bdr_has_no_equity_exemption():
    assert ordinary_month_tax([sale(100, -50)], prior_loss=20)["loss_carry"] == 70
    assert ordinary_month_tax([sale(100, 50, "bdr")], prior_loss=20)["tax"] == D("4.5")
    result = ordinary_month_tax([sale(100, 50), {**sale(100, -20, "bdr"), "isin": "BDR"}])
    assert result["exempt_equity_gain"] == 50 and result["loss_carry"] == 20


def test_tax_rejects_combined_months_day_trade_and_unreviewed_classes():
    for rows in ([sale(100, 10), {**sale(100, -10), "date": "2020-02-03"}],
                 [sale(100, 10), {**sale(100, 0), "quantity": 1}], [sale(100, 10, "foreign")]):
        with pytest.raises(ValueError):
            ordinary_month_tax(rows)


def test_conversion_requires_whole_delivery_and_preserves_basis_until_sale():
    b = book(0)
    b.positions["A"] = Holding("TEST", 10, D(100))
    leg = dict(ticker="B", isin="NEXT", quantity=4, tax_class="equity", credit_date="2020-01-08")
    for bad in ({**leg, "quantity": 4.5}, {**leg, "credit_date": "2020-01-02"}):
        with pytest.raises(ValueError):
            b.deliver_conversion("A", "TEST", [bad], [1])
        assert "A" in b.positions
    b.deliver_conversion("A", "TEST", [leg], [1])
    assert b.positions["B"].basis == 100
    with pytest.raises(ValueError, match="delivered"):
        b.order("B", "NEXT", -4, quote(isin="NEXT"), "2020-01-02", "2020-01-07")
    b.advance("2020-01-08")
    assert b.order("B", "NEXT", -4, quote(b.day, "NEXT", fractional=30), "2020-01-07", "2020-01-10", 0)["gain"] == 20


def test_gate_requires_complete_intervals_and_explicit_execution_review():
    interval = ["A", "TEST", "2020-01-03", "2020-04-01"]
    coverage = [{"interval": interval, "verified": True, "sources": ["sha256:fixture"]}]
    checks = {k: {"verified": True, "sources": ["sha256:fixture"]} for k in
              ("quotes", "corporate_actions", "tax_schedule", "cash_coverage_inventory")}
    row = dict(event_id="d1", ticker="A", isin="TEST", ex_date="2020-01-06", payment_date="2020-01-07",
               available_on="2020-01-08", net_per_share="0", source_review=True, sources=["sha256:fixture"],
               tax_source="sha256:fixture")
    assert execution_readiness([interval], coverage, [row], [], checks)["ready"]
    for cov, rows, chk in ([], [row], checks), (coverage, [{**row, "net_per_share": ""}], checks), \
                          (coverage, [{**row, "source_review": "yes"}], checks), (coverage, [row, row], checks), \
                          (coverage, [row], None):
        result = execution_readiness([interval], cov, rows, [], chk)
        assert not result["ready"] and result["profit"] is None
        assert result["new_historical_return_evaluations"] == 0
    assert not execution_readiness([], [], [], [], checks)["ready"]
