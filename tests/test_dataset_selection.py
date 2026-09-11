from dataclasses import replace
import os
from pathlib import Path
import tempfile
import unittest

from stocks_predictor import operational_store as store
from stocks_predictor.dataset_selection import DatasetSelection, materialize, simulate_selected


class DatasetSelectionTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(dir=os.getenv('STOCKS_TEST_TMP'))
        self.addCleanup(self.folder.cleanup)
        self.db = Path(self.folder.name) / 'synthetic.sqlite'
        store.initialize(self.db)
        with store.writer(self.db) as conn:
            for source, opening, observed in (('a', 10, '2026-01-05T00:00:00Z'),
                                               ('b', 20, '2026-01-06T00:00:00Z')):
                conn.execute('INSERT INTO source_versions VALUES (?,?,?,?,?,?,?,?,?)',
                             (source, 'synthetic', 'fixture', source, 'spot', '0'*64,
                              'https://example.invalid', 'fixture', observed))
                for day in ('2026-01-02', '2026-01-05'):
                    conn.execute('INSERT INTO prices_raw VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                                 (day, 'TEST3', '02', '010', opening, opening, opening, opening,
                                  100, 10, 1, source))
        self.selection = DatasetSelection(('a',), '2026-01-05T23:00:00Z', '2026-01-02', '2026-01-05')

    def test_exact_source_selection_and_no_store_writes(self):
        before = self.db.read_bytes()
        selected = materialize(self.db, self.selection)
        self.assertEqual(selected['bars']['TEST3']['2026-01-02'], (10, 10))
        self.assertEqual(selected, materialize(self.db, self.selection))
        self.assertEqual(before, self.db.read_bytes())

    def test_missing_and_future_version_are_rejected(self):
        for ids, message in ((('missing',), 'missing'), (('b',), 'after the cutoff')):
            with self.subTest(ids=ids), self.assertRaisesRegex(ValueError, message):
                materialize(self.db, replace(self.selection, source_ids=ids))

    def test_conflicting_versions_are_never_selected_implicitly(self):
        selection = replace(self.selection, source_ids=('a', 'b'), observed_before='2026-01-07T00:00:00Z')
        with self.assertRaisesRegex(ValueError, 'ambiguous normalized prices'):
            materialize(self.db, selection)

    def test_selected_prices_reach_causal_simulator(self):
        result = simulate_selected(self.db, self.selection, {'2026-01-02': {'TEST3': 1}},
                                   corporate_actions={'reference': 'synthetic-no-events',
                                                      'splits': {}, 'cash_events': {}, 'stock_events': {}})
        self.assertTrue(result['simulation']['executions'])
        self.assertFalse(result['capital_enabled'])
        self.assertEqual(len(result['inputs_sha256']), 64)


if __name__ == '__main__':
    unittest.main()
