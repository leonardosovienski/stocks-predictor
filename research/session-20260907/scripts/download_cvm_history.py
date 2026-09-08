"""Public raw sources only; no prices, signals or protected returns are read."""
import concurrent.futures
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import shutil
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parent.parent
RAW=ROOT/'work/source-acquisition'
RAW.mkdir(exist_ok=True)
for kind in ('dfp','fre'):
    target=RAW/f'{kind}_cia_aberta_2023.zip'
    if not target.exists():
        shutil.copyfile(next((ROOT/'work/raw').glob(f'*{kind}*.zip')),target)

def fetch(kind,year):
    name=f'{kind}_cia_aberta_{year}.zip'
    path=RAW/name
    url=f'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/{kind.upper()}/DADOS/{name}'
    try:
        if not path.exists():
            req=urllib.request.Request(url,headers={'User-Agent':'stocks-predictor public-source research'})
            with urllib.request.urlopen(req,timeout=60) as r:
                payload=r.read()
            with zipfile.ZipFile(__import__('io').BytesIO(payload)) as z:
                if z.testzip() is not None: raise ValueError('ZIP CRC failed')
            path.write_bytes(payload)
        data=path.read_bytes()
        result={'kind':kind,'year':year,'status':'OK','url':url,'bytes':len(data),
                'sha256':hashlib.sha256(data).hexdigest(),'retrieved_at':datetime.now(timezone.utc).isoformat()}
        (RAW/(name+'.source.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        return result
    except Exception as e:
        return {'kind':kind,'year':year,'status':'FAILED','url':url,'error':repr(e)}

results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    futures=[pool.submit(fetch,kind,year) for year in range(2016,2027) for kind in ('dfp','fre','fca')]
    for f in concurrent.futures.as_completed(futures):
        result=f.result()
        results.append(result)
        print(json.dumps({k:result.get(k) for k in ('kind','year','status','bytes','error') if k in result}),flush=True)
        (ROOT/'outputs/historical-acquisition.json').write_text(json.dumps(sorted(results,key=lambda r:(r['year'],r['kind'])),indent=2)+'\n',encoding='utf-8')
print('ACQUIRED',sum(r['status']=='OK' for r in results),'OF',len(results),flush=True)
