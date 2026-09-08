"""Adversarial checks on disposable copied inputs, never the protected source tree."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from source_utils import ROOT, OUT, read
from stocks_predictor.source_closure import audit

base=ROOT/'work/stocks-final-review-bundle/inputs';original=OUT/'execution-inputs-04'
signals=ROOT/'work/h20-implementation-20260908/observation-02.json'
protocol=ROOT/'work/stocks-predictor/docs/research/2026-09-08-source-closure-protocol.json'
cases=[]
with tempfile.TemporaryDirectory(prefix='source-closure-negative-',dir=OUT) as scratch:
    target=Path(scratch)/'inputs';shutil.copytree(original,target)
    pristine=read(target/'SHA256.json')
    for kind in ['changed_primary_bytes','lost_entitlement','changed_gross','cleared_inventory']:
        manifest=deepcopy(pristine)
        if kind=='changed_primary_bytes':
            filename=next(k for k in manifest if k.startswith('primary/'))
            path=target/filename;saved=path.read_bytes();path.write_bytes(saved+b'corrupt')
        else:
            filename='evidence.json' if kind=='cleared_inventory' else 'cash-events.json'
            path=target/filename;saved=path.read_bytes();value=read(path)
            if kind=='lost_entitlement':value.pop(0)
            elif kind=='changed_gross':value[0]['gross_per_share']='1234567'
            else:value['execution_checks']['cash_coverage_inventory']['verified']=True
            path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
            manifest[filename]=hashlib.sha256(path.read_bytes()).hexdigest()
        (target/'SHA256.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
        try:audit(base,target,signals,protocol)
        except ValueError as exc:
            cases.append(dict(case=kind,rejected=True,reason=str(exc)));print(kind,str(exc),flush=True)
        else:raise AssertionError('unsafe revision accepted: '+kind)
        path.write_bytes(saved)
        shutil.copy2(original/'SHA256.json',target/'SHA256.json')
with (OUT/'revision-negative-checks.json').open('x',encoding='utf-8') as f:json.dump(cases,f,indent=2)
