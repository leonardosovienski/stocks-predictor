"""Historical annualization must never be serialized or printed as a forecast."""
import unittest

from stocks_predictor import economics


class EconomicEvidenceLabels(unittest.TestCase):
    def setUp(self):
        self.cfg = {"economics": {"capital_brl": 10000, "min_annual_net_profit_brl": 1,
                                   "max_acceptable_drawdown": 0.5}}

    def test_no_forecast_value_from_historical_returns(self):
        _, _, detail = economics.classify(economics.screen([0.001] * 252), self.cfg)
        self.assertIsNone(detail["expected_annual_profit_brl"])
        self.assertGreater(detail["historical_annualized_profit_equivalent_brl"], 0)

    def test_summary_explicitly_historical(self):
        line = economics.summary_line([0.001] * 252, self.cfg)
        self.assertNotIn("lucro anual esperado", line)
        self.assertIn("histórico", line)
        self.assertIn("não é previsão", line)

    def test_classification_keeps_historical_minimum_comparison(self):
        state, _, detail = economics.classify(economics.screen([0.001] * 252), self.cfg)
        self.assertEqual(state, economics.ACIMA_DO_MINIMO)
        self.assertEqual(detail["forecast_status"], "NOT_ESTIMATED")


if __name__ == "__main__":
    unittest.main()
