import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parent.parent
REPO=ROOT/'work/stocks-predictor'
OUT=ROOT/'outputs'

def git(*args):
    return subprocess.check_output(['git',*args],cwd=REPO)

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):
            h.update(b)
    return h.hexdigest()

tests=(OUT/'repair-tests-full.txt').read_text(encoding='utf-8-sig')
match=re.search(r'(\d+) passed in ([0-9.]+)s',tests)
if not match or 'FAILED ' in tests:
    raise RuntimeError('Final tests have not completed successfully.')
tested_commit=git('rev-parse','HEAD').decode().strip()
passed=int(match[1])
seconds=float(match[2])
if passed < 422:
    raise RuntimeError('Expected final package-import regression has not run.')

for name in ('HANDOFF.md','RESEARCH_FREEZE.md','STOCKS_CURRENT_STATE.md'):
    path=REPO/name
    s=path.read_text(encoding='utf-8')
    s=s.replace('47 testes dirigidos passaram; suíte completa será registrada na entrega.',
                f'Suíte completa: **{passed} testes aprovados**, com cobertura; lint e Pyright verdes.')
    path.write_text(s,encoding='utf-8')
doc=REPO/'docs/research/2026-09-07-repairs.md'
s=doc.read_text(encoding='utf-8')
s += f'''

### Resultado final

- **{passed} testes passaram** em {seconds:.2f}s com coverage e Core 3.2.0;
  commit de código testado `{tested_commit}`.
- Ruff aprovado; Pyright: zero erros, zero avisos. Wheel construída e
  importada com sucesso fora do checkout, incluindo os módulos novos.
- Ledger derivado conferido pelo migrador existente: idempotente.
- Cópia demonstrativa do banco real: 3 documentos DFP + 3 FRE de 2023
  (Ambev, Banco do Brasil e Energisa); todas as tabelas históricas iguais
  à origem por contagem e SHA-256 do conteúdo. A origem manteve seu hash.
- As derivações completas de 2023 foram exportadas em JSONL: 475 DFP e
  455 FRE, independentemente do mapeamento demonstrativo de três emissores.
- Nenhum push, investimento, nova tentativa científica ou desempenho
  protegido. A cobertura histórica completa de proventos e as bases
  certificadas das ações permanecem pendentes de fonte, explicitamente.
'''
doc.write_text(s,encoding='utf-8')
git('add','HANDOFF.md','RESEARCH_FREEZE.md','STOCKS_CURRENT_STATE.md','docs/research/2026-09-07-repairs.md')
git('commit','-m','Record repair validation and remaining source-data gaps')
commit=git('rev-parse','HEAD').decode().strip()
shutil.copyfile(doc,OUT/'CORRECOES_STOCKS.md')
patch=OUT/'stocks-correcoes.patch'
patch.write_bytes(git('diff','--binary','d48d05dc590c7e14a9186e7097c048c3020a6a53',commit))
archive=OUT/'stocks-correcoes-codigo.zip'
subprocess.run(['git','archive','--format=zip','--prefix=stocks-predictor/','-o',str(archive),commit],cwd=REPO,check=True)
wheel=ROOT/'work/repair-wheel/stocks_predictor-0.1.0-py3-none-any.whl'
shutil.copyfile(wheel,OUT/wheel.name)

deliverables=['CORRECOES_STOCKS.md','stocks-correcoes.patch','stocks-correcoes-codigo.zip',wheel.name,
              'repair-tests-full.txt','repair-real-validation.json','repair-copy-validation.json',
              'repair-historical-integrity.json','integrity-verification.json','repair-pyright.txt',
              'repair-build.txt','repair-wheel-smoke.txt','repair-coverage.txt','repair-lint.txt',
              'dfp-2023-corrigida.jsonl','fre-2023-documentos.jsonl']
manifest={'commit':commit,'tested_code_commit':tested_commit,'branch':'fix/stocks-cvm-execution-20260907',
          'patch_base':'d48d05dc590c7e14a9186e7097c048c3020a6a53',
          'tests':{'passed':passed,'seconds':seconds,'python':'3.13.14','core':'3.2.0','coverage':'7.16.0',
                   'ruff':'PASS','pyright':'PASS','wheel_build':'PASS','installed_wheel_smoke':'PASS'},
          'pushed':False,'protected_performance_observed':False,
          'operational_database_modified':False,'complete_historical_backfill':False,
          'real_database_copy_scope':'2023, 3 issuers; complete raw 2023 derived separately without ticker inference',
          'remaining_source_gaps':['verified share effective date and price-class equivalence','verified per-security cash events and coverage','full historical rebuild'],
          'sha256':{name:digest(OUT/name) for name in deliverables}}
(OUT/'repair-delivery-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
with zipfile.ZipFile(OUT/'stocks-correcoes.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
    for name in deliverables+['repair-delivery-manifest.json']:
        z.write(OUT/name,name)
    for path in (ROOT/'work/raw').glob('*.zip'):
        z.write(path,'raw/'+path.name)
    z.write(ROOT/'work/stocks-cvm-2023-repaired-example.db','demonstracao/stocks-cvm-2023-repaired-example.db')
    z.write(ROOT/'work/repair-example-map-2023.json','demonstracao/mapa-2023.json')
with zipfile.ZipFile(OUT/'stocks-correcoes.zip') as z:
    assert z.testzip() is None
print(json.dumps({'commit':commit,'tested_code_commit':tested_commit,'passed':passed,
                  'package_bytes':(OUT/'stocks-correcoes.zip').stat().st_size,
                  'package_sha256':digest(OUT/'stocks-correcoes.zip')},indent=2))
assert not git('status','--porcelain').strip()
