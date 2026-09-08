"""Inventory full-cohort primary cash notices without observing any returns."""
from collections import Counter
from datetime import date
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'work/h19-cash-expanded-source'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
obs = read(ROOT/'outputs/h18-h19-reorganization-observation.json')
trial = next(t for t in obs['trials'] if t['family']=='H19' and t['holding_months']==3)
ids = {m['ticker']:m['cnpj'] for p in trial['periods'] for m in p['members']}
queue = read(ROOT/'outputs/H19_CAIXA_PAGAMENTOS_REVISADOS_V3.json')['cash_queue']
targets = []
for r in queue:
    raw = read(Path(r['source_path']))[r['source_row']]
    a = raw['dateApproval']
    targets.append({**r, 'cnpj':ids[r['ticker']], 'approval_date':date(int(a[6:]),int(a[3:5]),int(a[:2])).isoformat()})
old = [d for suffix in ('selected','later','followup') for d in read(BASE/f'ipe-{suffix}-notices.json')]
by_url = {d['Link_Download']:d['local_file'] for d in old}
docs=[]; jobs=[]
for d in read(BASE/'ipe-cash-index.json'):
    if d['Categoria'] not in ('Aviso aos Acionistas','Comunicado ao Mercado','Fato Relevante'): continue
    cnpj = re.sub(r'\D','',d['CNPJ_Companhia'])
    matches=[]
    for t in targets:
        if t['cnpj'] != cnpj: continue
        days=(date.fromisoformat(d['Data_Referencia'])-date.fromisoformat(t['approval_date'])).days
        if -2 <= days <= 550:
            matches.append({k:t[k] for k in ('ticker','ex_date','value_per_share','action','selected')})
    if not matches:continue
    name=by_url.get(d['Link_Download'], f'cvm-complete-{len(docs):04d}.pdf')
    docs.append({**d,'local_file':name,'matching_cash_requirements':matches})
    if not (BASE/name).exists():jobs.append([name,d['Link_Download']])
(BASE/'ipe-complete-notices.json').write_text(json.dumps(docs,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'work/h19-complete-source-batch.json').write_text(json.dumps(jobs,indent=2),encoding='utf-8')
print(json.dumps({'total_notice_documents':len(docs),'to_download':len(jobs),'queue_by_ticker':dict(Counter(r['ticker'] for r in queue)), 'stock_event_gaps':read(ROOT/'outputs/H19_CAIXA_EXECUCAO_V3.json')['issue_counts']},indent=2))
