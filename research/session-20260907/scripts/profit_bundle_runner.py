"""Offline reproduction of frozen prices/entitlements and all 12 risk scenarios."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output-dir',type=Path,required=True)
parser.add_argument('--verify-only',action='store_true')
args=parser.parse_args()
manifest=read(ROOT/'validation-manifest.json')
for name,sha in manifest['files'].items():
    path=(ROOT/name).resolve()
    if not path.is_relative_to(ROOT.resolve()) or digest(path)!=sha:raise ValueError('Changed package file: '+name)
if args.verify_only:
    print(json.dumps({'status':'PASS','verified_files':len(manifest['files'])}));sys.exit(0)
out=args.output_dir.resolve()
out.mkdir(parents=True,exist_ok=False)
base=ROOT/'baseline'
sys.path.insert(0,str(base/'code'))
from stocks_predictor.discovery_reorganizations import run,merged_market
from stocks_predictor.discovery_h17 import adjustment_map
from stocks_predictor.discovery_value import group_events
run(base/'observations/h18-h19-repaired-observation.json',base/'base/quotes.db',base/'base/identity',
    base/'successors/successors.db',base/'successors/identity',base/'base/events.json',
    base/'base/reviewed-jumps.json',base/'terms/reorganizations.json',
    base/'protocol.json',out/'baseline-reproduced.json')
baseline=read(out/'baseline-reproduced.json')
expected_base=read(base/'observations/h18-h19-reorganization-observation.json')
if baseline['trials']!=expected_base['trials']:raise ValueError('Original measurement reproduction differs')
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
validator=module('standalone_profit_validator',ROOT/'validator/profit_validation.py')
bootstrap=module('unchanged_core_bootstrap',ROOT/'validator/bootstrap.py')
bars,_=merged_market(base/'base/quotes.db',base/'base/identity',base/'successors/successors.db',base/'successors/identity')
events,legacy=group_events(read(base/'base/events.json'))
factors={t:adjustment_map(events[t],legacy[t])[0] for t in bars}
actual=validator.audit_trials(baseline,bars,factors,read(base/'terms/reorganizations.json'),bootstrap.bootstrap_ci)
expected=read(ROOT/'results/VALIDACAO_LUCRO_STOCKS.json')
for key in actual:
    if actual[key]!=expected[key]:raise ValueError('Profit validation differs: '+key)
with (out/'profit-validation-reproduced.json').open('x',encoding='utf-8') as f:json.dump(actual,f,ensure_ascii=False,indent=2,allow_nan=False)
verified={'status':'PASS','verified_files':len(manifest['files']),'independent_cells':actual['independently_verified_cells'],
          'all_12_scenarios_and_bootstrap_intervals_identical':True,'original_4_cohorts_reproduced':True,
          'ordinary_cash_net_profit_or_real_orders_verified':False,
          'does_not_add_independent_evidence':True}
with (out/'verification.json').open('x',encoding='utf-8') as f:json.dump(verified,f,indent=2)
print(json.dumps(verified,indent=2))
