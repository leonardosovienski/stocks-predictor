from collections import Counter
import json
from source_utils import OUT, read, pages
from stocks_predictor.cash_source_audit import parse_b3_credit_pages

rows=[];counts=Counter()
old=read(OUT/'current-credit-reconciliation.json')
fields=('isin','action','approval_date','gross_per_share','payment_date')
for d in old['documents']:
    r=parse_b3_credit_pages(pages(d['file']),d['file'][-14:-4])
    counts[r['status']]+=1
    rows.extend(tuple(v[k] for k in fields) for v in r['rows'])
expected=[tuple(v[k] for k in fields) for v in old['credit_rows']]
assert Counter(expected)==Counter(rows)
result=dict(status='EXACT_PARITY',counts=counts,credit_rows=len(rows),documents=len(old['documents']),new_return_evaluations=0)
with (OUT/'parser-validation.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
print(result)
