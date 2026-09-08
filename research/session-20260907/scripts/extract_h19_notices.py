"""Extract acquired primary notices and index exact-value passages for review."""
import json
from pathlib import Path
import re
import sys
from pypdf import PdfReader

BASE=Path(__file__).resolve().parent/'h19-cash-expanded-source'
suffix=sys.argv[1] if len(sys.argv)>1 else 'selected'
docs=json.loads((BASE/f'ipe-{suffix}-notices.json').read_text(encoding='utf-8'))
results=[]
for doc in docs:
    p=BASE/doc['local_file']
    if not p.exists():continue
    dest=p.with_suffix('.extracted.json')
    if dest.exists():pages=json.loads(dest.read_text(encoding='utf-8'))
    else:
        try:
            reader=PdfReader(p)
            pages=[{'page':i+1,'text':page.extract_text() or ''} for i,page in enumerate(reader.pages)]
            dest.write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding='utf-8')
        except Exception as e:
            results.append({'file':p.name,'error':str(e)});continue
    text=' '.join(' '.join(p['text'].split()) for p in pages)
    matching=[]
    for r in doc['matching_cash_requirements']:
        # Exact decimal spelling after discarding only insignificant trailing zeroes.
        needle=r['value_per_share'].rstrip('0').rstrip('.')
        if needle.replace('.',',') in text or needle in text:matching.append(r)
    if matching:
        passages=[text[max(0,m.start()-70):m.end()+210] for m in re.finditer(r'pagamento|pagos|creditados|Payment|paid',text,re.I)]
        results.append({'file':p.name,'cnpj':doc['CNPJ_Companhia'],'reference':doc['Data_Referencia'],'title':doc['Assunto'],
                        'matches':matching,'payment_passages':passages,'text_chars':len(text),'pages':len(pages)})
result={'downloaded_pdf_count':sum((BASE/d['local_file']).exists() for d in docs),'matching_notices':results}
(BASE/f'notice-{suffix}-amount-passages.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'downloaded':result['downloaded_pdf_count'],'exact_amount_documents':len(results),'unique_requirements':len({(r['ticker'],r['ex_date'],r['value_per_share']) for d in results for r in d.get('matches',[])})},indent=2))
