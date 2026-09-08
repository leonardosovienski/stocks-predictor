"""Read raw B3 archives without excluding held instruments that change BDI."""
from pathlib import Path
import collections
import hashlib
import json
import sqlite3
import zipfile

ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/'work/h17-run-pack-v2/data'
DEST=ROOT/'work/value-measurement-source'
DEST.mkdir(exist_ok=True)
snapshots=json.loads((BASE/'snapshots.json').read_text(encoding='utf-8'))
needed={r['ticker'] for s in snapshots for r in s['universe']}
needed_isins={r['isin'] for s in snapshots for r in s['universe']}
rows={};identities=collections.defaultdict(dict);sources={};raw_files=[]
for year in range(2016,2027):
    archive=Path(r'C:\Users\Superleo13\stocks-predictor-work\data')/f'COTAHIST_A{year}.ZIP'
    with archive.open('rb') as stream: sha=hashlib.file_digest(stream,'sha256').hexdigest()
    sources[archive.name]=sha
    raw_path=DEST/f'cash-equity-{year}.txt'
    with raw_path.open('xb') as output,zipfile.ZipFile(archive) as z:
        for name in z.namelist():
            for raw in z.open(name):
                if raw[:2]!=b'01' or raw[24:27]!=b'010':continue
                ticker=raw[12:24].strip().decode('ascii');isin=raw[230:242].strip().decode('ascii')
                if ticker not in needed and isin not in needed_isins:continue
                output.write(raw)
                ds=raw[2:10].decode('ascii');day=f'{ds[:4]}-{ds[4:6]}-{ds[6:]}'
                scale=int(raw[210:217]);opening=int(raw[56:69])/100;close=int(raw[108:121])/100
                if min(scale,opening,close)<=0:raise ValueError('invalid source quote')
                row=(day,ticker,'010',opening,close,scale,int(raw[170:188])/100,archive.name)
                key=ticker,day
                if key in rows and rows[key]!=row:raise ValueError('conflicting raw quotes')
                rows[key]=row
                identities[ticker][day]=(isin,raw[39:49].decode('latin1').strip(),raw[10:12].decode('ascii'))
    raw_files.append(raw_path.name)
    print(year,'cash equity records',len(rows),flush=True)
db=DEST/'quotes.db'
if db.exists():raise FileExistsError(db)
with sqlite3.connect(db) as conn:
    conn.execute('CREATE TABLE prices_raw(date TEXT,ticker TEXT,market_type TEXT,open REAL,close REAL,quote_factor INTEGER,volume_fin REAL,source_file TEXT,PRIMARY KEY(ticker,date))')
    conn.executemany('INSERT INTO prices_raw VALUES(?,?,?,?,?,?,?,?)',rows.values())
outdir=DEST/'identity';outdir.mkdir(exist_ok=True)
blocks=[]
for ticker,byday in sorted(identities.items()):
    block=None
    for day,(isin,kind,bdi) in sorted(byday.items()):
        if block is None or block['isin']!=isin or block['first_date'][:4]!=day[:4]:
            if block:blocks.append(block)
            block={'ticker':ticker,'isin':isin,'kind':kind,'first_date':day,'last_date':day,'sessions':0,'bdi_codes':[]}
        block['last_date']=day;block['sessions']+=1
        if bdi not in block['bdi_codes']:block['bdi_codes'].append(bdi)
    if block:blocks.append(block)
for year in range(2016,2027):
    with (outdir/f'identity-{year}.jsonl').open('x',encoding='utf-8') as stream:
        for block in blocks:
            if block['first_date'][:4]==str(year):stream.write(json.dumps(block)+'\n')
panel=json.loads((BASE/'events.json').read_text(encoding='utf-8'))
superseded=[];keep=[]
for legacy in panel['legacy_adjustments']:
    if (legacy['ticker'],legacy['ex_date']) in {('NATU3','2019-09-18'),('PSSA3','2021-10-21')}:
        primary=[r for r in panel['events'] if r['ticker']==legacy['ticker'] and r['ex_date']==legacy['ex_date'] and r['label']=='BONIFICACAO']
        assert len(primary)==1 and legacy['factor']==primary[0]['price_factor']==0.5
        superseded.append({'legacy':legacy,'primary':primary[0],'resolution':'Same 100% bonus mislabeled split in legacy; primary is counted once.'})
    else:keep.append(legacy)
panel['legacy_adjustments']=keep
panel['explicit_superseded_legacy_audit']=superseded
(DEST/'events.json').write_text(json.dumps(panel,ensure_ascii=False,indent=2),encoding='utf-8')
with sqlite3.connect((BASE/'quotes.db').as_uri()+'?mode=ro',uri=True) as conn:
    old=list(conn.execute('select date,ticker,market_type,open,close,quote_factor,volume_fin,source_file from prices_raw'))
    differences=[{'ticker':r[1],'date':r[0],'old':r,'new':rows.get((r[1],r[0]))} for r in old if rows.get((r[1],r[0]))!=r]
    # Source filename serialization can differ; actual original values must agree.
    actual_changes=[d for d in differences if tuple(d['old'][:7])!=tuple(d['new'][:7])]
    if actual_changes:raise ValueError(('Existing quote value changed',actual_changes[:1]))
report={'archive_sha256':sources,'raw_excerpts':raw_files,'old_quote_count':len(old),'new_quote_count':len(rows),
        'existing_quote_value_changes':len(actual_changes),'added_tickers':sorted(set(identities)-needed),
        'bdi_counts':dict(collections.Counter(bdi for ds in identities.values() for _,_,bdi in ds.values())),
        'superseded_legacy':superseded,'selection_policy':'Original frozen candidate features and selections will be retained; only outcomes remeasured.'}
(DEST/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ('archive_sha256','superseded_legacy')},indent=2))
