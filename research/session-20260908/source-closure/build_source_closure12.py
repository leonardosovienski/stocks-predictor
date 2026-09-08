"""Additional dated primary receipts and duration-specific Selic withholding."""
from bisect import bisect_right
from copy import deepcopy
from datetime import date
from decimal import Decimal as D
import json
from pathlib import Path
import re
from source_utils import ROOT, BASE, OUT, read, pages, norm, dates
from closure_helpers import sha, source, original_b3, iso

old=read(OUT/'cash-closure-11.json'); events=deepcopy(old['cash_events'])
cards=read(OUT/'cash-review-cards.json'); byid={r['event_id']:r for r in events}
sessions=read(ROOT/'work/stocks-final-review-bundle/inputs/quote-tape-index.json')['sessions']
law_old=next(r['tax_source'] for r in events if r.get('net_rule')=='RESIDENT_PF_PRE_2026_ORDINARY_DISTRIBUTION')
facts=[]; net_facts=[]

def add_date(i,pay,ss,net=None,**metadata):
    c=cards[i];r=byid[c['event_id']];assert not r['payment_date']
    j=bisect_right(sessions,pay)
    ss=original_b3(c)+ss
    r.update(payment_date=pay,known_on=pay,available_on=sessions[j] if j<len(sessions) else None,
        sources=ss,net_per_share=net,tax_source=law_old if net is not None else None,
        source_review=net is not None,actual_broker_cent_rounding_not_verified=True,**metadata)
    facts.append(dict(card_index=i,event_id=r['event_id'],payment_date=pay,sources=ss,**metadata))

table=read(OUT/'new-primary/issuer-bbseguridade.tables.json')[15]
assert table[1:5]==['Redução de capital','30/04/2020','09/01/2020','10/01/2020']
assert D(table[6].replace(',','.'))==D(cards[114]['gross_per_share'])
add_date(114,'2020-04-30',[source('issuer-bbseguridade.html',row=15)],
    resident_pf_capital_repayment_tax_and_basis_pending=True)
name='issuer-issuer-telefonica-capital-2025-payment.pdf'
t=norm(pages(name)[0]['text']);assert '1,23337023478' in t and '2025-07-15' in {d for d,_,_ in dates(t)}
add_date(280,'2025-07-15',[source(name,pages=[1])],
    resident_pf_capital_repayment_tax_and_basis_pending=True)
# B3 publishes this credit with no approval date; issuer notice supplies that
# date and the record/ex boundary. Preserve this missing B3 field explicitly.
name='b3-section-04-1-2025-12-30.pdf';t=norm(pages(name)[1]['text'])
assert 'vivara participacoes s.a brvivaacnor0 108 dividendo - 0,69765914173 30/12/2025' in t
add_date(321,'2025-12-30',[source(name,pages=[2]),source('cvm-complete-1363.pdf',pages=[1])],
    net=cards[321]['gross_per_share'],
    b3_credit_approval_date_missing=True,issuer_approval_and_ex_boundary_separately_matched=True)
docs=read(BASE/'ipe-complete-notices.json')
vv=[next(d for d in docs if d['local_file']==f'cvm-complete-{n}.pdf') for n in [1524,1525]]
assert [(d['Data_Referencia'],d['Versao']) for d in vv]==[('2026-03-23','1'),('2026-03-23','2')]
assert vv[1]['Tipo_Apresentacao'].startswith('RE -') and vv[1]['Data_Entrega']=='2026-03-24'
index=next(p for p in BASE.glob('ipe-*.zip') if '2026' in p.name)
im=read(index.with_suffix('.zip.source.json'));assert sha(index)==im['sha256']
index_source=dict(file=str(index),sha256=im['sha256'],url=im['url'],
    locator='CNPJ34.274.233/0001-02, reference2026-03-23, version2 received2026-03-24; protocol024295IPE230320260270420140-62.')
add_date(341,'2027-09-15',[source('cvm-complete-1524.pdf',pages=[1],superseded_by_version=2),
    source('cvm-complete-1525.pdf',pages=[1],cvm_version=2,received_on='2026-03-24'),
    index_source],
    superseded_schedule_date='2026-09-15',future_schedule_not_realized_cash=True)

# Bind original nominal RENDIMENTO amounts directly to B3's raw pagination,
# including cases formerly supported only by the intermediate local report.
queue=read(ROOT/'outputs/H19_CAIXA_PAGAMENTOS_REVISADOS_V5.json')['cash_queue']
def bind_nominal(r):
    q=next(q for q in queue if (q['ticker'],q['isin'],q['ex_date'],q['action'],D(q['value_per_share']))==
        (r['ticker'],r['isin'],r['ex_date'],r['action'],D(r['gross_per_share'])))
    oldpath=Path(q['source_path']);stem=oldpath.name.replace('-all.json','');found=[]
    for p in (ROOT/'work'/oldpath.parent.name).glob(stem+'-*.json'):
        if not re.search(r'-\d+\.json$',p.name):continue
        m=read(p.with_suffix('.source.json'));assert sha(p)==m['sha256']
        for n,v in enumerate(read(p)['results']):
            if (v['typeStock']=='ON' and v['corporateAction']=='RENDIMENTO'
                and iso(v['lastDatePriorEx'])==q['last_cum']
                and D(v['valueCash'].replace(',','.'))/D(v['quotedPerShares'])==D(r['gross_per_share'])):
                found.append(dict(file=str(p),sha256=m['sha256'],url=m['url'],row=n))
    assert len(found)==1,(r['event_id'],len(found))
    return found

tax=source(str(OUT/'law/mafon-2019.pdf'),pages=[48,49,50],
    scope='Code8053: PF; monetary remuneration on dividends/JCP follows fixed-income rules; rate depends on duration.')
specs=[
 ('BBSE3','2018-08-10','2018-06-30','cvm-complete-0024.pdf'),
 ('BBSE3','2019-02-15','2018-12-31','cvm-complete-0126.pdf'),
 ('BBSE3','2019-08-12','2019-06-30','cvm-complete-0129.pdf'),
 ('BBSE3','2020-02-14','2019-12-31','cvm-complete-0317.pdf'),
 ('BBSE3','2021-02-12','2020-12-31','cvm-complete-0492.pdf'),
 ('BBSE3','2023-02-15','2022-12-30','cvm-complete-0882.pdf'),
 ('BBSE3','2024-02-09','2023-12-29','cvm-complete-1085.pdf'),
 ('BBSE3','2025-02-21','2024-12-31','cvm-complete-1331.pdf'),
 ('BBSE3','2026-02-13','2025-12-31','cvm-complete-1509.pdf'),
 ('BBAS3','2020-02-26','2019-12-31','cvm-notice-0027.pdf'),
 ('BBAS3','2021-02-23','2020-12-31','cvm-notice-0046.pdf'),
 ('BBAS3','2022-03-03','2021-12-31','cvm-notice-0070.pdf'),
 ('BBAS3','2023-02-24','2022-12-31','cvm-notice-0094.pdf'),
 ('BBAS3','2023-08-22','2023-06-30','cvm-notice-0096.pdf'),
 ('BBAS3','2024-02-22','2023-12-31','cvm-notice-0117.pdf'),
 ('BBAS3','2024-08-22','2024-06-30','cvm-notice-0119.pdf'),
 ('BBAS3','2025-03-12','2024-12-31','cvm-complete-1160.pdf'),
 ('BBAS3','2026-02-24','2025-12-31','cvm-notice-0159.pdf'),
 ('CXSE3','2025-01-06','2024-12-31','cvm-complete-1341.pdf'),
 ('CXSE3','2025-05-02','2024-12-31','cvm-complete-1346.pdf'),
 ('CXSE3','2026-01-05','2025-12-31','cvm-complete-1516.pdf'),
 ('BRDT3','2021-04-16','2020-12-31','cvm-complete-0514.pdf')]
for ticker,ex,start,name in specs:
    pp=[1,2] if ticker=='BRDT3' else [1]
    t=' '.join(norm(p['text']) for p in pages(name) if p['page'] in pp)
    # Repair spaces inside the printed day only for literal-date verification.
    t=re.sub(r'\b([0-3]) ([0-9]/)',r'\1\2',t)
    assert start in {d for d,_,_ in dates(t)},(ticker,ex,start)
    rr=[r for r in events if (r['ticker'],r['ex_date'],r['action'])==(ticker,ex,'RENDIMENTO')]
    assert rr
    for r in rr:
        assert r['net_per_share'] is None and r['payment_date']
        days=(date.fromisoformat(r['payment_date'])-date.fromisoformat(start)).days
        assert 0<days<=360
        rate=D('.225') if days<=180 else D('.20')
        ss=bind_nominal(r)+[source(name,pages=pp)]
        r['sources']+=ss
        r.update(net_per_share=str(D(r['gross_per_share'])*(1-rate)),tax_source=[tax],source_review=True,
            net_rule='RESIDENT_PF_SELIC_DURATION_WITHHOLDING',accrual_start=start,
            accrual_days=days,withholding_rate=str(rate),actual_broker_cent_rounding_not_verified=True,
            withholding_only_not_personal_annual_minimum_tax=True)
        net_facts.append(dict(event_id=r['event_id'],net_per_share=r['net_per_share'],
            accrual_start=start,accrual_days=days,rate=str(rate),sources=ss,tax_source=[tax]))

result={**old,'schema':'SOURCE_CLOSURE_CASH_12','parent_sha256':sha(OUT/'cash-closure-11.json'),
    'cash_events':events,'facts':old['facts']+facts,'net_facts':old.get('net_facts',[])+net_facts}
result['counts']={**old['counts'],'new_single_payment_dates':old['counts']['new_single_payment_dates']+len(facts),
    'missing_payment_after':sum(not r['payment_date'] for r in events),
    'missing_net_after':sum(r['net_per_share'] is None for r in events)}
with (OUT/'cash-closure-12.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result['counts']))
