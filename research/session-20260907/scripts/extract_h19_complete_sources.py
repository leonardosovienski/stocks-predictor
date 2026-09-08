"""Fast primary-document text extraction, separate from runtime and pricing."""
import hashlib
import json
from pathlib import Path
import sys
import pypdfium2 as pdfium

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'work/h19-cash-expanded-source'
label=sys.argv[1] if len(sys.argv)>1 else 'complete'
docs=json.loads((BASE/f'ipe-{label}-notices.json').read_text(encoding='utf-8'))
stats={'cached':0,'extracted':0,'unavailable':0,'errors':[]}
for d in docs:
    path=BASE/d['local_file']; target=path.with_suffix('.complete-text.json')
    old=path.with_suffix('.extracted.json')
    if old.exists() or target.exists():stats['cached']+=1;continue
    meta=path.with_suffix('.pdf.source.json')
    if not meta.exists():stats['unavailable']+=1;continue
    try:
        assert hashlib.sha256(path.read_bytes()).hexdigest()==json.loads(meta.read_text(encoding='utf-8'))['sha256']
        pdf=pdfium.PdfDocument(path)
        pages=[]
        for i in range(len(pdf)):
            page=pdf[i]; text=page.get_textpage()
            pages.append({'page':i+1,'text':text.get_text_range()})
            text.close();page.close()
        pdf.close()
        target.write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding='utf-8')
        stats['extracted']+=1
    except Exception as exc:stats['errors'].append({'file':path.name,'error':str(exc)})
    if (stats['extracted']+len(stats['errors']))%100==0:print(json.dumps({k:v for k,v in stats.items() if k!='errors'}),flush=True)
(BASE/f'{label}-extraction-status.json').write_text(json.dumps(stats,indent=2),encoding='utf-8')
print(json.dumps(stats,indent=2),flush=True)
