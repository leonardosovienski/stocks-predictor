"""Immutable next version of reviewed facts; original raw event tape untouched."""
from bisect import bisect_right
from copy import deepcopy
from decimal import Decimal as D
import hashlib
import json
from pathlib import Path
from source_utils import ROOT, BASE, OUT, read, pages, norm, dates, amounts

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
baseline=ROOT/'work/stocks-final-review-bundle/inputs'
original=read(baseline/'cash-events.json')
first=read(OUT/'cash-closure-01.json');new=deepcopy(first['cash_events'])
cards=read(OUT/'cash-review-cards.json');index=read(baseline/'quote-tape-index.json')
sessions=index['sessions'];byid={r['event_id']:r for r in new}
docs={d['local_file']:d for d in read(BASE/'ipe-complete-notices.json')}
docs.update({d['local_file']:d for d in read(BASE/'ipe-corporate-notices.json')})
docs.update({d['local_file']:d for d in read(OUT/'additional-notices.json')})

def source(name,pp,needles=()):
    p=BASE/name
    if not p.exists():p=OUT/'new-primary'/name
    mp=p.with_suffix('.pdf.source.json')
    if not mp.exists():mp=p.with_suffix('.source.json')
    meta=read(mp);assert sha(p)==meta['sha256'],name
    text=' '.join(' '.join(v['text'].split()) for v in pages(name) if v['page'] in pp)
    for n in needles:assert norm(n) in norm(text),(name,n)
    return dict(file=str(p.relative_to(ROOT)),sha256=meta['sha256'],url=meta['url'],pages=pp,
                received_on=docs[name]['Data_Entrega'],checked_fragments=list(needles))

def law(name,pp,scope):
    p=OUT/'law'/name;m=read(p.with_suffix('.source.json'));assert sha(p)==m['sha256']
    return dict(file=str(p.relative_to(ROOT)),sha256=m['sha256'],url=m['url'],pages=pp,scope=scope)

# Two staged generic joins confused another action's payment with this JCP.
# Withdraw the proposal entirely, preserving both the staged snapshot and raw row.
withdrawn=[]
for i in (172,318):
    eid=cards[i]['event_id'];prior=deepcopy(byid[eid])
    raw=next(r for r in original if r['event_id']==eid)
    byid[eid].clear();byid[eid].update(deepcopy(raw))
    withdrawn.append(dict(card_index=i,event_id=eid,incorrect_staged_payment=prior['payment_date'],
        reason='Payment clause belongs to DIVIDENDO; this JCP has only a deadline in that document.',
        original_source_preserved=True))

facts=[f for f in first['facts'] if f['card_index'] not in (172,318)]
historical_law=next(r['tax_source'] for r in new if r.get('net_rule')=='RESIDENT_PF_PRE_2026_ORDINARY_DISTRIBUTION')
for path in sorted(OUT.glob('curated-cash-round*.json')):
    for f in read(path):
        i=f['card_index'];c=cards[i];t=byid[c['event_id']];day=f['payment_date']
        assert not t['payment_date'],(i,'already dated')
        ss=[source(f['file'],f['pages'],f.get('checked_fragments',[]))]
        ss.extend(source(e['file'],e['pages']) for e in f.get('extra_sources',[]))
        assert c['ex_date']<=day and all(s['received_on']<=day for s in ss),(i,'chronology')
        text=norm(' '.join(p['text'] for p in pages(f['file']) if p['page'] in f['pages']))
        assert day in {d for d,_,_ in dates(text)},(i,day)
        pos=bisect_right(sessions,day)
        t.update(payment_date=day,known_on=day,available_on=sessions[pos] if pos<len(sessions) else None,
            sources=ss,payment_date_reviewed=True,payment_review_method='EXPLICIT_PRIMARY_RELATION',
            payment_review_note=f['note'])
        if day<'2026-01-01' and t['action'] in ('DIVIDENDO','JRS CAP PROPRIO'):
            t.update(net_per_share=str(D(t['gross_per_share'])*(D('.85') if t['action']=='JRS CAP PROPRIO' else D(1))),
                tax_source=historical_law,source_review=True,net_rule='RESIDENT_PF_PRE_2026_ORDINARY_DISTRIBUTION',
                actual_broker_cent_rounding_not_verified=True)
        published=f.get('published_net_per_share')
        if published:
            assert amounts(text,published),(i,'net not in source')
            assert 0<D(published)<=D(t['gross_per_share'])
            t.update(net_per_share=published,source_review=True,net_rule='PUBLISHED_ISSUER_STANDARD_NET',
                tax_source=ss+[law('mafon-2019.pdf',[42],'Historical JCP paid or individually credited; issuer table identifies2025credit and standardnet, no blanket2026rate.')],
                actual_broker_cent_rounding_not_verified=True)
        facts.append(dict(event_id=t['event_id'],**f,sources=ss))

assert len({r['event_id'] for r in new})==len(new)==len(original)
for a,b in zip(original,new):
    assert all(a[k]==b[k] for k in ('event_id','ticker','isin','ex_date','action','gross_per_share'))

evidence=read(baseline/'evidence.json');actions=[]
split_specs=[
 ('TOTS3','2020-05-04','3','2020-05-06','cvm-corporate-0031.pdf'),
 ('RADL3','2020-09-21','5','2020-09-23','cvm-corporate-0039.pdf'),
 ('HAPV3','2020-11-25','5','2020-11-27','cvm-corporate-0020.pdf'),
 ('CSMG3','2020-11-26','3','2020-11-30','cvm-corporate-0022.pdf'),
 ('ENEV3','2021-03-12','4','2021-03-16','cvm-corporate-0047.pdf'),
 ('CSAN3','2021-05-06','4','2021-05-10','cvm-corporate-0073.pdf'),
 ('PRIO3','2021-05-06','5','2021-05-10','cvm-corporate-0064.pdf'),
]
for ticker,ex,ratio,credit,name in split_specs:
    req=next(r for r in evidence['required_actions'] if r['ticker']==ticker and r['ex_date']==ex)
    identities={isin for t,isin in index['identities'] if t==ticker};assert len(identities)==1
    isin=identities.pop();s=source(name,[1]);assert s['received_on']<=ex
    text=norm(pages(name)[0]['text']);dd={d for d,_,_ in dates(text)}
    assert ex in dd and credit in dd
    actions.append(dict(event_id=req['event_id'],ticker=ticker,isin=isin,ex_date=ex,
        terms_known_on=s['received_on'],source_review=True,sources=[s],
        tax_source=[law('rir-2018.pdf',[84],'RIR/2018 art843 caput and§3II: existing aggregate basis retained; incremental split shares add no cost.')],
        basis_mode='carry',removes_original=True,cash=[],stocks=[dict(ticker=ticker,isin=isin,
            ratio=ratio,basis_fraction='1',credit_date=credit,tradable_on=ex,tax_class='equity',
            fraction_settlement=None)],
        review_scope='Approved integer forward split; same rights; explicit ex trading and credit dates. No fractions for integer original holdings. Same-day dividends use pre-action holdings.'))

result=dict(schema='SOURCE_CLOSURE_CASH_2',parent_sha256=sha(OUT/'cash-closure-01.json'),
    source_baseline_sha256=sha(baseline/'cash-events.json'),source_protocol_sha256=first['source_protocol_sha256'],
    cash_events=new,facts=facts,withdrawn_staged_matches=withdrawn,corporate_actions=actions,
    complete_inventory_certified=False,new_return_evaluations=0,
    counts=dict(events=len(new),new_payment_dates=len(facts),withdrawn_staged_matches=len(withdrawn),
        missing_payment_before=sum(not r['payment_date'] for r in original),
        missing_payment_after=sum(not r['payment_date'] for r in new),
        missing_net_before=sum(r['net_per_share'] is None for r in original),
        missing_net_after=sum(r['net_per_share'] is None for r in new),approved_integer_splits=len(actions)))
with (OUT/'cash-closure-02.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result['counts']))
