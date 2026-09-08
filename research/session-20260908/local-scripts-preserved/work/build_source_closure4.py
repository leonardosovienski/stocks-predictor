"""Restore the Ambev JCP as three separately dated rights; no dividend-date join."""
from copy import deepcopy
import hashlib
import json
from source_utils import ROOT, BASE, OUT, read, pages, norm, dates, amounts
from stocks_predictor.cash_source_audit import expand_reviewed_installments

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=read(OUT/'cash-closure-03.json');events=deepcopy(old['cash_events'])
card=read(OUT/'cash-review-cards.json')[318]
parent=next(r for r in events if r['event_id']==card['event_id'])
docs={d['local_file']:d for d in read(BASE/'ipe-complete-notices.json')}
parts=[]
for n,day,gross,net in [(1482,'2026-04-06','.075','.063'),(1484,'2026-07-06','.0755','.0642'),(1485,'2026-10-06','.1185','.1007')]:
    name=f'cvm-complete-{n:04d}.pdf';p=BASE/name;meta=read(p.with_suffix('.pdf.source.json'))
    assert sha(p)==meta['sha256']
    text=norm(pages(name)[0]['text']);assert day in {d for d,_,_ in dates(text)}
    assert amounts(text,gross) and amounts(text,net) and docs[name]['Data_Entrega']<=day
    sources=[dict(file=str(p),sha256=meta['sha256'],url=meta['url'],pages=[1],received_on=docs[name]['Data_Entrega'])]
    parts.append({**{k:parent[k] for k in ('ticker','isin','ex_date','action')},
        'payment_date':day,'known_on':day,'gross_per_share':gross,'sources':sources,
        'net_per_share':None,'tax_source':None,'source_review':False,'published_approximate_net_per_share':net,
        'net_pending_reason':'Issuer rounded/estimated net, including first-parcel rate/precision discrepancy; no exact net inferred.'})
spec=dict(card_index=318,parent_event_id=parent['event_id'],payments=parts,source_review=True,sources=[s for p in parts for s in p['sources']])
sessions=read(ROOT/'work/stocks-final-review-bundle/inputs/quote-tape-index.json')['sessions']
new,lineage=expand_reviewed_installments(events,[spec],sessions)
result={**old,'schema':'SOURCE_CLOSURE_CASH_4','parent_sha256':sha(OUT/'cash-closure-03.json'),
    'cash_events':new,'schedules':old['schedules']+[spec],
    'installment_lineage':old['installment_lineage']+lineage,'raw_parent_rows':old['raw_parent_rows']+[parent]}
result['counts']={**old['counts'],'execution_payment_rows':len(new),'new_complete_schedules':7,
    'new_installment_payments':23,'missing_payment_after':sum(not r['payment_date'] for r in new),
    'missing_net_after':sum(r['net_per_share'] is None for r in new)}
with (OUT/'cash-closure-04.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result['counts']))
