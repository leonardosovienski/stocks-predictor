"""Verify current R8 code separately from immutable R7 historical receipts."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = 'docs/engineering/2026-09-10-r8/evidence.json'
EXTRA = {'.github/workflows/ci.yml', 'main.py', 'pyproject.toml', 'uv.lock', 'tools/build-requirements.txt'}


def code_paths(root):
    return EXTRA | {path.relative_to(root).as_posix() for folder in ('stocks_predictor', 'tests', 'tools')
                    for path in (root / folder).rglob('*.py')}


def canonical_sha(path):
    # Git's text checkout policy is LF. Windows CRLF is not a code change.
    return hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def checked_path(root, name):
    if not isinstance(name, str) or not name or '\\' in name or ':' in name or '..' in Path(name).parts:
        raise ValueError('invalid evidence path')
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('evidence outside repository')
    return path


def verify(root=ROOT):
    record = json.loads((root / REGISTRY).read_text(encoding='utf-8'))
    if set(record['current_code_sha256_lf']) != code_paths(root):
        raise ValueError('current code population differs from operational evidence')
    for name, expected in record['current_code_sha256_lf'].items():
        if canonical_sha(checked_path(root, name)) != expected:
            raise ValueError('current operational code changed: ' + name)
    for name, expected in record['historical_and_run_sha256'].items():
        if hashlib.sha256(checked_path(root, name).read_bytes()).hexdigest() != expected:
            raise ValueError('historical or run evidence changed: ' + name)
    if record['capital_enabled'] is not False or record['profit_certified'] is not False:
        raise ValueError('infrastructure evidence cannot enable capital or certify profit')
    real = json.loads((root / record['real_validation']).read_text(encoding='utf-8'))
    old = json.loads((root / 'docs/audit/2026-09-10-r7/evidence/real-versioned-ingestion.json').read_text(encoding='utf-8'))
    if (real['status'] != 'PASS' or real['source_sha256'] != old['source_sha256']
            or len(real['inspection']['sources']) != 1):
        raise ValueError('real source identity or validation failed')
    source = real['inspection']['sources'][0]
    if any(source[key] != old[prior] for key, prior in
           [('source_id', 'source_id'), ('rows', 'stored_rows'), ('rows_sha256', 'rows_sha256'),
            ('tickers', 'distinct_tickers'), ('date_min', 'date_min'), ('date_max', 'date_max')]):
        raise ValueError('real operational data differs from the preserved R7 population')
    capacity = json.loads((root / record['capacity_validation']).read_text(encoding='utf-8'))
    if capacity['status'] != 'PASS' or capacity['rows'] != 250000:
        raise ValueError('finite capacity acceptance failed')
    for run in (real, capacity):
        expected_package = {Path(name).name: sha for name, sha in record['current_code_sha256_lf'].items()
                            if name.startswith('stocks_predictor/') and len(Path(name).parts) == 2}
        if run['package_code_sha256_lf'] != expected_package:
            raise ValueError('operational run used a different package revision')
        results = [step['result'] for step in run['measurements']]
        if (len(results) != 9 or any(step['exit_code'] != 0 for step in run['measurements'])
                or results[1]['inserted'] != run['rows'] or results[2]['inserted'] != 0
                or results[3] != results[6] or results[3] != results[5]['inspection']
                or results[4]['inspection'] != results[3]
                or results[7]['status'] != 'INCOMPLETE_PERSONAL_SCENARIO'
                or results[8]['status'] != 'INSUFFICIENT_EVIDENCE'):
            raise ValueError('operational acceptance sequence changed')
    return {'status': 'PASS', 'current_code_files': len(record['current_code_sha256_lf']),
            'real_rows': source['rows'], 'capacity_rows': capacity['rows'],
            'capital_enabled': False, 'profit_certified': False}


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
