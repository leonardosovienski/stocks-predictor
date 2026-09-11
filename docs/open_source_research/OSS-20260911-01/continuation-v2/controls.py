import copy,datetime,hashlib,json,math,pathlib,platform,random,statistics,sys,time
W=pathlib.Path(__file__).parent;REPO=pathlib.Path('C:/STOCKS/stocks-predictor');sys.path.insert(0,str(REPO/'stocks_predictor'))
import document_panel as panel
import economic_gate
start=time.monotonic();results=[]
def check(name,fn):
 try:fn();results.append({'case':name,'status':'PASS'})
 except Exception as e:results.append({'case':name,'status':'FAIL','error':repr(e)})
def eq(a,b):assert a==b,(a,b)
def raises(fn,text):
 try:fn()
 except ValueError as e:assert text in str(e);return
 raise AssertionError('expected rejection')
f={'cnpj':'1','ref_date':'2023-12-31','document_version':1,'available_at':'2024-03-01','accruals':.1}
s={'cnpj':'1','ref_date':'2024-01-01','version':1,'available_at':'2024-04-01','ticker':'AAAA3','trading_start':'2010-01-01','trading_end':None,'document_id':'FCA1'}
asof='2024-04-01'
run=lambda fs=[f],ss=[s],day=asof,**kw:panel.fundamentals_asof(fs,ss,day,**kw)
check('before availability',lambda:eq(run(day='2024-03-31'),{}))
check('exact availability',lambda:eq(run(),{'AAAA3':f}))
check('future append invariance',lambda:eq(run([f,{**f,'available_at':'2025-01-01','document_version':9,'accruals':99}]),run()))
new={**f,'document_version':2,'available_at':asof,'accruals':None}
check('revision available',lambda:eq(run([f,new])['AAAA3']['accruals'],None))
check('conflicting version',lambda:raises(lambda:run([f,{**f,'accruals':9}]),'conflicting'))
check('ambiguous ticker',lambda:raises(lambda:run([f,{**f,'cnpj':'2'}],[s,{**s,'cnpj':'2'}]),'ambiguous'))
check('future security',lambda:eq(run(ss=[{**s,'available_at':'2025-01-01'}]),{}))
check('expired security',lambda:eq(run(ss=[{**s,'trading_end':'2024-03-31'}]),{}))
check('two classes',lambda:eq(sorted(run(ss=[s,{**s,'ticker':'AAAA4'}])),['AAAA3','AAAA4']))
check('new blank metadata',lambda:eq(run(security_metadata=[s,{**s,'version':2,'document_id':'FCA2'}]),{}))
check('three issuers',lambda:eq(len(run([{**f,'cnpj':str(j)} for j in range(3)],[{**s,'cnpj':str(j),'ticker':f'X{j}3'} for j in range(3)])),3))
check('future reference',lambda:eq(run([{**f,'ref_date':'2025-12-31'}]),{}))
fixture=REPO/'tests/fixtures/real_integration';provenance=json.loads((fixture/'provenance.json').read_text())
for doc,total,treasury,scale in [('134335',15753833000,4384000,'Mil'),('133944',2865417020,11640980,'Unidade'),('134790',2039086540,3772375,'Unidade')]:
 def verify(doc=doc,total=total,treasury=treasury,scale=scale):
  name=f'capital-{doc}.html';payload=(fixture/name).read_bytes();eq(hashlib.sha256(payload).hexdigest(),provenance[name]['sha256'])
  r=panel.capital_from_viewer(payload,{'ref_date':'2023-12-31','document_id':doc},'CVM')
  eq((r['total'],r['treasury_total'],r['share_scale'],r['eligible_for_valuation']),(total,treasury,scale,False))
 check('public document '+doc,verify)
def wilson(k,n):
 p=k/n;z=1.96;a=1+z*z/n;c=(p+z*z/(2*n))/a;d=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/a
 return [c-d,c+d]
unc=[];n=504
for phi in [0,.5]:
 counts=[0,0];widths=[[],[]]
 var_mean=(n+2*sum((n-k)*phi**k for k in range(1,n)))/(n*n*(1-phi*phi))
 for i in range(500):
  rng=random.Random(20260911+i);x=rng.gauss(0,1/math.sqrt(1-phi*phi));values=[]
  for t in range(n+200):
   x=phi*x+rng.gauss(0,1)
   if t>=200:values.append(x)
  est=economic_gate.estimate_edge(values,minimum_observations=12,z_score=1.96)
  m=est.mean_gross_edge;half=m-est.lower_gross_edge
  for j,h in enumerate([half,1.96*math.sqrt(var_mean)]):counts[j]+=int(abs(m)<=h);widths[j].append(2*h)
  if time.monotonic()-start>120:raise TimeoutError('predefined wall budget')
 for j,name in enumerate(['current iid','known AR covariance oracle']):
  ci=wilson(counts[j],500);unc.append({'phi':phi,'method':name,'covered':counts[j],'n':500,'coverage':counts[j]/500,'wilson95':ci,'mean_width':statistics.mean(widths[j]),'nominal_inside_interval':ci[0]<=.95<=ci[1]})
scores=list(range(20));returns=[-.1+j*.001 for j in scores];rho=1-6*sum((j-k)**2 for j,k in zip(scores,sorted(scores)))/(20*(20*20-1))
rank={'spearman':rho,'top5_gross':statistics.mean(returns[-5:]),'top5_net':statistics.mean(returns[-5:])-.001,'baseline_cash_synthetic':0}
assert rank['spearman']==1 and rank['top5_net']<rank['top5_gross']<0
receipt={'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'python':platform.python_version(),'command':'python -I -B -X utf8 controls.py','protocol_sha256':hashlib.sha256((W/'G1.json').read_bytes()).hexdigest(),'runner_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'source_sha256':{name:hashlib.sha256((REPO/'stocks_predictor'/name).read_bytes()).hexdigest() for name in ['document_panel.py','source_history.py','cvm_pit.py','ingest_cvm.py','economic_gate.py']},'pit':results,'uncertainty':unc,'ranking':rank,'seconds':time.monotonic()-start,'external_packages_executed':False,'economic_result':'NOT_EVALUATED'}
(W/'controls-receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');print(json.dumps(receipt,indent=2))
