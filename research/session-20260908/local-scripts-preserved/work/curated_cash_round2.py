"""Explicit relations read in the complete original pages; no auto approval."""
from source_utils import OUT, read
import json

facts = [
 (1,'2018-10-11','notice-67c875505891d4.pdf',[1],['R$ 0,01','24/09/2018','11/10/2018'],'Local ON schedule; exclude ADS October 18.'),
 (3,'2018-11-12','cvm-complete-0006.pdf',[1],['0,099162742','12 de novembro de 2018','25 de julho de 2018'],'Explicit anticipation replaces November 13 notice.'),
 (29,'2018-12-05','notice-2fd99825781a9e.pdf',[1],['0,92795072','05 de dezembro de 2018','26 de novembro de 2018'],'Approved board resolution.'),
 (31,'2019-04-30','notice-b191366c2667cd.pdf',[3],['0,4100294985','27/12/2018','30/04/2019'],'Accounting credit December 31 is not cash payment.'),
 (93,'2019-09-05','notice-2abd1a5aab039b.pdf',[1],['0,3088','05/09/2019','07/08/2019'],'Approved dividend clause iii.'),
 (104,'2020-03-11','notice-a529f78588c81d.pdf',[1],['0,038235294','20/12/2019','11/03/2020'],'Accounting credit December 20 is not payment.'),
 (153,'2021-12-15','notice-89449257ffbe4e.pdf',[1],['0,024891333','15/12/2021','08/12/2021'],'Clause 5.2 dividend only; May 2022 deadline belongs to JCP.'),
 (200,'2023-05-18','notice-01855d727462cf.pdf',[1],['2,59617683','04 de maio de 2023','18 de maio de 2023'],'Final per-share amount after excluding treasury shares.'),
 (208,'2023-08-25','notice-47a2340c28f1a6.pdf',[2],['R$ 0,25','25 de agosto de 2023','17 de agosto de 2023'],'Brazil record date; US record date August 21 excluded.'),
 (229,'2024-08-14','notice-501889473bdfeb.pdf',[1],['0,057764706','22/03/2024','14/08/2024'],'Payment distinct from accounting credit.'),
 (231,'2024-06-14','notice-dd7cb6d4c1fa02.pdf',[1],['0,45147654','05 de junho de 2024','14 de junho de 2024'],'Explicit CSAN3 local payment.'),
 (234,'2024-07-09','notice-0a7fb7ac538579.pdf',[1],['0,155919','09.07.2024','25.06.2024'],'Explicit distribution and payment.'),
 (241,'2024-11-29','cvm-complete-1119.pdf',[1],['0,60634801971','0,30317400985','29/11/2024'],'Second of two dividend installments. B3 row retains 0.30317400986, rounding difference 1e-11; sum matches total 0.60634801971. Initial notice 18/04/2024 establishes same entitlement.'),
 (268,'2024-10-04','notice-918fe97093caf1.pdf',[1],['0,15610475797','4 de outubro de 2024','26 de setembro de 2024'],'Source says centavos de real after R$, a unit typo; B3 per-share reais identity retained.'),
 (322,'2026-01-13','notice-325f36bd59110e.pdf',[1],['0,84173491445','13 de janeiro de 2026','5 de dezembro de 2025'],'Estimated per-share amount remains B3 value; source date reviewed, 2026 tax separate.'),
 (332,'2025-12-30','notice-174b61a88b9372.pdf',[1],['R$0,17','15 de dezembro de 2025','30 de dezembro de 2025'],'Explicit JCP per-share payment.'),
 (347,'2026-04-07','notice-bc7f3453e8fbf7.pdf',[1],['0,15914793216','07 de abril de 2026','26 de março de 2026'],'After replay endpoint; no reinvestment invented. Unit typo same as RDOR 2024; B3 reais retained.'),
]
with (OUT / 'curated-cash-round2.json').open('w',encoding='utf-8') as f:
    json.dump([dict(card_index=i,payment_date=d,file=n,pages=p,checked_fragments=x,note=s) for i,d,n,p,x,s in facts],f,ensure_ascii=False,indent=2)
print('EXPLICIT_RELATIONS',len(facts))
