"""Unexecuted research harness. Requires a permitted, isolated Linux host.

Usage: python -I -B linux_bootstrap_protocol.py --execute --output NEW_DIRECTORY
No install, data downloads, original database access or protected evaluators.
G1: 500 series per phi, 504 observations, block21, 1000 resamples, fixed seeds.
Comparison: IID normal vs arch stationary percentile; nominal95%, Wilson95%.
Stop at30minutes. Record every run, including failed checks; never tune to PASS.
Environment qualification and immutable dependency receipt are prerequisites.
"""
import argparse,datetime,hashlib,importlib.metadata,json,math,pathlib,platform,sys,time
p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
if not a.execute or platform.system()!='Linux' or sys.version_info[:2] not in [(3,13),(3,14)]:
 raise SystemExit('BLOCKED: explicit execution on permitted Linux Python3.13/3.14 required')
if a.output.exists():raise SystemExit('Refusing existing receipt directory')
import numpy as np
from arch.bootstrap import StationaryBootstrap
if importlib.metadata.version('arch')!='8.0.0':raise SystemExit('Requires reviewed arch8.0.0; requalify other versions')
a.output.mkdir(parents=True);start=time.monotonic();results=[]
environment={'python':sys.version,'platform':platform.platform(),'packages':{d.metadata['Name']:d.version for d in importlib.metadata.distributions()},'runner_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(a.output/'environment.json').write_text(json.dumps(environment,indent=2))
def wilson(k,n):
 q=k/n;z=1.96;d=1+z*z/n;center=(q+z*z/(2*n))/d;half=z*math.sqrt(q*(1-q)/n+z*z/(4*n*n))/d
 return [center-half,center+half]
try:
 for phi in [0,.5]:
  for i in range(500):
   rng=np.random.default_rng(20260911+i);x=rng.normal(scale=1/math.sqrt(1-phi*phi));values=[]
   for t in range(704):
    x=phi*x+rng.normal()
    if t>=200:values.append(x)
   y=np.asarray(values);m=y.mean();h=1.96*y.std(ddof=1)/math.sqrt(len(y))
   bs=StationaryBootstrap(21,y,seed=20270911+i)
   ci=bs.conf_int(np.mean,reps=1000,method='percentile',size=.95)
   r={'phi':phi,'seed':20260911+i,'iid_lower':float(m-h),'iid_upper':float(m+h),'block_lower':float(ci[0,0]),'block_upper':float(ci[1,0])};results.append(r)
   with (a.output/'all-series.jsonl').open('a') as f:f.write(json.dumps(r)+'\n')
   if time.monotonic()-start>1800:raise TimeoutError('G1 wall limit30min')
 summary=[]
 for phi in [0,.5]:
  selected=[r for r in results if r['phi']==phi]
  for method in ['iid','block']:
   k=sum(r[method+'_lower']<=0<=r[method+'_upper'] for r in selected);ci=wilson(k,len(selected))
   summary.append({'phi':phi,'method':method,'coverage':k/len(selected),'wilson95':ci,'nominal_inside':ci[0]<=.95<=ci[1]})
 (a.output/'summary.json').write_text(json.dumps({'result':'EXECUTED_NOT_ECONOMIC_VALIDATION','summary':summary,'seconds':time.monotonic()-start},indent=2))
except Exception as e:
 (a.output/'failure.json').write_text(json.dumps({'error':repr(e),'completed':len(results),'seconds':time.monotonic()-start}));raise
