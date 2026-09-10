import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(r'C:\STOCKS')
REPO = ROOT/'stocks-predictor'
WORK = ROOT/'work/data-completion-r2-20260909'

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def git(*args):
    return subprocess.check_output(['git', *args], cwd=REPO, text=True, encoding='utf-8').strip()

protected = {
    ROOT/'DADOS_STOCKS.zip': '83d5aac8e23d72e4deb1331077e08313914375a5dbac4276e5f8ad89da586d23',
    ROOT/'work/h21/result-01.json': '39a940514b5fdcbb577c496f996ddd324c8107436852ab67da352401bb8870d2',
    ROOT/'work/h21/inputs/quotes.json': '445a24c3098deb3da6f3bdd7b3d92ca48e24e6b4f9fdc38fb52b7705c2467d94',
    ROOT/'work/h21/inputs/BOVA11.original-lines.txt': '95a0f8c69954911c7c8e332af846b830989ccbe3d2f7e6ed1bdff014213e6eb3',
    REPO/'docs/research/2026-09-09-h21-protocol.json': '5721d7405af2f398448be3966eeb832deda06f7aa936e5244059ae7ca86797fb',
    REPO/'docs/continuation/MANDATO_20260909.md': 'd63db21471620a6a4a83671e1acebda1d7ff0be04a96652d5f0d658997cc73cc',
    ROOT/'work/h21-source-closure-20260909/normalized-v2/quotes-2018-20260908.json': '813a21aa335a84fb4288f125613dd3aab40b30d1c32a53e4e96c065431bc7adb',
}
for move in read(ROOT/'work/centralizacao-20260909/movimentacoes.json')['moves']:
    protected[Path(move['destination'])] = move['sha256']
    assert not Path(move['source']).exists(), move['source']
for path, expected in protected.items():
    assert sha(path) == expected, str(path)

snapshots = {'bova-event-review.json': '2026-09-09-bova-event-review-r2.json',
             'operational-inputs.json': '2026-09-09-operational-inputs-r2.json',
             'readiness.json': '2026-09-09-data-readiness.json',
             'source-inventory.json': '2026-09-09-source-inventory-r2.json'}
hashes = read(WORK/'normalized-v1/SHA256.json')
for source, dest in snapshots.items():
    assert sha(WORK/'normalized-v1'/source) == hashes[source]
    assert sha(REPO/'docs/research'/dest) == hashes[source]
    read(REPO/'docs/research'/dest)
assert sha(ROOT/'data/CATALOG.json') == hashes['readiness.json']
ready = read(ROOT/'data/CATALOG.json')
assert ready['all_data_ready'] is False
assert len(ready['databases']) == 12
assert all(d['integrity_status'] == 'PASS' and Path(d['path']).exists() for d in ready['databases'])
events = read(WORK/'normalized-v1/bova-event-review.json')
assert events['full_event_interval_certified'] is False
assert events['cash_event_records_for_economic_use'] is None
assert events['unit_event_records_for_economic_use'] is None
inputs = read(WORK/'normalized-v1/operational-inputs.json')
assert inputs['ready_for_full_net_backtest'] is False
assert ready['acquisition_summary']['jobs'] == 121
assert ready['sources13_14']['revision14_missing_net_payment_values'] == 52

files = [REPO/name for name in ['AGENTS.md','README.md','HANDOFF.md','STOCKS_CURRENT_STATE.md',
    'docs/DOCUMENTATION_INDEX.md','docs/continuation/PROMPT_NOVO_CHAT.md',
    'docs/continuation/MIGRACAO_MAIN.md','docs/continuation/SESSION_CONTEXT.md',
    'docs/research/2026-09-09-data-completion-r2.md','research/session-20260909/data_completion/README.md']]
files += [ROOT/'AGENTS.md', ROOT/'COMECE_AQUI.md', ROOT/'data/README.md']
links = []
for path in files:
    body = path.read_text(encoding='utf-8').split('\n---\n', 1)[0]
    if path == REPO/'README.md':
        body = body.split('## Linha histórica:', 1)[0]
    for target in re.findall(r'\]\(([^)]+)\)', body):
        if target.startswith(('https://','http://','#')):
            continue
        resolved = (path.parent/target.split('#',1)[0]).resolve()
        assert resolved.is_relative_to(ROOT) and resolved.exists(), (str(path), target)
        links.append({'file': str(path), 'target': str(resolved)})

links_outside = []
all_files = []
for path in ROOT.rglob('*'):
    if path.is_symlink() or path.is_junction():
        links_outside.append(str(path))
    if path.is_file():
        all_files.append(path)
assert not links_outside, links_outside
prior = Path(r'C:\Users\leona\Documents\Codex\2026-09-09\crie-uma-imagem-de-2')
assert not list(p for p in prior.rglob('*') if p.is_file())
assert not (REPO/'.git/objects/info/alternates').exists()
result = {'verified_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
          'status': 'PASS', 'protected_files': {str(p): s for p,s in protected.items()},
          'snapshots_match_local_and_repository_bytes': hashes,
          'active_markdown_files_checked': len(files), 'active_local_links_checked': len(links),
          'active_local_links': links, 'files_under_root': len(all_files),
          'bytes_under_root': sum(p.stat().st_size for p in all_files),
          'reparse_points': [], 'prior_codex_directory_files': 0,
          'external_user_folder_full_scan_repeated': False,
          'previous_full_scan_reference': str(ROOT/'LOCALIZACAO_PROJETO.json'),
          'git_head_at_verification': git('rev-parse', 'HEAD'),
          'new_economic_valuations': 0}
out = WORK/'readiness-verification.json'
with out.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('protected_files','active_local_links','snapshots_match_local_and_repository_bytes')}))
