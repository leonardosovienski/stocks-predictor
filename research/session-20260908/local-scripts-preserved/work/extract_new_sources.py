"""Text extraction from hash-verified new primary PDFs, outside the old archive."""
import hashlib
import json
from pathlib import Path
import pypdfium2 as pdfium

ROOT=Path(r'C:\Users\Superleo13\stocks-predictor-work\.local-research\stocks-session-20260907')
BASE=ROOT/'work/source-closure-20260908/new-primary'
count=0
for p in sorted(BASE.glob('*.pdf')):
    dest=p.with_suffix('.text.json')
    if dest.exists():continue
    m=json.loads(p.with_suffix('.source.json').read_text(encoding='utf-8'))
    assert hashlib.sha256(p.read_bytes()).hexdigest()==m['sha256']
    try:
        pdf=pdfium.PdfDocument(p); pages=[]
        for i in range(len(pdf)):
            page=pdf[i];t=page.get_textpage()
            pages.append({'page':i+1,'text':t.get_text_range()})
            t.close();page.close()
        pdf.close()
        with dest.open('x',encoding='utf-8') as f:json.dump(pages,f,ensure_ascii=False)
        count+=1
    except Exception as exc:print(p.name,str(exc),flush=True)
print('EXTRACTED',count,flush=True)
