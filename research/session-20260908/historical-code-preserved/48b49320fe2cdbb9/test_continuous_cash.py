"""Synthetic multi-month paths; no new historical strategy observations."""
from copy import deepcopy
from datetime import date, timedelta
from decimal import Decimal as D

import pytest

from stocks_predictor.continuous_cash import OrdinaryTaxLedger, apply_action, run_continuous
from stocks_predictor.retail_cash import Holding, RetailBook


def calendar():
    return {f'2020-{m:02}': {'due_date': f'2020-{m+1:02}-28', 'source_review': True,
            'sources': ['synthetic'], 'irrf_rate': '.00005', 'irrf_waiver': '1', 'minimum_darf': '10'}
            for m in range(1, 4)}


def tape():
    day = date(2020, 1, 2)
    sessions = []
    while day <= date(2020, 3, 6):
        if day.weekday() < 5:
            sessions.append(day.isoformat())
        day += timedelta(days=1)
    quotes = {}
    for day in sessions:
        price = '10' if day < '2020-01-31' else '11'
        quotes[(day, 'A')] = {'date': day, 'isin': 'A-ISIN', 'standard': price,
                               'fractional': price, 'close': price, 'lot': 100}
    member = {'ticker': 'A', 'isin': 'A-ISIN', 'lot': 100, 'tax_class': 'equity'}
    plans = [{'asof': '2020-01-02', 'entry': '2020-01-03', 'members': [member]},
             {'asof': '2020-01-31', 'entry': '2020-02-03', 'members': [member]},
             {'asof': '2020-03-02', 'entry': '2020-03-03', 'members': []}]
    return dict(capital=1000, cost_rate=0, plans=plans, quotes=quotes, sessions=sessions,
                settlements={d: sessions[i+2] for i, d in enumerate(sessions[:-2])},
                cash_events=[], actions=[], tax_calendar=calendar(), coverage_ready=True)


def dividend(pay='2020-02-28', available='2020-03-02'):
    return {'event_id': 'div-1', 'ticker': 'A', 'isin': 'A-ISIN', 'ex_date': '2020-01-15',
            'payment_date': pay, 'available_on': available, 'net_per_share': '.5',
            'source_review': True, 'sources': ['synthetic'], 'tax_source': ['synthetic'],
            'known_on': '2020-01-14'}


def test_continuous_retention_and_paid_dividend_close_by_independent_arithmetic():
    data = tape(); data['cash_events'] = [dividend()]
    result = run_continuous(**data)
    assert [(r['quantity'], r['date']) for r in result['trades']] == [(100, '2020-01-03'), (-100, '2020-03-03')]
    # Independently: R$1,100 sale + R$50 paid dividend - R$1,000 initial.
    assert result['profit_excluding_unpaid_receivables'] == 150
    assert result['terminal']['unpaid_receivables'] == 0
    assert all(r['settled_cash'] >= 0 for r in result['snapshots'])


def test_post_exit_dividend_preserved_as_receivable_and_does_not_fund_retention():
    data = tape(); data['cash_events'] = [dividend('2020-04-30', '2020-05-04')]
    result = run_continuous(**data)
    assert result['profit_excluding_unpaid_receivables'] == 100
    assert result['profit_including_unpaid_receivables_at_face'] == 150
    assert result['unpaid_receivables']['div-1']['net'] == 50
    assert len(result['trades']) == 2


def test_missing_middle_path_quote_is_fatal_without_partial_profit():
    data = tape(); del data['quotes'][('2020-02-10', 'A')]
    with pytest.raises(KeyError):
        run_continuous(**data)


def test_unreviewed_coverage_events_and_noncausal_plan_are_fatal():
    data = tape(); data['coverage_ready'] = False
    with pytest.raises(ValueError, match='comparison evidence'):
        run_continuous(**data)
    data = tape(); data['plans'][0]['asof'] = data['plans'][0]['entry']
    with pytest.raises(ValueError, match='earlier session'):
        run_continuous(**data)
    data = tape(); data['cash_events'] = [dividend(), dividend()]
    with pytest.raises(ValueError, match='unique reviewed'):
        run_continuous(**data)


def sale(day, settlement, gross, gain, tax_class='equity'):
    return dict(date=day, settlement_date=settlement, isin='A-ISIN', quantity=-1,
                gross=D(gross), gain=D(gain), tax_class=tax_class)


def test_tax_cumulative_withholding_reserve_and_credit_not_double_charged():
    book = RetailBook(100000, '2020-01-03'); tax = OrdinaryTaxLedger(calendar())
    tax.enter(book, '2020-01')
    book.trades.append(sale('2020-01-03', '2020-01-07', '20000', '1000'))
    tax.refresh(book)
    assert not book.pending  # IRRF exactly R$1 is waived, equity gain exempt.
    book.trades.append(sale('2020-01-06', '2020-01-08', '10000', '500'))
    tax.refresh(book)
    assert tax.last['tax'] == 225
    assert tax.last['irrf'] == D('1.50')
    assert tax.last['darf'] == D('223.50')
    before = deepcopy(book.pending); tax.refresh(book)
    assert book.pending == before
    assert not book.fundable('99800', '2020-01-09')
    book.advance('2020-02-03'); tax.enter(book, '2020-02')
    assert tax.assessments[0]['darf'] == D('223.50')
    book.advance('2020-02-28')
    assert book.cash == 99775


def test_bdr_tax_small_darf_accumulates_and_equity_loss_carries_forward():
    book = RetailBook(1000, '2020-01-03'); tax = OrdinaryTaxLedger(calendar())
    tax.enter(book, '2020-01')
    book.trades.append(sale('2020-01-03', '2020-01-07', '500', '40', 'bdr'))
    tax.refresh(book)
    assert tax.unscheduled_liability == 6
    assert book.cash_buffer == 6
    assert not book.fundable(995, '2020-01-09')
    assert not book.pending
    book.advance('2020-02-03'); tax.enter(book, '2020-02')
    book.trades.append(sale('2020-02-03', '2020-02-05', '500', '40', 'bdr'))
    tax.refresh(book)
    assert tax.last['darf'] == 12
    assert tax.last['darf_due'] == '2020-03-28'
    book.trades.append(sale('2020-02-04', '2020-02-06', '100', '-90'))
    tax.refresh(book)
    assert tax.last['loss_carry'] == 50
    assert tax.unscheduled_liability == 6
    assert not book.pending


def bonus():
    return {'event_id': 'bonus', 'ticker': 'A', 'isin': 'A-ISIN', 'ex_date': '2020-01-15',
            'terms_known_on': '2020-01-14',
            'source_review': True, 'sources': ['synthetic'], 'tax_source': ['synthetic'],
            'basis_mode': 'bonus', 'removes_original': False, 'cash': [],
            'stocks': [{'ticker': 'A', 'isin': 'A-ISIN', 'ratio': '.1', 'credit_date': '2020-01-20',
                        'tax_class': 'equity', 'basis_per_share': '2'}]}


def test_bonus_preserves_original_tradability_and_locks_only_new_delivery():
    book = RetailBook(1000, '2020-01-15')
    book.positions['A'] = Holding('A-ISIN', 100, D(1000))
    apply_action(book, bonus())
    h = book.positions['A']
    assert h.quantity == 110 and h.basis == 1020
    assert h.available_quantity('2020-01-15') == 100
    assert h.available_quantity('2020-01-20') == 110
    q = {'date': book.day, 'isin': 'A-ISIN', 'standard': '10', 'fractional': '10'}
    with pytest.raises(ValueError, match='delivered position'):
        book.order('A', 'A-ISIN', -101, q, '2020-01-14', '2020-01-17')
    assert book.order('A', 'A-ISIN', -100, q, '2020-01-14', '2020-01-17')
    assert book.positions['A'].quantity == 10


def test_unreviewed_fraction_rejects_atomically_then_preserves_exact_basis():
    book = RetailBook(0, '2020-01-15'); book.positions['A'] = Holding('A-ISIN', 13, D(130))
    action = bonus(); action.update(basis_mode='carry', removes_original=True)
    action['stocks'][0].update(ticker='B', isin='B-ISIN', ratio='.5', basis_fraction='1')
    before = deepcopy(book.__dict__)
    with pytest.raises(KeyError):
        apply_action(book, action)
    assert book.__dict__ == before
    action['stocks'][0]['fraction_settlement'] = {'source_review': True, 'sources': ['synthetic'],
        'net_cash_per_fraction': '22', 'payment_date': '2020-02-03', 'available_on': '2020-02-04',
        'known_on': '2020-02-01'}
    log = apply_action(book, action)
    assert book.positions['B'].quantity == 6
    assert book.positions['B'].basis == 120
    assert log == [{'fraction': D('.5'), 'removed_basis': D(10), 'net_cash': D(11)}]
    assert book.cash == 0
    book.advance('2020-02-03'); assert book.cash == 0
    book.advance('2020-02-04'); assert book.cash == 11


def test_late_announced_cash_update_does_not_leak_into_earlier_nav_or_trades():
    data = tape(); event = dividend(); event['known_on'] = '2020-02-20'
    data['cash_events'] = [event]
    result = run_continuous(**data)
    early = next(r for r in result['snapshots'] if r['date'] == '2020-01-31')
    assert early['unvalued_claims'] == 1
    assert early['equity_including_receivables'] is None
    assert early['liquid_equity'] == 1100
    assert result['profit_excluding_unpaid_receivables'] == 150
    assert len(result['trades']) == 2
    assert result['cleared_cash_on_last_obligation_date'] == 1150


def test_reverse_split_then_split_must_not_be_cancelled_to_a_noop():
    book = RetailBook(0, '2020-01-15'); book.positions['A'] = Holding('A-ISIN', 143, D(1430))
    action = bonus(); action.update(basis_mode='carry', removes_original=True)
    action['stocks'][0].update(ratio='1', rounding_lot=100, basis_fraction='1',
        fraction_settlement={'source_review': True, 'sources': ['synthetic'],
            'net_cash_per_fraction': '15', 'payment_date': '2020-02-03',
            'available_on': '2020-02-04', 'known_on': '2020-02-01'})
    apply_action(book, action)
    assert book.positions['A'].quantity == 100
    assert book.positions['A'].basis == 1000
    assert book.rights['bonus:fraction:0']['net'] == 645
    assert book.cash == 0


def test_documented_trading_before_credit_requires_delivery_by_sale_settlement():
    book = RetailBook(0, '2020-01-15')
    book.positions['A'] = Holding('A-ISIN', 10, D(100), available_on='2020-01-20',
                                  tradable_on='2020-01-15')
    q = {'date': book.day, 'isin': 'A-ISIN', 'standard': '10', 'fractional': '10'}
    with pytest.raises(ValueError, match='delivered position'):
        book.order('A', 'A-ISIN', -10, q, '2020-01-14', '2020-01-17')
    assert book.order('A', 'A-ISIN', -10, q, '2020-01-14', '2020-01-20')


def test_partial_precredit_sale_consumes_only_the_usable_delivery_lots():
    book = RetailBook(0, '2020-01-15')
    book.positions['A'] = Holding('A-ISIN', 100, D(1000), locked_deliveries=[
        {'quantity': 40, 'credit_date': '2020-01-20', 'tradable_on': '2020-01-15'},
        {'quantity': 30, 'credit_date': '2020-01-23', 'tradable_on': None}])
    q = {'date': book.day, 'isin': 'A-ISIN', 'standard': '10', 'fractional': '10'}
    # Sell 30 already delivered + 20 legally tradable, leaving 20 + 30 pending.
    assert book.order('A', 'A-ISIN', -50, q, '2020-01-14', '2020-01-20', 0)
    h = book.positions['A']
    assert h.quantity == 50 and h.basis == 500
    assert h.available_quantity('2020-01-16', '2020-01-20') == 20
    assert h.available_quantity('2020-01-20') == 20
    assert h.available_quantity('2020-01-23') == 50
    assert [r['quantity'] for r in h.locked_deliveries] == [20, 30]


def test_purchase_merges_with_a_pending_delivery_without_unlocking_it():
    book = RetailBook(1000, '2020-01-15')
    book.positions['A'] = Holding('A-ISIN', 10, D(100), available_on='2020-01-23')
    q = {'date': book.day, 'isin': 'A-ISIN', 'standard': '10', 'fractional': '10'}
    assert book.order('A', 'A-ISIN', 20, q, '2020-01-14', '2020-01-20', 0)
    h = book.positions['A']
    assert h.quantity == 30 and h.basis == 300
    assert h.available_quantity('2020-01-16') == 20
    assert h.available_quantity('2020-01-23') == 30


def test_multiple_deliveries_merge_without_double_locking_the_base_position():
    book = RetailBook(0, '2020-01-15')
    book.positions['A'] = Holding('A-ISIN', 100, D(1000), available_on='2020-01-20')
    apply_action(book, bonus())
    h = book.positions['A']
    assert h.quantity == 110 and h.available_quantity('2020-01-15') == 0
    assert h.available_quantity('2020-01-20') == 110


def test_future_corporate_quantity_information_rejected_without_mutation():
    book = RetailBook(0, '2020-01-15'); book.positions['A'] = Holding('A-ISIN', 100, D(1000))
    action = bonus(); action['terms_known_on'] = '2020-01-20'
    before = deepcopy(book.__dict__)
    with pytest.raises(ValueError, match='future corporate quantity'):
        apply_action(book, action)
    assert book.__dict__ == before


def test_delayed_plan_and_weekend_settlement_do_not_pass_next_session_protocol():
    data = tape(); data['plans'][0]['entry'] = '2020-01-06'
    with pytest.raises(ValueError, match='next session'):
        run_continuous(**data)
    data = tape(); data['settlements']['2020-01-03'] = '2020-01-04'
    with pytest.raises(ValueError, match='later exchange session'):
        run_continuous(**data)
