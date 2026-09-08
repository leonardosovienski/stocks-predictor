"""Read immutable COTAHIST archives into an isolated full-path quote tape."""
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'work/h19-continuous-inputs';BASE.mkdir(exist_ok=True)
def read(p):return json.loads(p.read_text(encoding='utf-8'))
obs=read(ROOT/'outputs/h18-h19-reorganization-observation.json')
trial=next(t for t in obs['trials'] if t['family']=='H19' and t['holding_months']==3)
periods=[p for p in trial['periods'] if any(m['selected'] for m in p['members'])]
ids={(m['ticker'],m['isin']) for p in periods for m in p['members']}
for e in read(ROOT/'work/value-event-terms/reorganizations.json')['events']:
    ids.add((e['ticker'],e['isin']))
    ids.update((s['ticker'],s['isin']) for s in e['stocks'])
symbols={t for t,i in ids};start=periods[0]['asof'];end=periods[-1]['exit']
sources=[];counts=Counter();sessions=set();missing=[]
for year in range(int(start[:4]),int(end[:4])+1):
    archive=Path(r'C:\Users\Superleo13\stocks-predictor-work\data')/f'COTAHIST_A{year}.ZIP'
    with archive.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
    dest=BASE/f'quotes-{year}.jsonl';rawdest=BASE/f'quotes-{year}.cotahist.txt'
    if dest.exists() and rawdest.exists():
        for line in dest.read_text(encoding='utf-8').splitlines():
            r=json.loads(line);sessions.add(r['date']);counts[r['market_type']]+=1
    else:
        rows={};raw=[]
        with zipfile.ZipFile(archive) as z:
            for name in z.namelist():
                with z.open(name) as f:
                    for line in f:
                        if line[:2]!=b'01' or line[24:27] not in (b'010',b'020'):continue
                        symbol=line[12:24].decode('ascii').strip()
                        market=line[24:27].decode('ascii')
                        ticker=symbol[:-1] if market=='020' and symbol.endswith('F') else symbol
                        if ticker not in symbols:continue
                        d=line[2:10].decode('ascii');day=f'{d[:4]}-{d[4:6]}-{d[6:]}'
                        if not start<=day<=end:continue
                        isin=line[230:242].decode('ascii')
                        if (ticker,isin) not in ids:continue
                        factor=int(line[210:217]); scale=Decimal(100*factor)
                        r={'date':day,'ticker':ticker,'isin':isin,'market_type':market,
                           'open':str(Decimal(int(line[56:69]))/scale),'close':str(Decimal(int(line[108:121]))/scale),
                           'volume_fin':str(Decimal(int(line[170:188]))/100),
                           'quantity':int(line[152:170]),'quote_factor':factor}
                        key=(day,ticker,market)
                        if key in rows and rows[key]!=r:raise ValueError(('conflicting raw quote',key))
                        if key not in rows:
                            rows[key]=r;raw.append(line.rstrip(b'\r\n'));sessions.add(day);counts[market]+=1
        with dest.open('x',encoding='utf-8') as f:
            for k,r in sorted(rows.items()):f.write(json.dumps(r,separators=(',',':'))+'\n')
        with rawdest.open('xb') as f:f.write(b'\n'.join(raw)+b'\n')
    sources.append({'archive':str(archive),'sha256':digest,'quotes':dest.name,
        'quotes_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'raw_excerpt':rawdest.name,
        'raw_excerpt_sha256':hashlib.sha256(rawdest.read_bytes()).hexdigest()})
    print(json.dumps({'year':year,'cumulative_rows':dict(counts)}),flush=True)
# Settlement needs exchange sessions beyond the last liquidation day; use the
# previously extracted full exchange calendar, not a weekday approximation.
all_sessions=read(ROOT/'work/h19-selected-dates-v3-bundle/inputs/sessions.json')
settlements={d:all_sessions[i+(3 if d<'2019-05-27' else 2)] for i,d in enumerate(all_sessions)
    if start<=d<=end and i+(3 if d<'2019-05-27' else 2)<len(all_sessions)}
plans={}
for name,selected in [('strategy',True),('comparison',False)]:
    items=[]
    for p in periods:
        items.append({'asof':p['asof'],'entry':p['entry'],'members':[
            {'ticker':m['ticker'],'isin':m['isin'],'lot':1 if m['ticker']=='JBSS32' else 100,
             'tax_class':'bdr' if m['ticker']=='JBSS32' else 'equity'}
            for m in p['members'] if not selected or m['selected']]})
    before=max(d for d in all_sessions if d<end)
    items.append({'asof':before,'entry':end,'members':[]})
    plans[name]=items
result={'source_observation_sha256':hashlib.sha256((ROOT/'outputs/h18-h19-reorganization-observation.json').read_bytes()).hexdigest(),
    'start':start,'end':end,'identities':sorted(ids),'quote_counts':dict(counts),'sources':sources,
    'sessions':all_sessions,'settlements':settlements,'plans':plans,'no_returns_observed':True}
(BASE/'quote-tape-index.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({'complete_quote_extraction':True,'rows':dict(counts),'plans_per_case':len(plans['strategy'])}))
