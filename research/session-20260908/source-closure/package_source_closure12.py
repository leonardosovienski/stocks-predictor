"""Build a portable, offline audit bundle and test the wheel outside the checkout."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
from source_utils import ROOT, OUT, read

CHAT=Path(r'C:\Users\Superleo13\Documents\Codex\2026-09-07\lei-2');repo=ROOT/'work/stocks-predictor'
stage=OUT/'portable-audit-12';stage.mkdir(exist_ok=True)
assert stage.resolve().parent==OUT.resolve() and not (stage/'PACKAGE_SHA256.json').exists()
wheel,=(OUT/'dist-12').glob('*.whl');(stage/'wheel').mkdir(exist_ok=True);shutil.copyfile(wheel,stage/'wheel'/wheel.name)
for source,target in [(ROOT/'work/stocks-final-review-bundle/inputs',stage/'baseline'),
                      (OUT/'execution-inputs-12',stage/'inputs')]:shutil.copytree(source,target,dirs_exist_ok=True)
for source,target in [(ROOT/'work/h20-implementation-20260908/observation-02.json','signals.json'),
    (repo/'docs/research/2026-09-08-source-closure-protocol.json','source-protocol.json'),
    (OUT/'integrated-readiness-12.json','expected-audit.json'),
    (CHAT/'work/REPRODUZIR_FONTES.py','REPRODUZIR_FONTES.py'),
    (repo/'research/session-20260908/source-closure/PENDENCIAS_STOCKS.json','PENDENCIAS_STOCKS.json')]:
    shutil.copyfile(source,stage/target)
trail=stage/'revision-trail';trail.mkdir(exist_ok=True)
for p in sorted(OUT.glob('cash-closure-*.json')):shutil.copyfile(p,trail/p.name)
for name in ['additional-acquisition.json','deadline-credit-acquisition-12.json',
             'cpfl-credit-acquisition.json','source-validation-12.json','full-tests-12.log']:
    shutil.copyfile(OUT/name,trail/name)
for p in (repo/'research/session-20260908/source-closure').glob('*.py'):
    shutil.copyfile(p,trail/p.name)
readme='''# Auditoria de fontes — revisão12

Resultado: BLOCKED_MISSING_EVIDENCE. O pacote reproduz a auditoria, sem
executar retornos históricos, emitir ordens ou acessar a rede. Não comprova lucro.

No Windows, use o Python global3.13 já existente, sem instalação ou ambiente virtual:

    py -3.13 -I REPRODUZIR_FONTES.py --output auditoria-reproduzida.json

O comando verifica os hashes de todos os arquivos, importa o código da wheel
incluída e exige uma saída idêntica a expected-audit.json. Código0 significa
reprodução correta; o resultado econômico permanece bloqueado. Uma segunda
execução precisa de outro nome em --output; nenhuma auditoria é sobrescrita.

inputs/ contém a revisão e todas as fontes referenciadas; baseline/ conserva os
31 arquivos congelados anteriores. primary-catalog.json vincula cada arquivo
ao hash, URL e classificação. Caminhos antigos presentes nos metadados são
linhagem histórica; a auditoria lê verified_primary_file dentro deste pacote.
revision-trail/ conserva as versões e os scripts de investigação originais.
Esses scripts históricos não são o comando portátil e contêm caminhos locais.

PENDENCIAS_STOCKS.json lista as datas/líquidos faltantes e demais bloqueios.
Não converter lacunas em zero. Nenhuma nova avaliação de retorno foi feita;
um protocolo separado com o hash final ainda é obrigatório antes de executá-la.
'''
(stage/'LEIA-ME.md').write_text(readme,encoding='utf-8',newline='\n')

# Tests use an extracted wheel and copied real/synthetic fixtures. The checkout
# is deliberately absent from PYTHONPATH; nothing is installed.
outside=OUT/'wheel-check-12';outside.mkdir(exist_ok=True);site=outside/'site';site.mkdir(exist_ok=True)
with zipfile.ZipFile(wheel) as z:
    assert all((site/n).resolve().is_relative_to(site.resolve()) for n in z.namelist())
    z.extractall(site)
testdir=outside/'tests';testdir.mkdir(exist_ok=True)
focused=['__init__.py','test_h20_continuous.py','test_h20_checked.py','test_h20_implementation.py',
    'test_continuous_cash.py','test_corporate_auction_tax.py','test_continuous_research.py',
    'test_cash_source_audit.py','test_source_closure.py']
for name in focused:shutil.copyfile(repo/'tests'/name,testdir/name)
for name in ['source_closure','cvm_source_history']:
    shutil.copytree(repo/'tests/fixtures'/name,testdir/'fixtures'/name,dirs_exist_ok=True)
env={**os.environ,'PYTHONUTF8':'1','PYTHONIOENCODING':'utf-8',
     'PYTHONPATH':os.pathsep.join(map(str,[site,site/'stocks_predictor',ROOT/'work/runtime',ROOT/'work/checks']))}
p=subprocess.run([sys.executable,'-m','pytest','tests','-q'],cwd=outside,env=env,
    capture_output=True,text=True,encoding='utf-8')
with (OUT/'wheel-tests-12-retry.log').open('x',encoding='utf-8') as log:log.write(p.stdout+p.stderr)
print(p.stdout+p.stderr,flush=True);assert p.returncode==0

def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
manifest={p.relative_to(stage).as_posix():digest(p) for p in sorted(stage.rglob('*')) if p.is_file()}
(stage/'PACKAGE_SHA256.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Payloads hashed:',len(manifest),flush=True)
env={**os.environ,'PYTHONUTF8':'1','PYTHONIOENCODING':'utf-8'};env.pop('PYTHONPATH',None)
p=subprocess.run([sys.executable,'-I',str(stage/'REPRODUZIR_FONTES.py'),'--output',str(OUT/'portable-reproduced-12.json')],
    cwd=stage,env=env,capture_output=True,text=True,encoding='utf-8')
(OUT/'portable-reproduction-12.log').write_text(p.stdout+p.stderr,encoding='utf-8')
print(p.stdout+p.stderr,flush=True);assert p.returncode==0

target=CHAT/'outputs/AUDITORIA_STOCKS_REPRODUZIVEL_12.zip'
assert not target.exists()
with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(stage.rglob('*')):
        if p.is_file():z.write(p,p.relative_to(stage).as_posix())
print('ZIP written:',target.stat().st_size,flush=True)
with zipfile.ZipFile(target) as z:
    assert z.testzip() is None
    expected=read(stage/'PACKAGE_SHA256.json')
    assert set(z.namelist())==set(expected)|{'PACKAGE_SHA256.json'}
    for name,sha in expected.items():
        with z.open(name) as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==sha
result=dict(wheel=wheel.name,wheel_sha256=digest(wheel),wheel_installed=False,
    portable_reproduction='BYTE_IDENTICAL_WITH_ISOLATED_GLOBAL_PYTHON_3_13',
    audit_sha256=digest(OUT/'portable-reproduced-12.json'),payloads_verified=len(manifest),
    zip_sha256=digest(target),zip_bytes=target.stat().st_size,new_historical_return_evaluations=0)
with (OUT/'package-validation-12.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
print(json.dumps(result),flush=True)
