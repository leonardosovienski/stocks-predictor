from decimal import Decimal as D

import hashlib
import json

import pytest

from tools.assess_execution_feasibility import economics, entry_case, load_unit_reviews


def test_cost_only_entry_keeps_signal_units_and_prices_fractional_remainder():
    plan = {'asof': '2020-01-02', 'entry': '2020-01-03', 'members': [
        {'ticker': 'A', 'isin': 'I', 'tax_class': 'equity', 'lot': 100}]}
    quotes = {('2020-01-02', 'A'): {'date': '2020-01-02', 'isin': 'I', 'close': 10},
              ('2020-01-03', 'A'): {'date': '2020-01-03', 'isin': 'I', 'standard': 10, 'fractional': 20}}
    result = entry_case(1100, 0, plan, quotes, '2020-01-07', [])
    assert result['requested_shares'] == 110
    assert result['filled_shares'] == 105  # 100*10 + 5*20, not 110 shares at the board-lot price
    assert result['standard_tickets'] == result['fractional_tickets'] == 1
    assert result['settled_residual_cash_brl'] == 0
    assert result['actual_continuous_turnover'] is None and result['profit'] is None
    blocked = entry_case(1100, 0, plan, quotes, '2020-01-07', [
        {'ticker': 'A', 'isin': 'I', 'ex_date': '2020-01-03', 'event_id': 'split'}])
    assert blocked['status'] == 'BLOCKED' and 'orders' not in blocked


def test_source_review_unblocks_only_unchanged_original_units_and_invents_no_bonus(tmp_path):
    raw = tmp_path/'source.txt'; raw.write_text('Synthetic original class unchanged', encoding='utf-8')
    rows = [{'event_id': 'bonus', 'ticker': 'A', 'isin': 'I', 'ex_date': '2020-01-03',
        'source_review': True, 'sources': [{'file': 'source.txt', 'sha256': hashlib.sha256(raw.read_bytes()).hexdigest()}],
        'kind': 'BONUS_IN_DIFFERENT_CLASS', 'removes_original': False,
        'original_share_units_unchanged': True, 'delivered_tickers': ['B'], 'terms_known_on': '2020-01-02'}]
    path=tmp_path/'review.json'; path.write_text(json.dumps(rows), encoding='utf-8')
    reviews=load_unit_reviews(path)
    plan={'asof': '2020-01-02', 'entry': '2020-01-03', 'members': [
        {'ticker': 'A', 'isin': 'I', 'tax_class': 'equity', 'lot': 100}]}
    quotes={('2020-01-02', 'A'): {'date': '2020-01-02', 'isin': 'I', 'close': 10},
            ('2020-01-03', 'A'): {'date': '2020-01-03', 'isin': 'I', 'standard': 10, 'fractional': 10}}
    # Real ordinary-action requirements omit ISIN; bind the review to the
    # independently frozen plan's identity instead of assuming that field.
    requirement=[{'event_id': 'bonus', 'ticker': 'A', 'ex_date': '2020-01-03'}]
    result=entry_case(1000, 0, plan, quotes, '2020-01-07', requirement, reviews)
    assert result['filled_shares'] == 100 and result['bonus_rights_received_by_new_entry'] == 0
    assert [r['ticker'] for r in result['orders']] == ['A']
    reviews[0]['terms_known_on']='2020-01-04'
    assert entry_case(1000, 0, plan, quotes, '2020-01-07', requirement, reviews)['status'] == 'BLOCKED'
    raw.write_text('Changed source', encoding='utf-8')
    with pytest.raises(ValueError, match='checksum'):
        load_unit_reviews(path)


def test_economic_hurdle_keeps_sunk_cost_out_and_amortizes_only_future_work():
    spec = {'capital_brl': [10000], 'maintenance_hours_per_month': [2],
            'hourly_opportunity_cost_brl': [25], 'fixed_cost_brl_per_year': [120],
            'future_reconstruction_hours': [20], 'desired_annual_incremental_profit_brl': [500],
            'amortization_years': 3, 'net_incremental_return_before_maintenance': ['.05']}
    row = economics(spec)[0]
    assert row['annual_recurring_cost_brl'] == 720
    assert abs(row['required_net_incremental_return_before_overhead'] - D('0.1386666666666666666666666667')) < D('1e-26')
    assert abs(row['assumed_edge_scenarios'][0]['incremental_profit_after_overhead_brl']
               - D('-386.6666666666666666666666667')) < D('1e-24')
