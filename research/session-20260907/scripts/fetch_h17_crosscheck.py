from pathlib import Path
from datetime import datetime, timezone
import concurrent.futures, hashlib, json, urllib.request, urllib.error, urllib.parse
root=Path.cwd();raw=root/'work/source-acquisition'
jobs=json.loads((root/'work/h17-preparation/needed-issuers.json').read_text(encoding='utf-8'))
tickers=sorted({t for j in jobs for t in j['tickers']})
def fetch(t):
 p=raw/f'yahoo-h17-{t}-actions.json'
 url='https://query1.finance.yahoo.com/v8/finance/chart/'+t+'.SA?period1=1451606400&period2=1770076800&interval=1mo&events=splits'
 try:
  if not p.exists():
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=25) as resp:data=resp.read()
   parsed=json.loads(data)
   if parsed.get('chart',{}).get('error'):raise ValueError(str(parsed['chart']['error']))
   p.write_bytes(data)
   p.with_suffix('.source.json').write_text(json.dumps({'url':url,'retrieved_at':datetime.now(timezone.utc).isoformat(),'sha256':hashlib.sha256(data).hexdigest()},indent=2),encoding='utf-8')
  data=json.loads(p.read_bytes());r=data['chart']['result'][0]
  events=r.get('events',{}).get('splits',{})
  return {'ticker':t,'status':'ACQUIRED','events':len(events),'symbol':r['meta']['symbol'],'source_file':p.name}
 except Exception as e:return {'ticker':t,'status':'FAILED','error':str(e)}
if __name__=='__main__':
 import sys
 selected=tickers if '--all' in sys.argv else ['ITSA4','BBDC4','BIDI4','LCAM3','GUAR3','SHUL4']
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(fetch,selected))
 (root/'outputs/h17-secondary-action-acquisition.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
 print(json.dumps(results,indent=2))
