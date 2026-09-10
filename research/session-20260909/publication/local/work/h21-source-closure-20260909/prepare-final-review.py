import base64
import json
import subprocess
from pathlib import Path
from pypdf import PdfReader

root = Path(r'C:\STOCKS\work\h21-source-closure-20260909')
batch = []
queries = [('GetCategories', 19674, 2025, None)]
queries += [('GetReportsRelevants', 19674, 2026, c) for c in ('2','3','11')]
queries += [('GetReportsRelevants', 990, y, '1') for y in (2019,2020,2021)]
for endpoint, fund, year, category in queries:
    q = dict(language='pt-br', idFNET=str(fund), typeFund='ETF', dateInitial=f'{year}-01-01', dateFinal=f'{year}-12-31' if year < 2026 else '2026-09-08', pageNumber=1, pageSize=60)
    if category is not None: q['category'] = category
    token = base64.b64encode(json.dumps(q,separators=(',',':')).encode()).decode()
    identifier = f'b3-final-{fund}-{year}-{category or "categories"}'
    batch.append(dict(id=identifier, filename=identifier+'.json', url='https://sistemaswebb3-listados.b3.com.br/fundsListedProxy/Search/'+endpoint+'/'+token, purpose='Correct single-calendar-year documentary scope; no performance calculation'))
(root/'batch-20.json').write_text(json.dumps(batch,indent=2),encoding='utf-8')
poppler = r'C:\Users\leona\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe'
for filename, phrase in [('bova-fs-2026-retry.pdf','Demonstração da evolução'),('bova-fs-2026-retry.pdf','14 Política'),('bova-fs-2026-retry.pdf','21 Evento'),('bova-regulamento-2026.pdf','6.6'),('bova-regulamento-legacy.pdf','Artigo 34')]:
    reader = PdfReader(root/'raw'/filename)
    pages = [i+1 for i,p in enumerate(reader.pages) if phrase in (p.extract_text() or '')]
    print(filename, phrase, pages)
    for p in pages[:2]:
        subprocess.run([poppler,'-f',str(p),'-l',str(p),'-scale-to','1400','-singlefile','-png',str(root/'raw'/filename),str(root/'visual-qa'/(filename[:-4]+f'-p{p}'))],check=True,timeout=25)
subprocess.run([poppler,'-f','11','-l','11','-scale-to','1400','-singlefile','-png',str(root/'raw'/'b3-fees-v5.pdf'),str(root/'visual-qa'/'b3-v5-p11')],check=True,timeout=25)
