import re
import sys
from source_utils import OUT, read, dates

cards=read(OUT/'cash-review-cards.json')
closed={r['card_index'] for r in read(OUT/'cash-closure-01.json')['facts']}
for p in OUT.glob('curated-cash-round*.json'):
    closed.update(r['card_index'] for r in read(p))
closed.difference_update({172,318})
start,end=map(int,sys.argv[1:])
for i,r in enumerate(cards):
    if i in closed or not start<=i<end:continue
    print('\nCARD',i,r['ticker'],r['ex_date'],r['action'],r['gross_per_share'])
    seen=set()
    for c in r['candidates']:
        if c['text'] in seen:continue
        seen.add(c['text'])
        parts=[]
        for d,a,b in dates(c['text']):
            if d<r['ex_date']:continue
            fragment=c['text'][max(0,a-150):b+80]
            if any(k in fragment for k in ['pag','credit','distribui','liquid','parcela']):parts.append(fragment)
        if parts:print(c['file'],c['page'],c['received'],' | '.join(parts))
