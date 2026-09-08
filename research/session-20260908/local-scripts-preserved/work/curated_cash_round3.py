"""Reviewed payment clauses and explicitly separated nominal/update amounts."""
from source_utils import OUT, read
import json

raw=[
 (13,'2018-08-15','cvm-complete-0049.pdf',1,'Dividend payment also covers earlier JCP; date same, quantities separate.'),
 (18,'2018-09-05','cvm-complete-0037.pdf',1,'Numbered item 3 is payment date.'),
 (22,'2018-10-31','cvm-complete-0010.pdf',1,'Payment starts October 31; October 24 is ex-date.'),
 (32,'2018-12-21','cvm-complete-0021.pdf',1,'Single installment programmed payment; November 16 is ex-date.'),
 (33,'2018-12-12','cvm-complete-0040.pdf',1,'Brazil local shares December 12; ADR December 18 excluded.'),
 (40,'2019-01-09','cvm-complete-0039.pdf',1,'Item 6 payment for both distributions; December 31 is accounting credit.'),
 (41,'2019-01-09','cvm-complete-0039.pdf',1,'Item 6 payment for both distributions; December 31 is accounting credit.'),
 (43,'2019-01-24','cvm-complete-0069.pdf',1,'Explicit anticipation replaces January 28 deadline.'),
 (51,'2019-03-13','cvm-complete-0209.pdf',1,'Dividend and prior JCP share payment day, remain separate rights.'),
 (66,'2019-05-09','cvm-complete-0080.pdf',1,'Numbered item 6 fixes dividend payment.'),
 (79,'2019-04-29','cvm-complete-0220.pdf',1,'Dividend and JCP already credited in 2018 paid April 29.'),
 (81,'2019-07-03','cvm-complete-0173.pdf',1,'Final value revised from .029899603 to .029899601; payment unchanged.'),
 (82,'2019-05-16','cvm-complete-0172.pdf',1,'Final value revised from .095290223 to .095254607; payment unchanged.'),
 (83,'2019-05-03','cvm-complete-0165.pdf',1,'Numbered payment item; April 5 is ex-date.'),
 (95,'2019-08-14','cvm-complete-0213.pdf',1,'Dividend and earlier JCP share payment day.'),
 (100,'2019-09-04','cvm-complete-0168.pdf',1,'Numbered payment item; August 7 is ex-date.'),
 (106,'2019-12-06','cvm-complete-0170.pdf',1,'Numbered payment item; November 5 is ex-date.'),
 (111,'2020-03-16','cvm-complete-0344.pdf',1,'Explicit payment date; April 16 AGM is not payment.'),
 (112,'2020-03-11','cvm-complete-0385.pdf',1,'Dividend and earlier JCP share payment day.'),
 (120,'2020-05-08','cvm-complete-0395.pdf',1,'Dividend and prior 2019 JCP paid May 8.'),
 (216,'2023-08-16','cvm-complete-0940.pdf',1,'Dividend and earlier JCP share payment day.'),
 (218,'2023-12-01','cvm-complete-0897.pdf',1,'Final value unchanged; December 8 ADR payment excluded.'),
 (219,'2023-12-01','cvm-complete-0897.pdf',1,'Final value unchanged; December 8 ADR payment excluded.'),
]
cards=read(OUT/'cash-review-cards.json')
facts=[]
for i,day,name,page,note in raw:
    card=cards[i]
    candidate=next(c for c in card['candidates'] if c['file']==name and c['page']==page)
    facts.append(dict(card_index=i,payment_date=day,file=name,pages=[page],
                      checked_fragments=[],note=note,record_date=card['last_cum'],
                      approval_date=card['approval_date'],gross_per_share=card['gross_per_share'],
                      candidate_source_sha256=candidate['sha256']))

for nominal,increment,day,name,total in [
 (14,15,'2018-08-21','cvm-complete-0026.pdf','0.788043790'),
 (52,53,'2019-02-26','cvm-complete-0128.pdf','0.683892528'),
 (101,102,'2019-08-21','cvm-complete-0131.pdf','0.898819266')]:
    from decimal import Decimal as D
    assert D(cards[nominal]['gross_per_share'])+D(cards[increment]['gross_per_share'])==D(total)
    for i in (nominal,increment):
        facts.append(dict(card_index=i,payment_date=day,file=name,pages=[1],
                          checked_fragments=[total.replace('.',','),cards[nominal]['gross_per_share'].replace('.',',')],
                          note='Final updated total = nominal dividend + separate B3 monetary increment. Do not credit the updated total twice. Increment taxation separate.',
                          reconciliation={'nominal_card':nominal,'increment_card':increment,'final_updated_per_share':total}))
with (OUT/'curated-cash-round3.json').open('w',encoding='utf-8') as f:json.dump(facts,f,ensure_ascii=False,indent=2)
print('RELATIONS',len(facts))
