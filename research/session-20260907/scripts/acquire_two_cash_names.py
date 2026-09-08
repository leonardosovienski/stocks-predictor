"""Historical trading names grounded in original B3 quotes, never inferred from returns."""
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'work/profit-cash-source'
raw=ROOT/'work/value-measurement-source/cash-equity-2019.txt'
proof={}
with raw.open('rb') as f:
    for line in f:
        ticker=line[12:24].decode('ascii').strip()
        if ticker in {'JBSS3','LCAM3'} and ticker not in proof:proof[ticker]=line.rstrip(b'\r\n')
jobs=[]
for ticker,line in proof.items():
    name=line[27:39].decode('latin-1').strip()
    trading=name.upper().strip()
    for char in (' ','-','_','/'):trading=trading.replace(char,'',1)
    rows=[];page=1;total=None
    while True:
        params={'tradingName':trading,'language':'pt-br','pageNumber':page,'pageSize':20}
        url='https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetListedCashDividends/'+base64.b64encode(json.dumps(params,separators=(',',':')).encode()).decode()
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=30) as response:data=response.read()
        payload=json.loads(data)
        target=OUT/f'raw-name-{ticker}-cash-{page}.json'
        with target.open('xb') as f:f.write(data)
        with target.with_suffix('.source.json').open('x',encoding='utf-8') as f:json.dump({'url':url,'params':params,'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),'sha256':hashlib.sha256(data).hexdigest()},f,indent=2)
        if total is None:total=payload['page']['totalRecords']
        if total!=payload['page']['totalRecords']:raise ValueError('Changed pagination')
        rows.extend(payload['results'])
        if page>=payload['page']['totalPages']:break
        page+=1
    if len(rows)!=total:raise ValueError('Incomplete pages')
    target=OUT/f'raw-name-{ticker}-cash-all.json'
    with target.open('x',encoding='utf-8') as f:json.dump(rows,f,ensure_ascii=False,indent=2)
    jobs.append({'ticker':ticker,'historical_b3_name':name,'trading_name':trading,'rows':len(rows),'path':str(target),
                 'original_quote_line':line.decode('latin-1'),'quote_excerpt_source':str(raw),
                 'quote_excerpt_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),
                 'identity_and_amounts_require_quote_crosscheck':True})
with (OUT/'two-names-acquisition.json').open('x',encoding='utf-8') as f:json.dump(jobs,f,ensure_ascii=False,indent=2)
print([(r['ticker'],r['historical_b3_name'],r['rows']) for r in jobs])
