import importlib.util
import json
import sqlite3
import sys
from inspect_state import ROOT, REPO, CANON

sys.path.insert(0,str(ROOT/'work/runtime'))
sys.path.insert(0,str(REPO/'stocks_predictor'))
spec=importlib.util.spec_from_file_location('coverage_only',REPO/'tools/cobertura_h18.py')
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
from config import load_config, h17_frozen_config_hash, h18_frozen_config_hash, h19_frozen_config_hash
cfg=load_config(REPO/'config.yaml')
conn=sqlite3.connect((CANON/'data/stocks.db').as_uri()+'?mode=ro',uri=True)
conn.execute('PRAGMA query_only=ON')
print('CONFIG_HASHES',json.dumps({f'H{i}':fn(cfg) for i,fn in ((17,h17_frozen_config_hash),(18,h18_frozen_config_hash),(19,h19_frozen_config_hash))}))
mod.cobertura_bruta(conn)
mod.cobertura_por_rebalance(conn,cfg,'2018-01-01')
conn.close()
