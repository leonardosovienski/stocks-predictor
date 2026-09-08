"""Freeze signal-date integer targets with optional H20 weight tolerance.

Execution delegates to RetailBook; callers must certify corporate boundaries and
provide the complete portfolio, including liabilities. This is local simulation.
"""
from copy import deepcopy
from dataclasses import asdict, dataclass
from decimal import Decimal
import hashlib
import json

from stocks_predictor.retail_cash import integer_targets, iso, number


def book_digest(book):
    state = dict(book.__dict__)
    state["positions"] = {t: asdict(h) for t, h in book.positions.items()}
    state["seen_right_ids"] = sorted(book.seen_right_ids)
    raw = json.dumps(state, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class FrozenRebalance:
    signal_date: str
    entry_date: str
    settlement_date: str
    expected_book_digest: str
    targets: tuple
    original_targets: tuple
    identities: tuple
    suppressed: tuple
    sizing_capital: Decimal
    weight_band: Decimal


def freeze_rebalance(book, selected, signal_quotes, entry_date, settlement_date, sizing_capital,
                     *, buffered=False):
    """Freeze against the actual signal book; every selected/held identity is checked."""
    asof = iso(book.day)
    if not asof < iso(entry_date) < iso(settlement_date):
        raise ValueError("signal, entry and settlement must increase")
    if len({m["ticker"] for m in selected}) != len(selected):
        raise ValueError("duplicate target member")
    identities = {m["ticker"]: (m["isin"], m.get("tax_class", "equity"), m.get("lot", 100)) for m in selected}
    for ticker, holding in book.positions.items():
        if ticker in identities and identities[ticker][:2] != (holding.isin, holding.tax_class):
            raise ValueError("target and held identity mismatch requires a reviewed conversion")
        lot = signal_quotes[ticker]["lot"]
        if ticker in identities and identities[ticker][2] != lot:
            raise ValueError("held and target lot mismatch")
        identities[ticker] = (holding.isin, holding.tax_class, lot)
    closes = {}
    for ticker, (isin, tax_class, lot) in identities.items():
        quote = signal_quotes[ticker]
        if quote.get("date") != asof or quote.get("isin") != isin:
            raise ValueError("signal quote identity or date mismatch")
        if (not isin or type(lot) is not int or lot <= 0 or tax_class not in {"equity", "bdr"}
                or quote.get("lot", lot) != lot):
            raise ValueError("invalid lot or tax class")
        closes[ticker] = number(quote["close"])
        if closes[ticker] <= 0:
            raise ValueError("nonpositive signal quote")
    capital = number(sizing_capital)
    ceiling = (book.cash - book.cash_buffer + sum((r["amount"] for r in book.pending), Decimal(0))
               + sum((h.quantity * closes[t] for t, h in book.positions.items()), Decimal(0)))
    if capital < 0 or capital > ceiling:
        raise ValueError("sizing capital exceeds signal assets after reserved liabilities")
    selected_prices = {m["ticker"]: closes[m["ticker"]] for m in selected}
    targets = integer_targets(capital, selected_prices) if selected_prices else {}
    original = tuple(sorted(targets.items()))
    band = Decimal(".025") if buffered else Decimal(0)
    suppressed = []
    for ticker, target in targets.items():
        held = book.positions[ticker].quantity if ticker in book.positions else 0
        difference = target - held
        # Never suppress a full exit, a new holding, or a mandatory liquidation.
        if held > 0 and target > 0 and difference and abs(difference) * closes[ticker] <= capital * band:
            targets[ticker] = held
            suppressed.append((ticker, difference, abs(difference) * closes[ticker]))
    expected = deepcopy(book)
    expected.advance(entry_date)
    return FrozenRebalance(asof, entry_date, settlement_date, book_digest(expected),
                           tuple(sorted(targets.items())), original,
                           tuple((t, *i) for t, i in sorted(identities.items())),
                           tuple(sorted(suppressed)), capital, band)


def execute_rebalance(book, plan, execution_quotes, cost_rate, *, order_units_reviewed=False):
    """Atomic simulated execution. No bypass for stale books or unchecked order units."""
    if order_units_reviewed is not True:
        raise ValueError("source review of signal-to-entry order units required")
    if book.day != plan.entry_date or book_digest(book) != plan.expected_book_digest:
        raise ValueError("book changed since the frozen signal; re-evaluate events and taxes")
    if not 0 <= number(cost_rate) < 1:
        raise ValueError("invalid cost rate")
    identities = {}
    for ticker, isin, tax_class, lot in plan.identities:
        q = execution_quotes[ticker]
        if q.get("date") != plan.entry_date or q.get("isin") != isin:
            raise ValueError("execution identity or date mismatch, including retained positions")
        identities[ticker] = {"isin": isin, "tax_class": tax_class, "lot": lot}
    staged = deepcopy(book)
    trades = staged.rebalance(dict(plan.targets), execution_quotes, identities,
                              plan.signal_date, plan.settlement_date, cost_rate)
    clearing = deepcopy(staged)
    clearing.advance(max([plan.settlement_date, *(r["date"] for r in clearing.pending)]))
    result = {"status": "SIMULATED_REBALANCE_NOT_PROFIT_EVIDENCE", "trades": trades,
              "suppressed": plan.suppressed, "original_targets": plan.original_targets,
              "targets": plan.targets, "filled_quantities": {t: h.quantity for t, h in staged.positions.items()},
              "unfilled_shares": {t: q - (staged.positions[t].quantity if t in staged.positions else 0)
                                  for t, q in plan.targets
                                  if q != (staged.positions[t].quantity if t in staged.positions else 0)},
              "traded_notional_brl": sum((r["gross"] for r in trades), Decimal(0)),
              "modeled_cost_brl": sum((r["costs"] for r in trades), Decimal(0)),
              "cleared_cash_brl": clearing.cash, "profit": None}
    book.__dict__.update(staged.__dict__)
    return result
