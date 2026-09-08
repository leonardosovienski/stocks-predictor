from collections import Counter
from decimal import Decimal as D
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1];base=root/'work/h19-cash-expanded-source'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
reg=read(root/'outputs/H19_CAIXA_PAGAMENTOS_REVISADOS_V4.json')
credits=read(base/'complete-credit-reconciliation.json')
for r in reg['cash_queue']:
    if r['payment_date_reviewed']:continue
    matches=[m for m in credits['exact_unique_queue_matches'] if all(m['row'][k]==r[k] for k in ('isin','ex_date','action','value_per_share','source_row'))]
    if matches:
        r.update(payment_date_reviewed=True,reviewed_payment={**matches[0]['evidence'],'net_amount_reviewed':False})
rows=[]
for r in reg['cash_queue']:
    if r['payment_date_reviewed']:continue
    raw=read(Path(r['source_path']))[r['source_row']];a=raw['dateApproval'];approval=f'{a[6:]}-{a[3:5]}-{a[:2]}'
    same=[c for c in credits['credit_rows'] if c['isin']==r['isin'] and c['action']==r['action'] and c['approval_date']==approval and c['payment_date']>=r['ex_date']]
    near=sorted(same,key=lambda c:abs(D(c['value_per_share'])-D(r['value_per_share'])))[:3]
    rows.append({'row':r,'same_identity_approval_credit_count':len(same),'nearest':near})
(base/'remaining-cash-review.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'remaining':len(rows),'by_ticker':dict(Counter(r['row']['ticker'] for r in rows)),
 'same_approval_amount_diff':sum(bool(r['nearest']) for r in rows),
 'examples':[{'ticker':r['row']['ticker'],'ex':r['row']['ex_date'],'amount':r['row']['value_per_share'],
 'candidates':[(c['value_per_share'],c['payment_date']) for c in r['nearest']]} for r in rows if r['nearest']][:30]},indent=2))
