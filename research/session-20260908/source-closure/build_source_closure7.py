"""Reviewed issuer payment histories joined to original entitlements."""
from bisect import bisect_right
from copy import deepcopy
from decimal import Decimal as D, ROUND_HALF_UP
import json
from source_utils import ROOT, OUT, read, pages, norm, dates
from closure_helpers import sha, iso, source, original_b3

old=read(OUT/'cash-closure-06.json');events=deepcopy(old['cash_events'])
cards=read(OUT/'cash-review-cards.json');byid={r['event_id']:r for r in events}
sessions=read(ROOT/'work/stocks-final-review-bundle/inputs/quote-tape-index.json')['sessions']
law=next(r['tax_source'] for r in events if r.get('net_rule')=='RESIDENT_PF_PRE_2026_ORDINARY_DISTRIBUTION')
facts=[]

def close(i,pay,ss,method,**metadata):
    c=cards[i];r=byid[c['event_id']];assert r['payment_date'] is None
    assert c['ex_date']<=pay<'2026-01-01'
    r.update(payment_date=pay,known_on=pay,available_on=sessions[bisect_right(sessions,pay)],sources=ss,
        net_per_share=str(D(r['gross_per_share'])*(D('.85') if r['action']=='JRS CAP PROPRIO' else D(1))),
        tax_source=law,source_review=True,net_rule='RESIDENT_PF_PRE_2026_ORDINARY_DISTRIBUTION',
        actual_broker_cent_rounding_not_verified=True,payment_review_method=method,**metadata)
    facts.append(dict(card_index=i,event_id=r['event_id'],payment_date=pay,sources=ss,method=method,**metadata))

for i,issuer,row_index,pay,anchor in [
    (2,'ser',12,'2018-09-25',None),(63,'ser',10,'2019-05-24','cvm-complete-0093.pdf'),
    (65,'qualicorp',13,'2019-05-10','cvm-complete-0112.pdf'),
    (89,'qualicorp',12,'2019-08-02','cvm-complete-0113.pdf')]:
    c=cards[i];rr=read(OUT/'new-primary'/f'issuer-{issuer}.tables.json');row=rr[row_index]
    assert iso(row[0])==pay
    literal=row[4].replace('R$','').strip().replace(',','.')
    delta=D(literal)-D(c['gross_per_share'])
    assert abs(delta)<=D('0.0000005') if i==2 else abs(delta)<=D('0.000000001')
    assert len([v for v in rr[1:] if len(v)>4 and v[0].endswith(pay[:4]) and v[4]==row[4]])==1
    ss=original_b3(c)+[source(f'issuer-{issuer}.html',table_row=row_index,retrospective_confirmation=True)]
    if anchor:ss.append(source(anchor,pages=[1]))
    close(i,pay,ss,'EXACT_B3_IDENTITY_PLUS_UNIQUE_ISSUER_PAYMENT_HISTORY',
        published_rounded_gross=literal,published_minus_original_gross=str(delta),
        original_nominal_preserved=True,no_pre_payment_publication_availability_asserted=True)

for indices,table_rows,year in [([235,236],[24,25],'2024'),([293,294],[16,17],'2025')]:
    rr=read(OUT/'new-primary'/'issuer-tim.tables.json')
    twin=[cards[i] for i in indices]
    assert len({(c['ticker'],c['isin'],c['approval_date'],c['ex_date'],c['action'],c['gross_per_share']) for c in twin})==1
    assert len({rr[n][-1] for n in table_rows})==2
    for i,n in zip(indices,table_rows):
        c=cards[i];row=rr[n];assert iso(row[1])==c['approval_date'] and iso(row[2])==c['ex_date']
        assert row[0]=='Dividendos' and row[5]=='Ordinária'
        literal=row[4].replace(',','.');assert abs(D(literal)-D(c['gross_per_share']))<=D('0.0000000005')
        ss=original_b3(c,duplicate_count=2)+[source('issuer-tim.html',table_row=n,retrospective_confirmation=True)]
        if year=='2025':ss.append(source('cvm-complete-1182.pdf',pages=[1]))
        close(i,iso(row[-1]),ss,'ISSUER_TWO_DISTINCT_PAYMENTS_OF_IDENTICAL_ENTITLEMENTS',
            identical_entitlement_group=[c['event_id'] for c in twin],
            date_assignment_rule='Stable row order to two economically interchangeable equal entitlements; not deduplicated.',
            published_rounded_gross=literal,original_nominal_preserved=True)

c=cards[335];row=read(OUT/'new-primary'/'issuer-tim.tables.json')[10]
assert iso(row[1])==c['approval_date'] and iso(row[2])==c['ex_date']
t=norm(pages('cvm-complete-1194.pdf')[0]['text'])
assert '0,7482883774' in t and '0,7491354635' in t and '1.790.000.000,00' in t
close(335,iso(row[-1]),original_b3(c)+[source('issuer-tim.html',table_row=10,retrospective_confirmation=True),
      source('cvm-complete-1194.pdf',pages=[1])],'ISSUER_PAYMENT_HISTORY_LINKED_BY_EXPLICIT_PER_SHARE_RECTIFICATION',
      stale_table_gross='0.7482883774',rectified_gross_preserved=True)

t=norm(pages('notice-f0d1521839c706.pdf')[37]['text']);c=cards[45]
assert {c['approval_date'],c['ex_date'],'2019-03-29'}<={d for d,_,_ in dates(t)}
close(45,'2019-03-29',original_b3(c)+[source('cvm-complete-0158.pdf',pages=[1]),
    source('notice-f0d1521839c706.pdf',pages=[38])],'ALREADY_APPROVED_ADVANCE_EXPLICIT_PAYMENT_DATE',
    excludes_unapproved_remaining_three_installments=True)

c=cards[113];t=norm(pages('issuer-rd-2020-itr.pdf')[2]['text'])
assert c['approval_date'] in {d for d,_,_ in dates(t)} and '03/12/2020' in t
assert D(c['gross_per_share']).quantize(D('.00001'),rounding=ROUND_HALF_UP)==D('.14248')
close(113,'2020-12-03',original_b3(c)+[source('issuer-rd-2020-itr.pdf',pages=[3])],
    'ORIGINAL_CVM_ITR_PAYMENT_FIELD_MATCHED_TO_DECLARATION',published_rounded_gross='0.14248',original_nominal_preserved=True)

result={**old,'schema':'SOURCE_CLOSURE_CASH_7','parent_sha256':sha(OUT/'cash-closure-06.json'),
    'cash_events':events,'facts':old['facts']+facts}
result['counts']={**old['counts'],'new_single_payment_dates':old['counts']['new_single_payment_dates']+len(facts),
    'missing_payment_after':sum(not r['payment_date'] for r in events),
    'missing_net_after':sum(r['net_per_share'] is None for r in events)}
with (OUT/'cash-closure-07.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result['counts']))
