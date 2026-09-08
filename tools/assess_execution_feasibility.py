"""Cost-only diagnostics on frozen plans; never computes an investment return."""
import argparse
from collections import Counter, defaultdict
from decimal import Decimal
import hashlib
from itertools import product
import json
from pathlib import Path
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stocks_predictor.continuous_research import inspect_inputs, load_quotes, read  # noqa: E402
from stocks_predictor.retail_cash import RetailBook, integer_targets, iso, number  # noqa: E402


def entry_case(capital, cost, plan, quotes, settlement, action_requirements, unit_reviews=()):
    """Independent empty book, not a rebalance of previously simulated wealth."""
    result = {'capital_brl': capital, 'one_way_cost_rate': cost, 'signal_date': plan['asof'],
              'entry_date': plan['entry'], 'settlement_date': settlement,
              'target_names': len(plan['members']), 'status': 'BLOCKED',
              'actual_continuous_turnover': None, 'profit': None}
    names = {m['ticker'] for m in plan['members']}
    reviewed = {r['event_id']: r for r in unit_reviews}
    boundary = []
    applied = []
    for r in action_requirements:
        if r['ticker'] not in names or not plan['asof'] < r['ex_date'] <= plan['entry']:
            continue
        review = reviewed.get(r['event_id'], {})
        if (review.get('kind') == 'BONUS_IN_DIFFERENT_CLASS' and review.get('removes_original') is False
                and review.get('original_share_units_unchanged') is True
                and review.get('ticker') == r['ticker'] and review.get('isin') == r['isin']
                and review.get('ex_date') == r['ex_date'] and review.get('sources_verified') is True
                and iso(review['terms_known_on']) <= plan['entry']
                and review.get('delivered_tickers') and r['ticker'] not in review['delivered_tickers']):
            applied.append(r['event_id'])
        else:
            boundary.append(r['event_id'])
    if applied:
        result['unit_reviews_applied'] = applied
        result['bonus_rights_received_by_new_entry'] = 0
    if boundary:
        # No silent inference from a price factor, even in a cheap diagnostic.
        return {**result, 'reason': 'ENTRY_ACTION_REQUIRES_REVIEWED_ORDER_UNITS', 'events': boundary}
    try:
        identities = {m['ticker']: m for m in plan['members']}
        closes = {}
        for m in plan['members']:
            q = quotes[(plan['asof'], m['ticker'])]
            if q['isin'] != m['isin'] or q['date'] != plan['asof']:
                raise ValueError('signal identity mismatch')
            closes[m['ticker']] = q['close']
        targets = integer_targets(capital, closes)
        book = RetailBook(capital, plan['asof']); book.advance(plan['entry'])
        execution_quotes = {t: quotes[(plan['entry'], t)] for t in names}
        trades = book.rebalance(targets, execution_quotes, identities, plan['asof'], settlement, cost)
        book.advance(settlement)
    except (ValueError, KeyError, TypeError) as exc:
        return {**result, 'reason': str(exc)}
    amounts = {r['ticker']: r['quantity'] for r in trades}
    standard_tickets = sum(r['quantity'] >= identities[r['ticker']]['lot'] for r in trades)
    fractional_tickets = sum(r['quantity'] % identities[r['ticker']]['lot'] > 0 for r in trades)
    return {**result, 'status': 'SIMULATED_ENTRY_ONLY', 'funded_names': len(trades),
            'zero_share_targets': sum(q == 0 for q in targets.values()),
            'requested_shares': sum(targets.values()), 'filled_shares': sum(amounts.values()),
            'standard_tickets': standard_tickets, 'fractional_tickets': fractional_tickets,
            'traded_notional_brl': sum((r['gross'] for r in trades), Decimal(0)),
            'modeled_cost_brl': sum((r['costs'] for r in trades), Decimal(0)),
            'settled_residual_cash_brl': book.cash,
            'unfilled_shares': {t: q-amounts.get(t, 0) for t, q in targets.items() if q != amounts.get(t, 0)},
            'orders': trades}


def economics(spec):
    rows = []
    keys = ('capital_brl', 'maintenance_hours_per_month', 'hourly_opportunity_cost_brl',
            'fixed_cost_brl_per_year', 'future_reconstruction_hours', 'desired_annual_incremental_profit_brl')
    for values in product(*(spec[k] for k in keys)):
        capital, hours, wage, fixed, rebuild, goal = map(number, values)
        recurring = 12 * hours * wage + fixed
        annual_rebuild = rebuild * wage / number(spec['amortization_years'])
        required = (recurring + annual_rebuild + goal) / capital
        rows.append({**dict(zip(keys, values)), 'annual_recurring_cost_brl': recurring,
            'annualized_future_reconstruction_brl': annual_rebuild,
            'required_net_incremental_return_before_overhead': required,
            'assumed_edge_scenarios': [
                {'assumed_net_incremental_return': edge,
                 'incremental_profit_after_overhead_brl': capital*number(edge)-recurring-annual_rebuild}
                for edge in spec['net_incremental_return_before_maintenance']]})
    return rows


def summarize(cases):
    grouped = defaultdict(list)
    for r in cases:
        grouped[(r['portfolio'], str(r['capital_brl']), str(r['one_way_cost_rate']))].append(r)
    output = []
    for (portfolio, capital, cost), rows in sorted(grouped.items()):
        usable = [r for r in rows if r['status'] == 'SIMULATED_ENTRY_ONLY']
        summary = {'portfolio': portfolio, 'capital_brl': capital, 'one_way_cost_rate': cost,
                   'attempted_dates': len(rows), 'completed_dates': len(usable),
                   'blocked_dates': [{'date': r['entry_date'], 'reason': r['reason']} for r in rows
                                     if r['status'] != 'SIMULATED_ENTRY_ONLY']}
        for field in ('target_names', 'funded_names', 'zero_share_targets', 'standard_tickets',
                      'fractional_tickets', 'traded_notional_brl', 'modeled_cost_brl', 'settled_residual_cash_brl'):
            data = [r[field] for r in usable]
            summary[field] = {'min': min(data), 'median': statistics.median(data), 'max': max(data)} if data else None
        output.append(summary)
    return output


def workload(evidence, cash):
    # Merge solely for planning document acquisition; this never certifies a
    # merged interval and never removes an original gate requirement.
    spans = defaultdict(list)
    for ticker, isin, start, end in evidence['required_intervals']:
        spans[(ticker, isin)].append((start, end))
    merged = []
    for (ticker, isin), intervals in sorted(spans.items()):
        current = []
        for start, end in sorted(intervals):
            if current and start <= current[-1][1]:
                current[-1][1] = max(current[-1][1], end)
            else:
                current.append([start, end])
        merged.extend([[ticker, isin, a, b] for a, b in current])
    return {'required_intervals': len(evidence['required_intervals']),
            'distinct_ticker_isin_pairs': len(spans), 'merged_acquisition_spans': len(merged),
            'spans_for_source_planning_only': merged,
            'cash_rows': len(cash), 'payment_dates_missing': sum(not r.get('payment_date') for r in cash),
            'net_amounts_missing': sum(r.get('net_per_share') is None for r in cash),
            'unreviewed_rows': sum(r.get('source_review') is not True for r in cash),
            'known_payment_without_availability': [r['event_id'] for r in cash
                                                 if r.get('payment_date') and not r.get('available_on')],
            'corporate_requirements': len(evidence['required_actions']),
            'corporate_requirements_by_kind': dict(Counter(r['kind'] for r in evidence['required_actions']))}


def load_unit_reviews(path):
    """Source review supplies units only, never entitlements or H19 approval."""
    if path is None:
        return []
    rows = read(path)
    if not rows or len({r['event_id'] for r in rows}) != len(rows):
        raise ValueError('nonempty unique entry-unit reviews required')
    for row in rows:
        if row.get('source_review') is not True or not row.get('sources'):
            raise ValueError('reviewed entry-unit sources required')
        for source in row['sources']:
            raw = (path.parent / source['file']).resolve()
            if not raw.is_relative_to(path.parent.resolve()):
                raise ValueError('entry-unit source outside its bundle')
            if hashlib.sha256(raw.read_bytes()).hexdigest() != source['sha256']:
                raise ValueError('entry-unit source checksum mismatch')
        row['sources_verified'] = True
    return rows


def assess(inputs, protocol_path, unit_review_path=None):
    spec = read(protocol_path)
    if spec['protocol'] != 'H19_EXECUTION_FEASIBILITY_20260908_1':
        raise ValueError('unknown feasibility protocol')
    _, index, cash, _, _, gate, count = inspect_inputs(inputs)
    quotes, quote_count = load_quotes(inputs, index)
    evidence = read(inputs/'evidence.json')
    unit_reviews = load_unit_reviews(unit_review_path)
    cases = []
    for portfolio, plans in index['plans'].items():
        for plan in plans[:-1]:
            for capital, cost in product(spec['entry_diagnostic']['capital_brl'],
                                        spec['entry_diagnostic']['one_way_cost_rates']):
                row = entry_case(capital, cost, plan, quotes, index['settlements'][plan['entry']],
                                 evidence['required_actions'], unit_reviews)
                cases.append({'portfolio': portfolio, **row})
    result = {'protocol': spec['protocol'], 'protocol_sha256': hashlib.sha256(protocol_path.read_bytes()).hexdigest(),
            'input_manifest_sha256': hashlib.sha256((inputs/'SHA256.json').read_bytes()).hexdigest(),
            'status': 'COMPLETE_FEASIBILITY_DIAGNOSTIC_NOT_A_RETURN_BACKTEST',
            'verified_input_files': count, 'validated_quote_records': quote_count,
            'registered_h19_evidence_ready': gate['ready'],
            'attempted_entry_snapshots': len(cases), 'summaries': summarize(cases), 'entry_cases': cases,
            'economic_scenarios': economics(spec['annual_economic_scenarios']),
            'source_workload': workload(evidence, cash), 'historical_profit_brl': None,
            'actual_continuous_turnover': None, 'historical_risk_adjusted_excess_return': None,
            'new_historical_return_evaluations': 0,
            'limitations': [
                'Independent empty-book entries are not the turnover, cash path or profit of continuous H19.',
                'Opening quotes and assumed costs do not prove fills, spreads or broker cent rounding.',
                'Blocked dates remain in the report; no annual result is extrapolated from the successful subset.',
                'Maintenance/reconstruction/edge inputs are scenarios, not preferences or forecasts.',
                'Overhead scenarios assume zero comparator overhead; subtract its documented overhead if nonzero.',
                'A positive historical excess return would still need risk matching and independent future evidence.']}
    if unit_review_path is not None:
        result['entry_unit_review_sha256'] = hashlib.sha256(unit_review_path.read_bytes()).hexdigest()
        result['entry_unit_reviews'] = unit_reviews
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--entry-unit-review', type=Path)
    args = parser.parse_args()
    result = assess(args.inputs, args.protocol, args.entry_unit_review)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items()
                      if k not in {'entry_cases', 'economic_scenarios', 'summaries', 'source_workload'}},
                     ensure_ascii=False, default=str))


if __name__ == '__main__':
    main()
