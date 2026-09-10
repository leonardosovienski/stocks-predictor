"""Verify and render the current audit overlay without rewriting historical findings."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / 'docs/audit/2026-09-10-r7/current.json'
R7_REVISION = 'c259ff64771a6c560ddb4aadac6bf81301c3066a'
GROUPS = {'original_issues': 16, 'r4_corrections': 10, 'r5_pre_measurement_corrections': 2,
          'limits': 25, 'improvements': 16, 'chat_items': 6}
STATES = {'RESOLVED_SCOPE', 'IMPLEMENTED_LIMITED', 'OPEN_DATA', 'OPEN_PERSONAL',
          'OPEN_TIME', 'OPEN_SCOPE', 'RETAINED_RESULT', 'CONDITIONAL_NOT_TRIGGERED'}


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def located(root, name):
    if not isinstance(name, str) or not name or '\\' in name or ':' in name:
        raise ValueError('invalid evidence path')
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()) or '..' in Path(name).parts:
        raise ValueError('evidence path outside repository')
    return path


def verify(current, root=ROOT):
    baseline_path = located(root, current['baseline_path'])
    if digest(baseline_path) != current['baseline_sha256']:
        raise ValueError('historical baseline identity changed')
    baseline = json.loads(baseline_path.read_text(encoding='utf-8'))
    required = set()
    for group, expected in GROUPS.items():
        rows = baseline[group]
        ids = [row['id'] for row in rows]
        if len(rows) != expected or len(set(ids)) != expected or required.intersection(ids):
            raise ValueError('missing/duplicate historical items: ' + group)
        required.update(ids)
    if set(current['items']) != required:
        raise ValueError('current overlay must retain every historical item exactly once')
    cash_ids = [row['event_id'] for row in baseline['missing_cash_records']]
    if len(cash_ids) != 50 or len(set(cash_ids)) != 50 or set(current['cash_records']) != set(cash_ids):
        raise ValueError('cash population lost or duplicated')
    corporate_ids = {f"CA-{i:02d}:{row.get('ticker')}:{row.get('ex_date')}"
                     for i, row in enumerate(baseline['corporate_records'], 1)}
    if len(baseline['corporate_records']) != 28 or set(current['corporate_records']) != corporate_ids:
        raise ValueError('corporate population lost')
    issues = baseline['source15_audit']['issues']
    if len(issues) != 1590 or dict(Counter(x['kind'] for x in issues)) != baseline['source15_audit']['issue_counts']:
        raise ValueError('source issue population/count mismatch')
    if len(baseline['fronts_historical']) != 24 or len(baseline['claims_historical']) != 22:
        raise ValueError('front or claim population changed')
    for group in (current['items'], current['cash_records'], current['corporate_records']):
        for key, row in group.items():
            if row['state'] not in STATES or not row.get('result') or not row.get('acceptance'):
                raise ValueError('unclassified item: ' + key)
            if row['state'] == 'RESOLVED_SCOPE' and not row.get('evidence'):
                raise ValueError('closure requires evidence: ' + key)
            if row['state'] not in {'RESOLVED_SCOPE', 'RETAINED_RESULT'} and not row.get('remaining'):
                raise ValueError('unfinished item requires explicit next condition: ' + key)
            for reference in row.get('evidence', []):
                if reference not in current['evidence_files']:
                    raise ValueError('unregistered evidence: ' + reference)
    for name, expected in current['evidence_files'].items():
        path = located(root, name)
        # R7 code receipts describe R7. Preserve their meaning while allowing new
        # implementations. Historical documents, raw evidence and protocols still
        # must match their receipts in the current working tree.
        if name.startswith(('stocks_predictor/', 'tests/', 'tools/', '.github/')) or name == 'pyproject.toml':
            blob = subprocess.run(['git', 'show', R7_REVISION + ':' + name], cwd=root,
                                  capture_output=True, check=True, timeout=30).stdout
            actual = hashlib.sha256(blob).hexdigest()
        else:
            actual = digest(path)
        if actual != expected:
            raise ValueError('evidence changed: ' + name)
    rights = json.loads((baseline_path.parent / 'source-rights.json').read_text(encoding='utf-8'))
    if (len(rights['records']) != 794 or len({row['file'] for row in rights['records']}) != 794
            or dict(Counter(row['status'] for row in rights['records'])) != rights['counts']):
        raise ValueError('source rights population/count mismatch')
    if current['profit_certified'] is not False or current['capital_enabled'] is not False:
        raise ValueError('this engineering registry cannot certify profit or enable capital')
    if current['items']['I15']['state'] != 'RESOLVED_SCOPE':
        raise ValueError('I15 files were recovered; do not resurrect the historical file blocker')
    return {'status': 'PASS', 'code_evidence_revision': R7_REVISION,
            'items': len(required), 'cash_records': len(cash_ids),
            'corporate_records': 28, 'source_issue_occurrences': len(issues),
            'states': dict(Counter(row['state'] for row in current['items'].values())),
            'scope': 'Inventory and evidence identity, not universal correctness or profit certification.'}


def render(current, baseline):
    titles = {row['id']: row.get('title', row.get('before', row['id']))
              for group in GROUPS for row in baseline[group]}
    lines = ['# Consolidado executado R7', '',
             'Estado atual sobre uma base histórica preservada. Lucro integral/futuro não certificado.', '',
             '| Item | Estado | Resultado / condição restante |', '|---|---|---|']
    for key, row in current['items'].items():
        text = row['result'] + (' Restante: ' + row['remaining'] if row.get('remaining') else '')
        lines.append(f"| {key} — {titles[key]} | {row['state']} | {text.replace('|', '/')} |")
    lines += ['', '## Registros sem líquido', '', '| Evento | Estado | Condição |', '|---|---|---|']
    for key, row in current['cash_records'].items():
        lines.append(f"| {key} | {row['state']} | {row['remaining'].replace('|', '/')} |")
    lines += ['', '## Registros societários', '', '| Registro | Estado | Condição |', '|---|---|---|']
    for key, row in current['corporate_records'].items():
        lines.append(f"| {key} | {row['state']} | {row['remaining'].replace('|', '/')} |")
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registry', type=Path, default=DEFAULT)
    parser.add_argument('--render', type=Path)
    args = parser.parse_args()
    current = json.loads(args.registry.read_text(encoding='utf-8'))
    result = verify(current)
    baseline = json.loads(located(ROOT, current['baseline_path']).read_text(encoding='utf-8'))
    content = render(current, baseline)
    if args.render:
        with args.render.open('x', encoding='utf-8', newline='\n') as handle:
            handle.write(content)
    elif (args.registry.parent / 'CONSOLIDADO.md').read_text(encoding='utf-8') != content:
        raise ValueError('rendered current view is stale')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
