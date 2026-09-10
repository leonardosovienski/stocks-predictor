from decimal import Decimal
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from stocks_predictor.research_profile import ResearchProfile
from tools.materialize_source_revision import materialize, safe_file


class ResearchControls(unittest.TestCase):
    def test_unknown_costs_stay_unknown_and_do_not_validate_profit(self):
        result = ResearchProfile(Decimal('5000')).assess()
        self.assertIsNone(result['known_fixed_reserve_brl'])
        self.assertIn('monthly_fixed_brl', result['missing_inputs'])
        self.assertFalse(result['absolute_net_profit_demonstrated'])

    def test_costs_can_make_small_capital_infeasible(self):
        result = ResearchProfile(Decimal('5000'), horizon_months=105, resident_pf_brazil=True,
                                 brokerage_per_order_brl=Decimal('0'), monthly_fixed_brl=Decimal('50'),
                                 advisor_annual_fraction=Decimal('0')).assess()
        self.assertEqual(result['known_fixed_reserve_brl'], '5250')
        self.assertFalse(result['fixed_reserve_fits_capital'])
        self.assertFalse(result['capital_enabled'])

    def test_nonfinite_negative_and_boolean_horizon_rejected(self):
        for profile in (ResearchProfile(Decimal('NaN')), ResearchProfile(Decimal('-1')),
                        ResearchProfile(Decimal('5000'), horizon_months=True),
                        ResearchProfile(Decimal('5000'), monthly_fixed_brl=Decimal('Infinity'))):
            with self.subTest(profile=profile), self.assertRaises(ValueError):
                profile.assess()

    def test_delta_materializes_exact_bytes_and_refuses_reuse_or_changed_parent(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            parent, delta, output = (root / n for n in ('parent', 'delta', 'output'))
            parent.mkdir(); delta.mkdir()
            (parent / 'a.txt').write_bytes(b'preserved')
            (delta / 'b.txt').write_bytes(b'new')
            a_sha = hashlib.sha256(b'preserved').hexdigest()
            b_sha = hashlib.sha256(b'new').hexdigest()
            (parent / 'SHA256.json').write_text(json.dumps({'a.txt': a_sha}), encoding='utf-8')
            (delta / 'SHA256.json').write_text(json.dumps({'a.txt': a_sha, 'b.txt': b_sha}), encoding='utf-8')
            ph = hashlib.sha256((parent / 'SHA256.json').read_bytes()).hexdigest()
            dh = hashlib.sha256((delta / 'SHA256.json').read_bytes()).hexdigest()
            self.assertEqual(materialize(parent, delta, output, ph, dh)['files'], 2)
            self.assertEqual((output / 'a.txt').read_bytes(), b'preserved')
            with self.assertRaises(ValueError):
                materialize(parent, delta, output, ph, dh)
            (parent / 'a.txt').write_bytes(b'tampered')
            with self.assertRaisesRegex(ValueError, 'parent payload changed'):
                materialize(parent, delta, root / 'another', ph, dh)
            self.assertFalse((root / 'another').exists())

    def test_manifest_paths_cannot_escape_or_use_windows_aliases(self):
        with tempfile.TemporaryDirectory() as folder:
            for name in ('../outside', '/absolute', 'C:/absolute', 'a\\b', 'a.txt:stream'):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    safe_file(Path(folder), name)


if __name__ == '__main__':
    unittest.main()
