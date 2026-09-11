"""Run only the frozen closure protocol. All fixtures synthetic and deterministic."""
import pathlib,importlib.util,json,hashlib,time,datetime,sys,statistics,itertools
W=pathlib.Path(__file__).parent;R=pathlib.Path('C:/STOCKS/stocks-predictor')
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
c=module('closure_capabilities',W/'capabilities.py');p=module('frozen_portfolio',R/'stocks_predictor/portfolio.py')
start=time.perf_counter();checks=[];results={};fixtures={}
def check(name,ok):checks.append({'test':name,'pass':bool(ok)})
def rejects(name,fn):
 try:fn();check(name,False)
 except ValueError:check(name,True)
train=[{'time':i,'known_at':i,'value':i} for i in range(10)];future=[{'time':i,'known_at':i,'value':1e9} for i in range(10,110)]
fixtures['K05']={'train':train,'future_poison':future}
a=c.fit_normalizer(train,0,10,10);b=c.fit_normalizer(train+future,0,10,10)
check('K05.future_append_invariance',a==b and a.transform(range(10))==b.transform(range(10)))
check('K05.analytic_fit',a.center==4.5 and abs(a.scale**2-8.25)<1e-12)
rejects('K05.fit_crosses_decision',lambda:c.fit_normalizer(train+future,0,11,10))
late=[dict(r,known_at=11) if r['time']==5 else r for r in train]
rejects('K05.late_training_value',lambda:c.fit_normalizer(late,0,10,10))
rejects('K05.constant_feature_explicit',lambda:c.fit_normalizer([dict(r,value=1) for r in train],0,10,10))
check('K05.unknown_not_imputed',a.transform([None,float('nan')])==[None,None])
results['K05']={'parameters':vars(a),'future_rows_ignored':100,'unprotected_all_rows_mean':statistics.mean([r['value'] for r in train+future]),'protected_mean':a.center,'baseline_scope':'No general ML fitted-transform contract in inspected runtime; all-row fit is deliberately flawed ablation, not production behavior','decision':'INTEGRATE_CANDIDATE'}
rows=[{'date':d,'asset':f'A{i}','score':100*d+i,'label':100*d+(5-i)} for d in range(2) for i in range(1,5)]
fixtures['K07']=rows;r=c.ranking_report(rows)
pooled=c.rank_ic([x['score'] for x in rows],[x['label'] for x in rows])
check('K07.date_not_pooled',r['mean_date_ic']==-1 and pooled>0)
check('K07.tie_average',c.ranks([1,1,3,4])==[1.5,1.5,3,4] and c.rank_ic([1,1,3,4],[1,1,3,4])==1)
check('K07.constant_undefined',c.rank_ic([1,1,1],[1,2,3]) is None)
missing=[dict(x,label=None) if x['date']==0 and x['asset']=='A4' else x for x in rows]
miss=c.ranking_report(missing)
check('K07.missing_label_does_not_select',miss['dates'][0]['top']==r['dates'][0]['top'] and miss['dates'][0]['spread'] is None and miss['dates'][0]['missing_labels']==1)
rejects('K07.duplicate_rejected',lambda:c.ranking_report(rows+[rows[0]]))
check('K07.monotone_invariance',c.ranking_report([dict(x,score=x['score']**3) for x in rows])['mean_date_ic']==-1)
check('K07.analytic_spread',all(x['spread']==-3 for x in r['dates']))
# Exhaustive no-tie permutation oracle: independent closed form 1-6*sum(d^2)/(n(n^2-1)).
maxerr=0
for perm in itertools.permutations(range(5)):
 oracle=1-6*sum((i-perm[i])**2 for i in range(5))/(5*24)
 maxerr=max(maxerr,abs(c.rank_ic(list(range(5)),list(perm))-oracle))
check('K07.120_permutation_oracles',maxerr<1e-12)
results['K07']={'pooled_ic_flawed_ablation':pooled,'correct_date_ic':r['mean_date_ic'],'report':r,'permutations_checked':120,'oracle_max_error':maxerr,'missing_label_case':miss,'baseline_scope':'existing selector supplies membership; diagnostic panel is incremental; pooled IC is deliberate ablation','decision':'INTEGRATE_CANDIDATE'}
residual=[-1.5,-.5,.5,1.5];groups={f'{g}{i}':{'group':g,'known_at':0} for g in ['A','B'] for i in range(4)}
scores={f'{g}{i}':(10 if g=='A' else -10)+residual[i] for g in ['A','B'] for i in range(4)}
n=c.group_residual(scores,groups,1);fixtures['K22']={'groups':groups,'scores':scores}
check('K22.planted_residual_recovered',all(n['residual'][f'{g}{i}']==residual[i] for g in ['A','B'] for i in range(4)))
check('K22.zero_group_means',all(abs(sum(n['residual'][f'{g}{i}'] for i in range(4)))<1e-12 for g in ['A','B']))
pure={a:(10 if a[0]=='A' else -10) for a in scores};pure_n=c.group_residual(pure,groups,1)
check('K22.pure_group_no_residual_signal',set(pure_n['residual'].values())=={0} and c.rank_ic(list(pure_n['residual'].values()),list(scores.values())) is None)
rejects('K22.future_group_block',lambda:c.group_residual(scores,{a:dict(g,known_at=2) for a,g in groups.items()},1))
rejects('K22.singleton_block',lambda:c.group_residual({'A0':1},{'A0':groups['A0']},1))
raw_order=list(scores);rawic=c.rank_ic([scores[a] for a in raw_order],[residual[int(a[1:])] for a in raw_order]);neutralic=c.rank_ic([n['residual'][a] for a in raw_order],[residual[int(a[1:])] for a in raw_order])
reverseic=c.rank_ic(list(n['residual'].values()),[-x for x in n['residual'].values()])
check('K22.reversal_not_hidden',reverseic==-1)
results['K22']={'raw_score_ic_with_planted_residual':rawic,'neutralized_ic':neutralic,'group_component_mean_abs_before':10,'group_component_mean_abs_after':0,'reversal_ic':reverseic,'pure_factor_residual_ic':None,'decision':'INTEGRATE_CANDIDATE_DIAGNOSTIC_ONLY','economic_note':'neutralization removes group information including genuine future group premia; not a universally better signal'}
vol=[{'time':i,'known_at':i,'volume_brl':100000} for i in [7,8,9]]
cases={'valid':(1000,vol),'insufficient':(1000,vol[:2]),'late':(1000,[dict(x,known_at=10) for x in vol]),'zero':(1000,[dict(x,volume_brl=0) for x in vol]),'negative':(1000,[dict(x,volume_brl=-1) for x in vol]),'oversized':(2000,vol)}
screens={k:c.participation_screen(*args,decision=10) for k,args in cases.items()};fixtures['K21']=cases
check('K21.six_cases_only_valid_passes',[k for k,v in screens.items() if v['eligible']]==['valid'])
check('K21.future_spike_invariant',screens['oversized']==c.participation_screen(2000,vol+[{'time':10,'known_at':10,'volume_brl':1e12}],10))
check('K21.reject_duplicate',not c.participation_screen(1000,vol+[vol[0]],10)['eligible'])
results['K21']={'cases':screens,'rejected':5,'accepted':1,'baseline_scope':'universe liquidity rank does not promise feasibility of an individual order; no production universe bug alleged','decision':'INTEGRATE_CANDIDATE'}
def desired(which):
 sig={a:(1 if a in which else 0) for a in ['A','B','C','D']};w=p.select_portfolio(sig,quantile=.5)
 return {**{a:.98*x for a,x in w.items()},'CASH':.02}
initial=desired(['A','B']);targets=[desired(['C','D'] if i%2==0 else ['A','B']) for i in range(20)];fixtures['K09']={'initial':initial,'targets':targets,'budget':.1,'fee':.002}
def path(budget):
 old=initial;nav=1.;totalcost=0.;records=[]
 for target in targets:
  row=c.bounded_rebalance(old,target,budget);records.append(row)
  totalcost+=nav*row['cost_fraction_initial_nav'];nav*=row['nav_fraction_after_fee']
  old={k:(row['cash_fraction_initial_nav_after_fee'] if k=='CASH' else v)/row['nav_fraction_after_fee'] for k,v in row['pre_fee_weights'].items()}
 return {'final_nav_cost_only':nav,'cash_cost_initial_nav':totalcost,'sum_turnover':sum(x['turnover'] for x in records),'records':records}
full=path(1);limited=path(.1)
check('K09.cost_reduction',limited['cash_cost_initial_nav']<full['cash_cost_initial_nav'])
check('K09.budget_bound',max(x['turnover'] for x in limited['records'])<=.1+1e-12)
check('K09.accounting_conservation',all(abs(x['final_nav_cost_only']+x['cash_cost_initial_nav']-1)<1e-12 for x in [full,limited]))
check('K09.weights_cash_caps',all(abs(sum(x['pre_fee_weights'].values())-1)<1e-12 and x['cash_fraction_initial_nav_after_fee']>=0 and max(v for k,v in x['pre_fee_weights'].items() if k!='CASH')<=.5+1e-12 for x in limited['records']))
check('K09.zero_budget_no_trade',c.bounded_rebalance(initial,targets[0],0)['turnover']==0)
check('K09.broad_budget_target',c.bounded_rebalance(initial,targets[0],1)['target_completion']==1)
rejects('K09.no_fee_reserve_block',lambda:c.bounded_rebalance({'A':.5,'B':.5},{'C':.5,'D':.5},1))
stress={'A':-.02,'B':-.02,'C':.02,'D':.02,'CASH':0}
def stress_net(row):return sum(w*stress[k] for k,w in row['pre_fee_weights'].items())-row['cost_fraction_initial_nav']
adverse={'full_rebalance':stress_net(full['records'][0]),'limited':stress_net(limited['records'][0])}
check('K09.adverse_counterexample_retained',adverse['limited']<adverse['full_rebalance'])
results['K09']={'full':full,'limited':limited,'cost_reduction_fraction':1-limited['cash_cost_initial_nav']/full['cash_cost_initial_nav'],'adverse_regime_net':adverse,'decision':'KEEP_EXPERIMENTAL','rejected_claim':'Lower turnover always improves net result','economic_scope':'synthetic counterexample, not B3 economic test; prices otherwise constant for cost-only path'}
elapsed=time.perf_counter()-start;check('resource_budget',elapsed<60)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
preserved=json.loads((W/'preservation-before.json').read_text());check('prior_science_and_runtime_preserved',all(sha(pathlib.Path(p))==h for p,h in preserved.items()))
for name,x in [('fixtures.json',fixtures),('benchmark-results.json',results)]: (W/name).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
receipt={'run_id':'OSS-20260911-01','observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'python':sys.version,'elapsed_seconds':elapsed,'protocol_sha256':sha(W/'protocol.json'),'code_sha256':sha(W/'capabilities.py'),'runner_sha256':sha(W/'benchmark.py'),'existing_portfolio_sha256':sha(R/'stocks_predictor/portfolio.py'),'fixtures_sha256':sha(W/'fixtures.json'),'results_sha256':sha(W/'benchmark-results.json'),'checks':checks,'pass':all(x['pass'] for x in checks),'economic_test':False,'external_engine_executed':False,'prior_files_preserved':len(preserved),'attempt':'current; prior failed receipts retained separately when applicable'}
(W/'benchmark-receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps({'pass':receipt['pass'],'checks':len(checks),'failed':[x for x in checks if not x['pass']],'K07_pooled':pooled,'K07_date':r['mean_date_ic'],'K22_raw_ic':rawic,'K22_neutral_ic':neutralic,'K09_cost_full':full['cash_cost_initial_nav'],'K09_cost_limited':limited['cash_cost_initial_nav'],'K09_adverse':adverse,'seconds':elapsed},indent=2))
if not receipt['pass']:raise SystemExit(1)
