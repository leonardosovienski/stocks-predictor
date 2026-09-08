"""Freeze new dated facts and construct a runnable, honest evidence gate."""
from bisect import bisect_right
from collections import Counter
from decimal import Decimal as D
import hashlib, json, shutil, urllib.request
from pathlib import Path

root=Path(__file__).resolve().parents[1];base=root/'work/h19-cash-expanded-source'
dest=root/'work/h19-continuous-bundle';inputs=dest/'inputs';inputs.mkdir(parents=True,exist_ok=True)
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,value):p.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
old=root/'outputs/H19_CAIXA_PAGAMENTOS_REVISADOS_V4.json';registry=read(old)
credits=read(base/'complete-credit-reconciliation.json');changes=[]
identity=lambda r:tuple(r[k] for k in ('isin','ex_date','action','value_per_share','source_row'))
lookup={identity(r):r for r in registry['cash_queue']}
for m in credits['exact_unique_queue_matches']:
    r=lookup[identity(m['row'])]
    if r['payment_date_reviewed']:continue
    e=m['evidence'];assert sha(base/e['source_file'])==e['source_sha256']
    r['payment_date_reviewed']=True
    r['reviewed_payment']={k:r[k] for k in ('ticker','isin','ex_date','last_cum','action','value_per_share')}
    r['reviewed_payment'].update(payment_date=e['payment_date'],sources=[e],
        method='EXACT_B3_ISIN_TYPE_APPROVAL_AMOUNT_CREDIT_ALL_PAGES',net_amount_reviewed=False)
    r['candidate_payment_dates']=sorted(set(r['candidate_payment_dates'])|{e['payment_date']})
    changes.append({'identity':identity(r),'payment_date':e['payment_date']})
registry['schema']='H19_REVIEWED_PAYMENT_DATES_5'
registry['summary']={
    'queue_rows':len(lookup),'selected_rows':sum(r['selected'] for r in lookup.values()),
    'reviewed_payment_rows':sum(r['payment_date_reviewed'] for r in lookup.values()),
    'selected_reviewed_payment_rows':sum(r['selected'] and r['payment_date_reviewed'] for r in lookup.values()),
    'without_candidate_date':sum(not r['candidate_payment_dates'] for r in lookup.values()),
    'selected_without_candidate_date':sum(r['selected'] and not r['candidate_payment_dates'] for r in lookup.values())}
registry['v5_increment']={'baseline_sha256':sha(old),'changes':changes,
    'all_page_credit_reconciliation_sha256':sha(base/'complete-credit-reconciliation.json'),
    'no_historical_returns_observed':True,'cash_coverage_not_certified':True}
write(root/'outputs/H19_CAIXA_PAGAMENTOS_REVISADOS_V5.json',registry)

taxdir=root/'work/h19-tax-source';legal=taxdir/'lei-9249.html'
url='http://www.planalto.gov.br/ccivil_03/leis/l9249.htm'
if not legal.exists():
    with urllib.request.urlopen(url,timeout=40) as response:legal.write_bytes(response.read())
tax_source={'file':legal.name,'url':url,'sha256':sha(legal),
    'scope':'Lei 9.249/1995 arts.9 paragraph2 (15% historical text) and10 (pre-2026); resident PF scenario'}
write(legal.with_suffix('.source.json'),tax_source)

obs=read(root/'outputs/h18-h19-reorganization-observation.json')
trial=next(t for t in obs['trials'] if t['family']=='H19' and t['holding_months']==3)
periods=[p for p in trial['periods'] if any(m['selected'] for m in p['members'])]
terms=read(root/'work/value-event-terms/reorganizations.json')['events']
intervals=set()
for period in periods:
    for member in period['members']:
        pending=[(member['ticker'],member['isin'],period['entry'])];seen=set()
        while pending:
            ticker,isin,start=pending.pop();key=(ticker,isin,start)
            assert key not in seen;seen.add(key)
            actions=[e for e in terms if e['ticker']==ticker and e['isin']==isin and start<e['ex_date']<=period['exit']]
            finish=min((e['ex_date'] for e in actions if e['removes_original']),default=period['exit'])
            intervals.add((ticker,isin,start,finish))
            for e in actions:
                for leg in e['stocks']:pending.append((leg['ticker'],leg['isin'],e['ex_date']))
index=read(root/'work/h19-continuous-inputs/quote-tape-index.json')
bonus=read(root/'work/h19-continuous-inputs/bonus-asset-coverage.json')
index['sources'].append(bonus)
index['identities']+=bonus['identities']
index['security_lots']={t:1 if t=='JBSS32' else 100 for t,i in index['identities']}
sessions=index['sessions']
cash=[];covered=set()
for schedule in registry.get('installment_schedule_reviews',[]):
    group=[r for r in lookup.values() if r['isin']==schedule['isin'] and r['ex_date']==schedule['ex_date'] and r['action']==schedule['action']]
    assert sum(D(r['value_per_share']) for r in group)==D(schedule['declared_total_per_share'])
    covered.update(identity(r) for r in group)
    for ins in schedule['installments']:
        cash.append({'event_id':f"{schedule['isin']}:{schedule['ex_date']}:installment:{ins['number']}",
            'ticker':schedule['ticker'],'isin':schedule['isin'],'ex_date':schedule['ex_date'],
            'action':schedule['action'],'payment_date':ins['payment_date'],
            'gross_per_share':ins['gross_per_share'],
            'sources':[{'source_file':schedule['source_file'],'source_sha256':schedule['source_sha256']}],
            'net_per_share':None,'source_review':False})
for r in lookup.values():
    if identity(r) in covered:continue
    fact=r.get('reviewed_payment') or {}
    cash.append({'event_id':f"{r['isin']}:{r['ex_date']}:{r['action']}:{r['source_row']}",
        'ticker':r['ticker'],'isin':r['isin'],'ex_date':r['ex_date'],'action':r['action'],
        'payment_date':fact.get('payment_date'),'gross_per_share':r['value_per_share'],
        'sources':fact.get('sources',[]),'net_per_share':fact.get('net_per_share_reported') if fact.get('net_amount_reviewed') else None,
        'tax_source':fact.get('sources',[]) if fact.get('net_amount_reviewed') else None,
        'source_review':bool(fact.get('net_amount_reviewed'))})
for r in cash:
    pay=r['payment_date'];i=bisect_right(sessions,pay) if pay else len(sessions)
    r['available_on']=sessions[i] if i<len(sessions) else None
    # Conservative knowledge cutoff: source-confirmed payment date, not an
    # invented ex-date announcement. Unknown face values are censored in NAV.
    r['known_on']=pay
    if pay and pay<'2026-01-01' and r['action'] in ('DIVIDENDO','JRS CAP PROPRIO') and r['net_per_share'] is None:
        rate=D(0) if r['action']=='DIVIDENDO' else D('.15')
        r['net_per_share']=str(D(r['gross_per_share'])*(1-rate))
        r['tax_source']=[tax_source];r['source_review']=True
        r['net_rule']='RESIDENT_PF_PRE_2026_ORDINARY_DISTRIBUTION'
        r['actual_broker_cent_rounding_not_verified']=True

prior=read(root/'outputs/H19_CAIXA_EXECUCAO_V3.json')
gaps=[g for g in prior['issues'] if g['kind'] in ('CORPORATE_TAX_AND_DELIVERY','ORDINARY_STOCK_ACTION_DELIVERY_AND_BASIS','JBS_HISTORY_TRUNCATED')]
required_actions=[{'event_id':f"{g['ticker']}:{g['ex_date']}:{g.get('label','REORGANIZATION')}",**g}
                  for g in gaps if 'ex_date' in g]
evidence={'required_intervals':sorted(intervals),'cash_coverage':[],
    'required_actions':required_actions,'action_gaps':gaps,
    'execution_checks':{
        'quotes':{'verified':False,'sources':['quote-coverage.json'],
            'reason':'76,301 initial holding days and 125 PN days complete; legal rounding and delivery paths not fully reconciled.'},
        'corporate_actions':{'verified':False,'sources':['corporate-primary-findings.json']},
        'tax_schedule':{'verified':True,'sources':['tax-calendar.json']},
        'cash_coverage_inventory':{'verified':False,'sources':['reviewed-payment-dates.json']}},
    'additional_issues':[
        {'kind':'CORPORATE_SECURITY_CLASS','ticker':'RENT3','delivered_security':'RENT4','ex_date':'2025-12-30',
         'quotes_acquired':True,'reason':'RENT4 quotes acquired; physical bonus, revised operational ratio and tax still require integrated review.'},
        {'kind':'CORPORATE_SECURITY_CLASS','ticker':'CYRE3','delivered_security':'CYRE4','ex_date':'2026-01-02',
         'quotes_acquired':True,'reason':'CYRE4 quotes acquired; preferred bonus, fractions and fiscal delivery path require integration.'},
        {'kind':'FRACTION_TAX_DEPENDS_ON_PORTFOLIO','reason':'Auction net-of-fees proceeds are not automatically net of personal income tax.'},
        {'kind':'SUCCESSOR_CASH_INVENTORY','reason':'Original queue does not certify successor or PN distributions.'},
        {'kind':'BROKER_CASH_ROUNDING','reason':'Theoretical per-share net values are not cent-rounded custody-account confirmations.'}]}
shutil.copy2(root/'work/h19-selected-dates-v3-bundle/inputs/protocol.json',inputs/'protocol.json')
write(inputs/'quote-tape-index.json',index)
write(inputs/'tax-calendar.json',read(root/'work/h19-continuous-inputs/tax-calendar-complete.json')['calendar'])
write(inputs/'cash-events.json',cash);write(inputs/'corporate-actions.json',[])
write(inputs/'evidence.json',evidence);write(inputs/'reviewed-payment-dates.json',registry)
shutil.copy2(root/'work/h19-continuous-inputs/quote-coverage.json',inputs/'quote-coverage.json')
shutil.copy2(root/'work/h19-continuous-inputs/bonus-asset-coverage.json',inputs/'bonus-asset-coverage.json')
shutil.copy2(root/'outputs/H19_EVENTOS_SOCIETARIOS_CONFERIDOS.json',inputs/'corporate-primary-findings.json')
for src in index['sources']:shutil.copy2(root/'work/h19-continuous-inputs'/src['quotes'],inputs/src['quotes'])
write(inputs/'SHA256.json',{p.name:sha(p) for p in inputs.iterdir() if p.is_file() and p.name!='SHA256.json'})
print(json.dumps({'registry':registry['summary'],'cash_events':len(cash),
    'source_reviewed_dated_net':sum(r['source_review'] for r in cash),'required_intervals':len(intervals),
    'required_actions':len(required_actions),'new_returns':0},indent=2))
