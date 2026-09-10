"""Local R8 delivery; run only after final-head and merged-main CI succeed."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

root=Path('C:/STOCKS/stocks-predictor')
work=Path('C:/STOCKS/work/operational-infra-r8-20260910')
outputs=Path('C:/STOCKS/outputs')
closure=json.loads((work/'closure.json').read_text(encoding='utf-8'))
if any(closure[key]['conclusion']!='success' for key in ('final_head_ci','main_ci')):
    raise ValueError('both final head and main must pass')
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
if head!=closure['merge_sha'] or subprocess.check_output(['git','status','--porcelain'],cwd=root).strip():
    raise ValueError('delivery requires the clean verified merge')
bundle=work/'STOCKS_R8_HISTORY.bundle'
if bundle.exists():
    raise FileExistsError(bundle)
subprocess.run(['git','bundle','create',str(bundle),'HEAD','main'],cwd=root,check=True)
subprocess.run(['git','bundle','verify',str(bundle)],cwd=root,check=True)
clone=work/'delivery-clone-check'
subprocess.run(['git','clone','--no-checkout',str(bundle),str(clone)],cwd=work,check=True)
if subprocess.check_output(['git','rev-parse','HEAD'],cwd=clone,text=True).strip()!=head:
    raise ValueError('bundle clone does not recover the verified head')
subprocess.run(['git','cat-file','-e','c259ff64771a6c560ddb4aadac6bf81301c3066a:tools/audit_registry.py'],cwd=clone,check=True)

def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()

def checked_zip(path, expected):
    if sha(path)!=expected.removeprefix('sha256:'):
        raise ValueError('downloaded artifact differs from GitHub digest: '+str(path))
    return zipfile.ZipFile(path)

artifact=closure['distribution_artifact']
with checked_zip(work/artifact['local_file'],artifact['digest']) as z:
    names=[n for n in z.namelist() if n.endswith('.whl')]
    if len(names)!=1:
        raise ValueError('one production wheel required')
    wheel=work/Path(names[0]).name
    with wheel.open('xb') as f:
        f.write(z.read(names[0]))
    build=json.loads(z.read('build-receipt.json'))
    if build['head']!=head or build['distributions'][wheel.name]!=sha(wheel):
        raise ValueError('wheel receipt must refer to verified main')
    build_path=work/'FINAL_BUILD_RECEIPT.json'
    with build_path.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(build,f,indent=2)
        f.write('\n')
report=f'''# Infraestrutura de pesquisa — entrega R8

Concluída e integrada para pesquisa em lote em um host, com SQLite em disco local.
PR79: https://github.com/leonardosovienski/stocks-predictor/pull/79
Complemento do scanner, PR80: https://github.com/leonardosovienski/stocks-predictor/pull/80
Merge: `{head}`.

- CI do commit final: {closure['final_head_ci']['url']}.
- CI de main: {closure['main_ci']['url']}.
- Cada Python 3.13/3.14: 891 testes ativos, 17 arquivados, 63 subtests, sem falhas.
- Cobertura geral 80%/79%; armazenamento operacional 92%, CLI 89%.
- Lint, tipagem, scanner, registros históricos, builds idênticos e wheel instalado aprovados.
- O scanner examina a árvore versionada inteira após merges; o scan vazio encontrado na CI226 foi corrigido.
- Concorrência, replay, leitores, WAL, interrupção abrupta, corrupção, timeout e restauração testados.
- 250 mil registros sintéticos e 55.986 preços reais reconciliados; 12 bancos originais preservados.

## Uso e reprodução

Entrada: `python -m stocks_predictor`; no checkout: `python main.py ops`.
O runbook completo está em `docs/engineering/2026-09-10-r8/RUNBOOK.md`.
O ZIP contém histórico Git completo, wheel, fonte real e recibo de aquisição,
backup validado, relatórios, logs e manifesto de hashes. Clone o bundle em um
diretório novo: `git clone STOCKS_R8_HISTORY.bundle projeto`.
Use Linux/Python 3.13 ou 3.14 e dependências do lock conforme o runbook/CI.
O ZIP não instala Python/Core neste Windows nem inicia operações financeiras.
O banco de fontes usa schema próprio; não direcionar backtests legados a ele.

Para repetir o teste real no clone, com diretório de saída novo:

```bash
python tools/operational_validation.py --output /dados/nova-validacao --rows 55986 \\
  --archive /entrega/source/COTAHIST_A2026.ZIP \\
  --receipt /entrega/source/COTAHIST_A2026.ZIP.receipt.json
```

Backup do banco real: `real-backup/`. Restaure em diretório novo conforme o runbook.
Esta entrega é um ponto de recuperação local; não há cópia externa nem rotina
de backup agendada. Os testes não certificam falha física de hardware/energia,
ambiente distribuído ou negociação ao vivo. O histórico Git e código não substituem
os outros bancos e fontes externos de experimentos anteriores, preservados em C:/STOCKS.

## Achados anteriores e limites

O consolidado R7 completo está incluído, preservando 75 achados, 50 líquidos,
22 datas e 28 eventos societários. A R8 acrescenta a entrada operacional,
backup/restauração, ensaios concorrentes e de falha, e atestados separados por versão.
Os recibos de tentativas conservam as falhas originais; o fechamento atual e a
resolução das falhas do scanner ficam em CI_CLOSURE.json e nos logs finais.
L22/M10 agora têm ensaios concorrentes e capacidade finita; continuam sem garantia
de capacidade irrestrita ou atribuição de memória por alocador. L10/L23 têm integração
operacional, sem certificar independência, datas reais ou migrar identidades históricas.
L24/M12 ganham reprodução deste fluxo com fonte e histórico; as demais bases externas
continuam necessárias para reproduzir todos os experimentos antigos.

Os dados econômicos continuam incompletos, custos/prazo pessoais desconhecidos e
observação prospectiva não concluída. Capital confirmado R$5.000. Lucro integral/futuro
não validado, capital não habilitado. Esta entrega não declara o pedido inicial inteiro
concluído nem toda combinação do código testada.
'''
md=outputs/'INFRAESTRUTURA_R8_VALIDACAO_20260910.md'
with md.open('x',encoding='utf-8',newline='\n') as f:
    f.write(report)
files={
    'LEIA-ME.md':md, 'STOCKS_R8_HISTORY.bundle':bundle,
    'wheel/'+wheel.name:wheel, 'wheel/BUILD_RECEIPT.json':build_path,
    'CI_CLOSURE.json':work/'closure.json',
    'source/COTAHIST_A2026.ZIP':Path('C:/STOCKS/work/gap-resolution-r6-20260910/raw/COTAHIST_A2026.ZIP'),
    'source/COTAHIST_A2026.ZIP.receipt.json':Path('C:/STOCKS/work/gap-resolution-r6-20260910/raw/COTAHIST_A2026.ZIP.receipt.json'),
    'R7/CONSOLIDADO.md':outputs/'CONSOLIDADO_FALHAS_PENDENCIAS_MELHORIAS_20260910_V3.md',
    'R7/CONSOLIDADO.json':outputs/'CONSOLIDADO_FALHAS_PENDENCIAS_MELHORIAS_20260910_V3.json',
}
source_receipt=json.loads(files['source/COTAHIST_A2026.ZIP.receipt.json'].read_text(encoding='utf-8'))
real_receipt=json.loads((root/'docs/engineering/2026-09-10-r8/evidence/real.json').read_text(encoding='utf-8'))
if sha(files['source/COTAHIST_A2026.ZIP']) != source_receipt['sha256'] or source_receipt['sha256'] != real_receipt['source_sha256']:
    raise ValueError('packaged source no longer matches validated acquisition')
backup=work/'real-cotahist-v2/backup'
backup_receipt=json.loads((backup/'manifest.json').read_text(encoding='utf-8'))
if sha(backup/'snapshot.sqlite') != backup_receipt['sha256'] or backup_receipt['inspection'] != real_receipt['inspection']:
    raise ValueError('packaged backup no longer matches validated data')
for folder,prefix in [(root/'docs/engineering/2026-09-10-r8','docs/engineering/2026-09-10-r8'),
                      (work/'real-cotahist-v2/backup','real-backup')]:
    for p in folder.rglob('*'):
        if p.is_file():
            files[prefix+'/'+p.relative_to(folder).as_posix()]=p
for p in work.glob('*.log'):
    files['logs/'+p.name]=p
for artifact in closure['quality_and_operations_artifacts']:
    p=work/artifact['local_file']
    with checked_zip(p,artifact['digest']) as zipped:
        if artifact['name']=='complete-tree-secrets':
            baseline=json.loads(zipped.read('stocks-current-tree.sarif'))
            control=json.loads(zipped.read('stocks-scan-control.sarif'))
            if baseline['runs'][0]['results'] or not control['runs'][0]['results']:
                raise ValueError('full-tree baseline/control evidence differs from closure')
        elif artifact['name'].startswith('operations-'):
            validation=json.loads(zipped.read('validation.json'))
            if validation['status']!='PASS' or validation['installed_wheel'] is not True or validation['rows']!=250000:
                raise ValueError('installed operational artifact failed acceptance')
    files['ci-artifacts/'+p.name]=p
manifest={'schema_version':1,'created_at':datetime.now(timezone.utc).isoformat(),
          'merge_sha':head,'files':[{'path':name,'bytes':path.stat().st_size,'sha256':sha(path)}
                                   for name,path in sorted(files.items())],
          'engineering_scope_complete':True,'all_initial_request_items_closed':False,
          'capital_enabled':False,'profit_certified':False}
package=outputs/'INFRAESTRUTURA_R8_EXECUTAVEL_20260910.zip'
with zipfile.ZipFile(package,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as zipped:
    for name,path in sorted(files.items()):
        method=zipfile.ZIP_STORED if path.suffix in ('.zip','.bundle','.whl') else zipfile.ZIP_DEFLATED
        zipped.write(path,name,compress_type=method)
    zipped.writestr('MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
with zipfile.ZipFile(package) as zipped:
    if set(zipped.namelist()) != set(files)|{'MANIFEST.json'}:
        raise ValueError('delivery population changed')
    for item in manifest['files']:
        with zipped.open(item['path']) as f:
            if hashlib.file_digest(f,'sha256').hexdigest()!=item['sha256']:
                raise ValueError('delivery member identity failed')
receipt={**manifest,'status':'PASS','archive':str(package),'archive_bytes':package.stat().st_size,
         'archive_sha256':sha(package),'report':str(md),'report_sha256':sha(md)}
with (outputs/'INFRAESTRUTURA_R8_VALIDACAO_20260910.receipt.json').open('x',encoding='utf-8',newline='\n') as f:
    json.dump(receipt,f,indent=2)
    f.write('\n')
print(json.dumps({k:receipt[k] for k in ('status','archive_bytes','archive_sha256','engineering_scope_complete','all_initial_request_items_closed')},indent=2))
