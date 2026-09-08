from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(r'C:\Users\Superleo13\stocks-predictor-work\.local-research\stocks-session-20260907')
REPO=ROOT/'work/stocks-predictor'
OUT=ROOT/'work/source-closure-20260908'
OUT.mkdir(exist_ok=True)
p=REPO/'docs/research/2026-09-08-source-closure-protocol.json'
spec={'protocol_id':'H19_H20_PRIMARY_SOURCE_CLOSURE_1',
 'registered_at_utc':datetime.now(timezone.utc).isoformat(),
 'base_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
 'user_request':'Resolve all remaining open issues, including missing sources; continue concrete work rather than stop at a gap list.',
 'scope':'Reconcile all required cash intervals and corporate actions against primary sources; immutable new source and execution versions only. Reuse existing source acquisitions before new public downloads.',
 'frozen_inputs':{'execution_manifest':'7edf2f20546e9dee910e4f2d1aa6a4a748efcc07dfd2b2a04b393f41a644b6e7','H20_signals':'13acee7062dddbf96c81356588f36806e758ea9e5c6c8f395e7891620b1f6a8f','H20_readiness':'d936cf6d6ef5f8780ebd23427c31fd21389f4796789e4e320bc062cff8e464e8'},
 'source_policy':'Match legal issuer/security, last-cum/ex date, action and amount; document version/receipt, payment vs deadline, installments, updated amounts, actual stock delivery and personal tax kept distinct. Hash original files; retain exact page/row evidence. Ambiguous candidates are not certifications.',
 'new_data':'An explicitly versioned dataset and additive review records outside all protected databases/ledgers/quarantines. No synthetic missing income or post-performance removal of difficult holdings.',
 'research_boundary':'No new strategy, parameter search or return evaluation during source reconstruction. Register a separate execution protocol with exact final source hashes before any new historical economic measurement. Preserve all prior observations.',
 'completion':'Resolve every achievable input/code issue using primary evidence and test the integrated execution. If an input cannot be determined, exhaust available primary paths and identify the exact irreducible field. Do not claim future performance evidence can be reconstructed from history.',
 'validation':'Primary-document positive/negative reconciliation fixtures; causal identity/date/amount/duplicate tests; source hashes and event/inventory conservation; accounting and package checks appropriate to changes.',
 'real_orders':False,'paid_data':False,'new_runtime_dependencies':[],'agents':False,
 'administrative_counts_before':[53,55]}
raw=(json.dumps(spec,indent=2,ensure_ascii=False)+'\n').encode('utf-8')
with p.open('xb') as f:f.write(raw)
attrs=REPO/'.gitattributes'
with attrs.open('a',encoding='utf-8',newline='\n') as f:f.write('\ndocs/research/2026-09-08-source-closure-protocol.json -text !eol\n')
print(hashlib.sha256(raw).hexdigest())
