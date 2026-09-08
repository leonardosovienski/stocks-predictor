"""Read-only source feasibility; does not observe new strategy returns."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
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

def read(path): return json.loads(path.read_text(encoding='utf-8'))
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
obs=read(ROOT/'outputs/h18-h19-reorganization-observation.json')
bars, identities=merged_market(WORK/'value-measurement-source/quotes.db',WORK/'value-measurement-source/identity',
                              WORK/'value-successor-source/successors.db',WORK/'value-successor-source/identity')
with sqlite3.connect((WORK/'value-measurement-source/quotes.db').as_uri()+'?mode=ro',uri=True) as con:
    sessions=[r[0] for r in con.execute('select distinct date from prices_raw order by date')]
issuers={''.join(c for c in x['cnpj'] if c.isdigit()):x for x in read(ROOT/'outputs/b3-historical-acquisition.json')}
needed=defaultdict(list)
for t in obs['trials']:
    for p in t['periods']:
        for m in p['members']:
            needed[m['cnpj'],m['ticker'],m['isin']].append((p['entry'],p['exit']))
issues, rows, sources, coverage = [], [], {}, []
for (cnpj,ticker,isin),intervals in sorted(needed.items()):
    issuer=issuers.get(cnpj)
    if not issuer or issuer['status']!='ACQUIRED':
        coverage.append({'cnpj':cnpj,'ticker':ticker,'status':'NO_ACQUIRED_B3_ISSUER'})
        continue
    path=WORK/f"source-acquisition/b3-cvm{issuer['codeCVM']}-cash-all.json"
    raw=read(path)
    sources[str(path)]=digest(path)
    unique={}
    counts=Counter()
    for i,r in enumerate(raw):
        if r['typeStock']!='ON':continue
        try:
            cum=br_date(r['lastDatePriorEx'])
        except ValueError:
            issues.append({'ticker':ticker,'row':i,'reason':'INVALID_CUM_DATE'})
            counts['invalid']+=1
            continue
        # Entry is already ex for rights whose last cum is before acquisition.
        if not any(start<=cum<end for start,end in intervals):continue
        record={'ticker':ticker,'isin':isin,'cnpj':cnpj,'source_file':path.name,'source_row':i,'last_cum':cum}
        try:
            normalized=normalize_b3_history(r,sessions)
            reported_close=float(br_decimal(r['closingPricePriorExDate'])) / float(br_decimal(r['quotedPerShares']))
            actual=bars.get(ticker,{}).get(cum)
            record.update(normalized)
            record['reported_prior_close']=reported_close
            record['cotahist_prior_close']=actual[1] if actual else None
            record['prior_close_matches_raw']=actual is not None and math.isclose(reported_close,actual[1],rel_tol=1e-8,abs_tol=.010000001)
            key=(normalized['approval_date'],normalized['last_cum'],normalized['action'],normalized['security_class'])
            if key in unique:
                counts['duplicate_key']+=1
                issues.append({**record,'reason':'DUPLICATE_ECONOMIC_KEY','other_row':unique[key]})
            unique[key]=i
            counts['normalized']+=1
            if not record['prior_close_matches_raw']:
                counts['prior_close_conflict']+=1
                issues.append({**record,'reason':'PRIOR_CLOSE_MISSING_OR_DIFFERS_FROM_RAW'})
            if normalized['action'] not in {'DIVIDENDO','JRS CAP PROPRIO','RENDIMENTO'}:
                counts['other_cash_action']+=1
            rows.append(record)
        except (ValueError, KeyError) as exc:
            counts['invalid']+=1
            issues.append({**record,'reason':str(exc)})
    coverage.append({'cnpj':cnpj,'ticker':ticker,'isin':isin,'status':'SINGLE_SOURCE_NO_PAYMENT_HISTORY',
                     'b3_pages':issuer['pages'],'counts':dict(counts),'full_executable_cash_coverage':False})
ticket=[]
for t in obs['trials']:
    for capital in (5000,10000):
        n=whole=less_one=0
        rounding=[]
        for p in t['periods']:
            selected=[m for m in p['members'] if m['selected']]
            if not selected:continue
            for m in selected:
                price=bars.get(m['ticker'],{}).get(p['entry'])
                if not price:continue
                ticket_value=capital/len(selected)
                q=math.floor(ticket_value/(price[0]*(1+.0036)))
                n+=1
                whole+=q>=100
                less_one+=q==0
                rounding.append((ticket_value-q*price[0]*(1+.0036))/capital)
        ticket.append({'family':t['family'],'holding_months':t['holding_months'],'capital_brl':capital,
                       'selected_tickets_with_quote':n,'tickets_under_100_shares':n-whole,'tickets_below_one_share':less_one,
                       'mean_rounding_cash_fraction_per_ticket':sum(rounding)/len(rounding),
                       'full_portfolio_or_fractional_fill_validation':False})
hash_checks=[]
for s,sha in obs['input_sha256'].items():
    path=Path(s)
    hash_checks.append({'path':s,'matches':path.exists() and digest(path)==sha})
if not all(r['matches'] for r in hash_checks):raise ValueError('Prior measured input changed')
result={'observed_at_utc':datetime.now(timezone.utc).isoformat(),'mode':'SOURCE_AND_TICKET_FEASIBILITY_NOT_NEW_RETURNS',
        'input_hashes_unchanged':hash_checks,'ordinary_cash_rows_examined':len(rows),
        'cash_issue_counts':dict(Counter(r['reason'] for r in issues)),
        'cash_issues':issues,'required_instruments':coverage,'cash_rows':rows,
        'source_sha256':sources,'ticket_feasibility':ticket,
        'conclusion':'No full ordinary-cash execution certification: pagination supplies entitlement values, not historic payment dates. Price agreement does not independently prove complete dividend coverage, cash basis or payment.',
        'net_profit_claim':False}
out=ROOT/'outputs/VALIDACAO_FONTES_LUCRO_STOCKS.json'
with out.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps({k:v for k,v in result.items() if k not in ('cash_issues','required_instruments','cash_rows','source_sha256','input_hashes_unchanged')},indent=2))
