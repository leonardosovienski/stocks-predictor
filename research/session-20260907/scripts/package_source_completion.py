"""Package the already verified revision. Never edits or commits repository files."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT / 'work/stocks-predictor'
OUT = ROOT / 'outputs'

def git(*args):
    return subprocess.check_output(['git', *args], cwd=REPO)

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

tests = (OUT / 'historical-tests-full.txt').read_text(encoding='utf-8-sig')
matched = re.search(r'(\d+) passed in ([0-9.]+)s', tests)
if not matched or 'FAILED ' in tests:
    raise ValueError('Full tests must pass before packaging')
if git('status', '--porcelain').strip():
    raise ValueError('Package requires clean checkout')
commit = git('rev-parse', 'HEAD').decode().strip()
table_integrity = json.loads((OUT / 'historical-table-integrity.json').read_text(encoding='utf-8'))
protected = json.loads((OUT / 'historical-protected-integrity.json').read_text(encoding='utf-8'))
assert table_integrity['all_historical_tables_unchanged'] and protected['all_protected_inputs_unchanged']

database = ROOT / 'work/stocks-history-2016-2026.db'
with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True) as conn:
    counts = dict(conn.execute('SELECT kind,COUNT(*) FROM research_source_documents GROUP BY kind'))
    assert conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    assert conn.execute('SELECT COUNT(*) FROM cash_events').fetchone()[0] == 95
    assert conn.execute('SELECT COUNT(*) FROM cash_event_coverage').fetchone()[0] == 4

doc = (REPO / 'docs/research/2026-09-07-source-completion.md').read_text(encoding='utf-8')
doc += f'''

## Validação final desta entrega

- {matched[1]} testes passaram em {matched[2]} segundos com coverage e Core 3.2.0.
- Commit testado: `{commit}`. Checkout limpo; nenhum push.
- Ruff aprovado, Pyright aprovado no escopo configurado pelo projeto (módulos RJ).
- Wheel construída e importada fora do checkout, incluindo os novos parsers.
- Todas as tabelas históricas e entradas protegidas preservadas por hash/conteúdo.
- O banco entregue contém 30.835 observações de auditoria, além de 95 recebíveis
  reconciliados e quatro intervalos de caixa. Os 4.177 documentos financeiros
  estão por emissor na área de auditoria; não foram projetados retroativamente
  para tickers sem vínculo histórico certificado.

O usuário não precisa baixar arquivos nem executar comandos para obter esta entrega.
O pacote não libera os testes protegidos nem demonstra lucro futuro.
'''
(OUT / 'COMPLEMENTO_STOCKS.md').write_text(doc, encoding='utf-8')
archive = OUT / 'stocks-complemento-codigo.zip'
subprocess.run(['git', 'archive', '--format=zip', '--prefix=stocks-predictor/', '-o', str(archive), commit], cwd=REPO, check=True)
base = '1117fee33552648e5a698ba86c83b5d5187aa700'
(OUT / 'stocks-complemento.patch').write_bytes(git('diff', '--binary', base, commit))
wheel = ROOT / 'work/historical-wheel/stocks_predictor-0.1.0-py3-none-any.whl'
deliverables = ['COMPLEMENTO_STOCKS.md', 'stocks-complemento-codigo.zip', 'stocks-complemento.patch',
    'historical-acquisition.json', 'historical-cvm-validation.json', 'historical-rebuild-validation.json',
    'b3-acquisition-universe.json', 'b3-historical-acquisition.json', 'b3-historical-coverage-sample.json',
    'cash-source-reconciliation.json', 'cash-source-matches.jsonl', 'reconciled-cash-events.csv',
    'reconciled-cash-coverage.json', 'reconciled-cash-import.json', 'historical-table-integrity.json',
    'historical-protected-integrity.json', 'historical-tests-full.txt', 'historical-coverage.txt',
    'historical-lint.txt', 'historical-pyright.txt', 'historical-build.txt', 'historical-wheel-smoke.txt']
source_paths = sorted(p for p in (ROOT / 'work/source-acquisition').iterdir() if p.suffix in {'.zip', '.json', '.pdf', '.xlsx'})
derived_paths = sorted((ROOT / 'work/history-expanded').glob('*.jsonl'))
scripts = ['download_cvm_history.py', 'explore_b3_events.py', 'collect_b3_universe.py', 'extract_ri_payments.py',
           'reconcile_cash_sources.py', 'import_reconciled_cash.py']
manifest = {'code_commit': commit, 'tested_code_commit': commit, 'patch_base': base,
    'branch': 'fix/stocks-cvm-execution-20260907', 'tests_passed': int(matched[1]), 'tests_seconds': float(matched[2]),
    'python': '3.13', 'core': '3.2.0', 'counts': counts,
    'cash_receivables_imported': 95, 'cash_coverage_intervals': 4,
    'cash_coverage_is_whole_universe': False, 'all_share_effective_dates_certified': False,
    'all_historical_filing_versions_recovered': False, 'all_noncash_actions_certified': False,
    'strategy_performance_observed': False, 'operational_database_modified': False, 'pushed': False,
    'source_database_sha256': 'a22739794ba4a43a11544338d4a91e14cb6a0b1f7b132ab460f96d3359f63cf4',
    'rebuilt_database_sha256': digest(database), 'wheel_sha256': digest(wheel),
    'deliverable_sha256': {name: digest(OUT / name) for name in deliverables},
    'source_files': [{'name': p.name, 'bytes': p.stat().st_size, 'sha256': digest(p)} for p in source_paths],
    'derived_files': [{'name': p.name, 'sha256': digest(p)} for p in derived_paths],
    'reproduction_note': 'Portable CVM rebuild CLI in source archive. Acquisition/reconciliation scripts preserve the session directory layout and contain no credentials.'}
(OUT / 'historical-delivery-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
with zipfile.ZipFile(OUT / 'stocks-complemento-fontes.zip', 'w', compression=zipfile.ZIP_DEFLATED) as package:
    for name in deliverables + ['historical-delivery-manifest.json']:
        package.write(OUT / name, name)
    package.write(wheel, 'wheel/' + wheel.name)
    package.write(database, 'data/stocks-history-2016-2026.db')
    for path in source_paths:
        package.write(path, 'source-acquisition/' + path.name, compress_type=zipfile.ZIP_STORED if path.suffix in {'.zip', '.xlsx'} else zipfile.ZIP_DEFLATED)
    for path in derived_paths:
        package.write(path, 'history-expanded/' + path.name)
    for name in scripts:
        package.write(ROOT / 'work' / name, 'reproduce/' + name)
    package.writestr('reproduce/README.txt', 'Primary source downloads are already included. The research database is already rebuilt.\nNo action by the user is required.\nThe portable offline reconstruction command is in tools/rebuild_source_history.py inside the code archive.\nThe supplemental acquisition/reconciliation scripts use the original session work/ and outputs/ layout.\nCVM/B3 processing uses Python 3.13 stdlib; XLSX/PDF extraction uses the bundled document runtime.\nNo strategy performance was observed or approved.\n')
package = OUT / 'stocks-complemento-fontes.zip'
result = {'file': str(package), 'bytes': package.stat().st_size, 'sha256': digest(package), 'commit': commit,
          'tests_passed': int(matched[1])}
(OUT / 'historical-package-checksum.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
