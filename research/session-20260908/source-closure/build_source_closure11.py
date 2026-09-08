"""Manual review of complete declarations and explicit correction chains."""
from bisect import bisect_right
from copy import deepcopy
from decimal import Decimal as D
import json
from source_utils import ROOT, OUT, read, pages, norm, dates
from closure_helpers import sha, source, original_b3
from stocks_predictor.cash_source_audit import expand_reviewed_installments

old = read(OUT/'cash-closure-10.json'); events = deepcopy(old['cash_events'])
cards = read(OUT/'cash-review-cards.json'); byid = {r['event_id']: r for r in events}
sessions = read(ROOT/'work/stocks-final-review-bundle/inputs/quote-tape-index.json')['sessions']
law = next(r['tax_source'] for r in events if r.get('net_rule') == 'RESIDENT_PF_PRE_2026_ORDINARY_DISTRIBUTION')
facts = []

def close(i, pay, names, *, literal=None, duplicate_count=1, review=True, **details):
    c = cards[i]; r = byid[c['event_id']]
    assert not r['payment_date'] and c['ex_date'] <= pay < '2026-01-01'
    ss = original_b3(c, duplicate_count=duplicate_count) + [source(n, pages=pp) for n,pp in names]
    # The locator content was read before this reconstruction. This assertion
    # checks literal dates only; it is not an automated semantic approval.
    text = ' '.join(norm(p['text']) for n, pp in names for p in pages(n) if p['page'] in pp)
    assert pay in {d for d,_,_ in dates(text)}, (i, pay)
    ordinary = r['action'] in {'DIVIDENDO', 'JRS CAP PROPRIO'} and review
    net = literal if literal is not None else (str(D(r['gross_per_share']) *
        (D('.85') if r['action'] == 'JRS CAP PROPRIO' else D(1))) if ordinary else None)
    r.update(payment_date=pay, known_on=pay, available_on=sessions[bisect_right(sessions,pay)],
        sources=ss, net_per_share=net, tax_source=law if net is not None else None,
        source_review=ordinary, net_rule='RESIDENT_PF_PRE_2026_ORDINARY_DISTRIBUTION' if ordinary else None,
        actual_broker_cent_rounding_not_verified=True,
        payment_review_method='MANUAL_COMPLETE_DECLARATION_AND_EXPLICIT_CORRECTION_CHAIN', **details)
    facts.append(dict(card_index=i, event_id=r['event_id'], payment_date=pay, sources=ss, **details))

def refs(*numbers):
    return [(f'cvm-complete-{n:04d}.pdf', [1]) for n in numbers]

for i,pay,nn in [
    (8,'2018-08-20',[32]), (28,'2018-12-12',[44,45]),
    (44,'2019-04-10',[65,66]), (67,'2019-05-21',[174]),
    (71,'2019-05-16',[81]), (73,'2019-07-05',[204]),
    (103,'2020-02-13',[64]), (139,'2021-06-24',[553,554,555,556]),
    (140,'2021-07-14',[497]), (181,'2023-03-01',[882,883]),
    (187,'2023-05-15',[891]), (190,'2023-05-31',[907]),
    (194,'2023-06-09',[848,849]), (214,'2023-08-28',[885]),
    (217,'2023-08-23',[929]), (221,'2023-10-27',[855]),
    (232,'2024-06-17',[1023,1024]), (247,'2024-06-24',[1128]),
    (251,'2024-07-09',[1033,1036]), (253,'2024-05-08',[1094]),
    (254,'2024-05-08',[1094]), (266,'2025-01-16',[1067,1068]),
    (278,'2024-12-30',[1034,1038])]:
    close(i,pay,refs(*nn))
close(38,'2019-03-13',refs(51,209),literal='0.043700000')
close(60,'2019-05-09',refs(218),review=False,
    share_unit_reconciliation_pending=True,
    original_nominal_preserved='1.894109',issuer_post_split_nominal='0.947055',
    reason='Issuer explicitly quotes post-split units; date is proven but execution units require separate action review.')
for a,b,pa,pb,nn in [(90,91,'2019-09-27','2019-11-29',[200,201,202]),
                    (124,125,'2020-09-25','2020-11-23',[380,381])]:
    assert cards[a]['gross_per_share'] == cards[b]['gross_per_share']
    for i,pay in [(a,pa),(b,pb)]:
        close(i,pay,refs(*nn),duplicate_count=2,
            equal_original_rights_mapped_to_two_explicit_payments=True,
            economically_identical_rows_canonical_date_assignment=True)
for i in [223,224]:
    assert sum(D(cards[j]['gross_per_share']) for j in [223,224]) == D('.78532126294')
    close(i,'2023-11-28',refs(868),issuer_aggregate_jcp='.78532126295',
        original_components_sum='.78532126294',published_precision_delta='-.00000000001',
        group_event_ids=[cards[j]['event_id'] for j in [223,224]])
for i in [291,292]:
    assert sum(D(cards[j]['gross_per_share']) for j in [291,292]) == D('.53241111198')
    close(i,'2025-05-06',refs(1300,1301),duplicate_count=2,
        two_original_components_reconcile_to_single_issuer_payment='.53241111198',
        group_event_ids=[cards[j]['event_id'] for j in [291,292]])
close(265,'2024-12-20',refs(1099)+[('cvm-complete-1100.pdf',[1,2])])
close(299,'2025-12-30',refs(1350)+[('cvm-complete-1351.pdf',[1,2])])

# BR Distribuidora's aggregate is two dividends. Monetary corrections are
# separate rights and are not added a second time to the dividend principal.
c = cards[123]; parent = byid[c['event_id']]; assert parent['payment_date'] is None
parts = []
for pay, gross, nn in [('2020-09-01','.0428003741',[337]),('2020-09-30','.45835939570',[338])]:
    parts.append({**{k:parent[k] for k in ('ticker','isin','ex_date','action')},
        'payment_date':pay,'known_on':pay,'gross_per_share':gross,'net_per_share':gross,
        'sources':[source(n,pages=pp) for n,pp in refs(*nn)],'tax_source':law,
        'source_review':True,'net_rule':'RESIDENT_PF_PRE_2026_ORDINARY_DISTRIBUTION',
        'actual_broker_cent_rounding_not_verified':True})
spec = dict(card_index=123,parent_event_id=parent['event_id'],payments=parts,source_review=True,
    sources=original_b3(c)+[source(n,pages=pp) for n,pp in refs(336,337,338)],
    published_rounding=dict(delta='-.00000000001',reviewed=True,
        sources=[source('cvm-complete-0338.pdf',pages=[1])],
        reason='Explicit nominal installments differ by 1e-11 from original aggregate; retain literal source amounts.'))
events,lineage = expand_reviewed_installments(events,[spec],sessions)
result = {**old,'schema':'SOURCE_CLOSURE_CASH_11','parent_sha256':sha(OUT/'cash-closure-10.json'),
    'cash_events':events,'facts':old['facts']+facts,'schedules':old['schedules']+[spec],
    'installment_lineage':old['installment_lineage']+lineage,'raw_parent_rows':old['raw_parent_rows']+[parent]}
result['counts'] = {**old['counts'],'execution_payment_rows':len(events),
    'new_single_payment_dates':old['counts']['new_single_payment_dates']+len(facts),
    'new_complete_schedules':len(result['schedules']),
    'new_installment_payments':sum(len(s['payments']) for s in result['schedules']),
    'missing_payment_after':sum(not r['payment_date'] for r in events),
    'missing_net_after':sum(r['net_per_share'] is None for r in events)}
with (OUT/'cash-closure-11.json').open('x',encoding='utf-8') as f:
    json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result['counts']))
