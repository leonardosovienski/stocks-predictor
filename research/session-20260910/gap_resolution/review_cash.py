"""Expose source-bound candidate texts for manual event-by-event reconciliation."""
import hashlib
import json
from pathlib import Path
import sys
from pypdf import PdfReader

sys.stdout.reconfigure(encoding='utf-8')
root = Path('C:/STOCKS/data/recovery-r2/source14-inputs')
out = Path('C:/STOCKS/work/gap-resolution-r6-20260910/cash-review')
out.mkdir(exist_ok=False)
events = json.loads((root/'cash-events.json').read_text(encoding='utf-8'))
index = []
for i, event in enumerate(events):
    if event.get('net_per_share') is not None and event.get('payment_date'):
        continue
    refs = event['sources'] + event.get('unresolved_payment_evidence', {}).get('sources', [])
    text = [json.dumps(event, ensure_ascii=False, indent=2)]
    for ref in refs:
        if not ref.get('verified_primary_file', '').endswith('.pdf'):
            continue
        path = root/ref['verified_primary_file']
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != ref.get('sha256', ref.get('source_sha256')):
            raise ValueError('Changed primary source')
        reader = PdfReader(path)
        pages = ref.get('pages') or range(1, min(len(reader.pages), 8) + 1)
        for page in pages:
            text.append(f'\nSOURCE {path.name} PAGE {page}\n' + (reader.pages[page-1].extract_text() or ''))
    target = out/f'{i:04d}-{event["ticker"]}.txt'
    target.write_text('\n'.join(text), encoding='utf-8')
    index.append({'index':i, 'event_id':event['event_id'], 'path':str(target), 'primary_refs':len(refs)})
(out/'index.json').write_text(json.dumps(index, indent=2), encoding='utf-8')
print(json.dumps(index, indent=2))
