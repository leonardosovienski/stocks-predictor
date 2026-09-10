"""Regression evidence from the integral audit; entirely synthetic, no Core."""
import sqlite3
import unittest

from stocks_predictor import cotahist, economic_gate, universe
from stocks_predictor.source_closure import source_counts


class QuoteContractTests(unittest.TestCase):
    def setUp(self):
        self.line = cotahist._pack('2024-01-02', 'TEST3', '02', '010', 10, 11, 9, 10, 1000, 10000, 1)

    def test_impossible_calendar_date_rejected(self):
        with self.assertRaises(ValueError):
            cotahist.parse_line(self.line[:2] + '20240231' + self.line[10:])

    def test_truncated_and_oversized_quotes_rejected(self):
        for line in (self.line[:217], self.line + 'X'):
            with self.subTest(length=len(line)), self.assertRaises(ValueError):
                cotahist.parse_line(line)

    def test_nonpositive_quote_basis_rejected(self):
        with self.assertRaises(ValueError):
            cotahist.parse_line(self.line[:210] + '0000000' + self.line[217:])

    def test_malformed_quote_is_counted_without_losing_valid_neighbor(self):
        records, bad = cotahist.parse_lines([self.line, self.line[:2] + '20240231' + self.line[10:]])
        self.assertEqual((len(records), bad), (1, 1))
        self.assertEqual(records[0]['date'], '2024-01-02')


class EconomicInputTests(unittest.TestCase):
    def test_missing_observations_are_not_silently_removed(self):
        with self.assertRaises(ValueError):
            economic_gate.estimate_edge([0.01, float('nan'), 0.02], minimum_observations=2)

    def test_nonfinite_costs_and_hurdles_cannot_produce_a_decision(self):
        for value in [float('nan'), float('inf')]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                economic_gate.decide_rebalance(None, value)
            with self.subTest(hurdle=value), self.assertRaises(ValueError):
                economic_gate.decide_rebalance(None, 0.01, minimum_net_edge=value)

    def test_nonfinite_policy_is_rejected(self):
        with self.assertRaises(ValueError):
            economic_gate.EconomicRebalanceGate(z_score=float('nan'))

    def test_invalid_external_edge_estimate_is_rejected(self):
        with self.assertRaises(ValueError):
            economic_gate.decide_rebalance(economic_gate.EdgeEstimate(0.01, float('inf'), 12), 0.01)


class UniverseEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        self.addCleanup(self.conn.close)
        self.conn.executescript('''
            CREATE TABLE prices_raw(date TEXT, ticker TEXT, market_type TEXT, volume_fin REAL);
            CREATE TABLE quarantine(ticker TEXT, date TEXT, resolved_at TEXT);
            CREATE TABLE universe_snapshots(asof_date TEXT, ticker TEXT, median_vol REAL,
                rank INTEGER, PRIMARY KEY(asof_date,ticker));
        ''')
        for day in ('2024-01-02', '2024-01-03', '2024-01-04'):
            self.conn.executemany('INSERT INTO prices_raw VALUES(?,?,?,?)',
                                 [(day, 'AAAA3', '010', 100), (day, 'BBBB3', '010', 200)])
        self.conn.commit()

    def snapshot(self):
        return universe.materialize_snapshot(self.conn, '2024-01-05', 1, 2, 2)

    def test_future_resolution_cannot_reopen_past_universe(self):
        self.conn.execute("INSERT INTO quarantine VALUES('BBBB3','2024-01-02','2025-01-01')")
        self.assertEqual(universe.select_universe(self.conn, '2024-01-05', 2, 2, 2), ['AAAA3'])

    def test_resolution_before_cutoff_reopens_instrument(self):
        self.conn.execute("INSERT INTO quarantine VALUES('BBBB3','2024-01-02','2024-01-04 12:00:00')")
        self.assertEqual(universe.select_universe(self.conn, '2024-01-05', 2, 2, 2), ['BBBB3', 'AAAA3'])

    def test_same_day_resolution_is_outside_strict_before_cutoff(self):
        self.conn.execute("INSERT INTO quarantine VALUES('BBBB3','2024-01-02','2024-01-05 09:00:00')")
        self.assertEqual(universe.select_universe(self.conn, '2024-01-05', 2, 2, 2), ['AAAA3'])

    def test_snapshot_conflict_fails_without_appending_members(self):
        self.assertEqual(self.snapshot(), ['BBBB3'])
        before = self.conn.execute('SELECT * FROM universe_snapshots').fetchall()
        self.conn.execute("UPDATE prices_raw SET volume_fin=500 WHERE ticker='AAAA3'")
        with self.assertRaises(ValueError):
            self.snapshot()
        self.assertEqual(self.conn.execute('SELECT * FROM universe_snapshots').fetchall(), before)

    def test_same_members_with_changed_evidence_cannot_rewrite_snapshot(self):
        self.snapshot()
        self.conn.execute("UPDATE prices_raw SET volume_fin=500 WHERE ticker='BBBB3'")
        with self.assertRaises(ValueError):
            self.snapshot()
        self.assertEqual(self.conn.execute('SELECT median_vol FROM universe_snapshots').fetchone()[0], 200)

    def test_identical_snapshot_is_idempotent(self):
        self.assertEqual(self.snapshot(), self.snapshot())
        self.assertEqual(self.conn.execute('SELECT count(*) FROM universe_snapshots').fetchone()[0], 1)

    def test_legacy_replay_keeps_latest_resolution_policy_explicitly(self):
        self.conn.execute("INSERT INTO quarantine VALUES('BBBB3','2024-01-02','2025-01-01')")
        self.assertEqual(universe.legacy_select_universe(self.conn, '2024-01-05', 2, 2, 2), ['BBBB3', 'AAAA3'])

    def test_snapshot_does_not_commit_callers_transaction(self):
        self.conn.execute("UPDATE prices_raw SET volume_fin=250 WHERE ticker='BBBB3'")
        self.snapshot()
        self.conn.rollback()
        self.assertEqual(self.conn.execute('SELECT count(*) FROM universe_snapshots').fetchone()[0], 0)
        self.assertEqual(self.conn.execute("SELECT volume_fin FROM prices_raw WHERE ticker='BBBB3'").fetchone()[0], 200)

    def test_empty_snapshot_fails_without_partial_rows(self):
        with self.assertRaises(ValueError):
            universe.materialize_snapshot(self.conn, '2024-01-01', 1, 2, 2)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM universe_snapshots').fetchone()[0], 0)

    def test_unknown_source_does_not_become_primary_by_default(self):
        result = source_counts({'unknown.json': {'sha256': '0' * 64}})
        self.assertEqual(result['verified_primary_files'], 0)
        self.assertEqual(result['unclassified_source_files'], 1)


if __name__ == '__main__':
    unittest.main()
