from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parent.parent
REPO=ROOT/'work/stocks-predictor'
DEST=ROOT/'work/value-ready-bundle'
DEST.mkdir(exist_ok=True)


def copy(source,relative):
    target=DEST/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)


def tree(source,relative):
    for f in source.rglob('*'):
        if f.is_file() and '__pycache__' not in f.parts:copy(f,Path(relative)/f.relative_to(source))


for name in ('__init__','discovery_h17','discovery_value','discovery_value_repair','disclosed_accounting',
             'document_panel','source_history','cvm_pit','ingest_cvm'):
    copy(REPO/f'stocks_predictor/{name}.py',f'code/stocks_predictor/{name}.py')
copy(ROOT/'work/value_bundle_runner.py','rodar_pesquisa.py')
tree(ROOT/'work/h17-run-pack-v2/data','original')
tree(ROOT/'work/h17-run-pack-v2/sources','event-sources')
tree(ROOT/'work/value-capital-source','capital')
tree(ROOT/'work/value-measurement-source','repaired')
tree(ROOT/'work/value-accounting-excerpts','accounting-excerpts')
for p in REPO.glob('docs/research/2026-09-07-value-*'):copy(p,'protocols/'+p.name)
for name in ('h18-h19-first-observation.json','h18-h19-repaired-observation.json'):
    copy(ROOT/'outputs'/name,'observations/'+name)
for name in ('H18_H19_RESULTADO_TESTADO.md','H18_H19_LACUNAS_RESTANTES.json','DECISAO_PESQUISA_STOCKS.json',
             'REVISAO_H1_H16_APOS_CORRECOES.json'):
    copy(ROOT/'outputs'/name,'reports/'+name)
for name in ('value-full-tests.log','value-coverage.log','value-repair-tests.log','value-repair-coverage.log',
             'value-source-integrity.json','value-feature-coverage.json'):
    copy(ROOT/'work'/name,'audit/'+name)
for name in ('fetch_disclosed_capital.py','derive_value_accounting.py','prepare_value_measurement_repair.py',
             'register_value_protocol.py','register_value_repair.py','review_prior_families.py'):
    copy(ROOT/'work'/name,'preparation-record/'+name)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
subprocess.run(['git','archive','--format=zip','HEAD','-o',str(DEST/('audit/repository-'+head[:12]+'.zip'))],cwd=REPO,check=True)
(DEST/'LEIA-ME.md').write_text('''# Pesquisa Stocks — H18 e H19

Este pacote já foi executado. As quatro configurações e sua correção ficaram
NO_PRIORITY_UPGRADE. H19 tem sinal exploratório condicional; não há lucro líquido
demonstrado, ordem de compra ou GO.

Com Python 3.13, execute `py -3.13 rodar_pesquisa.py --output-dir <pasta-nova>`.
Não requer instalação nem acesso à rede. `--verify-only` verifica os arquivos,
reprocessa 745 capitais originais e rederiva a atribuição contábil de 750 documentos.
A execução normal também reproduz as quatro configurações nas duas versões e
compara todas as seleções, fatores, retornos e resumos com as saídas preservadas.

Os bancos SQLite só são lidos. Os resultados novos são escritos na pasta escolhida.
A reprodução idêntica não é evidência independente nem nova tentativa adaptativa.

`original/` contém o extrato usado na primeira observação. `repaired/` preserva
as cotações à vista em todas as classificações BDI, incluindo recuperação judicial,
e a correção explícita das duas duplicações de bonificação. As linhas originais
COTAHIST e hashes dos ZIPs de origem estão juntos. `capital/` contém as páginas
originais CVM e metadados. `accounting-excerpts/` contém 113.827 linhas de contas
dos documentos usados, com URL e hashes dos ZIPs oficiais e dos membros originais.
Os ZIPs integrais CVM e COTAHIST podem ser recuperados nas fontes registradas; os
extratos aqui não substituem o acervo completo para pesquisa de outro universo.

`preparation-record/` é a trilha dos scripts da aquisição original, com caminhos
daquela sessão; o ponto de entrada portátil é `rodar_pesquisa.py`. O arquivo de
repositório em `audit/` preserva implementação, testes e histórico documental no HEAD
de entrega. O pacote mínimo importa apenas os módulos de diagnóstico sem Core.

As demais limitações, o resultado negativo do gate, as 35 lacunas restantes e a
decisão de pesquisa estão em `reports/H18_H19_RESULTADO_TESTADO.md`.
''',encoding='utf-8')
hashes={}
for p in sorted(DEST.rglob('*')):
    if p.is_file():
        with p.open('rb') as stream:hashes[str(p.relative_to(DEST)).replace('\\','/')]=hashlib.file_digest(stream,'sha256').hexdigest()
(DEST/'manifest.json').write_text(json.dumps({'created_at_utc':datetime.now(timezone.utc).isoformat(),
    'repository_head':head,'tested_code_commit':'2a86e0cf4c6dac53c267390e57235d3ad6b87a80',
    'files_sha256':hashes},ensure_ascii=False,indent=2),encoding='utf-8')
archive=ROOT/'outputs/STOCKS_H18_H19_TESTADOS.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(DEST.rglob('*')):
        if p.is_file():z.write(p,str(p.relative_to(DEST)).replace('\\','/'))
with archive.open('rb') as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
info={'archive':archive.name,'sha256':sha,'bytes':archive.stat().st_size,'files':len(hashes)+1,'repository_head':head}
(ROOT/'outputs/H18_H19_PACOTE_MANIFESTO.json').write_text(json.dumps(info,indent=2),encoding='utf-8')
print(json.dumps(info,indent=2))
