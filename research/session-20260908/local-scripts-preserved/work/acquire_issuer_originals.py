"""Original issuer filings on official RI servers; hash, do not infer facts."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import urllib.request
from source_utils import OUT

jobs=[
 ('smto-2018-agm','https://ri.saomartinho.com.br/Download.aspx?Arquivo=J7WGlhW3N77bDQJzf4N3TA%3D%3D&IdCanal=3kK+JHozjxal5isJwnwwEA%3D%3D&linguagem=en'),
 ('rd-2025-manual','https://ri.rdsaude.com.br/Download.aspx?Arquivo=pKXfi%2F3cEpONvABbkeWqvQ%3D%3D&linguagem=pt'),
 ('rd-2024-manual','https://ri.rd.com.br/Download.aspx?Arquivo=4sk+BbZwWdrfICDa4x5t5g%3D%3D&IdCanal=q+YUWbrgVc6JUWPec07dcw%3D%3D'),
 ('rd-2025-agm','https://ri.rdsaude.com.br/Download.aspx?Arquivo=zTOc+6BMhE9k20FC0oYG5w%3D%3D&linguagem=pt'),
]

def get(job):
    name,url=job;p=OUT/'new-primary'/f'issuer-{name}.pdf'
    if p.exists():return {'file':p.name,'status':'EXISTS'}
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req,timeout=30) as r:b=r.read()
        if not b.startswith(b'%PDF-'):raise ValueError('not PDF')
        with p.open('xb') as f:f.write(b)
        with p.with_suffix('.source.json').open('x',encoding='utf-8') as f:
            json.dump(dict(url=url,sha256=hashlib.sha256(b).hexdigest(),retrieved_at_utc=datetime.now(timezone.utc).isoformat()),f,indent=2)
        return {'file':p.name,'status':'DOWNLOADED','bytes':len(b)}
    except Exception as e:return {'url':url,'status':'UNAVAILABLE','error':str(e)}

if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=4) as pool:
        for r in pool.map(get,jobs):print(r,flush=True)
