"""Offline continuous research entry point with a mandatory evidence gate.

Run: python -m stocks_predictor.continuous_research --inputs DIR --output FILE
Exit 0: both portfolios completed for every registered case.
Exit 2: evidence is incomplete; no historical profit has been emitted.
Exit 1: invalid input, failed integrity check or execution error.
"""
import argparse
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path

from stocks_predictor.continuous_cash import run_continuous
from stocks_predictor.retail_cash import execution_readiness, iso, number


H19_PROTOCOL_SHA256 = '721f1ce6f8d5f0dcaa89e75aa5226f2cad9de9d9774e1902d675ba8d6002d115'
H19_OBSERVATION_SHA256 = 'c47fcca89d07e2064c1ba6ebc7a1f1dc763473a1364291284dfe6d761d7e9128'


def validate_contract(base, manifest, protocol, index):
    """A self-consistent manifest alone cannot certify a registered experiment."""
    capital = [number(v) for v in protocol['capital_brl']]
    costs = [number(v) for v in protocol['one_way_cost_rates']]
    if (not capital or not costs or len(set(capital)) != len(capital) or len(set(costs)) != len(costs)
            or any(c <= 0 for c in capital) or any(not 0 <= c < 1 for c in costs)):
        raise ValueError('nonempty unique valid capital and cost cases required')
    sessions = index['sessions']
    if not sessions or sessions != sorted(set(sessions)) or any(iso(d) != d for d in sessions):
        raise ValueError('unique chronological sessions required')
    if iso(index['start']) >= iso(index['end']):
        raise ValueError('invalid replay endpoints')
    if set(index['plans']) != {'strategy', 'comparison'}:
        raise ValueError('strategy and comparison plans required')
    schedules = []
    for plans in index['plans'].values():
        if len(plans) < 2 or plans[-1]['members'] or any(not p['members'] for p in plans[:-1]):
            raise ValueError('nonempty plans and explicit liquidation required')
        if plans[0]['asof'] != index['start'] or plans[-1]['entry'] != index['end']:
            raise ValueError('index endpoints differ from replay plans')
        if [p['entry'] for p in plans] != sorted({p['entry'] for p in plans}):
            raise ValueError('unique chronological plans required')
        for p in plans:
            if (p['asof'] not in sessions or p['entry'] not in sessions
                    or sessions.index(p['entry']) != sessions.index(p['asof']) + 1):
                raise ValueError('plan must execute in the next session')
            delivery = index['settlements'].get(p['entry'])
            if delivery not in sessions or delivery <= p['entry']:
                raise ValueError('settlement must be a later exchange session')
            if len({m['ticker'] for m in p['members']}) != len(p['members']):
                raise ValueError('duplicate plan member')
            for m in p['members']:
                if (type(m['lot']) is not int or m['lot'] <= 0 or m['tax_class'] not in {'equity', 'bdr'}
                        or m['lot'] != index['security_lots'].get(m['ticker']) or not m['isin']):
                    raise ValueError('invalid member identity or trading lot')
        schedules.append([(p['asof'], p['entry']) for p in plans])
    if schedules[0] != schedules[1]:
        raise ValueError('asymmetric comparison schedule')
    # Synthetic fixtures are labelled explicitly in all results. Production
    # research must bind both protocol bytes and actual membership to the
    # independently frozen observation, not to caller-supplied hashes alone.
    if protocol.get('protocol') == 'SYNTHETIC_ENGINE_TEST':
        return 'SYNTHETIC_ENGINE_TEST'
    if protocol.get('protocol') != 'H19_QUARTERLY_RETAIL_CASH_1':
        raise ValueError('unknown registered research protocol')
    if manifest['protocol.json'] != H19_PROTOCOL_SHA256:
        raise ValueError('registered H19 protocol changed')
    source = protocol['source_observation']
    if (manifest.get(source) != H19_OBSERVATION_SHA256
            or index.get('source_observation_sha256') != H19_OBSERVATION_SHA256):
        raise ValueError('frozen H19 observation absent or changed')
    observation = read(base / source)
    trials = [t for t in observation['trials'] if t['family'] == 'H19' and t['holding_months'] == 3]
    if len(trials) != 1:
        raise ValueError('ambiguous frozen H19 trial')
    periods = [p for p in trials[0]['periods'] if any(m['selected'] for m in p['members'])]
    for portfolio, selected in [('strategy', True), ('comparison', False)]:
        expected = [{'asof': p['asof'], 'entry': p['entry'], 'members': [
            {'ticker': m['ticker'], 'isin': m['isin'], 'lot': 1 if m['ticker'] == 'JBSS32' else 100,
             'tax_class': 'bdr' if m['ticker'] == 'JBSS32' else 'equity'}
            for m in p['members'] if not selected or m['selected']]} for p in periods]
        endpoint = periods[-1]['exit']
        expected.append({'asof': sessions[sessions.index(endpoint)-1], 'entry': endpoint, 'members': []})
        if index['plans'][portfolio] != expected:
            raise ValueError('replay plans differ from frozen H19 selection')
    return 'REGISTERED_H19_DISCOVERY'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'), parse_float=Decimal)


def verify_manifest(base):
    manifest = read(base / 'SHA256.json')
    if not manifest:
        raise ValueError('empty input manifest')
    for name, expected in manifest.items():
        path = (base / name).resolve()
        if not path.is_relative_to(base.resolve()) or not path.is_file():
            raise ValueError('invalid manifest path: ' + name)
        with path.open('rb') as stream:
            actual = hashlib.file_digest(stream, 'sha256').hexdigest()
        if actual != expected:
            raise ValueError('input checksum mismatch: ' + name)
    return manifest


def load_quotes(base, index):
    """Validate all supplied quote records even when economic evidence is missing."""
    quotes = {}
    rows = 0
    sessions = set(index['sessions'])
    for source in index['sources']:
        with (base / source['quotes']).open(encoding='utf-8') as stream:
            for line in stream:
                r = json.loads(line)
                if r['market_type'] not in {'010', '020'}:
                    raise ValueError('unsupported execution market')
                if iso(r['date']) not in sessions or not index['start'] <= r['date'] <= index['end']:
                    raise ValueError('quote outside registered trading calendar')
                if number(r['open']) <= 0 or number(r['close']) <= 0:
                    raise ValueError('nonpositive execution quote')
                key = (r['date'], r['ticker'])
                q = quotes.setdefault(key, {'date': r['date'], 'isin': r['isin'],
                    'lot': index['security_lots'][r['ticker']]})
                if q['isin'] != r['isin']:
                    raise ValueError('ambiguous quote identity')
                field = 'standard' if r['market_type'] == '010' else 'fractional'
                if field in q:
                    raise ValueError('duplicate execution quote')
                q[field] = r['open']
                if field == 'standard':
                    q['close'] = r['close']
                rows += 1
    if not rows:
        raise ValueError('empty execution quote tape')
    return quotes, rows


def inspect_inputs(base):
    manifest = verify_manifest(base)
    required = {'protocol.json', 'quote-tape-index.json', 'evidence.json',
                'cash-events.json', 'corporate-actions.json', 'tax-calendar.json'}
    if not required <= set(manifest):
        raise ValueError('required replay inputs are outside the manifest')
    protocol = read(base / 'protocol.json')
    index = read(base / 'quote-tape-index.json')
    evidence = read(base / 'evidence.json')
    cash = read(base / 'cash-events.json')
    actions = read(base / 'corporate-actions.json')
    tax = read(base / 'tax-calendar.json')
    validate_contract(base, manifest, protocol, index)
    for source in index['sources']:
        if source['quotes'] not in manifest or manifest[source['quotes']] != source['quotes_sha256']:
            raise ValueError('quote tape not covered by its source manifest')
    gate = execution_readiness(evidence['required_intervals'], evidence['cash_coverage'],
        cash, evidence['action_gaps'], evidence['execution_checks'])
    gate['issues'].extend(evidence.get('additional_issues', []))
    months = sorted({d[:7] for d in index['sessions']
                     if index['start'] <= d <= index['end']})
    for month in months:
        row = tax.get(month, {})
        if row.get('source_review') is not True or not row.get('sources') or not row.get('due_date'):
            gate['issues'].append({'kind': 'TAX_CALENDAR_MONTH', 'month': month})
    for row in cash:
        if not row.get('known_on'):
            gate['issues'].append({'kind': 'CASH_KNOWLEDGE_DATE', 'event': row.get('event_id')})
    required_actions = {r['event_id'] for r in evidence['required_actions']}
    approved = {r['event_id'] for r in actions if r.get('source_review') is True
                and r.get('sources') and r.get('tax_source')}
    for event_id in sorted(required_actions - approved):
        gate['issues'].append({'kind': 'CORPORATE_EVENT_INPUT', 'event': event_id})
    for event in actions:
        try:
            if iso(event.get('terms_known_on')) > iso(event['ex_date']):
                raise ValueError('future quantity terms')
        except ValueError:
            gate['issues'].append({'kind': 'CORPORATE_QUANTITY_KNOWLEDGE', 'event': event.get('event_id')})
    gate['ready'] = not gate['issues']
    return protocol, index, cash, actions, tax, gate, len(manifest)


def execute(base):
    protocol, index, cash, actions, tax, gate, count = inspect_inputs(base)
    quotes, quote_rows = load_quotes(base, index)
    common = {'protocol': protocol, 'verified_input_files': count,
              'validated_quote_records': quote_rows,
              'evidence_kind': ('SYNTHETIC_ENGINE_TEST' if protocol.get('protocol') == 'SYNTHETIC_ENGINE_TEST'
                                else 'REGISTERED_H19_DISCOVERY'),
              'full_history_executed': False, 'profit': None,
              'new_historical_return_evaluations': 0,
              'issue_counts': dict(Counter(r['kind'] for r in gate['issues'])),
              'issues': gate['issues']}
    if not gate['ready']:
        return 2, {'status': 'BLOCKED_MISSING_EVIDENCE', **common}
    results = []
    # No partial case results are returned if a later path fails.
    for capital in protocol['capital_brl']:
        for cost in protocol['one_way_cost_rates']:
            pair = {}
            try:
                for portfolio in ('strategy', 'comparison'):
                    pair[portfolio] = run_continuous(capital, cost, index['plans'][portfolio],
                        quotes, index['sessions'], index['settlements'], cash, actions, tax, True)
            except (ValueError, KeyError, TypeError) as exc:
                return 1, {**common, 'status': 'EXECUTION_FAILURE_NO_PARTIAL_PROFIT',
                    'error': str(exc), 'attempted_pair_evaluations': len(results) + 1,
                    'completed_pairs_suppressed': len(results),
                    'new_historical_return_evaluations': (0 if common['evidence_kind'] == 'SYNTHETIC_ENGINE_TEST'
                                                          else len(results) + 1)}
            results.append({'capital_brl': capital, 'one_way_cost_rate': cost, 'portfolios': pair})
    return 0, {**common, 'status': ('COMPLETE_SYNTHETIC_TEST_NOT_PROFIT_EVIDENCE'
               if common['evidence_kind'] == 'SYNTHETIC_ENGINE_TEST'
               else 'COMPLETE_HISTORICAL_REPLAY_NOT_PROOF_OF_EDGE'),
               'full_history_executed': True, 'cases': results,
               'synthetic_pair_evaluations': len(results) if common['evidence_kind'] == 'SYNTHETIC_ENGINE_TEST' else 0,
               'new_historical_return_evaluations': (0 if common['evidence_kind'] == 'SYNTHETIC_ENGINE_TEST'
                                                      else len(results))}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        code, result = execute(args.inputs)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        code, result = 1, {'status': 'INVALID_INPUT_OR_EXECUTION_FAILURE',
            'full_history_executed': False, 'profit': None,
            'new_historical_return_evaluations': 0, 'error': str(exc)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k not in ('cases', 'issues', 'protocol')},
                     ensure_ascii=False, default=str))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
