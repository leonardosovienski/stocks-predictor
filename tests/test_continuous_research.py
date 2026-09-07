"""Exercise the installed-style driver, integrity gate and paired replay."""
import hashlib
import json

from stocks_predictor.continuous_research import execute, main
from tests.test_continuous_cash import dividend, tape


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bundle(base, ready=True):
    data = tape()
    rows = []
    for (day, ticker), q in data['quotes'].items():
        for market, field in [('010', 'standard'), ('020', 'fractional')]:
            rows.append(dict(date=day, ticker=ticker, isin=q['isin'], market_type=market,
                             open=q[field], close=q['close']))
    path = base / 'quotes.jsonl'
    path.write_text(''.join(json.dumps(r) + '\n' for r in rows), encoding='utf-8')
    interval = ['A', 'A-ISIN', '2020-01-03', '2020-03-03']
    files = {
        'protocol.json': {'capital_brl': [1000, 2000], 'one_way_cost_rates': ['0', '.0018']},
        'quote-tape-index.json': {
            'start': data['plans'][0]['asof'], 'end': data['plans'][-1]['entry'],
            'sessions': data['sessions'], 'settlements': data['settlements'],
            'sources': [{'quotes': path.name, 'quotes_sha256': sha(path)}],
            'security_lots': {'A': 100},
            'plans': {'strategy': data['plans'], 'comparison': data['plans']}},
        'tax-calendar.json': data['tax_calendar'], 'corporate-actions.json': [],
        'cash-events.json': [dividend()],
        'evidence.json': {
            'required_intervals': [interval], 'required_actions': [], 'action_gaps': [],
            'cash_coverage': [{'interval': interval, 'verified': ready, 'sources': ['synthetic']}],
            'execution_checks': {name: {'verified': True, 'sources': ['synthetic']} for name in
                ('quotes', 'corporate_actions', 'tax_schedule', 'cash_coverage_inventory')}}}
    for name, value in files.items():
        (base / name).write_text(json.dumps(value), encoding='utf-8')
    manifest = {p.name: sha(p) for p in base.iterdir() if p.is_file()}
    (base / 'SHA256.json').write_text(json.dumps(manifest), encoding='utf-8')


def test_all_registered_pairs_run_on_persistent_books(tmp_path):
    bundle(tmp_path)
    code, result = execute(tmp_path)
    assert code == 0 and result['full_history_executed']
    assert len(result['cases']) == 4
    assert result['new_historical_return_evaluations'] == 4
    zero_cost = [r for r in result['cases'] if r['one_way_cost_rate'] == '0']
    for r in zero_cost:
        for portfolio in r['portfolios'].values():
            assert portfolio['profit_excluding_unpaid_receivables'] == r['capital_brl'] * 15 // 100
            assert len(portfolio['trades']) == 2


def test_missing_evidence_stops_before_any_portfolio_return(tmp_path):
    bundle(tmp_path, ready=False)
    code, result = execute(tmp_path)
    assert code == 2 and not result['full_history_executed']
    assert result['profit'] is None and 'cases' not in result
    assert result['issue_counts'] == {'CASH_COVERAGE': 1}
    assert result['new_historical_return_evaluations'] == 0


def test_changed_source_returns_input_error_without_profit(tmp_path):
    bundle(tmp_path)
    (tmp_path / 'quotes.jsonl').write_text('{}\n', encoding='utf-8')
    output = tmp_path / 'result.json'
    code = main(['--inputs', str(tmp_path), '--output', str(output)])
    result = json.loads(output.read_text(encoding='utf-8'))
    assert code == 1 and result['profit'] is None
    assert 'checksum mismatch' in result['error']
