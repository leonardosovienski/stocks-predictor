"""Curated primary relations, separately versioned from the original cash tape.

Payment clauses were reviewed in context. Known multi-section false matches are
excluded or resolved using the full original pages. This is source work only.
"""
from bisect import bisect_right
from copy import deepcopy
from datetime import date, timedelta
from decimal import Decimal as D
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(r'C:\Users\Superleo13\stocks-predictor-work\.local-research\stocks-session-20260907')
BASE=ROOT/'work/h19-cash-expanded-source'
OUT=ROOT/'work/source-closure-20260908'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
cards=read(OUT/'cash-review-cards.json')
proposals=read(OUT/'payment-proposals.json')['unambiguous']
old_path=ROOT/'work/stocks-final-review-bundle/inputs/cash-events.json'
cash=read(old_path);new=deepcopy(cash)
byid={r['event_id']:r for r in new}
index=read(ROOT/'work/stocks-final-review-bundle/inputs/quote-tape-index.json')
sessions=index['sessions']
docs={d['local_file']:d for d in read(BASE/'ipe-complete-notices.json')}
law=ROOT/'work/h19-tax-source/lei-9249.html'
law_source={'file':str(law.relative_to(ROOT)),'sha256':sha(law),
 'url':'http://www.planalto.gov.br/ccivil_03/leis/l9249.htm',
 'scope':'Historical resident-PF distributions paid before 2026: ordinary dividend exempt / JCP 15%; theoretical per-share tax, custody cents not certified.'}
assert law_source['sha256']=='e6fe901511d531cb1063932c6be6d3c9a189ca964c32e69c194b6c65d2f63a72'
facts=[]
def source(name,pages,needles=()):
    path=BASE/name;m=read(path.with_suffix('.pdf.source.json'))
    assert sha(path)==m['sha256']
    txt=path.with_suffix('.extracted.json')
    if not txt.exists():txt=path.with_suffix('.complete-text.json')
    ps=read(txt)
    text=' '.join(' '.join(p['text'].split()) for p in ps if p['page'] in pages)
    for needle in needles:assert needle in text,(name,needle)
    return {'file':str(path.relative_to(ROOT)),'sha256':m['sha256'],'url':m['url'],
            'pages':pages,'received_on':docs[name]['Data_Entrega'],'checked_fragments':list(needles)}
def close(card,payment,sources,method,note=''):
    r=cards[card];t=byid[r['event_id']]
    assert t['payment_date'] is None,(card,'already known')
    assert r['ex_date']<=payment
    assert all(s['received_on']<=payment for s in sources)
    t['payment_date']=payment;t['sources']=sources
    # Conservative known-date policy from the existing tape, unchanged: only
    # recognize the face value at payment, even if an earlier notice existed.
    t['known_on']=payment
    i=bisect_right(sessions,payment)
    t['available_on']=sessions[i] if i<len(sessions) else None
    t['payment_date_reviewed']=True
    t['payment_review_method']=method
    if payment<'2026-01-01' and t['action'] in ['DIVIDENDO','JRS CAP PROPRIO']:
        rate=D('.15') if t['action']=='JRS CAP PROPRIO' else D(0)
        t['net_per_share']=str(D(t['gross_per_share'])*(1-rate))
        t['tax_source']=[law_source];t['source_review']=True
        t['net_rule']='RESIDENT_PF_PRE_2026_ORDINARY_DISTRIBUTION'
        t['actual_broker_cent_rounding_not_verified']=True
    facts.append({'event_id':r['event_id'],'card_index':card,'payment_date':payment,
                  'method':method,'sources':sources,'note':note})

# Reviewed simple relations. These exclusions came from source semantics, not
# from returns: AGM is not payment; installments and different distribution types
# require their own explicit schedule.
excluded={45,161,162,304,305,306,326}
for r in proposals:
    i=r['card_index']
    if i in excluded:continue
    candidates=[h for h in r['payment_candidates'] if h['record_date_present']]
    h=candidates[0]
    close(i,h['payment_date'],[source(h['file'],[h['page']])],
          'REVIEWED_EXACT_ISSUER_RECORD_DATE_AMOUNT_AND_PAYMENT_CLAUSE',h['clause'])

# Same entitlement / identical installments are a group. Source row numbers did
# not encode their payment order; the chronological assignment below is canonical
# and preserves both amounts, dates and all original ancestor row ids.
close(161,'2022-06-30',[source('cvm-complete-0704.pdf',[1,2],['30 de junho de 2022','0,00469805303'])],
      'REVIEWED_INSTALLMENT_SCHEDULE','First of two equal installments; source explicitly says first.')
close(162,'2022-12-26',[source('cvm-complete-0706.pdf',[1,2],['26 de dezembro de 2022','0,00469805303'])],
      'REVIEWED_INSTALLMENT_SCHEDULE','Second installment. The May 2023 paragraph applies to different JCP, not these dividends.')
for i,pay in [(304,'2026-01-07'),(305,'2026-03-04'),(306,'2026-03-04')]:
    close(i,pay,[source('cvm-complete-1361.pdf',[1],['1,244102486','0,768133538','1,569535033'])],
          'REVIEWED_LOCAL_SHARES_SCHEDULE','Local share payment clauses (i)/(ii); ADR dates excluded. 2026 tax treatment remains separately pending.')

assert len({r['event_id'] for r in new})==len(new)==len(cash)
for a,b in zip(cash,new):
    for key in ['event_id','ticker','isin','ex_date','action','gross_per_share']:
        assert a[key]==b[key]
snapshot={'schema':'SOURCE_CLOSURE_CASH_1','source_baseline_sha256':sha(old_path),
 'source_protocol_sha256':'da8b91a7a263d9870822c58af85b4a47f2c051e932ecb3099fea986ba4456c49',
 'new_return_evaluations':0,'complete_inventory_certified':False,
 'cash_events':new,'facts':facts,
 'counts':{'events':len(new),'new_payment_dates':len(facts),
           'missing_payment_before':sum(not r['payment_date'] for r in cash),
           'missing_payment_after':sum(not r['payment_date'] for r in new),
           'missing_net_before':sum(r['net_per_share'] is None for r in cash),
           'missing_net_after':sum(r['net_per_share'] is None for r in new)}}
with (OUT/'cash-closure-01.json').open('x',encoding='utf-8') as f:json.dump(snapshot,f,ensure_ascii=False,indent=2)
print(json.dumps(snapshot['counts']))
