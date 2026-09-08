from decimal import Decimal as D

from tools.assess_execution_feasibility import economics, entry_case


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
        {'ticker': 'A', 'ex_date': '2020-01-03', 'event_id': 'split'}])
    assert blocked['status'] == 'BLOCKED' and 'orders' not in blocked


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
