"""Run after the exact merged main commit and its CI have passed."""
import argparse
import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path

repo=Path(r'C:\STOCKS\stocks-predictor')
root=Path(r'C:\STOCKS\work\h21-source-closure-20260909')
outputs=Path(r'C:\STOCKS\outputs')

def git(*args):
    return subprocess.check_output(['git',*args],cwd=repo,text=True,encoding='utf-8').strip()

def sha(path):
    with path.open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()

def write(path,obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

parser=argparse.ArgumentParser()
parser.add_argument('merged_sha')
args=parser.parse_args()
head=args.merged_sha
assert git('rev-parse','HEAD')==head==git('rev-parse','origin/main')
assert git('branch','--show-current')=='main' and not git('status','--porcelain')
assert git('rev-list','--count','main..research/h21-source-closure-20260909')=='0' if 'research/h21-source-closure-20260909' in git('branch','--format=%(refname:short)').splitlines() else True
now=dt.datetime.now(dt.timezone.utc).isoformat()
ci=json.loads((root/'ci-main.json').read_text(encoding='utf-8-sig'))
jobs=json.loads((root/'ci-main-jobs.json').read_text(encoding='utf-8-sig'))
assert ci['head_sha']==head and ci['event']=='push' and ci['conclusion']=='success'
assert len(jobs['jobs'])==2 and all(j['conclusion']=='success' for j in jobs['jobs'])
profile=json.loads((repo/'docs/research/2026-09-09-h21-operational-inputs.json').read_text(encoding='utf-8'))
protection=json.loads((root/'original-deliveries-preservation.json').read_text(encoding='utf-8-sig'))
assert all(sha(Path(p['path']))==p['sha256'] for p in protection)
newfiles=['docs/research/2026-09-09-h21-source-closure.md','docs/research/2026-09-09-h21-operational-inputs.json','docs/research/2026-09-09-h21-source-inventory.json','docs/research/2026-09-09-h21-source-closure-protocol.json','research/session-20260909/source_closure/reconcile_quotes.py']
files={}
for name in newfiles:
    committed=subprocess.check_output(['git','show',head+':'+name],cwd=repo)
    files[name]=dict(local_sha256=sha(repo/name),committed_bytes_sha256=hashlib.sha256(committed).hexdigest(),git_blob=git('rev-parse',head+':'+name))
report_url='https://github.com/leonardosovienski/stocks-predictor/blob/'+head+'/docs/research/2026-09-09-h21-source-closure.md'
receipt=dict(kind='SOURCE_REVIEW_DELIVERY_NOT_ECONOMIC_APPROVAL',delivered_at_utc=now,
    root=r'C:\STOCKS',branch='main',commit=head,git_working_tree_clean=True,
    pr_url='https://github.com/leonardosovienski/stocks-predictor/pull/71',report_url=report_url,
    report_local_path=str(repo/'docs/research/2026-09-09-h21-source-closure.md'),
    reviewed_head='1bb3d23ffcb8cbdf1c9ef60215889dc3d745d9ff',
    ci=dict(run_id=ci['id'],run_number=ci['run_number'],url=ci['html_url'],head_sha=head,conclusion='success',
            jobs=[dict(name=j['name'],conclusion=j['conclusion'],steps=[dict(name=s['name'],conclusion=s['conclusion']) for s in j['steps']]) for j in jobs['jobs']],
            scope='Canonical Linux CI; research helper independently validated locally.',
            verified_summary=json.loads((root/'ci-main-summary.json').read_text(encoding='utf-8')),
            quality_log_sha256=sha(root/'ci-main-quality.log')),
    local_validation=json.loads((root/'precommit-validation.json').read_text(encoding='utf-8')),
    source_reconciliation=json.loads((root/'normalized-v2/reconciliation.json').read_text(encoding='utf-8')),
    raw_sources=str(root/'raw'),original_deliveries_unchanged=protection,
    files=files,local_vs_committed_hash_policy='Git normalizes text line endings; distinct hashes retained. Original registered protocol bytes separately preserved in work.',
    registered_protocol_original_path=str(root/'protocol-registered.original.json'),registered_protocol_original_sha256=sha(root/'protocol-registered.original.json'),
    personal_profile=profile['personal_profile'],remaining_gaps=profile['events']['unresolved']+profile['execution_unknowns'],
    events_certified=False,full_net_cost_certified=False,expected_future_profit=None,
    new_economic_valuations=0,new_orders=0,recurring_jobs_started=0,
    migration_archive=dict(path=r'C:\STOCKS\DADOS_STOCKS.zip',bytes=Path(r'C:\STOCKS\DADOS_STOCKS.zip').stat().st_size,hash_recomputed_this_round=False,not_written_this_round=True),
    centralization=dict(previous_task_directory_files=0,reparse_points_under_root=0,all_new_authored_project_files_within_root=True,
                        scope='Rechecked original task directory and root reparse points; prior external folder scan remains dated in location map. App/runtime caches and authorized GitHub remain external environment resources.'),
    budgets=dict(data_closed_at_utc='2026-09-09T20:11:20.380794+00:00',delivery_deadline_utc='2026-09-09T20:50:00Z',
                 delivered_before_deadline=now<'2026-09-09T20:50:00',direct_acquisition_attempts=77,request_counter_excludes_browser_search_redirects=True,
                 retained_transport_bytes=82716664,normalization_revisions=2))
target=outputs/'ENTREGA_FONTES_H21_20260909.json'
assert not target.exists()
write(target,receipt)
map_path=Path(r'C:\STOCKS\LOCALIZACAO_PROJETO.json')
mapping=json.loads(map_path.read_text(encoding='utf-8-sig'))
mapping.update(code_commit=head,local_branch='main',git_working_tree_clean=True,git_worktrees=git('worktree','list','--porcelain').splitlines(),
               current_code_state_verified_at_utc=now,source_review_report=report_url,source_review_receipt=str(target),source_review_work=str(root))
write(map_path,mapping)
print(json.dumps(dict(receipt=str(target),report_url=report_url,ci=ci['html_url'],main=head,delivered_at_utc=now),ensure_ascii=False))
