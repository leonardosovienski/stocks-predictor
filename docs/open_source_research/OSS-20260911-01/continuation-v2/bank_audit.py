import datetime,hashlib,json,pathlib,sqlite3
W=pathlib.Path(__file__).parent
catalog=json.loads(pathlib.Path('C:/STOCKS/data/CATALOG.json').read_text(encoding='utf-8-sig'))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
results=[]
for row in catalog['databases']:
 p=pathlib.Path(row['path']);r={'path':str(p),'expected_sha256':row['sha256'],'policy':'schema only, no market/outcome rows; mode=ro&immutable=1, query_only'}
 r['before']=sha(p);assert r['before']==row['sha256']
 sidecars=[str(p)+s for s in ['-wal','-journal','-shm'] if pathlib.Path(str(p)+s).exists() and pathlib.Path(str(p)+s).stat().st_size]
 if sidecars:r['blocked_sidecars']=sidecars
 else:
  con=sqlite3.connect(p.as_uri()+'?mode=ro&immutable=1',uri=True);con.execute('PRAGMA query_only=ON')
  r['schema']=[dict(name=x[0],type=x[1],sql=x[2]) for x in con.execute("SELECT name,type,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'")]
  con.close()
 r['after']=sha(p);assert r['after']==r['before'];results.append(r)
 print(p.name[:12],len(r.get('schema',[])),r['after']==r['before'])
(W/'bank-receipt.json').write_text(json.dumps({'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'databases':results,'result':'PASS','protected_rows_read':False},indent=2),encoding='utf-8')
