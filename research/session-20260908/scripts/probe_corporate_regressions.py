"""Three synthetic counterexamples, runnable with either runtime on PYTHONPATH."""
from copy import deepcopy
from decimal import Decimal
import json

from stocks_predictor import continuous_cash as engine
from stocks_predictor.retail_cash import Holding, RetailBook


def state():
    book = RetailBook(1000, '2020-01-15')
    book.positions['A'] = Holding('I', 13, Decimal(130))
    fingerprint = getattr(engine, 'portfolio_fingerprint', lambda _: 'LEGACY_HAS_NO_CONTEXT_BINDING')
    action = {'event_id': 'action', 'ticker': 'A', 'isin': 'I', 'ex_date': book.day,
        'terms_known_on': book.day, 'source_review': True, 'sources': ['synthetic'],
        'tax_source': ['synthetic'], 'basis_mode': 'carry', 'removes_original': True,
        'stocks': [{'ticker': 'B', 'isin': 'J', 'ratio': '.5', 'basis_fraction': '1',
            'tax_class': 'equity', 'credit_date': '2020-01-20', 'fraction_settlement': {
                'source_review': True, 'sources': ['synthetic'],
                'tax_treatment': 'reviewed_portfolio_net', 'portfolio_state_sha256': 'DIFFERENT_BOOK',
                'net_cash_per_fraction': '29', 'payment_date': '2020-02-10',
                'available_on': '2020-02-11', 'known_on': '2020-02-03'}}]}
    return book, action, fingerprint


rows = []
for case in ('net_fraction_reused_across_portfolios', 'compulsory_tax_reused_across_portfolios',
             'future_tax_debited_before_it_is_known'):
    book, action, fingerprint = state()
    if case != 'net_fraction_reused_across_portfolios':
        action.update(basis_mode='explicit_disposal', stocks=[], disposal_tax=[{
            'source_review': True, 'sources': ['synthetic'], 'tax_per_original': '1',
            'payment_date': '2020-02-28', 'known_on': '2020-01-15',
            'portfolio_state_sha256': 'DIFFERENT_BOOK'}])
        if case == 'future_tax_debited_before_it_is_known':
            action['disposal_tax'][0].update(known_on='2020-02-03', portfolio_state_sha256=fingerprint(book))
    before = deepcopy(book.__dict__)
    try:
        engine.apply_action(book, action)
        rows.append({'case': case, 'unsafe_input_accepted': True})
    except ValueError as exc:
        rows.append({'case': case, 'unsafe_input_accepted': False, 'error': str(exc),
                     'failed_atomically': before == book.__dict__})
print(json.dumps({'synthetic': True, 'new_historical_return_evaluations': 0, 'cases': rows}, indent=2))
