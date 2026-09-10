from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from tools.audit_registry import DEFAULT, verify
from tools.reproducible_build import distribution_hashes


class AuditRegistryTests(unittest.TestCase):
    def test_population_loss_and_unsupported_closure_are_rejected(self):
        original = json.loads(DEFAULT.read_text(encoding='utf-8'))
        self.assertEqual(verify(original)['items'], 75)
        for kind in ('cash', 'corporate', 'finding', 'evidence', 'profit'):
            current = deepcopy(original)
            if kind == 'cash':
                current['cash_records'].pop(next(iter(current['cash_records'])))
            elif kind == 'corporate':
                removed = current['corporate_records'].pop(next(iter(current['corporate_records'])))
                current['corporate_records']['wrong-identity-same-count'] = removed
            elif kind == 'finding':
                current['items'].pop('L18')
            elif kind == 'evidence':
                current['items']['I14']['state'] = 'RESOLVED_SCOPE'
                current['items']['I14']['evidence'] = []
            else:
                current['profit_certified'] = True
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                verify(current)

    def test_changed_evidence_is_not_accepted_by_its_old_receipt(self):
        current = json.loads(DEFAULT.read_text(encoding='utf-8'))
        current['evidence_files'][next(iter(current['evidence_files']))] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'evidence changed'):
            verify(current)

    def test_uv_auxiliary_file_is_not_a_distribution_but_missing_or_extra_wheels_fail(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'package.whl').write_bytes(b'wheel')
            (root / '.gitignore').write_bytes(b'*')
            with self.assertRaises(ValueError):
                distribution_hashes(root)
            (root / 'package.tar.gz').write_bytes(b'source')
            original = distribution_hashes(root)
            self.assertEqual(len(original), 2)
            (root / '.gitignore').write_bytes(b'other auxiliary contents')
            self.assertEqual(distribution_hashes(root), original)
            (root / 'package.whl').write_bytes(b'changed distribution')
            self.assertNotEqual(distribution_hashes(root), original)
            (root / 'extra.whl').write_bytes(b'extra')
            with self.assertRaises(ValueError):
                distribution_hashes(root)


if __name__ == '__main__':
    unittest.main()
