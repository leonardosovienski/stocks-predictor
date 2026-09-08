"""Preserve research outside its chat directory; no orders or database writes.

This script records authored text in Git, copies extensive evidence separately,
and compares source/destination SHA256. It never deletes a source or changes the
main checkout. Run only for this explicitly requested preservation operation.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / 'work/stocks-predictor'
MAIN = Path(r'C:\Users\Superleo13\stocks-predictor-work')
DEST = MAIN / '.local-research/stocks-session-20260907'
CHECKOUT = DEST / 'work/stocks-predictor'
BRANCH = 'fix/stocks-cvm-execution-20260907'
CONTEXT = REPO / 'docs/continuation'
ARCHIVE = REPO / 'research/session-20260907'
EXCLUDED_DIRS = {'.git', '__pycache__', '.pytest_cache'}


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True, encoding='utf-8').strip()


assert ROOT != DEST and not DEST.is_relative_to(ROOT) and not ROOT.is_relative_to(DEST)
assert not DEST.exists(), 'Destination already exists: inspect it, do not overwrite'
assert git(REPO, 'branch', '--show-current') == BRANCH
assert git(MAIN, 'remote', 'get-url', 'origin') == git(REPO, 'remote', 'get-url', 'origin')
main_status = git(MAIN, 'status', '--porcelain')
main_branch = git(MAIN, 'branch', '--show-current')
main_head = git(MAIN, 'rev-parse', 'HEAD')
if subprocess.run(['git', '-C', str(MAIN), 'show-ref', '--verify', '--quiet', 'refs/heads/' + BRANCH]).returncode == 0:
    raise ValueError('Destination branch already exists; no overwrite is allowed')

CONTEXT.mkdir(parents=True, exist_ok=True)
original = Path(r'C:\Users\Superleo13\.codex\attachments\9563025a-61a3-4fd4-a422-ce159e917b1e\pasted-text.txt')
shutil.copy2(original, CONTEXT / 'INITIAL_REQUEST.md')
paths = {'original_research_root': str(ROOT), 'durable_research_root': str(DEST),
    'durable_checkout': str(CHECKOUT), 'main_git_repository': str(MAIN), 'research_branch': BRANCH,
    'original_prompt_sha256': sha(original),
    'relocation': 'Resolve original root prefixes to durable_research_root without modifying evidence bytes.',
    'large_data_policy': 'Raw downloads, databases and ZIPs are copied and hashed outside Git object storage.',
    'local_git_only': True, 'github_push_performed': False,
    'external_database': str(MAIN / 'data/stocks.db')}
write(CONTEXT / 'PATHS.json', paths)
shutil.copy2(CONTEXT / 'PROMPT_NOVO_CHAT.md', ROOT / 'outputs/PROMPT_NOVO_CHAT_STOCKS.md')

authored = []
for folder, target, extensions in [
        (ROOT / 'work', ARCHIVE / 'scripts', {'.py', '.ps1', '.md'}),
        (ROOT / 'outputs', ARCHIVE / 'deliverables', {'.json', '.jsonl', '.md', '.txt', '.py', '.ps1', '.csv', '.yaml', '.yml'}),
        (ROOT / 'work', ARCHIVE / 'logs', {'.log'})]:
    target.mkdir(parents=True, exist_ok=True)
    for source in sorted(folder.iterdir()):
        if not source.is_file() or source.suffix.lower() not in extensions:
            continue
        if source.stat().st_size > 50_000_000:
            raise ValueError('Review unusually large authored file before adding to Git: ' + str(source))
        dest = target / source.name
        shutil.copy2(source, dest)
        authored.append({'original_relative_path': source.relative_to(ROOT).as_posix(),
            'git_path': dest.relative_to(REPO).as_posix(), 'bytes': dest.stat().st_size, 'sha256': sha(dest)})
write(CONTEXT / 'AUTHORED_FILES.json', authored)
(ARCHIVE / 'README.md').write_text('''# Arquivo da sessão 06–07/09/2026

Scripts autorais, entregas textuais e logs preservados para continuidade.
São documentos históricos: nem todos os scripts são seguros para reexecutar
automaticamente. Alguns criam bancos isolados ou sobrescrevem saídas antigas.
Use docs/continuation/SESSION_CONTEXT.md e o prompt revisado como ponto de partida.
Dados extensos, PDFs, ZIPs e bancos ficam na cópia externa registrada em PATHS.json
e no manifesto de preservação; não foram transformados em blobs Git gigantes.
''', encoding='utf-8')
handoff = REPO / 'HANDOFF.md'
prefix = '''## Continuidade sem depender deste chat (2026-09-07)

Usuário pediu commitar todo o trabalho, conferir o prompt e permitir apagar a
conversa. Prompt e contexto estão em docs/continuation; scripts/entregas/logs
autorais externos foram incorporados em research/session-20260907. Dados extensos
são preservados com SHA256 na raiz durável de PATHS.json, fora da pasta do chat.
A conclusão econômica permanece NO_GO/inconclusiva; não houve novo experimento.
Ver o recibo de preservação para o resultado da cópia e retomada independente.

'''
handoff_text = handoff.read_text(encoding='utf-8')
if not handoff_text.startswith(prefix):
    handoff.write_text(prefix + handoff_text, encoding='utf-8')
git(REPO, 'add', '.gitattributes', 'docs/continuation', 'research/session-20260907', 'HANDOFF.md')
# Preserve historical logs byte-for-byte, including original whitespace.
git(REPO, 'diff', '--cached', '--check', '--', '.',
    ':(exclude)research/session-20260907', ':(exclude)docs/continuation/INITIAL_REQUEST.md')
print(git(REPO, 'commit', '-m', 'Preserve complete session context, research scripts and evidence reports'), flush=True)
commit = git(REPO, 'rev-parse', 'HEAD')
assert not git(REPO, 'status', '--porcelain')

# These user-created worktrees live outside the Codex-owned chat directory.
exclude = MAIN / '.git/info/exclude'
old_exclude = exclude.read_text(encoding='utf-8') if exclude.exists() else ''
if '/.local-research/' not in old_exclude.splitlines():
    exclude.parent.mkdir(parents=True, exist_ok=True)
    exclude.write_text(old_exclude.rstrip('\n') + '\n/.local-research/\n', encoding='utf-8')
git(MAIN, 'fetch', '--no-tags', str(REPO), f'refs/heads/{BRANCH}:refs/heads/{BRANCH}')
git(MAIN, 'worktree', 'add', str(CHECKOUT), BRANCH)
git(MAIN, 'worktree', 'lock', '--reason', 'Preserved Stocks research independent of deleted chat', str(CHECKOUT))
tracked = set(git(REPO, 'ls-files').splitlines())

files = []
skipped = []
for folder, dirs, names in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS and not (Path(folder)/d).is_symlink()
               and not (Path(folder)/d).is_junction()]
    for name in names:
        source = Path(folder) / name
        relative = source.relative_to(ROOT)
        if source.is_symlink() or source.is_junction():
            skipped.append({'path': relative.as_posix(), 'reason': 'link'})
            continue
        if relative.parts[:2] == ('work', 'stocks-predictor'):
            if relative.relative_to('work/stocks-predictor').as_posix() in tracked:
                continue  # Already preserved by the exact Git commit/worktree.
        files.append((source, relative, source.stat().st_size))
total = sum(size for _, _, size in files)
assert shutil.disk_usage(DEST).free > total * 1.1 + 1_000_000_000
manifest = []
began = last_progress = time.monotonic()
copied_bytes = 0
for i, (source, relative, size) in enumerate(files, 1):
    dest = (DEST / relative).resolve()
    assert dest.is_relative_to(DEST.resolve()) and dest != DEST.resolve()
    if dest.exists():
        raise ValueError('Unexpected pre-existing destination: ' + str(dest))
    stat = source.stat()
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    source_sha = sha(source)
    assert sha(dest) == source_sha, relative
    assert (stat.st_size, stat.st_mtime_ns) == (source.stat().st_size, source.stat().st_mtime_ns), relative
    manifest.append({'path': relative.as_posix(), 'bytes': size, 'sha256': source_sha})
    copied_bytes += size
    if time.monotonic() - last_progress >= 20:
        print(json.dumps({'copied_and_verified': i, 'total_files': len(files),
            'gigabytes': round(copied_bytes/1e9, 3), 'total_gigabytes': round(total/1e9, 3)}), flush=True)
        last_progress = time.monotonic()

result = {'status': 'COPIED_AND_SHA256_VERIFIED', 'created_at_utc': datetime.now(timezone.utc).isoformat(),
    'source_root': str(ROOT), 'preserved_root': str(DEST), 'durable_checkout': str(CHECKOUT),
    'research_branch': BRANCH, 'initial_preservation_commit': commit,
    'copied_files': len(manifest), 'copied_bytes': copied_bytes, 'files': manifest,
    'tracked_project_files_preserved_in_git': len(tracked),
    'excluded_regenerable_directories': sorted(EXCLUDED_DIRS), 'skipped_links': skipped,
    'elapsed_seconds': round(time.monotonic()-began, 2),
    'main_checkout_original_branch': main_branch, 'main_checkout_original_head': main_head,
    'main_checkout_original_status': main_status, 'github_push_performed': False}
write(DEST / 'PRESERVACAO_MANIFESTO.json', result)
write(ROOT / 'outputs/STOCKS_PRESERVACAO_MANIFESTO.json', result)
assert git(MAIN, 'branch', '--show-current') == main_branch
assert git(MAIN, 'rev-parse', 'HEAD') == main_head
assert git(MAIN, 'status', '--porcelain') == main_status
assert git(CHECKOUT, 'rev-parse', 'HEAD') == commit
assert not git(CHECKOUT, 'status', '--porcelain')
print(json.dumps({k:v for k,v in result.items() if k != 'files'}, ensure_ascii=False), flush=True)
