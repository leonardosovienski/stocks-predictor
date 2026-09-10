"""Finalize local delivery only after exact-commit CI and reviewed Git integration."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(r'C:\STOCKS')
REPO = ROOT/'stocks-predictor'
WORK = ROOT/'work/data-completion-r2-20260909'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def git(*args):
    return subprocess.check_output(['git', *args], cwd=REPO, text=True, encoding='utf-8').strip()

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def write(path, value, mode='x'):
    with path.open(mode, encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

parser = argparse.ArgumentParser()
parser.add_argument('merge_sha')
parser.add_argument('reviewed_head')
args = parser.parse_args()
assert git('branch', '--show-current') == 'main'
assert git('rev-parse','HEAD') == args.merge_sha == git('rev-parse','origin/main')
assert git('rev-parse', args.merge_sha+'^{tree}') == git('rev-parse', args.reviewed_head+'^{tree}')
assert git('status','--porcelain') == ''
assert len(git('worktree','list','--porcelain').split('worktree ')) == 2
assert 'data/complete-sources-r2-20260909' not in git('branch','--all')
pr = read(WORK/'ci-pr-final.json')
main = read(WORK/'ci-main-final.json')
for state, expected, event in ((pr,args.reviewed_head,'pull_request'),(main,args.merge_sha,'push')):
    assert state['run']['head_sha'] == expected
    assert state['run']['event'] == event
    assert state['run']['status'] == 'completed' and state['run']['conclusion'] == 'success'
    jobs = state['jobs']['jobs']
    assert len(jobs) == 2 and all(j['conclusion'] == 'success' for j in jobs)
    quality = next(j for j in jobs if j['name'] == 'Quality / Python 3.13')
    for name in ('Ruff','Pyright','Tests','Build wheel','Wheel smoke outside checkout'):
        assert next(s for s in quality['steps'] if s['name']==name)['conclusion']=='success'
log = (WORK/'ci-main-quality.log').read_text(encoding='utf-8')
assert '791 passed' in log
assert '78%' in log
assert 'CPython (3.13.15)' in log and 'predictor-core==3.2.0' in log

verification = read(WORK/'readiness-verification.json')
ready = read(ROOT/'data/CATALOG.json')
hashes = read(WORK/'normalized-v1/SHA256.json')
snapshots = {'bova-event-review.json':'2026-09-09-bova-event-review-r2.json',
             'operational-inputs.json':'2026-09-09-operational-inputs-r2.json',
             'readiness.json':'2026-09-09-data-readiness.json',
             'source-inventory.json':'2026-09-09-source-inventory-r2.json'}
for source,dest in snapshots.items():
    local = REPO/'docs/research'/dest
    blob = subprocess.check_output(['git','show',args.merge_sha+':docs/research/'+dest],cwd=REPO)
    assert sha(local) == hashes[source] == hashlib.sha256(blob).hexdigest()
assert sha(ROOT/'data/CATALOG.json') == hashes['readiness.json']
for path, expected in verification['protected_files'].items():
    p = Path(path)
    if p.stat().st_size < 1_000_000_000:
        assert sha(p) == expected

prior = Path(r'C:\Users\leona\Documents\Codex\2026-09-09\crie-uma-imagem-de-2')
assert not [p for p in prior.rglob('*') if p.is_file()]
assert not [p for p in ROOT.rglob('*') if p.is_symlink() or p.is_junction()]
now = dt.datetime.now(dt.timezone.utc).isoformat()
url = 'https://github.com/leonardosovienski/stocks-predictor'
report = url+'/blob/'+args.merge_sha+'/docs/research/2026-09-09-data-completion-r2.md'
registry = read(ROOT/'LOCALIZACAO_PROJETO.json')
registry.update(code_commit=args.merge_sha, git_working_tree_clean=True,
                git_worktrees=git('worktree','list','--porcelain').splitlines(),
                current_code_state_verified_at_utc=now,
                data_state_updated_at_utc=now, source_review_r2_report=report,
                current_root_file_verification=verification['verified_at_utc'])
write(ROOT/'LOCALIZACAO_PROJETO.json',registry,'w')

artifact_paths = [WORK/'acquisition.jsonl',WORK/'normalize_readiness.py',WORK/'acquire.py',
    WORK/'normalized-v1/SHA256.json',WORK/'reproduced-source-audits.json',
    WORK/'readiness-verification.json',WORK/'ci-pr-final.json',WORK/'ci-pr-quality.log',WORK/'ci-main-final.json',
    WORK/'ci-main-quality.log',ROOT/'data/CATALOG.json',ROOT/'data/recovery-r2/catalog.json',
    ROOT/'LOCALIZACAO_PROJETO.json',ROOT/'data/README.md',ROOT/'COMECE_AQUI.md',
    REPO/'docs/research/2026-09-09-data-completion-r2.md']
result = {'schema_version':1,'delivered_at_utc':now,'round':'DATA_COMPLETION_20260909_R2',
          'round_completed_with_explicit_remaining_dependencies':True,
          'all_project_data_economically_ready':False,
          'local_root':str(ROOT),'checkout':str(REPO),'branch':'main','git_clean':True,
          'single_worktree':True,'temporary_branch_removed':True,
          'base_sha':'c45c6e1aba148190ee1bd99da87f7a719af3b1b0',
          'reviewed_head_sha':args.reviewed_head,'merge_sha':args.merge_sha,
          'merge_tree_equals_reviewed_tree':True,'pull_request':url+'/pull/72',
          'report':report,'pr_ci':pr['run']['html_url'],'main_ci':main['run']['html_url'],
          'main_ci_tests':791,'coverage_percent':78,'archived_tests_not_run':17,
          'local_auxiliary_tests':9,'local_auxiliary_python':'3.12.14',
          'production_validation':'Linux GitHub CI, Python 3.13.15/Core 3.2.0',
          'databases':{'unique':12,'original_path_aliases':37,'integrity_pass':12,
                       'sources13_14_separate':True,'activated_for_production':False},
          'public_acquisitions':ready['acquisition_summary'],
          'data_normalization_revisions':{'source14_composition':1,'events_and_costs':1},
          'new_economic_variants':0,'new_economic_valuations':0,
          'h21_original_preserved':True,'source_round_r1_preserved':True,
          'all_new_authored_local_files_inside_root':True,'prior_codex_directory_files':0,
          'no_reparse_points_in_project':True,
          'full_external_folder_scan_repeated':False,
          'full_external_scan_reference':'LOCALIZACAO_PROJETO.json verified_at_utc (original dated scan)',
          'orders_broker_authentication_paid_services_or_recurring_jobs':False,
          'remaining':ready['remaining_external_or_research_dependencies'],
          'broad_source14_gaps':ready['sources13_14'],
          'user_profile_pending':'XP preferred; channel/adviser status, capital, horizon and loss tolerance unknown',
          'artifacts':{str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in artifact_paths}}
path = ROOT/'outputs/ENTREGA_DADOS_FONTES_R2_20260909.json'
write(path,result)
print(json.dumps({'status':'DELIVERED','path':str(path),'sha256':sha(path),
                  'merge_sha':args.merge_sha,'tests':791,'all_data_ready':False}))
