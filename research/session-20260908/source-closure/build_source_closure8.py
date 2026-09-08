"""Explicit withholding transitions, corrected TIM dates, approved MGLU split."""
from bisect import bisect_right
from copy import deepcopy
from decimal import Decimal as D
import json
from source_utils import ROOT,BASE,OUT,read,pages,norm,dates,amounts
from closure_helpers import sha,source

old=read(OUT/'cash-closure-07.json');events=deepcopy(old['cash_events']);actions=deepcopy(old['corporate_actions'])
law_old=next(r['tax_source'] for r in events if r.get('net_rule')=='RESIDENT_PF_PRE_2026_ORDINARY_DISTRIBUTION')
def law(name,scope):
    p=OUT/'law'/name;m=read(p.with_suffix('.source.json'));assert sha(p)==m['sha256']
    return dict(file=str(p),sha256=m['sha256'],url=m['url'],scope=scope)
law_jcp=law('lc-224-2025.html','Art.8 and art.14: JCP withholding 17.5% for payment or individual credit from 2026-01-01.')
law_div=law('lei-15270-2025.html','Lei9250 art6A§3 and16A§1XII: pre2026 profits approved in2025, paid in2026-2028 under original terms; residentPF transition.')
facts=[];corrections=[]
sessions=read(ROOT/'work/stocks-final-review-bundle/inputs/quote-tape-index.json')['sessions']
def find(ticker,ex,action='JRS CAP PROPRIO'):
    rows=[r for r in events if (r['ticker'],r['ex_date'],r['action'])==(ticker,ex,action)]
    assert len(rows)==1,(ticker,ex);return rows[0]
def net(r,rate,ss,rule,tax_sources,literal=None,**metadata):
    assert r['net_per_share'] is None and r['payment_date']
    r.update(net_per_share=literal or str(D(r['gross_per_share'])*(1-D(rate))),
        source_review=True,tax_source=tax_sources,net_rule=rule,
        actual_broker_cent_rounding_not_verified=True,**metadata)
    r['sources']+=ss
    facts.append(dict(event_id=r['event_id'],net_per_share=r['net_per_share'],rate=rate,
                      rule=rule,sources=ss,tax_source=tax_sources,**metadata))

# Both declaration years are explicit in the same later primary notice.
for ex,rate in [('2025-04-01','.15'),('2026-03-24','.175')]:
    r=find('TIMS3',ex);assert r['payment_date']=='2026-04-30'
    s=source('cvm-complete-1437.pdf',pages=[1]);t=norm(pages('cvm-complete-1437.pdf')[0]['text'])
    assert amounts(t,r['gross_per_share']) and '2026-04-22' in {d for d,_,_ in dates(t)}
    corrections.append(dict(event_id=r['event_id'],old_payment_date=r['payment_date'],new_payment_date='2026-04-22',source=s,
        reason='Issuer accelerated both payments; the issuer history HTML still displays the superseded date.'))
    r.update(payment_date='2026-04-22',known_on='2026-04-22',available_on=None)
    net(r,rate,[s],'ISSUER_EXPLICIT_RESIDENT_PF_WITHHOLDING',law_old if rate=='.15' else [law_jcp])

specs=[('MULT3','2025-04-01','cvm-complete-1294.pdf',1),('MULT3','2025-06-30','cvm-complete-1295.pdf',1),
       ('VAMO3','2025-12-19','cvm-complete-1347.pdf',1),('CSMG3','2025-12-23','cvm-complete-1330.pdf',2),
       ('EGIE3','2025-12-19','cvm-complete-1211.pdf',1)]
for ticker,ex,name,page in specs:
    r=find(ticker,ex);t=norm(pages(name)[page-1]['text']);assert amounts(t,r['gross_per_share'])
    assert '15%' in t or (ticker=='CSMG3' and '22.12.2025' in t and 'data de credito' in t)
    net(r,'.15',[source(name,pages=[page])],'ISSUER_PRE_2026_CREDIT_OR_EXPLICIT_15_PERCENT',law_old)

r=find('VIVT3','2025-04-14');t=norm(pages('cvm-complete-1228.pdf')[0]['text'])
assert '0,14814432785' in t and '0,12592267868' in t
net(r,'.15',[source('cvm-complete-1228.pdf',pages=[1])],'ISSUER_PUBLISHED_NET_IN_ORIGINAL_EX_DATE_SHARE_UNITS',law_old,
    literal='0.12592267868',subsequent_split_does_not_change_existing_cash_entitlement=True)

# All these JCP entitlements were declared in2026. The rate therefore does not
# depend on deciding whether a2025 declaration was individually credited in2025.
for r in events:
    if r['ex_date']>='2026-01-01' and r['action']=='JRS CAP PROPRIO' and r['payment_date'] and r['net_per_share'] is None:
        assert r['ex_date']<'2027-01-01'
        ss=[];literal=None
        if r['ticker']=='WEGE3':
            t=norm(pages('cvm-complete-1539.pdf')[0]['text']);assert '0,082600000' in t and '17,5%' in t
            ss=[source('cvm-complete-1539.pdf',pages=[1])];literal='0.082600000'
        net(r,'.175',ss,'RESIDENT_PF_JCP_2026_CREDIT_LEGAL_RATE',[law_jcp],literal=literal,
            withholding_only_not_personal_annual_minimum_tax=True)

# Transition is reviewed event by event, never a blanket2026 dividend exemption.
for ticker,ex,name in [('VALE3','2025-12-12','cvm-complete-1361.pdf'),
                      ('SUZB3','2025-12-19','cvm-complete-1309.pdf'),
                      ('TEND3','2025-12-26','cvm-complete-1392.pdf')]:
    t=norm(pages(name)[0]['text']);dd={d for d,_,_ in dates(t)}
    assert '2025' in t and ('balanco' in t or 'lucro' in t)
    for r in events:
        if (r['ticker'],r['ex_date'],r['action'])!=(ticker,ex,'DIVIDENDO'):continue
        assert r['payment_date'] in dd and amounts(t,r['gross_per_share'])
        net(r,'0',[source(name,pages=[1])],'REVIEWED_PRE_2026_PROFITS_APPROVAL_AND_ORIGINAL_2026_PAYMENT_TERMS',[law_div])

# Quantity terms published in CVM before ex-date; later newspaper is corroboration.
name='issuer-mglu-2020-cvm-agm.pdf';t=norm(pages(name)[1]['text'])
assert '1 (uma) acao ordinaria para 4 (quatro)' in t
assert {'2020-10-14','2020-10-16'}<={d for d,_,_ in dates(t)}
requirements=read(ROOT/'work/stocks-final-review-bundle/inputs/evidence.json')['required_actions']
req=next(r for r in requirements if r['ticker']=='MGLU3' and r['ex_date']=='2020-10-14')
index=next(p for p in BASE.glob('ipe-*.zip') if '2020' in p.name);m=read(index.with_suffix('.zip.source.json'));assert sha(index)==m['sha256']
index_source=dict(file=str(index),sha256=m['sha256'],url=m['url'],
    locator='CNPJ47.960.950/0001-21, AGE Ata2020-10-07, protocol022470IPE071020200104411111-35, received2020-10-07.')
a=dict(event_id=req['event_id'],ticker='MGLU3',isin='BRMGLUACNOR2',ex_date='2020-10-14',terms_known_on='2020-10-07',
    source_review=True,sources=[source(name,pages=[1,2],received_on='2020-10-07'),index_source],
    tax_source=deepcopy(actions[0]['tax_source']),basis_mode='carry',removes_original=True,cash=[],
    stocks=[dict(ticker='MGLU3',isin='BRMGLUACNOR2',ratio='4',basis_fraction='1',credit_date='2020-10-16',
        tradable_on='2020-10-14',tax_class='equity',fraction_settlement=None)],
    review_scope='Approved integer forward split: original aggregate fiscal basis retained; explicit credit and trading dates; no fractions.')
assert all(v['event_id']!=a['event_id'] for v in actions);actions.append(a)

result={**old,'schema':'SOURCE_CLOSURE_CASH_8','parent_sha256':sha(OUT/'cash-closure-07.json'),
    'cash_events':events,'corporate_actions':actions,'net_facts':old.get('net_facts',[])+facts,
    'payment_date_corrections':old.get('payment_date_corrections',[])+corrections}
result['counts']={**old['counts'],'missing_net_after':sum(r['net_per_share'] is None for r in events),
    'approved_integer_splits':len(actions),'explicit_payment_date_corrections':len(result['payment_date_corrections'])}
with (OUT/'cash-closure-08.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result['counts']));print('NEW_NET',len(facts))
