"""Package and replay this audit in a fresh directory, preserving prior bundles."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parent.parent
WORK=ROOT/'work'
BASE=WORK/'h19-retail-bundle'
OUTPUTS=ROOT/'outputs'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
subprocess.run([sys.executable,str(WORK/'prepare_h19_retail_bundle.py')],check=True,cwd=ROOT,capture_output=True)
assert '558 passed' in (WORK/'h19-retail-tests.log').read_text(encoding='utf-8')
assert 'All checks passed!' in (WORK/'h19-retail-lint.log').read_text(encoding='utf-8')
assert '0 errors' in (WORK/'h19-retail-pyright.log').read_text(encoding='utf-8')
assert 'Successfully built' in (WORK/'h19-retail-build.log').read_text(encoding='utf-8')
assert 'PASS wheel' in (WORK/'h19-retail-wheel-smoke.log').read_text(encoding='utf-8')
(BASE/'verification').mkdir(exist_ok=True)
for p in WORK.glob('h19-retail-*.log'):shutil.copy2(p,BASE/'verification'/p.name)
shutil.copy2(WORK/'stocks-predictor/tests/test_retail_cash.py',BASE/'verification/test_retail_cash.py')
(BASE/'research-scripts').mkdir(exist_ok=True)
for name in ['build_h19_reviewed_dates.py','reconcile_h19_cash_tables.py','extract_h19_notices.py',
             'cash_research_fetch.py','index_h19_ipe.py','extend_h19_ipe_payments.py','prepare_h19_retail_bundle.py']:
    shutil.copy2(WORK/name,BASE/'research-scripts'/name)
# Downloads/derived text are evidence only; the offline runner never fetches or
# executes primary-source content. Original repository paths in research scripts
# document the acquisition workflow; only RODAR_H19_CAIXA.py is the portable CLI.
sources=BASE/'sources'; sources.mkdir(exist_ok=True)
for p in (WORK/'h19-cash-expanded-source').iterdir():
    if p.is_file() and p.name!='reconciliation.json':shutil.copy2(p,sources/p.name)
registry=read(WORK/'h19-cash-expanded-source/reviewed-payment-dates.json')
for row in registry['cash_queue']:
    p=Path(row['source_path']); target=sources/p.name
    if target.exists():assert sha(target)==sha(p)
    else:shutil.copy2(p,target)
for fact in registry['facts']:
    for source in fact['sources']:
        name=source['file']
        candidates=[WORK/'h19-cash-expanded-source'/name,WORK/'source-acquisition'/name,OUTPUTS/name]
        origin=next(p for p in candidates if p.exists())
        assert sha(origin)==source['sha256']
        target=sources/name
        if target.exists():assert sha(target)==sha(origin)
        else:shutil.copy2(origin,target)
for p in (WORK/'h19-cash-closure-source').iterdir():
    if p.is_file():shutil.copy2(p,sources/p.name)
shutil.copy2(OUTPUTS/'cash-source-matches.jsonl',sources/'cash-source-matches.jsonl')
shutil.copy2(WORK/'h19-retail-dist/stocks_predictor-0.1.0-py3-none-any.whl',BASE/'verification/stocks_predictor-0.1.0-py3-none-any.whl')
save(BASE/'verification/context.json',dict(runtime_commit='5e71bc8',tests=558,seconds=154.91,
    coverage_percent=79,retail_module_coverage_percent=85,ruff='PASS',configured_pyright='PASS_RJ_SCOPE',
    wheel_build='PASS',wheel_external_import='PASS',new_dependencies=0,
    source_observation_sha256='c47fcca89d07e2064c1ba6ebc7a1f1dc763473a1364291284dfe6d761d7e9128'))
(BASE/'LEIA-ME.md').write_text('''# H19 — auditoria de caixa e teste de entrada

Este pacote executa uma auditoria das pendências e quatro testes contábeis da
primeira compra congelada (02/07/2018), com R$5 mil/R$10 mil e custo hipotético
de 18/36 pontos-base por lado. Não executa a carteira histórica completa e não
calcula lucro líquido, retorno ou comparação econômica.

Extraia a pasta e execute com Python 3.13 global:

```powershell
py -3.13 RODAR_H19_CAIXA.py --output H19_CAIXA_EXECUCAO.json
```

O código de saída **2** e `BLOCKED_MISSING_EVIDENCE` são o resultado esperado:
o auditor encontrou dados obrigatórios ausentes. Uma exceção Python, hash
divergente ou outro código de saída é falha técnica. Os quatro resultados
`PASS_ACCOUNTING_ONLY` validam somente a entrada; não constituem quatro
backtests. Não há dependência de rede, API, Core, credencial ou instalação de
bibliotecas para esse comando.

SHA256.json verifica todos os arquivos incluídos. inputs/ contém as seleções
anteriores, cotações brutas da entrada e inventários. sources/ preserva avisos,
metadados, tabelas e textos extraídos. Valores transcritos de imagem são
identificados no registro. verification/ contém os logs dos 558 testes, lint,
Pyright no escopo configurado, build e importação externa da wheel. O teste
pytest é documentação do teste de desenvolvimento, não requisito do comando.

research-scripts/ documenta a aquisição no workspace original; esses scripts
não são comandos portáteis nem devem ser executados como parte do replay.

Limites: ainda faltam a carteira contínua, cobertura completa de proventos das
duas carteiras, tratamento fiscal e entrega de ações/frações. Pagamento
declarado pelo emissor não comprova crédito numa conta real. Preços de abertura
do COTAHIST não garantem preenchimento de ordens. Nenhum desses limites foi
resolvido atribuindo zero a dados ausentes. Nenhuma ordem real é enviada.
''',encoding='utf-8')
payload={p.relative_to(BASE).as_posix():sha(p) for p in sorted(BASE.rglob('*'))
         if p.is_file() and p.name!='SHA256.json' and '__pycache__' not in p.parts}
save(BASE/'SHA256.json',payload)
archive=OUTPUTS/'STOCKS_H19_CAIXA_TESTADO_V2.zip'
if archive.exists():raise FileExistsError('Do not overwrite a delivered bundle')
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for name in [*payload,'SHA256.json']:z.write(BASE/name,name)
digest=sha(archive)
fresh=WORK/f'h19-cash-replay-{digest[:12]}'
fresh.mkdir(exist_ok=False)
with zipfile.ZipFile(archive) as z:z.extractall(fresh)
replay_output=WORK/'h19-retail-offline-replay.json'
run=subprocess.run([sys.executable,'RODAR_H19_CAIXA.py','--output',str(replay_output)],
    cwd=fresh,capture_output=True,text=True,encoding='utf-8')
(WORK/'h19-retail-offline-replay.log').write_text(run.stdout+'\n'+run.stderr,encoding='utf-8')
assert run.returncode==2 and not run.stderr, (run.returncode,run.stderr)
result=read(replay_output)
assert result['profit'] is None and len(result['first_entry_smoke'])==4
assert all(r['status']=='PASS_ACCOUNTING_ONLY' for r in result['first_entry_smoke'])
assert result['verified_package_files']==len(payload)
# Replay a second time without modifying its inputs; must be bit-for-bit stable.
again=WORK/'h19-retail-offline-replay-again.json'
run2=subprocess.run([sys.executable,'RODAR_H19_CAIXA.py','--output',str(again)],cwd=fresh,capture_output=True)
assert run2.returncode==2 and replay_output.read_bytes()==again.read_bytes()
shutil.copy2(replay_output,OUTPUTS/'H19_CAIXA_EXECUCAO_V2.json')
shutil.copy2(WORK/'h19-cash-expanded-source/reviewed-payment-dates.json',OUTPUTS/'H19_CAIXA_PAGAMENTOS_REVISADOS_V2.json')
dbs={}
for p,expected in [(Path(r'C:\Users\Superleo13\stocks-predictor-work\data\stocks.db'),
                    'a22739794ba4a43a11544338d4a91e14cb6a0b1f7b132ab460f96d3359f63cf4'),
                   (WORK/'stocks-tested-real-v2-20260907.db',
                    'a8238568980d3303890b04590cfb5c55ab2d24c9271edd86820269336b09679a')]:
    actual=sha(p);assert actual==expected;dbs[str(p)]=actual
verification=dict(archive=archive.name,sha256=digest,bytes=archive.stat().st_size,
    payload_files=len(payload),archive_entries=len(payload)+1,offline_replay='PASS_EXPECTED_BLOCKED_STATUS',
    repeated_output_identical=True,output_sha256=sha(replay_output),exit_code=2,
    historical_profit=None,first_entry_checks=4,source_databases_unchanged=dbs)
save(OUTPUTS/'H19_CAIXA_REPRODUCAO_V2.json',verification)
print(json.dumps(verification,indent=2))
