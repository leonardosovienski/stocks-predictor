"""Find public CVM cash notices for the already selected H19 holdings."""
from datetime import date
import csv
import io
import json
from pathlib import Path
import re
import zipfile

ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/'work/h19-cash-expanded-source'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
obs=read(ROOT/'outputs/h18-h19-reorganization-observation.json')
trial=next(t for t in obs['trials'] if t['family']=='H19' and t['holding_months']==3)
ident={m['ticker']:m['cnpj'] for p in trial['periods'] for m in p['members']}
queue=read(ROOT/'outputs/H19_CAIXA_FILA_DE_VALIDACAO.json')['cash_queue']
targets=[]
for r in queue:
    if not r['selected']:continue
    raw=read(Path(r['source_path']))[r['source_row']]
    d=raw['dateApproval'];approval=date(int(d[6:]),int(d[3:5]),int(d[:2])).isoformat()
    targets.append({**r,'cnpj':ident[r['ticker']],'approval_date':approval})
full=[];chosen={}
for p in sorted(BASE.glob('ipe-*.zip')):
    with zipfile.ZipFile(p) as z:
        text=z.read(z.namelist()[0]).decode('latin1')
    for r in csv.DictReader(io.StringIO(text),delimiter=';'):
        cnpj=re.sub(r'\D','',r['CNPJ_Companhia'])
        if cnpj not in set(ident.values()):continue
        text=(r['Assunto']+' '+r['Tipo']).lower()
        if not any(w in text for w in ('dividend','juros','jcp','jscp','provento','remunera')):continue
        full.append(r)
        matched=[]
        for t in targets:
            if t['cnpj']!=cnpj:continue
            delta=(date.fromisoformat(r['Data_Referencia'])-date.fromisoformat(t['approval_date'])).days
            # Source acquisition window only; does not select or evaluate returns.
            if -2<=delta<=40:matched.append({k:t[k] for k in ('ticker','ex_date','value_per_share','action')})
        if not matched or r['Categoria'] not in ('Aviso aos Acionistas','Comunicado ao Mercado','Fato Relevante'):continue
        key=r['Link_Download']
        chosen[key]={**r,'matching_cash_requirements':matched}
docs=list(chosen.values())
for i,r in enumerate(docs):r['local_file']=f"cvm-notice-{i:04d}.pdf"
(BASE/'ipe-cash-index.json').write_text(json.dumps(full,ensure_ascii=False,indent=2),encoding='utf-8')
(BASE/'ipe-selected-notices.json').write_text(json.dumps(docs,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'work/h19-notices-batch.json').write_text(json.dumps([[r['local_file'],r['Link_Download']] for r in docs],indent=2),encoding='utf-8')
print(json.dumps({'cash_related_issuer_filings':len(full),'selected_nearby_notices':len(docs),'required_selected_cash_rows':len(targets)},indent=2))
