import sqlite3
import unittest

from stocks_predictor import universe
from stocks_predictor.validation import iso_day, positive_integer


class InputContractTests(unittest.TestCase):
    def test_date_requires_canonical_calendar_form(self):
        for bad in ('20240201', '2024-02-30', '2024-1-2', None):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                iso_day(bad)
        self.assertEqual(iso_day('2024-02-29'), '2024-02-29')

    def test_boolean_fractional_and_nonpositive_counts_rejected(self):
        for bad in (True, 0, -1, 1.5):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                positive_integer(bad, 'count')

    def test_invalid_universe_parameters_fail_before_sql(self):
        conn = sqlite3.connect(':memory:')
        self.addCleanup(conn.close)
        for kw in ({'lookback':0}, {'min_history':-1}, {'lookback':True}):
            with self.subTest(kw=kw), self.assertRaises(ValueError):
                universe.rank_universe(conn, '2024-01-02', **kw)
        for select in (universe.select_universe, universe.legacy_select_universe, universe.materialize_snapshot):
            with self.subTest(select=select.__name__), self.assertRaises(ValueError):
                select(conn, '2024-01-02', top_n=-1)


if __name__ == '__main__':
    unittest.main()
