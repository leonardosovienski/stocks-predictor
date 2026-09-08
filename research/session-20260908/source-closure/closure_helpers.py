"""Read-only identity and source helpers; no mutation on import."""
from decimal import Decimal as D
import hashlib
from pathlib import Path
import re
from source_utils import ROOT, BASE, OUT, read

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
iso=lambda s:f'{s[6:]}-{s[3:5]}-{s[:2]}'

def source(name, **loc):
    p=BASE/name
    if not p.exists():p=OUT/'new-primary'/name
    side=p.with_suffix('.pdf.source.json') if p.parent==BASE else p.with_suffix('.source.json')
    m=read(side);assert sha(p)==m['sha256']
    return dict(file=str(p),sha256=m['sha256'],url=m['url'],**loc)

def original_b3(c, duplicate_count=1):
    queue=read(ROOT/'outputs/H19_CAIXA_PAGAMENTOS_REVISADOS_V5.json')['cash_queue']
    q=next(r for r in queue if (r['ticker'],r['isin'],r['ex_date'],r['action'],D(r['value_per_share']))==
           (c['ticker'],c['isin'],c['ex_date'],c['action'],D(c['gross_per_share'])))
    old_path=Path(q['source_path']);stem=old_path.name.replace('-all.json','')
    matches=[]
    for p in (ROOT/'work'/old_path.parent.name).glob(stem+'-*.json'):
        if not re.search(r'-\d+\.json$',p.name):continue
        m=read(p.with_suffix('.source.json'));assert sha(p)==m['sha256']
        for n,r in enumerate(read(p)['results']):
            if (r['typeStock']=='ON' and r['corporateAction']==c['action'] and iso(r['dateApproval'])==c['approval_date']
                and iso(r['lastDatePriorEx'])==c['last_cum'] and D(r['valueCash'].replace(',','.'))/D(r['quotedPerShares'])==D(c['gross_per_share'])):
                matches.append(dict(file=str(p),sha256=m['sha256'],url=m['url'],row=n))
    assert len(matches)==duplicate_count,(c['event_id'],len(matches),duplicate_count)
    return matches
