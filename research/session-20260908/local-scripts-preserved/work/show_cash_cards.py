import json
from pathlib import Path
import sys

BASE=Path(r'C:\Users\Superleo13\stocks-predictor-work\.local-research\stocks-session-20260907\work\source-closure-20260908')
cards=json.loads((BASE/'cash-review-cards.json').read_text(encoding='utf-8'))
if sys.argv[1]=='proposals':
    data=json.loads((BASE/'payment-proposals.json').read_text(encoding='utf-8'))
    for r in data['unambiguous'][int(sys.argv[2]):int(sys.argv[3])]:
        h=r['payment_candidates'][0]
        print(r['card_index'],r['ticker'],r['ex_date'],r['gross_per_share'],h['payment_date'],h['file'],h['clause'])
else:
    for i in map(int,sys.argv[1:]):
        r=cards[i]
        print('\nCARD',i,{k:v for k,v in r.items() if k!='candidates'})
        seen=set()
        for c in r['candidates']:
            key=(c['file'],c['page'])
            if key in seen:continue
            seen.add(key)
            print('PAGE',c['file'],c['page'],'received',c['received'])
            print(c['text'])
