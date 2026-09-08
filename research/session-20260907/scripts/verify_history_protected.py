import json
import pathlib
from datetime import datetime, timezone
from inspect_state import ROOT, REPO, CANON, digest

baseline=json.loads((ROOT/'outputs/state-evidence.json').read_text(encoding='utf-8'))
checks=[]
for p,expected in baseline['file_hashes'].items():
    if pathlib.Path(p)==REPO/'trials_v2.json':
        continue
    actual=digest(pathlib.Path(p))
    checks.append({'path':p,'before_sha256':expected,'after_sha256':actual,'unchanged':actual==expected})
for i in (14,15,16):
    rel=f'reports/h{i}_verdict_adhoc.md'
    checks.append({'path':rel,'source_sha256':digest(CANON/rel),'copied_sha256':digest(REPO/rel),'unchanged':digest(CANON/rel)==digest(REPO/rel)})
out={'checked_at':datetime.now(timezone.utc).isoformat(),'all_protected_inputs_unchanged':all(c['unchanged'] for c in checks),'checks':checks,
     'declared_derived_change':'Only audit-checkout trials_v2.json regenerated from existing 15-trial legacy ledger. Operational checkout untouched.'}
(ROOT/'outputs/historical-protected-integrity.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(out['all_protected_inputs_unchanged'])
assert out['all_protected_inputs_unchanged']
