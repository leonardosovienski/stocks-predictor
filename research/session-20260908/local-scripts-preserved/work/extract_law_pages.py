import hashlib
import json
import pypdfium2 as pdfium
from source_utils import OUT, norm, read

for p in (OUT/'law').glob('*.pdf'):
    assert hashlib.sha256(p.read_bytes()).hexdigest()==read(p.with_suffix('.source.json'))['sha256']
    dest=p.with_suffix('.text.json')
    if dest.exists():pp=read(dest)
    else:
        pdf=pdfium.PdfDocument(p);pp=[]
        for i in range(len(pdf)):
            page=pdf[i];tp=page.get_textpage();pp.append(dict(page=i+1,text=tp.get_text_range()));tp.close();page.close()
        pdf.close();dest.write_text(json.dumps(pp,ensure_ascii=False),encoding='utf-8')
    for row in pp:
        t=norm(row['text'])
        if 'desdobramento' in t or ('dividendos' in t and 'renda fixa' in t):
            print(p.name,row['page'],row['text'])
