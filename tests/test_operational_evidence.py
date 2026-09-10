"""Current code must not inherit an obsolete historical code attestation."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import verify_operational_evidence as evidence


class OperationalEvidenceTests(unittest.TestCase):
    def test_current_complete_evidence(self):
        self.assertEqual(evidence.verify()['real_rows'], 55986)

    def test_code_mutation_or_omission_is_detected_before_run_receipts(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / 'code.py'
            path.write_text('before\n', encoding='utf-8')
            record = {'current_code_sha256_lf': [{'path': 'code.py', 'sha256': evidence.canonical_sha(path)}]}
            registry = root / evidence.REGISTRY
            registry.parent.mkdir(parents=True)
            registry.write_text(json.dumps(record), encoding='utf-8')
            path.write_text('after\n', encoding='utf-8')
            with patch.object(evidence, 'code_paths', return_value={'code.py'}):
                with self.assertRaisesRegex(ValueError, 'code changed'):
                    evidence.verify(root)
            with patch.object(evidence, 'code_paths', return_value={'code.py', 'missing.py'}):
                with self.assertRaisesRegex(ValueError, 'population'):
                    evidence.verify(root)


if __name__ == '__main__':
    unittest.main()
