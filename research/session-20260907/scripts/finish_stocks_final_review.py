"""Record only completed checks, publish a coherent review and reproduce its ZIP."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / 'work/stocks-predictor'
BASE = ROOT / 'work/stocks-final-review-bundle'
OUT = ROOT / 'outputs'


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def write(p, v):
    p.write_text(json.dumps(v, ensure_ascii=False, indent=2), encoding='utf-8')


def sha(p):
    with p.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


validation = read(OUT / 'STOCKS_REVISAO_FINAL_VALIDACAO.json')
assert validation['status'] == 'TECHNICAL_CHECKS_PASSED_ECONOMIC_REPLAY_BLOCKED'
assert any(s['step'] == 'actual-readonly-status' and s['exit_code'] == 0 for s in validation['steps'])
commit = validation['validated_commit']
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip() == commit
assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=REPO).strip()
count = validation['tests_passed']
test_step = next(s for s in validation['steps'] if s['step'] == 'tests')
coverage_text = (ROOT / 'work/stocks-final-review-v2-coverage.log').read_text(encoding='utf-8')
coverage = int(re.search(r'^TOTAL.*? (\d+)%', coverage_text, re.M).group(1))
scope_coverage = {name: int(re.search(r'^stocks_predictor[\\/]' + name + r'\.py\s+.*? (\d+)%', coverage_text, re.M).group(1))
                  for name in ('retail_cash', 'continuous_cash', 'continuous_research')}
reproduced = read(OUT / 'STOCKS_REVISAO_FINAL_PRECOS_REPRODUZIDOS.json')
assert reproduced['status'] == 'PASS' and reproduced['independent_cells'] == 9732
source = read(OUT / 'STOCKS_REVISAO_FINAL_FONTES.json')
run_result = read(OUT / 'STOCKS_REVISAO_FINAL_EXECUCAO.json')
assert run_result['validated_quote_records'] == source['total_quote_records_equal_to_raw'] == 365198
final_validation = f'''Validação final do código `{commit}`: **{count} testes passaram** em
{test_step['elapsed_seconds']:.2f} segundos. Cobertura geral {coverage}%; contabilidade de varejo
{scope_coverage['retail_cash']}%, execução contínua {scope_coverage['continuous_cash']}% e driver
{scope_coverage['continuous_research']}%. Ruff, Pyright no escopo ampliado, build da wheel e importação
fora do checkout passaram. O recorte independente passou 48 testes. O comando
de status foi executado no banco real com conexão somente leitura; os dois bancos
mantiveram os hashes anteriores. Nenhuma instalação/dependência nova de runtime.

O replay real validou 31 arquivos de entrada e 365.198 registros de cotação,
então terminou com **exit 2 / BLOCKED_MISSING_EVIDENCE**. Não executou o histórico
completo nem publicou retorno parcial. Os quatro casos continuam cadastrados;
nenhum foi observado nesta revisão. A reprodução anterior conferiu 1.448 arquivos,
as quatro coortes, 9.732 células e os 12 cenários/intervalos antigos idênticos.
Isso não acrescenta amostra independente nem transforma preços em lucro líquido.
'''
review_path = REPO / 'docs/research/2026-09-07-final-review.md'
review = review_path.read_text(encoding='utf-8')
review = review[:review.index('## Validação desta versão')] + '## Validação desta versão\n\n' + final_validation
review_path.write_text(review, encoding='utf-8')
handoff = REPO / 'HANDOFF.md'
handoff.write_text(f'''## Encerramento da revisão final (2026-09-07)

Código validado {commit}: {count} testes, {coverage}% cobertura, Ruff,
Pyright RJ+H19, wheel/importação externa e 48 testes do recorte passaram.
Status real executado somente leitura e hashes dos dois bancos preservados.
365.198 registros confrontados com extratos brutos; 367 fontes verificadas.
Reprodução histórica de 9.732 células e 12 cenários antiga idêntica.
Replay econômico atual exit 2, 356 datas pendentes, 0/1.237 intervalos com
inventário certificado e 0/36 registros societários integrados/aprovados.
Não há lucro líquido confirmado; não há prova de prejuízo. NO_GO operacional,
H19 Discovery inconclusiva. Nenhuma avaliação histórica nova, ordem ou gasto.
Parecer canônico: docs/research/2026-09-07-final-review.md. O pacote final
inclui código-fonte completo em ZIP, wheel, recorte executável e entradas/fontes.

''' + handoff.read_text(encoding='utf-8'), encoding='utf-8')
state = REPO / 'STOCKS_CURRENT_STATE.md'
text = state.read_text(encoding='utf-8').replace('A contabilidade contínua existe e está sob validação da revisão final.',
    f'A revisão final passou {count} testes e os controles técnicos declarados.')
state.write_text(text, encoding='utf-8')
subprocess.run(['git', 'add', 'HANDOFF.md', 'STOCKS_CURRENT_STATE.md', 'docs/research/2026-09-07-final-review.md'], cwd=REPO, check=True)
subprocess.run(['git', 'commit', '-m', 'Record final review validation and unresolved net-profit evidence'], cwd=REPO, check=True)
docs_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip()
assert not subprocess.check_output(['git', 'diff', commit, '--', 'stocks_predictor', 'tests', 'main.py', 'pyproject.toml', 'tools'], cwd=REPO).strip()

decision = {'date_utc': datetime.now(timezone.utc).isoformat(), 'review_commit': docs_commit,
    'validated_runtime_commit': commit, 'technical_validation': 'PASSED_DECLARED_CHECKS',
    'economic_verdict': 'INCONCLUSIVE_NET_PROFIT', 'operational_decision': 'NO_GO',
    'net_profit_brl': None, 'loss_demonstrated': False,
    'project_quality': 'AUDITABLE_RESEARCH_PROTOTYPE_WITH_INCOMPLETE_ECONOMIC_IMPLEMENTATION_AND_INPUTS',
    'capital_scenarios_brl': [5000, 10000], 'tests_passed': count,
    'new_historical_return_evaluations': 0,
    'minimum_exposed_configurations': 32, 'minimum_historical_evaluations': 37,
    'untouched_holdout_demonstrated': False, 'paper_fill_history_validated': False,
    'unresolved': {'cash_payment_dates': 356, 'cash_intervals_without_inventory_certificate': 1237,
        'required_corporate_records': 36, 'integrated_approved_corporate_records': 0,
        'portfolio_dependent_corporate_tax_implemented': False,
        'successor_and_later_JBS_cash_complete': False,
        'actual_fills_and_broker_rounding_validated': False},
    'research_decisions': ['Keep frozen H19 selections and source lineage',
        'Do not reuse invalid legacy backtests as profit evidence',
        'No new H20 or ML search to bypass measurement gaps',
        'Finish case-dependent corporate accounting and primary cash coverage before any net-profit claim'],
    'real_orders_submitted': False, 'external_paid_services_purchased': False,
    'database_hashes_preserved': validation['database_hashes']}
write(OUT / 'STOCKS_REVISAO_FINAL_DECISAO.json', decision)
front = f'''# Estado final de Stocks

**A revisão técnica foi concluída. O projeto ainda não demonstrou lucro líquido.**
Ele é um protótipo de pesquisa auditável, com dados e contabilidade societária
insuficientes para concluir o resultado econômico. Decisão atual: **não operar**.

| Verificação | Resultado |
|---|---|
| Código | {count} testes passaram; lint, análise estática ampliada e wheel passaram |
| Correções | Entregas parciais, conhecimento de eventos, vínculo ao protocolo, casos inválidos e consultas sem escrita |
| Cotações | 365.198 registros comparados com os extratos brutos, sem divergência nos campos auditados |
| Resultados antigos | 9.732 células e 12 cenários reproduzidos; continuam sendo diagnósticos de preços |
| Execução econômica real | Tentada; bloqueada por evidência incompleta, sem retorno publicado |
| Lucro ou prejuízo líquido | Ainda indeterminado; bloqueio não significa lucro zero |

Faltam 356 datas de pagamento, certificar o inventário de caixa dos 1.237
intervalos e integrar os 36 registros societários exigidos. Há também tratamento
fiscal que depende da posição de cada carteira: essa parte exige código e revisão
de fontes. Não é apenas preencher datas ou apertar outro botão de execução.

O pacote `STOCKS_REVISAO_FINAL.zip` contém o código completo, a wheel e uma
reprodução offline. `RODAR_H19.ps1` executa a auditoria com Python 3.13 global,
sem instalar bibliotecas. Com estes dados o resultado correto é **código 2**.
`RESULTADO_H19.json` enumera as pendências. O programa não envia ordens.

Os detalhes e limites da revisão estão abaixo.

---

'''
(OUT / 'ESTADO_FINAL_STOCKS.md').write_text(front + review, encoding='utf-8')
shutil.copy2(OUT / 'ESTADO_FINAL_STOCKS.md', BASE / 'ESTADO_FINAL_STOCKS.md')
for name in ('STOCKS_REVISAO_FINAL_VALIDACAO.json', 'STOCKS_REVISAO_FINAL_EXECUCAO.json',
             'STOCKS_REVISAO_FINAL_FONTES.json', 'STOCKS_REVISAO_FINAL_PRECOS_REPRODUZIDOS.json',
             'STOCKS_REVISAO_FINAL_DECISAO.json'):
    shutil.copy2(OUT / name, BASE / 'verification' / name)
for row in validation['steps']:
    shutil.copy2(ROOT / 'work' / row['log'], BASE / 'verification' / row['log'])
shutil.copy2(ROOT / 'work/stocks-final-review-before-fixes.log', BASE / 'verification')
shutil.copy2(ROOT / 'work/stocks-final-review-v2-wheel' / validation['wheel'], BASE / validation['wheel'])
subprocess.run(['git', 'archive', '--format=zip', '--output=' + str(BASE / 'CODIGO_COMPLETO_STOCKS.zip'), docs_commit], cwd=REPO, check=True)
for name in ('prepare_stocks_final_review.py', 'validate_stocks_final_review.py', 'check_stocks_old_regressions.py'):
    shutil.copy2(ROOT / 'work' / name, BASE / 'research-scripts' / name)
write(BASE / 'BUILD.json', {'validated_runtime_commit': commit, 'review_commit': docs_commit,
    'tests_passed': count, 'standalone_tests_passed': 48, 'source_module_hashes': validation['source_module_hashes'],
    'runtime_dependencies_for_standalone_replay': [], 'new_historical_return_evaluations': 0,
    'economic_result': 'BLOCKED_MISSING_EVIDENCE', 'code_archive_sha256': sha(BASE / 'CODIGO_COMPLETO_STOCKS.zip')})
(BASE / 'LEIA-ME.md').write_text('''# Stocks: revisão final

Estado: protótipo de pesquisa; lucro líquido não demonstrado; NO_GO para operar.
Leia ESTADO_FINAL_STOCKS.md para o parecer e verification/ para os resultados.

Execute RODAR_H19.ps1 ou, nesta pasta:

```powershell
py -3.13 -m stocks_predictor.continuous_research --inputs ./inputs --output ./RESULTADO_H19.json
```

Python 3.13 global, sem bibliotecas adicionais. Código 2 significa que os dados
atuais impedem calcular lucro; código 1 indica entrada inválida/erro; código 0
exige completar ambas as carteiras em todos os casos. Não são enviadas ordens.
O programa confere hashes e as seleções congeladas da H19, lê as cotações e
relata as lacunas de evidência. Não substitui proventos desconhecidos por zero.

O recorte stocks_predictor/ é autossuficiente para esse comando. A wheel e
CODIGO_COMPLETO_STOCKS.zip contêm também as demais partes do projeto; estas
mantêm as dependências declaradas no pyproject.toml, incluindo Core global.
O projeto completo não deve ser confundido com este recorte sem dependências.

SHA256.json cobre os arquivos do pacote. inputs/SHA256.json protege as entradas.
sources/ contém 367 cópias primárias; SOURCE_FILES.json faz o mapeamento.
inputs/ também contém extratos brutos COTAHIST e a observação congelada.
Copiar fontes e verificar hashes não certifica completude econômica.

Com pytest já disponível, os 48 testes do recorte rodam por:
`py -3.13 -m pytest tests -q`. Seus ganhos são sintéticos e não evidência de lucro.
Os logs com prefixo h19-continuous documentam a entrega anterior; os arquivos
STOCKS_REVISAO_FINAL e stocks-final-review-v2 documentam esta revisão.
research-scripts/ preserva a preparação; alguns exigem a área de pesquisa original
e não são necessários para reproduzir a execução acima.
''', encoding='utf-8')

def payloads():
    return sorted(p for p in BASE.rglob('*') if p.is_file() and p != BASE / 'SHA256.json'
                  and not {'__pycache__', '.pytest_cache'} & set(p.relative_to(BASE).parts))

write(BASE / 'SHA256.json', {p.relative_to(BASE).as_posix(): sha(p) for p in payloads()})
package = OUT / 'STOCKS_REVISAO_FINAL.zip'
with zipfile.ZipFile(package, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for p in [*payloads(), BASE / 'SHA256.json']:
        archive.write(p, p.relative_to(BASE).as_posix())
package_sha = sha(package)
fresh = ROOT / 'work' / ('stocks-final-review-reproduced-' + package_sha[:12])
fresh.mkdir(exist_ok=False)
with zipfile.ZipFile(package) as archive:
    for name in archive.namelist():
        assert (fresh / name).resolve().is_relative_to(fresh.resolve())
    archive.extractall(fresh)
manifest = read(fresh / 'SHA256.json')
for name, expected in manifest.items():
    assert sha(fresh / name) == expected, name
env = dict(os.environ, PYTHONPATH=str(ROOT / 'work/checks'))
tests = subprocess.run([sys.executable, '-X', 'utf8', '-m', 'pytest', 'tests', '-q'], cwd=fresh,
    env=env, capture_output=True, text=True, encoding='utf-8')
(ROOT / 'work/stocks-final-review-zip-tests.log').write_text(tests.stdout+tests.stderr, encoding='utf-8')
assert tests.returncode == 0 and '48 passed' in tests.stdout
outputs = []
for n in (1, 2):
    target = fresh / f'reproduction-{n}.json'
    result = subprocess.run([sys.executable, '-X', 'utf8', '-m', 'stocks_predictor.continuous_research',
        '--inputs', 'inputs', '--output', str(target)], cwd=fresh, env=env,
        capture_output=True, text=True, encoding='utf-8')
    assert result.returncode == 2
    assert read(target) == run_result
    outputs.append({'run': n, 'exit_code': result.returncode, 'sha256': sha(target)})
assert outputs[0]['sha256'] == outputs[1]['sha256']
receipt = {'package': package.name, 'package_sha256': package_sha, 'bytes': package.stat().st_size,
    'verified_payloads': len(manifest), 'primary_sources': 367, 'standalone_tests_passed': 48,
    'fresh_extraction_replays': outputs, 'identical_to_installed_wheel_execution': True,
    'full_economic_history_executed': False, 'profit': None, 'new_historical_return_evaluations': 0,
    'validated_runtime_commit': commit, 'review_commit': docs_commit}
write(OUT / 'STOCKS_REVISAO_FINAL_REPRODUCAO.json', receipt)
assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=REPO).strip()
for name, expected in validation['database_hashes'].items():
    assert sha(Path(name)) == expected
print(json.dumps(receipt, ensure_ascii=False), flush=True)
