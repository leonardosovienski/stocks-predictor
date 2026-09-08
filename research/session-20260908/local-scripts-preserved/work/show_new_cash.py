import sys
from source_utils import OUT, read

data = read(OUT / 'new-cash-review-cards.json')
for r in data:
    if len(sys.argv)>1 and r['card_index'] not in set(map(int,sys.argv[1:])):
        continue
    print('\nCARD',r['card_index'],r['ticker'],r['ex_date'],r['action'],r['gross_per_share'])
    for c in r['new_candidates']:
        if not c['record_date_present'] and len(sys.argv)==1:
            continue
        print(c['file'], c['page'], c['received'])
        print(c['text'] if len(sys.argv)>1 else '\n'.join(d+' '+t for d,t in c['dates'] if any(k in t for k in ('paga','pago','credito','remunera','distribui','ex-'))))
