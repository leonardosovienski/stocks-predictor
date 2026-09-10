"""Non-circular failure cases for streaming source ingestion (stdlib runnable)."""
import sqlite3
from pathlib import Path
import tempfile
import unittest

from stocks_predictor import cotahist


def connection():
    conn = sqlite3.connect(':memory:')
    conn.executescript('''
        CREATE TABLE prices_raw(date TEXT NOT NULL, ticker TEXT NOT NULL,
          bdi_code TEXT NOT NULL, market_type TEXT NOT NULL, open REAL, high REAL,
          low REAL, close REAL CHECK(close>0), volume_fin REAL, qty INTEGER,
          quote_factor INTEGER, source_file TEXT NOT NULL,
          UNIQUE(date,ticker,source_file));
        CREATE TABLE unrelated(value INTEGER);
    ''')
    return conn


def line(ticker='TEST3', close=10):
    return cotahist._pack('2024-01-02', ticker, '02', '010', 10, 11, 9, close, 100, 1000, 1)


class IngestionIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.conn = connection()
        self.addCleanup(self.conn.close)

    def load(self, records):
        return cotahist.load_prices(self.conn, records, 'source.txt')

    def test_idempotent_replay_reports_zero_new_rows(self):
        self.assertEqual(self.load([line()]), 1)
        self.assertEqual(self.load([line()]), 0)

    def test_duplicates_in_one_source_report_actual_insertions(self):
        self.assertEqual(self.load([line(), line()]), 1)

    def test_changed_source_content_is_rejected_without_overwrite(self):
        self.load([line()])
        with self.assertRaisesRegex(ValueError, 'conflict'):
            self.load([line('NEW3'), line(close=11)])
        self.assertEqual(self.conn.execute('SELECT ticker,close FROM prices_raw').fetchall(), [('TEST3', 10)])

    def test_conflicting_duplicates_inside_one_batch_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'conflict'):
            self.load([line(), line(close=11)])
        self.assertEqual(self.conn.execute('SELECT count(*) FROM prices_raw').fetchone()[0], 0)

    def test_success_keeps_callers_transaction_uncommitted(self):
        self.conn.execute('INSERT INTO unrelated VALUES(1)')
        self.load([line()])
        self.conn.rollback()
        self.assertEqual(self.conn.execute('SELECT count(*) FROM unrelated').fetchone()[0], 0)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM prices_raw').fetchone()[0], 0)

    def test_constraint_failure_rolls_back_all_new_rows_and_preserves_caller(self):
        self.conn.execute('INSERT INTO unrelated VALUES(1)')
        with self.assertRaises(sqlite3.IntegrityError):
            self.load([line('GOOD3'), line('BAD3', close=0)])
        self.assertEqual(self.conn.execute('SELECT count(*) FROM prices_raw').fetchone()[0], 0)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM unrelated').fetchone()[0], 1)
        self.assertTrue(self.conn.in_transaction)

    def test_late_stream_failure_leaves_no_partial_ingestion(self):
        def broken():
            for i in range(1500):
                yield line(f'T{i:06}')
            raise OSError('truncated source stream')
        with self.assertRaises(OSError):
            self.load(broken())
        self.assertEqual(self.conn.execute('SELECT count(*) FROM prices_raw').fetchone()[0], 0)
        self.assertFalse(self.conn.in_transaction)

    def test_source_identity_is_required(self):
        with self.assertRaises(ValueError):
            cotahist.load_prices(self.conn, [line()], '   ')

    def test_conflicting_duplicate_across_batches_rolls_back_every_batch(self):
        records = [line(f'T{i:06}') for i in range(1500)]
        records.append(line('T000000', close=11))
        with self.assertRaisesRegex(ValueError, 'conflict'):
            self.load(records)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM prices_raw').fetchone()[0], 0)
        self.assertFalse(self.conn.in_transaction)

    def test_busy_commit_leaves_no_pending_ingestion(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'locked.db'
            writer = sqlite3.connect(path, timeout=0)
            self.conn.backup(writer)
            reader = sqlite3.connect(path, timeout=0)
            try:
                reader.execute('BEGIN')
                reader.execute('SELECT * FROM prices_raw').fetchall()
                with self.assertRaises(sqlite3.OperationalError):
                    cotahist.load_prices(writer, [line()], 'source.txt')
                self.assertFalse(writer.in_transaction)
                self.assertEqual(writer.execute('SELECT count(*) FROM prices_raw').fetchone()[0], 0)
            finally:
                reader.close()
                writer.close()

    def test_malformed_neighbor_keeps_valid_row_and_warning(self):
        with self.assertLogs(cotahist.logger, level='WARNING'):
            self.assertEqual(self.load([line(), line()[:50]]), 1)

    def test_only_nonspot_records_are_valid_but_filtered(self):
        other = cotahist._pack('2024-01-02', 'OPT1', '78', '070', 1, 1, 1, 1, 10, 10, 1)
        self.assertEqual(self.load([other]), 0)
        self.assertFalse(self.conn.in_transaction)


if __name__ == '__main__':
    unittest.main()
