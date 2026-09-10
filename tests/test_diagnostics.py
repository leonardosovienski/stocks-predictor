from contextlib import redirect_stdout
import hashlib
from importlib import metadata
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from stocks_predictor import diagnostics


class DiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_missing_database_is_not_created(self):
        missing = self.root / 'absent' / 'stocks.db'
        self.assertEqual(diagnostics.inspect_database(missing)['status'], 'missing')
        self.assertFalse(missing.parent.exists())

    def test_existing_database_is_unchanged(self):
        path = self.root / 'existing.db'
        conn = sqlite3.connect(path)
        conn.execute('CREATE TABLE prices(id INTEGER)')
        conn.commit()
        conn.close()
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        result = diagnostics.inspect_database(path)
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['tables'], ['prices'])
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), before)
        self.assertEqual(list(self.root.iterdir()), [path])

    def test_corrupt_file_returns_structured_error(self):
        path = self.root / 'corrupt.db'
        path.write_bytes(b'not SQLite')
        self.assertEqual(diagnostics.inspect_database(path)['status'], 'unreadable')
        self.assertEqual(path.read_bytes(), b'not SQLite')

    def test_missing_core_is_reported_without_import(self):
        with patch.object(diagnostics.metadata, 'version', side_effect=metadata.PackageNotFoundError):
            result = diagnostics.diagnose()
        self.assertEqual(result['dependencies']['predictor-core']['status'], 'missing')
        self.assertFalse(result['runtime_metadata_compatible'])
        self.assertEqual(result['database']['status'], 'not_requested')

    def test_supported_versions_and_incompatible_versions(self):
        for version, valid in [('3.2.0', True), ('3.3.0', True), ('3.1.9', False), ('4.0.0', False), ('3.2.0rc1', False)]:
            with self.subTest(version=version), patch.object(diagnostics.metadata, 'version', return_value=version):
                self.assertEqual(diagnostics._dependency('predictor-core', (3, 2), 4)['metadata_compatible'], valid)

    def test_check_exit_code_and_json(self):
        with patch.object(diagnostics, 'diagnose', return_value={
            'runtime_metadata_compatible': False, 'database': {'status': 'not_requested'}
        }), redirect_stdout(io.StringIO()) as output:
            self.assertEqual(diagnostics.main(['--check']), 1)
        self.assertFalse(json.loads(output.getvalue())['runtime_metadata_compatible'])


if __name__ == '__main__':
    unittest.main()
