from pathlib import Path
from datetime import datetime, timezone
import collections, hashlib, json, math
root=Path.cwd();raw=root/'work/source-acquisition';dest=root/'work/h17-preparation'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
panel=read(dest/'event-panel-preflight.json');jobs=read(dest/'needed-issuers.json')
aliases={r['historical_ticker']:r for r in read(dest/'secondary-source-aliases.json')}
ids=collections.defaultdict(list)
for p in (root/'work/h17-source-identity-v3').glob('*.jsonl'):
 for line in p.read_text(encoding='utf-8').splitlines():
  r=json.loads(line);ids[r['ticker']].append(r)
audit=[]
for j in jobs:
 for t in j['tickers']:
  source=t if (raw/f'yahoo-h17-{t}-actions.json').exists() else aliases.get(t,{}).get('source_ticker')
  path=raw/f'yahoo-h17-{source}-actions.json'
  if not source or not path.exists():
   audit.append({'ticker':t,'status':'SECOND_SOURCE_UNAVAILABLE'});continue
  data=read(path)['chart']['result'][0]
  if data['meta']['symbol']!=source+'.SA':raise ValueError('source symbol mismatch')
  panel['sources'].append({'path':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'codeCVM':j['codeCVM'],'ticker':t,'alias':aliases.get(t)})
  for e in data.get('events',{}).get('splits',{}).values():
   day=datetime.fromtimestamp(e['date'],timezone.utc).date().isoformat()
   if not '2016-01-01'<=day<='2026-02-02':continue
   identities={r['isin'] for r in ids[t] if r['first_date']<=day<=r['last_date']}
   if len(identities)!=1:continue
   factor=float(e['denominator'])/float(e['numerator'])
   existing=[r for r in panel['events'] if r['ticker']==t and r['ex_date']==day and r['price_factor'] is not None]
   previous=[r for r in panel['legacy_adjustments'] if r['ticker']==t and r['ex_date']==day and r['approved_by']]
   row={'ticker':t,'date':day,'factor':factor,'source_file':path.name}
   if existing or previous:
    # Approved legacy factors are only a fallback when B3 has no share action.
    primary=math.prod(r['price_factor'] for r in existing) if existing else math.prod(r['factor'] for r in previous)
    row['primary_factor']=primary
    row['status']='CROSSCHECK_MATCH' if math.isclose(factor,primary,rel_tol=1e-6) else ('CROSSCHECK_ROUNDING_DIFFERENCE' if math.isclose(factor,primary,rel_tol=1e-4) else 'CROSSCHECK_CONFLICT')
   else:
    row['status']='SECONDARY_ADDITION'
    panel['events'].append({'ticker':t,'codeCVM':j['codeCVM'],'isin':next(iter(identities)),
       'last_cum':None,'ex_date':day,'approved_on':None,'label':'SECONDARY_SHARE_BASE',
       'price_factor':factor,'raw':e,'sources':[path.name],
       'quality':'SECONDARY_SOURCE_EXPLORATORY_ADJUSTMENT_NOT_TRADABLE_SHARE_DELIVERY'})
   audit.append(row)
panel['secondary_action_audit']=audit
(dest/'event-panel-with-crosscheck.json').write_text(json.dumps(panel,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(collections.Counter(r['status'] for r in audit)),indent=2))
print('conflicts',json.dumps([r for r in audit if r['status']=='CROSSCHECK_CONFLICT'],indent=2))
