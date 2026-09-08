"""Join later Hypera payment notices to exact original declaration identities."""
from bisect import bisect_right
from copy import deepcopy
from decimal import Decimal as D
import hashlib
import json
from source_utils import ROOT, BASE, OUT, read, pages, norm, dates, amounts

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=read(OUT/'cash-closure-04.json');events=deepcopy(old['cash_events'])
cards=read(OUT/'cash-review-cards.json');byid={r['event_id']:r for r in events}
docs={d['local_file']:d for d in read(BASE/'ipe-complete-notices.json')}
sessions=read(ROOT/'work/stocks-final-review-bundle/inputs/quote-tape-index.json')['sessions']
law=next(r['tax_source'] for r in events if r.get('net_rule')=='RESIDENT_PF_PRE_2026_ORDINARY_DISTRIBUTION')
facts=[]
raw_sources=[]
for page in range(1,4):
    p=ROOT/f'work/source-acquisition/b3-cvm21431-cash-{page}.json'
    m=read(p.with_suffix('.source.json'));assert sha(p)==m['sha256']
    for n,row in enumerate(read(p)['results']):
        raw_sources.append((row,dict(file=str(p),sha256=m['sha256'],url=m['url'],row=n)))

def original_b3(c):
    iso=lambda s:f'{s[6:]}-{s[3:5]}-{s[:2]}'
    matches=[s for r,s in raw_sources if r['typeStock']=='ON' and r['corporateAction']==c['action']
        and iso(r['dateApproval'])==c['approval_date'] and iso(r['lastDatePriorEx'])==c['last_cum']
        and D(r['valueCash'].replace(',','.'))/D(r['quotedPerShares'])==D(c['gross_per_share'])]
    assert len(matches)==1,(c['event_id'],'B3 declaration identity not unique')
    return matches[0]

def source(name):
    p=BASE/name;m=read(p.with_suffix('.pdf.source.json'));assert sha(p)==m['sha256']
    return dict(file=str(p),sha256=m['sha256'],url=m['url'],pages=[1],received_on=docs[name]['Data_Entrega'])

groups=[([110,116,128,129],261,'2021-01-07'),([132,143,144,149],440,'2022-01-07'),
        ([225,226,242,243,244,260,261,275,276],1247,'2025-12-17')]
for indices,n,pay in groups:
    name=f'cvm-complete-{n:04d}.pdf';text=norm(pages(name)[0]['text'])
    dd={d for d,_,_ in dates(text)};assert pay in dd
    for i in indices:
        c=cards[i];r=byid[c['event_id']];assert r['payment_date'] is None
        assert c['approval_date'] in dd,(i,'original approval absent from payment notice')
        anchors=[p for p in c['candidates'] if p['approval_matched'] and p['last_cum_matched']
                 and amounts(norm(p['text']),c['gross_per_share'])]
        ss=[original_b3(c),source(name)]
        if anchors:ss.append(source(anchors[0]['file']))
        assert all(s.get('received_on',pay)<=pay for s in ss) and c['ex_date']<=pay
        assert len([v for v in events if (v['isin'],v['ex_date'],v['action'],v['gross_per_share'])==
                   (r['isin'],r['ex_date'],r['action'],r['gross_per_share'])])==1
        r.update(payment_date=pay,known_on=pay,available_on=sessions[bisect_right(sessions,pay)],sources=ss,
            net_per_share=str(D(r['gross_per_share'])*(D('.85') if r['action']=='JRS CAP PROPRIO' else D(1))),
            tax_source=law,source_review=True,net_rule='RESIDENT_PF_PRE_2026_ORDINARY_DISTRIBUTION',
            actual_broker_cent_rounding_not_verified=True,
            payment_review_method='ORIGINAL_ISSUER_ENTITLEMENT_PLUS_EXPLICIT_LATER_PAYMENT_LIST_OF_DECLARATIONS')
        facts.append(dict(card_index=i,event_id=r['event_id'],payment_date=pay,sources=ss,
            method=r['payment_review_method'],original_approval_date=c['approval_date']))
result={**old,'schema':'SOURCE_CLOSURE_CASH_5','parent_sha256':sha(OUT/'cash-closure-04.json'),
    'cash_events':events,'facts':old['facts']+facts}
result['counts']={**old['counts'],'new_single_payment_dates':old['counts']['new_single_payment_dates']+len(facts),
    'missing_payment_after':sum(not r['payment_date'] for r in events),
    'missing_net_after':sum(r['net_per_share'] is None for r in events)}
with (OUT/'cash-closure-05.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result['counts']))
