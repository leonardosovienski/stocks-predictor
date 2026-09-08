"""Acquire primary notices omitted by the earlier cash-keyword index.

No ingestion, database changes, feature calculation or returns.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import urllib.request
import zipfile

ROOT=Path(r'C:\Users\Superleo13\stocks-predictor-work\.local-research\stocks-session-20260907')
BASE=ROOT/'work/h19-cash-expanded-source'
OUT=ROOT/'work/source-closure-20260908'
DEST=OUT/'new-primary';DEST.mkdir(exist_ok=True)
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
cards=read(OUT/'cash-review-cards.json')
obs=read(ROOT/'outputs/h18-h19-reorganization-observation.json')
trial=next(t for t in obs['trials'] if t['family']=='H19' and t['holding_months']==3)
ids={m['ticker']:m['cnpj'] for p in trial['periods'] for m in p['members']}
old={d['Link_Download']:d['local_file'] for p in BASE.glob('ipe-*-notices.json') for d in read(p)}
targets=[r for r in cards if not r['candidates']]
jobs=[];seen=set()
for p in sorted(BASE.glob('ipe-*.zip')):
    meta=read(p.with_suffix('.zip.source.json'))
    assert hashlib.sha256(p.read_bytes()).hexdigest()==meta['sha256']
    with zipfile.ZipFile(p) as z:text=z.read(z.namelist()[0]).decode('latin1')
    for d in csv.DictReader(io.StringIO(text),delimiter=';'):
        if d['Categoria'] not in ['Aviso aos Acionistas','Comunicado ao Mercado','Fato Relevante','Assembleia','Reunião da Administração']:continue
        issuer=re.sub(r'\D','',d['CNPJ_Companhia'])
        matches=[r['event_id'] for r in targets if ids[r['ticker']]==issuer
                 and -5<=(date.fromisoformat(d['Data_Referencia'])-date.fromisoformat(r['approval_date'])).days<=12]
        if not matches:continue
        url=d['Link_Download']
        if url in seen:continue
        seen.add(url)
        old_name=old.get(url)
        if old_name and (BASE/old_name).exists():continue
        name='notice-'+hashlib.sha256(url.encode()).hexdigest()[:14]+'.pdf'
        jobs.append({**d,'local_file':name,'matching_events':matches,'index_source':str(p),'index_sha256':meta['sha256']})
(OUT/'additional-notices.json').write_text(json.dumps(jobs,ensure_ascii=False,indent=2),encoding='utf-8')
print('NEW_DOCUMENTS',len(jobs),flush=True)
def fetch(d):
    p=DEST/d['local_file'];metadata=p.with_suffix('.source.json')
    try:
        if p.exists():
            m=read(metadata);assert hashlib.sha256(p.read_bytes()).hexdigest()==m['sha256']
            return {'file':p.name,'status':'CACHE_VERIFIED'}
        url=d['Link_Download']
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=25) as response:
            raw=response.read()
        if not raw.startswith(b'%PDF'):raise ValueError('not a PDF')
        with p.open('xb') as f:f.write(raw)
        m={'url':url,'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
        with metadata.open('x',encoding='utf-8') as f:json.dump(m,f,indent=2)
        return {'file':p.name,'status':'DOWNLOADED','bytes':len(raw)}
    except Exception as exc:return {'file':p.name,'status':'UNAVAILABLE','error':str(exc)}
results=[]
with ThreadPoolExecutor(max_workers=2) as pool:
    for r in pool.map(fetch,jobs):
        results.append(r)
        if len(results)%10==0:print('COMPLETED',len(results),'/',len(jobs),flush=True)
(OUT/'additional-acquisition.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print('FINISHED',len(results),'UNAVAILABLE',sum(r['status']=='UNAVAILABLE' for r in results),flush=True)
