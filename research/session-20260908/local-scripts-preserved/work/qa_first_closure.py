from source_utils import OUT, read, pages, norm, dates
import re

cards=read(OUT/'cash-review-cards.json')
for fact in read(OUT/'cash-closure-01.json')['facts']:
    i=fact['card_index'];r=cards[i]
    for s in fact['sources']:
        name=s['file'].replace('\\','/').split('/')[-1]
        pp=pages(name)
        joined=' '.join(norm(p['text']) for p in pp if p['page'] in s['pages'])
        payment_mentions=[]
        for d,a,b in dates(joined):
            if d<r['ex_date']:continue
            frag=joined[max(0,a-130):b+30]
            if any(k in frag for k in ['pag','credit','parcela','distribui']):payment_mentions.append((d,frag))
        meaningful={d for d,t in payment_mentions if d>r['ex_date']}
        if len(meaningful)>1 or 'parcela' in joined or 'adr' in joined or 'ads' in joined:
            print('\nCARD',i,r['ticker'],r['ex_date'],r['action'],r['gross_per_share'],'ASSIGNED',fact['payment_date'],name)
            print(' | '.join(t for d,t in payment_mentions if d>r['ex_date']))
