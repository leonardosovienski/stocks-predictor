"""Verify the relocated research, commit receipts, and create a local Git bundle.

One-time continuation of preserve_stocks_session.py. No orders/database writes.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / 'work/stocks-predictor'
OUT = ROOT / 'outputs'
MAIN = Path(r'C:\Users\Superleo13\stocks-predictor-work')
DEST = MAIN / '.local-research/stocks-session-20260907'
CHECKOUT = DEST / 'work/stocks-predictor'
BASE = DEST / 'work/stocks-final-review-bundle'
BRANCH = 'fix/stocks-cvm-execution-20260907'
DOCS = REPO / 'docs/continuation'
ARCHIVE = REPO / 'research/session-20260907'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True, encoding='utf-8').strip()


manifest_path = OUT / 'STOCKS_PRESERVACAO_MANIFESTO.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
assert manifest['status'] == 'COPIED_AND_SHA256_VERIFIED'
assert sha(manifest_path) == sha(DEST / 'PRESERVACAO_MANIFESTO.json')
if '--seal' in sys.argv:
    receipt = json.loads((DOCS / 'PRESERVATION_VERIFIED.json').read_text(encoding='utf-8'))
    assert receipt['status'] == 'VERIFIED_INDEPENDENT_LOCAL_CONTINUATION'
    assert receipt['snapshot_manifest_sha256'] == sha(manifest_path)
    test_count = receipt['relocated_tests_passed']
    logs = [OUT / row['log'] for row in receipt['steps']]
    for row, log in zip(receipt['steps'], logs):
        assert sha(log) == row['log_sha256']
    assert sha(DEST / 'outputs/STOCKS_CONTINUIDADE_REPLAY.json') == receipt['replay_sha256']
    target = ARCHIVE / 'scripts' / Path(__file__).name
    shutil.copy2(Path(__file__), target)
    authored = json.loads((DOCS / 'AUTHORED_FILES.json').read_text(encoding='utf-8'))
    for row in authored:
        if row['git_path'] == target.relative_to(REPO).as_posix():
            row['bytes'], row['sha256'] = target.stat().st_size, sha(target)
        assert sha(REPO / row['git_path']) == row['sha256'], row['git_path']
    write(DOCS / 'AUTHORED_FILES.json', authored)
    git(REPO, 'add', str(target))
else:
    assert not git(REPO, 'status', '--porcelain')
    assert not git(CHECKOUT, 'status', '--porcelain')
    assert git(REPO, 'rev-parse', 'HEAD') == git(CHECKOUT, 'rev-parse', 'HEAD')

    validation = json.loads((OUT / 'STOCKS_REVISAO_FINAL_VALIDACAO.json').read_text(encoding='utf-8'))
    runtime = validation['validated_commit']
    assert not git(REPO, 'diff', runtime, 'HEAD', '--', 'stocks_predictor', 'tests', 'main.py', 'pyproject.toml')
    for name, digest in validation['source_module_hashes'].items():
        assert sha(CHECKOUT / 'stocks_predictor' / name) == digest
        assert sha(BASE / 'stocks_predictor' / name) == digest

    env = dict(os.environ, PYTHONPATH=str(DEST / 'work/checks'), PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1')
    env.pop('PYTEST_ADDOPTS', None)
    env.pop('PREDICTOR_DB_PATH', None)
    steps = []
    logs = []


    def run(name, args, expected=0):
        result = subprocess.run([sys.executable, '-B', '-X', 'utf8', *args], cwd=BASE,
                                env=env, capture_output=True, text=True, encoding='utf-8', errors='replace')
        log = OUT / ('STOCKS_CONTINUIDADE_' + name.upper() + '.log')
        log.write_text(result.stdout + result.stderr, encoding='utf-8')
        logs.append(log)
        steps.append({'step': name, 'cwd': str(BASE), 'exit_code': result.returncode,
                      'expected_exit_code': expected, 'log': log.name, 'log_sha256': sha(log)})
        print(json.dumps(steps[-1]), flush=True)
        assert result.returncode == expected, result.stdout[-4000:] + result.stderr[-2000:]
        return result.stdout


    imports = run('import', ['-c', 'import pathlib, stocks_predictor.continuous_research as m; '
        'p=pathlib.Path(m.__file__).resolve(); assert p.is_relative_to(pathlib.Path.cwd()); print(p)'])
    tests = run('tests', ['-m', 'pytest', 'tests', '-q', '-p', 'no:cacheprovider'])
    test_count = int(re.search(r'(\d+) passed', tests).group(1))
    assert test_count == 48
    replay_path = DEST / 'outputs/STOCKS_CONTINUIDADE_REPLAY.json'
    run('replay', ['-m', 'stocks_predictor.continuous_research', '--inputs', 'inputs', '--output', str(replay_path)], 2)
    replay = json.loads(replay_path.read_text(encoding='utf-8'))
    assert replay['status'] == 'BLOCKED_MISSING_EVIDENCE' and replay['profit'] is None
    assert replay['validated_quote_records'] == 365198 and replay['verified_input_files'] == 31
    assert replay['new_historical_return_evaluations'] == 0
    assert sha(replay_path) == sha(OUT / 'STOCKS_REVISAO_FINAL_EXECUCAO.json')
    shutil.copy2(replay_path, OUT / replay_path.name)

    db_hashes = {}
    for old_path, digest in validation['database_hashes'].items():
        old = Path(old_path)
        assert sha(old) == digest
        db_hashes[str(old)] = digest
        if old.is_relative_to(ROOT):
            relocated = DEST / old.relative_to(ROOT)
            assert sha(relocated) == digest
            db_hashes[str(relocated)] = digest

    for relative in ('docs/continuation/PROMPT_NOVO_CHAT.md', 'docs/continuation/SESSION_CONTEXT.md'):
        assert (REPO / relative).read_text(encoding='utf-8') == (CHECKOUT / relative).read_text(encoding='utf-8')
    assert (DOCS / 'PROMPT_NOVO_CHAT.md').read_text(encoding='utf-8') == (DEST / 'outputs/PROMPT_NOVO_CHAT_STOCKS.md').read_text(encoding='utf-8')

    # Git had already staged some historic CRLF files before the -text rule was added.
    # Renormalize that index once, preserving original archived bytes, never editing logs.
    attributes = REPO / '.gitattributes'
    attribute_text = attributes.read_text(encoding='utf-8')
    if 'docs/continuation/*.json -text' not in attribute_text:
        attributes.write_text(attribute_text + '\n# Receipts and manifests retain their recorded byte hashes.\ndocs/continuation/*.json -text !eol\n', encoding='utf-8')
    authored = json.loads((DOCS / 'AUTHORED_FILES.json').read_text(encoding='utf-8'))
    new_sources = [(Path(__file__), ARCHIVE / 'scripts' / Path(__file__).name)]
    new_sources += [(p, ARCHIVE / 'logs' / p.name) for p in logs]
    new_sources += [(OUT / replay_path.name, ARCHIVE / 'deliverables' / replay_path.name)]
    for source, target in new_sources:
        shutil.copy2(source, target)
        authored.append({'original_relative_path': source.relative_to(ROOT).as_posix(),
            'git_path': target.relative_to(REPO).as_posix(), 'bytes': target.stat().st_size, 'sha256': sha(target)})
    write(DOCS / 'AUTHORED_FILES.json', authored)
    git(REPO, 'add', 'research/session-20260907', 'docs/continuation/AUTHORED_FILES.json')
    git(REPO, 'add', '--renormalize', 'research/session-20260907', 'docs/continuation')
    batch = subprocess.Popen(['git', '-C', str(REPO), 'cat-file', '--batch'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    try:
        for row in authored:
            batch.stdin.write((':' + row['git_path'] + '\n').encode()); batch.stdin.flush()
            header = batch.stdout.readline().decode().split()
            assert header[1] == 'blob', header
            data = batch.stdout.read(int(header[2])); assert batch.stdout.read(1) == b'\n'
            assert hashlib.sha256(data).hexdigest() == row['sha256'], row['git_path']
    finally:
        batch.stdin.close()
        assert batch.wait() == 0
    original = subprocess.check_output(['git', '-C', str(REPO), 'show', ':docs/continuation/INITIAL_REQUEST.md'])
    paths = json.loads((DOCS / 'PATHS.json').read_text(encoding='utf-8'))
    assert hashlib.sha256(original).hexdigest() == paths['original_prompt_sha256']

    shutil.copy2(manifest_path, DOCS / 'PRESERVATION_MANIFEST.json')
    receipt = {'status': 'VERIFIED_INDEPENDENT_LOCAL_CONTINUATION', 'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'durable_root': str(DEST), 'durable_checkout': str(CHECKOUT), 'branch': BRANCH,
        'snapshot_commit': manifest['initial_preservation_commit'], 'validated_runtime_commit': runtime,
        'runtime_changes_since_592_test_validation': False,
        'copied_files': manifest['copied_files'], 'copied_bytes': manifest['copied_bytes'],
        'snapshot_manifest_sha256': sha(manifest_path), 'authored_files_exact_git_bytes_verified': len(authored),
        'relocated_tests_passed': test_count, 'independent_import_path': imports.strip(), 'steps': steps,
        'replay_sha256': sha(replay_path), 'replay_matches_prior_result': True,
        'replay_status': replay['status'], 'profit': None, 'new_historical_return_evaluations': 0,
        'database_hashes_preserved': db_hashes, 'github_push_performed': False,
        'scope': 'Local preservation outside the chat folder; not off-device backup or GitHub upload.',
        'preservation_commit': 'The Git commit containing this receipt; inspect git log -1 -- docs/continuation/PRESERVATION_VERIFIED.json'}
    write(DOCS / 'PRESERVATION_VERIFIED.json', receipt)
    summary = f'''# Continuidade Stocks preservada

    Código, contexto, prompt, scripts, relatórios e logs estão commitados na branch
    `{BRANCH}`. Os dados extensos estão fora dos objetos Git, com manifesto versionado.

    Pasta independente deste chat (mantenha esta pasta e o repositório que a contém):
    `{DEST}`

    Código atualizado: `{CHECKOUT}`

    - {manifest['copied_files']:,} arquivos copiados, {manifest['copied_bytes']/1e9:.3f} GB, comparados por SHA256.
    - {len(authored)} arquivos autorais têm os bytes do arquivo Git conferidos contra os originais.
    - 48 testes passaram na cópia independente; o replay conferiu 31 entradas e 365.198 cotações.
    - O replay foi idêntico ao anterior: código 2, BLOCKED_MISSING_EVIDENCE, lucro desconhecido.
    - Nenhuma alteração de runtime desde os 592 testes da revisão anterior; nenhuma nova avaliação histórica.
    - Commit e cópia são locais. Não foi feito push ao GitHub.

    O histórico da conversa pode ser apagado sem ser necessário à retomada. Os arquivos
    preservados precisam permanecer no computador. A cópia local não protege contra
    perda do disco. Nenhuma conversa foi apagada ou arquivada por esta operação.

    No novo chat, use o prompt completo de `outputs/PROMPT_NOVO_CHAT_STOCKS.md` desta
    pasta preservada, também versionado em `docs/continuation/PROMPT_NOVO_CHAT.md`.
    Leia SESSION_CONTEXT.md e PRESERVATION_VERIFIED.json para contexto e verificações.

    O pacote Git portátil STOCKS_CONTINUIDADE_GIT.bundle e seu recibo complementar
    ficam na pasta outputs preservada. Ele guarda código e documentos; os dados de
    13,5 GB dependem da pasta preservada e do manifesto, não estão dentro do bundle.
    '''
    (DOCS / 'PRESERVATION_VERIFIED.md').write_text(summary, encoding='utf-8')
    (OUT / 'STOCKS_CONTINUIDADE_CONFIRMADA.md').write_text(summary, encoding='utf-8')
    write(OUT / 'STOCKS_CONTINUIDADE_CONFIRMADA.json', receipt)
    bootstrap = f'Continue a pesquisa stocks-predictor. Leia e execute o prompt completo em:\n{CHECKOUT / "docs/continuation/PROMPT_NOVO_CHAT.md"}\n\nO contexto, recibo de preservação e caminhos estão no mesmo diretório docs/continuation. Use esse checkout e a raiz preservada; não é necessário recuperar o chat anterior.\n'
    (OUT / 'ABRIR_NOVO_CHAT_STOCKS.txt').write_text(bootstrap, encoding='utf-8')
    (DOCS / 'ABRIR_NOVO_CHAT.txt').write_text(bootstrap, encoding='utf-8')
git(REPO, 'add', '.gitattributes', 'docs/continuation')
git(REPO, '-c', 'core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol', 'diff', '--cached', '--check', '--', 'docs/continuation', ':(exclude)docs/continuation/INITIAL_REQUEST.md')
print(git(REPO, 'commit', '-m', 'Verify independent restoration and preserve exact evidence hashes'), flush=True)
commit = git(REPO, 'rev-parse', 'HEAD')
git(CHECKOUT, 'fetch', '--no-tags', str(REPO), BRANCH)
git(CHECKOUT, 'merge', '--ff-only', 'FETCH_HEAD')
assert git(CHECKOUT, 'rev-parse', 'HEAD') == commit
assert not git(CHECKOUT, 'status', '--porcelain') and not git(REPO, 'status', '--porcelain')
assert git(MAIN, 'branch', '--show-current') == manifest['main_checkout_original_branch']
assert git(MAIN, 'rev-parse', 'HEAD') == manifest['main_checkout_original_head']
assert git(MAIN, 'status', '--porcelain') == manifest['main_checkout_original_status']

# Copy supplementary receipts created after the initial immutable snapshot.
extras = [manifest_path, Path(__file__), *logs, OUT / 'STOCKS_CONTINUIDADE_CONFIRMADA.md',
          OUT / 'STOCKS_CONTINUIDADE_CONFIRMADA.json', OUT / 'ABRIR_NOVO_CHAT_STOCKS.txt']
for source in extras:
    target = DEST / source.relative_to(ROOT)
    shutil.copy2(source, target)
    assert sha(source) == sha(target)

bundle = OUT / 'STOCKS_CONTINUIDADE_GIT.bundle'
git(MAIN, 'bundle', 'create', str(bundle), 'refs/heads/' + BRANCH)
git(MAIN, 'bundle', 'verify', str(bundle))
shutil.copy2(bundle, DEST / 'outputs' / bundle.name)
assert sha(bundle) == sha(DEST / 'outputs' / bundle.name)
restored = DEST / 'work/git-bundle-restore-check'
assert not restored.exists()
subprocess.run(['git', 'clone', '--no-checkout', '--branch', BRANCH, str(bundle), str(restored)], check=True)
assert git(restored, 'rev-parse', 'HEAD') == commit
git(restored, 'fsck', '--full')
final = {'status': 'COMPLETE', 'final_commit': commit, 'branch': BRANCH,
    'durable_root': str(DEST), 'durable_checkout': str(CHECKOUT),
    'copied_files': manifest['copied_files'], 'copied_bytes': manifest['copied_bytes'],
    'git_bundle_file': bundle.name, 'git_bundle_sha256': sha(bundle), 'git_bundle_bytes': bundle.stat().st_size,
    'bundle_independent_clone_and_fsck': 'PASSED', 'relocated_tests_passed': test_count,
    'main_checkout_unchanged': True, 'research_checkouts_clean': True, 'github_push_performed': False,
    'snapshot_manifest_sha256': sha(manifest_path), 'receipt_sha256': sha(OUT / 'STOCKS_CONTINUIDADE_CONFIRMADA.json')}
write(OUT / 'STOCKS_CONTINUIDADE_GIT_RECIBO.json', final)
shutil.copy2(OUT / 'STOCKS_CONTINUIDADE_GIT_RECIBO.json', DEST / 'outputs/STOCKS_CONTINUIDADE_GIT_RECIBO.json')
print(json.dumps(final, ensure_ascii=False), flush=True)
