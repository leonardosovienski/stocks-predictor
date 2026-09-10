"""Real SQLite/process failures, offline CLI boundaries and snapshot recovery."""
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import zipfile

from stocks_predictor import cotahist, operational_store as store, operations

ROOT = Path(__file__).resolve().parents[1]


class OperationalTests(unittest.TestCase):
    def setUp(self):
        # Respect project-local scratch when running on the user's Windows host.
        self.folder = tempfile.TemporaryDirectory(dir=os.getenv('STOCKS_TEST_TMP'))
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.db = self.root / 'research.sqlite'
        store.initialize(self.db)
        self.archive = self.root / 'source.zip'
        self.make_archive(1101)

    def make_archive(self, count, suffix=''):
        with zipfile.ZipFile(self.archive, 'w') as zipped:
            lines = [cotahist._pack('2024-01-02', f'T{i}', '02', '010', 10, 11, 9, 10, 100, 1000, 1)
                     for i in range(count)]
            zipped.writestr('COTAHIST.TXT', '\n'.join(lines) + suffix)

    def kwargs(self, version='v1'):
        return dict(publisher='B3', dataset='fixture', version=version,
                    source_url='https://example.invalid/source.zip', observed_at='2026-09-10T10:00:00Z',
                    expected_sha256=store.file_sha256(self.archive), scratch_dir=self.root)

    def load(self, version='v1'):
        return store.ingest(self.db, self.archive, **self.kwargs(version))

    def test_version_isolation_replay_and_append_only(self):
        self.assertEqual(self.load()['inserted'], 1101)
        self.assertEqual(self.load()['inserted'], 0)
        self.make_archive(1102)
        with self.assertRaisesRegex(ValueError, 'conflicting content'):
            self.load()
        self.load('v2')
        report = store.inspect(self.db)
        self.assertEqual(sorted(row['rows'] for row in report['sources']), [1101, 1102])
        self.assertFalse(report['capital_enabled'])
        with store.writer(self.db) as conn:
            for table in ('prices_raw', 'source_versions'):
                with self.subTest(table=table), self.assertRaises(sqlite3.IntegrityError):
                    conn.execute('DELETE FROM ' + table)
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute('UPDATE prices_raw SET close=1')

    def test_hash_is_checked_on_snapshot_and_malformed_tail_rolls_back(self):
        params = self.kwargs()
        self.make_archive(1102)
        with self.assertRaisesRegex(ValueError, 'snapshot differs'):
            store.ingest(self.db, self.archive, **params)
        self.assertEqual(store.inspect(self.db)['stored_rows'], 0)
        self.make_archive(1101, '\n01broken')
        with self.assertRaises(ValueError):
            self.load()
        self.assertEqual(store.inspect(self.db)['sources'], [])

    def test_snapshot_restores_committed_wal_and_rejects_reuse(self):
        with closing(sqlite3.connect(self.db)) as keeper:
            keeper.execute('PRAGMA wal_autocheckpoint=0')
            keeper.execute('BEGIN')
            keeper.execute('SELECT COUNT(*) FROM prices_raw').fetchone()
            self.load()
            self.assertGreater(Path(str(self.db) + '-wal').stat().st_size, 0)
            before = store.inspect(self.db)
            manifest = store.snapshot(self.db, self.root / 'backup')
            self.assertEqual(manifest['inspection'], before)
            self.load('v2')
            store.restore(self.root / 'backup', self.root / 'restored')
            self.assertEqual(store.inspect(self.root / 'restored/research.sqlite'), before)
        for action in (lambda: store.initialize(self.db),
                       lambda: store.snapshot(self.db, self.root / 'backup'),
                       lambda: store.restore(self.root / 'backup', self.root / 'restored')):
            with self.assertRaises(FileExistsError):
                action()
        # Restored store is writable and retains its old source after a new append.
        store.ingest(self.root / 'restored/research.sqlite', self.archive, **self.kwargs('v3'))
        self.assertEqual(store.inspect(self.root / 'restored/research.sqlite')['stored_rows'], 2202)

    def test_corrupt_backup_and_incomplete_artifacts_are_refused(self):
        self.load()
        store.snapshot(self.db, self.root / 'backup')
        with (self.root / 'backup/snapshot.sqlite').open('ab') as stream:
            stream.write(b'corrupt')
        with self.assertRaisesRegex(ValueError, 'SHA-256'):
            store.restore(self.root / 'backup', self.root / 'badrestore')
        self.assertTrue((self.root / 'badrestore/INCOMPLETE.json').is_file())
        self.assertFalse((self.root / 'badrestore/research.sqlite').exists())
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            store.inspect(self.root / 'badrestore/research.sqlite.partial')
        (self.root / 'backup/INCOMPLETE.json').write_text('{}', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            store.restore(self.root / 'backup', self.root / 'unused')
        self.assertFalse((self.root / 'unused').exists())

    def test_snapshot_manifest_write_failure_never_publishes_ready_backup(self):
        original = store._write_json

        def disk_full(path, value):
            if path.name == 'manifest.json':
                raise OSError('simulated disk full')
            original(path, value)

        with patch.object(store, '_write_json', side_effect=disk_full), self.assertRaises(OSError):
            store.snapshot(self.db, self.root / 'failed')
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            store.restore(self.root / 'failed', self.root / 'unused')
        self.assertEqual(store.inspect(self.db)['stored_rows'], 0)

    def test_backup_timeout_is_incomplete_and_source_is_intact(self):
        self.load()
        with patch.object(store.time, 'monotonic', side_effect=[0, 100]), self.assertRaises(TimeoutError):
            store.snapshot(self.db, self.root / 'timeout', timeout=1)
        self.assertTrue((self.root / 'timeout/INCOMPLETE.json').exists())
        self.assertEqual(store.inspect(self.db)['stored_rows'], 1101)

    def test_wrong_schema_missing_file_orphan_and_bad_timeout_fail_closed(self):
        for timeout in (0, -1, float('nan'), float('inf'), 3601, True):
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                with store.writer(self.db, timeout=timeout):
                    pass
        with self.assertRaises(FileNotFoundError):
            store.inspect(self.root / 'missing.sqlite')
        self.assertFalse((self.root / 'missing.sqlite').exists())
        self.load()
        with closing(sqlite3.connect(self.db)) as conn:
            conn.execute("INSERT INTO prices_raw SELECT '2024-01-03',ticker,bdi_code,market_type,open,high,low,close,volume_fin,qty,quote_factor,'missing' FROM prices_raw LIMIT 1")
            conn.commit()
        with self.assertRaisesRegex(ValueError, 'references'):
            store.inspect(self.db)
        with closing(sqlite3.connect(self.db)) as conn:
            conn.execute('DROP TRIGGER prices_raw_no_delete')
        with self.assertRaisesRegex(ValueError, 'schema differs'):
            store.inspect(self.db)

    def cli_args(self, version='v1'):
        return ['ingest', '--db', str(self.db), '--archive', str(self.archive),
                '--publisher', 'B3', '--dataset', 'fixture', '--version', version,
                '--source-url', 'https://example.invalid/source.zip', '--observed-at', '2026-09-10T10:00:00Z',
                '--sha256', store.file_sha256(self.archive), '--scratch-dir', str(self.root)]

    def process(self, code, *args):
        return subprocess.Popen([sys.executable, '-c', code, str(self.db), *args], cwd=ROOT,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def reap(self, proc):
        if proc.poll() is None:
            proc.kill()
        return proc.communicate(timeout=10)

    def test_concurrent_process_replays_serialize_without_duplicates(self):
        processes = [subprocess.Popen([sys.executable, '-m', 'stocks_predictor', *self.cli_args(),
                                      '--timeout', '20'], cwd=ROOT, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, text=True) for _ in range(3)]
        for proc in processes:
            self.addCleanup(self.reap, proc)
        outputs = []
        for proc in processes:
            out, err = proc.communicate(timeout=30)
            self.assertEqual(proc.returncode, 0, err)
            outputs.append(json.loads(out)['inserted'])
        self.assertEqual(sorted(outputs), [0, 0, 1101])
        self.assertEqual(store.inspect(self.db)['stored_rows'], 1101)

    def test_crashed_writer_rolls_back_and_reader_and_backup_see_committed_snapshot(self):
        self.load()
        before = store.inspect(self.db)
        ready = self.root / 'writer-ready'
        code = '''import sys,time
from pathlib import Path
from stocks_predictor import operational_store as store
with store.writer(Path(sys.argv[1])) as c:
    c.execute("INSERT INTO prices_raw SELECT '2024-01-03',ticker,bdi_code,market_type,open,high,low,close,volume_fin,qty,quote_factor,source_file FROM prices_raw")
    Path(sys.argv[2]).write_text('ready',encoding='utf-8')
    time.sleep(30)
'''
        proc = self.process(code, str(ready))
        self.addCleanup(self.reap, proc)
        deadline = time.monotonic() + 10
        while not ready.exists() and proc.poll() is None and time.monotonic() < deadline:
            time.sleep(0.02)
        self.assertTrue(ready.exists(), 'child did not acquire transaction')
        self.assertEqual(store.inspect(self.db), before)
        self.assertEqual(store.snapshot(self.db, self.root / 'during-write')['inspection'], before)
        started = time.monotonic()
        with self.assertRaises(sqlite3.OperationalError):
            with store.writer(self.db, timeout=0.15):
                pass
        self.assertLess(time.monotonic() - started, 3)
        proc.kill()
        proc.communicate(timeout=10)
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(store.inspect(self.db), before)
        self.assertEqual(self.load('v2')['inserted'], 1101)

    def test_cli_json_errors_and_personal_and_temporal_controls(self):
        profile = self.root / 'profile.json'
        profile.write_text('{"capital_brl":"5000"}', encoding='utf-8')
        result = operations._profile(profile, 2)
        self.assertEqual(result['status'], 'INCOMPLETE_PERSONAL_SCENARIO')
        self.assertFalse(result['capital_enabled'])
        for content in ('{"capital_brl":null}', '{"capital_brl":true}',
                        '{"capital_brl":5000,"capital_brl":2}', '{"capital_brl":NaN}',
                        '{"capital_brl":5000,"unexpected":2}', '{"capital_brl":5000,"horizon_months":true}'):
            profile.write_text(content, encoding='utf-8')
            with self.subTest(content=content), self.assertRaises((ValueError, TypeError)):
                operations._profile(profile, 2)
        outcomes = self.root / 'outcomes.json'
        row = dict(observation_id='one', decision_at='2024-01-01T00:00:00Z',
                   matured_at='2024-02-01T00:00:00Z', observed_at='2024-02-02T00:00:00Z', gross_edge=0.01)
        outcomes.write_text(json.dumps([row]), encoding='utf-8')
        self.assertEqual(operations._evidence(outcomes, '2024-03-01T00:00:00Z', 2)['status'], 'INSUFFICIENT_EVIDENCE')
        with self.assertRaisesRegex(ValueError, 'strictly before'):
            operations._evidence(outcomes, row['observed_at'], 2)
        with patch.object(sys, 'stderr'), patch.object(sys, 'stdout'):
            self.assertEqual(operations.main(['profile', '--input', str(profile)]), 2)
            self.assertEqual(operations.main(['evidence', '--input', str(outcomes), '--asof', '2024-03-01T00:00:00Z']), 0)
            bad = self.cli_args()
            bad[bad.index('--sha256') + 1] = '0' * 64
            self.assertEqual(operations.main(bad), 2)
        self.assertEqual(store.inspect(self.db)['stored_rows'], 0)

    def test_legacy_refuses_managed_store_before_migration(self):
        try:
            from stocks_predictor import db
        except ModuleNotFoundError as exc:
            if exc.name and exc.name.startswith('predictor_core'):
                self.skipTest('production Core available only in Linux CI')
            raise
        identity = hashlib.sha256(self.db.read_bytes()).hexdigest()
        with patch.object(db.infra, 'run_migrations', side_effect=AssertionError('migration attempted')):
            for connect in (db.get_connection, db.get_readonly_connection):
                with self.assertRaisesRegex(ValueError, 'legacy access refused'):
                    connect(self.db)
        self.assertEqual(hashlib.sha256(self.db.read_bytes()).hexdigest(), identity)


if __name__ == '__main__':
    unittest.main()
