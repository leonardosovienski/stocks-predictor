"""Regression parity and adversarial copies for the final source revision."""
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from source_utils import ROOT, OUT, read, pages
from stocks_predictor.source_closure import audit, DERIVED_REVIEW_SHAS
from stocks_predictor.cash_source_audit import parse_b3_credit_pages

old=read(OUT/'current-credit-reconciliation.json'); rows=[]; incomplete=[]; counts=Counter()
fields=('isin','action','approval_date','gross_per_share','payment_date')
for d in old['documents']:
    r=parse_b3_credit_pages(pages(d['file']),d['file'][-14:-4]);counts[r['status']]+=1
    rows.extend(tuple(v[k] for k in fields) for v in r['rows'])
    incomplete.extend(r['incomplete_rows'])
assert Counter(rows)==Counter(tuple(v[k] for k in fields) for v in old['credit_rows'])
parser=dict(status='EXACT_PARITY_FOR_COMPLETE_ROWS',complete_rows=len(rows),
    incomplete_rows_preserved=len(incomplete),documents=len(old['documents']),statuses=dict(counts))
print(parser,flush=True)

base=ROOT/'work/stocks-final-review-bundle/inputs'; original=OUT/'execution-inputs-12'
signals=ROOT/'work/h20-implementation-20260908/observation-02.json'
protocol=ROOT/'work/stocks-predictor/docs/research/2026-09-08-source-closure-protocol.json'
cases=[]
with tempfile.TemporaryDirectory(prefix='negative-12-',dir=OUT) as scratch:
    scratch_path=Path(scratch).resolve()
    assert scratch_path.parent==OUT.resolve()
    target=scratch_path/'inputs';assert target.resolve().is_relative_to(scratch_path)
    shutil.copytree(original,target);pristine=read(target/'SHA256.json')
    for kind in ['changed_primary_bytes','lost_entitlement','changed_gross','cleared_inventory','derived_labeled_primary']:
        manifest=deepcopy(pristine)
        if kind=='changed_primary_bytes':
            filename=next(k for k in manifest if k.startswith('primary/'))
            path=target/filename;saved=path.read_bytes();path.write_bytes(saved+b'corrupt')
        else:
            filename={'cleared_inventory':'evidence.json','derived_labeled_primary':'primary-catalog.json'}.get(kind,'cash-events.json')
            path=target/filename;saved=path.read_bytes();value=read(path)
            if kind=='lost_entitlement':value.pop(0)
            elif kind=='changed_gross':value[0]['gross_per_share']='1234567'
            elif kind=='cleared_inventory':value['execution_checks']['cash_coverage_inventory']['verified']=True
            else:
                next(v for v in value.values() if v['sha256'] in DERIVED_REVIEW_SHAS)['source_kind']='PRIMARY_SOURCE_RECORD'
            path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
            manifest[filename]=hashlib.sha256(path.read_bytes()).hexdigest()
        (target/'SHA256.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
        try:audit(base,target,signals,protocol)
        except ValueError as exc:
            cases.append(dict(case=kind,rejected=True,reason=str(exc)));print(kind,str(exc),flush=True)
        else:raise AssertionError('unsafe revision accepted: '+kind)
        path.write_bytes(saved);shutil.copyfile(original/'SHA256.json',target/'SHA256.json')
    assert scratch_path.parent==OUT.resolve() and target.resolve().is_relative_to(scratch_path)
result=dict(parser=parser,adversarial_checks=cases,new_historical_return_evaluations=0)
with (OUT/'source-validation-12.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
