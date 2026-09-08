"""Read-only official RI sources. Raw files and cell/page locators retained."""
import concurrent.futures
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / 'work/source-acquisition'
SOURCES = {
    'ri-bbas-payments.pdf': 'https://api.mziq.com/mzfilemanager/v2/d/5760dff3-15e1-4962-9e81-322a0b3d0bbd/14581997-4233-3b2e-1d82-0d9c766cb7ec?origin=2',
    'ri-engi-payments.xlsx': 'https://api.mziq.com/mzfilemanager/v2/d/60f49a2d-bd8c-4fd9-95ab-bdf833097a83/c1722b44-9139-333e-3545-30dc98ed51c0?origin=2',
    'ri-abev-payments.xlsx': 'https://api.mziq.com/mzfilemanager/v2/d/c8182463-4b7e-408c-9d0f-42797662435e/24107927-8c3d-7046-8ae8-b2c677b4ed63?origin=2',
}

def download(item):
    name, url = item
    path = RAW / name
    if not path.exists():
        with urllib.request.urlopen(url, timeout=45) as response:
            payload = response.read()
            content_type = response.headers.get('Content-Type')
        path.write_bytes(payload)
        (RAW / (name + '.source.json')).write_text(json.dumps({'url': url, 'sha256': hashlib.sha256(payload).hexdigest(),
                                                             'retrieved_at': datetime.now(timezone.utc).isoformat(), 'content_type': content_type}), encoding='utf-8')
    return path

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    paths = list(pool.map(download, SOURCES.items()))

for path in paths:
    if path.suffix == '.pdf':
        from pypdf import PdfReader
        reader = PdfReader(path)
        pages = [{'page': i + 1, 'text': page.extract_text(extraction_mode='layout')} for i, page in enumerate(reader.pages)]
        (RAW / (path.stem + '-extracted.json')).write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding='utf-8')
        print(path.name, 'pages', len(pages))
        print(pages[0]['text'][:2100])
    else:
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        sheets = []
        for sheet in wb:
            rows = [{'row': i, 'values': list(row)} for i, row in enumerate(sheet.iter_rows(values_only=True), 1) if any(x is not None for x in row)]
            sheets.append({'sheet': sheet.title, 'rows': rows})
            print(path.name, sheet.title, 'rows', len(rows))
            for row in rows[:16]:
                print(row)
        (RAW / (path.stem + '-extracted.json')).write_text(json.dumps(sheets, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
        wb.close()
