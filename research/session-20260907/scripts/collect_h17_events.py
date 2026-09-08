import sys,json,concurrent.futures
from pathlib import Path
root=Path.cwd();sys.path.insert(0,str(root/'work'));from explore_b3_events import fetch
raw=root/'work/source-acquisition';jobs=json.loads((root/'work/h17-preparation/needed-issuers.json').read_text(encoding='utf-8'))
def collect(job):
 code=job['codeCVM'];p=raw/f'b3-cvm{code}-supplement.json'
 if p.exists():return {**job,'status':'CACHED','source_file':p.name}
 results=[]
 for prefix in sorted({t[:4] for t in job['tickers']}):
  name=f'b3-h17-{code}-{prefix}-supplement'
  try:
   data=fetch('GetListedSupplementCompany',{'issuingCompany':prefix,'language':'pt-br'},name)
   matched=[r for r in data if str(int(r.get('codeCVM') or '0'))==code]
   results.append({'prefix':prefix,'source_file':name+'.json','status':'ACQUIRED' if matched else 'IDENTITY_UNVERIFIED','stock_rows':sum(len(r.get('stockDividends',[])) for r in matched),'subscription_rows':sum(len(r.get('subscriptions',[])) for r in matched),'returned_codes':[r.get('codeCVM') for r in data]})
  except Exception as e:results.append({'prefix':prefix,'status':'FAILED','error':str(e)})
 return {**job,'results':results}
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 for r in pool.map(collect,jobs):
  results.append(r)
  if r.get('status')!='CACHED':print(r['codeCVM'],r['results'],flush=True)
(root/'outputs/h17-event-source-acquisition.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
