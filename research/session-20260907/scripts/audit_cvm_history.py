import concurrent.futures
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(ROOT/'work/stocks-predictor/stocks_predictor'),str(ROOT/'work/runtime')]
import cvm_pit
RAW=ROOT/'work/source-acquisition'
DERIVED=ROOT/'work/history-derived'
DERIVED.mkdir(exist_ok=True)

def audit(year):
    result={'year':year,'performance_observed':False}
    for kind in ('dfp','fre'):
        try:
            payload=(RAW/f'{kind}_cia_aberta_{year}.zip').read_bytes()
            issues=[]
            rows=cvm_pit.derive_dfp(payload,year,issues=issues) if kind=='dfp' else cvm_pit.derive_fre_shares(payload,year,issues=issues)
            (DERIVED/f'{kind}_{year}.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in rows),encoding='utf-8')
            result[kind]={'status':'DERIVED','documents':len(rows),'company_names':len({r['company'] for r in rows}),
                          'first_available':min((r['available_at'] for r in rows),default=None),
                          'last_available':max((r['available_at'] for r in rows),default=None),'issues':issues}
        except Exception as e:
            result[kind]={'status':'FAILED','error':repr(e)}
    return result

results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    for result in pool.map(audit,range(2016,2027)):
        results.append(result)
        print(json.dumps(result,ensure_ascii=False),flush=True)
        (ROOT/'outputs/historical-cvm-validation.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
