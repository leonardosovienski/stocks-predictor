import sys
from decimal import Decimal as D
from source_utils import BASE, OUT, read

credits=read(BASE/'complete-credit-reconciliation.json')['credit_rows']
cards=read(OUT/'cash-review-cards.json')
for i in map(int,sys.argv[1:]):
    r=cards[i]
    rr=[v for v in credits if v['isin']==r['isin'] and v['action']==r['action'] and
        (v['approval_date']==r['approval_date'] or abs(D(v['value_per_share'])-D(r['gross_per_share']))<D('.000000001'))]
    print('\nCARD',i,r['ticker'],r['approval_date'],r['ex_date'],r['gross_per_share'])
    for c in rr:print({k:v for k,v in c.items() if k not in ['url','source_sha256']})
