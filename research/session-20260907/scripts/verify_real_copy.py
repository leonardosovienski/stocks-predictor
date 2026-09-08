import hashlib
import json
from pathlib import Path
import sqlite3

ROOT=Path(__file__).resolve().parent.parent
source=Path('C:/Users/Superleo13/stocks-predictor-work/data/stocks.db')
copied=ROOT/'work/stocks-tested-real-v2-20260907.db'

def connect(path):
    conn=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)
    conn.execute('PRAGMA query_only=ON')
    return conn

def table_digest(conn, name):
    h=hashlib.sha256()
    count=0
    quoted='"'+name.replace('"','""')+'"'
    for row in conn.execute(f'SELECT * FROM {quoted} ORDER BY rowid'):
        h.update(json.dumps(row,ensure_ascii=False,separators=(',',':')).encode('utf-8'))
        h.update(b'\n')
        count+=1
    return {'rows':count,'sha256':h.hexdigest()}

src,dst=connect(source),connect(copied)
tables=[r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        if 'migrat' not in r[0] and r[0]!='sqlite_sequence']
checks=[]
for name in tables:
    old,new=table_digest(src,name),table_digest(dst,name)
    checks.append({'table':name,'source':old,'copy':new,'unchanged':old==new})
report={'all_historical_tables_unchanged':all(r['unchanged'] for r in checks),'checks':checks,
        'new_counts':{name:dst.execute(f'SELECT COUNT(*) FROM {name}').fetchone()[0]
                      for name in ('fundamentals_pit','shares_pit','cash_events','cash_event_coverage','ingestion_issues','research_source_documents','stock_bonus_events')}}
src.close()
dst.close()
(ROOT/'outputs/real-integration-table-integrity.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'all_historical_tables_unchanged':report['all_historical_tables_unchanged'],'new_counts':report['new_counts']}))
assert report['all_historical_tables_unchanged']
