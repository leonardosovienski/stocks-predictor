"""Download distinct B3 section candidates; never replace an existing source."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import urllib.request
from source_utils import OUT

jobs=[('2023-05-31', s) for s in ('04-1','04','00')]+[('2026-04-14','04-1')]

def get(job):
    day,section=job
    url=f'https://arquivos.b3.com.br/bdi/download/bdi/{day}/BDI_{section}_{day.replace("-", "")}.pdf'
    path=OUT/'new-primary'/f'b3-section-{section}-{day}.pdf'
    if path.exists():return {'file':path.name,'status':'EXISTS'}
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req,timeout=35) as r:data=r.read()
        if not data.startswith(b'%PDF-'):raise ValueError('not PDF')
        with path.open('xb') as f:f.write(data)
        meta=dict(url=url,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),retrieved_at_utc=datetime.now(timezone.utc).isoformat())
        with path.with_suffix('.source.json').open('x',encoding='utf-8') as f:json.dump(meta,f,indent=2)
        return {'file':path.name,'status':'DOWNLOADED','bytes':len(data)}
    except Exception as e:return {'url':url,'status':'UNAVAILABLE','error':str(e)}

if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=3) as pool:
        for item in pool.map(get,jobs):print(json.dumps(item),flush=True)
