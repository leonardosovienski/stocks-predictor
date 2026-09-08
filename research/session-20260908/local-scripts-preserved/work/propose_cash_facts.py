"""Strict text relations for review; no return computation or approval markers."""
from collections import Counter
import json
from pathlib import Path
import re
from build_cash_review_cards import dates

ROOT=Path(r'C:\Users\Superleo13\stocks-predictor-work\.local-research\stocks-session-20260907')
OUT=ROOT/'work/source-closure-20260908'
cards=json.loads((OUT/'cash-review-cards.json').read_text(encoding='utf-8'))
good=[]; pending=[]
for i,r in enumerate(cards):
    hits=[]
    for c in r['candidates']:
        text=c['text']
        for day,start,end in dates(text):
            if day < r['ex_date'] or day < c['received']:continue
            left=text[max(0,start-200):start]
            markers=list(re.finditer(r'pagamento|pagos|pago|pagas|paga|creditados|creditado|creditadas|creditada|creditos disponiveis',left))
            if not markers:continue
            prefix=left[markers[-1].start():]
            if not re.search(r'(?:em|dia|de|do|a)\s*$',prefix):continue
            if re.search(r'negociad|posicao|registro|detentor|data.base|ate|definid|oportun|futur|ex.provento|acionaria|deliberad|aprovad|saldo|contabil|assembleia',prefix):continue
            if len(prefix)>130:continue
            suffix=text[end:end+40]
            if re.match(r'\s*(?:a |ate |e (?:em |no dia |a partir |\d))',suffix):continue
            if re.search(r'janeiro|fevereiro|marco|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro|\d{2}/\d{2}',prefix):continue
            hits.append({'payment_date':day,'file':c['file'],'page':c['page'], 'received':c['received'],
                         'clause':text[max(0,start-len(prefix)):min(len(text),end+40)],
                         'record_date_present':c['last_cum_matched'],'source_sha256':c['sha256'],'url':c['url']})
    # Keep all conflicts visible, regardless of document recency.
    days={h['payment_date'] for h in hits}
    item={k:r[k] for k in ['event_id','ticker','isin','ex_date','last_cum','approval_date','action','gross_per_share']}
    item.update(card_index=i,payment_candidates=hits)
    if len(days)==1 and any(h['record_date_present'] for h in hits):good.append(item)
    else:pending.append(item)
(OUT/'payment-proposals.json').write_text(json.dumps({'unambiguous':good,'pending':pending},indent=2),encoding='utf-8')
print('PROPOSALS',len(good),'PENDING',len(pending),'MULTI',sum(len({h['payment_date'] for h in r['payment_candidates']})>1 for r in pending))
for r in good:
    h=r['payment_candidates'][0]
    print(r['card_index'],r['ticker'],r['ex_date'],r['gross_per_share'],h['payment_date'],h['file'],h['clause'])
print('PENDING_WITH_NO_PRIMARY_PAGES',dict(Counter(r['ticker'] for r in cards if not r['candidates'])))
