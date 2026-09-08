"""Acquire candidate receipts; save original HTML/PDF without certifying fields."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from collections import Counter
import hashlib
import json
import re
import urllib.request
from acquire_issuer_tables import Tables
from source_utils import OUT, read

def get(row):
    url = row['Link_Download']
    number = re.search(r'numProtocolo=(\d+)', url)[1]
    prefix = OUT / 'new-primary' / f'issuer-13-cvm-{number}'
    if any(prefix.with_suffix(ext).exists() for ext in ['.pdf', '.html']):
        return {'number': number, 'status': 'EXISTS'}
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(request, timeout=25) as response:
            data = response.read()
            headers = dict(response.headers)
            status = response.status
        pdf = data.startswith(b'%PDF-')
        path = prefix.with_suffix('.pdf' if pdf else '.html')
        metadata = {
            **row, 'url': url, 'sha256': hashlib.sha256(data).hexdigest(),
            'retrieved_at_utc': datetime.now(timezone.utc).isoformat(),
            'http_status': status, 'http_headers': headers,
            'pdf_eof_present': b'%%EOF' in data[-2048:] if pdf else None,
            'candidate_only': True,
        }
        with path.open('xb') as handle:
            handle.write(data)
        with prefix.with_suffix('.source.json').open('x', encoding='utf-8') as handle:
            json.dump(metadata, handle, ensure_ascii=False, indent=2)
        if not pdf:
            parser = Tables()
            parser.feed(data.decode('utf-8', errors='replace'))
            with prefix.with_suffix('.tables.json').open('x', encoding='utf-8') as handle:
                json.dump(parser.rows, handle, ensure_ascii=False, indent=2)
        return {'file': path.name, 'ticker': row['ticker'], 'reference': row['Data_Referencia'],
                'category': row['Categoria'], 'bytes': len(data), 'status': 'DOWNLOADED',
                'pdf_eof_present': metadata['pdf_eof_present']}
    except Exception as exc:
        return {'url': url, 'status': 'UNAVAILABLE', 'error': str(exc)}

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--index', default='overlooked-filings-index-13.json')
    parser.add_argument('--output', default='overlooked-filings-acquisition-13.json')
    args = parser.parse_args()
    rows = read(OUT / args.index)
    result = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for row in pool.map(get, rows):
            result.append(row)
            if len(result) % 30 == 0:
                print('RECEIPTS', len(result), '/', len(rows), flush=True)
    with (OUT / args.output).open('x', encoding='utf-8') as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    print(dict(Counter(row['status'] for row in result)), flush=True)
