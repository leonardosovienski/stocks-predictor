"""Acquire official monthly agenda PDFs for remaining 6015 dates."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import urllib.request

from acquire_h19_tax_calendar import ROOT, BASE, PREFIX, MONTHS, fetch, norm

record=json.loads((ROOT/'work/h19-continuous-inputs/tax-calendar.json').read_text(encoding='utf-8'))
jobs=[];missing=[]
for year in sorted({r['year'] for r in record['errors'] if 'year' in r}):
    url=PREFIX+f'arquivos-e-imagens-agenda-tributaria/agenda-tributaria-{year}'
    if year==2024:url+='-1'  # Actual Receita archive, verified in official index.
    page,source=fetch(url)
    for error in [r for r in record['errors'] if r.get('year')==year]:
        month=error['month'];name=MONTHS[month-1]
        links=[(u.removesuffix('/view'),t) for u,t in page.links if norm(t).startswith(name+' de '+str(year)) and '.pdf' in u]
        if not links:missing.append(error)
        for u,t in sorted(set(links)):
            jobs.append({'year':year,'month':month,'url':u,'title':t,'source_index':source})
def download(row):
    dest=BASE/f"agenda-{row['year']}-{row['month']:02}-{hashlib.sha256(row['url'].encode()).hexdigest()[:8]}.pdf"
    if not dest.exists():
        with urllib.request.urlopen(urllib.request.Request(row['url'],headers={'User-Agent':'Mozilla/5.0'}),timeout=40) as r:data=r.read()
        if not data.startswith(b'%PDF'):raise ValueError('non-PDF agenda')
        dest.write_bytes(data)
    result={**row,'file':dest.name,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'retrieved_at_utc':datetime.now(timezone.utc).isoformat()}
    dest.with_suffix('.source.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result
with ThreadPoolExecutor(max_workers=3) as pool:acquired=list(pool.map(download,jobs))
(BASE/'pdf-gap-index.json').write_text(json.dumps({'acquired':acquired,'missing':missing},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'acquired':len(acquired),'missing':missing},indent=2))
