"""Use original B3 supplement names for closed instruments; record identity limits."""
from pathlib import Path
import base64
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import urllib.request

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'work/profit-cash-source'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def fetch(params,name):
    path=OUT/(name+'.json')
    if path.exists():return read(path)
    url='https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetListedCashDividends/'+base64.b64encode(json.dumps(params,separators=(',',':')).encode()).decode()
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=30) as r:data=r.read()
    value=json.loads(data)
    with path.open('xb') as f:f.write(data)
    with (OUT/(name+'.source.json')).open('x',encoding='utf-8') as f:json.dump({'url':url,'params':params,'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),'sha256':hashlib.sha256(data).hexdigest()},f,indent=2)
    return value
jobs={r['cnpj']:r for r in read(ROOT/'outputs/h17-event-source-acquisition.json')}
missing=[r for r in read(OUT/'acquisition.json') if r['status']=='UNAVAILABLE']
def collect(old):
    job=jobs[old['cnpj']]; code=old['codeCVM']; result=dict(old)
    try:
        candidates=[]
        filenames=([job['source_file']] if 'source_file' in job else [])+[r['source_file'] for r in job.get('results',[]) if 'source_file' in r]
        for name in filenames:
            path=ROOT/'work/source-acquisition'/name
            for row in read(path):
                if row.get('tradingName'):
                    candidates.append((row,path))
        if not candidates:raise ValueError('No saved B3 historical trading name')
        exact=[x for x in candidates if str(x[0].get('codeCVM'))==code]
        row,path=(exact or candidates)[0]
        trading=row['tradingName'].upper().strip()
        for char in (' ','-','_','/'):trading=trading.replace(char,'',1)
        result.update(name_source=str(path),name_source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                      requested_original_code=code,returned_supplement_code=row['codeCVM'],
                      original_cvm_identity_matches=bool(exact),trading_name=trading)
        rows=[];page=1;total=None
        while True:
            p=fetch({'tradingName':trading,'language':'pt-br','pageNumber':page,'pageSize':20},f'historical-cvm{code}-cash-{page}')
            if total is None:total=p['page']['totalRecords']
            if total!=p['page']['totalRecords']:raise ValueError('Changed pagination')
            rows.extend(p['results'])
            if page>=p['page']['totalPages']:break
            page+=1
            if page>100:raise ValueError('Too many pages')
        if len(rows)!=total:raise ValueError('Incomplete history')
        dest=OUT/f'historical-cvm{code}-cash-all.json'
        with dest.open('x',encoding='utf-8') as f:json.dump(rows,f,ensure_ascii=False,indent=2)
        result.update(status='ACQUIRED_HISTORICAL_NAME' if exact else 'ACQUIRED_IDENTITY_REQUIRES_RECONCILIATION',
                      path=str(dest),rows=total,pages=page)
    except Exception as e:result.update(status='UNAVAILABLE',reason=str(e))
    return result
with ThreadPoolExecutor(max_workers=2) as pool:
    results=list(pool.map(collect,missing))
with (OUT/'historical-acquisition.json').open('x',encoding='utf-8') as f:json.dump(results,f,ensure_ascii=False,indent=2)
for r in results:print(json.dumps(r,ensure_ascii=False),flush=True)
