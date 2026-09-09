"""Meaningful cash/causality guards, usable with unittest without Core imports."""
import copy
from decimal import Decimal
import unittest

from stocks_predictor.etf_hold import cents, selic_reference, simulate, validate_quotes


def fixture():
    days = ["2018-01-02", "2018-01-03", "2018-01-04", "2018-01-05", "2018-01-08", "2018-01-09"]
    records = [{"date": d, "ticker": "BOVA11", "isin": "BRBOVACTF003", "market_type": "010",
                "currency": "R$", "quote_factor": 1, "open": p, "close": p,
                "low": p - 1, "high": p + 1, "volume_fin": 1000000}
               for d, p in zip(days[:3], [100, 50, 120])]
    return records, days


def run_case(records=None, days=None, **kwargs):
    default_records, default_days = fixture()
    options = {"capital": 10000, "rate": "0.0018", "mode": "open",
               "entry_signal": "2017-12-29", "exit_signal": "2018-01-03"}
    options.update(kwargs)
    return simulate(default_records if records is None else records,
                    default_days if days is None else days, **options)


class EtfBookTests(unittest.TestCase):
    def test_integer_lot_reserves_costs_and_separates_principal(self):
        r = run_case()
        self.assertEqual(r["units"], 90)
        self.assertEqual(r["tax_basis_brl"], 9016.20)
        self.assertEqual(r["residual_cash_brl"], 983.80)
        self.assertEqual(r["modeled_pretax_profit_brl"], 1764.36)
        self.assertEqual(r["tax_obligation_brl"], 264.65)
        self.assertEqual(r["conditional_profit_before_unknown_expenses_brl"], 1499.71)
        self.assertEqual(r["end_equity_after_tax_reserve_brl"], 11499.71)

    def test_tax_applies_below_20000_etf_sale(self):
        r = run_case()
        self.assertLess(r["sale_notional_brl"], 20000)
        self.assertGreater(r["tax_obligation_brl"], 0)

    def test_no_tax_on_loss_or_invented_loss_credit(self):
        r, days = fixture()
        r[-1].update(open=70, close=70, low=69, high=71)
        result = run_case(r, days)
        self.assertEqual(result["tax_obligation_brl"], 0)
        self.assertLess(result["conditional_profit_before_unknown_expenses_brl"], 0)

    def test_unsettled_sale_not_available_and_d3_calendar(self):
        r = run_case()
        self.assertEqual(r["cash_timeline"][1]["date"], "2018-01-05")
        sale = r["cash_timeline"][2]
        self.assertEqual(sale["cash_available"], r["residual_cash_brl"])
        self.assertEqual(sale["etf_units"], 0)
        self.assertGreater(sale["sale_receivable"], sale["cash_available"])

    def test_d2_calendar_after_rule_change(self):
        records, _ = fixture()
        days = ["2026-03-30", "2026-03-31", "2026-04-01", "2026-04-02", "2026-04-06"]
        for row, day in zip(records, days):
            row["date"] = day
        r = run_case(records, days, entry_signal="2026-03-27", exit_signal="2026-03-31")
        self.assertEqual(r["cash_timeline"][1]["date"], "2026-04-01")
        self.assertEqual(r["cash_timeline"][-1]["date"], "2026-04-06")

    def test_future_exit_price_cannot_change_entry_quantity(self):
        records, days = fixture()
        baseline = run_case(records, days)
        records[-1].update(open=900, close=900, low=899, high=901)
        result = run_case(records, days)
        self.assertEqual(result["units"], baseline["units"])
        self.assertEqual(result["tax_basis_brl"], baseline["tax_basis_brl"])

    def test_exit_close_cannot_enter_open_sale_curve(self):
        records, days = fixture()
        baseline = run_case(records, days)
        records[-1].update(close=900, high=901)
        self.assertEqual(run_case(records, days)["equity_curve"], baseline["equity_curve"])

    def test_worst_mode_sizes_at_adverse_buy_and_sells_at_adverse_exit(self):
        records, days = fixture()
        records[0].update(close=110, high=111)
        records[-1].update(close=115, low=114)
        r = run_case(records, days, mode="worst_open_close")
        self.assertEqual((r["buy_reference_brl"], r["sell_reference_brl"]), (110, 115))
        self.assertGreaterEqual(r["residual_cash_brl"], 0)

    def test_decision_on_execution_day_is_rejected(self):
        with self.assertRaises(ValueError):
            run_case(entry_signal="2018-01-02")
        with self.assertRaises(ValueError):
            run_case(exit_signal="2018-01-04")

    def test_missing_internal_price_is_not_skipped(self):
        records, days = fixture()
        with self.assertRaises(ValueError):
            run_case([records[0], records[-1]], days)

    def test_wrong_identity_or_price_basis_is_rejected(self):
        for key, value in [("isin", "OTHER"), ("quote_factor", 1000), ("currency", "USD")]:
            records, days = fixture()
            records[1][key] = value
            with self.assertRaises(ValueError):
                run_case(records, days)

    def test_bad_ohlc_and_nonfinite_are_rejected(self):
        for value in [-1, float("nan"), float("inf")]:
            records, days = fixture()
            records[1]["close"] = value
            with self.assertRaises(ValueError):
                run_case(records, days)

    def test_empty_and_no_affordable_lot_rejected(self):
        with self.assertRaises(ValueError):
            run_case(records=[])
        with self.assertRaises(ValueError):
            run_case(capital=100)

    def test_expenses_and_forecast_stay_unknown(self):
        r = run_case()
        self.assertIsNone(r["fully_net_executable_profit_brl"])
        self.assertIsNone(r["unknown_additional_expenses_brl"])
        self.assertIsNone(r["expected_future_profit_brl"])
        self.assertFalse(r["event_inventory_certified"])

    def test_calendar_attribution_and_drawdown_reconcile(self):
        r = run_case()
        self.assertAlmostEqual(sum(r["calendar_year_pnl_brl"].values()),
                               r["conditional_profit_before_unknown_expenses_brl"])
        self.assertGreater(r["max_marked_drawdown"], 0.4)
        self.assertEqual(r["largest_marked_loss_from_initial_brl"], 4516.20)

    def test_duplicate_and_unsorted_quotes_rejected(self):
        records, days = fixture()
        with self.assertRaises(ValueError):
            run_case([records[0], records[1], copy.deepcopy(records[1]), records[2]], days)
        with self.assertRaises(ValueError):
            validate_quotes(list(reversed(records)), days, records[0]["date"], records[-1]["date"], "BRBOVACTF003")

    def test_money_rounding_half_up(self):
        self.assertEqual(cents("1.005"), Decimal("1.01"))

    def test_rate_and_capital_validation(self):
        for options in [{"capital": True}, {"capital": -1}, {"rate": -1}, {"tax_rate": 2}, {"lot": True}]:
            with self.assertRaises(ValueError):
                run_case(**options)

    def test_selic_percent_daily_not_annual(self):
        data = [{"data": "02/01/2018", "valor": "0.1"}, {"data": "03/01/2018", "valor": "0.2"}]
        r = selic_reference(data, fixture()[1], "2018-01-02", "2018-01-04")
        self.assertAlmostEqual(r["gross_factor"], 1.001 * 1.002)
        with self.assertRaises(ValueError):
            selic_reference(data[:1], fixture()[1], "2018-01-02", "2018-01-04")


if __name__ == "__main__":
    unittest.main()
