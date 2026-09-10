import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path

repo=Path(r'C:\STOCKS\stocks-predictor')
root=Path(r'C:\STOCKS\work\h21-source-closure-20260909')
protected={
    repo/'docs/research/2026-09-09-h21-protocol.json':'5721d7405af2f398448be3966eeb832deda06f7aa936e5244059ae7ca86797fb',
    repo/'docs/research/2026-09-09-h21-source-closure-protocol.json':'6ec703ba840d9badd2e20514d36fe2f63ccedf92a0a7d52cf597bcaae57fb4ef',
    repo/'docs/continuation/MANDATO_20260909.md':'d63db21471620a6a4a83671e1acebda1d7ff0be04a96652d5f0d658997cc73cc',
    Path(r'C:\STOCKS\instructions\STOCKS_PREDICTOR_PROMPT_FINAL_20260909.md'):'d63db21471620a6a4a83671e1acebda1d7ff0be04a96652d5f0d658997cc73cc',
    Path(r'C:\STOCKS\work\h21\result-01.json'):'39a940514b5fdcbb577c496f996ddd324c8107436852ab67da352401bb8870d2',
    Path(r'C:\STOCKS\work\h21\inputs\quotes.json'):'445a24c3098deb3da6f3bdd7b3d92ca48e24e6b4f9fdc38fb52b7705c2467d94'}
hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
assert all(hashes[str(p)]==sha for p,sha in protected.items())
mdpaths=['AGENTS.md','README.md','HANDOFF.md','STOCKS_CURRENT_STATE.md','docs/DOCUMENTATION_INDEX.md','docs/continuation/PROMPT_NOVO_CHAT.md','docs/research/2026-09-09-h21-source-closure.md','research/session-20260909/source_closure/README.md']
checked=[]
for name in mdpaths:
    p=repo/name
    body=p.read_text(encoding='utf-8').split('\n---\n')[0] if name in ['HANDOFF.md','STOCKS_CURRENT_STATE.md'] else p.read_text(encoding='utf-8')
    for url in re.findall(r'(?<!!)\[[^\]]+\]\(([^)]+)\)',body):
        if ':' in url or url.startswith('#'): continue
        target=(p.parent/url.split('#')[0]).resolve()
        assert target.exists(), (name,url)
        checked.append([name,url])
for p in (repo/'docs/research').glob('2026-09-09-h21-*.json'):
    json.loads(p.read_text(encoding='utf-8'))
ast.parse((repo/'research/session-20260909/source_closure/reconcile_quotes.py').read_text(encoding='utf-8'))
local=json.loads((root/'local-validation.json').read_text(encoding='utf-8'))
assert len(local['checks'])==4 and all(c['result'].startswith('PASS') for c in local['checks'])
profile=json.loads((repo/'docs/research/2026-09-09-h21-operational-inputs.json').read_text(encoding='utf-8'))
assert profile['expected_future_profit'] is None and profile['events']['cash_events'] is None
assert not profile['ready_for_full_net_backtest'] and profile['personal_profile']['actual_capital_brl'] is None
process=subprocess.run(['git','diff','--check'],cwd=repo,text=True,capture_output=True,check=True)
receipt=dict(protected_hashes=hashes, markdown_files_checked=mdpaths, valid_local_links=len(checked),
             local_source_checks=local, operational_profile_unknowns_preserved=True, json_and_python_syntax='PASS', git_diff_check='PASS')
(root/'precommit-validation.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(protected_hashes_pass=len(hashes), valid_local_links=len(checked), source_checks=len(local['checks']))))
