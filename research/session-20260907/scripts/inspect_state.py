import collections
import hashlib
import json
import pathlib
import sqlite3
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
REPO = ROOT / 'work/stocks-predictor'
CANON = pathlib.Path('C:/Users/Superleo13/stocks-predictor-work')
OUT = ROOT / 'outputs'

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def main():
    out = {'observed_at': datetime.now(timezone.utc).isoformat(), 'kind': 'READ_ONLY_METADATA_NO_NEW_PERFORMANCE'}
    paths = [CANON / 'data/stocks.db']
    for base in (REPO, CANON):
        paths.extend(base / p for p in ('trials.json', 'trials_v2.json', 'trials.harness_attestation.json', 'config.yaml'))
    out['file_hashes'] = {str(p): digest(p) for p in paths}
    out['database_sidecars'] = {s: (CANON / ('data/stocks.db' + s)).exists() for s in ('-wal', '-shm', '-journal')}
    conn = sqlite3.connect((CANON / 'data/stocks.db').as_uri() + '?mode=ro', uri=True)
    conn.execute('PRAGMA query_only=ON')
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    out['table_counts'] = {t: conn.execute('SELECT COUNT(*) FROM "' + t.replace('"', '""') + '"').fetchone()[0] for t in tables}
    out['fundamentals_schema'] = [dict(zip(('cid','name','type','notnull','default','pk'), row)) for row in conn.execute('PRAGMA table_info(fundamentals)')]
    out['prices_metadata'] = conn.execute('SELECT MIN(date), MAX(date), COUNT(DISTINCT ticker), COUNT(DISTINCT date) FROM prices_raw').fetchone()
    out['fundamentals_by_source'] = conn.execute('SELECT source,COUNT(*),COUNT(DISTINCT ticker),COUNT(known_at),MIN(ref_date),MAX(ref_date),MIN(known_at),MAX(known_at) FROM fundamentals GROUP BY source ORDER BY source').fetchall()
    out['fundamentals_coverage'] = {}
    for col in ('lucro_liquido','patrimonio_liquido','shares_outstanding','roe','leverage','net_margin','receita_liquida','fluxo_caixa_operacional','accruals'):
        out['fundamentals_coverage'][col] = conn.execute(f'SELECT COUNT({col}),COUNT(DISTINCT CASE WHEN {col} IS NOT NULL THEN ticker END) FROM fundamentals').fetchone()
    out['adjustment_types'] = conn.execute('SELECT type, COUNT(*), MIN(ex_date), MAX(ex_date) FROM adjustments GROUP BY type').fetchall()
    out['quarantine_counts'] = conn.execute('SELECT COUNT(*),SUM(resolved_at IS NULL) FROM quarantine').fetchone()
    if 'dividends' in tables:
        out['dividend_schema'] = list(conn.execute('PRAGMA table_info(dividends)'))
        out['dividend_range'] = conn.execute('SELECT MIN(ex_date),MAX(ex_date),COUNT(DISTINCT ticker) FROM dividends').fetchone()
    conn.close()
    out['ledger'] = {}
    for name in ('trials.json','trials_v2.json'):
        rows = json.loads((REPO/name).read_text(encoding='utf-8'))
        out['ledger'][name] = {'count':len(rows), 'rows':rows}
    OUT.mkdir(exist_ok=True)
    (OUT / 'state-evidence.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in out.items() if k not in ('ledger','fundamentals_schema','dividend_schema','file_hashes')},ensure_ascii=False,indent=2))
    print('ledger lengths', {k:v['count'] for k,v in out['ledger'].items()})

if __name__ == '__main__':
    main()
