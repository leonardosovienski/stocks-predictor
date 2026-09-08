"""Independent dated issuer notice + B3 amount/payment reconciliation candidates.

No approval is inferred from a lone nearby date. Require the same record/ex
date and amount in the issuer page and the same ISIN/type/amount on the actual
B3 credit date. The issuing-page date evidence is retained for manual review.
"""
from datetime import date
from decimal import Decimal as D
import hashlib, json, re, unicodedata
from pathlib import Path

root=Path(__file__).resolve().parents[1];base=root/'work/h19-cash-expanded-source'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
norm=lambda s:' '.join(unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower().split())
months={v:i+1 for i,v in enumerate('janeiro fevereiro marco abril maio junho julho agosto setembro outubro novembro dezembro'.split())}
pattern=re.compile(r'\b(\d{1,2})\s*(?:de\s+('+'|'.join(months)+r')\s*(?:de\s*)?|([/.-])(\d{1,2})\3)(\d{4})\b')
def dates(text):
    result=[]
    for m in pattern.finditer(text):
        try:day=date(int(m[5]),months[m[2]] if m[2] else int(m[4]),int(m[1])).isoformat()
        except ValueError:continue
        result.append((day,m.start(),m.end()))
    return result
registry=read(root/'outputs/H19_CAIXA_PAGAMENTOS_REVISADOS_V4.json')
credits=read(base/'complete-credit-reconciliation.json')
closed={(m['row']['isin'],m['row']['ex_date'],m['row']['action'],m['row']['source_row']) for m in credits['exact_unique_queue_matches']}
index={}
for d in read(base/'ipe-complete-notices.json'):
    p=base/d['local_file'];textpath=p.with_suffix('.extracted.json')
    if not textpath.exists():textpath=p.with_suffix('.complete-text.json')
    if not textpath.exists():continue
    pages=[(r['page'],norm(r['text'])) for r in read(textpath)]
    for r in d['matching_cash_requirements']:
        key=(r['ticker'],r['ex_date'])
        if d['local_file'] not in index.setdefault(key,{}):index[key][d['local_file']]=(d,pages)
result=[]
for r in registry['cash_queue']:
    if r['payment_date_reviewed'] or (r['isin'],r['ex_date'],r['action'],r['source_row']) in closed:continue
    gross=D(r['value_per_share']);matches=[]
    bc=[c for c in credits['credit_rows'] if c['isin']==r['isin'] and c['action']==r['action']
        and D(c['value_per_share'])==gross and c['payment_date']>=r['ex_date']]
    if not bc:continue
    for d,pages in index.get((r['ticker'],r['ex_date']),{}).values():
        for page,text in pages:
            ds=dates(text)
            if not any(day in (r['last_cum'],r['ex_date']) for day,a,b in ds):continue
            amounts=[m for m in re.finditer(r'(?<![\d.,])\d+[.,]\d+(?!\d|[.,]\d)',text)
                     if D(m.group().replace(',','.'))==gross]
            if not amounts:continue
            for credit in bc:
                pays=[(a,b) for day,a,b in ds if day==credit['payment_date']
                      and re.search(r'pagamento|pagos|pago|creditados|credito',text[max(0,a-220):b+80])]
                if not pays:continue
                src=read((base/d['local_file']).with_suffix('.pdf.source.json'))
                assert hashlib.sha256((base/d['local_file']).read_bytes()).hexdigest()==src['sha256']
                matches.append({'payment_date':credit['payment_date'],'credit':credit,
                    'notice':{'file':d['local_file'],'url':d['Link_Download'],'sha256':src['sha256'],'page':page},
                    'amount_passages':[text[max(0,m.start()-100):m.end()+240] for m in amounts],
                    'payment_passages':[text[max(0,a-220):b+80] for a,b in pays],
                    'record_passages':[text[max(0,a-140):b+90] for day,a,b in ds if day in (r['last_cum'],r['ex_date'])]})
    if matches:result.append({'row':r,'matches':matches,'distinct_payment_dates':sorted({m['payment_date'] for m in matches}),
        'source_review':False})
(base/'notice-credit-review-candidates.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'rows':len(result),'unique_date':sum(len(r['distinct_payment_dates'])==1 for r in result),
    'list':[(r['row']['ticker'],r['row']['ex_date'],r['row']['value_per_share'],r['distinct_payment_dates']) for r in result]},indent=2))
