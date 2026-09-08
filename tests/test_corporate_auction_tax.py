"""Accounting examples with invented prices/positions; zero strategy observations."""
from copy import deepcopy
from decimal import Decimal as D

import pytest

from stocks_predictor.continuous_cash import (
    OrdinaryTaxLedger, apply_action, mark, portfolio_fingerprint, run_continuous,
)
from stocks_predictor.retail_cash import Holding, RetailBook
from tests.test_continuous_cash import bonus, calendar, sale, tape


def auction(basis=130, tax_class='bdr'):
    book = RetailBook(1000, '2020-01-15')
    book.positions['A'] = Holding('A-ISIN', 13, D(basis))
    action = bonus()
    action.update(basis_mode='carry', removes_original=True)
    action['stocks'][0].update(ticker='B', isin='B-ISIN', ratio='.5', basis_fraction='1',
        tax_class=tax_class, fraction_settlement={
            'source_review': True, 'sources': ['synthetic auction'], 'tax_source': ['synthetic classification'],
            'tax_treatment': 'ordinary_exchange', 'disposal_date': '2020-02-03',
            'known_on': '2020-02-03', 'payment_date': '2020-02-10', 'available_on': '2020-02-11',
            'gross_cash_per_fraction': '30', 'fees_per_fraction': '1', 'irrf_per_fraction': '.2'})
    return book, action


@pytest.mark.parametrize('basis,whole_basis,gain,tax_due,loss', [
    (130, 120, '4.5', '.67', '0'), (260, 240, '-5.5', '0', '5.5')])
def test_identical_fraction_cash_has_different_tax_for_different_cost_basis(basis, whole_basis, gain, tax_due, loss):
    book, action = auction(basis)
    apply_action(book, action)
    assert book.positions['B'].quantity == 6
    assert book.positions['B'].basis == whole_basis
    assert book.corporate_disposals[0]['basis'] == D(basis) / 13
    assert book.corporate_disposals[0]['gain'] == D(gain)
    assert book.rights['bonus:fraction:0']['net'] == D('14.5')
    book.advance('2020-02-03')
    tax = OrdinaryTaxLedger(calendar()); tax.enter(book, '2020-02')
    assert tax.last['tax'] == D(tax_due)
    assert tax.last['loss_carry'] == D(loss)
    before = deepcopy(book.pending); tax.refresh(book)
    assert book.pending == before
    assert tax.last['corporate_irrf'] == D('.1')
    book.advance('2020-02-10'); assert book.cash == 1000
    book.advance('2020-02-11'); assert book.cash == D('1014.4')


@pytest.mark.parametrize('ordinary_gross,total_tax', [('19985', '0'), ('19990', '15.67')])
def test_auction_gross_joins_monthly_equity_threshold_before_fee_deduction(ordinary_gross, total_tax):
    book, action = auction(tax_class='equity'); apply_action(book, action)
    book.advance('2020-02-03')
    book.trades.append(sale('2020-02-03', '2020-02-05', ordinary_gross, '100'))
    tax = OrdinaryTaxLedger(calendar()); tax.enter(book, '2020-02')
    assert tax.last['equity_sales'] == D(ordinary_gross) + 15
    assert tax.last['tax'] == D(total_tax)
    assert tax.last['irrf'] == 0


def test_prior_month_auction_loss_offsets_later_gain_without_becoming_cash():
    book, action = auction(260); apply_action(book, action)
    book.advance('2020-02-03')
    tax = OrdinaryTaxLedger(calendar()); tax.enter(book, '2020-02')
    book.advance('2020-03-02'); tax.enter(book, '2020-03')
    book.trades.append(sale('2020-03-02', '2020-03-04', '100', '10', 'bdr'))
    tax.refresh(book)
    assert tax.last['taxable_gain'] == D('4.5')
    assert tax.last['tax'] == D('.67')
    assert tax.last['darf_carry'] == D('.57')  # reviewed prior withholding credit
    assert book.cash == D('1014.4')  # no cash refund invented for the loss or credit


def test_auction_gain_and_withholding_do_not_leak_before_disposal_day():
    book, action = auction(); apply_action(book, action)
    book.advance('2020-02-01')
    tax = OrdinaryTaxLedger(calendar()); tax.enter(book, '2020-02')
    q = {('2020-02-01', 'B'): {'date': '2020-02-01', 'isin': 'B-ISIN', 'close': '10'}}
    before = mark(book, book.day, q, tax)
    assert before['unvalued_claims'] == 1
    assert before['equity_including_receivables'] is None
    assert tax.last['tax'] == 0 and not book.pending
    assert not book.fundable('1000.01', '2020-02-12')
    book.advance('2020-02-03'); tax.refresh(book)
    assert tax.last['tax'] == D('.67') and book.cash == 1000


def test_full_replay_recognizes_tax_on_a_day_with_no_strategy_order():
    data = tape(); data['plans'].pop(1)
    _, action = auction()
    leg = action['stocks'][0]; leg['ratio'] = '.065'
    leg['fraction_settlement'].update(gross_cash_per_fraction='500', fees_per_fraction='0', irrf_per_fraction='0')
    data['actions'] = [action]
    for day in data['sessions']:
        data['quotes'][(day, 'B')] = {'date': day, 'isin': 'B-ISIN', 'standard': '100',
                                     'fractional': '100', 'close': '100', 'lot': 100}
    result = run_continuous(**data)
    # 100 original -> 6 whole B + .5 auction unit. Removed basis = 1000/13.
    # February tax: truncate((250 - 1000/13)*15%) = 25.96. March losses
    # cannot retroactively refund February tax. Cash = 600 + 250 - 25.96.
    assert result['profit_excluding_unpaid_receivables'] == D('-175.96')
    assert result['cleared_cash_on_last_obligation_date'] == D('824.04')
    february = next(r for r in result['tax_assessments'] if r['month'] == '2020-02')
    assert february['tax'] == D('25.96')
    assert february['corporate_disposal_ids'] == ['bonus:fraction:0']
    assert not any(r['date'] == '2020-02-03' for r in result['trades'])
    assert all(type(r['quantity']) is int for r in result['trades'])


@pytest.mark.parametrize('field,value', [('gross_cash_per_fraction', None), ('irrf_per_fraction', None),
    ('known_on', '2020-02-04'), ('disposal_date', '2020-01-14'), ('tax_source', []),
    ('fees_per_fraction', '-1'), ('tax_treatment', None)])
def test_missing_or_noncausal_terms_fail_without_changing_the_book(field, value):
    book, action = auction()
    action['stocks'][0]['fraction_settlement'][field] = value
    before = deepcopy(book.__dict__)
    with pytest.raises(ValueError):
        apply_action(book, action)
    assert book.__dict__ == before


def test_fee_net_scalar_requires_review_bound_to_full_portfolio_context():
    book, action = auction()
    terms = action['stocks'][0]['fraction_settlement']
    terms.update(tax_treatment='reviewed_portfolio_net', net_cash_per_fraction='29',
                 portfolio_state_sha256=portfolio_fingerprint(book))
    changed = deepcopy(book)
    changed.trades.append(sale('2020-01-03', '2020-01-07', '100', '-50'))
    with pytest.raises(ValueError, match='portfolio state'):
        apply_action(changed, action)
    changed = deepcopy(book); changed.positions['A'].basis += 1
    with pytest.raises(ValueError, match='portfolio state'):
        apply_action(changed, action)
    apply_action(book, action)
    assert book.rights['bonus:fraction:0']['net'] == D('14.5')


def test_fixed_compulsory_disposal_tax_cannot_be_reused_across_books():
    book, action = auction()
    action.update(basis_mode='explicit_disposal', stocks=[], disposal_tax=[{
        'source_review': True, 'sources': ['synthetic'], 'payment_date': '2020-02-28',
        'known_on': '2020-01-15',
        'tax_per_original': '1', 'portfolio_state_sha256': portfolio_fingerprint(book)}])
    changed = deepcopy(book); changed.positions['A'].basis += 1
    with pytest.raises(ValueError, match='portfolio state'):
        apply_action(changed, action)
    apply_action(book, action)
    assert book.pending == [{'date': '2020-02-28', 'amount': D(-13), 'kind': 'CORPORATE_TAX'}]


def test_future_fixed_tax_is_not_an_early_liability_even_with_matching_portfolio():
    book, action = auction()
    action.update(basis_mode='explicit_disposal', stocks=[], disposal_tax=[{
        'source_review': True, 'sources': ['synthetic'], 'payment_date': '2020-02-28',
        'known_on': '2020-02-03', 'tax_per_original': '1',
        'portfolio_state_sha256': portfolio_fingerprint(book)}])
    before = deepcopy(book.__dict__)
    with pytest.raises(ValueError, match='future disposal tax'):
        apply_action(book, action)
    assert book.__dict__ == before


def test_post_endpoint_auction_cannot_publish_an_untaxed_terminal_profit():
    data = tape(); data['plans'].pop(1)
    _, action = auction(); action['stocks'][0]['ratio'] = '.065'
    action['stocks'][0]['fraction_settlement'].update(disposal_date='2020-03-10',
        known_on='2020-03-10', payment_date='2020-03-12', available_on='2020-03-13')
    data['actions'] = [action]
    for day in data['sessions']:
        data['quotes'][(day, 'B')] = {'date': day, 'isin': 'B-ISIN', 'standard': '100',
                                    'fractional': '100', 'close': '100', 'lot': 100}
    with pytest.raises(ValueError, match='extended reviewed tax horizon'):
        run_continuous(**data)
