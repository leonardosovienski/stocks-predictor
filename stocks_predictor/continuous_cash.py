"""Continuous integer-share replay on an explicitly reviewed event tape.

This module does not certify source completeness. The caller must pass the
coverage gate before publishing results. All prices, settlements, corporate
deliveries and tax dates are supplied; missing inputs stop the replay.
"""

from collections import defaultdict
from copy import deepcopy
from datetime import date, timedelta
from decimal import Decimal, ROUND_DOWN, ROUND_FLOOR

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
        self.last = None

    def enter(self, book, month):
        if month == self.month:
            return
        if self.month:
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
        spec = self.calendar[self.month]
        if spec.get('source_review') is not True or not spec.get('sources'):
            raise ValueError('unreviewed monthly tax calendar')
        due = iso(spec['due_date'])
        if due[:7] <= self.month:
            raise ValueError('tax payment must follow assessment month')
        rows = [r for r in book.trades if r['date'][:7] == self.month]
        calc = ordinary_month_tax(rows, self.loss)
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
        usable = self.credit + irrf
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
    and cash legs with already reviewed net withholding. A taxable compulsory
    disposition must supply its dated tax cash flow separately; it cannot be
    silently classified as an exempt exchange trade.
    """
    staged = deepcopy(book)
    if action['ex_date'] != book.day or action.get('source_review') is not True:
        raise ValueError('unreviewed or mistimed action')
    if not action.get('sources') or not action.get('tax_source'):
        raise ValueError('corporate source and fiscal treatment required')
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
            # Cash is supplied as a NET amount after the explicitly reviewed
            # disposal tax and auction charges; never use a market-price guess.
            amount = fraction * number(terms['net_cash_per_fraction'])
            _corporate_cash(staged, f"{action['event_id']}:fraction:{n}", amount, terms)
            log.append({'fraction': fraction, 'removed_basis': full_basis-whole_basis, 'net_cash': amount})
        if whole:
            existing = staged.positions.get(leg['ticker'])
            if existing:
                if existing.isin != leg['isin'] or existing.tax_class != leg['tax_class']:
                    raise ValueError('merged delivery identity mismatch')
                if existing.available_on > book.day:
                    existing.locked_deliveries.append({'quantity': existing.quantity,
                                                      'credit_date': existing.available_on,
                                                      'tradable_on': existing.tradable_on})
                    existing.available_on = book.day
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
        amount = quantity * number(tax['tax_per_original'])
        if amount < 0 or iso(tax['payment_date']) <= book.day:
            raise ValueError('invalid disposal tax flow')
        staged.pending.append({'date': tax['payment_date'], 'amount': -amount, 'kind': 'CORPORATE_TAX'})
    book.__dict__.update(staged.__dict__)
    return log


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
                   cash_events, actions, tax_calendar, coverage_ready, coverage_issues=()):
    """Execute every supplied plan on one persistent book through final exit.

    The last plan is the explicit liquidation plan (empty members). Signal-day
    sizing excludes unpaid receivables. Returns are emitted only after the full
    tape succeeds; a missing mid-path quote does not produce a partial profit.
    """
    if coverage_ready is not True or coverage_issues:
        raise ValueError('complete reviewed strategy AND comparison evidence required')
    if len(plans) < 2 or plans[-1]['members'] or any(not p['members'] for p in plans[:-1]):
        raise ValueError('nonempty rebalance plans and an explicit final liquidation required')
    if [p['entry'] for p in plans] != sorted({p['entry'] for p in plans}):
        raise ValueError('unique chronological plans required')
    session_set = set(sessions)
    for p in plans:
        if iso(p['asof']) >= iso(p['entry']) or p['entry'] not in session_set or p['asof'] not in session_set:
            raise ValueError('plan must use an earlier session signal')
        if len({m['ticker'] for m in p['members']}) != len(p['members']):
            raise ValueError('duplicate plan member')
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
        if day in by_day:
            plan = by_day[day]
            target = targets[plan['asof']]
            # A split/conversion between signal and entry changes order units;
            # require an explicit transformed plan instead of silent wrong units.
            if any(plan['asof'] < e['ex_date'] <= day and e['ticker'] in target for e in actions):
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
    tax.refresh(book)
    # Receivables after the endpoint remain claims, never reported as bank cash.
    terminal = mark(book, end, quotes, tax)
    # Prove that dated sale settlements and tax debits can actually clear.
    # This copy does not move post-end dividends into endpoint profit.
    clearing = deepcopy(book)
    clearing_day = max([end, *(r['date'] for r in clearing.pending)])
    clearing.advance(clearing_day)
    return {'full_history_executed': True, 'capital': number(capital), 'cost_rate': number(cost_rate),
            'first_entry': plans[0]['entry'], 'final_exit': end, 'snapshots': snapshots,
            'trades': book.trades, 'tax_assessments': [*tax.assessments, tax.last],
            'unused_irrf_for_personal_return': tax.external_credits,
            'corporate_log': action_log, 'remaining_cash_flows': book.pending,
            'last_obligation_date': clearing_day, 'cleared_cash_on_last_obligation_date': clearing.cash,
            'unpaid_receivables': book.rights, 'terminal': terminal,
            'profit_excluding_unpaid_receivables': terminal['liquid_equity']-number(capital),
            'profit_including_unpaid_receivables_at_face': (None if terminal['unvalued_claims']
                else terminal['equity_including_receivables']-number(capital))}
