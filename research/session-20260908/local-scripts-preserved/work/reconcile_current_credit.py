"""B3 credit candidates, restricted to observed credit tables and exact identity."""
from collections import Counter
from decimal import Decimal as D
import hashlib
import json
import re
from source_utils import OUT, read, pages, norm

rx=re.compile(r'\b(br[a-z0-9]{10})\s+(\d+\s+)?(dividendo|rendimento|juros\s+sobre\s+capital\s+proprio)\s+(\d{2}/\d{2}/\d{4})\s+([\d.,]+)\s+(\d{2}/\d{2}/\d{4})')
iso=lambda t:f'{t[6:]}-{t[3:5]}-{t[:2]}'
rows=[];documents=[]
for p in sorted((OUT/'new-primary').glob('b3-section-04-1-*.pdf')):
    meta=read(p.with_suffix('.source.json'));assert hashlib.sha256(p.read_bytes()).hexdigest()==meta['sha256']
    pp=pages(p.name);heading=any('credito de proventos' in norm(v['text']) for v in pp)
    found=[]
    if heading:
        for page in pp:
            for m in rx.finditer(norm(page['text'])):
                if iso(m[6])!=p.stem[-10:]:continue
                found.append(dict(isin=m[1].upper(),action='JRS CAP PROPRIO' if m[3].startswith('juros') else m[3].upper(),
                    approval_date=iso(m[4]),gross_per_share=str(D(m[5].replace('.','').replace(',','.'))),payment_date=iso(m[6]),
                    sources=[dict(file=str(p),sha256=meta['sha256'],url=meta['url'],pages=[page['page']],source_excerpt=m[0])]))
    rows.extend(found)
    documents.append(dict(file=p.name,credit_heading=heading,rows=len(found),pages=len(pp),complete_cash_inventory=False))
cards=read(OUT/'cash-review-cards.json');snap=read(OUT/'cash-closure-02.json')
pending={r['event_id'] for r in snap['cash_events'] if not r['payment_date']}
matches=[]
for i,c in enumerate(cards):
    if c['event_id'] not in pending:continue
    found=[r for r in rows if (r['isin'],r['action'],r['approval_date'])==(c['isin'],c['action'],c['approval_date'])]
    exact=[r for r in found if D(r['gross_per_share'])==D(c['gross_per_share'])]
    if found:
        matches.append(dict(card_index=i,event_id=c['event_id'],ticker=c['ticker'],amount=c['gross_per_share'],ex_date=c['ex_date'],matches=found,exact=len(exact)))
result=dict(credit_rows=rows,documents=documents,pending_matches=matches,new_return_evaluations=0)
with (OUT/'current-credit-reconciliation.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
print('DOCUMENTS',len(documents),'ROWS',len(rows),'CARDS',len(matches))
for r in matches:print(r['card_index'],r['ticker'],r['amount'],'EXACT',r['exact'],[(m['gross_per_share'],m['payment_date']) for m in r['matches']])
