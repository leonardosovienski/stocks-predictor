"""Search the complete issuer cash corpus, including adjusted per-share units."""
import sys
from source_utils import ROOT, BASE, OUT, read, pages, norm, dates

cards=read(OUT/'cash-review-cards.json')
obs=read(ROOT/'outputs/h18-h19-reorganization-observation.json')
trial=next(t for t in obs['trials'] if t['family']=='H19' and t['holding_months']==3)
ids={m['ticker']:m['cnpj'] for p in trial['periods'] for m in p['members']}
docs=read(BASE/'ipe-complete-notices.json')
for i in map(int,sys.argv[1:]):
    r=cards[i];print('\nCARD',i,r['ticker'],r['last_cum'],r['approval_date'],r['gross_per_share'])
    for d in docs:
        cnpj=''.join(c for c in d['CNPJ_Companhia'] if c.isdigit())
        if cnpj!=ids[r['ticker']] or d['Data_Entrega']<r['approval_date']:continue
        try:pp=pages(d['local_file'])
        except FileNotFoundError:continue
        for p in pp:
            t=norm(p['text']);dd=dates(t)
            if not {r['last_cum'],r['approval_date']}&{s for s,_,_ in dd}:continue
            matches=[]
            for day,a,b in dd:
                if day<=r['ex_date']:continue
                s=t[max(0,a-100):b+80]
                if any(k in s for k in ['pag','parcela','liquid']):matches.append(s)
            if matches:print(d['local_file'],p['page'],d['Data_Entrega'],' | '.join(dict.fromkeys(matches)))
