"""Locate exact published nominal values for manual net/tax review only."""
from collections import defaultdict
from decimal import Decimal as D
import json
import re
from source_utils import BASE,OUT,read,norm

cash=[r for r in read(OUT/'cash-closure-07.json')['cash_events'] if r['payment_date'] and r['net_per_share'] is None]
by_amount=defaultdict(list)
for r in cash:by_amount[D(r['gross_per_share'])].append(r)
hits=defaultdict(list);seen=set()
for root in [BASE,OUT/'new-primary']:
    for p in root.glob('*.json'):
        if not p.name.endswith(('.complete-text.json','.extracted.json','.text.json')) or p.name.startswith('b3'):continue
        rr=read(p)
        if not isinstance(rr,list):continue
        for pg in rr:
            if not isinstance(pg,dict) or 'text' not in pg:continue
            t=norm(pg['text']);found=set()
            for m in re.finditer(r'(?<![\d,.])0,\s*\d{4,}(?!\d)',t):
                val=D(re.sub(r'\s+','',m[0]).replace(',','.'))
                found.update(r['event_id'] for r in by_amount.get(val,[]))
            for eid in found:
                name=re.sub(r'\.(complete-text|extracted|text)\.json$','.pdf',p.name)
                key=(eid,name,pg['page'])
                if key in seen:continue
                seen.add(key)
                hits[eid].append(dict(file=name,page=pg['page'],text=t))
result=[dict(event=r,candidates=hits[r['event_id']]) for r in cash]
with (OUT/'net-review-candidates-07.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False)
for r in result:print(r['event']['event_id'],[(c['file'],c['page']) for c in r['candidates'] if 'liquid' in c['text'] or '17,5' in c['text'] or '15%' in c['text']])
