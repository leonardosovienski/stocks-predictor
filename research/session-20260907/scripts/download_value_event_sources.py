"""Save issuer/B3 original documents separately from parsing and scoring."""
from pathlib import Path
import concurrent.futures
import datetime
import hashlib
import json
import urllib.request

BASE = Path(__file__).resolve().parent
DEST = BASE / 'value-event-terms'
DEST.mkdir(exist_ok=True)

def download(item):
    name, url = item
    path = DEST / (name + '.pdf')
    if path.exists():
        return {'name': name, 'status': 'already_saved'}
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=45) as response:
            raw = response.read()
            final_url = response.url
        if not raw.startswith(b'%PDF'):
            raise ValueError('not PDF')
        with path.open('xb') as stream:
            stream.write(raw)
        record = {'name': name, 'url': url, 'final_url': final_url, 'sha256': hashlib.sha256(raw).hexdigest(),
                  'downloaded_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'size_bytes': len(raw)}
        (DEST / (name + '.source.json')).write_text(json.dumps(record, indent=2), encoding='utf-8')
        return record
    except Exception as exc:
        return {'name': name, 'error': str(exc)}

if __name__ == '__main__':
    items = json.loads((BASE / 'value-event-sources.json').read_text(encoding='utf-8'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(download, items):
            print(json.dumps(result), flush=True)
