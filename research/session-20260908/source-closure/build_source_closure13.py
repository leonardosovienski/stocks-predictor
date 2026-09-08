"""Reconcile overlooked issuer filings, retaining unresolved dates and raw rows."""
from bisect import bisect_right
from copy import deepcopy
from decimal import Decimal as D
import json
from pathlib import Path
from source_utils import ROOT, BASE, OUT, read, pages, norm, dates
from closure_helpers import sha, source, original_b3
from stocks_predictor.cash_source_audit import coalesce_reviewed_cash_duplicates

old = read(OUT / 'cash-closure-12.json')
cards = read(OUT / 'cash-review-cards.json')
sessions = read(ROOT / 'work/stocks-final-review-bundle/inputs/quote-tape-index.json')['sessions']
law = next(r['tax_source'] for r in old['cash_events']
           if r.get('net_rule') == 'RESIDENT_PF_PRE_2026_ORDINARY_DISTRIBUTION')
refs = original_b3(cards[227], duplicate_count=2)
assert [r['row'] for r in refs] == [15, 16]
reviews = [dict(canonical_event_id=cards[227]['event_id'],
    duplicate_event_ids=[cards[228]['event_id']], source_review=True,
    issuer_distribution_count=1,
    identity={k: cards[227][k] for k in ['ticker', 'isin', 'action', 'ex_date',
                                       'approval_date', 'last_cum', 'gross_per_share']},
    raw_records=[dict(event_id=cards[i]['event_id'], source=s) for i, s in zip([227, 228], refs)],
    issuer_sources=[source('cvm-complete-1009.pdf', pages=[1]),
                    source('cvm-complete-1247.pdf', pages=[1]),
                    source('issuer-13-cvm-1456495.pdf', pages=[1], cvm_version=3, received_on='2025-12-11')],
    reason='B3 rows 15/16 are identical. Issuer January 29 declaration specifies ONE R$0.09725 distribution, '
           'total R$61,552,784.82; version3 and December11 notice bind it to December17/2025. '
           'Do not apply this review to Iguatemi records: those represent distinct documented installments.',
    raw_records_preserved=True, review_as_of='2026-09-08')]

def raw_row(s):
    p = Path(s['file'])
    assert sha(p) == s['sha256']
    return read(p)['results'][s['row']]

events = coalesce_reviewed_cash_duplicates(old['cash_events'], reviews, raw_row, sessions)
byid = {r['event_id']: r for r in events}
facts = []

def checked(name, pp, literals=(), required_dates=()):
    p = BASE / name
    if not p.exists(): p = OUT / 'new-primary' / name
    # A PDF parser can salvage a truncated download. Never count it as complete.
    blob = p.read_bytes()
    # CVM pads generated reports with NUL bytes after a valid PDF EOF.
    # Ignore only that padding for validation; preserve the original bytes/hash.
    assert blob.startswith(b'%PDF-') and blob.rstrip(b'\x00 \r\n\t').endswith(b'%%EOF'), name
    t = ' '.join(norm(page['text']) for page in pages(name) if page['page'] in pp)
    assert all(norm(s) in t for s in literals), (name, literals)
    assert set(required_dates) <= {d for d, _, _ in dates(t)}, (name, required_dates)
    return source(name, pages=pp)

def add(i, pay, sources, net=True, duplicate_count=1, **metadata):
    c = cards[i]; r = byid[c['event_id']]
    assert r['payment_date'] is None and pay >= c['ex_date']
    j = bisect_right(sessions, pay)
    amount = str(D(c['gross_per_share']) * (D('.85') if c['action'] == 'JRS CAP PROPRIO' else 1)) if net else None
    ss = original_b3(c, duplicate_count=duplicate_count) + sources
    r.update(payment_date=pay, known_on=pay, available_on=sessions[j] if j < len(sessions) else None,
        sources=ss, net_per_share=amount, tax_source=law if net else None, source_review=net,
        payment_date_reviewed=True, actual_broker_cent_rounding_not_verified=True,
        actual_broker_receipt_verified=False,
        knowledge_policy='Retrospective sources verify cash only; never announce their contents before publication. '
                         'known_on is conservative cash recognition on payment day, not filing publication.',
        **metadata)
    facts.append(dict(card_index=i, event_id=r['event_id'], payment_date=pay, sources=ss, **metadata))

ss = checked('issuer-13-iguatemi-dfp2019.pdf', [88], ['25% foram pagos', 'saldo restante foi liquidado'],
             ['2019-04-18', '2019-06-28', '2019-09-30', '2019-12-20'])
for i, day in zip([68, 69, 70], ['2019-06-28', '2019-09-30', '2019-12-20']):
    add(i, day, [ss], duplicate_count=3,
        payment_review_method='ISSUER_DFP_CONFIRMS_THREE_SEPARATE_PAYMENTS',
        retrospective_evidence=True, indistinguishable_raw_rows_assigned_in_chronological_order=True)
add(117, '2020-05-20', [checked('issuer-13-totvs-agm2020.pdf', [2], ['24.816.612,56'],
    ['2020-04-27', '2020-04-28', '2020-05-20']), source('issuer-13-totvs-history.html',
    locator='Dividendos, approval27/04/2020, payment20/05/2020; nominal displayed rounded.')],
    payment_review_method='ISSUER_AGM_AND_PAYMENT_HISTORY', rounded_issuer_nominal_original_b3_precision_preserved=True)
add(121, '2020-12-03', [checked('issuer-13-radl-agm2021-doe.pdf', [1],
    ['04/06/2020', '0,148540028', 'pago aos acionistas em 03/12/2020'])],
    payment_review_method='ISSUER_AGM_CONFIRMS_PAST_PAYMENT', retrospective_evidence=True,
    gross_basis='Original entitlement before five-for-one split; do not divide accrued right at payment.')
add(146, '2021-10-22', [checked('cvm-complete-0448.pdf', [1], ['0,0117651047']),
    checked('issuer-13-hapvida-agm2022.pdf', [3], ['ja pagos aos acionistas'], ['2021-09-22', '2021-10-22'])],
    payment_review_method='ISSUER_DECLARATION_AND_AGM_CONFIRMS_PAST_PAYMENT', retrospective_evidence=True)
add(158, '2022-03-28', [checked('cvm-complete-0707.pdf', [1], ['1,613026961']),
    checked('issuer-13-hapvida-prospectus2022.pdf', [2300], ['1,613026961', 'pagos em'], ['2022-03-28', '2022-02-11'])],
    payment_review_method='ISSUER_PROSPECTUS_CONFIRMS_PAYMENT_EXACT_AMOUNT_AND_CLOSING', retrospective_evidence=True,
    approval_history_note='Prospectus recalls initial March29/2021 authorization; January20/2022 notice '
        'and merger closing separately bind the frozen ex-date. Merger consideration is not this dividend.')
add(177, '2023-10-05', [checked('issuer-13-cvm-1145284.pdf', [1], ['0,1823270000'],
    ['2023-03-16', '2023-03-21', '2023-10-05']), source('issuer-13-renner-history.html',
    locator='RCA16/03/2023, .182327, Data do Evento05/10/2023; legend explicitly defines payment date.')],
    payment_review_method='CVM_VERSION_2_AND_ISSUER_PAYMENT_HISTORY', supersedes_undated_version=1)
add(209, '2023-12-05', [checked('issuer-13-cvm-1167175.pdf', [1], ['0,274930192'], ['2023-12-05']),
    checked('issuer-13-cvm-1167313.pdf', [1], ['0,2749301920'], ['2023-08-09', '2023-08-18', '2023-12-05']),
    checked('issuer-13-yduqs-dfp2023.pdf', [58], ['0,274930192'], ['2023-12-05'])],
    payment_review_method='BLANK_SUBJECT_NOTICE_VERSION_4_AND_ISSUER_DFP',
    superseded_candidate_date='2023-12-29', earlier_gross='0.275425', exact_final_gross_preserved=True)
add(212, '2023-11-20', [checked('cvm-complete-0879.pdf', [1], ['20/11/23', '27/09/23', '28/09/23']),
    checked('cvm-complete-0880.pdf', [1], ['0,406579138', 'em complemento ao fato relevante divulgado em 22 de setembro de 2023'])],
    payment_review_method='FIXED_DATE_DECLARATION_AND_EXPLICIT_NOMINAL_CORRECTION',
    original_gross='0.406425666', unavailable_followup_notice='cvm-complete-0872.pdf',
    followup_limitation='Final November16 notice not recovered; date supported by fixed September22 '
        'declaration whose September27 correction changes nominal and subscription ratio only. No payment receipt inferred.')
add(227, '2025-12-17', [checked('issuer-13-cvm-1456495.pdf', [1], ['0,0972500000'],
    ['2024-01-29', '2024-02-01', '2025-12-17']), checked('cvm-complete-1247.pdf', [1],
    ['17 de dezembro de 2025', '29 de janeiro'])], duplicate_count=2,
    payment_review_method='ONE_ISSUER_DECLARATION_WITH_TWO_RAW_ALIASES_VERSION_3')
add(283, '2026-04-10', [checked('issuer-13-cvm-1502854.pdf', [1], ['0,4327368133'],
    ['2025-03-25', '2025-03-28', '2026-04-10']), checked('b3-section-04-1-2026-04-10.pdf', [2],
    ['brpssaacnor7 157 juros sobre capital proprio 28/03/2025 0,43273681330 10/04/2026'])], net=False,
    payment_review_method='CVM_VERSION_3_AND_B3_ACTUAL_CREDIT',
    b3_credit_approval_column_is_last_cum=True, issuer_actual_approval_separately_matched=True,
    net_conflict_pending=True)

# Explicitly preserve structured-report dates that conflict with an "até"
# clause or stale installment schedule. These do not fill payment_date.
candidates = [
    (171, '1037840', 2, '2023-05-31'), (192, '1090357', 1, '2023-05-05'),
    (202, '1088636', 1, '2023-05-31'), (233, '1225281', 1, '2024-05-15'),
    (255, '1222941', 1, '2024-05-31'), (300, '1426141', 1, '2026-09-30'),
    (320, '1461005', 1, '2026-12-30'), (346, '1496627', 1, '2027-03-31'),
    (342, '1490656', 1, '2027-04-30'), (343, '1480277', 1, '2027-04-30'),
    (339, '1498839', 1, '2027-12-31'), (345, '1497966', 1, '2027-12-31'),
    (326, '1457814', 1, '2026-12-30'), (353, '1471585', 1, '2026-12-31')]
for i, protocol, page, day in candidates:
    s = checked(f'issuer-13-cvm-{protocol}.pdf', [page], required_dates=[day])
    r = byid[cards[i]['event_id']]
    assert r['payment_date'] is None
    r['unresolved_payment_evidence'] = dict(candidate_date=day,
        classification='STALE_AGGREGATE_SCHEDULE' if i == 353 else 'STRUCTURED_DATE_REQUIRES_DEADLINE_RECONCILIATION',
        payment_date_inferred=False, sources=[s], source_review=False,
        reason='Structured payment field does not override the underlying maximum deadline or a later installment notice.')

result = {**old, 'schema': 'SOURCE_CLOSURE_CASH_13', 'parent_sha256': sha(OUT/'cash-closure-12.json'),
    'cash_events': events, 'facts': old['facts'] + facts, 'duplicate_lineage': reviews,
    'rejected_primary_downloads': [dict(file='issuer-13-hapvida-itr1t2022.pdf',
        reason='Truncated2097152-byte download without PDF EOF; extracted pages not primary proof.',
        replacement='issuer-13-hapvida-prospectus2022.pdf')],
    'counts': {**old['counts'], 'execution_payment_rows': len(events),
        'raw_records_coalesced': 1, 'unique_declared_entitlements': 777, 'reviewed_duplicate_groups': 1,
        'new_single_payment_dates': old['counts']['new_single_payment_dates'] + len(facts),
        'missing_payment_after': sum(not r['payment_date'] for r in events),
        'missing_net_after': sum(r['net_per_share'] is None for r in events),
        'unresolved_structured_date_candidates': len(candidates)}}
assert result['counts']['missing_payment_after'] == 24
with (OUT/'cash-closure-13.json').open('x', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(json.dumps(result['counts']))
