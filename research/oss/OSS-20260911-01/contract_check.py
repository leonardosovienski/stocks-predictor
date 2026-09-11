import importlib.util,pathlib,json,hashlib,datetime,sys
W=pathlib.Path(__file__).parent;R=pathlib.Path('C:/STOCKS/stocks-predictor')
spec=importlib.util.spec_from_file_location('existing_execution',R/'stocks_predictor/execution.py');e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
result=json.loads((W/'benchmark-results.json').read_text());fixture=json.loads((W/'fixtures.json').read_text());checks=[]
for name in ['full','limited']:
 old=fixture['K09']['initial']
 for i,row in enumerate(result['K09'][name]['records']):
  # Existing cost uses L1 turnover; external limit uses half L1. Cash is excluded.
  expected=e.weighted_turnover_cost({k:v for k,v in old.items() if k!='CASH'},{k:v for k,v in row['pre_fee_weights'].items() if k!='CASH'},.002)
  checks.append({'path':name,'step':i,'difference':expected-row['cost_fraction_initial_nav'],'pass':abs(expected-row['cost_fraction_initial_nav'])<1e-12})
  old={k:(row['cash_fraction_initial_nav_after_fee'] if k=='CASH' else v)/row['nav_fraction_after_fee'] for k,v in row['pre_fee_weights'].items()}
out={'run_id':'OSS-20260911-01','reason':'Integration convention discovered during source review: L1 vs half L1, never charge cash as another security','checks':checks,'pass':all(r['pass'] for r in checks),'existing_execution_sha256':hashlib.sha256((R/'stocks_predictor/execution.py').read_bytes()).hexdigest(),'independent_external_engine':False,'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(W/'cost-contract-receipt.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps({'pass':out['pass'],'comparisons':len(checks),'max_error':max(abs(x['difference']) for x in checks)}))
assert out['pass']
