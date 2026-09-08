"""Validate the clean committed checkout; build without installing the package."""
import json
import os
from pathlib import Path
import subprocess
import sys
from source_utils import ROOT, OUT

repo=ROOT/'work/stocks-predictor'
assert subprocess.check_output(['git','status','--porcelain'],cwd=repo)==b''
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
env={**os.environ,'PYTHONUTF8':'1','PYTHONIOENCODING':'utf-8',
     'PYTHONPATH':os.pathsep.join(map(str,[repo,ROOT/'work/runtime',ROOT/'work/checks',ROOT/'work/lint']))}
commands=[('full-tests-13.log',['-m','pytest','tests','research/session-20260908/chat-review/test_h20_evidence_integrity.py',
    'research/session-20260908/h20-profit-test/test_h20_profit_comparison.py','-q']),
    ('ruff-13.log',['-m','ruff','check','stocks_predictor','tests','main.py']),
    ('pyright-13.log',['-m','pyright']),
    ('wheel-build-13.log',['-m','hatchling','build','-t','wheel','-d',str(OUT/'dist-13')])]
results=[]
for name,args in commands:
    p=subprocess.run([sys.executable,*args],cwd=repo,env=env,capture_output=True,text=True,encoding='utf-8')
    with (OUT/name).open('x',encoding='utf-8') as f:f.write(p.stdout+p.stderr)
    print(name,p.stdout[-1500:]+p.stderr[-1500:],flush=True)
    results.append({'log':name,'returncode':p.returncode})
    assert p.returncode==0,name
assert subprocess.check_output(['git','status','--porcelain'],cwd=repo)==b''
with (OUT/'code-validation-13.json').open('x',encoding='utf-8') as f:
    json.dump(dict(tested_commit=commit,commands=results,new_historical_return_evaluations=0),f,indent=2)
