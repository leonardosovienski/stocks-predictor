"""Verify the immutable R8 closure and, optionally, its preserved local delivery."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[3]
DIRECTORY = ROOT / 'docs/continuation/2026-09-10-closure'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify(local=False):
    manifest = read(DIRECTORY / 'manifest.json')
    names = set()
    for row in manifest['files']:
        name = row['path']
        path = (DIRECTORY / name).resolve()
        require(name not in names and path.is_relative_to(DIRECTORY.resolve()), 'invalid receipt path')
        require(path.stat().st_size == row['bytes'] and sha(path) == row['sha256'], name)
        names.add(name)
    require(names == {p.relative_to(DIRECTORY).as_posix()
                      for p in (DIRECTORY / 'evidence').rglob('*') if p.is_file()},
            'closure evidence population differs')
    closure = read(DIRECTORY / 'evidence/ci230-closure.json')
    require(closure['status'] == 'PASS', 'closure did not pass')
    for key in ('final_head_ci', 'main_ci'):
        require(closure[key]['status'] == 'completed' and closure[key]['conclusion'] == 'success', key)
    require(closure['main_ci']['head'] == closure['merge_sha'] == manifest['implementation_revision'],
            'closure revision differs')
    require(all(job['conclusion'] == 'success' for job in closure['main_jobs']), 'failed CI job')
    for key in ('all_initial_request_items_closed', 'capital_enabled', 'profit_certified'):
        require(closure[key] is False, 'closure overstates economic readiness: ' + key)
    pending = read(ROOT / 'docs/engineering/2026-09-10-r8/evidence/failures.json')['attempts']
    require({x['id'] for x in pending if 'PENDING' in x['status']} <= set(closure['resolved_attempts']),
            'unresolved historical CI attempt')
    for version in ('3.13', '3.14'):
        folder = DIRECTORY / 'evidence' / ('python-' + version)
        suites = ET.parse(folder / 'test-results.xml').getroot().findall('testsuite')
        require(len(suites) == 1 and suites[0].get('tests') == '954', 'CI230 JUnit population differs')
        require(all(suites[0].get(k) == '0' for k in ('errors', 'failures', 'skipped')), 'CI230 tests failed')
        require(read(folder / 'coverage.json')['totals']['percent_covered'] >= 77, 'coverage below floor')
        run = read(folder / 'operations.json')
        require(run['status'] == 'PASS' and run['installed_wheel'] is True and run['rows'] == 250000,
                'installed operational acceptance failed')
    baseline = read(DIRECTORY / 'evidence/stocks-current-tree.sarif')['runs'][0]['results']
    control = read(DIRECTORY / 'evidence/stocks-scan-control.sarif')['runs'][0]['results']
    require(not baseline, 'unresolved baseline scanner findings')
    require(any(x['ruleId'] == 'generic-api-key' and x['locations'][0]['physicalLocation']
                ['artifactLocation']['uri'].endswith('/stocks_predictor/trials_gate.py')
                for x in control), 'scanner did not detect its synthetic control')
    require(read(DIRECTORY / 'evidence/build.json')['head'] == closure['merge_sha'], 'build revision differs')
    result = {'status': 'PASS', 'implementation_revision': closure['merge_sha'], 'evidence_files': len(names),
              'scope': 'Historical CI230 receipt identities and consistency, not a new software test run.',
              'local_delivery_checked': local, 'capital_enabled': False, 'profit_certified': False}
    if local:
        receipt = read(DIRECTORY / 'evidence/delivery-receipt.json')
        archive = Path(receipt['archive'])
        require(sha(archive) == receipt['archive_sha256'], 'local delivery archive changed')
        require(sha(Path(receipt['report'])) == receipt['report_sha256'], 'local delivery report changed')
        with zipfile.ZipFile(archive) as zipped:
            expected = {x['path'] for x in receipt['files']}
            require(len(expected) == len(receipt['files']), 'duplicate delivery receipt member')
            require(set(zipped.namelist()) == expected | {'MANIFEST.json'}, 'delivery population differs')
            require(len(zipped.namelist()) == len(expected) + 1, 'duplicate ZIP member')
            require(json.loads(zipped.read('MANIFEST.json'))['files'] == receipt['files'], 'inner manifest differs')
            for row in receipt['files']:
                with zipped.open(row['path']) as stream:
                    require(hashlib.file_digest(stream, 'sha256').hexdigest() == row['sha256'], row['path'])
        catalog = read(Path('C:/STOCKS/data/CATALOG.json'))
        require(len(catalog['databases']) == 12, 'original database population differs')
        for row in catalog['databases']:
            require(sha(Path(row['path'])) == row['sha256'], 'original database changed: ' + row['path'])
        result.update(delivery_members=len(receipt['files']), preserved_databases=12)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--local', action='store_true', help='Also hash the existing C:/STOCKS delivery and 12 banks.')
    args = parser.parse_args()
    print(json.dumps(verify(args.local), indent=2))
