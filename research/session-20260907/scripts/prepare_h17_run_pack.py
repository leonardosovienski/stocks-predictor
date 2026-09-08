from pathlib import Path
import hashlib,json,shutil,sqlite3
root=Path.cwd();repo=root/'work/stocks-predictor';pack=root/'work/h17-run-pack'
pack.mkdir(exist_ok=True);(pack/'data').mkdir(exist_ok=True)
source=root/'work/stocks-tested-real-v2-20260907.db'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
snap=root/'work/h17-preparation/snapshots-before-event-gates.json'
needed={r['ticker'] for s in json.loads(snap.read_text(encoding='utf-8')) for r in s['universe']}
db=pack/'data/quotes.db'
if db.exists():raise FileExistsError('prepare a new input snapshot instead of replacing a frozen database')
parent=sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)
out=sqlite3.connect(db)
out.execute('create table prices_raw(date text,ticker text,market_type text,open real,close real,quote_factor real,volume_fin real,source_file text,primary key(ticker,date))')
rows=[r for r in parent.execute("select date,ticker,market_type,open,close,quote_factor,volume_fin,source_file from prices_raw where market_type='010' order by ticker,date") if r[1] in needed]
out.executemany('insert into prices_raw values(?,?,?,?,?,?,?,?)',rows);out.commit()
calendar=[r[0] for r in parent.execute('select distinct date from prices_raw order by date')]
assert calendar==[r[0] for r in out.execute('select distinct date from prices_raw order by date')]
out.close();parent.close()
shutil.copyfile(snap,pack/'data/snapshots.json')
shutil.copyfile(root/'work/h17-preparation/event-panel-with-crosscheck.json',pack/'data/events.json')
shutil.copytree(root/'work/h17-source-identity-v3',pack/'data/identity')
shutil.copyfile(repo/'docs/research/2026-09-07-h17-discovery-protocol.json',pack/'protocol.json')
manifest={'parent_database':str(source),'parent_database_sha256':sha(source),'subset_database_sha256':sha(db),'price_rows':len(rows),'tickers':len(needed),'sessions':len(calendar),'derivation':'Exact market_type=010 source rows for all historical snapshot tickers; no prices changed; parent calendar equality asserted. Financial/security documents and corporate-action provenance are in snapshots/events inputs. Full archives remain in the prior source delivery.'}
(pack/'data/source-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps(manifest,indent=2))
