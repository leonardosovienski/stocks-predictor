from pathlib import Path
from datetime import datetime,timezone
import hashlib
import json
import shutil
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parent.parent
REPO=ROOT/'work/stocks-predictor'
DEST=ROOT/'work/reorganization-ready-bundle'
DEST.mkdir(exist_ok=True)
def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def copy(source,relative):
    target=DEST/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
def tree(source,relative):
    for file in source.rglob('*'):
        if file.is_file() and '__pycache__' not in file.parts:copy(file,Path(relative)/file.relative_to(source))
for name in ('__init__','discovery_h17','discovery_value','discovery_value_repair','discovery_reorganizations'):
    copy(REPO/f'stocks_predictor/{name}.py',f'code/stocks_predictor/{name}.py')
copy(ROOT/'work/reorganization_bundle_runner.py','rodar_reorganizacoes.py')
tree(ROOT/'work/value-measurement-source','base')
tree(ROOT/'work/value-successor-source','successors')
protocol=json.loads((REPO/'docs/research/2026-09-07-reorganization-protocol.json').read_text(encoding='utf-8'))
for name in protocol['primary_source_sha256']:
    copy(ROOT/'work/value-event-terms'/name,'terms/'+name)
    if name.endswith('.pdf') and (ROOT/'work/value-event-terms'/name).with_suffix('.txt').exists():
        copy((ROOT/'work/value-event-terms'/name).with_suffix('.txt'),'terms/'+Path(name).with_suffix('.txt').name)
copy(ROOT/'work/value-event-terms/reorganizations.json','terms/reorganizations.json')
copy(REPO/'docs/research/2026-09-07-reorganization-protocol.json','protocol.json')
for name in ('h18-h19-repaired-observation.json','h18-h19-reorganization-observation.json'):
    copy(ROOT/'outputs'/name,'observations/'+name)
for name in ('H18_H19_REORGANIZACOES_RESULTADO.md','H18_H19_REORGANIZACOES_AUDITORIA.json','H19_PROXIMO_TESTE_VIABILIDADE.json'):
    copy(ROOT/'outputs'/name,'reports/'+name)
for name in ('reorganization-tests.log','reorganization-coverage.log','reorganization-observation.log'):
    copy(ROOT/'work'/name,'audit/'+name)
for name in ('download_value_event_sources.py','value-event-sources.json','value-event-sources-more.json',
             'value-event-sources-cvm.json','download_final_terms.py','extend_value_successor_quotes.py',
             'build_value_reorganization_terms.py','check_value_event_inputs.py','value-event-stage-intent.json',
             'register_value_reorganizations.py','assess_next_stocks_test.py','record_reorganization_results.py'):
    copy(ROOT/'work'/name,'preparation-record/'+name)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
subprocess.run(['git','archive','--format=zip','HEAD','-o',str(DEST/('audit/repository-'+head[:12]+'.zip'))],cwd=REPO,check=True)
(DEST/'LEIA-ME.md').write_text('''# Stocks: reorganizações H18/H19

Execute `py -3.13 rodar_reorganizacoes.py --output-dir <pasta-nova>`.
Python 3.13; sem instalação, rede, conta de corretora ou ordens. SQLite somente leitura.
`--verify-only` verifica os hashes; a execução normal também recalcula e compara todos
os membros, resultados e resumos das quatro configurações com a saída preservada.

São preços mais direitos compulsórios, com quantidades teóricas. Não é retorno total
nem lucro líquido. As quatro configurações continuam NO_PRIORITY_UPGRADE. Veja reports/.
As datas de crédito físico ainda desconhecidas são explícitas, assim como direitos de
subscrição marcados a zero e dividendos/JCP ordinários omitidos. Cotações, documentos
originais, termos e protocolo acompanham o pacote. A reprodução não reavalia o sinal
contábil: ela usa as mesmas seleções já reproduzidas no pacote anterior H18/H19.
''',encoding='utf-8')
files={p.relative_to(DEST).as_posix():sha(p) for p in sorted(DEST.rglob('*')) if p.is_file() and p.name!='manifest.json'}
manifest={'created_at_utc':datetime.now(timezone.utc).isoformat(),'repository_commit':head,'files_sha256':files}
(DEST/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
archive=ROOT/'outputs/STOCKS_REORGANIZACOES_TESTADAS.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(DEST.rglob('*')):
        if p.is_file():z.write(p,p.relative_to(DEST).as_posix())
digest=sha(archive)
outer='''"""Extrai e reproduz o pacote de reorganizações Stocks, sem instalar dependências."""
from pathlib import Path
import argparse
import hashlib
import subprocess
import sys
import zipfile

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path)
    parser.add_argument('--verify-only',action='store_true')
    args=parser.parse_args()
    here=Path(__file__).resolve().parent
    archive=here/'STOCKS_REORGANIZACOES_TESTADAS.zip'
    expected='ZIP_SHA'
    with archive.open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
    if actual!=expected:raise ValueError('O ZIP difere do pacote testado')
    destination=here.parent/'work'/('reorganization-ready-'+expected[:12])
    marker=destination/'.extraction-complete'
    if not marker.exists():
        if destination.exists():raise FileExistsError('Extracao incompleta preservada: '+str(destination))
        with zipfile.ZipFile(archive) as z:
            for name in z.namelist():
                if not (destination/name).resolve().is_relative_to(destination.resolve()):
                    raise ValueError('Caminho inseguro no ZIP')
            z.extractall(destination)
        marker.write_text(expected,encoding='utf-8')
    if marker.read_text(encoding='utf-8')!=expected:raise ValueError('Extracao de outro pacote')
    cmd=[sys.executable,str(destination/'rodar_reorganizacoes.py')]
    if args.output_dir:cmd+=['--output-dir',str(args.output_dir.resolve())]
    if args.verify_only:cmd+=['--verify-only']
    raise SystemExit(subprocess.call(cmd))

if __name__=='__main__':main()
'''.replace('ZIP_SHA',digest)
(ROOT/'outputs/RODAR_REORGANIZACOES_STOCKS.py').write_text(outer,encoding='utf-8')
record={'archive':archive.name,'sha256':digest,'bytes':archive.stat().st_size,'files':len(files)+1,'repository_commit':head}
(ROOT/'outputs/REORGANIZACOES_PACOTE_MANIFESTO.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(record,indent=2))
