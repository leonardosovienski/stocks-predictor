"""Run the registered audit without changing old observations or source data."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent.parent
WORK=ROOT/'work'
sys.path.insert(0,str(WORK/'stocks-predictor'))
from stocks_predictor.discovery_reorganizations import merged_market
from stocks_predictor.discovery_h17 import adjustment_map
from stocks_predictor.discovery_value import group_events
from stocks_predictor.profit_validation import audit_trials

def read(p):return json.loads(p.read_text(encoding='utf-8'))
if '539 passed' not in (WORK/'profit-validation-tests.log').read_text(encoding='utf-8'):
    raise RuntimeError('Full clean-checkout suite must pass before new observation')
protocol_path=WORK/'stocks-predictor/docs/research/2026-09-07-profit-validation-protocol.json'
protocol=read(protocol_path)
source=ROOT/'outputs/h18-h19-reorganization-observation.json'
if hashlib.sha256(source.read_bytes()).hexdigest()!=protocol['source_observation_sha256']:
    raise ValueError('Frozen observation changed')
bars,identities=merged_market(WORK/'value-measurement-source/quotes.db',WORK/'value-measurement-source/identity',
                              WORK/'value-successor-source/successors.db',WORK/'value-successor-source/identity')
events,legacy=group_events(read(WORK/'value-measurement-source/events.json'))
factors={ticker:adjustment_map(events[ticker],legacy[ticker])[0] for ticker in bars}
boot_path=WORK/'stocks-predictor/vendor/predictor_core/measurement/bootstrap.py'
spec=importlib.util.spec_from_file_location('stocks_existing_core_bootstrap',boot_path)
boot=importlib.util.module_from_spec(spec)
spec.loader.exec_module(boot)
result=audit_trials(read(source),bars,factors,read(WORK/'value-event-terms/reorganizations.json'),boot.bootstrap_ci)
result.update(protocol=protocol,observed_at_utc=datetime.now(timezone.utc).isoformat(),
              source_observation_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
              bootstrap_source_sha256=hashlib.sha256(boot_path.read_bytes()).hexdigest(),
              validator_source_sha256=hashlib.sha256((WORK/'stocks-predictor/stocks_predictor/profit_validation.py').read_bytes()).hexdigest(),
              budget={'nominal_configurations_minimum_after':32,'historical_return_evaluations_minimum_after':37,
                      'reason':'Eight new execution-price sensitivities; no new asset selection or independent holdout.'})
out=ROOT/'outputs/VALIDACAO_LUCRO_STOCKS.json'
with out.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False)
print('independent cells',result['independently_verified_cells'],'max error',result['max_absolute_return_difference'])
for t in result['trials']:
    for mode,m in t['modes'].items():
        s=m['summary']
        print(json.dumps({'family':t['family'],'horizon':t['holding_months'],'mode':mode,
                          'spread72':s['spread_after_72bp_per_month'],
                          'CI95':s['descriptive_stationary_bootstrap_95pct_after_72bp'],
                          'strategy_gross':s['synthetic_strategy_gross'],
                          'benchmark_gross':s['synthetic_benchmark_gross']},ensure_ascii=False))
