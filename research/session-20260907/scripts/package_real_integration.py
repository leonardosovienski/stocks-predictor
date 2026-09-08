from pathlib import Path
import hashlib,json,subprocess,zipfile,datetime
root=Path.cwd();out=root/'outputs';repo=root/'work/stocks-predictor';sources=root/'work/source-acquisition'
code=out/'stocks-testes-reais-codigo.zip';patch=out/'stocks-testes-reais.patch'
subprocess.run(['git','archive','--format=zip','--output',str(code),'HEAD'],cwd=repo,check=True)
patch.write_bytes(subprocess.check_output(['git','diff','--binary','ce94aeecd2f7b78308cdb09b4a22ba2a06feea70','HEAD'],cwd=repo))
files={}
def add(p,name=None):files[name or str(p.relative_to(root)).replace('\\','/')]=p
for p in (code,patch,out/'TESTES_REAIS_STOCKS.md'):add(p)
for p in out.glob('real-integration-*.json'):
 if p.name not in {'real-integration-delivery-manifest.json','real-integration-package-validation.json'}:add(p)
add(out/'stocks-testes-reais.bundle')
for p in out.glob('real-integration-*.txt'):add(p)
add(root/'work/stocks-history-2016-2026.db');add(root/'work/stocks-tested-real-v2-20260907.db')
add(root/'work/real-integration-wheel/stocks_predictor-0.1.0-py3-none-any.whl')
for p in (root/'work/runtime').rglob('*'):
 if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':add(p)
for p in sources.glob('fca_cia_aberta_*'):add(p)
for p in sources.glob('dfp_cia_aberta_2023*'):add(p)
for doc in ('133944','134335','134790'):
 for p in sources.glob(f'cvm-capital-session-{doc}.*'):add(p)
for p in sources.glob('engi-bonus-2025.*'):add(p)
for prefix in ('ri-bbas','ri-abev','ri-engi','b3-cvm1023-','b3-cvm23264-','b3-cvm15253-'):
 for p in sources.glob(prefix+'*'):add(p)
for name in ('reconciled-cash-events.csv','reconciled-cash-coverage.json','reconciled-cash-import.json'):add(out/name)
for name in ('verify_real_copy.py','verify_real_protected.py','inspect_state.py','smoke_real_wheel.py'):add(root/'work'/name)
# Include source checkout files as well as an immutable git archive so paths in
# the recorded command work immediately after extracting this delivery.
with zipfile.ZipFile(code) as z:
 code_members={i.filename:z.read(i.filename) for i in z.infolist() if not i.is_dir()}
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
manifest={'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'package_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),'tested_code_commit':'5c09c7b8ffebefef00467cbab12481f3535a7837','tests_passed':463,'real_controls_passed':36,'runtime_dependencies_added':[],'files':{name:{'bytes':p.stat().st_size,'sha256':digest(p)} for name,p in files.items()},'checkout_files':{name:hashlib.sha256(b).hexdigest() for name,b in code_members.items()}}
mp=out/'real-integration-delivery-manifest.json';mp.write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8');add(mp)
readme='''PACOTE DE TESTES REAIS STOCKS — 2026-09-07
Resultado: 463 testes automatizados e 36 controles reais aprovados. H17-H19 ainda não executadas.
Leia outputs/TESTES_REAIS_STOCKS.md para limites e fontes.
Os testes já foram executados; não há ação manual necessária para esta entrega.
Para reprodução, extraia em uma pasta nova. O código exportado está em work/stocks-predictor. Para executar com identidade Git preservada, clone o bundle local como indicado abaixo.
O pacote contém o banco de entrada original e a cópia testada. Escolha novos nomes de saída.
No PowerShell, a partir da pasta extraída, com Python 3.13 e PyYAML disponíveis:
git clone outputs/stocks-testes-reais.bundle work/stocks-replay
$env:PYTHONPATH = (Join-Path (Get-Location) 'work/runtime')
py -3.13 work/stocks-replay/tools/test_real_integration.py --source-db work/stocks-history-2016-2026.db --output-db work/reteste.db --sources work/source-acquisition --report outputs/reteste.json
Esse comando repete os 36 controles; não faz backtest de H17-H19. Não usa rede nem corretora.
O clone offline foi testado e reproduziu os 36 controles. A suíte completa de pytest também requer as dependências de desenvolvimento do pyproject.toml e um checkout Git limpo. O zip de código não contém .git.
O patch aplica-se ao commit ce94aeecd2f7b78308cdb09b4a22ba2a06feea70 do complemento anterior.
O manifesto registra hashes dos dados e código. A aquisição integral anterior continua no pacote stocks-complemento-fontes.zip.
'''
package=out/'stocks-testes-reais.zip'
print('Packaging',len(files),'files plus',len(code_members),'checkout files',flush=True)
with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 z.writestr('LEIA-ME.txt',readme)
 for name,p in files.items():z.write(p,name)
 for name,b in code_members.items():z.writestr('work/stocks-predictor/'+name,b)
print('Package bytes',package.stat().st_size,flush=True)
with zipfile.ZipFile(package) as z:
 assert z.testzip() is None
 for doc in ('133944','134335','134790'):
  key=f'tests/fixtures/real_integration/capital-{doc}.html'
  assert hashlib.sha256(z.read('work/stocks-predictor/'+key)).hexdigest()==manifest['checkout_files'][key]
 for name in ('work/stocks-history-2016-2026.db','work/stocks-tested-real-v2-20260907.db'):
  with z.open(name) as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
  assert actual==manifest['files'][name]['sha256']
 count=len(z.infolist())
check={'file':package.name,'bytes':package.stat().st_size,'sha256':digest(package),'entries':count,'crc_valid':True,'database_hashes_match':True,'capital_fixture_hashes_match':True}
(out/'real-integration-package-validation.json').write_text(json.dumps(check,indent=2),encoding='utf-8')
print(json.dumps(check),flush=True)
