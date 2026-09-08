"""Continuous integer-share replay on an explicitly reviewed event tape.

This module does not certify source completeness. The caller must pass the
coverage gate before publishing results. All prices, settlements, corporate
deliveries and tax dates are supplied; missing inputs stop the replay.
"""

from collections import defaultdict
from copy import deepcopy
from dataclasses import asdict
from datetime import date, timedelta
from decimal import Decimal, ROUND_DOWN, ROUND_FLOOR
import hashlib
import json

from stocks_predictor.retail_cash import Holding, RetailBook, integer_targets, iso, number, ordinary_month_tax


def cents(value):
    return number(value).quantize(Decimal('.01'), rounding=ROUND_DOWN)


class OrdinaryTaxLedger:
    """One resident individual, one broker, ordinary trades; reviewed calendar.

    Keep dated IRRF separate from trading expenses and carry losses by month.
    Recompute a provisional DARF after sales so buys reserve its cash. IRRF
    thresholds use cumulative monthly gross sales, including BDRs. A year-end
    unused credit is recorded for the personal return, never invented as cash.
    """

    def __init__(self, calendar):
        self.calendar = calendar
        self.month = None
        self.loss = Decimal(0)
        self.credit = Decimal(0)
        self.small_darf = Decimal(0)
        self.assessments = []
        self.external_credits = []
        self.withheld = defaultdict(Decimal)
        self.withheld_disposals = set()
        self.last = None

    def enter(self, book, month):
        if month == self.month:
            return
        if self.month:
            if self.last is None:
                raise ValueError('previous tax month was not assessed')
            self.assessments.append(self.last)
            self.loss = self.last['loss_carry']
            self.credit = self.last['credit_carry']
            self.small_darf = self.last['darf_carry']
            if month[:4] != self.month[:4]:
                self.external_credits.append({'year': self.month[:4], 'credit': self.credit})
                self.credit = Decimal(0)
        self.month = month
        self.refresh(book)

    def refresh(self, book):
        if self.month is None:
            raise ValueError('enter a tax month before assessment')
        spec = self.calendar[self.month]
        if spec.get('source_review') is not True or not spec.get('sources'):
            raise ValueError('unreviewed monthly tax calendar')
        due = iso(spec['due_date'])
        if due[:7] <= self.month:
            raise ValueError('tax payment must follow assessment month')
        rows = [r for r in book.trades if r['date'][:7] == self.month and r['date'] <= book.day]
        disposals = [r for r in book.corporate_disposals
                     if r['date'][:7] == self.month and r['date'] <= book.day]
        calc = ordinary_month_tax(rows, self.loss, corporate_disposals=disposals)
        sales = [r for r in rows if r['quantity'] < 0]
        raw_irrf = sum((r['gross'] for r in sales), Decimal(0)) * number(spec['irrf_rate'])
        irrf = cents(raw_irrf) if raw_irrf > number(spec['irrf_waiver']) else Decimal(0)
        increment = irrf - self.withheld[self.month]
        if increment < 0:
            raise ValueError('cumulative sale withholding cannot decrease')
        if increment:
            # Charge each newly crossed cumulative amount against the sale
            # settlement that made it due; do not debit it again next month.
            when = max(r['settlement_date'] for r in sales)
            book.pending.append({'date': when, 'amount': -increment, 'kind': 'IRRF'})
            self.withheld[self.month] = irrf
        # Auction intermediaries may differ from the trading broker. Use only
        # their explicitly reviewed withholding, not the broker's threshold.
        auction_irrf = sum((r['irrf'] for r in disposals), Decimal(0))
        for row in disposals:
            if row['event_id'] not in self.withheld_disposals:
                if row['irrf']:
                    book.pending.append({'date': row['settlement_date'], 'amount': -row['irrf'],
                                         'kind': 'CORPORATE_IRRF', 'event_id': row['event_id']})
                self.withheld_disposals.add(row['event_id'])
        usable = self.credit + irrf + auction_irrf
        gross_tax = cents(calc['tax'])
        net_tax = max(Decimal(0), gross_tax - usable)
        credit_carry = max(Decimal(0), usable - gross_tax)
        total = self.small_darf + net_tax
        payable = total if total >= number(spec['minimum_darf']) else Decimal(0)
        tag = 'DARF:' + self.month
        book.pending[:] = [r for r in book.pending if r.get('tag') != tag]
        if payable:
            book.pending.append({'date': due, 'amount': -payable, 'tag': tag, 'kind': 'DARF'})
        self.last = {'month': self.month, **calc, 'tax': gross_tax, 'irrf': irrf,
                     'darf': payable, 'darf_due': due, 'credit_carry': credit_carry,
                     'darf_carry': total - payable}
        if disposals:
            self.last.update(corporate_irrf=auction_irrf,
                             corporate_disposal_ids=[r['event_id'] for r in disposals])
        book.cash_buffer = self.last['darf_carry']

    @property
    def unscheduled_liability(self):
        return self.last['darf_carry'] if self.last else Decimal(0)


def mark(book, day, quotes, tax):
    """Mark close using the matching identity; an absent price is not zero."""
    securities = Decimal(0)
    for ticker, holding in book.positions.items():
        q = quotes[(day, ticker)]
        if q['isin'] != holding.isin or q['date'] != day:
            raise ValueError('mark identity or date mismatch')
        price = number(q['close'])
        if price <= 0:
            raise ValueError('nonpositive mark')
        securities += holding.quantity * price
    obligations = sum((r['amount'] for r in book.pending), Decimal(0))
    known_rights = [r for r in book.rights.values() if r.get('known_on', day) <= day]
    receivables = sum((r['net'] for r in known_rights), Decimal(0))
    unknown_claims = len(book.rights) - len(known_rights)
    liquid_equity = book.cash + obligations + securities - tax.unscheduled_liability
    return {'date': day, 'settled_cash': book.cash, 'trade_and_tax_pending': obligations,
            'securities': securities, 'unpaid_receivables': receivables,
            'unscheduled_tax_liability': tax.unscheduled_liability,
            'unvalued_claims': unknown_claims,
            'liquid_equity': liquid_equity,
            'equity_including_receivables': None if unknown_claims else liquid_equity + receivables}


def apply_action(book, action):
    """Apply explicitly reviewed integer deliveries and cash terms atomically.

    Supports carry-basis conversions/splits, bonuses with issuer-declared basis,
    and explicitly classified auction gains with position-dependent basis.
    Other compulsory dispositions require an externally reviewed tax flow bound
    to the entire portfolio state; this is not a general reorganization tax solver.
    """
    staged = deepcopy(book)
    if action['ex_date'] != book.day or action.get('source_review') is not True:
        raise ValueError('unreviewed or mistimed action')
    if not action.get('sources') or not action.get('tax_source'):
        raise ValueError('corporate source and fiscal treatment required')
    if iso(action.get('terms_known_on')) > book.day:
        raise ValueError('future corporate quantity terms require a dated revision event')
    original = staged.positions.get(action['ticker'])
    if not original:
        return []
    if original.isin != action['isin']:
        raise ValueError('corporate identity mismatch')
    if action['basis_mode'] not in {'carry', 'bonus', 'explicit_disposal'}:
        raise ValueError('unsupported corporate basis mode')
    quantity = original.quantity
    original_basis = original.basis
    legs = action['stocks']
    if action['basis_mode'] == 'carry':
        if (not action['removes_original'] or sum(number(s['basis_fraction']) for s in legs) != 1
                or any(number(s['basis_fraction']) < 0 for s in legs)):
            raise ValueError('carry conversion requires full basis allocation')
    elif action['basis_mode'] == 'bonus' and action['removes_original']:
        raise ValueError('bonus must retain the original holding')
    elif action['basis_mode'] == 'explicit_disposal':
        if 'disposal_tax' not in action or not action['removes_original']:
            raise ValueError('explicit disposal tax schedule required')
    if action['removes_original']:
        del staged.positions[action['ticker']]
    log = []
    for n, leg in enumerate(legs):
        ratio = number(leg['ratio'])
        if ratio <= 0:
            raise ValueError('positive delivery ratio required')
        exact = quantity * ratio
        # A reverse split followed by a split can round positions to lots
        # even when its net price factor is one (e.g. 100:1 followed by 1:100).
        rounding_lot = leg.get('rounding_lot', 1)
        if type(rounding_lot) is not int or rounding_lot <= 0:
            raise ValueError('positive integer corporate rounding lot required')
        whole = int((exact / rounding_lot).to_integral_value(rounding=ROUND_FLOOR)) * rounding_lot
        fraction = exact - whole
        credit = iso(leg['credit_date'])
        tradable = iso(leg['tradable_on']) if leg.get('tradable_on') else None
        if tradable and not book.day <= tradable <= credit:
            raise ValueError('invalid documented pre-credit trading date')
        if credit < book.day or leg['tax_class'] not in {'equity', 'bdr'}:
            raise ValueError('invalid corporate credit date or tax class')
        if action['basis_mode'] == 'carry':
            full_basis = original_basis * number(leg['basis_fraction'])
        else:
            full_basis = exact * number(leg['basis_per_share'])
        if full_basis < 0:
            raise ValueError('negative fiscal basis')
        whole_basis = full_basis * whole / exact
        if fraction:
            terms = leg['fraction_settlement']
            if terms.get('source_review') is not True or not terms.get('sources'):
                raise ValueError('fraction settlement not reviewed')
            event_id = f"{action['event_id']}:fraction:{n}"
            removed_basis = full_basis - whole_basis
            if terms.get('tax_treatment') == 'ordinary_exchange':
                disposal = _auction_disposal(book, action, leg, terms, event_id, fraction, removed_basis)
                staged.corporate_disposals.append(disposal)
                amount = disposal['gross'] - disposal['costs']
                _corporate_cash(staged, event_id, amount, terms)
                log.append({'fraction': fraction, 'removed_basis': removed_basis,
                            'cash_before_personal_tax': amount, 'disposal_date': disposal['date'],
                            'known_on': terms['known_on']})
            elif terms.get('tax_treatment') == 'reviewed_portfolio_net':
                _require_portfolio_context(book, terms)
                amount = fraction * number(terms['net_cash_per_fraction'])
                _corporate_cash(staged, event_id, amount, terms)
                log.append({'fraction': fraction, 'removed_basis': removed_basis, 'net_cash': amount})
            else:
                raise ValueError('explicit fraction tax treatment required; fee-net is not personal-tax-net')
        if whole:
            existing = staged.positions.get(leg['ticker'])
            if existing:
                if existing.isin != leg['isin'] or existing.tax_class != leg['tax_class']:
                    raise ValueError('merged delivery identity mismatch')
                existing.normalize_deliveries(book.day)
                if credit > book.day:
                    existing.locked_deliveries.append({'quantity': whole, 'credit_date': credit,
                                                       'tradable_on': tradable})
                existing.quantity += whole
                existing.basis += whole_basis
            else:
                staged.positions[leg['ticker']] = Holding(leg['isin'], whole, whole_basis,
                                                          leg['tax_class'], credit, tradable_on=tradable)
    for n, cash in enumerate(action.get('cash', [])):
        _corporate_cash(staged, f"{action['event_id']}:cash:{n}", quantity*number(cash['net_per_original']), cash)
    for tax in action.get('disposal_tax', []):
        if tax.get('source_review') is not True or not tax.get('sources'):
            raise ValueError('disposal tax not reviewed')
        _require_portfolio_context(book, tax)
        if iso(tax.get('known_on')) > book.day:
            raise ValueError('future disposal tax amount requires a dated recognition event')
        amount = quantity * number(tax['tax_per_original'])
        if amount < 0 or iso(tax['payment_date']) <= book.day:
            raise ValueError('invalid disposal tax flow')
        staged.pending.append({'date': tax['payment_date'], 'amount': -amount, 'kind': 'CORPORATE_TAX'})
    book.__dict__.update(staged.__dict__)
    return log


def portfolio_fingerprint(book):
    """Bind externally computed net tax to this book, including its trade history.

    A matching fingerprint is an applicability check, not source approval. It
    includes previous disposals/loss-producing trades; quantity/basis alone would
    let two different monthly tax situations share an inappropriate net constant.
    """
    state = {**book.__dict__, 'positions': {k: asdict(v) for k, v in book.positions.items()},
             'seen_right_ids': sorted(book.seen_right_ids)}
    return hashlib.sha256(json.dumps(state, sort_keys=True, default=str).encode('utf-8')).hexdigest()


def _require_portfolio_context(book, terms):
    if terms.get('portfolio_state_sha256') != portfolio_fingerprint(book):
        raise ValueError('reviewed net corporate tax must match the portfolio state')


def _auction_disposal(book, action, leg, terms, event_id, quantity, basis):
    """Reviewed ordinary-exchange auction; never infer its legal tax category.

    Gross proceeds, expenses and actual withholding are separate inputs. A
    result announced only net of fees cannot establish monthly gross sales or
    personal income tax. Missing gross/withholding therefore remains an error.
    """
    if not terms.get('tax_source'):
        raise ValueError('auction tax classification source required')
    when, known = iso(terms['disposal_date']), iso(terms['known_on'])
    available = iso(terms['available_on'])
    if not book.day <= when <= iso(terms['payment_date']) < available or known > when:
        raise ValueError('auction needs causal disposal, knowledge and cash dates')
    gross = quantity * number(terms['gross_cash_per_fraction'])
    costs = quantity * number(terms['fees_per_fraction'])
    irrf = quantity * number(terms['irrf_per_fraction'])
    if gross <= 0 or costs < 0 or irrf < 0 or costs + irrf > gross:
        raise ValueError('invalid auction gross, expenses or withholding')
    if any(r['event_id'] == event_id for r in book.corporate_disposals):
        raise ValueError('duplicate corporate disposal')
    return {'event_id': event_id, 'ticker': leg['ticker'], 'isin': leg['isin'],
            'date': when, 'settlement_date': available, 'quantity': quantity,
            'gross': gross, 'costs': costs, 'basis': basis, 'gain': gross-costs-basis,
            'irrf': irrf, 'tax_class': leg['tax_class'], 'source_review': True,
            'sources': terms['sources'], 'tax_source': terms['tax_source'],
            'originating_action': action['event_id']}


def _corporate_cash(book, event_id, amount, terms):
    if amount < 0 or not book.day <= iso(terms['payment_date']) < iso(terms['available_on']):
        raise ValueError('invalid corporate cash chronology')
    if event_id in book.seen_right_ids:
        raise ValueError('duplicate corporate cash')
    book.seen_right_ids.add(event_id)
    known_on = iso(terms['known_on'])
    if known_on > terms['payment_date']:
        raise ValueError('cash amount cannot become known after payment')
    if amount:
        book.rights[event_id] = {'net': amount, 'payment_date': terms['payment_date'],
                                 'available_on': terms['available_on'], 'ticker': 'corporate',
                                 'known_on': known_on}


def run_continuous(capital, cost_rate, plans, quotes, sessions, settlements,
                   cash_events, actions, tax_calendar, coverage_ready, coverage_issues=(), *,
                   selection_policy=None):
    """Execute every supplied plan on one persistent book through final exit.

    The last plan is the explicit liquidation plan (empty members). Signal-day
    sizing excludes unpaid receivables. Returns are emitted only after the full
    tape succeeds; a missing mid-path quote does not produce a partial profit.
    """
    if coverage_ready is not True or coverage_issues:
        raise ValueError('complete reviewed strategy AND comparison evidence required')
    if number(capital) <= 0 or not 0 <= number(cost_rate) < 1:
        raise ValueError('positive capital and valid cost required')
    if len(plans) < 2 or plans[-1]['members'] or any(not p['members'] for p in plans[:-1]):
        raise ValueError('nonempty rebalance plans and an explicit final liquidation required')
    if [p['entry'] for p in plans] != sorted({p['entry'] for p in plans}):
        raise ValueError('unique chronological plans required')
    session_set = set(sessions)
    if sessions != sorted(session_set) or any(iso(d) != d for d in sessions):
        raise ValueError('unique chronological sessions required')
    for p in plans:
        if iso(p['asof']) >= iso(p['entry']) or p['entry'] not in session_set or p['asof'] not in session_set:
            raise ValueError('plan must use an earlier session signal')
        if len({m['ticker'] for m in p['members']}) != len(p['members']):
            raise ValueError('duplicate plan member')
        if sessions.index(p['entry']) != sessions.index(p['asof']) + 1:
            raise ValueError('execution must follow the signal in the next session')
        settlement = iso(settlements[p['entry']])
        if settlement not in session_set or settlement <= p['entry']:
            raise ValueError('settlement must be a later exchange session')
    by_day = {p['entry']: p for p in plans}
    by_signal = {p['asof']: p for p in plans}
    if len(by_signal) != len(plans):
        raise ValueError('unique signal dates required')
    cash_by_day = defaultdict(list)
    action_by_day = defaultdict(list)
    ids = set()
    for event, dest in [(e, cash_by_day) for e in cash_events] + [(e, action_by_day) for e in actions]:
        if not event.get('event_id') or event['event_id'] in ids or event.get('source_review') is not True:
            raise ValueError('unique reviewed events required')
        if not event.get('sources') or not event.get('tax_source'):
            raise ValueError('event source and fiscal treatment required')
        ids.add(event['event_id'])
        dest[iso(event['ex_date'])].append(event)
    book = RetailBook(capital, plans[0]['asof'])
    tax = OrdinaryTaxLedger(tax_calendar)
    tax.enter(book, book.day[:7])
    targets = {}
    selected_plans = {}
    signal_decisions = []
    snapshots = []
    action_log = []
    seen_actions = set()
    end = plans[-1]['entry']
    today = date.fromisoformat(book.day)
    while today.isoformat() <= end:
        day = today.isoformat()
        book.advance(day)
        tax.enter(book, day[:7])
        for event in cash_by_day[day]:
            known_on = iso(event['known_on'])
            if known_on > event['payment_date']:
                raise ValueError('cash amount cannot become known after payment')
            book.entitlement(event['event_id'], event['ticker'], event['isin'], day,
                             event['payment_date'], event['available_on'], event['net_per_share'])
            if event['event_id'] in book.rights:
                book.rights[event['event_id']]['known_on'] = known_on
        for event in action_by_day[day]:
            if event['event_id'] in seen_actions:
                raise ValueError('duplicate action')
            seen_actions.add(event['event_id'])
            action_log.append({'event': event['event_id'], 'date': day, 'details': apply_action(book, event)})
        # Recognize an auction gain on its reviewed disposal date, even when no
        # strategy trade occurs. Its later payment never becomes early buying power.
        if any(r['date'] == day for r in book.corporate_disposals):
            tax.refresh(book)
        if day in by_day:
            plan = by_day[day]
            if selection_policy is not None:
                plan = selected_plans[plan['asof']]
            target = targets[plan['asof']]
            # A split/conversion between signal and entry changes order units;
            # require an explicit transformed plan instead of silent wrong units.
            # A bonus in a DIFFERENT class leaves original order units intact.
            # Only previous holders get that entitlement; planned new buys do
            # not receive free bonus shares. Its sale is an ordinary reduction.
            if any(plan['asof'] < e['ex_date'] <= day and e['ticker'] in target
                   and (e['removes_original'] or any(s['ticker'] == e['ticker'] for s in e['stocks']))
                   for e in actions):
                raise ValueError('corporate action between signal and execution requires reviewed order transformation')
            identities = {m['ticker']: m for m in plan['members']}
            if any(t in identities and (identities[t]['isin'] != h.isin
                   or identities[t]['tax_class'] != h.tax_class) for t, h in book.positions.items()):
                raise ValueError('target and retained holding identity mismatch')
            identities.update({t: {'isin': h.isin, 'tax_class': h.tax_class,
                                  'lot': quotes[(day, t)]['lot']} for t, h in book.positions.items()})
            deltas = {t: target.get(t, 0) - (book.positions[t].quantity if t in book.positions else 0)
                      for t in set(target) | set(book.positions)}
            for buying in (False, True):
                for ticker in sorted(deltas):
                    delta = deltas[ticker]
                    if not delta or (delta > 0) != buying:
                        continue
                    identity = identities[ticker]
                    q = quotes[(day, ticker)]
                    while delta:
                        r = book.order(ticker, identity['isin'], delta, q, plan['asof'], settlements[day],
                                       cost_rate, identity['lot'], identity['tax_class'])
                        if r:
                            break
                        delta -= 1
                    if not buying:
                        tax.refresh(book)
                if not buying:
                    tax.refresh(book)
        if day in session_set:
            valuation = mark(book, day, quotes, tax)
            snapshots.append(valuation)
            if day in by_signal:
                plan = by_signal[day]
                if selection_policy is not None:
                    available = {m['ticker']: m for m in plan['members']}
                    symbols = set(available) | set(book.positions)
                    signal_quotes = {t: deepcopy(quotes[(day, t)]) for t in symbols}
                    decision = selection_policy(deepcopy(plan), deepcopy(book),
                        max(0, valuation['liquid_equity']), signal_quotes, settlements[plan['entry']])
                    members, quantities = decision['members'], decision['targets']
                    if (len({m['ticker'] for m in members}) != len(members)
                            or set(quantities) != {m['ticker'] for m in members}
                            or any(type(q) is not int or q < 0 for q in quantities.values())
                            or any(m != available.get(m['ticker']) for m in members)
                            or (plan['members'] and not members)
                            or (not plan['members'] and quantities)):
                        raise ValueError('signal policy changed the allowed identities or order contract')
                    selected_plans[day] = {**plan, 'members': deepcopy(members)}
                    targets[day] = dict(quantities)
                    signal_decisions.append({'asof': day, 'entry': plan['entry'], **deepcopy(decision)})
                    today += timedelta(days=1)
                    continue
                prices = {}
                for m in plan['members']:
                    q = quotes[(day, m['ticker'])]
                    if q['date'] != day or q['isin'] != m['isin']:
                        raise ValueError('signal quote identity mismatch')
                    prices[m['ticker']] = q['close']
                targets[day] = integer_targets(max(0, valuation['liquid_equity']), prices) if prices else {}
        today += timedelta(days=1)
    if book.positions:
        raise ValueError('final liquidation left positions')
    if any(r['date'] > end for r in book.corporate_disposals):
        raise ValueError('post-end corporate auction requires an extended reviewed tax horizon')
    tax.refresh(book)
    # Receivables after the endpoint remain claims, never reported as bank cash.
    terminal = mark(book, end, quotes, tax)
    # Prove that dated sale settlements and tax debits can actually clear.
    # This copy does not move post-end dividends into endpoint profit.
    clearing = deepcopy(book)
    clearing_day = max([end, *(r['date'] for r in clearing.pending)])
    clearing.advance(clearing_day)
    result = {'full_history_executed': True, 'capital': number(capital), 'cost_rate': number(cost_rate),
            'first_entry': plans[0]['entry'], 'final_exit': end, 'snapshots': snapshots,
            'trades': book.trades, 'corporate_disposals': book.corporate_disposals,
            'tax_assessments': [*tax.assessments, tax.last],
            'unused_irrf_for_personal_return': tax.external_credits,
            'corporate_log': action_log, 'remaining_cash_flows': book.pending,
            'last_obligation_date': clearing_day, 'cleared_cash_on_last_obligation_date': clearing.cash,
            'unpaid_receivables': book.rights, 'terminal': terminal,
            'profit_excluding_unpaid_receivables': terminal['liquid_equity']-number(capital),
            'profit_including_unpaid_receivables_at_face': (None if terminal['unvalued_claims']
                else terminal['equity_including_receivables']-number(capital))}
    if selection_policy is not None:
        result.update(signal_decisions=signal_decisions,
            traded_notional_brl=sum((r['gross'] for r in book.trades), Decimal(0)),
            modeled_trading_cost_brl=sum((r['costs'] for r in book.trades), Decimal(0)))
    return result
