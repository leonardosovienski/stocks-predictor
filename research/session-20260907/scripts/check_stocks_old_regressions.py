"""Reproduce review defects on the previous commit without editing its checkout."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
repo = root / 'work/stocks-predictor'
base = root / 'work/stocks-final-review-before-fixes'
base.mkdir(exist_ok=False)
(base / 'stocks_predictor').mkdir()
(base / 'stocks_predictor/__init__.py').write_text('', encoding='utf-8')
for name in ('retail_cash.py', 'continuous_cash.py', 'continuous_research.py'):
    content = subprocess.check_output(['git', 'show', '4b899f4:stocks_predictor/' + name], cwd=repo)
    (base / 'stocks_predictor' / name).write_bytes(content)
(base / 'tests').mkdir()
(base / 'tests/__init__.py').write_text('', encoding='utf-8')
for name in ('test_continuous_cash.py', 'test_continuous_research.py'):
    shutil.copy2(repo / 'tests' / name, base / 'tests' / name)
env = dict(os.environ, PYTHONPATH=str(root / 'work/checks'))
selection = 'partial_precredit or purchase_merges or future_corporate_quantity or delayed_plan or empty_or_invalid_cases or different_production_protocol or economic_gate_does_not_hide'
result = subprocess.run([sys.executable, '-X', 'utf8', '-m', 'pytest', 'tests', '-q', '-k', selection],
                        cwd=base, env=env, capture_output=True, text=True, encoding='utf-8')
(root / 'work/stocks-final-review-before-fixes.log').write_text(result.stdout + result.stderr, encoding='utf-8')
print(json.dumps({'old_commit': '4b899f4', 'regression_exit': result.returncode,
                  'last_lines': result.stdout.splitlines()[-14:]}))
if result.returncode != 1:
    raise ValueError('Expected reproduced assertion failures on the previous version')
