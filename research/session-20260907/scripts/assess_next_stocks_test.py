"""Read-only next-test feasibility: target overlap and verified cash coverage."""
from pathlib import Path
import hashlib
import json
import sqlite3
import statistics

ROOT=Path(__file__).resolve().parent.parent
observation=json.loads((ROOT/'outputs/h18-h19-reorganization-observation.json').read_text(encoding='utf-8'))
result={'mode':'DATA_AND_IMPLEMENTATION_FEASIBILITY_NOT_NEW_RETURN_EVALUATION','capital_brl':[5000,10000],
        'economic_hurdle_is_research_assumption_not_user_confirmed_profit_floor':True,'trials':[]}
for trial in observation['trials']:
    rows=[p for p in trial['periods'] if p['members']]
    changes=[]
    for old,new in zip(rows,rows[1:]):
        previous={m['ticker'] for m in old['members'] if m['selected']}
        current={m['ticker'] for m in new['members'] if m['selected']}
        changes.append({'asof':new['asof'],'retained':len(previous&current),'target_names':len(current),
                        'new_target_weight_fraction':len(current-previous)/len(current)})
    gross=trial['summary']['overall']['complete_case_spread_per_month']
    headroom=(gross-.0042)*trial['holding_months']
    result['trials'].append({'family':trial['family'],'holding_months':trial['holding_months'],
        'mean_new_target_weight_fraction':statistics.mean(c['new_target_weight_fraction'] for c in changes),
        'median_new_target_weight_fraction':statistics.median(c['new_target_weight_fraction'] for c in changes),
        'per_period_cost_headroom_at_same_hurdle':headroom,
        'full_roundtrip_equivalents_at_72bp_headroom':headroom/.0072,
        'changes':changes,
        'limitations':'Target-name overlap is NOT realized turnover, a turnover bound, or a net return. Price drift, sizing, forced cash, dividends, settlement and execution still need measurement.'})
db=ROOT/'work/stocks-tested-real-v2-20260907.db'
with sqlite3.connect(db.as_uri()+'?mode=ro',uri=True) as conn:
    result['cash_sources_by_kind']=dict(conn.execute('select kind,count(*) from research_source_documents group by kind'))
    result['verified_cash_events_by_ticker']=dict(conn.execute('select ticker,count(*) from cash_events group by ticker'))
    result['verified_cash_coverage']=[dict(zip(['ticker','start_date','end_date'],row)) for row in conn.execute('select ticker,start_date,end_date from cash_event_coverage')]
coverage=result['verified_cash_coverage']
for trial in result['trials']:
    source=next(t for t in observation['trials'] if (t['family'],t['holding_months'])==(trial['family'],trial['holding_months']))
    selected=[(m['ticker'],p['entry'],p['exit']) for p in source['periods'] for m in p['members'] if m['selected']]
    trial['selected_cells']=len(selected)
    trial['selected_cells_with_full_verified_cash_interval']=sum(any(r['ticker']==ticker and r['start_date']<=start and r['end_date']>=end for r in coverage) for ticker,start,end in selected)
result['next_test']='H19 quarterly: measure actual frozen-portfolio turnover and cash/event execution. Source feasibility first; no change to factor, selection, holding interval, hurdle or stress prices. Do not reinvest uncredited stock or unpaid cash.'
result['why_not_new_h11_or_ml']='Rebuilding total-return momentum needs a longer clean signal history. New model complexity cannot repair absent cash or settlement data.'
result['research_status']='Cheap portfolio-execution feasibility is worth checking; no priority upgrade, replication or deployable alpha is claimed.'
result['stopping_rule']='One fixed construction comparison; abandon if full historical cash coverage cannot be obtained cheaply or if integer-sizing/worst-price stress removes economic headroom. Do not optimize turnover thresholds or period selection.'
path=ROOT/'outputs/H19_PROXIMO_TESTE_VIABILIDADE.json'
with path.open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2)
print(json.dumps({**result,'trials':[{k:v for k,v in t.items() if k!='changes'} for t in result['trials']]},ensure_ascii=False,indent=2))
