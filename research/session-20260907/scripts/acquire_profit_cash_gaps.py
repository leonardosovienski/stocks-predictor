"""Acquire missing public B3 histories; separate immutable directory, two workers."""
import base64
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'work/profit-cash-source'
OUT.mkdir(exist_ok=True)
BASE='https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def fetch(method,params,name):
    path=OUT/(name+'.json')
    if path.exists():return read(path)
    url=BASE+method+'/'+base64.b64encode(json.dumps(params,separators=(',',':')).encode()).decode()
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=30) as r:
        data=r.read()
    value=json.loads(data)
    with path.open('xb') as f:f.write(data)
    with (OUT/(name+'.source.json')).open('x',encoding='utf-8') as f:
        json.dump({'url':url,'params':params,'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),
                   'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)},f,indent=2)
    return value

jobs={r['cnpj']:r for r in read(ROOT/'outputs/h17-event-source-acquisition.json')}
missing={r['cnpj'] for r in read(ROOT/'outputs/VALIDACAO_FONTES_LUCRO_STOCKS.json')['required_instruments']
         if r['status']=='NO_ACQUIRED_B3_ISSUER'}
def collect(cnpj):
    job=jobs[cnpj]; code=job['codeCVM']
    result={'cnpj':cnpj,'codeCVM':code,'tickers':job['tickers']}
    try:
        detail=fetch('GetDetail',{'codeCVM':code,'language':'pt-br'},f'cvm{code}-detail')
        if not isinstance(detail,dict) or ''.join(c for c in detail.get('cnpj','') if c.isdigit())!=cnpj:
            raise ValueError('No matching issuer detail; do not query a replacement issuer')
        trading=detail['tradingName'].upper().strip()
        for char in (' ','-','_','/'):trading=trading.replace(char,'',1)
        rows=[]; total=None; page=1
        while True:
            payload=fetch('GetListedCashDividends',{'tradingName':trading,'language':'pt-br','pageNumber':page,'pageSize':20},f'cvm{code}-cash-{page}')
            if total is None:total=payload['page']['totalRecords']
            if total!=payload['page']['totalRecords']:raise ValueError('Pagination changed')
            rows.extend(payload['results'])
            if page>=payload['page']['totalPages']:break
            page+=1
            if page>100:raise ValueError('Unexpectedly large cash history')
        if len(rows)!=total:raise ValueError('Incomplete cash history')
        path=OUT/f'cvm{code}-cash-all.json'
        if not path.exists():
            with path.open('x',encoding='utf-8') as f:json.dump(rows,f,ensure_ascii=False,indent=2)
        result.update(status='ACQUIRED',rows=total,pages=page,path=str(path),trading_name=trading)
    except Exception as e:result.update(status='UNAVAILABLE',reason=str(e))
    return result

results=[]
with ThreadPoolExecutor(max_workers=2) as pool:
    for r in pool.map(collect,sorted(missing)):
        results.append(r)
        print(json.dumps(r,ensure_ascii=False),flush=True)
with (OUT/'acquisition.json').open('x',encoding='utf-8') as f:json.dump(results,f,ensure_ascii=False,indent=2)
