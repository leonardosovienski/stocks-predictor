"""Visual primary PDFs and explicit revised declaration links, preserving raw units."""
from bisect import bisect_right
from copy import deepcopy
from decimal import Decimal as D
import json
from source_utils import ROOT,OUT,read,pages,norm,dates
from closure_helpers import sha,source,original_b3

old=read(OUT/'cash-closure-08.json');events=deepcopy(old['cash_events']);cards=read(OUT/'cash-review-cards.json')
byid={r['event_id']:r for r in events};sessions=read(ROOT/'work/stocks-final-review-bundle/inputs/quote-tape-index.json')['sessions']
law=next(r['tax_source'] for r in events if r.get('net_rule')=='RESIDENT_PF_PRE_2026_ORDINARY_DISTRIBUTION')
facts=[]
def close(i,pay,ss,method,net_literal=None,**review):
    c=cards[i];r=byid[c['event_id']];assert not r['payment_date'] and c['ex_date']<=pay<'2026-01-01'
    ss=original_b3(c)+ss
    r.update(payment_date=pay,known_on=pay,available_on=sessions[bisect_right(sessions,pay)],sources=ss,
        net_per_share=net_literal or str(D(r['gross_per_share'])*(D('.85') if r['action']=='JRS CAP PROPRIO' else D(1))),
        tax_source=law,source_review=True,net_rule='RESIDENT_PF_PRE_2026_ORDINARY_DISTRIBUTION',
        actual_broker_cent_rounding_not_verified=True,payment_review_method=method,**review)
    facts.append(dict(card_index=i,event_id=r['event_id'],payment_date=pay,sources=ss,method=method,**review))

for i,pay,name,literal in [(61,'2019-05-09','cvm-complete-0097.pdf',None),
                         (184,'2023-06-28','cvm-complete-0863.pdf',None),
                         (174,'2023-10-18','cvm-notice-0105.pdf','0.14834705593'),
                         (175,'2023-10-18','cvm-notice-0105.pdf','0.05420598981')]:
    assert len(norm(pages(name)[0]['text']))<100
    c=cards[i]
    close(i,pay,[source(name,pages=[1])],'VISUAL_ORIGINAL_PDF_PAGE_REVIEW',net_literal=literal,
        reviewed_visual_transcription=dict(approval_date=c['approval_date'],last_cum=c['last_cum'],
            gross_per_share=c['gross_per_share'],payment_date=pay,published_net_per_share=literal),
        empty_text_extraction_was_not_missing_document=True)

t=norm(pages('issuer-tupy-2018-nov-payment.pdf')[0]['text'])
assert {'2018-11-07','2018-11-12','2018-11-13','2018-11-26'}<={d for d,_,_ in dates(t)}
for i in [20,21]:
    close(i,'2018-11-26',[source('issuer-tupy-2018-nov-payment.pdf',pages=[1])],
        'SAME_ISSUER_APPROVAL_RECORD_EX_AND_SHARED_DIV_JCP_PAYMENT',
        nominal_source='Exact original B3 entitlement; issuer preliminary unit value differs and is not substituted.',
        preliminary_issuer_nominal='.15001109' if i==20 else '.19686043')

assert sum(D(cards[i]['gross_per_share']) for i in [136,137])==D('2.189670064')
t=norm(pages('issuer-vale-2021-jun-final.pdf')[0]['text']);assert '2,189670064' in t
for i in [136,137]:
    close(i,'2021-06-30',[source('issuer-vale-2021-jun-announcement.pdf',pages=[1]),
        source('issuer-vale-2021-jun-final.pdf',pages=[1])],'ORIGINAL_COMPONENTS_RECONCILE_TO_FINAL_ISSUER_TOTAL',
        issuer_final_total='2.189670064',group_event_ids=[cards[j]['event_id'] for j in [136,137]],
        local_share_payment_not_adr_date=True)
close(207,'2023-09-01',[source('cvm-complete-0899.pdf',pages=[1]),source('cvm-complete-0896.pdf',pages=[1])],
    'INITIAL_PAYMENT_CALENDAR_PLUS_EXPLICIT_FINAL_PER_SHARE_RECTIFICATION',local_share_payment_not_adr_date=True)

result={**old,'schema':'SOURCE_CLOSURE_CASH_9','parent_sha256':sha(OUT/'cash-closure-08.json'),
    'cash_events':events,'facts':old['facts']+facts}
result['counts']={**old['counts'],'new_single_payment_dates':old['counts']['new_single_payment_dates']+len(facts),
    'missing_payment_after':sum(not r['payment_date'] for r in events),
    'missing_net_after':sum(r['net_per_share'] is None for r in events)}
with (OUT/'cash-closure-09.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result['counts']))
