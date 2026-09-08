"""Find later payment confirmations, never treat an announced deadline as payment."""
from datetime import date
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parent.parent;BASE=ROOT/'work/h19-cash-expanded-source'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
obs=read(ROOT/'outputs/h18-h19-reorganization-observation.json')
t=next(t for t in obs['trials'] if t['family']=='H19' and t['holding_months']==3)
ids={m['ticker']:m['cnpj'] for p in t['periods'] for m in p['members']}
focus={'ENBR3','CSMG3','VLID3','LIGT3','NEOE3','HGTX3','VIVT3','CYRE3','MYPK3','EZTC3','ALSO3','ALOS3','CIEL3','COGN3','NTCO3','MOVI3','BRML3','TIMP3','PETZ3'}
q=[r for r in read(ROOT/'outputs/H19_CAIXA_FILA_DE_VALIDACAO.json')['cash_queue'] if r['selected'] and r['ticker'] in focus]
previous=read(BASE/'ipe-selected-notices.json')+read(BASE/'ipe-later-notices.json');used={d['Link_Download'] for d in previous}
docs=[]
for d in read(BASE/'ipe-cash-index.json'):
    if d['Link_Download'] in used or d['Categoria'] not in ('Aviso aos Acionistas','Comunicado ao Mercado','Fato Relevante'):continue
    title=d['Assunto'].lower()
    if not any(w in title for w in ('pagamento','provento','remunera','dividend','juro','jcp','jscp')) and 'Dividendos' not in d['Tipo']:continue
    cnpj=re.sub(r'\D','',d['CNPJ_Companhia']);matches=[]
    for r in q:
        if ids[r['ticker']]!=cnpj:continue
        delta=(date.fromisoformat(d['Data_Referencia'])-date.fromisoformat(r['ex_date'])).days
        if 0<=delta<=550:matches.append({k:r[k] for k in ('ticker','ex_date','value_per_share','action')})
    if matches:
        used.add(d['Link_Download']);docs.append({**d,'matching_cash_requirements':matches,'local_file':f'cvm-followup-{len(docs):04d}.pdf'})
(BASE/'ipe-followup-notices.json').write_text(json.dumps(docs,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'work/h19-followup-batch.json').write_text(json.dumps([[d['local_file'],d['Link_Download']] for d in docs],indent=2),encoding='utf-8')
print(len(docs))
