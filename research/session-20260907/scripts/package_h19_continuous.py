"""Package the actual guarded replay, its evidence and independently rerun it."""
from collections import Counter
from datetime import datetime,timezone
import hashlib,json,os,shutil,subprocess,sys,zipfile
from pathlib import Path

root=Path(__file__).resolve().parents[1];repo=root/'work/stocks-predictor'
base=root/'work/h19-continuous-bundle';inputs=base/'inputs'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
pkg=base/'stocks_predictor';pkg.mkdir(exist_ok=True)
(pkg/'__init__.py').write_text('"""Standalone, stdlib-only continuous research slice of stocks-predictor."""\n',encoding='utf-8')
for name in ('retail_cash.py','continuous_cash.py','continuous_research.py'):
    shutil.copy2(repo/'stocks_predictor'/name,pkg/name)
srcdir=base/'sources';srcdir.mkdir(exist_ok=True)
source_dirs=[root/'work/h19-cash-expanded-source',root/'work/h19-tax-source',
    root/'work/h19-cash-closure-source',root/'work/source-acquisition',root/'work/profit-cash-source',
    root/'work/value-event-terms',root/'work/h19-selected-dates-v3-bundle/sources',
    root/'work/h19-cash-replay-8f9e8375c77c/sources']
refs=[]
def walk(x):
    if isinstance(x,dict):
        name=x.get('source_file',x.get('file'));digest=x.get('source_sha256',x.get('sha256'))
        if isinstance(name,str) and isinstance(digest,str) and len(digest)==64:refs.append((name,digest))
        for value in x.values():walk(value)
    elif isinstance(x,list):
        for value in x:walk(value)
for name in ('reviewed-payment-dates.json','corporate-primary-findings.json','tax-calendar.json','cash-events.json'):
    walk(read(inputs/name))
missing=[];copied=[]
for name,digest in sorted(set(refs)):
    candidates=[Path(name)] if Path(name).is_absolute() else [d/name for d in source_dirs]
    found=next((p for p in candidates if p.is_file() and sha(p)==digest),None)
    if found is None:missing.append({'file':name,'sha256':digest});continue
    target=srcdir/(digest[:12]+'-'+found.name)
    shutil.copy2(found,target);copied.append({'referenced_name':name,'packaged_path':str(target.relative_to(base)).replace('\\','/'),'sha256':digest})
write(base/'SOURCE_FILES.json',{'copied':copied,'unresolved_raw_copies':missing,
    'coverage_is_not_certified_by_copying_source_files':True})

research=base/'research-scripts';research.mkdir(exist_ok=True)
for name in ('prepare_h19_continuous_quotes.py','audit_h19_continuous_quote_coverage.py',
 'prepare_h19_bonus_quotes.py','reconcile_h19_credit_bulletins.py','complete_h19_tax_calendar.py',
 'record_h19_corporate_findings.py','build_h19_continuous_evidence.py','cash_research_fetch.py',
 'acquire_h19_tax_calendar.py','acquire_h19_tax_pdf_gaps.py','extract_h19_tax_pdf_dates.py'):
    shutil.copy2(root/'work'/name,research/name)
verification=base/'verification';verification.mkdir(exist_ok=True)
for name in ('h19-continuous-tests.log','h19-continuous-lint.log','h19-continuous-pyright.log',
             'h19-continuous-wheel.log','h19-continuous-coverage.log'):
    p=root/'work'/name
    if p.exists():shutil.copy2(p,verification/name)
shutil.copy2(root/'work/h19-continuous-external-tests.log',verification/'h19-continuous-external-tests.log')
tests=base/'tests';tests.mkdir(exist_ok=True)
for name in ('test_retail_cash.py','test_continuous_cash.py','test_continuous_research.py'):
    shutil.copy2(repo/'tests'/name,tests/name)
(tests/'__init__.py').write_text('',encoding='utf-8')
(tests/'conftest.py').write_text(
    'import sys\nfrom pathlib import Path\nsys.path.insert(0, str(Path(__file__).resolve().parents[1] / "stocks_predictor"))\n',encoding='utf-8')
(base/'RODAR_H19.ps1').write_text('''$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    py -3.13 -m stocks_predictor.continuous_research --inputs ./inputs --output ./RESULTADO_H19.json
    $h19ExitCode = $LASTEXITCODE
    if ($h19ExitCode -eq 2) { Write-Host 'Dados incompletos: auditoria concluida, lucro nao calculado. Consulte RESULTADO_H19.json.' }
    exit $h19ExitCode
} finally { Pop-Location }
''',encoding='utf-8')
readme='''# H19: execução contínua auditada

Estado atual: **NO_GO para operar. Lucro líquido não validado.**

Este pacote contém o programa de simulação contínua e o cadastro real de
evidências. Ao rodar com os dados atuais, o programa gera uma auditoria e
termina com código 2 porque faltam evidências. Não gera um backtest parcial,
não substitui dividendos ausentes por zero e não envia ordens.

No PowerShell, dentro desta pasta:

```powershell
py -3.13 -m stocks_predictor.continuous_research --inputs ./inputs --output ./RESULTADO_H19.json
```

Também pode executar `RODAR_H19.ps1`. Python 3.13 global; nenhuma instalação
de biblioteca é necessária para essa execução. O pacote é um recorte de
pesquisa do projeto, não uma cópia do sistema operacional completo.

O código 0 só ocorre quando ambas as carteiras completam todos os casos.
Código 2 significa evidência incompleta. Código 1 significa entrada inválida
ou falha de execução. A saída distingue esses estados e nunca chama bloqueio
de lucro zero. Os casos registrados usam R$5 mil/R$10 mil e custos hipotéticos
de 0,18%/0,36% por lado; as seleções trimestrais permanecem congeladas.

`inputs/evidence.json` enumera intervalos e eventos pendentes.
`inputs/corporate-primary-findings.json` registra as novas constatações.
`inputs/SHA256.json` protege os arquivos usados pelo programa.
`SHA256.json` lista os arquivos deste pacote, e `SOURCE_FILES.json` localiza
as cópias das fontes. Um hash garante integridade, não completude econômica.

Os testes são sintéticos e podem ser executados com pytest, se já disponível:
`py -3.13 -m pytest tests -q`. Os lucros conhecidos desses testes não são
resultados de H19. Os scripts em research-scripts documentam a preparação e
usam os caminhos de pesquisa originais; não são necessários para rodar o pacote.

Não há configuração, segredo, conta de corretora ou credencial no pacote.
'''
(base/'LEIA-ME.md').write_text(readme,encoding='utf-8')
git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
write(base/'BUILD.json',{'validated_source_commit':git_head,'created_at_utc':datetime.now(timezone.utc).isoformat(),
    'original_source_module_hashes':{n:sha(pkg/n) for n in ('retail_cash.py','continuous_cash.py','continuous_research.py')},
    'no_runtime_dependencies_for_replay':True,'new_historical_returns':0})
manifest={str(p.relative_to(base)).replace('\\','/'):sha(p) for p in sorted(base.rglob('*'))
          if p.is_file() and '__pycache__' not in p.parts and p.name not in ('SHA256.json','RESULTADO_H19.json')}
# The input manifest itself is also protected by the outer manifest.
manifest['inputs/SHA256.json']=sha(inputs/'SHA256.json')
write(base/'SHA256.json',manifest)
archive=root/'outputs/STOCKS_H19_EXECUCAO_CONTINUA_AUDITADA.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for name in [*sorted(manifest),'SHA256.json']:z.write(base/name,name)
fresh=root/'work'/('h19-continuous-reproduced-'+sha(archive)[:12]);fresh.mkdir(exist_ok=True)
with zipfile.ZipFile(archive) as z:z.extractall(fresh)
for name,digest in read(fresh/'SHA256.json').items():assert sha(fresh/name)==digest,name
env=dict(os.environ);env.pop('PYTHONPATH',None);env['PYTHONUTF8']='1'
command=[sys.executable,'-m','stocks_predictor.continuous_research','--inputs','inputs','--output','RESULTADO_H19.json']
first=subprocess.run(command,cwd=fresh,env=env,capture_output=True,text=True,encoding='utf-8')
assert first.returncode==2,(first.returncode,first.stdout,first.stderr)
digest=sha(fresh/'RESULTADO_H19.json')
second=subprocess.run(command,cwd=fresh,env=env,capture_output=True,text=True,encoding='utf-8')
assert second.returncode==2 and sha(fresh/'RESULTADO_H19.json')==digest
shutil.copy2(fresh/'RESULTADO_H19.json',root/'outputs/H19_EXECUCAO_CONTINUA_AUDITORIA.json')
receipt={'source_commit':git_head,'zip_sha256':sha(archive),'zip_bytes':archive.stat().st_size,
    'payload_files_verified':len(manifest),'source_files_copied':len(copied),'unresolved_raw_source_copies':missing,
    'replay_exit_codes':[first.returncode,second.returncode],'identical_replays':True,'result_sha256':digest,
    'real_historical_pnl_computed':False,'new_return_evaluations':0,'source_directory':str(fresh),
    'status':'REPRODUCED_EVIDENCE_BLOCK_NO_VALIDATED_PROFIT'}
write(root/'outputs/H19_EXECUCAO_CONTINUA_REPRODUCAO.json',receipt)
print(json.dumps(receipt,ensure_ascii=False,indent=2))
