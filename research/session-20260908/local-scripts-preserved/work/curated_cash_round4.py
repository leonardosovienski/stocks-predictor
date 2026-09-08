"""Reviewed schedules indexed by declaration/record date, no fuzzy amount approval."""
import json
from source_utils import OUT, read

cards=read(OUT/'cash-review-cards.json');facts=[]

def add(i,day,name,page,note,net=None,extra_sources=()):
    facts.append(dict(card_index=i,payment_date=day,file=name,pages=[page],checked_fragments=[],
                      note=note,published_net_per_share=net,extra_sources=list(extra_sources)))

for i in (7,26):
    add(i,'2019-01-09','cvm-complete-0013.pdf',1,'Explicit payment of earlier declarations June 28 / September 27; original declaration supplies same entitlement amount.',extra_sources=[dict(file=cards[i]['candidates'][0]['file'],pages=[1])])
for i in (16,39):
    add(i,'2019-04-29','cvm-complete-0220.pdf',1,'Explicit 2018 JCP credit-date list. Original declaration binds per-share value and record date.',extra_sources=[dict(file=cards[i]['candidates'][0]['file'],pages=[1])])
for i in (55,78,98,108):
    add(i,'2020-05-08','cvm-complete-0395.pdf',1,'Explicit 2019 JCP credit-date list. Original declaration binds per-share value and record date.',extra_sources=[dict(file=cards[i]['candidates'][0]['file'],pages=[1])])

for i,day,name,note in [
 (141,'2021-09-30','cvm-complete-0453.pdf','3T21 row binds September 16 record / September 17 ex / September 30 payment, R$0.05 per share.'),
 (145,'2021-11-03','cvm-complete-0501.pdf','Numbered item 3 payment date, not AGM date.'),
 (148,'2022-01-31','cvm-complete-0502.pdf','Numbered item 3 payment date.'),
 (152,'2022-01-31','cvm-complete-0454.pdf','Numbered item 3 payment date.'),
 (166,'2023-03-22','cvm-complete-0898.pdf','Prior JCP declaration December 2022; local March 22 versus ADR March 29.'),
 (180,'2023-03-01','cvm-complete-0882.pdf','Nominal dividend payment; monetary increment remains separate.'),
 (183,'2023-03-15','cvm-complete-0937.pdf','Dividend and previous JCP share payment day.'),
 (239,'2025-02-27','cvm-complete-1127.pdf','First table row: record 28/06/2024, gross .46684904167, payment27/02/2025.'),
 (259,'2025-05-30','cvm-complete-1127.pdf','Second table row: record23/09/2024,gross.23499089814,payment30/05/2025.'),
 (270,'2025-05-27','cvm-complete-1208.pdf','2024 interim dividends; December 23 belongs to different 2025 entitlement.'),
 (274,'2024-08-14','cvm-complete-1150.pdf','Dividend and prior JCP share payment day.'),
 (312,'2026-04-02','cvm-complete-1347.pdf','Numbered item3 payment after endpoint; no early cash.'),
 (329,'2025-12-29','cvm-complete-1388.pdf','Dividend clause(ii) payment29/12/2025. Source exdate06/12 is Saturday; B3 next session08/12 retained. JCP May deadline excluded.'),
 (348,'2026-01-16','cvm-complete-1516.pdf','Nominal dividend; updated total separate.'),
 (351,'2026-03-02','cvm-complete-1511.pdf','Final updated amount does not replace nominal dividend plus increment.'),
]:add(i,day,name,1,note)

for i,net in [(154,'0.12689752322'),(155,'0.09128575606'),(163,'0.15278755767')]:
    add(i,'2023-04-18','cvm-followup-0039.pdf',1,'JCP table row exact record date/gross/net/payment. Do not use dividend July rows.',net)
for i,net in [(285,'0.05264314492'),(286,'0.13116945695'),(296,'0.10608541339'),(297,'0.06624319750'),(298,'0.08715426995'),(314,'0.09309657299'),(315,'0.09035622247'),(316,'0.10078114272')]:
    add(i,'2026-04-14','cvm-complete-1449.pdf',1,'JCP declared/credited2025, publisher gives exact net and payment2026. Unadjusted post-April-split unit; do not apply table first row to old units.',net)
with (OUT/'curated-cash-round4.json').open('w',encoding='utf-8') as f:json.dump(facts,f,ensure_ascii=False,indent=2)
print('EXPLICIT_RELATIONS',len(facts))
