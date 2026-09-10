"""Replay recovered frozen code with the previously declared R3 numeric tolerance.

This does not change or certify the original byte-exact numeric comparator.
"""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

work = Path('C:/STOCKS/work/gap-resolution-r6-20260910')
root = work/'h20-complete-package'
output = work/'h20-complete-numeric-reconciliation.json'
if output.exists():
    raise FileExistsError(output)
read = lambda path: json.loads(path.read_text(encoding='utf-8'))
manifest = read(root/'validation-manifest.json')
for name, expected in manifest['files'].items():
    with (root/name).open('rb') as stream:
        if hashlib.file_digest(stream,'sha256').hexdigest() != expected:
            raise ValueError('Changed restored input')
sys.path.insert(0,str(root/'baseline/code'))
from stocks_predictor.discovery_reorganizations import merged_market
from stocks_predictor.discovery_h17 import adjustment_map
from stocks_predictor.discovery_value import group_events


def module(name,path):
    spec = importlib.util.spec_from_file_location(name,path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def compare(actual,expected,path='',differences=None):
    if differences is None:
        differences = []
    if isinstance(actual,dict) and isinstance(expected,dict):
        if actual.keys() != expected.keys():
            raise ValueError('Different keys: '+path)
        for key in actual:
            compare(actual[key],expected[key],path+'/'+key,differences)
    elif isinstance(actual,list) and isinstance(expected,list):
        if len(actual) != len(expected):
            raise ValueError('Different length: '+path)
        for i,(left,right) in enumerate(zip(actual,expected)):
            compare(left,right,path+'/'+str(i),differences)
    elif actual != expected:
        if not isinstance(actual,float) or not isinstance(expected,float) or not math.isclose(actual,expected,rel_tol=2e-12,abs_tol=2e-12):
            raise ValueError('Material or non-numeric difference: '+path)
        differences.append({'path':path,'actual':actual,'expected':expected,'absolute_error':abs(actual-expected)})
    return differences


base = root/'baseline'
baseline = read(work/'h20-original-replay/baseline-reproduced.json')
base_diffs = compare(baseline['trials'],read(base/'observations/h18-h19-reorganization-observation.json')['trials'])
bars,_ = merged_market(base/'base/quotes.db',base/'base/identity',base/'successors/successors.db',base/'successors/identity')
events,legacy = group_events(read(base/'base/events.json'))
factors = {ticker:adjustment_map(events[ticker],legacy[ticker])[0] for ticker in bars}
validator = module('recovered_validator',root/'validator/profit_validation.py')
bootstrap = module('recovered_bootstrap',root/'validator/bootstrap.py')
actual = validator.audit_trials(baseline,bars,factors,read(base/'terms/reorganizations.json'),bootstrap.bootstrap_ci)
expected = read(root/'results/VALIDACAO_LUCRO_STOCKS.json')
diffs = compare(actual,{key:expected[key] for key in actual})
report = {'status':'PASS_WITH_PREVIOUSLY_DECLARED_FLOAT_TOLERANCE','verified_package_files':len(manifest['files']),
          'original_strict_numeric_replay_status':'FAIL','original_strict_numeric_failure':'Profit validation differs: trials',
          'tolerance_reference':'research/session-20260910/integral/reconcile_h20.py',
          'absolute_and_relative_tolerance':2e-12,'baseline_differences':base_diffs,'floating_differences':diffs,
          'python':sys.version,'independent_cells':actual['independently_verified_cells'],
          'new_independent_economic_evidence':False,'profit_certified':False}
with output.open('x',encoding='utf-8') as stream:
    json.dump({'report':report,'reproduced':actual},stream,indent=2)
print(json.dumps(report,indent=2))
