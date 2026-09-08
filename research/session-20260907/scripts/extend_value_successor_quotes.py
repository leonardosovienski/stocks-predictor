"""Extract raw successor quotes; never change or filter existing source DB."""
from pathlib import Path
import collections
import hashlib
import json
import sqlite3
import zipfile

BASE = Path(__file__).resolve().parent
DEST = BASE / 'value-successor-source'
DEST.mkdir(exist_ok=True)
TICKERS = {'SUZB3','TIMS3','IGTI11','HAPV3','RENT3','ALSO3','AZZA3','MOTV3','JBSS32','NATU3','AMOB3'}
rows = {}
identities = collections.defaultdict(dict)
sources = {}
for year in range(2016, 2027):
    archive = Path(r'C:\Users\Superleo13\stocks-predictor-work\data') / f'COTAHIST_A{year}.ZIP'
    with archive.open('rb') as stream:
        sources[archive.name] = hashlib.file_digest(stream,'sha256').hexdigest()
    with (DEST / f'successors-{year}.txt').open('xb') as out, zipfile.ZipFile(archive) as z:
        for member in z.namelist():
            for raw in z.open(member):
                if raw[:2] != b'01' or raw[24:27] != b'010':
                    continue
                ticker = raw[12:24].strip().decode('ascii')
                if ticker not in TICKERS:
                    continue
                out.write(raw)
                ds = raw[2:10].decode('ascii')
                day = f'{ds[:4]}-{ds[4:6]}-{ds[6:]}'
                row = (day,ticker,'010',int(raw[56:69])/100,int(raw[108:121])/100,int(raw[210:217]),int(raw[170:188])/100,archive.name)
                key = ticker,day
                if key in rows and rows[key] != row:
                    raise ValueError('conflicting quote')
                rows[key] = row
                identities[ticker][day] = (raw[230:242].decode('ascii'),raw[39:49].decode('latin1').strip(),raw[10:12].decode('ascii'))
    print(year,len(rows),flush=True)
db = DEST / 'successors.db'
if db.exists():
    raise FileExistsError(db)
with sqlite3.connect(db) as conn:
    conn.execute('CREATE TABLE prices_raw(date TEXT,ticker TEXT,market_type TEXT,open REAL,close REAL,quote_factor INTEGER,volume_fin REAL,source_file TEXT,PRIMARY KEY(ticker,date))')
    conn.executemany('INSERT INTO prices_raw VALUES(?,?,?,?,?,?,?,?)',rows.values())
outdir = DEST / 'identity'
outdir.mkdir(exist_ok=True)
blocks = []
for ticker, dates in sorted(identities.items()):
    block = None
    for day,(isin,kind,bdi) in sorted(dates.items()):
        if block is None or block['isin'] != isin or block['first_date'][:4] != day[:4]:
            if block:
                blocks.append(block)
            block = dict(ticker=ticker,isin=isin,kind=kind,first_date=day,last_date=day,sessions=0,bdi_codes=[])
        block['last_date'] = day
        block['sessions'] += 1
        if bdi not in block['bdi_codes']:
            block['bdi_codes'].append(bdi)
    if block:
        blocks.append(block)
for year in range(2016,2027):
    with (outdir / f'identity-{year}.jsonl').open('x',encoding='utf-8') as stream:
        for block in blocks:
            if block['first_date'][:4] == str(year):
                stream.write(json.dumps(block)+'\n')
(DEST / 'manifest.json').write_text(json.dumps({'archives':sources,'tickers':sorted(TICKERS),'rows':len(rows)},indent=2),encoding='utf-8')
