"""Reconcile public issuer tables against the frozen cash queue, without returns."""
from bisect import bisect_right
from collections import Counter
from datetime import date
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sqlite3

ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/'work/h19-cash-expanded-source'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def dt(v):
    v=v.strip();assert re.fullmatch(r'\d{2}/\d{2}/\d{4}',v)
    return date(int(v[6:]),int(v[3:5]),int(v[:2])).isoformat()
def dec(v):return Decimal(v.replace('.','').replace(',','.').strip())
with sqlite3.connect((ROOT/'work/value-measurement-source/quotes.db').as_uri()+'?mode=ro',uri=True) as c:
    sessions=[r[0] for r in c.execute('select distinct date from prices_raw order by date')]
def nxt(d):
    i=bisect_right(sessions,d)
    return sessions[i] if i<len(sessions) else None

facts=[];source_conflicts=[]
def add(ticker,kind,cum,ex,pay,value,quantum,source,row,method='EXACT_DATED_ROW',**kw):
    if ex is None or pay<ex:return
    facts.append(dict(ticker=ticker,action=kind,last_cum=cum,ex_date=ex,payment_date=pay,value=str(value),
                      tolerance=str(quantum/2),source_file=source,source_row=row,method=method,**kw))
for i,r in enumerate(read(BASE/'copasa.tables.json')):
    if len(r)!=7 or not re.fullmatch(r'\d{2}/\d{2}/\d{4}',r[5]) or not re.fullmatch(r'\d{2}/\d{2}/\d{4}',r[6]):continue
    cum=dt(r[5]);scale=Decimal(3 if cum<'2020-11-26' else 1)
    add('CSMG3','JRS CAP PROPRIO' if r[1].startswith('JCP') else 'DIVIDENDO',cum,nxt(cum),dt(r[6]),dec(r[4])*scale,Decimal('1e-10')*scale,'copasa.html',i,'RI_SPLIT_SCALE_RECONCILED',raw_row=r,scale=str(scale))
for i,r in enumerate(read(BASE/'jhsf.tables.json')):
    if len(r)!=9 or r[0]!='JHSF3':continue
    if not all(re.fullmatch(r'\d{2}/\d{2}/\d{4}',v) for v in r[6:9]):continue
    cum,ex,pay=map(dt,r[6:9])
    if cum<'2018-01-01':continue
    if nxt(cum) is None:continue
    if ex!=nxt(cum):
        source_conflicts.append({'source':'jhsf.html','row':i,'raw_row':r,'reason':'RI ex date differs from first exchange session after record date'})
        continue
    add('JHSF3','DIVIDENDO',cum,ex,pay,dec(r[5]),Decimal('1e-10'),'jhsf.html',i,raw_row=r)
for i,r in enumerate(read(BASE/'mrv.tables.json')):
    if len(r)!=6 or not re.fullmatch(r'\d{2}/\d{2}/\d{4}',r[2]):continue
    if not r[1].startswith('Dividendos'):continue # Old JCP is net in this RI table.
    cum=dt(r[2]);add('MRVE3','DIVIDENDO',cum,nxt(cum),dt(r[3]),dec(r[5]),Decimal('1e-7'),'mrv.html',i,raw_row=r)
for i,r in enumerate(read(BASE/'tim.tables.json')):
    if len(r)!=8 or not re.fullmatch(r'\d{2}/\d{2}/\d{4}',r[2]) or not re.fullmatch(r'\d{2}/\d{2}/\d{4}',r[7]):continue
    declared=dt(r[2]);value=dec(r[4]);kind='JRS CAP PROPRIO' if r[0].startswith('Juros') else 'DIVIDENDO'
    ticker='TIMP3' if declared<'2020-10-13' else 'TIMS3'
    add(ticker,kind,None,declared,dt(r[7]),value,Decimal(1).scaleb(value.as_tuple().exponent),'tim.html',i,'RI_DECLARED_EX_DATE',raw_row=r)
for i,r in enumerate(read(BASE/'cielo-table.extracted.json')['PT']):
    if len(r)!=7 or not isinstance(r[3],str) or not re.match(r'20\d\d-',r[3]) or not isinstance(r[4],(int,float)):continue
    value=Decimal(str(r[4]));pay=r[3][:10]
    # Without record date this is a candidate date, even when amount uniquely matches.
    add('CIEL3','JRS CAP PROPRIO' if r[1]=='JSCP' else 'DIVIDENDO',None,'2000-01-01',pay,value,Decimal(1).scaleb(value.as_tuple().exponent),'cielo-table.bin',i,'UNDATED_RI_AMOUNT_CANDIDATE',raw_row=r)

queue=read(ROOT/'outputs/H19_CAIXA_FILA_DE_VALIDACAO.json')['cash_queue']
resolved=[];ambiguous=[];unmatched=[]
for r in queue:
    matches=[]
    for f in facts:
        if f['ticker']!=r['ticker'] or f['action']!=r['action']:continue
        if abs(Decimal(f['value'])-Decimal(r['value_per_share']))>Decimal(f['tolerance']):continue
        method=f['method'];strong=True
        if method=='UNDATED_RI_AMOUNT_CANDIDATE':
            gap=(date.fromisoformat(f['payment_date'])-date.fromisoformat(r['ex_date'])).days
            if not 0<=gap<=370:continue
            strong=False
        elif f['last_cum'] is not None:
            if f['last_cum']!=r['last_cum'] or f['ex_date']!=r['ex_date']:continue
        elif f['ex_date']!=r['ex_date']:
            if f['ex_date']!=r['last_cum']:continue
            method='RI_EX_LABEL_EQUALS_B3_LAST_CUM_REQUIRES_NOTICE';strong=False
        matches.append({**f,'method':method,'dated_amount_reconciled':strong})
    if len(matches)==1:
        f=matches[0];resolved.append({**r,'payment_date':f['payment_date'],'evidence':f,
            'status':'DATED_SOURCE_ROW_RECONCILED' if f['dated_amount_reconciled'] else 'CANDIDATE_DATE_REQUIRES_RECORD_DATE_VERIFICATION',
            'whole_interval_coverage':False})
    elif matches:ambiguous.append({**r,'matches':matches})
    elif r['ticker'] in {f['ticker'] for f in facts}:unmatched.append(r)
result={'issuer_facts':facts,'source_conflicts':source_conflicts,'reconciled_queue_rows':resolved,'ambiguous':ambiguous,'unmatched_for_acquired_issuers':unmatched,
        'new_strategy_returns_observed':False,'source_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in BASE.iterdir() if p.is_file()},
        'not_complete_cash_coverage':True}
(BASE/'reconciliation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'reconciled_rows':len(resolved),'selected':sum(r['selected'] for r in resolved),
 'strong_dated_rows':sum(r['evidence']['dated_amount_reconciled'] for r in resolved),
 'new_dates':sum(not r['candidate_payment_dates'] for r in resolved),
 'new_selected_dates':sum(r['selected'] and not r['candidate_payment_dates'] for r in resolved),
 'by_ticker':dict(Counter(r['ticker'] for r in resolved)),
 'unmatched_selected':[(r['ticker'],r['ex_date'],r['value_per_share']) for r in unmatched if r['selected']],
 'ambiguous':len(ambiguous)},indent=2))
