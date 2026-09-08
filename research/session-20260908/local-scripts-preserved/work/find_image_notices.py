"""Find acquired primary notices whose pages need visual review, not zero imputation."""
from datetime import date
import json,re
from source_utils import BASE,ROOT,OUT,read,pages

cash=read(OUT/'cash-closure-08.json')['cash_events'];cc=read(OUT/'cash-review-cards.json')
pending={r['event_id'] for r in cash if not r['payment_date']}
obs=read(ROOT/'outputs/h18-h19-reorganization-observation.json')
trial=next(t for t in obs['trials'] if t['family']=='H19' and t['holding_months']==3)
ids={m['ticker']:m['cnpj'] for p in trial['periods'] for m in p['members']}
docs=read(BASE/'ipe-complete-notices.json')+read(OUT/'additional-notices.json')
hits=[];seen=set()
for d in docs:
    name=d['local_file']
    if name in seen:continue
    seen.add(name)
    try:pp=pages(name)
    except FileNotFoundError:continue
    short=[p['page'] for p in pp if len(' '.join(p['text'].split()))<100]
    if not short:continue
    issuer=re.sub(r'\D','',d['CNPJ_Companhia'])
    related=[(i,c) for i,c in enumerate(cc) if c['event_id'] in pending and ids[c['ticker']]==issuer
        and c['approval_date']<=d['Data_Referencia']]
    if not related:continue
    candidates=[i for i,c in related if -5<=(date.fromisoformat(d['Data_Referencia'])-date.fromisoformat(c['approval_date'])).days<=400]
    if candidates:
        hits.append(dict(file=name,pages=short,received=d['Data_Entrega'],subject=d['Assunto'],candidate_cards=candidates,url=d['Link_Download']))
with (OUT/'image-notice-review-08.json').open('x',encoding='utf-8') as f:json.dump(hits,f,ensure_ascii=False,indent=2)
for h in hits:print(h['file'],h['pages'],h['received'],h['candidate_cards'],h['subject'])
