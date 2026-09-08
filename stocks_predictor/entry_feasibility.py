"""Independent empty-book entry simulation shared by registered diagnostics."""
from decimal import Decimal
import hashlib

from stocks_predictor.continuous_research import read

from stocks_predictor.retail_cash import RetailBook, integer_targets, iso


def entry_case(capital, cost, plan, quotes, settlement, action_requirements, unit_reviews=()):
    """Independent empty book, not a rebalance of previously simulated wealth."""
    result = {'capital_brl': capital, 'one_way_cost_rate': cost, 'signal_date': plan['asof'],
              'entry_date': plan['entry'], 'settlement_date': settlement,
              'target_names': len(plan['members']), 'status': 'BLOCKED',
              'actual_continuous_turnover': None, 'profit': None}
    identities = {m['ticker']: m for m in plan['members']}
    names = set(identities)
    reviewed = {r['event_id']: r for r in unit_reviews}
    boundary = []
    applied = []
    for r in action_requirements:
        if r['ticker'] not in names or not plan['asof'] < r['ex_date'] <= plan['entry']:
            continue
        review = reviewed.get(r['event_id'], {})
        if (review.get('kind') == 'BONUS_IN_DIFFERENT_CLASS' and review.get('removes_original') is False
                and review.get('original_share_units_unchanged') is True
                and review.get('ticker') == r['ticker']
                and review.get('isin') == identities[r['ticker']]['isin']
                and (not r.get('isin') or review['isin'] == r['isin'])
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

