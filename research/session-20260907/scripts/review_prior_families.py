"""Reclassify reliability, not historical returns; no trials are rerun here."""
from pathlib import Path
import hashlib,json
root=Path.cwd();repo=root/'work/stocks-predictor'
trials=json.loads((repo/'trials.json').read_text(encoding='utf-8'))
families={1:('momentum 12-1','INCONCLUSIVE_METHOD'),2:('low volatility','INCONCLUSIVE_METHOD'),
4:('inverse-volatility sizing','WEAK_NEGATIVE_UNDER_LEGACY_MEASUREMENT'),5:('21-day reversal','STRONGEST_NEGATIVE_UNDER_LEGACY_MEASUREMENT'),
6:('momentum 6-1','INCONCLUSIVE_METHOD'),7:('ROE','WEAK_POSITIVE_DATA_AND_METHOD_LIMITED'),8:('momentum and low-volatility','WEAK_POSITIVE_METHOD_LIMITED'),
9:('low leverage','INCONCLUSIVE_DATA_AND_METHOD'),10:('ROE and low leverage','INCONCLUSIVE_DATA_AND_METHOD'),
11:('momentum with approximate cash distributions','APPARENT_POSITIVE_UNVERIFIED_TOTAL_RETURN'),12:('net margin','INCONCLUSIVE_DATA_AND_METHOD'),
13:('revenue growth','INCONCLUSIVE_DATA_AND_METHOD'),14:('52-week high proximity','WEAK_POSITIVE_METHOD_LIMITED'),15:('relative volume','INCONCLUSIVE_METHOD'),
16:('turn of month','WEAK_NEGATIVE_UNDER_LEGACY_MEASUREMENT')}
common=['Historical quantities not carried self-financing between rebalance dates; daily averages implement an implicit reset.',
        'Quarantine resolution uses its current state, rather than resolution known at each historical signal.',
        'Missing quotes and terminal delistings do not have a fully documented settlement model.',
        'Shared adaptive historical window; no intact confirmation sample demonstrated.']
rows=[]
for trial in trials:
 n=int(trial['name'].split('-')[0][1:]);description,status=families[n]
 errors=common.copy()
 if n!=16:errors+=['Signal uses the same closing price from which evaluated returns start, despite next_open configuration.',
                   'Benchmark is a daily average over available assets, not self-financing buy-and-hold with symmetric costs.']
 if n in {7,9,10,12,13}:errors+=['Legacy CVM issuer/date/version/scale assumptions; source repairs materially affect eligibility and signal values.']
 if n==11:errors+=['Payment dates used as ex-date proxies, class-average distributions and split-adjusted price divided into historical cash amounts.',
                  '2018-2022 actual window differs from generic ledger period; compare only like-for-like evidence.']
 elif n!=16:errors+=['Price-only target omits cash distributions, with a strategy-dependent relative bias.']
 if n==16:errors+=['Timing uses same-day close-to-close returns and free daily equal weighting; cash return is zero and composition turnover omitted.']
 rows.append({'hypothesis':'H'+str(n),'trial_name':trial['name'],'mechanism':description,
              'historical_official_verdict_preserved':'NOT_SUPPORTED','updated_reliability':status,
              'execution_ready_alpha_evidence':False,'material_reopening_basis':'Demonstrated data/execution errors, only through a separate disclosed replication protocol.',
              'automatic_reopening':False,'issues':errors})
record={'review_type':'READ_ONLY_POST_REPAIR_RELIABILITY_REVIEW','historical_trials':len(rows),'H3_executed':False,
        'new_return_observations':0,'families':rows,
        'decision':'Do not rerun all closed families or pick the highest old Sharpe. First test the genuinely new valuation information already registered as H18/H19, with original reported share counts, fixed order and explicit observable-proxy limitations.',
        'why_not_H11_first':'Its favorable point estimate is unvalidated, its total-return input is materially unreliable, and complete historical corporate-action repair is still expensive.',
        'why_not_more_H17_tuning':'First price diagnostic is weak and partly censored; no empirical basis for reversing the direction or optimizing thresholds.',
        'economic_priority':'Use actual owner earnings/equity and disclosed share capital, instead of adding models or more combinations of weak existing factors.',
        'source_hashes':{name:hashlib.sha256((repo/name).read_bytes()).hexdigest() for name in ['trials.json','stocks_predictor/backtest.py','stocks_predictor/universe.py','stocks_predictor/adjust.py']}}
dest=root/'outputs/REVISAO_H1_H16_APOS_CORRECOES.json'
dest.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
print('reviewed',len(rows),'new_returns',0,'next','H18 then H19 disclosed-capital discovery')
