"""CPFL2025: image table contains all seven payments missed by text extraction."""
from copy import deepcopy
from decimal import Decimal as D
import json
from source_utils import ROOT,OUT,read,pages,norm,dates
from closure_helpers import sha,source,original_b3
from stocks_predictor.cash_source_audit import expand_reviewed_installments

old=read(OUT/'cash-closure-09.json');events=deepcopy(old['cash_events'])
c=read(OUT/'cash-review-cards.json')[290];parent=next(r for r in events if r['event_id']==c['event_id'])
law=next(r['tax_source'] for r in events if r.get('net_rule')=='RESIDENT_PF_PRE_2026_ORDINARY_DISTRIBUTION')
reviewed=[('2025-06-25','.781077485'),('2025-07-25','.433931936'),('2025-08-25','.321109633'),
          ('2025-09-25','.216965968'),('2025-10-27','.173572774'),('2025-11-19','.607504711'),('2025-12-15','.260014244')]
assert sum(D(g) for _,g in reviewed)==D(parent['gross_per_share'])+D('.000000001')
table=source('cvm-complete-1205.pdf',pages=[1],review_method='VISUAL_ORIGINAL_IMAGE_TABLE',
    retrospective_confirmation_of_earlier_installments=True)
parts=[]
for n,(day,gross) in enumerate(reviewed,1199):
    name=f'cvm-complete-{n:04d}.pdf';text=norm(pages(name)[0]['text'])
    assert {day,c['approval_date'],c['ex_date']}<={d for d,_,_ in dates(text)}
    parts.append({**{k:parent[k] for k in ('ticker','isin','ex_date','action')},
        'payment_date':day,'known_on':day,'gross_per_share':gross,'net_per_share':gross,
        'sources':[source(name,pages=[1]),table],'tax_source':law,'source_review':True,
        'net_rule':'RESIDENT_PF_PRE_2026_ORDINARY_DISTRIBUTION','actual_broker_cent_rounding_not_verified':True,
        'published_amount_visually_checked_in_original_pdf_table':True})
spec=dict(card_index=290,parent_event_id=parent['event_id'],payments=parts,source_review=True,
    sources=original_b3(c)+[source('cvm-complete-1198.pdf',pages=[1]),table],
    published_rounding=dict(delta='.000000001',reviewed=True,sources=[table],
        reason='Seven explicitly published per-share payments sum1e-9 above the published aggregate; retain each literal, no balancing payment.'))
sessions=read(ROOT/'work/stocks-final-review-bundle/inputs/quote-tape-index.json')['sessions']
new,lineage=expand_reviewed_installments(events,[spec],sessions)
result={**old,'schema':'SOURCE_CLOSURE_CASH_10','parent_sha256':sha(OUT/'cash-closure-09.json'),
    'cash_events':new,'schedules':old['schedules']+[spec],
    'installment_lineage':old['installment_lineage']+lineage,'raw_parent_rows':old['raw_parent_rows']+[parent]}
result['counts']={**old['counts'],'execution_payment_rows':len(new),'new_complete_schedules':8,
    'new_installment_payments':30,'missing_payment_after':sum(not r['payment_date'] for r in new),
    'missing_net_after':sum(r['net_per_share'] is None for r in new)}
with (OUT/'cash-closure-10.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result['counts']))
