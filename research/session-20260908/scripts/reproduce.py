"""Offline reproduction. Uses preserved quote inputs; never opens a database."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--inputs', type=Path, default=Path(
    'C:/Users/Superleo13/stocks-predictor-work/.local-research/stocks-session-20260907/work/stocks-final-review-bundle/inputs'))
args = parser.parse_args()
for name, expected in json.loads((root/'SHA256.json').read_text(encoding='utf-8')).items():
    path = (root/name).resolve()
    if not path.is_relative_to(root) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise SystemExit('Package integrity failed: '+name)
out = root/'work'; out.mkdir(exist_ok=True)
code = root/'code'
env = dict(os.environ, PYTHONPATH=str(code))


def run(name, command, expected=0, run_env=None):
    with (out/(name+'.log')).open('w', encoding='utf-8') as log:
        process = subprocess.run(command, cwd=code, env=run_env or env, stdout=log, stderr=subprocess.STDOUT)
    if process.returncode != expected:
        raise SystemExit(f'{name}: expected exit {expected}, got {process.returncode}; see {out/name}.log')
    return process.returncode


run('tests', [sys.executable, '-m', 'pytest', 'tests', '-q'])
run('replay', [sys.executable, '-m', 'stocks_predictor.continuous_research',
              '--inputs', str(args.inputs), '--output', str(out/'replay.json')], 2)
run('feasibility', [sys.executable, 'tools/assess_execution_feasibility.py',
    '--inputs', str(args.inputs), '--protocol', str(root/'protocol.json'),
    '--entry-unit-review', str(root/'entry-unit-review/review.json'), '--output', str(out/'feasibility.json')])
run('vivt-source-audit', [sys.executable, str(root/'research-scripts/audit_vivt_sources.py'),
    '--sources', str(root/'sources/vivt'), '--output', str(out/'vivt-source-audit.json')])
for label, runtime in [('before', root/'regression-runtime-before'), ('after', code)]:
    run('regression-'+label, [sys.executable, str(root/'research-scripts/probe_corporate_regressions.py')],
        run_env=dict(os.environ, PYTHONPATH=str(runtime)))
    value=json.loads((out/('regression-'+label+'.log')).read_text(encoding='utf-8'))
    if any(r['unsafe_input_accepted'] != (label == 'before') for r in value['cases']):
        raise SystemExit('Regression result differs: '+label)
for actual, expected in [('replay.json', 'replay.json'), ('feasibility.json', 'feasibility-final.json'),
                         ('vivt-source-audit.json', 'vivt-source-audit.json')]:
    if (out/actual).read_bytes() != (root/'results'/expected).read_bytes():
        raise SystemExit('Reproduction differs: '+actual)
print('PASS: packaged tests, three old/new regressions, source audit and byte-identical diagnostics.')
print('Economic replay remains BLOCKED_MISSING_EVIDENCE (exit 2); profit is unknown.')
