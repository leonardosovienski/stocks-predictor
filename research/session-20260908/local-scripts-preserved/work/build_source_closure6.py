"""Approved AGM terms and explicit retrospective issuer confirmation of payments."""
from bisect import bisect_right
from copy import deepcopy
from decimal import Decimal as D
import hashlib
import json
from pathlib import Path
import re
from source_utils import ROOT, OUT, read, pages, norm, dates, amounts

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=read(OUT/'cash-closure-05.json');events=deepcopy(old['cash_events']);byid={r['event_id']:r for r in events}
cards=read(OUT/'cash-review-cards.json');queue=read(ROOT/'outputs/H19_CAIXA_PAGAMENTOS_REVISADOS_V5.json')['cash_queue']
sessions=read(ROOT/'work/stocks-final-review-bundle/inputs/quote-tape-index.json')['sessions']
law=next(r['tax_source'] for r in events if r.get('net_rule')=='RESIDENT_PF_PRE_2026_ORDINARY_DISTRIBUTION')
iso=lambda s:f'{s[6:]}-{s[3:5]}-{s[:2]}'

def original_b3(c):
    q=next(r for r in queue if (r['ticker'],r['isin'],r['ex_date'],r['action'],D(r['value_per_share']))==
           (c['ticker'],c['isin'],c['ex_date'],c['action'],D(c['gross_per_share'])))
    old_path=Path(q['source_path']);stem=old_path.name.replace('-all.json','')
    matches=[]
    for p in (ROOT/'work'/old_path.parent.name).glob(stem+'-*.json'):
        if not re.search(r'-\d+\.json$',p.name):continue
        m=read(p.with_suffix('.source.json'));assert sha(p)==m['sha256']
        for n,r in enumerate(read(p)['results']):
            if (r['typeStock']=='ON' and r['corporateAction']==c['action'] and iso(r['dateApproval'])==c['approval_date']
                and iso(r['lastDatePriorEx'])==c['last_cum'] and D(r['valueCash'].replace(',','.'))/D(r['quotedPerShares'])==D(c['gross_per_share'])):
                matches.append(dict(file=str(p),sha256=m['sha256'],url=m['url'],row=n))
    assert len(matches)==1,(c['event_id'],len(matches))
    return matches[0]

specs=[(4,'issuer-smto-2018-agm.pdf',[1,3],'2018-08-15','APPROVED_AGM_EX_DATE_AND_PAYMENT'),
       (203,'issuer-rd-2024-manual.pdf',[29,30],'2023-12-01','RETROSPECTIVE_ISSUER_ACTUAL_PAYMENT_TABLE'),
       (215,'issuer-rd-2024-manual.pdf',[29,30],'2023-12-01','RETROSPECTIVE_ISSUER_ACTUAL_PAYMENT_TABLE'),
       (272,'issuer-rd-2025-manual.pdf',[11,30],'2024-12-06','RETROSPECTIVE_ISSUER_EXPLICIT_PAID_STATEMENT')]
facts=[]
for i,name,pp,pay,method in specs:
    c=cards[i];r=byid[c['event_id']];assert r['payment_date'] is None
    p=OUT/'new-primary'/name;m=read(p.with_suffix('.source.json'));assert sha(p)==m['sha256']
    text=norm(' '.join(v['text'] for v in pages(name) if v['page'] in pp));dd={d for d,_,_ in dates(text)}
    assert pay in dd and c['approval_date'] in dd and amounts(text,c['gross_per_share'])
    ss=[original_b3(c),dict(file=str(p),sha256=m['sha256'],url=m['url'],pages=pp,
        retrospective_confirmation=method.startswith('RETROSPECTIVE'),
        knowledge_rule='Historical cash occurrence only, known_on payment; no publication availability or pre-payment valuation asserted.')]
    r.update(payment_date=pay,known_on=pay,available_on=sessions[bisect_right(sessions,pay)],sources=ss,
        net_per_share=str(D(r['gross_per_share'])*(D('.85') if r['action']=='JRS CAP PROPRIO' else D(1))),
        tax_source=law,source_review=True,net_rule='RESIDENT_PF_PRE_2026_ORDINARY_DISTRIBUTION',
        actual_broker_cent_rounding_not_verified=True,payment_review_method=method)
    facts.append(dict(card_index=i,event_id=r['event_id'],payment_date=pay,sources=ss,method=method))
result={**old,'schema':'SOURCE_CLOSURE_CASH_6','parent_sha256':sha(OUT/'cash-closure-05.json'),
    'cash_events':events,'facts':old['facts']+facts}
result['counts']={**old['counts'],'new_single_payment_dates':old['counts']['new_single_payment_dates']+len(facts),
    'missing_payment_after':sum(not r['payment_date'] for r in events),
    'missing_net_after':sum(r['net_per_share'] is None for r in events)}
with (OUT/'cash-closure-06.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result['counts']))
