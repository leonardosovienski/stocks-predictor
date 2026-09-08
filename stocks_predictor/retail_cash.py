"""Integer-share, dated-cash research ledger. Missing evidence is an error.

This module is accounting machinery, not a calibrated strategy or tax advisor.
Cash entitlements require an explicit net amount and a verified availability date.
Corporate deliveries and cost bases must be supplied by their reviewed terms.
"""

from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass, field as dataclass_field
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_FLOOR


def number(value):
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("invalid money or quantity") from exc
    if not result.is_finite():
        raise ValueError("nonfinite money or quantity")
    return result


def iso(value):
    if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
        raise ValueError("invalid ISO date")
    return value


@dataclass
class Holding:
    isin: str
    quantity: int
    basis: Decimal
    tax_class: str = "equity"
    available_on: str = "0001-01-01"
    locked_deliveries: list = dataclass_field(default_factory=list)
    tradable_on: str | None = None

    def normalize_deliveries(self, day):
        """Represent undelivered shares individually before a quantity mutation."""
        locked = sum(r['quantity'] for r in self.locked_deliveries)
        if locked < 0 or locked > self.quantity:
            raise ValueError('invalid undelivered quantity')
        if self.available_on > day:
            base = self.quantity - locked
            if base:
                self.locked_deliveries.append({'quantity': base, 'credit_date': self.available_on,
                                              'tradable_on': self.tradable_on})
            self.available_on = day
            self.tradable_on = None
        self.locked_deliveries[:] = [r for r in self.locked_deliveries if r['credit_date'] > day]

    def consume_delivery(self, quantity, day, settlement_date):
        """Consume delivered shares first, then legally tradable pending lots.

        A partial pre-credit sale must reduce its delivery lot as well as the
        total position, or later sales can lock shares which no longer exist.
        """
        self.normalize_deliveries(day)
        remaining = max(0, quantity - (self.quantity - sum(r['quantity'] for r in self.locked_deliveries)))
        for row in sorted(self.locked_deliveries, key=lambda r: r['credit_date']):
            if row.get('tradable_on') is not None and row['tradable_on'] <= day and row['credit_date'] <= settlement_date:
                take = min(remaining, row['quantity'])
                row['quantity'] -= take
                remaining -= take
        if remaining:
            raise ValueError('sale exceeds delivered position')
        self.locked_deliveries[:] = [r for r in self.locked_deliveries if r['quantity']]

    def available_quantity(self, day, settlement_date=None):
        def usable(credit, tradable):
            return credit <= day or (tradable is not None and tradable <= day
                                     and settlement_date is not None and credit <= settlement_date)
        if not usable(self.available_on, self.tradable_on):
            return 0
        locked = sum(r['quantity'] for r in self.locked_deliveries
                     if not usable(r['credit_date'], r.get('tradable_on')))
        if locked < 0 or locked > self.quantity:
            raise ValueError('invalid undelivered quantity')
        return self.quantity - locked


def trade_value(quantity, quote, lot=100):
    """A standard-lot ticket plus its actual fractional-market remainder."""
    if type(quantity) is not int or quantity < 0 or type(lot) is not int or lot <= 0:
        raise ValueError("integer nonnegative shares and positive lot required")
    standard, remainder = divmod(quantity, lot)
    result = Decimal(0)
    if standard:
        price = number(quote["standard"])
        if price <= 0:
            raise ValueError("nonpositive standard price")
        result += standard * lot * price
    if remainder:
        price = number(quote["fractional"])
        if price <= 0:
            raise ValueError("nonpositive fractional price")
        result += remainder * price
    return result


def integer_targets(capital, close_prices):
    """Order sizes use signal-day closes, never an unseen opening price."""
    capital = number(capital)
    if capital < 0 or not close_prices:
        raise ValueError("nonnegative capital and nonempty prices required")
    each = capital / len(close_prices)
    targets = {}
    for ticker, value in close_prices.items():
        price = number(value)
        if price <= 0:
            raise ValueError("nonpositive sizing price")
        targets[ticker] = int((each / price).to_integral_value(rounding=ROUND_FLOOR))
    return targets


def ordinary_month_tax(trades, prior_loss=0, exemption=20000, rate="0.15", corporate_disposals=()):
    """Research PF scenario, no external trades; ordinary equity/BDR sales only.

    Small equity-sale positive gains are exempt; their losses still enter the
    common loss pool. BDR gains do not inherit the equity-sales exemption.
    IRRF credits and payment dates belong in the caller's reviewed tax schedule.
    """
    loss, limit, fraction = map(number, (prior_loss, exemption, rate))
    if loss < 0 or limit < 0 or not 0 <= fraction <= 1:
        raise ValueError("invalid tax inputs")
    trades = list(trades)
    if any(r.get('corporate_disposal') for r in trades):
        raise ValueError('corporate disposals must use the separate reviewed input')
    disposals = list(corporate_disposals)
    ids = set()
    for row in disposals:
        event_id = row.get('event_id')
        if not event_id or event_id in ids:
            raise ValueError('unique corporate disposal required')
        ids.add(event_id)
        if row.get('source_review') is not True or not row.get('sources') or not row.get('tax_source'):
            raise ValueError('reviewed ordinary corporate disposal required')
        quantity, gross, costs, basis = map(number, (row['quantity'], row['gross'], row['costs'], row['basis']))
        if quantity <= 0 or gross <= 0 or not 0 <= costs <= gross or basis < 0:
            raise ValueError('invalid corporate disposal economics')
        if number(row['gain']) != gross - costs - basis:
            raise ValueError('corporate gain must use allocated position basis')
        # Fractions are tax disposals, never fractional exchange orders or
        # additional tradable positions. Keep them out of the integer ledger.
        trades.append({**row, 'quantity': -quantity, 'corporate_disposal': True})
    if len({iso(r["date"])[:7] for r in trades}) > 1:
        raise ValueError("one calendar month required")
    sides = defaultdict(set)
    for row in trades:
        if ((type(row["quantity"]) is not int and not row.get('corporate_disposal'))
                or not row["quantity"] or number(row["gross"]) < 0):
            raise ValueError("invalid trade quantity or gross proceeds")
        if row["tax_class"] not in {"equity", "bdr"}:
            raise ValueError("unreviewed tax treatment")
        sides[(row["isin"], row["date"])].add(row["quantity"] > 0)
    if any(len(v) > 1 for v in sides.values()):
        raise ValueError("day trade requires a separate tax calculation")
    sales_rows = [r for r in trades if r["quantity"] < 0]
    sales = sum((number(r["gross"]) for r in sales_rows if r["tax_class"] == "equity"), Decimal(0))
    gains = defaultdict(Decimal)
    for row in sales_rows:
        gains[row["tax_class"]] += number(row["gain"])
    exempt_gain = max(gains["equity"], Decimal(0)) if sales <= limit else Decimal(0)
    taxable_before_loss = gains["equity"] - exempt_gain + gains["bdr"]
    taxable = max(Decimal(0), taxable_before_loss - loss)
    remaining_loss = max(Decimal(0), loss - taxable_before_loss)
    return {"equity_sales": sales, "exempt_equity_gain": exempt_gain,
            "taxable_gain": taxable, "tax": taxable * fraction, "loss_carry": remaining_loss}


class RetailBook:
    """Track trading obligations and separately dated distributable cash."""

    def __init__(self, capital, start_date):
        self.cash = number(capital)
        if self.cash < 0:
            raise ValueError("negative starting capital")
        self.day = iso(start_date)
        self.positions = {}
        self.pending = []
        self.rights = {}
        self.seen_right_ids = set()
        self.trades = []
        self.corporate_disposals = []
        self.cash_buffer = Decimal(0)

    def advance(self, day):
        day = iso(day)
        if day < self.day:
            raise ValueError("ledger cannot move backward")
        paid = {k: r for k, r in self.rights.items() if r["available_on"] <= day}
        due = [f for f in self.pending if f["date"] <= day]
        due += [{"date": r["available_on"], "amount": r["net"]} for r in paid.values()]
        remaining = [f for f in self.pending if f["date"] > day]
        # Net all flows settling on a given day. Later credits cannot cure a
        # deficit on an earlier settlement date.
        cash = self.cash
        for when in sorted({f["date"] for f in due}):
            cash += sum((f["amount"] for f in due if f["date"] == when), Decimal(0))
            if cash < 0:
                raise ValueError("settlement deficit")
        self.cash, self.pending, self.day = cash, remaining, day
        for key in paid:
            del self.rights[key]

    def fundable(self, amount, settlement_date):
        """Only trade obligations offset; unpaid dividends are never buying power."""
        amount = number(amount)
        if amount < 0 or iso(settlement_date) <= self.day:
            raise ValueError("nonnegative funding after the current date required")
        flows = [*self.pending, {"date": settlement_date, "amount": -amount}]
        cash = self.cash - self.cash_buffer
        for day in sorted({f["date"] for f in flows}):
            cash += sum((f["amount"] for f in flows if f["date"] == day), Decimal(0))
            if cash < 0:
                return False
        return True

    def entitlement(self, event_id, ticker, isin, ex_date, payment_date, available_on, net_per_share):
        """Call before ex-day trades. A later sale cannot erase the receivable."""
        if event_id in self.seen_right_ids:
            raise ValueError("duplicate entitlement or installment identifier")
        if not event_id or any(r["date"] == self.day for r in self.trades):
            raise ValueError("identify entitlements before ex-day trades")
        if iso(ex_date) != self.day or not iso(ex_date) <= iso(payment_date) < iso(available_on):
            raise ValueError("invalid entitlement/payment availability chronology")
        amount = number(net_per_share)
        if amount < 0:
            raise ValueError("negative net entitlement")
        holding = self.positions.get(ticker)
        if holding and holding.isin != isin:
            raise ValueError("entitlement security identity mismatch")
        net = amount * (holding.quantity if holding else 0)
        self.seen_right_ids.add(event_id)
        if net:
            self.rights[event_id] = {"net": net, "payment_date": payment_date,
                                     "available_on": available_on, "ticker": ticker}
        return net

    def order(self, ticker, isin, delta, quote, signal_date, settlement_date,
              cost_rate="0.0018", lot=100, tax_class="equity"):
        if type(delta) is not int or iso(signal_date) >= self.day:
            raise ValueError("integer order after its signal required")
        if quote.get("date") != self.day or quote.get("isin") != isin:
            raise ValueError("execution quote date or identity mismatch")
        if iso(settlement_date) <= self.day or tax_class not in {"equity", "bdr"}:
            raise ValueError("invalid settlement or unreviewed tax class")
        fee = number(cost_rate)
        if not 0 <= fee < 1:
            raise ValueError("invalid cost rate")
        existing = self.positions.get(ticker)
        if existing and (existing.isin != isin or existing.tax_class != tax_class):
            raise ValueError("holding identity mismatch")
        if not delta:
            return None
        if any(r["date"] == self.day and r["isin"] == isin and (r["quantity"] > 0) != (delta > 0)
               for r in self.trades):
            raise ValueError("intraday reversal requires a separate day-trade ledger")
        quantity = abs(delta)
        if delta < 0:
            if not existing or quantity > existing.available_quantity(self.day, settlement_date):
                raise ValueError("sale exceeds delivered position")
        gross = trade_value(quantity, quote, lot)
        costs = gross * fee
        if delta > 0 and not self.fundable(gross + costs, settlement_date):
            return None  # Unfilled, never a loan or negative cash.
        if delta > 0:
            gain = Decimal(0)
            if existing:
                existing.normalize_deliveries(self.day)
                existing.quantity += quantity
                existing.basis += gross + costs
            else:
                self.positions[ticker] = Holding(isin, quantity, gross + costs, tax_class)
            cash_flow = -gross - costs
        else:
            assert existing is not None  # Sale validation above establishes this invariant.
            removed_basis = existing.basis * quantity / existing.quantity
            gain = gross - costs - removed_basis
            existing.consume_delivery(quantity, self.day, settlement_date)
            existing.quantity -= quantity
            existing.basis -= removed_basis
            if not existing.quantity:
                del self.positions[ticker]
            cash_flow = gross - costs
        self.pending.append({"date": settlement_date, "amount": cash_flow})
        row = {"ticker": ticker, "isin": isin, "date": self.day, "signal_date": signal_date,
               "settlement_date": settlement_date, "quantity": delta, "gross": gross,
               "costs": costs, "gain": gain, "tax_class": tax_class}
        self.trades.append(row)
        return row

    def rebalance(self, targets, quotes, identities, signal_date, settlement_date, cost_rate="0.0018"):
        """Sell reductions, then deterministic buys; retained shares cost nothing."""
        # Validate and execute on a copy, so one missing quote cannot leave a
        # partially mutated portfolio. Unaffordable buys may still be unfilled.
        staged = deepcopy(self)
        log = staged._rebalance(targets, quotes, identities, signal_date, settlement_date, cost_rate)
        self.__dict__.update(staged.__dict__)
        return log

    def _rebalance(self, targets, quotes, identities, signal_date, settlement_date, cost_rate):
        if any(type(q) is not int or q < 0 for q in targets.values()):
            raise ValueError("nonnegative integer targets required")
        deltas = {t: targets.get(t, 0) - (self.positions[t].quantity if t in self.positions else 0)
                  for t in set(targets) | set(self.positions)}
        log = []
        for buying in (False, True):
            for ticker in sorted(deltas):
                delta = deltas[ticker]
                if not delta or (delta > 0) != buying:
                    continue
                identity = identities[ticker]
                while delta:
                    result = self.order(ticker, identity["isin"], delta, quotes[ticker], signal_date,
                                        settlement_date, cost_rate, identity.get("lot", 100),
                                        identity.get("tax_class", "equity"))
                    if result:
                        log.append(result)
                        break
                    delta -= 1  # Only buys can be unfilled for buying power.
        return log

    def deliver_conversion(self, ticker, isin, deliveries, removed_basis_allocation):
        """Explicit whole-share replacement; fractions require reviewed cash terms.

        Caller supplies legal share quantities and tax-basis fractions, not a
        convenient price-ratio inference. Cash consideration is a separate event.
        """
        original = self.positions[ticker]
        if original.isin != isin:
            raise ValueError("conversion identity mismatch")
        weights = [number(v) for v in removed_basis_allocation]
        if len(weights) != len(deliveries) or sum(weights) != 1 or any(v < 0 for v in weights):
            raise ValueError("explicit complete cost-basis allocation required")
        staged = {}
        for leg, weight in zip(deliveries, weights):
            quantity = leg["quantity"]
            if type(quantity) is not int or quantity <= 0:
                raise ValueError("fractional or missing stock-delivery terms")
            if iso(leg["credit_date"]) < self.day or leg["tax_class"] not in {"equity", "bdr"}:
                raise ValueError("invalid delivery date or tax class")
            dest = leg["ticker"]
            if dest in staged or (dest in self.positions and dest != ticker):
                raise ValueError("conversion merging requires separate delivered lots")
            staged[dest] = Holding(leg["isin"], quantity, original.basis * weight,
                                   leg["tax_class"], iso(leg["credit_date"]))
        del self.positions[ticker]
        self.positions.update(staged)


def execution_readiness(required_intervals, coverage, cash_rows, action_gaps, execution_checks=None):
    """Report unresolved evidence before any historical wealth is published."""
    issues = []
    required_intervals = list(required_intervals)
    if not required_intervals:
        issues.append({"kind": "EMPTY_COVERAGE_UNIVERSE"})
    verified = {tuple(r["interval"]) for r in coverage if r.get("verified") is True and r.get("sources")}
    for key in required_intervals:
        if tuple(key) not in verified:
            issues.append({"kind": "CASH_COVERAGE", "interval": key})
    keys = set()
    for r in cash_rows:
        key = r.get("event_id")
        if not key or key in keys:
            issues.append({"kind": "ENTITLEMENT_IDENTITY", "event": key})
        keys.add(key)
        for field in ("ticker", "isin", "ex_date", "payment_date", "available_on", "tax_source", "sources"):
            if not r.get(field):
                issues.append({"kind": "CASH_EVENT_FIELD", "event": key, "field": field})
        if r.get("source_review") is not True:
            issues.append({"kind": "CASH_EVENT_FIELD", "event": key, "field": "source_review"})
        try:
            if number(r.get("net_per_share")) < 0:
                raise ValueError("negative net amount")
        except ValueError:
            issues.append({"kind": "CASH_EVENT_FIELD", "event": key, "field": "net_per_share"})
        try:
            if not iso(r.get("ex_date")) <= iso(r.get("payment_date")) < iso(r.get("available_on")):
                raise ValueError("cash chronology")
        except ValueError:
            issues.append({"kind": "CASH_CHRONOLOGY", "event": key})
    for name in ("quotes", "corporate_actions", "tax_schedule", "cash_coverage_inventory"):
        check = (execution_checks or {}).get(name, {})
        if check.get("verified") is not True or not check.get("sources"):
            issues.append({"kind": "EXECUTION_CHECK", "check": name})
    issues.extend(action_gaps)
    return {"ready": not issues, "issues": issues, "profit": None,
            "new_historical_return_evaluations": 0}
