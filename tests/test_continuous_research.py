"""Exercise the installed-style driver, integrity gate and paired replay."""
import hashlib
import json

import pytest

from stocks_predictor.continuous_research import execute, main
from tests.test_continuous_cash import dividend, tape


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bundle(base, ready=True):
    data = tape()
    rows = []
    for (day, ticker), q in data['quotes'].items():
        if day > data['plans'][-1]['entry']:
            continue
        for market, field in [('010', 'standard'), ('020', 'fractional')]:
            rows.append(dict(date=day, ticker=ticker, isin=q['isin'], market_type=market,
                             open=q[field], close=q['close']))
    path = base / 'quotes.jsonl'
    path.write_text(''.join(json.dumps(r) + '\n' for r in rows), encoding='utf-8')
    interval = ['A', 'A-ISIN', '2020-01-03', '2020-03-03']
    files = {
        'protocol.json': {'protocol': 'SYNTHETIC_ENGINE_TEST', 'capital_brl': [1000, 2000],
                          'one_way_cost_rates': ['0', '.0018']},
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
    assert result['status'] == 'COMPLETE_SYNTHETIC_TEST_NOT_PROFIT_EVIDENCE'
    assert result['new_historical_return_evaluations'] == 0
    assert result['synthetic_pair_evaluations'] == 4
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


def replace_input(base, name, value):
    (base / name).write_text(json.dumps(value), encoding='utf-8')
    manifest = json.loads((base / 'SHA256.json').read_text(encoding='utf-8'))
    manifest[name] = sha(base / name)
    (base / 'SHA256.json').write_text(json.dumps(manifest), encoding='utf-8')


@pytest.mark.parametrize('field,value', [('capital_brl', []), ('one_way_cost_rates', []),
    ('capital_brl', [1000, 1000]), ('capital_brl', [0]), ('one_way_cost_rates', [-1])])
def test_empty_or_invalid_cases_cannot_report_success_without_running(tmp_path, field, value):
    bundle(tmp_path)
    protocol = json.loads((tmp_path / 'protocol.json').read_text(encoding='utf-8'))
    protocol[field] = value; replace_input(tmp_path, 'protocol.json', protocol)
    with pytest.raises(ValueError, match='nonempty unique valid'):
        execute(tmp_path)


def test_manifest_does_not_authorize_a_different_production_protocol(tmp_path):
    bundle(tmp_path)
    protocol = json.loads((tmp_path / 'protocol.json').read_text(encoding='utf-8'))
    protocol['protocol'] = 'H19_QUARTERLY_RETAIL_CASH_1'
    replace_input(tmp_path, 'protocol.json', protocol)
    with pytest.raises(ValueError, match='registered H19 protocol changed'):
        execute(tmp_path)


def test_plans_bound_to_frozen_members_even_after_local_manifest_rebuilt(tmp_path, monkeypatch):
    import stocks_predictor.continuous_research as driver
    bundle(tmp_path)
    index = json.loads((tmp_path / 'quote-tape-index.json').read_text(encoding='utf-8'))
    periods = [{'asof': p['asof'], 'entry': p['entry'], 'exit': index['plans']['strategy'][i+1]['entry'],
        'members': [{**m, 'selected': True} for m in p['members']]}
        for i, p in enumerate(index['plans']['strategy'][:-1])]
    source = 'frozen-fixture.json'
    replace_input(tmp_path, source, {'trials': [{'family': 'H19', 'holding_months': 3, 'periods': periods}]})
    source_sha = sha(tmp_path / source)
    protocol = json.loads((tmp_path / 'protocol.json').read_text(encoding='utf-8'))
    protocol.update(protocol='H19_QUARTERLY_RETAIL_CASH_1', source_observation=source)
    replace_input(tmp_path, 'protocol.json', protocol)
    index['source_observation_sha256'] = source_sha
    replace_input(tmp_path, 'quote-tape-index.json', index)
    monkeypatch.setattr(driver, 'H19_PROTOCOL_SHA256', sha(tmp_path / 'protocol.json'))
    monkeypatch.setattr(driver, 'H19_OBSERVATION_SHA256', source_sha)
    # Test the binding separately from any return calculation.
    driver.inspect_inputs(tmp_path)
    index['plans']['strategy'][0]['members'][0]['isin'] = 'CHANGED-ISIN'
    replace_input(tmp_path, 'quote-tape-index.json', index)
    with pytest.raises(ValueError, match='differ from frozen H19'):
        driver.inspect_inputs(tmp_path)


def test_index_cannot_hide_a_longer_replay_or_a_different_comparison_schedule(tmp_path):
    bundle(tmp_path)
    index = json.loads((tmp_path / 'quote-tape-index.json').read_text(encoding='utf-8'))
    index['end'] = '2020-02-28'; replace_input(tmp_path, 'quote-tape-index.json', index)
    with pytest.raises(ValueError, match='endpoints differ'):
        execute(tmp_path)


def test_economic_gate_does_not_hide_a_corrupt_quote_record(tmp_path):
    bundle(tmp_path, ready=False)
    path = tmp_path / 'quotes.jsonl'
    lines = path.read_text(encoding='utf-8').splitlines()
    row = json.loads(lines[0]); row['market_type'] = '030'; lines[0] = json.dumps(row)
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    manifest = json.loads((tmp_path / 'SHA256.json').read_text(encoding='utf-8'))
    manifest['quotes.jsonl'] = sha(path)
    (tmp_path / 'SHA256.json').write_text(json.dumps(manifest), encoding='utf-8')
    index = json.loads((tmp_path / 'quote-tape-index.json').read_text(encoding='utf-8'))
    index['sources'][0]['quotes_sha256'] = sha(path)
    replace_input(tmp_path, 'quote-tape-index.json', index)
    with pytest.raises(ValueError, match='unsupported execution market'):
        execute(tmp_path)
