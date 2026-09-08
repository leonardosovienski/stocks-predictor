import json
import pathlib
import sqlite3
import sys
from inspect_state import ROOT,REPO,CANON

sys.path.insert(0,str(ROOT/'work/runtime'))
sys.path.insert(0,str(REPO/'stocks_predictor'))
import factor
import config
c=sqlite3.connect((CANON/'data/stocks.db').as_uri()+'?mode=ro',uri=True)
c.execute('PRAGMA query_only=ON')
cfg=config.load_config(REPO/'config.yaml')
out={'hashes':{f'H{i}':getattr(config,f'h{i}_frozen_config_hash')(cfg) for i in (17,18,19)}}
row=c.execute("SELECT shares_outstanding,ref_date,known_at FROM fundamentals WHERE ticker='BBAS3' AND source='CVM FRE 2023'").fetchone()
out['bbas_share_base']={'recorded_shares':row[0],'reference_label':row[1],'document_received':row[2],'shares_after_current_split_function':factor._shares_on_price_base(c,'BBAS3',row[0],row[1],'2024-05-31')}
out['dividends_years']=list(c.execute('SELECT substr(ex_date,1,4),COUNT(*) FROM dividends GROUP BY substr(ex_date,1,4)'))
out['duplicate_dividend_keys']=c.execute('SELECT COUNT(*) FROM (SELECT ticker,ex_date,COUNT(*) AS n FROM dividends GROUP BY ticker,ex_date HAVING n>1)').fetchone()[0]
c.close()
(ROOT/'outputs/audit-details.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out,ensure_ascii=False,indent=2))
