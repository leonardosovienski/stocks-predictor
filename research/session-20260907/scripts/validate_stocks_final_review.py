"""Execute the final test/build/replay checks; no database connection or orders."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / 'work/stocks-predictor'
BASE = ROOT / 'work/stocks-final-review-bundle'
OUT = ROOT / 'outputs'
LABEL = 'stocks-final-review' + ('-v2' if '--v2' in sys.argv else '')
PREFIX = ROOT / 'work' / LABEL
ENV = dict(os.environ, PYTHONPATH=os.pathsep.join(str(ROOT / 'work' / p) for p in ('runtime', 'checks', 'lint')))


def sha(p):
    with p.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(p, v):
    p.write_text(json.dumps(v, ensure_ascii=False, indent=2), encoding='utf-8')


steps = []


def run(name, command, cwd=REPO, expected=(0,), env=ENV):
    print(json.dumps({'starting': name}), flush=True)
    began = time.monotonic()
    result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace')
    log = PREFIX.with_name(PREFIX.name + '-' + name + '.log')
    log.write_text(result.stdout + result.stderr, encoding='utf-8')
    row = {'step': name, 'exit_code': result.returncode, 'elapsed_seconds': round(time.monotonic()-began, 2),
           'log': log.name, 'log_sha256': sha(log), 'passed_expected_exit': result.returncode in expected}
    steps.append(row)
    print(json.dumps(row), flush=True)
    if result.returncode not in expected:
        print(result.stdout[-5000:] + result.stderr[-3000:], flush=True)
        write(OUT / 'STOCKS_REVISAO_FINAL_VALIDACAO.json', {'status': 'CHECK_FAILED', 'steps': steps})
        raise ValueError('Unexpected result: ' + name)
    return result.stdout


assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=REPO).strip()
commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip()
databases = [Path(r'C:\Users\Superleo13\stocks-predictor-work\data\stocks.db'), ROOT / 'work/stocks-tested-real-v2-20260907.db']
before = {str(p): sha(p) for p in databases}
tests = run('tests', [sys.executable, '-X', 'utf8', '-m', 'coverage', 'run',
    '--data-file=' + str(PREFIX.with_suffix('.coverage')), '-m', 'pytest', '-q'])
count = int(re.search(r'(\d+) passed', tests).group(1))
coverage = run('coverage', [sys.executable, '-m', 'coverage', 'report',
    '--data-file=' + str(PREFIX.with_suffix('.coverage'))])
run('lint', [sys.executable, '-m', 'ruff', 'check', 'stocks_predictor', 'tests', 'main.py'])
run('pyright', [sys.executable, '-m', 'pyright'])
wheel_dir = ROOT / 'work' / (LABEL + '-wheel')
run('wheel', [sys.executable, '-m', 'build', '--wheel', '--no-isolation', '--outdir', str(wheel_dir)])
wheel = next(wheel_dir.glob('*.whl'))
installed = ROOT / 'work' / (LABEL + '-wheel-installed')
installed.mkdir(exist_ok=False)
with zipfile.ZipFile(wheel) as archive:
    archive.extractall(installed)
wheel_env = dict(ENV, PYTHONPATH=str(installed) + os.pathsep + str(ROOT / 'work/runtime'))
run('wheel-import', [sys.executable, '-c', 'import predictor_core, stocks_predictor.continuous_cash, stocks_predictor.continuous_research, stocks_predictor.rj_judge; print(stocks_predictor.continuous_cash.__file__)'],
    cwd=ROOT / 'work', env=wheel_env)
for name in ('retail_cash.py', 'continuous_cash.py', 'continuous_research.py'):
    shutil.copy2(REPO / 'stocks_predictor' / name, BASE / 'stocks_predictor' / name)
for name in ('test_retail_cash.py', 'test_continuous_cash.py', 'test_continuous_research.py'):
    shutil.copy2(REPO / 'tests' / name, BASE / 'tests' / name)
run('standalone-tests', [sys.executable, '-X', 'utf8', '-m', 'pytest', 'tests', '-q'], cwd=BASE)
audit = OUT / 'STOCKS_REVISAO_FINAL_EXECUCAO.json'
run('real-replay', [sys.executable, '-X', 'utf8', '-m', 'stocks_predictor.continuous_research',
    '--inputs', str(BASE / 'inputs'), '--output', str(audit)], cwd=ROOT / 'work', expected=(2,), env=wheel_env)
replay = json.loads(audit.read_text(encoding='utf-8'))
assert replay['status'] == 'BLOCKED_MISSING_EVIDENCE' and replay['profit'] is None
assert replay['new_historical_return_evaluations'] == 0 and 'cases' not in replay
if '--v2' in sys.argv:
    run('actual-readonly-status', [sys.executable, '-X', 'utf8', 'main.py', 'status'],
        env=dict(ENV, PREDICTOR_DB_PATH=str(databases[0])))
after = {str(p): sha(p) for p in databases}
assert before == after
assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=REPO).strip()
write(OUT / 'STOCKS_REVISAO_FINAL_VALIDACAO.json', {
    'status': 'TECHNICAL_CHECKS_PASSED_ECONOMIC_REPLAY_BLOCKED', 'validated_commit': commit,
    'tests_passed': count, 'steps': steps,
    'wheel': wheel.name, 'wheel_sha256': sha(wheel),
    'database_hashes_before_and_after_equal': True, 'database_hashes': after,
    'source_module_hashes': {n: sha(REPO / 'stocks_predictor' / n) for n in
        ('retail_cash.py', 'continuous_cash.py', 'continuous_research.py')},
    'profit_demonstrated': False, 'new_historical_return_evaluations': 0,
    'historical_replay_status': replay['status'], 'validated_quote_records': replay['validated_quote_records'],
    'raw_quote_comparison_report': 'STOCKS_REVISAO_FINAL_FONTES.json',
    'pyright_scope': 'RJ three modules plus retail_cash, continuous_cash, continuous_research',
    'no_runtime_dependencies_added': True})
print(json.dumps({'complete': True, 'tests_passed': count, 'profit_demonstrated': False}), flush=True)
