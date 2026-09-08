"""Document inspection only, using the bundled PDF runtime; not a project test."""
from collections import defaultdict
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import unicodedata
import pypdfium2 as pdfium

ROOT=Path(__file__).resolve().parent
BASE=ROOT/'baseline-13'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def norm(s):return ' '.join(unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower().split())

manifest=read(BASE/'PACKAGE_SHA256.json')
for name, expected in manifest.items():
    p=(BASE/name).resolve()
    assert p.is_relative_to(BASE.resolve()) and digest(p)==expected,name
print('Verified original package payloads:',len(manifest),flush=True)
catalog=read(BASE/'inputs/primary-catalog.json')
cash=read(BASE/'inputs/cash-events.json')
pending=[r for r in cash if r['net_per_share'] is None or not r['payment_date']]
amounts=defaultdict(list)
for r in pending:amounts[Decimal(r['gross_per_share'])].append(r['event_id'])
hits=defaultdict(list);errors=[];page_count=0;parsed=0
out=ROOT/'document-text';out.mkdir(exist_ok=True)
for name,meta in catalog.items():
    p=BASE/'inputs'/name
    if p.suffix!='.pdf' or p.name[65:].startswith('b3'):continue
    cache=out/(p.stem+'.json')
    known=BASE/'investigation-candidates'/(p.name[65:-4]+'.text.json')
    try:
        if cache.exists():pages=read(cache)
        elif known.exists():pages=read(known)
        else:
            pdf=pdfium.PdfDocument(p);pages=[]
            for i in range(len(pdf)):
                page=pdf[i];textpage=page.get_textpage()
                pages.append({'page':i+1,'text':textpage.get_text_range()})
                textpage.close();page.close()
            pdf.close()
            with cache.open('x',encoding='utf-8') as f:json.dump(pages,f,ensure_ascii=False)
        for page in pages:
            t=norm(page['text']);found=set()
            for match in re.finditer(r'(?<![\d,.])(?:\d+,\s*\d{5,})(?!\d)',t):
                amount=Decimal(re.sub(r'\s+','',match[0]).replace(',','.'))
                found.update(amounts.get(amount,[]))
            for event in found:hits[event].append({'source':name,'sha256':meta['sha256'],'url':meta['url'],
                                                   'page':page['page'],'text':t})
        page_count+=len(pages);parsed+=1
        if parsed%40==0:print('Documents inspected:',parsed,'pages:',page_count,flush=True)
    except Exception as exc:errors.append({'file':name,'error':str(exc)})
result={'purpose':'PRIMARY_DOCUMENT_INSPECTION_ONLY_NOT_PROJECT_TEST_OR_EXECUTION_CERTIFICATION',
    'verified_package_payloads':len(manifest),'documents':parsed,'pages':page_count,'errors':errors,
    'events':[{'event':r,'candidates':hits[r['event_id']]} for r in pending]}
with (ROOT/'local-candidates-14.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
for r in result['events']:
    print(r['event']['event_id'],[(c['source'][73:],c['page']) for c in r['candidates']
          if 'liquid' in c['text'] or 'retencao' in c['text'] or 'creditad' in c['text']],flush=True)
print('Done; errors:',len(errors),flush=True)
