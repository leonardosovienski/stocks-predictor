"""Primary payment fixtures plus synthetic positions, never strategy returns."""
from copy import deepcopy
from datetime import date, timedelta
from decimal import Decimal as D
import json
from pathlib import Path

import pytest

from stocks_predictor.cash_source_audit import expand_reviewed_installments, parse_b3_credit_pages
from stocks_predictor.continuous_cash import apply_action
from stocks_predictor.retail_cash import Holding, RetailBook
from stocks_predictor.source_closure import DERIVED_REVIEW_SHAS, source_counts

FIXTURES = Path(__file__).parent / 'fixtures/source_closure'


def fixture():
    return json.loads((FIXTURES / 'reviewed-payments.json').read_text(encoding='utf-8'))


def sessions():
    # Synthetic calendar only. Production expansion uses the frozen B3 sessions.
    day = date(2020, 1, 1)
    result = []
    while day <= date(2026, 4, 1):
        if day.weekday() < 5:
            result.append(day.isoformat())
        day += timedelta(days=1)
    return result


def test_actual_installments_preserve_parents_and_never_pay_aggregate_twice():
    f = fixture(); before = deepcopy(f)
    rows, lineage = expand_reviewed_installments(f['parents'], f['schedules'], sessions())
    assert f == before
    assert len(rows) == 32 and len(lineage) == 9
    assert not {r['event_id'] for r in rows} & {r['event_id'] for r in f['parents']}
    cpfe = [r for r in rows if r['ticker'] == 'CPFE3' and r['ex_date'] == '2023-05-02']
    assert [(r['payment_date'], D(r['gross_per_share'])) for r in cpfe] == [
        ('2023-06-23', D('.540074494')), ('2023-10-25', D('.260359162')),
        ('2023-11-17', D('.433931936'))]
    assert sum(D(r['gross_per_share']) for r in cpfe) == D('1.234365592')
    assert sum(D(r['published_rounding_delta']) != 0 for r in lineage) == 4


def test_cpfl_image_table_and_br_distribuidora_principal_have_distinct_payment_schedules():
    f = fixture()
    rows, _ = expand_reviewed_installments(f['parents'], f['schedules'], sessions())
    cpfl = [r for r in rows if r['ticker'] == 'CPFE3' and r['ex_date'] == '2025-04-30']
    assert [r['payment_date'] for r in cpfl] == [
        '2025-06-25', '2025-07-25', '2025-08-25', '2025-09-25',
        '2025-10-27', '2025-11-19', '2025-12-15']
    assert sum(D(r['gross_per_share']) for r in cpfl) == D('2.794176751')
    br = [r for r in rows if r['ticker'] == 'BRDT3']
    assert [(r['payment_date'], D(r['gross_per_share'])) for r in br] == [
        ('2020-09-01', D('.0428003741')), ('2020-09-30', D('.45835939570'))]
    assert all(r['action'] == 'DIVIDENDO' and r['gross_per_share'] == r['net_per_share'] for r in br)


def test_jcp_does_not_inherit_dividend_date_or_unverified_net():
    f = fixture()
    rows, _ = expand_reviewed_installments(f['parents'], f['schedules'], sessions())
    ambev = [r for r in rows if r['ticker'] == 'ABEV3']
    assert [r['payment_date'] for r in ambev] == ['2026-04-06', '2026-07-06', '2026-10-06']
    assert sum(D(r['gross_per_share']) for r in ambev) == D('.269')
    assert all(r['net_per_share'] is None and r['available_on'] is None for r in ambev)
    assert all(r['source_review'] is False for r in ambev)


@pytest.mark.parametrize('field,value', [('ticker', 'WRONG3'), ('isin', 'BRWRONG00000'),
    ('action', 'DIVIDENDO'), ('ex_date', '2020-01-07')])
def test_installment_cross_entitlement_join_rejected(field, value):
    f = fixture(); f['schedules'][0]['payments'][0][field] = value
    with pytest.raises(ValueError, match='different entitlement'):
        expand_reviewed_installments(f['parents'], f['schedules'], sessions())


@pytest.mark.parametrize('mutation', ['duplicate_date', 'duplicate_parent', 'missing_source',
    'future_knowledge', 'wrong_sum', 'unreviewed_rounding', 'wrong_rounding', 'net_without_tax'])
def test_unsafe_installment_materialization_rejected(mutation):
    f = fixture(); s = f['schedules'][0]; p = s['payments'][0]
    if mutation == 'duplicate_date':
        s['payments'][1]['payment_date'] = p['payment_date']
    elif mutation == 'duplicate_parent':
        f['schedules'].append(deepcopy(s))
    elif mutation == 'missing_source':
        p['sources'] = []
    elif mutation == 'future_knowledge':
        p['known_on'] = '2027-01-01'
    elif mutation == 'wrong_sum':
        p['gross_per_share'] = '.079844034'
    elif mutation == 'unreviewed_rounding':
        s['published_rounding']['reviewed'] = False
    elif mutation == 'wrong_rounding':
        s['published_rounding']['delta'] = '0'
    else:
        p['tax_source'] = None
    with pytest.raises(ValueError):
        expand_reviewed_installments(f['parents'], f['schedules'], sessions())


@pytest.mark.parametrize('action', fixture()['corporate_actions'], ids=lambda a: a['ticker'])
def test_approved_integer_splits_conserve_cost_basis_on_odd_holdings(action):
    book = RetailBook(1000, action['ex_date'])
    book.positions[action['ticker']] = Holding(action['isin'], 17, D('253.79'), 'equity')
    apply_action(book, action)
    position = book.positions[action['ticker']]
    assert position.quantity == 17 * D(action['stocks'][0]['ratio'])
    assert position.basis == D('253.79') and book.cash == 1000
    assert not book.rights  # Integer forward splits do not invent fractional proceeds.


def test_b3_credit_pdf_section_and_identity_golden():
    cases = json.loads((FIXTURES / 'b3-credit-pages.json').read_text(encoding='utf-8'))
    missing = parse_b3_credit_pages(cases[0]['pages'], cases[0]['day'])
    assert missing['status'] == 'CREDIT_SECTION_MISSING'
    assert not missing['rows'] and not missing['complete_cash_inventory']
    result = parse_b3_credit_pages(cases[1]['pages'], cases[1]['day'])
    vivt = [r for r in result['rows'] if r['isin'] == 'BRVIVTACNOR0']
    assert len(vivt) == 9
    april = next(r for r in vivt if r['approval_date'] == '2025-04-01')
    assert april['payment_date'] == '2026-04-14' and D(april['gross_per_share']) == D('.14814432785')
    assert all(r['action'] == 'JRS CAP PROPRIO' for r in vivt)
    assert not result['net_amount_inferred'] and not result['complete_cash_inventory']


def test_b3_wrong_report_date_and_duplicate_pages_never_certify_income():
    case = json.loads((FIXTURES / 'b3-credit-pages.json').read_text(encoding='utf-8'))[1]
    result = parse_b3_credit_pages(case['pages'], '2026-04-15')
    assert not result['rows'] and result['rejected']
    with pytest.raises(ValueError, match='unique chronological'):
        parse_b3_credit_pages(case['pages'] * 2, case['day'])


def test_hashed_local_reconstruction_is_not_counted_as_primary_evidence():
    local = {'sha256': next(iter(DERIVED_REVIEW_SHAS))}
    catalog = {'local.json': local, 'issuer.pdf': {'sha256': 'a' * 64},
               'unknown.json': {'sha256': 'b' * 64, 'source_kind': 'UNCLASSIFIED'}}
    assert source_counts(catalog) == {'verified_source_files': 3, 'verified_primary_files': 1,
        'verified_derived_review_files': 1, 'unclassified_source_files': 1}
    local['source_kind'] = 'PRIMARY_SOURCE_RECORD'
    with pytest.raises(ValueError, match='cannot be relabeled'):
        source_counts(catalog)


def test_published_credit_with_missing_approval_is_preserved_outside_joinable_rows():
    case = json.loads((FIXTURES / 'b3-credit-pages.json').read_text(encoding='utf-8'))[3]
    result = parse_b3_credit_pages(case['pages'], case['day'])
    assert not [r for r in result['rows'] if r['isin'] == 'BRVIVAACNOR0']
    vivara = [r for r in result['incomplete_rows'] if r['isin'] == 'BRVIVAACNOR0']
    assert len(vivara) == 1
    assert vivara[0]['approval_date'] is None and vivara[0]['payment_date'] == '2025-12-30'
    assert D(vivara[0]['gross_per_share']) == D('.69765914173')
    assert vivara[0]['requires_separate_issuer_identity_review']
    assert not result['complete_cash_inventory'] and not result['net_amount_inferred']
