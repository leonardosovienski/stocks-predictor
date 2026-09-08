"""Immutable reviewed single dates and explicitly reconciled payment schedules."""
from bisect import bisect_right
from copy import deepcopy
from decimal import Decimal as D
import hashlib
import json
from source_utils import ROOT, BASE, OUT, read, pages, norm, dates, amounts
from stocks_predictor.cash_source_audit import expand_reviewed_installments

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=read(OUT/'cash-closure-02.json');events=deepcopy(old['cash_events'])
cards=read(OUT/'cash-review-cards.json');byid={r['event_id']:r for r in events}
sessions=read(ROOT/'work/stocks-final-review-bundle/inputs/quote-tape-index.json')['sessions']
docs={d['local_file']:d for d in read(BASE/'ipe-complete-notices.json')}
law=next(r['tax_source'] for r in events if r.get('net_rule')=='RESIDENT_PF_PRE_2026_ORDINARY_DISTRIBUTION')

def source(n,day,amount):
    name=f'cvm-complete-{n:04d}.pdf';p=BASE/name;m=read(p.with_suffix('.pdf.source.json'))
    assert sha(p)==m['sha256']
    text=norm(pages(name)[0]['text'])
    assert day in {d for d,_,_ in dates(text)} and amounts(text,amount),(name,day,amount)
    assert docs[name]['Data_Entrega']<=day
    return dict(file=str(p),sha256=m['sha256'],url=m['url'],pages=[1],received_on=docs[name]['Data_Entrega'])

facts=[]
for i,n,day in [(189,856,'2023-06-30'),(195,812,'2023-05-16')]:
    row=byid[cards[i]['event_id']];assert row['payment_date'] is None
    sources=[source(n,day,row['gross_per_share'])];pos=bisect_right(sessions,day)
    row.update(payment_date=day,known_on=day,available_on=sessions[pos],sources=sources,
        net_per_share=str(D(row['gross_per_share'])*(D('.85') if row['action']=='JRS CAP PROPRIO' else D(1))),
        tax_source=law,source_review=True,net_rule='RESIDENT_PF_PRE_2026_ORDINARY_DISTRIBUTION',
        actual_broker_cent_rounding_not_verified=True)
    facts.append(dict(card_index=i,event_id=row['event_id'],payment_date=day,sources=sources,method='REVIEWED_TABLE_ENTITLEMENT_DATE_AND_AMOUNT'))

for match in read(OUT/'current-credit-reconciliation.json')['pending_matches']:
    assert match['exact']==1 and len(match['matches'])==1
    c=cards[match['card_index']];r=byid[c['event_id']];m=match['matches'][0];day=m['payment_date']
    assert r['payment_date'] is None and c['ex_date']<=day
    equivalent=[v for v in events if (v['isin'],v['action'],v['ex_date'],D(v['gross_per_share']))==
                (c['isin'],c['action'],c['ex_date'],D(c['gross_per_share']))]
    assert len(equivalent)==1,'Repeated entitlement needs installment review'
    for s in m['sources']:assert sha(__import__('pathlib').Path(s['file']))==s['sha256']
    pos=bisect_right(sessions,day)
    r.update(payment_date=day,known_on=day,available_on=sessions[pos] if pos<len(sessions) else None,
        sources=m['sources'],payment_date_reviewed=True,payment_review_method='B3_EXACT_ISIN_ACTION_APPROVAL_AMOUNT_CREDIT_ROW',
        source_review=False,net_per_share=None,tax_source=None)
    facts.append(dict(card_index=match['card_index'],event_id=r['event_id'],payment_date=day,sources=m['sources'],
        method='REVIEWED_B3_UNIQUE_FULL_IDENTITY_CREDIT',net_evidence_still_required=True))

specs=[
 (115,[(269,'2020-07-24','.079844024'),(270,'2020-09-18','.079844024')]),
 (118,[(269,'2020-07-24','.008242123'),(270,'2020-09-18','.008242123')]),
 (142,[(427,'2021-10-22','.433931936'),(427,'2021-11-16','.433931936'),(428,'2021-12-16','.633970975')]),
 (196,[(813,'2023-06-23','.540074494'),(815,'2023-10-25','.260359162'),(817,'2023-11-17','.433931936')]),
 (211,[(817,'2023-11-17','.173572775'),(818,'2023-11-30','.147536858'),(819,'2023-12-15','.303752355'),(819,'2023-12-20','.158496102')]),
 (248,[(984,'2024-05-13','1.197652144'),(985,'2024-06-28','.373181465'),(986,'2024-07-26','.086786387'),
       (987,'2024-08-30','.173572774'),(988,'2024-09-27','.303752355'),(989,'2024-12-26','.619031470')]),
]
schedules=[]
for i,spec in specs:
    c=cards[i];payments=[]
    for n,day,amount in spec:
        ss=[source(n,day,amount)]
        payments.append({**{k:c[k] for k in ('ticker','isin','ex_date','action')},
            'payment_date':day,'known_on':day,'gross_per_share':amount,
            'net_per_share':str(D(amount)*(D('.85') if c['action']=='JRS CAP PROPRIO' else D(1))),
            'sources':ss,'tax_source':law,'source_review':True,
            'net_rule':'RESIDENT_PF_PRE_2026_ORDINARY_DISTRIBUTION','actual_broker_cent_rounding_not_verified':True})
    ss=[s for r in payments for s in r['sources']]
    delta=sum(D(p['gross_per_share']) for p in payments)-D(c['gross_per_share'])
    schedules.append(dict(card_index=i,parent_event_id=c['event_id'],payments=payments,source_review=True,sources=ss,
        published_rounding=dict(reviewed=True,delta=str(delta),sources=ss,
            reason='Sum of separately rounded published installments; original nominal amount preserved in lineage. No balancing cash adjustment.')))

expanded,lineage=expand_reviewed_installments(events,schedules,sessions)
result=dict(schema='SOURCE_CLOSURE_CASH_3',parent_sha256=sha(OUT/'cash-closure-02.json'),
    source_baseline_sha256=old['source_baseline_sha256'],source_protocol_sha256=old['source_protocol_sha256'],
    cash_events=expanded,facts=old['facts']+facts,schedules=schedules,installment_lineage=lineage,
    withdrawn_staged_matches=old['withdrawn_staged_matches'],corporate_actions=old['corporate_actions'],
    raw_parent_rows=[byid[s['parent_event_id']] for s in schedules],complete_inventory_certified=False,new_return_evaluations=0,
    counts=dict(raw_entitlements=778,execution_payment_rows=len(expanded),new_single_payment_dates=len(old['facts'])+len(facts),
        new_complete_schedules=len(schedules),new_installment_payments=sum(len(s['payments']) for s in schedules),
        missing_payment_before=356,missing_payment_after=sum(not r['payment_date'] for r in expanded),
        missing_net_before=389,missing_net_after=sum(r['net_per_share'] is None for r in expanded),approved_integer_splits=7))
with (OUT/'cash-closure-03.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result['counts']))
