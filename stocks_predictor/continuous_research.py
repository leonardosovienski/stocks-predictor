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
from stocks_predictor.retail_cash import execution_readiness


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
    gate['ready'] = not gate['issues']
    return protocol, index, cash, actions, tax, gate, len(manifest)


def execute(base):
    protocol, index, cash, actions, tax, gate, count = inspect_inputs(base)
    common = {'protocol': protocol, 'verified_input_files': count,
              'full_history_executed': False, 'profit': None,
              'new_historical_return_evaluations': 0,
              'issue_counts': dict(Counter(r['kind'] for r in gate['issues'])),
              'issues': gate['issues']}
    if not gate['ready']:
        return 2, {'status': 'BLOCKED_MISSING_EVIDENCE', **common}
    quotes = {}
    for source in index['sources']:
        with (base / source['quotes']).open(encoding='utf-8') as stream:
            for line in stream:
                r = json.loads(line)
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
                    'new_historical_return_evaluations': len(results) + 1}
            results.append({'capital_brl': capital, 'one_way_cost_rate': cost, 'portfolios': pair})
    return 0, {**common, 'status': 'COMPLETE_HISTORICAL_REPLAY_NOT_PROOF_OF_EDGE',
               'full_history_executed': True, 'cases': results,
               'new_historical_return_evaluations': len(results)}


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
