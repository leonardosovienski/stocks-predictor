from pathlib import Path
import collections, concurrent.futures, json, sys
root=Path.cwd();sys.path.insert(0,str(root/'work'))
from fetch_h17_crosscheck import fetch
raw=root/'work/source-acquisition';dest=root/'work/h17-preparation'
jobs=json.loads((dest/'needed-issuers.json').read_text(encoding='utf-8'))
failed={r['ticker'] for r in json.loads((root/'outputs/h17-secondary-action-acquisition.json').read_text(encoding='utf-8')) if r['status']=='FAILED'}
ids=collections.defaultdict(set)
for p in (root/'work/h17-source-identity-v3').glob('*.jsonl'):
 for line in p.read_text(encoding='utf-8').splitlines():
  r=json.loads(line);ids[r['ticker']].add(r['isin'][6:11])
details={}
for p in raw.glob('b3-*-detail.json'):
 try:r=json.loads(p.read_text(encoding='utf-8-sig'))
 except ValueError:continue
 if isinstance(r,dict) and r.get('cnpj'):details[str(int(r['codeCVM']))]=(r,p.name)
aliases=[]
for j in jobs:
 if j['codeCVM'] not in details:continue
 d,path=details[j['codeCVM']]
 if ''.join(x for x in d['cnpj'] if x.isdigit())!=j['cnpj']:continue
 for t in j['tickers']:
  if t not in failed or len(ids[t])!=1:continue
  matches=[r for r in d.get('otherCodes') or [] if r['isin'][6:11] in ids[t]]
  if len(matches)==1 and matches[0]['code']!=t:
   aliases.append({'historical_ticker':t,'source_ticker':matches[0]['code'],'cnpj':j['cnpj'],'codeCVM':j['codeCVM'],'detail_source':path,'mapping_purpose':'Retrospective corporate-action cross-check only, never universe membership; same CVM CNPJ and ISIN instrument class.'})
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 result=list(pool.map(fetch,sorted({a['source_ticker'] for a in aliases})))
(dest/'secondary-source-aliases.json').write_text(json.dumps(aliases,indent=2),encoding='utf-8')
(root/'outputs/h17-secondary-alias-acquisition.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('aliases',len(aliases),'acquired',sum(r['status']=='ACQUIRED' for r in result))
print(json.dumps(aliases,indent=2))
