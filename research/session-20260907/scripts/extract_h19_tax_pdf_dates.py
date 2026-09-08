"""Extract 6015 with its left-column due-date group and render whole pages."""
import hashlib
import json
from pathlib import Path
import re
import unicodedata
import pdfplumber
import pypdfium2 as pdfium

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'work/h19-tax-source'
OUT=BASE/'review-pages';OUT.mkdir(exist_ok=True)
def norm(s):return ' '.join(unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower().split())
rows=[];missing=[]
for item in json.loads((BASE/'pdf-gap-index.json').read_text(encoding='utf-8'))['acquired']:
    path=BASE/item['file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256']
    pdf=pdfium.PdfDocument(path);hits=[]
    for i in range(len(pdf)):
        pg=pdf[i];tp=pg.get_textpage();text=tp.get_text_range();tp.close();pg.close()
        if '6015' in text and 'ganhos liquidos em operacoes em bolsa' in norm(text):hits.append(i)
    if not hits:missing.append(item);pdf.close();continue
    with pdfplumber.open(path) as parsed:
        for i in hits:
            page=parsed.pages[i];words=page.extract_words()
            codes=[w for w in words if w['text']=='6015']
            for code in codes:
                left=[w for w in words if re.fullmatch(r'\d{1,2}',w['text']) and 1<=int(w['text'])<=31
                    and w['x1']<min(130,code['x0']/2) and 90<w['top']<=code['top']+3]
                if not left:missing.append({'file':path.name,'page':i+1,'reason':'date group not resolved'});continue
                day=max(left,key=lambda w:w['top'])
                dest=OUT/f'{path.stem}-p{i+1}.png'
                pg=pdf[i];pg.render(scale=1.4).to_pil().save(dest);pg.close()
                rows.append({**item,'page':i+1,'candidate_due_date':f"{item['year']}-{item['month']:02}-{int(day['text']):02}",
                    'date_word':day,'code_word':code,'page_text':page.extract_text(),
                    'rendered_page':str(dest),'source_review':False})
    pdf.close()
    print(json.dumps({'file':path.name,'6015_pages':len(hits)}),flush=True)
(BASE/'pdf-date-review.json').write_text(json.dumps({'candidates':rows,'missing':missing},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'candidates':len(rows),'missing':len(missing)}),flush=True)
