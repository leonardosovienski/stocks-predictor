"""Audit expanded histories and match payment evidence; no return calculation."""
from collections import Counter, defaultdict
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import sys

ROOT=Path(__file__).resolve().parent.parent
WORK=ROOT/'work'
sys.path.insert(0,str(WORK/'stocks-predictor'))
from stocks_predictor.cash_source_audit import br_date, br_decimal, normalize_b3_history
from stocks_predictor.discovery_reorganizations import merged_market

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=read(ROOT/'outputs/VALIDACAO_FONTES_LUCRO_STOCKS.json')
obs=read(ROOT/'outputs/h18-h19-reorganization-observation.json')
bars,_=merged_market(WORK/'value-measurement-source/quotes.db',WORK/'value-measurement-source/identity',
                    WORK/'value-successor-source/successors.db',WORK/'value-successor-source/identity')
with sqlite3.connect((WORK/'value-measurement-source/quotes.db').as_uri()+'?mode=ro',uri=True) as c:
    sessions=[r[0] for r in c.execute('select distinct date from prices_raw order by date')]
by_cnpj={}
for r in read(ROOT/'outputs/b3-historical-acquisition.json'):
    if r['status']=='ACQUIRED':
        by_cnpj[''.join(c for c in r['cnpj'] if c.isdigit())]={'path':str(WORK/f"source-acquisition/b3-cvm{r['codeCVM']}-cash-all.json"),'status':'ORIGINAL_ACQUIRED','codeCVM':r['codeCVM']}
for filename in ('acquisition.json','historical-acquisition.json'):
    for r in read(WORK/'profit-cash-source'/filename):
        if r['status'].startswith('ACQUIRED'):by_cnpj[r['cnpj']]=r
jobs={t:r for r in read(ROOT/'outputs/h17-event-source-acquisition.json') for t in r['tickers']}
for r in read(WORK/'profit-cash-source/two-names-acquisition.json'):
    job=jobs[r['ticker']]
    by_cnpj[job['cnpj']]={**r,'status':'RAW_B3_NAME_REQUIRES_IDENTITY_RECONCILIATION','codeCVM':job['codeCVM']}
needed=defaultdict(set)
for t in obs['trials']:
    for p in t['periods']:
        for m in p['members']:needed[m['cnpj'],m['ticker'],m['isin']].add((p['entry'],p['exit']))
# Original B3 supplements have payment dates but are incomplete historical lists.
payments=defaultdict(dict)
supplement_sources={}
for path in sorted((WORK/'source-acquisition').glob('*supplement.json')):
    payload=read(path)
    if not isinstance(payload,list):continue
    supplement_sources[str(path)]=digest(path)
    for company in payload:
        for row in company.get('cashDividends',[]):
            try:
                key=(row['isinCode'],br_date(row['lastDatePrior']),row['label'],str(br_decimal(row['rate']).normalize()))
                pay=br_date(row['paymentDate'])
                if pay<=key[1]:continue
                payments[key].setdefault(pay,[]).append({'path':str(path),'codeCVM':company['codeCVM']})
            except (ValueError,KeyError):continue
rows=[];instruments=[];issues=[];sources={};groups=defaultdict(list)
for (cnpj,ticker,isin),intervals in sorted(needed.items()):
    source=by_cnpj.get(cnpj)
    if not source:
        instruments.append({'ticker':ticker,'status':'SOURCE_MISSING'})
        continue
    path=Path(source['path']); sources[str(path)]=digest(path)
    raw=read(path);count=0
    for i,r in enumerate(raw):
        if r.get('typeStock')!='ON':continue
        try:cum=br_date(r['lastDatePriorEx'])
        except ValueError:continue
        if not any(a<=cum<b for a,b in intervals):continue
        record={'ticker':ticker,'isin':isin,'cnpj':cnpj,'source_path':str(path),'source_row':i,
                'source_identity_status':source['status']}
        try:
            normalized=normalize_b3_history(r,sessions)
            prior=float(br_decimal(r['closingPricePriorExDate']))/float(br_decimal(r['quotedPerShares']))
            actual=bars.get(ticker,{}).get(cum)
            record.update(normalized,source_prior_close=prior,cotahist_prior_close=actual[1] if actual else None)
            if actual is None or not math.isclose(actual[1],prior,rel_tol=1e-8,abs_tol=.010000001):
                issues.append({**record,'issue':'PRIOR_CLOSE_MISMATCH_OR_MISSING'})
            key=(isin,cum,normalized['action'],str(Decimal(normalized['value_per_share']).normalize()))
            record['b3_supplement_payment_dates']=sorted(payments.get(key,{}))
            record['payment_source_matches']=[p for evidence in payments.get(key,{}).values() for p in evidence]
            rows.append(record);groups[key].append(record);count+=1
        except (KeyError,ValueError) as e:issues.append({**record,'issue':str(e)})
    instruments.append({'ticker':ticker,'isin':isin,'cnpj':cnpj,'status':source['status'],
                        'path':str(path),'total_history_rows':len(raw),'relevant_rows':count,
                        'complete_verified_cash_history':False})
duplicates=[]
for key,values in groups.items():
    # Different approval dates are distinct entitlements, even with the same amount.
    approved=defaultdict(list)
    for v in values:approved[v['approval_date']].append(v)
    for approval,items in approved.items():
        if len(items)>1:
            dates=sorted(payments.get(key,{}))
            duplicates.append({'ticker':items[0]['ticker'],'isin':key[0],'last_cum':key[1],
                               'action':key[2],'amount_per_row':key[3],'approval':approval,'history_rows':len(items),
                               'distinct_supplement_payment_dates':dates,
                               'same_count_of_distinct_payment_dates':len(dates)==len(items),
                               'interpretation':'Repeated values may be separate installments. Neither sum nor deduplicate without terms; count agreement is a clue, not full verification.'})
result={'mode':'EXPANDED_PRIMARY_CASH_FEASIBILITY_NO_RETURN_EVALUATION','instruments':instruments,
        'required_instruments':len(needed),'histories_located':len(instruments)-sum(i['status']=='SOURCE_MISSING' for i in instruments),
        'cash_rows_examined':len(rows),'rows_with_at_least_one_supplement_payment_date':sum(bool(r['b3_supplement_payment_dates']) for r in rows),
        'issue_counts':dict(Counter(r['issue'] for r in issues)),'issues':issues,'exact_repeated_value_groups':duplicates,
        'cash_rows':rows,'source_sha256':sources,'supplement_source_sha256':supplement_sources,
        'all_126_histories_found_does_not_mean_cash_complete':True,'ordinary_cash_return_evaluation_performed':False,
        'why_no_profit_claim':'Dated cash is incomplete; repeated equal amounts can be installments. Historical-name issuer transitions and successor cash need reconciliation. Original equity risk remains large and all descriptive excess-return intervals include zero.'}
result['correction_of_prior_source_audit']='Compare decimal values after removing insignificant trailing zeros. Prior audit retained, no strategy returns were observed in either audit.'
with (ROOT/'outputs/VALIDACAO_PROVENTOS_AMPLIADA_STOCKS_V2.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps({k:v for k,v in result.items() if k not in ('instruments','cash_rows','source_sha256','supplement_source_sha256','issues','exact_repeated_value_groups')},ensure_ascii=False,indent=2))
print('repeated groups',len(duplicates),'matched date counts',sum(d['same_count_of_distinct_payment_dates'] for d in duplicates))
