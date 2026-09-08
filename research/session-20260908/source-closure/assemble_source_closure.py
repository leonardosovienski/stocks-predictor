"""Create a self-contained additive input revision with verified primary bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from source_utils import ROOT, BASE, OUT, read
from stocks_predictor.continuous_research import verify_manifest

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parser=argparse.ArgumentParser();parser.add_argument('--version',default='10',choices=[f'{i:02d}' for i in range(4,21)])
args=parser.parse_args()
base=ROOT/'work/stocks-final-review-bundle/inputs'
manifest=verify_manifest(base);snapshot=OUT/f'cash-closure-{args.version}.json';snap=read(snapshot)
dest=OUT/f'execution-inputs-{args.version}';assert not dest.exists(),dest
dest.mkdir();(dest/'primary').mkdir()
for name in manifest:
    p=dest/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(base/name,p)

catalog={};refs={}
roots=[BASE,OUT/'new-primary',ROOT/'work/h19-tax-source',ROOT/'work/stocks-final-review-bundle/sources']

def materialize(s):
    filename=s.get('file',s.get('source_file'));digest=s.get('sha256',s.get('source_sha256'))
    if not filename or not digest:raise ValueError(('unbound source reference',s))
    key=(str(filename),digest)
    if key in refs:return refs[key]
    p=Path(filename)
    candidates=[p,ROOT/p] if p.is_absolute() else [ROOT/p]
    for directory in roots:
        candidates.extend([directory/p.name,directory/(digest[:12]+'-'+p.name)])
    found=next((p for p in candidates if p.is_file() and sha(p)==digest),None)
    if found is None:raise FileNotFoundError(key)
    name=f'primary/{digest}-{found.name}'
    if name not in catalog:
        shutil.copy2(found,dest/name)
        kind=('DERIVED_LOCAL_REVIEW' if digest=='e4282eb0155808fd57469704966d7e1718c6560fbe9520a3ef2f420b3c5b7bf2'
              else 'PRIMARY_SOURCE_RECORD')
        catalog[name]=dict(original_file=str(found),sha256=digest,url=s.get('url'),source_kind=kind)
    refs[key]=name
    return name

def rewrite(value):
    if isinstance(value,list):return [rewrite(v) for v in value]
    if not isinstance(value,dict):return value
    result={k:rewrite(v) for k,v in value.items()}
    if ('file' in value or 'source_file' in value) and ('sha256' in value or 'source_sha256' in value):
        result['verified_primary_file']=materialize(value)
    return result

cash=rewrite(snap['cash_events']);actions=rewrite(snap['corporate_actions'])
tax=rewrite(read(base/'tax-calendar.json'))
ev=read(base/'evidence.json')
keys={(a['ticker'],a['ex_date']) for a in actions}
removed=[g for g in ev['action_gaps'] if (g.get('ticker'),g.get('ex_date')) in keys]
ev['action_gaps']=[g for g in ev['action_gaps'] if (g.get('ticker'),g.get('ex_date')) not in keys]
assert len(removed)==len(actions)
lineage=rewrite(snap['installment_lineage'])
for name,value in [('cash-events.json',cash),('corporate-actions.json',actions),('evidence.json',ev),
                   ('tax-calendar.json',tax),('source-lineage.json',lineage),('primary-catalog.json',catalog)]:
    (dest/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
revision=dict(schema='PRIMARY_SOURCE_EXECUTION_REVISION_1',base_manifest_sha256=sha(base/'SHA256.json'),
    snapshot_sha256=sha(snapshot),source_protocol_sha256=snap['source_protocol_sha256'],
    original_cash_events_sha256=manifest['cash-events.json'],counts=snap['counts'],removed_action_gaps=removed,
    complete_inventory_certified=False,new_historical_return_evaluations=0,
    intent='Dated cash/source readiness only. Frozen selection unchanged. Separate registration before any new returns.')
(dest/'source-revision.json').write_text(json.dumps(revision,indent=2)+'\n',encoding='utf-8')
new={str(p.relative_to(dest)).replace('\\','/'):sha(p) for p in sorted(dest.rglob('*')) if p.is_file() and p.name!='SHA256.json'}
(dest/'SHA256.json').write_text(json.dumps(new,indent=2)+'\n',encoding='utf-8')
verify_manifest(base);verify_manifest(dest)
print(json.dumps(dict(input_directory=str(dest),files=len(new),verified_source_files=len(catalog),
    verified_primary_files=sum(v['source_kind']=='PRIMARY_SOURCE_RECORD' for v in catalog.values()),
    manifest_sha256=sha(dest/'SHA256.json'),counts=snap['counts'])))
