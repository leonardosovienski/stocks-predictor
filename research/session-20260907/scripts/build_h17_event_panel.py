from pathlib import Path
from datetime import datetime
from decimal import Decimal
import bisect, collections, hashlib, json, sqlite3
root=Path.cwd(); raw=root/'work/source-acquisition'; dest=root/'work/h17-preparation'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
jobs=read(dest/'needed-issuers.json'); job_codes={j['codeCVM'] for j in jobs}
ids=collections.defaultdict(list)
for p in (root/'work/h17-source-identity-v3').glob('identity-*.jsonl'):
 for line in p.read_text(encoding='utf-8').splitlines():
  r=json.loads(line); ids[r['isin']].append(r)
c=sqlite3.connect((root/'work/stocks-tested-real-v2-20260907.db').as_uri()+'?mode=ro',uri=True)
dates=[r[0] for r in c.execute('select distinct date from prices_raw order by date')]
sources=[]; events={}; unmatched={}
for p in sorted(raw.glob('b3-*-supplement.json')):
 try: data=read(p)
 except (ValueError, OSError): continue
 if not isinstance(data,list): continue
 for issuer in data:
  code=str(int(issuer.get('codeCVM') or 0))
  if code not in job_codes: continue
  sources.append({'path':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'codeCVM':code})
  for typ in ('stockDividends','subscriptions'):
   for r in issuer.get(typ,[]):
    try: cum=datetime.strptime(r['lastDatePrior'],'%d/%m/%Y').date().isoformat()
    except (ValueError,KeyError): continue
    if not '2016-01-01'<=cum<='2026-02-02':continue
    ix=bisect.bisect_right(dates,cum)
    if ix==len(dates):continue
    ex=dates[ix]
    try: approved=datetime.strptime(r['approvedOn'],'%d/%m/%Y').date().isoformat()
    except (ValueError,KeyError):approved=None
    matches={x['ticker'] for x in ids[r['isinCode']] if x['first_date']<=cum<=x['last_date']}
    label=r['label'].strip() if typ=='stockDividends' else 'SUBSCRICAO'
    factor=None
    if label in {'DESDOBRAMENTO','BONIFICACAO','GRUPAMENTO'}:
     number=Decimal(r['factor'].replace('.','').replace(',','.'))
     mult=number if label=='GRUPAMENTO' else 1+number/100
     if mult<=0: raise ValueError('invalid factor')
     factor=float(1/mult)
    key=(code,r['isinCode'],cum,label,r.get('factor',r.get('percentage')))
    value={'codeCVM':code,'isin':r['isinCode'],'last_cum':cum,'ex_date':ex,'approved_on':approved,'label':label,'price_factor':factor,'raw':r,'sources':[p.name]}
    if len(matches)==1:
     value['ticker']=next(iter(matches))
     if key in events:
      if events[key]['raw']!=r:events[key].setdefault('source_variants',[]).append({'source':p.name,'raw':r})
      events[key]['sources'].append(p.name)
     else:events[key]=value
    else:
     unmatched[key]={**value,'identity_matches':sorted(matches)}
by=collections.defaultdict(list)
for e in events.values():by[e['ticker']].append(e)
adjustments=[dict(zip(('ticker','ex_date','type','factor','source','approved_by'),r)) for r in c.execute('select ticker,ex_date,type,factor,source,approved_by from adjustments')]
gaps=[]
needed={t for j in jobs for t in j['tickers']}
all_prices=collections.defaultdict(list)
for t,d,o,cl in c.execute("select ticker,date,open/quote_factor,close/quote_factor from prices_raw where market_type='010' order by ticker,date"):
 if t in needed:all_prices[t].append((d,o,cl))
for t in sorted(needed):
 rows=all_prices[t]
 for a,b in zip(rows,rows[1:]):
  if not '2018-01-01'<=b[0]<='2026-02-02':continue
  evs=[e for e in by[t] if a[0]<e['ex_date']<=b[0]]
  fac=1
  known=collections.defaultdict(float)
  for e in evs:
   if e['price_factor']:fac*=e['price_factor'];known[e['ex_date']]+=1
  for e in adjustments:
   if e['ticker']==t and a[0]<e['ex_date']<=b[0] and e['ex_date'] not in known:fac*=e['factor']
  ret=b[1]/(a[2]*fac)-1
  if abs(ret)>.30:gaps.append({'ticker':t,'previous':a[0],'date':b[0],'normalized_overnight':ret,'events':evs})
out={'sources':sources,'events':sorted(events.values(),key=lambda e:(e['ex_date'],e['ticker'],e['label'])),'unmatched':list(unmatched.values()),'legacy_adjustments':adjustments,'unexplained_gaps':gaps}
(dest/'event-panel-preflight.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'events':len(events),'labels':dict(collections.Counter(e['label'] for e in events.values())),'unmatched':len(unmatched),'gaps':len(gaps),'gap_tickers':dict(collections.Counter(e['ticker'] for e in gaps))},indent=2))
