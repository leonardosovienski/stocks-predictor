"""Locate actual fractional-market endpoints in original B3 archives."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sqlite3
import zipfile

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'work/profit-fractional-source'
OUT.mkdir(exist_ok=True)
data=json.loads((ROOT/'outputs/VALIDACAO_LUCRO_STOCKS.json').read_text(encoding='utf-8'))
needed=set()
for trial in data['trials']:
    for p in trial['modes']['open']['periods']:
        for m in p['members']:
            if m['failed_entry']:continue
            needed.add((m['ticker'],p['entry']))
            for t in m['stocks']:needed.add((t,p['exit']))
rows={}; sources=[]
for year in sorted({int(d[:4]) for t,d in needed}):
    path=Path(r'C:\Users\Superleo13\stocks-predictor-work\data')/f'COTAHIST_A{year}.ZIP'
    with path.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
    raw=[]
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            with z.open(name) as f:
                for line in f:
                    if line[:2]!=b'01' or line[24:27]!=b'020':continue
                    symbol=line[12:24].decode('ascii').strip()
                    if not symbol.endswith('F'):continue
                    d=line[2:10].decode('ascii'); day=f'{d[:4]}-{d[4:6]}-{d[6:]}'
                    key=(symbol[:-1],day)
                    if key not in needed:continue
                    scale=int(line[210:217])
                    value={'ticker':symbol,'base_ticker':key[0],'date':day,'isin':line[230:242].decode('ascii'),
                           'open':int(line[56:69])/100/scale,'close':int(line[108:121])/100/scale,
                           'bdi':line[10:12].decode('ascii'),'market_type':'020','quote_factor':scale}
                    if key in rows and rows[key]!=value:raise ValueError('Conflicting fractional quotation')
                    rows[key]=value;raw.append(line.rstrip(b'\r\n'))
    target=OUT/f'fractional-{year}.txt'
    with target.open('xb') as f:f.write(b'\n'.join(raw)+b'\n')
    sources.append({'archive':str(path),'archive_sha256':sha,'excerpt':target.name,'rows':len(raw),
                    'excerpt_sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
    print(year,len(raw),flush=True)
stats=[]
for trial in data['trials']:
    targets=[(m,p) for p in trial['modes']['open']['periods'] for m in p['members'] if m['selected'] and not m['failed_entry']]
    missing=[];price_gaps=[]
    for m,p in targets:
        if (m['ticker'],p['entry']) not in rows:
            missing.append({'asof':p['asof'],'ticker':m['ticker'],'date':p['entry'],'side':'entry'})
        else:price_gaps.append(rows[m['ticker'],p['entry']]['open']/m['entry_price']-1)
        for t in m['stocks']:
            if (t,p['exit']) not in rows:missing.append({'asof':p['asof'],'ticker':t,'date':p['exit'],'side':'exit'})
    stats.append({'family':trial['family'],'holding_months':trial['holding_months'],
                  'selected_entry_tickets':len(targets),'missing_fractional_endpoints':missing,
                  'mean_fractional_minus_standard_open_relative':sum(price_gaps)/len(price_gaps),
                  'max_absolute_fractional_vs_standard_open_gap':max(map(abs,price_gaps)),
                  'no_position_sizing_or_net_return_measured':True})
result={'required_unique_endpoints':len(needed),'found':len(rows),'missing':sorted(needed-set(rows)),
        'rows':list(rows.values()),'sources':sources,'trials':stats,
        'limit':'A daily fractional quote is not a guaranteed fill or evidence of auction depth, bid-ask spread, tax or settlement. No actual small-capital P&L has been inferred.'}
with (ROOT/'outputs/VALIDACAO_FRACIONARIO_STOCKS.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps({k:v for k,v in result.items() if k not in ('rows','sources','missing')},ensure_ascii=False))
