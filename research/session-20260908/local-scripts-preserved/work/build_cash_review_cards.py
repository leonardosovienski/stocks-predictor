"""Read-only candidate index; never a source certification or cash change."""
from collections import Counter
from datetime import date
from decimal import Decimal as D
import hashlib
import json
from pathlib import Path
import re
import unicodedata

ROOT=Path(r'C:\Users\Superleo13\stocks-predictor-work\.local-research\stocks-session-20260907')
BASE=ROOT/'work/h19-cash-expanded-source'
OUT=ROOT/'work/source-closure-20260908'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def norm(s):return ' '.join(unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower().split())
months={v:i+1 for i,v in enumerate('janeiro fevereiro marco abril maio junho julho agosto setembro outubro novembro dezembro'.split())}
pat=re.compile(r'\b(\d{1,2})\s*(?:de\s+('+ '|'.join(months)+r')\s*(?:de\s*)?|([/.-])(\d{1,2})\3)(\d{4})\b')
def dates(s):
    result=[]
    for m in pat.finditer(s):
        try:d=date(int(m[5]),months[m[2]] if m[2] else int(m[4]),int(m[1])).isoformat()
        except ValueError:continue
        result.append((d,m.start(),m.end()))
    return result
meta={r['local_file']:r for r in read(BASE/'ipe-complete-notices.json')}
cash=read(ROOT/'work/stocks-final-review-bundle/inputs/cash-events.json')
missing=[r for r in cash if not r['payment_date']]
old=read(BASE/'complete-payment-candidates.json')
cards=[]
for r in missing:
    match=[v for v in old if v['ticker']==r['ticker'] and v['ex_date']==r['ex_date'] and v['action']==r['action'] and D(v['value_per_share'])==D(r['gross_per_share'])]
    match=[v for v in match if str(v['source_row'])==r['event_id'].rsplit(':',1)[-1]]
    identities={tuple(v[k] for k in ['isin','last_cum','approval_date','source_path','source_row']) for v in match}
    assert len(identities)==1,(r,len(match),identities)
    o=match[0];a=o['approval_date']; approval=f'{a[6:]}-{a[3:5]}-{a[:2]}'
    options=[]
    for c in o['matches']:
        p=BASE/c['file']; txt=p.with_suffix('.extracted.json')
        if not txt.exists():txt=p.with_suffix('.complete-text.json')
        page=next(v['text'] for v in read(txt) if v['page']==c['page'])
        text=norm(page); ds=dates(text)
        dd={v[0] for v in ds}
        if not ({o['last_cum'],approval}&dd):continue
        if not (re.search(r'aviso|acionistas|comunicado|companhia',text)):continue
        source=read(p.with_suffix('.pdf.source.json'))
        assert hashlib.sha256(p.read_bytes()).hexdigest()==source['sha256']
        options.append({'file':c['file'],'page':c['page'],'url':source['url'],'sha256':source['sha256'],
            'received':meta[c['file']]['Data_Entrega'],'last_cum_matched':o['last_cum'] in dd,
            'approval_matched':approval in dd,'dates':[(d,text[max(0,start-110):end+80]) for d,start,end in ds],
            'candidate_payment_dates':c['date_candidates'],'text':text})
    cards.append({**r,'last_cum':o['last_cum'],'approval_date':approval,'candidates':options})
(OUT/'cash-review-cards.json').write_text(json.dumps(cards,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'rows':len(cards),'with_anchored_primary_pages':sum(bool(r['candidates']) for r in cards),
 'both_date_anchors':sum(any(c['last_cum_matched'] and c['approval_matched'] for c in r['candidates']) for r in cards),
 'empty_by_ticker':dict(Counter(r['ticker'] for r in cards if not r['candidates']))}))
for i,r in enumerate(cards):
    print(i,r['ticker'],r['ex_date'],r['gross_per_share'],[(c['file'],c['page'],c['last_cum_matched'],c['candidate_payment_dates']) for c in r['candidates']][:4])
