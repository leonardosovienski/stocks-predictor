import copy,datetime,decimal,hashlib,importlib.util,json,pathlib,platform,time
ROOT=pathlib.Path(__file__).parent
source=pathlib.Path('C:/STOCKS/stocks-predictor/stocks_predictor/simulation.py')
spec=importlib.util.spec_from_file_location('mechanical_simulation',source)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
D=decimal.Decimal;days=['2000-01-03','2000-01-04','2000-01-05','2000-01-06'];results=[]
def run(bars,**kw):return mod.simulate_portfolio(days,{'AAAA3':bars},{days[0]:{'AAAA3':1}},initial_cash=1000,**kw)
def check(name,fn):
 try:detail=fn();results.append(dict(case=name,status='PASS',detail=detail))
 except Exception as e:results.append(dict(case=name,status='FAIL',error=repr(e)))
def close(x,y):
 err=abs(x-float(y));assert err<=1e-8,(x,str(y),err);return err
def gap():
 r=run(dict(zip(days,[(100,100),(200,220),(220,242),(242,242)])),cost_per_side=0)
 assert all(e['exec_date']>e['signal_date'] for e in r['executions'])
 return {'error_brl':close(r['nav'][-1],D(1000)/D(200)*D(242))}
def cost():
 r=run({d:(100,100) for d in days},cost_per_side=.01)
 return {'error_brl':close(r['nav'][-1],D(1000)/D('1.01'))}
def split():
 r=run(dict(zip(days,[(100,100),(100,100),(50,50),(50,50)])),cost_per_side=0,splits={'AAAA3':{days[2]:.5}})
 assert r['holdings']['AAAA3']==20
 return {'error_brl':close(r['nav'][-1],1000)}
def cash():
 r=run(dict(zip(days,[(100,100),(100,100),(90,90),(90,90)])),cost_per_side=0,cash_events={'AAAA3':[(days[2],days[3],10)]})
 assert r['cash']==100
 return {'error_brl':max(close(v,1000) for v in r['nav'])}
def stale():
 try:run({d:(100,100) for d in days[:-1]},cost_per_side=0)
 except ValueError as e:assert 'stale' in str(e);return str(e)
 raise AssertionError('stale holding accepted')
def future():
 b={d:(100,100) for d in days};r=run(b,cost_per_side=0);b2=copy.deepcopy(b);b2[days[-1]]=(900,1000);s=run(b2,cost_per_side=0)
 assert r['nav'][:-1]==s['nav'][:-1] and r['executions']==s['executions'];return 'prefix invariant'
def missing():
 r=run({days[2]:(100,100),days[3]:(100,100)},cost_per_side=0)
 assert r['nav'][1]==1000 and r['executions'][0]['exec_date']==days[2];return 'cash retained until first quote'
def closing():
 r=run(dict(zip(days,[(100,100),(100,200),(200,220),(220,220)])),cost_per_side=0,price_mode='next_close')
 return {'error_brl':close(r['nav'][-1],D(1000)/D(200)*D(220))}
t=time.perf_counter()
for name,fn in [('entrada após gap',gap),('custo proporcional',cost),('split',split),('dividendo',cash),('stale',stale),('futuro',future),('sem cotação',missing),('fechamento',closing)]:check(name,fn)
receipt={'id':'OSS-20260911-01-MECH-01','executed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'python':platform.python_version(),'platform':platform.platform(),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'protocol_sha256':hashlib.sha256((ROOT/'G1.json').read_bytes()).hexdigest(),'runner_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'seconds':time.perf_counter()-t,'results':results,'scope':'LOCAL/ENGINEERING; C3; E5; no external engine execution; no economic validation'}
(ROOT/'mechanical-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(receipt,ensure_ascii=False));raise SystemExit(any(r['status']=='FAIL' for r in results))
