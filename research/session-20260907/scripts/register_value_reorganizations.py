from pathlib import Path
import datetime
import hashlib
import json

BASE=Path(__file__).resolve().parent
REPO=BASE/'stocks-predictor'
def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
protocol=json.loads((BASE/'value-event-stage-intent.json').read_text(encoding='utf-8'))
protocol['sealed_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
protocol['input_sha256']={key:digest(path) for key,path in {
    'first':BASE.parent/'outputs/h18-h19-repaired-observation.json',
    'db':BASE/'value-measurement-source/quotes.db',
    'successor_db':BASE/'value-successor-source/successors.db',
    'events':BASE/'value-measurement-source/events.json',
    'reviews':BASE/'value-measurement-source/reviewed-jumps.json',
    'terms':BASE/'value-event-terms/reorganizations.json'}.items()}
for key,folder in [('identities','value-measurement-source'),('successor_identities','value-successor-source')]:
    protocol[key]={p.name:digest(p) for p in sorted((BASE/folder/'identity').glob('identity-*.jsonl'))}
protocol['primary_source_sha256']={p.name:digest(p) for p in sorted((BASE/'value-event-terms').iterdir())
    if p.suffix=='.pdf' or p.name.endswith('.source.json') or (p.name.startswith('b3-') and p.suffix=='.json')}
protocol['source_notes']=[
    'Issuer-authored documents hosted on broker/publication mirrors retain explicit original authorship and mirror URL; no anonymous summary used for terms.',
    'TIMP last cum 2020-10-09 and first TIMS 2020-10-13 checked directly in raw B3 quotes; CVM confirms 1:1 unchanged economic rights.',
    'Unknown physical credit dates remain null. Cash statuses reflect disclosed schedules, not verified broker account receipts.',
    'B3 VAMO historical-volume migration 28.290555 percent is NOT share delivery ratio 1.15136366.',
    'Pre-seal schema inspection corrected the source label CIS RED CAP; no third-stage aggregate had been evaluated.'
]
protocol['terms_count']=13
protocol['subscriptions_count']=6
canonical=json.dumps(protocol,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
sha=hashlib.sha256(canonical).hexdigest()
path=REPO/'docs/research/2026-09-07-reorganization-protocol.json'
with path.open('x',encoding='utf-8') as stream:json.dump(protocol,stream,ensure_ascii=False,indent=2)
code=REPO/'stocks_predictor/discovery_reorganizations.py'
content=code.read_text(encoding='utf-8')
assert 'TO_BE_SEALED_BEFORE_OBSERVATION' in content
code.write_text(content.replace('TO_BE_SEALED_BEFORE_OBSERVATION',sha),encoding='utf-8')
print('protocol semantic sha256',sha)
