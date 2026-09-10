"""Replay recovered frozen code with the previously declared R3 numeric tolerance.

This does not change or certify the original byte-exact numeric comparator.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--package',type=Path,required=True)
parser.add_argument('--output-dir',type=Path,required=True)
args = parser.parse_args()
root = args.package.resolve()
out = args.output_dir.resolve()
if out.exists() or out.is_relative_to(root):
    raise ValueError('Output must be new and outside the preserved package')
output = out/'numeric-reconciliation.json'
read = lambda path: json.loads(path.read_text(encoding='utf-8'))
if hashlib.sha256((root/'validation-manifest.json').read_bytes()).hexdigest() != '51eed47cc7985a9d8f0be7ca14527871caeba2d9f8cacfb10d4abf423cb7f7fa':
    raise ValueError('Original manifest seal differs')
manifest = read(root/'validation-manifest.json')
for name, expected in manifest['files'].items():
    with (root/name).open('rb') as stream:
        if hashlib.file_digest(stream,'sha256').hexdigest() != expected:
            raise ValueError('Changed restored input')
sys.path.insert(0,str(root/'baseline/code'))
from stocks_predictor.discovery_reorganizations import merged_market, run
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
out.mkdir(parents=True,exist_ok=False)
run(base/'observations/h18-h19-repaired-observation.json',base/'base/quotes.db',base/'base/identity',
    base/'successors/successors.db',base/'successors/identity',base/'base/events.json',
    base/'base/reviewed-jumps.json',base/'terms/reorganizations.json',base/'protocol.json',out/'baseline-reproduced.json')
baseline = read(out/'baseline-reproduced.json')
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
          'strict_values_identical':not base_diffs and not diffs,
          'tolerance_reference':'research/session-20260910/integral/reconcile_h20.py',
          'absolute_and_relative_tolerance':2e-12,'baseline_differences':base_diffs,'floating_differences':diffs,
          'python':sys.version,'independent_cells':actual['independently_verified_cells'],
          'new_independent_economic_evidence':False,'profit_certified':False}
with output.open('x',encoding='utf-8') as stream:
    json.dump({'report':report,'reproduced':actual},stream,indent=2)
print(json.dumps(report,indent=2))
