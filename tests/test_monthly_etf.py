"""Synthetic chronology and cash tests, independent of observed market returns."""
import copy
import importlib.util
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
import unittest

from stocks_predictor.monthly_etf import Costs, MonthlyTax, money, monthly_signals, simulate


def fixture():
    calendar = []
    d = date(2017, 1, 2)
    while d <= date(2019, 8, 10):
        if d.weekday() < 5:
            calendar.append(d.isoformat())
        d += timedelta(days=1)
    records = []
    for day in calendar:
        if day > "2019-08-05":
            continue
        p = 10 + (int(day[:4]) - 2017) * 12 + int(day[5:7])
        records.append(dict(date=day, ticker="BOVA11", isin="BRBOVACTF003", currency="R$",
                            bdi_code="14", market_type="010", quote_factor=1,
                            open=p, close=p, low=p, high=p, qty=10000))
    return records, calendar


ZERO = Costs(Decimal(0), Decimal(0), Decimal(0))


class MonthlyETFTests(unittest.TestCase):
    def test_signal_never_uses_execution_close_or_future(self):
        records, calendar = fixture()
        before = monthly_signals(records, calendar)
        changed = copy.deepcopy(records)
        for r in changed:
            if r["date"] >= "2018-01-01":
                for key in ("open", "close", "low", "high"):
                    r[key] = 1000
        after = monthly_signals(changed, calendar)
        self.assertEqual([s for s in before if s["execution_date"] <= "2018-01-01"],
                         [s for s in after if s["execution_date"] <= "2018-01-01"])
        self.assertTrue(all(s["signal_date"] < s["execution_date"] for s in before))
        self.assertEqual(before[0]["signal_date"], "2017-10-31")

    def test_manual_hold_cash_fees_tax_reserve_and_settlement(self):
        records, calendar = fixture()
        for r in records:
            if r["date"] >= "2018-01-01":
                p = 10 if r["date"] < "2018-02-01" else 12
                r.update(open=p, close=p, low=p, high=p)
        costs = Costs(Decimal("0.01"), Decimal(5), Decimal(10))
        r = simulate(records, calendar, start="2018-01-01", end="2018-02-01",
                     capital=1000, costs=costs, arm="hold")
        # Reserve 20; buy90@10 +14=914; remaining66. Sell1080-15.80;
        # gain150.20, tax22.53; net wealth66+1064.20-22.53=1107.67.
        self.assertEqual(r["profit"], 107.67)
        self.assertEqual(r["tax"], 22.53)
        self.assertEqual(r["expenses"], 20)
        self.assertEqual(r["fees"], 29.80)
        self.assertEqual(r["curve"][-1]["receivable"], 1064.20)
        self.assertEqual(r["ledger"][-1]["settlement_date"], "2018-02-06")
        self.assertEqual(r["curve"][0]["expense_reserve"], 10)
        self.assertEqual(r["order_count"], 2)

    def test_monthly_tax_loss_netting_no_retroactive_refund(self):
        t = MonthlyTax()
        t.gain = money(100)
        self.assertEqual(t.liability, 15)
        t.gain -= money(40)
        t.finish("2018-01")
        self.assertEqual(t.committed, 9)
        t.gain = money(-100)
        t.finish("2018-02")
        self.assertEqual(t.committed, 9)
        t.gain = money(150)
        t.finish("2018-03")
        self.assertEqual(t.committed, Decimal("16.50"))
        self.assertEqual(t.loss, 0)

    def test_uptrend_matches_hold_and_no_monthly_rebalance(self):
        records, calendar = fixture()
        kw = dict(start="2018-01-01", end="2019-08-05", capital=5000, costs=ZERO)
        a = simulate(records, calendar, arm="trend", **kw)
        b = simulate(records, calendar, arm="hold", **kw)
        self.assertEqual(a["profit"], b["profit"])
        self.assertEqual(a["order_count"], 2)
        self.assertEqual(a["ledger"][-1]["settlement_date"], "2019-08-07")

    def test_declining_closes_stay_cash_and_equality_is_cash(self):
        records, calendar = fixture()
        for r in records:
            r.update(open=20, close=20, low=20, high=20)
        self.assertTrue(all(not s["long"] for s in monthly_signals(records, calendar)))
        r = simulate(records, calendar, arm="trend", start="2018-01-01", end="2018-02-01",
                     capital=5000, costs=Costs(Decimal(0), Decimal(5), Decimal(10)))
        self.assertEqual(r["profit"], -20)
        self.assertEqual(r["order_count"], 0)

    def test_expense_infeasible_is_explicit(self):
        records, calendar = fixture()
        r = simulate(records, calendar, arm="hold", start="2018-01-01", end="2018-02-01",
                     capital=50, costs=Costs(Decimal(0), Decimal(0), Decimal(30)))
        self.assertEqual(r["status"], "INFEASIBLE_EXPENSE_RESERVE")
        self.assertNotIn("profit", r)

    def test_missing_quote_and_duplicate_calendar_fail(self):
        records, calendar = fixture()
        with self.assertRaises(ValueError):
            monthly_signals(records[:20] + records[21:], calendar)
        with self.assertRaises(ValueError):
            monthly_signals(records, calendar + calendar[-1:])

    def test_reject_lot_without_spending_or_repeated_daily_orders(self):
        records, calendar = fixture()
        r = simulate(records, calendar, arm="hold", start="2018-01-01", end="2018-02-01",
                     capital=1, costs=ZERO)
        self.assertEqual(r["profit"], 0)
        self.assertEqual(sum(x["kind"] == "REJECTED_BUY" for x in r["ledger"]), 1)

    def test_terminal_has_priority_and_adverse_fills(self):
        records, calendar = fixture()
        for r in records:
            r["close"] += 1
            r["high"] += 1
        r = simulate(records, calendar, arm="hold", start="2018-01-01", end="2018-01-01",
                     capital=1000, costs=ZERO)
        self.assertEqual(r["order_count"], 0)
        r = simulate(records, calendar, arm="hold", start="2018-01-01", end="2018-02-01",
                     capital=1000, costs=Costs(Decimal(0), Decimal(0), Decimal(0), "worst_open_close"))
        trades = [t for t in r["ledger"] if t["kind"] in {"BUY", "SELL"}]
        self.assertEqual(trades[0]["price"], 24)
        self.assertEqual(trades[-1]["price"], 24)

    def test_bad_inputs(self):
        for value in ["NaN", "Infinity"]:
            with self.assertRaises(ValueError):
                money(value)
        with self.assertRaises(ValueError):
            Costs(Decimal("-1"), Decimal(0), Decimal(0))
        records, calendar = fixture()
        records[0]["isin"] = "other"
        with self.assertRaises(ValueError):
            monthly_signals(records, calendar)

    def test_rounded_fee_maximum_lot(self):
        records, calendar = fixture()
        for r in records:
            r.update(open=1.01, close=1.01, low=1.01, high=1.01, bdi_code="02")
        r = simulate(records, calendar, arm="hold", start="2018-01-01", end="2018-02-01",
                     capital="10.10", costs=Costs(Decimal("0.0001"), Decimal(0), Decimal(0)))
        self.assertEqual(r["order_count"], 2)
        self.assertEqual(r["profit"], 0)

    def test_multiple_transitions_reconcile_and_tampering_is_rejected(self):
        records, calendar = fixture()
        for r in records:
            if r["date"].startswith("2018"):
                p = 50 if int(r["date"][5:7]) % 2 else 5
                r.update(open=p, close=p, low=p, high=p)
        spec = dict(one_way_variable_cost=0.0018, fixed_cost_per_order_brl=5,
                    monthly_expense_brl=10, price_mode="open")
        result = simulate(records, calendar, arm="trend", start="2018-01-01", end="2018-12-31",
                          capital=5000, costs=Costs(Decimal("0.0018"), Decimal(5), Decimal(10)))
        self.assertGreater(result["order_count"], 2)
        path = Path(__file__).resolve().parents[1] / "research/session-20260910/profit_validation/verify.py"
        module_spec = importlib.util.spec_from_file_location("h22_verify", path)
        assert module_spec is not None and module_spec.loader is not None
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)
        inputs = dict(records=records, calendar=calendar)
        self.assertEqual(module.verify(result, inputs, spec)["status"], "PASS")
        for field in ["wealth", "receivable", "investable_cash", "tax_committed_and_provisional"]:
            damaged = copy.deepcopy(result)
            damaged["curve"][30][field] += 0.01
            with self.subTest(field=field), self.assertRaises(AssertionError):
                module.verify(damaged, inputs, spec)


if __name__ == "__main__":
    unittest.main()
