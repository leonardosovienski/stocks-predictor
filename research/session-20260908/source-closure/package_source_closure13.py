"""Package the current sources, original candidates and tested wheel offline."""
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
code=read(OUT/'code-validation-13.json')
assert all(r['returncode']==0 for r in code['commands'])
assert subprocess.check_output(['git','status','--porcelain'],cwd=repo)==b''
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()==code['tested_commit']
stage=OUT/'portable-audit-13';stage.mkdir()
wheel,=(OUT/'dist-13').glob('*.whl');(stage/'wheel').mkdir();shutil.copyfile(wheel,stage/'wheel'/wheel.name)
with zipfile.ZipFile(wheel) as z:
    modules=[n for n in z.namelist() if n.startswith('stocks_predictor/') and n.endswith('.py')]
    assert set(modules)=={p.relative_to(repo).as_posix() for p in (repo/'stocks_predictor').rglob('*.py')}
    assert all(z.read(n)==(repo/n).read_bytes() for n in modules)
for source,target in [(ROOT/'work/stocks-final-review-bundle/inputs',stage/'baseline'),
                      (OUT/'execution-inputs-13',stage/'inputs')]:shutil.copytree(source,target)
for source,target in [(ROOT/'work/h20-implementation-20260908/observation-02.json','signals.json'),
    (repo/'docs/research/2026-09-08-source-closure-protocol.json','source-protocol.json'),
    (OUT/'integrated-readiness-13.json','expected-audit.json'),
    (CHAT/'work/REPRODUZIR_FONTES.py','REPRODUZIR_FONTES.py'),
    (repo/'research/session-20260908/source-closure/PENDENCIAS_STOCKS.json','PENDENCIAS_STOCKS.json')]:
    shutil.copyfile(source,stage/target)
trail=stage/'revision-trail';trail.mkdir()
for p in sorted(OUT.glob('cash-closure-*.json')):shutil.copyfile(p,trail/p.name)
for pattern in ['*13*.json','*13*.log']:
    for p in OUT.glob(pattern):shutil.copyfile(p,trail/p.name)
for p in (repo/'research/session-20260908/source-closure').glob('*.py'):shutil.copyfile(p,trail/p.name)
for name in ['test_source_closure13.py','package_source_closure13.py']:
    shutil.copyfile(CHAT/'work'/name,trail/name)
# This directory preserves acquisition attempts, including the explicitly
# rejected partial ITR and HTML error responses; it never certifies a payment.
candidates=stage/'investigation-candidates';candidates.mkdir()
for p in (OUT/'new-primary').glob('issuer-13-*'):shutil.copyfile(p,candidates/p.name)
for name in ['issuer-13-cvm-1456495-p1.png','issuer-13-cvm-1037840-p2.png',
             'issuer-13-hapvida-prospectus2022-p2300.png']:
    shutil.copyfile(OUT/'pages'/name,candidates/name)
(stage/'LEIA-ME.md').write_text('''# Auditoria de fontes — revisão 13

Este pacote reproduz a auditoria de fontes. Não executa retornos históricos,
ordens ou acessos à rede. O resultado econômico é BLOCKED_MISSING_EVIDENCE.

Use o Python global 3.13 existente, sem instalação ou ambiente virtual:

    py -3.13 -I REPRODUZIR_FONTES.py --output auditoria-reproduzida.json

O comando verifica o manifesto do pacote e importa a wheel incluída. Exige
auditoria idêntica a expected-audit.json. Saída 0 significa reprodução correta,
não lucro demonstrado. Cada execução precisa de um novo arquivo de saída.

inputs/ contém fontes referenciadas e sua classificação no primary-catalog.json;
baseline/ conserva as entradas anteriores. Caminhos locais históricos nos
metadados são linhagem; verified_primary_file é o caminho usado no pacote.
duplicate-lineage.json preserva duas linhas B3 Hypera para UM pagamento.
Os três pagamentos Iguatemi de 2019 continuam distintos. Não deduplicar por
valor ou aparência. A revisão exige documentos originais e análise explícita.

investigation-candidates/ preserva downloads usados na investigação, incluindo
documentos substituídos, HTML de erro e um ITR Hapvida parcial rejeitado como
prova. Presença neste diretório não significa fonte válida ou pagamento aprovado.
Somente inputs/ define a auditoria. PDFs CVM podem conter bytes NUL depois de
EOF; os originais foram preservados integralmente, sem reparo do conteúdo.

revision-trail/ contém snapshots e scripts originais de investigação, que usam
caminhos históricos. REPRODUZIR_FONTES.py é o comando portátil. Não executar
scripts históricos como se fossem o pipeline portátil. PENDENCIAS_STOCKS.json
lista 24 datas, 54 líquidos e as demais lacunas. Nenhum prazo máximo foi
convertido em pagamento recebido. Lucro/projeção continuam desconhecidos.
''',encoding='utf-8',newline='\n')

outside=OUT/'wheel-check-13';outside.mkdir();site=outside/'site';site.mkdir()
with zipfile.ZipFile(wheel) as z:
    assert all((site/n).resolve().is_relative_to(site.resolve()) for n in z.namelist())
    z.extractall(site)
testdir=outside/'tests';testdir.mkdir()
for name in ['__init__.py','test_h20_continuous.py','test_h20_checked.py','test_h20_implementation.py',
    'test_continuous_cash.py','test_corporate_auction_tax.py','test_continuous_research.py',
    'test_cash_source_audit.py','test_source_closure.py']:shutil.copyfile(repo/'tests'/name,testdir/name)
for name in ['source_closure','cvm_source_history']:
    shutil.copytree(repo/'tests/fixtures'/name,testdir/'fixtures'/name)
env={**os.environ,'PYTHONUTF8':'1','PYTHONIOENCODING':'utf-8',
     'PYTHONPATH':os.pathsep.join(map(str,[site,site/'stocks_predictor',ROOT/'work/runtime',ROOT/'work/checks']))}
p=subprocess.run([sys.executable,'-m','pytest','tests','-q'],cwd=outside,env=env,
    capture_output=True,text=True,encoding='utf-8')
with (OUT/'wheel-tests-13.log').open('x',encoding='utf-8') as log:log.write(p.stdout+p.stderr)
print(p.stdout+p.stderr,flush=True);assert p.returncode==0
shutil.copyfile(OUT/'wheel-tests-13.log',trail/'wheel-tests-13.log')

def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
manifest={p.relative_to(stage).as_posix():digest(p) for p in sorted(stage.rglob('*')) if p.is_file()}
(stage/'PACKAGE_SHA256.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Payloads hashed:',len(manifest),flush=True)
env={**os.environ,'PYTHONUTF8':'1','PYTHONIOENCODING':'utf-8'};env.pop('PYTHONPATH',None)
p=subprocess.run([sys.executable,'-I',str(stage/'REPRODUZIR_FONTES.py'),'--output',str(OUT/'portable-reproduced-13.json')],
    cwd=stage,env=env,capture_output=True,text=True,encoding='utf-8')
(OUT/'portable-reproduction-13.log').write_text(p.stdout+p.stderr,encoding='utf-8')
print(p.stdout+p.stderr,flush=True);assert p.returncode==0

target=CHAT/'outputs/AUDITORIA_STOCKS_REPRODUZIVEL_13.zip'
with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(stage.rglob('*')):
        if p.is_file():z.write(p,p.relative_to(stage).as_posix())
print('ZIP written:',target.stat().st_size,flush=True)
with zipfile.ZipFile(target) as z:
    assert z.testzip() is None
    assert set(z.namelist())==set(manifest)|{'PACKAGE_SHA256.json'}
    for name,expected in manifest.items():
        with z.open(name) as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==expected
result=dict(tested_commit=code['tested_commit'],wheel=wheel.name,wheel_sha256=digest(wheel),
    wheel_modules_matched_to_checkout=len(modules),wheel_installed=False,
    portable_reproduction='BYTE_IDENTICAL_WITH_ISOLATED_GLOBAL_PYTHON_3_13',
    audit_sha256=digest(OUT/'portable-reproduced-13.json'),payloads_verified=len(manifest),
    zip_sha256=digest(target),zip_bytes=target.stat().st_size,new_historical_return_evaluations=0)
with (OUT/'package-validation-13.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
print(json.dumps(result),flush=True)
