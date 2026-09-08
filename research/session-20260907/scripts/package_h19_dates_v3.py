"""Small self-contained replay of the 16-date closure and current evidence gate."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parent.parent
WORK=ROOT/'work'; OUT=ROOT/'outputs'; BASE=WORK/'h19-selected-dates-v3-bundle'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
BASE.mkdir(exist_ok=True)
shutil.copytree(WORK/'h19-retail-bundle/inputs',BASE/'inputs',dirs_exist_ok=True)
for name in ['retail_cash.py','RODAR_H19_CAIXA.py']:
    shutil.copy2(WORK/'h19-retail-bundle'/name,BASE/name)
registry=OUT/'H19_CAIXA_PAGAMENTOS_REVISADOS_V3.json'
shutil.copy2(registry,BASE/'inputs/reviewed-payment-dates.json')
(BASE/'outputs').mkdir(exist_ok=True)
shutil.copy2(OUT/'H19_CAIXA_PAGAMENTOS_REVISADOS_V2.json',BASE/'outputs/H19_CAIXA_PAGAMENTOS_REVISADOS_V2.json')
(BASE/'work/h19-cash-expanded-source').mkdir(parents=True,exist_ok=True)
for name in read(registry)['incremental_review']['source_files']:
    shutil.copy2(WORK/'h19-cash-expanded-source'/name,BASE/'work/h19-cash-expanded-source'/name)
shutil.copy2(WORK/'close_h19_selected_dates.py',BASE/'work/close_h19_selected_dates.py')
(BASE/'LEIA-ME.md').write_text('''# H19 — fechamento das 16 datas e auditoria V3

Esta versão acrescenta a conciliação das 16 datas selecionadas antes pendentes.
Não acrescenta backtest, retorno ou lucro. O código contábil permanece o mesmo
do commit 5e71bc8642cc2b0759e8a1885cab446e315121fd, validado com 558 testes na
rodada anterior. Não foi necessário repetir a suíte para essa atualização de dados.

Execute a auditoria offline com Python 3.13 global, sem instalar bibliotecas:

```powershell
py -3.13 RODAR_H19_CAIXA.py --output H19_CAIXA_EXECUCAO_V3.json
```

O retorno esperado continua sendo código **2**, `BLOCKED_MISSING_EVIDENCE`.
Os quatro testes da primeira compra passam; a carteira histórica completa
ainda não é executada. A lista de pendências usa os pagamentos atualizados.

Para reproduzir separadamente a conciliação das 16 datas:

```powershell
py -3.13 work/close_h19_selected_dates.py
```

Esse comando lê o registro V2 em outputs/ e verifica trechos específicos dos
avisos/atas/boletins e a aritmética das atualizações do Banco do Brasil. Ele
gera outputs/H19_CAIXA_PAGAMENTOS_REVISADOS_V3.json. O resultado deve ser igual
ao registro em inputs/reviewed-payment-dates.json. PDFs primários e respectivas
extrações/metadados estão em work/h19-cash-expanded-source/. Fontes e histórico
mais amplos continuam preservados no pacote V2 anterior.

Nenhum valor ausente é tratado como zero. As datas são apenas uma dimensão:
ainda faltam cobertura completa dos eventos e integração da carteira contínua,
entregas, frações e tratamento fiscal. O arquivo SHA256.json verifica os arquivos
de entrada incluídos; resultados criados pelos comandos não integram o manifesto.
''',encoding='utf-8')
files={p.relative_to(BASE).as_posix():sha(p) for p in sorted(BASE.rglob('*'))
       if p.is_file() and p.name!='SHA256.json' and '__pycache__' not in p.parts}
save(BASE/'SHA256.json',files)
archive=OUT/'STOCKS_H19_DATAS_E_AUDITORIA_V3.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for name in [*files,'SHA256.json']:z.write(BASE/name,name)
fresh=WORK/f'h19-dates-v3-replay-{sha(archive)[:12]}'
fresh.mkdir(exist_ok=False)
with zipfile.ZipFile(archive) as z:z.extractall(fresh)
closed=subprocess.run([sys.executable,'work/close_h19_selected_dates.py'],cwd=fresh,capture_output=True,text=True,encoding='utf-8')
assert closed.returncode==0 and not closed.stderr,closed.stderr
assert (fresh/'outputs/H19_CAIXA_PAGAMENTOS_REVISADOS_V3.json').read_bytes()==registry.read_bytes()
audit=OUT/'H19_CAIXA_EXECUCAO_V3.json'
ran=subprocess.run([sys.executable,'RODAR_H19_CAIXA.py','--output',str(audit)],cwd=fresh,capture_output=True,text=True,encoding='utf-8')
assert ran.returncode==2 and not ran.stderr,ran.stderr
result=read(audit)
assert result['original_queue_summary']['selected_without_candidate_date']==0
assert result['profit'] is None and result['new_historical_return_evaluations']==0
assert all(r['status']=='PASS_ACCOUNTING_ONLY' for r in result['first_entry_smoke'])
verify=dict(archive=archive.name,sha256=sha(archive),bytes=archive.stat().st_size,
    payload_files=len(files),date_reconciliation='PASS_16_PRIMARY_SOURCE_REVIEWS',
    rebuilt_registry_identical=True,registry_sha256=sha(registry),
    audit='PASS_EXPECTED_MISSING_EVIDENCE_EXIT_2',audit_sha256=sha(audit),
    runtime_unchanged=True,prior_runtime_tests=558,runtime_tests_repeated=False,
    new_return_evaluations=0,profit=None,summary=result['original_queue_summary'])
save(OUT/'H19_DATAS_V3_REPRODUCAO.json',verify)
print(json.dumps(verify,indent=2))
