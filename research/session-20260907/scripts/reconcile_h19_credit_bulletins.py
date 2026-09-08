"""Join primary B3 credit rows on ISIN, action, approval and exact amount."""
from collections import Counter
from datetime import date
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import unicodedata
import pypdfium2 as pdfium

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'work/h19-cash-expanded-source'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def norm(t):return ' '.join(unicodedata.normalize('NFKD',t).encode('ascii','ignore').decode().upper().split())
def iso(s):return date(int(s[6:]),int(s[3:5]),int(s[:2])).isoformat()
rx=re.compile(r'\b(BR[A-Z0-9]{10})\s+(?:\d+\s+)?(DIVIDENDO|RENDIMENTO|JUROS\s+SOBRE\s+CAPITAL\s+PROPRIO)\s+(\d{2}/\d{2}/\d{4})\s+([\d.,]+)\s+(\d{2}/\d{2}/\d{4})')
credits=[];sources=[];rejected=[]
for pdfpath in sorted([*BASE.glob('b3-credit-*.pdf'), *BASE.glob('b3-legacy-*.pdf')]):
    meta=read(pdfpath.with_suffix('.pdf.source.json'))
    assert hashlib.sha256(pdfpath.read_bytes()).hexdigest()==meta['sha256']
    path=pdfpath.with_suffix('.credit-pages.json')
    if path.exists():pages=read(path)
    else:
        pdf=pdfium.PdfDocument(pdfpath);pages=[]
        for i in range(min(len(pdf),12)):
            page=pdf[i];tp=page.get_textpage()
            pages.append({'page':i+1,'text':tp.get_text_range()})
            tp.close();page.close()
        pdf.close();path.write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding='utf-8')
    full=norm(' '.join(p['text'] for p in pages))
    pdf=pdfium.PdfDocument(pdfpath)
    had=len(pages)
    # Credit tables can continue beyond page 12 even when the heading was
    # already seen. A heading is not evidence that all table rows were read.
    for i in range(had,len(pdf)):
        page=pdf[i];tp=page.get_textpage()
        pages.append({'page':i+1,'text':tp.get_text_range()})
        tp.close();page.close()
    pdf.close()
    if len(pages)!=had:
        path.write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding='utf-8')
        full=norm(' '.join(p['text'] for p in pages))
    if 'CREDITO DE PROVENTOS' not in full:continue
    expected=pdfpath.stem[-8:];expected=f'{expected[:4]}-{expected[4:6]}-{expected[6:]}'
    for p in pages:
        text=norm(p['text'])
        for m in rx.finditer(text):
            try:
                pay=iso(m[5]);approval=iso(m[3])
            except ValueError:
                rejected.append({'file':pdfpath.name,'page':p['page'],'excerpt':m.group(),'reason':'invalid civil date'})
                continue
            if pay!=expected:continue
            amount=m[4]
            if ',' in amount:
                if not re.fullmatch(r'(?:\d+|\d{1,3}(?:\.\d{3})+),\d+',amount):
                    raise ValueError(('ambiguous credit amount',pdfpath.name,amount))
                amount=amount.replace('.','').replace(',','.')
            elif not re.fullmatch(r'\d+(?:\.\d{4,})?',amount):
                rejected.append({'file':pdfpath.name,'page':p['page'],'excerpt':m.group(),'reason':'ambiguous decimal separator'})
                continue
            credits.append({'isin':m[1],'action':'JRS CAP PROPRIO' if m[2].startswith('JUROS') else m[2],
                'approval_date':approval,'value_per_share':str(Decimal(amount)),
                'payment_date':pay,'source_file':pdfpath.name,'source_sha256':meta['sha256'],
                'url':meta['url'],'page':p['page'],'source_excerpt':m.group()})
    sources.append({'file':pdfpath.name,**meta})
registry=read(ROOT/'outputs/H19_CAIXA_PAGAMENTOS_REVISADOS_V3.json')
updates=[];ambiguous=[]
for row in registry['cash_queue']:
    if row['payment_date_reviewed']:continue
    raw=read(Path(row['source_path']))[row['source_row']]
    approval=iso(raw['dateApproval'])
    matches=[r for r in credits if r['isin']==row['isin'] and r['action']==row['action']
        and r['approval_date']==approval and Decimal(r['value_per_share'])==Decimal(row['value_per_share'])
        and r['payment_date']>=row['ex_date']]
    if len(matches)!=1:
        if matches:ambiguous.append({'row':row,'matches':matches})
        continue
    match=matches[0]
    # Repeated equal B3 source rows may be separate installments. A single
    # matching credit must not be assigned to more than one obligation.
    economic=[r for r in registry['cash_queue'] if r['isin']==row['isin'] and r['ex_date']==row['ex_date']
              and r['action']==row['action'] and Decimal(r['value_per_share'])==Decimal(row['value_per_share'])]
    if len(economic)!=1:
        ambiguous.append({'row':row,'matches':matches,'reason':'repeated equal amount; installment review required'});continue
    updates.append({'row':{k:row[k] for k in ('ticker','ex_date','isin','action','value_per_share','selected','source_row')},'evidence':match})
result={'credit_rows':credits,'sources':sources,'exact_unique_queue_matches':updates,'ambiguous':ambiguous,'rejected_rows':rejected,
    'all_pdf_pages_examined':True,
    'summary':{'credit_documents':len(sources),'parsed_credit_rows':len(credits),'new_exact_payment_matches':len(updates),
        'selected_new_matches':sum(r['row']['selected'] for r in updates),'matched_by_year':dict(Counter(r['row']['ex_date'][:4] for r in updates))},
    'net_amount_not_inferred':True,'full_cash_coverage_verified':False,'new_return_evaluations':0}
(BASE/'complete-credit-reconciliation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result['summary'],indent=2))
