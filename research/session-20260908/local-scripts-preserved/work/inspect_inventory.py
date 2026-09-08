from source_utils import ROOT, OUT, read
from collections import Counter

b=ROOT/'work/stocks-final-review-bundle/inputs'
ev=read(b/'evidence.json')
for k,v in ev.items():
    print(k,'LEN',len(v) if hasattr(v,'__len__') else '')
    if isinstance(v,list):print(v[:2])
    elif k=='execution_checks':print(v)
print('PENDING')
snap=read(OUT/'cash-closure-02.json')
cards={r['event_id']:i for i,r in enumerate(read(OUT/'cash-review-cards.json'))}
for r in snap['cash_events']:
    if not r['payment_date']:print(cards[r['event_id']],r['ticker'],r['ex_date'],r['action'],r['gross_per_share'])
