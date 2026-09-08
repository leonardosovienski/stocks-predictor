"""Package immutable inputs and a dependency-free offline numerical replay."""
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parent.parent
WORK=ROOT/'work';OUT=ROOT/'outputs';REPO=WORK/'stocks-predictor'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
base=OUT/'STOCKS_REORGANIZACOES_TESTADAS.zip'
if digest(base)!='e5e8b429ca89c97421ef248641ad680993ef723803d070acc621cb65867d4f64':raise ValueError('Changed base package')
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
archive=WORK/f'profit-repository-{head[:12]}.zip'
subprocess.run(['git','archive','--format=zip','--output',str(archive),'HEAD'],cwd=REPO,check=True)
files={
    'rodar_validacao.py':WORK/'profit_bundle_runner.py',
    'validator/profit_validation.py':REPO/'stocks_predictor/profit_validation.py',
    'validator/bootstrap.py':REPO/'vendor/predictor_core/measurement/bootstrap.py',
    'validator/test_profit_validation.py':REPO/'tests/test_profit_validation.py',
    'audit/profit-validation-tests.log':WORK/'profit-validation-tests.log',
    'audit/profit-validation-coverage.log':WORK/'profit-validation-coverage.log',
    'audit/profit-validation-observation.log':WORK/'profit-validation-observation.log',
    'audit/repository.zip':archive,
    'protocol.json':REPO/'docs/research/2026-09-07-profit-validation-protocol.json',
}
for p in OUT.glob('VALIDACAO_*STOCKS*.json'):files['results/'+p.name]=p
for name in ('VALIDACAO_LUCRO_AUDITORIA.json','VALIDACAO_LUCRO_STOCKS_RESULTADO.md'):
    files['results/'+name]=OUT/name
for directory in ('profit-cash-source','profit-fractional-source','profit-opportunity-source'):
    for p in sorted((WORK/directory).iterdir()):
        if p.is_file():files['sources/'+directory+'/'+p.name]=p
cash=read(OUT/'VALIDACAO_PROVENTOS_AMPLIADA_STOCKS_V2.json')
source_paths=set(cash['source_sha256'])|set(cash['supplement_source_sha256'])
for name in source_paths:
    p=Path(name)
    if p.parent==WORK/'source-acquisition':
        files['sources/original/'+p.name]=p
        meta=p.with_suffix('.source.json')
        if meta.exists():files['sources/original/'+meta.name]=meta
        if p.name.endswith('-cash-all.json'):
            prefix=p.name.removesuffix('-all.json')
            for page in p.parent.glob(prefix+'-*.json'):files['sources/original/'+page.name]=page
for name in ('register_profit_validation.py','run_profit_validation.py','audit_profit_sources.py',
             'acquire_profit_cash_gaps.py','acquire_profit_historical_cash.py','acquire_two_cash_names.py',
             'validate_expanded_profit_cash.py','audit_fractional_quotes.py','audit_profit_opportunity_cost.py'):
    files['preparation/'+name]=WORK/name
readme=WORK/'profit-bundle-readme.txt'
readme.write_text('STOCKS - VALIDACAO DE LUCRO\n\nPython 3.13, somente biblioteca padrao.\n'
    'Execute rodar_validacao.py --output-dir CAMINHO_NOVO\n'
    'Reproduz as quatro coortes anteriores e os 12 cenarios de preco/risco, com bootstrap.\n'
    'Confere hashes de todos os arquivos. Nao instala pacotes, nao acessa rede, nao envia ordens.\n'
    'Scripts em preparation documentam a aquisicao/auditoria no workspace original; nao sao chamados pelo replay.\n'
    'A validacao numerica NAO demonstra lucro liquido; proventos, execucao e impostos ainda incompletos.\n',encoding='utf-8')
files['LEIA-ME.txt']=readme
target=OUT/'STOCKS_VALIDACAO_LUCRO_TESTADA.zip';hashes={}
with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    with zipfile.ZipFile(base) as old:
        for name in old.namelist():
            if name.endswith('/'):continue
            data=old.read(name);dest='baseline/'+name
            z.writestr(dest,data);hashes[dest]=hashlib.sha256(data).hexdigest()
    for name,path in sorted(files.items()):
        z.write(path,name);hashes[name]=digest(path)
    manifest={'repository_head':head,'tested_code_commit':'28cf87e1819d25eb031067d6c707fa8519171953',
              'test_count':539,'tests_seconds':153.65,'files':hashes,'profit_claim':False}
    z.writestr('validation-manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2))
sha=digest(target)
launcher=OUT/'RODAR_VALIDACAO_LUCRO_STOCKS.py'
script='''"""Verifica, extrai e reproduz offline a validacao Stocks. Python 3.13."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parent
PACKAGE=ROOT/'STOCKS_VALIDACAO_LUCRO_TESTADA.zip'
EXPECTED='PACKAGE_HASH'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output-dir',type=Path,default=ROOT.parent/'work/profit-validation-reproduction')
parser.add_argument('--verify-only',action='store_true')
args=parser.parse_args()
with PACKAGE.open('rb') as stream:
    if hashlib.file_digest(stream,'sha256').hexdigest()!=EXPECTED:raise ValueError('Pacote alterado')
base=ROOT.parent/'work'/('profit-validation-ready-'+EXPECTED[:12])
if not base.exists():
    base.mkdir(parents=True)
    with zipfile.ZipFile(PACKAGE) as z:
        for name in z.namelist():
            if not (base/name).resolve().is_relative_to(base.resolve()):raise ValueError('Caminho inseguro no pacote')
        z.extractall(base)
    (base/'.extraction-complete').write_text(EXPECTED,encoding='utf-8')
elif not (base/'.extraction-complete').exists():raise ValueError('Extracao anterior incompleta; use uma pasta nova')
command=[sys.executable,str(base/'rodar_validacao.py'),'--output-dir',str(args.output_dir.resolve())]
if args.verify_only:command.append('--verify-only')
subprocess.run(command,check=True)
'''.replace('PACKAGE_HASH',sha)
with launcher.open('x',encoding='utf-8') as f:f.write(script)
summary={'package':target.name,'sha256':sha,'bytes':target.stat().st_size,'files':len(hashes)+1,
         'repository_head':head,'tested_code_commit':manifest['tested_code_commit'],'profit_claim':False}
with (OUT/'VALIDACAO_LUCRO_PACOTE_MANIFESTO.json').open('x',encoding='utf-8') as f:json.dump(summary,f,indent=2)
print(json.dumps(summary,indent=2))
