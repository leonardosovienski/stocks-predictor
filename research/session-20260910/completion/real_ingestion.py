"""Run the opt-in source catalog on an acquired real annual ZIP in a new staging DB."""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import time

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repo',type=Path,required=True)
parser.add_argument('--archive',type=Path,required=True)
parser.add_argument('--receipt',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
sys.path.insert(0,str(args.repo))
from stocks_predictor.source_catalog import ingest_version

receipt=json.loads(args.receipt.read_text(encoding='utf-8'))
with args.archive.open('rb') as f:
    if hashlib.file_digest(f,'sha256').hexdigest()!=receipt['sha256']:
        raise ValueError('original acquisition identity differs')
args.output.mkdir(parents=True,exist_ok=False)
db=args.output/'source-stage.sqlite'
# Only the raw price contract is created. This is explicitly not a full project DB.
schema='''CREATE TABLE prices_raw(date TEXT NOT NULL, ticker TEXT NOT NULL,
bdi_code TEXT NOT NULL, market_type TEXT NOT NULL, open REAL NOT NULL,
high REAL NOT NULL, low REAL NOT NULL, close REAL NOT NULL, volume_fin REAL NOT NULL,
qty INTEGER NOT NULL, quote_factor INTEGER NOT NULL, source_file TEXT NOT NULL,
UNIQUE(date,ticker,source_file))'''
started=time.perf_counter()
with closing(sqlite3.connect(db)) as conn:
    conn.execute(schema)
    params=dict(publisher='B3',dataset='COTAHIST_A2026',version='observed-20260910T152027Z',
                source_url=receipt['url'],observed_at=receipt['completed_at_utc'],scratch_dir=args.output)
    first=ingest_version(conn,args.archive,**params)
    print(json.dumps({'stage':'first_ingestion','result':first}),flush=True)
    second=ingest_version(conn,args.archive,**params)
    if second['inserted']!=0 or first['source_id']!=second['source_id']:
        raise ValueError('real replay is not idempotent')
    n,tickers,lo,hi=conn.execute('SELECT COUNT(*),COUNT(DISTINCT ticker),MIN(date),MAX(date) FROM prices_raw').fetchone()
    integrity=conn.execute('PRAGMA integrity_check').fetchall()
    if integrity!=[('ok',)] or first['inserted']!=n:
        raise ValueError('stage consistency failed')
    rows_hash=hashlib.sha256()
    for row in conn.execute('SELECT * FROM prices_raw ORDER BY date,ticker,source_file'):
        rows_hash.update(json.dumps(row,separators=(',',':')).encode('utf-8'))
    observation=conn.execute('SELECT observed_at FROM source_versions').fetchone()[0]
with db.open('rb') as f: db_sha=hashlib.file_digest(f,'sha256').hexdigest()
report={'status':'PASS','completed_at_utc':datetime.now(timezone.utc).isoformat(),
        'source_acquisition_receipt_sha256':hashlib.sha256(args.receipt.read_bytes()).hexdigest(),
        'source_sha256':receipt['sha256'],'source_url':receipt['url'],'source_id':first['source_id'],
        'source_observed_at':observation,'first_inserted':first['inserted'],'replay_inserted':second['inserted'],
        'stored_rows':n,'distinct_tickers':tickers,'date_min':lo,'date_max':hi,'rows_sha256':rows_hash.hexdigest(),
        'database_sha256':db_sha,'seconds_including_both_ingestions_and_validation':time.perf_counter()-started,
        'scope':'New raw-source staging DB, spot BDI02/market010 only. Not the full project schema, not all instruments, not a point-in-time identity/calendar/event audit; no historical banks changed.',
        'new_return_evaluations':0,'capital_enabled':False}
with (args.output/'receipt.json').open('x',encoding='utf-8') as f: json.dump(report,f,indent=2)
print(json.dumps(report,indent=2),flush=True)
