"""Save primary issuer history and B3 credit records for a bounded repair pilot."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'work/h19-cash-closure-source';OUT.mkdir(exist_ok=True)
jobs=[('jbs-20230619-notice.pdf','https://api.mziq.com/mzfilemanager/v2/d/043a77e1-0127-4502-bc5b-21427b991b22/11a431b2-5282-5345-0234-53fdf7524bfb?origin=1'),
      ('jbs-dividends.html','https://ir.jbsglobal.com/shareholder-information/dividends/'),
      ('b3-credit-20250612.pdf','https://arquivos.b3.com.br/bdi/download/bdi/2025-06-12/BDI_05_20250612.pdf'),
      ('b3-credit-20230629.pdf','https://arquivos.b3.com.br/bdi/download/bdi/2023-06-29/BDI_05_20230629.pdf')]
def fetch(job):
    name,url=job;path=OUT/name
    if path.exists():return {'file':name,'status':'CACHED'}
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=40) as r:data=r.read()
        if name.endswith('.pdf') and not data.startswith(b'%PDF'):raise ValueError('Non-PDF response')
        with path.open('xb') as f:f.write(data)
        meta={'url':url,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'retrieved_at_utc':datetime.now(timezone.utc).isoformat()}
        with path.with_suffix('.source.json').open('x',encoding='utf-8') as f:json.dump(meta,f,indent=2)
        return {'file':name,'status':'ACQUIRED',**meta}
    except Exception as e:return {'file':name,'status':'FAILED','reason':str(e)}
with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(fetch,jobs))
print(json.dumps(results,indent=2))
