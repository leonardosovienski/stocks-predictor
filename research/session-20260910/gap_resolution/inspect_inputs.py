"""Read-only inventory of preserved gaps and archive metadata."""
import json
from pathlib import Path
import sys
import zipfile

sys.stdout.reconfigure(encoding='utf-8')
root = Path('C:/STOCKS')
with zipfile.ZipFile(root / 'DADOS_STOCKS.zip') as archive:
    manifest = json.loads(archive.read('objects/51eed47cc7985a9d8f0be7ca14527871caeba2d9f8cacfb10d4abf423cb7f7fa'))
    print('PACKAGE', json.dumps({k:v for k,v in manifest.items() if k != 'files'}))
    for name, digest in manifest['files'].items():
        if name.endswith('manifest.json') and 'baseline/' in name and 'objects/' + digest in archive.namelist():
            value = json.loads(archive.read('objects/' + digest))
            print('BASE', name, json.dumps({k:v for k,v in value.items() if 'commit' in k or 'created_at' in k}))
inputs = root / 'data/recovery-r2/source14-inputs'
for filename in ('cash-events.json', 'corporate-actions.json', 'reviewed-payment-dates.json', 'evidence.json'):
    value = json.loads((inputs / filename).read_text(encoding='utf-8'))
    print('STRUCTURE', filename, type(value).__name__, list(value)[:12] if isinstance(value,dict) else len(value))
    rows = value if isinstance(value,list) else value.get('events', [])
    if rows:
        print('EXAMPLE', json.dumps(rows[0], ensure_ascii=False)[:1200])
        if filename == 'cash-events.json':
            for row in rows:
                if row.get('net_per_share') is None or row.get('payment_date') is None:
                    print('MISSING', json.dumps({k:row.get(k) for k in ('event_id','payment_date','net_per_share','gross_per_share','net_rule')}, ensure_ascii=False))
audit = json.loads((root / 'work/data-completion-r2-20260909/source14-audit.json').read_text(encoding='utf-8'))
other = [r for r in audit['issues'] if r.get('code', r.get('kind')) not in ('CASH_COVERAGE', 'CASH_EVENT_FIELD')]
print('ISSUE_EXAMPLES', json.dumps(other[:2], ensure_ascii=False)[:2000])
