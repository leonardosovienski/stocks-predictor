"""Reproduce the parent and reject forged duplicate/cash revisions."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from source_utils import ROOT, OUT, read
from stocks_predictor.source_closure import audit, DERIVED_REVIEW_SHAS

base=ROOT/'work/stocks-final-review-bundle/inputs'; original=OUT/'execution-inputs-13'
signals=ROOT/'work/h20-implementation-20260908/observation-02.json'
protocol=ROOT/'work/stocks-predictor/docs/research/2026-09-08-source-closure-protocol.json'
assert audit(base,OUT/'execution-inputs-12',signals,protocol)==read(OUT/'integrated-readiness-12.json')
assert audit(base,original,signals,protocol)==read(OUT/'integrated-readiness-13.json')
assert read(OUT/'overlooked-filings-index-13-v2.json')==read(OUT/'overlooked-filings-index-13-v3.json')
cases=[]
with tempfile.TemporaryDirectory(prefix='negative-13-',dir=OUT) as scratch:
    scratch_path=Path(scratch).resolve()
    assert scratch_path.parent==OUT.resolve()
    target=scratch_path/'inputs';assert target.resolve().is_relative_to(scratch_path)
    shutil.copytree(original,target);pristine=read(target/'SHA256.json')
    for kind in ['changed_primary_bytes','lost_entitlement','changed_gross','cleared_inventory',
                 'derived_labeled_primary','duplicate_reintroduced','duplicate_proof_removed',
                 'unreviewed_duplicate','forged_raw_locator','unbound_issuer','aliases_removed']:
        manifest=deepcopy(pristine)
        if kind=='changed_primary_bytes':
            filename=next(k for k in manifest if k.startswith('primary/'))
            path=target/filename;saved=path.read_bytes();path.write_bytes(saved+b'corrupt')
        else:
            filename={'cleared_inventory':'evidence.json','derived_labeled_primary':'primary-catalog.json',
                'duplicate_proof_removed':'duplicate-lineage.json','unreviewed_duplicate':'duplicate-lineage.json',
                'forged_raw_locator':'duplicate-lineage.json','unbound_issuer':'duplicate-lineage.json'}.get(kind,'cash-events.json')
            path=target/filename;saved=path.read_bytes();value=read(path)
            if kind=='lost_entitlement':value.pop(0)
            elif kind=='changed_gross':value[0]['gross_per_share']='1234567'
            elif kind=='cleared_inventory':value['execution_checks']['cash_coverage_inventory']['verified']=True
            elif kind=='derived_labeled_primary':
                next(v for v in value.values() if v['sha256'] in DERIVED_REVIEW_SHAS)['source_kind']='PRIMARY_SOURCE_RECORD'
            elif kind=='duplicate_proof_removed':value=[]
            elif kind=='unreviewed_duplicate':value[0]['source_review']=False
            elif kind=='forged_raw_locator':value[0]['raw_records'][1]['source']['row']=17
            elif kind=='unbound_issuer':value[0]['issuer_sources']=[{'note':'trust me'}]
            elif kind=='aliases_removed':
                next(v for v in value if v.get('duplicate_raw_event_ids')).pop('duplicate_raw_event_ids')
            else:
                row=deepcopy(next(v for v in value if v.get('duplicate_raw_event_ids')))
                row['event_id']=row.pop('duplicate_raw_event_ids')[0];value.append(row)
            path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
            manifest[filename]=hashlib.sha256(path.read_bytes()).hexdigest()
        (target/'SHA256.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
        try:audit(base,target,signals,protocol)
        except ValueError as exc:
            cases.append(dict(case=kind,rejected=True,reason=str(exc)));print(kind,str(exc),flush=True)
        else:raise AssertionError('unsafe revision accepted: '+kind)
        path.write_bytes(saved);shutil.copyfile(original/'SHA256.json',target/'SHA256.json')
    assert scratch_path.parent==OUT.resolve() and target.resolve().is_relative_to(scratch_path)
result=dict(parent_12_audit='IDENTICAL_WITH_UPDATED_CODE',current_13_audit='REPRODUCED',
    candidate_queue='174_IDENTICAL_WITH_TESTED_SELECTOR',adversarial_checks=cases,new_historical_return_evaluations=0)
with (OUT/'source-validation-13.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
print(json.dumps(result),flush=True)
