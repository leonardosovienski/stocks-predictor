"""Atomicity, conflict and temporal boundaries for R7 additions; stdlib runnable."""
from contextlib import closing
import dataclasses
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest
import zipfile

from stocks_predictor import cotahist
from stocks_predictor.source_catalog import ingest_version
from stocks_predictor.temporal_evidence import DatedOutcome, estimate_asof

SCHEMA = '''CREATE TABLE prices_raw(date TEXT, ticker TEXT, bdi_code TEXT,
market_type TEXT, open REAL, high REAL, low REAL, close REAL, volume_fin REAL,
qty INTEGER, quote_factor INTEGER, source_file TEXT, UNIQUE(date,ticker,source_file))'''


class VersionedSources(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.conn = sqlite3.connect(':memory:')
        self.addCleanup(self.conn.close)
        self.conn.execute(SCHEMA)
        self.archive = self.root / 'source.zip'
        self.good = cotahist._pack('2024-01-02', 'TEST3', '02', '010', 10, 11, 9, 10, 100, 1000, 1)
        self.pack([self.good])

    def pack(self, lines):
        with zipfile.ZipFile(self.archive, 'w') as zipped:
            zipped.writestr('COTAHIST.TXT', '\n'.join(lines))

    def load(self, version='2024-v1', archive=None):
        return ingest_version(self.conn, archive or self.archive, publisher='B3', dataset='COTAHIST',
                              version=version, source_url='https://example.invalid/source',
                              observed_at='2026-09-10T12:00:00Z', scratch_dir=self.root)

    def test_renamed_identical_source_replays_and_preserves_first_observation(self):
        first = self.load()
        renamed = self.root / 'renamed.zip'
        shutil.copyfile(self.archive, renamed)
        second = self.load(archive=renamed)
        self.assertEqual((first['inserted'], second['inserted']), (1, 0))
        self.assertEqual(first['source_id'], second['source_id'])
        self.assertEqual(self.conn.execute('SELECT COUNT(*) FROM source_versions').fetchone()[0], 1)

    def test_changed_excluded_content_conflicts_but_new_version_keeps_prior(self):
        first = self.load()
        option = cotahist._pack('2024-01-02', 'OPT1', '78', '070', 1, 2, 1, 1, 1, 1, 1)
        self.pack([self.good, option])
        with self.assertRaisesRegex(ValueError, 'conflicting content'):
            self.load()
        second = self.load(version='2024-v2')
        self.assertNotEqual(first['source_id'], second['source_id'])
        self.assertEqual(self.conn.execute('SELECT COUNT(*) FROM source_versions').fetchone()[0], 2)

    def test_malformed_line_after_committed_batches_rolls_back_catalog_and_prices(self):
        lines = [cotahist._pack('2024-01-02', f'T{i}', '02', '010', 10, 11, 9, 10, 1, 10, 1) for i in range(1100)]
        self.pack(lines + ['01broken'])
        with self.assertRaises(ValueError):
            self.load()
        self.assertFalse(self.conn.in_transaction)
        self.assertEqual(self.conn.execute('SELECT COUNT(*) FROM prices_raw').fetchone()[0], 0)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE name='source_versions'").fetchone()[0], 0)

    def test_caller_transaction_is_not_committed(self):
        self.conn.execute('CREATE TABLE caller (value INTEGER)')
        self.conn.execute('INSERT INTO caller VALUES (1)')
        self.load()
        self.assertTrue(self.conn.in_transaction)
        self.conn.rollback()
        self.assertEqual(self.conn.execute('SELECT COUNT(*) FROM prices_raw').fetchone()[0], 0)

    def test_malformed_failure_preserves_callers_prior_write(self):
        self.conn.execute('CREATE TABLE caller (value INTEGER)')
        self.conn.execute('INSERT INTO caller VALUES (1)')
        self.pack([self.good, '01broken'])
        with self.assertRaises(ValueError):
            self.load()
        self.assertEqual(self.conn.execute('SELECT COUNT(*) FROM caller').fetchone()[0], 1)
        self.assertTrue(self.conn.in_transaction)

    def test_failed_outer_commit_releases_writer(self):
        path = self.root / 'locks.sqlite'
        with closing(sqlite3.connect(path, timeout=0)) as writer, closing(sqlite3.connect(path, timeout=0)) as reader:
            writer.execute(SCHEMA)
            reader.execute('BEGIN')
            reader.execute('SELECT * FROM prices_raw').fetchall()
            with self.assertRaises(sqlite3.OperationalError):
                ingest_version(writer, self.archive, publisher='B3', dataset='COTAHIST', version='v1',
                               source_url='https://example.invalid/source', observed_at='2026-09-10T12:00:00Z', scratch_dir=self.root)
            self.assertFalse(writer.in_transaction)
            reader.rollback()
            self.assertEqual(writer.execute('SELECT COUNT(*) FROM prices_raw').fetchone()[0], 0)


class TemporalEvidence(unittest.TestCase):
    def setUp(self):
        self.row = DatedOutcome('a', '2026-01-01T00:00:00Z', '2026-02-01T00:00:00Z',
                                '2026-02-02T00:00:00Z', 0.01)

    def test_future_same_instant_and_duplicate_evidence_rejected(self):
        for cutoff in ('2026-02-01T00:00:00Z', '2026-02-02T00:00:00Z'):
            with self.subTest(cutoff=cutoff), self.assertRaises(ValueError):
                estimate_asof([self.row], cutoff)
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            estimate_asof([self.row, self.row], '2026-03-01T00:00:00Z')

    def test_invalid_chronology_naive_timestamp_and_nonfinite_rejected(self):
        for changed in ({'observed_at': '2026-01-10T00:00:00Z'}, {'decision_at': self.row.matured_at},
                        {'observed_at': '2026-02-02'}, {'gross_edge': float('inf')}):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                dataclasses.replace(self.row, **changed).validate()

    def test_offset_normalization_and_eligible_arithmetic(self):
        second = dataclasses.replace(self.row, observation_id='b', gross_edge=0.03,
                                     observed_at='2026-02-01T21:00:00-03:00')
        result = estimate_asof([self.row, second], '2026-02-02T00:00:01Z', minimum_observations=2, z_score=0)
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result.mean_gross_edge, 0.02)


if __name__ == '__main__':
    unittest.main()
