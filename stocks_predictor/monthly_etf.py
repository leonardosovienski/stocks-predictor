"""H22 retrospective long/cash experiment. No broker or operational entry point.

All money is rounded to cents, half up. Taxes remain committed/encumbered rather
than claiming actual payment; their cash cannot be reinvested. This has the same
wealth effect as payment because uninvested cash earns zero. No event adjustment
is invented here: source readiness must be assessed separately by the caller.
"""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


def money(value: Any) -> Decimal:
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError("Money must be finite")
    return result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Costs:
    variable: Decimal
    fixed: Decimal
    monthly: Decimal
    price_mode: str = "open"

    def __post_init__(self):
        if any(not x.is_finite() or x < 0 for x in (self.variable, self.fixed, self.monthly)):
            raise ValueError("Invalid cost")
        if self.variable >= 1 or self.price_mode not in {"open", "worst_open_close"}:
            raise ValueError("Invalid cost/price mode")
        if self.fixed != money(self.fixed) or self.monthly != money(self.monthly):
            raise ValueError("Fixed expenses must be cents")


class MonthlyTax:
    """Ordinary ETF scenario: monthly netting, forward losses, no past refund."""

    def __init__(self):
        self.loss = Decimal(0)
        self.committed = Decimal(0)
        self.gain = Decimal(0)
        self.ledger: list[dict[str, Any]] = []

    @property
    def provisional(self) -> Decimal:
        return money(max(Decimal(0), self.gain - self.loss) * Decimal("0.15"))

    @property
    def liability(self) -> Decimal:
        return self.committed + self.provisional

    def finish(self, month: str):
        tax = self.provisional
        self.ledger.append({"month": month, "realized_gain": float(self.gain),
                            "loss_before": float(self.loss), "tax_committed": float(tax)})
        self.committed += tax
        self.loss = max(Decimal(0), self.loss - self.gain)
        self.gain = Decimal(0)


def validate_prices(records: list[dict[str, Any]], calendar: list[str]):
    if not records or calendar != sorted(set(calendar)):
        raise ValueError("Empty prices or nonunique/unsorted calendar")
    for day in calendar:
        if date.fromisoformat(day).isoformat() != day:
            raise ValueError("Noncanonical date")
    dates = [r["date"] for r in records]
    if dates != sorted(set(dates)):
        raise ValueError("Nonunique/unsorted prices")
    expected = [d for d in calendar if dates[0] <= d <= dates[-1]]
    if dates != expected:
        raise ValueError("Prices do not cover supplied sessions exactly")
    for r in records:
        if (r["ticker"], r["isin"], r["currency"], r["market_type"],
                r["quote_factor"]) != ("BOVA11", "BRBOVACTF003", "R$", "010", 1):
            raise ValueError("Instrument identity mismatch")
        # The original 2019 archive contains 92 BOVA11 spot records under 02.
        # ISIN, ticker, currency and market remain identical; retain source BDI.
        if r["bdi_code"] not in {"02", "14"}:
            raise ValueError("Unexpected BDI")
        o, h, lo, c = (money(r[k]) for k in ("open", "high", "low", "close"))
        if not (0 < lo <= min(o, c) <= max(o, c) <= h) or r["qty"] <= 0:
            raise ValueError("Invalid price/volume")


def monthly_signals(records: list[dict[str, Any]], calendar: list[str]) -> list[dict[str, Any]]:
    validate_prices(records, calendar)
    by_day = {r["date"]: r for r in records}
    last: dict[str, str] = {}
    for day in calendar:
        last[day[:7]] = day
    closes: list[tuple[str, Decimal]] = []
    signals = []
    positions = {d: i for i, d in enumerate(calendar)}
    for day in last.values():
        if day not in by_day:
            continue
        closes.append((day, money(by_day[day]["close"])))
        if len(closes) < 10:
            continue
        window = closes[-10:]
        months = [date.fromisoformat(d).year * 12 + date.fromisoformat(d).month for d, _ in window]
        if months[-1] - months[0] != 9:
            raise ValueError("Missing complete warmup month")
        i = positions[day]
        if i + 1 >= len(calendar):
            continue
        total = sum((c for _, c in window), Decimal(0))
        signals.append({"signal_date": day, "execution_date": calendar[i + 1],
                        "long": window[-1][1] * 10 > total,
                        "close": float(window[-1][1]), "sma10": float(total / 10),
                        "input_dates": [d for d, _ in window]})
    return signals


def simulate(records: list[dict[str, Any]], calendar: list[str], *, start: str, end: str,
             capital: Any, costs: Costs, arm: str) -> dict[str, Any]:
    signals = monthly_signals(records, calendar)
    if arm not in {"trend", "hold"} or start > end:
        raise ValueError("Invalid arm/window")
    initial = money(capital)
    if initial <= 0:
        raise ValueError("Capital must be positive")
    rows = [r for r in records if start <= r["date"] <= end]
    if not rows:
        raise ValueError("Empty window")
    prior = [s for s in signals if s["execution_date"] <= rows[0]["date"]]
    if not prior:
        raise ValueError("Ten completed months required before entry")
    latest = prior[-1]
    by_execution = {s["execution_date"]: s for s in signals}
    months = sorted({r["date"][:7] for r in rows})
    reserved = money(costs.monthly * len(months))
    if reserved > initial:
        return {"status": "INFEASIBLE_EXPENSE_RESERVE", "capital": float(initial),
                "required_expense_reserve": float(reserved), "months": len(months)}
    cash = initial - reserved
    pending: list[tuple[str, Decimal]] = []
    position = 0
    basis = Decimal(0)
    tax = MonthlyTax()
    ledger: list[dict[str, Any]] = []
    curve: list[dict[str, Any]] = []
    indices = {d: i for i, d in enumerate(calendar)}
    peak = initial
    max_dd = Decimal(0)
    min_wealth = initial
    previous_month = ""
    previous_target = False
    expenses = Decimal(0)
    fees = Decimal(0)
    for r in rows:
        day = r["date"]
        month = day[:7]
        for due, amount in pending:
            if due <= day:
                cash += amount
        pending = [(due, amount) for due, amount in pending if due > day]
        if month != previous_month:
            if previous_month:
                tax.finish(previous_month)
            reserved -= costs.monthly
            expenses += costs.monthly
            ledger.append({"date": day, "kind": "EXPENSE", "amount": float(costs.monthly)})
            previous_month = month
        if day in by_execution:
            latest = by_execution[day]
        target = arm == "hold" or latest["long"]
        # Terminal liquidation is precommitted; do not open a same-day round trip.
        if day == rows[-1]["date"]:
            target = False
        if target != previous_target:
            if target:
                price = money(r["open"])
                if costs.price_mode == "worst_open_close":
                    price = max(price, money(r["close"]))
                available = max(Decimal(0), cash - tax.liability)
                qty = max(0, int((available - costs.fixed + Decimal("0.005"))
                                // (price * 10 * (1 + costs.variable)))) * 10
                fee = money(price * qty * costs.variable) + costs.fixed
                while qty and price * qty + fee > available:
                    qty -= 10
                    fee = money(price * qty * costs.variable) + costs.fixed
                if not qty:
                    ledger.append({"date": day, "kind": "REJECTED_BUY", "reason": "NO_AFFORDABLE_LOT",
                                   "available": float(available), "signal_date": latest["signal_date"]})
                else:
                    position = qty
                    basis = price * qty + fee
                    cash -= basis
                    fees += fee
                    ledger.append({"date": day, "kind": "BUY", "qty": qty, "price": float(price),
                                   "fee": float(fee), "basis": float(basis),
                                   "available_before": float(available), "signal_date": latest["signal_date"]})
            elif position:
                price = money(r["open"])
                if costs.price_mode == "worst_open_close":
                    price = min(price, money(r["close"]))
                fee = money(price * position * costs.variable) + costs.fixed
                proceeds = price * position - fee
                if proceeds < 0:
                    raise ValueError("Sale costs exceed proceeds")
                gain = proceeds - basis
                tax.gain += gain
                lag = 3 if day < "2019-05-27" else 2
                if indices[day] + lag >= len(calendar):
                    raise ValueError("Missing settlement sessions")
                due = calendar[indices[day] + lag]
                pending.append((due, proceeds))
                fees += fee
                ledger.append({"date": day, "kind": "SELL", "qty": position, "price": float(price),
                               "fee": float(fee), "basis": float(basis), "proceeds": float(proceeds),
                               "realized_gain": float(gain), "settlement_date": due,
                               "signal_date": latest["signal_date"], "terminal": day == rows[-1]["date"]})
                position = 0
                basis = Decimal(0)
        previous_target = target
        receivable = sum((amount for _, amount in pending), Decimal(0))
        wealth = cash + reserved + receivable + position * money(r["close"]) - tax.liability
        if cash < 0 or reserved < 0 or wealth < 0:
            raise ValueError("Unfunded obligation")
        peak = max(peak, wealth)
        max_dd = max(max_dd, 1 - wealth / peak)
        min_wealth = min(min_wealth, wealth)
        curve.append({"date": day, "wealth": float(wealth), "cash_gross": float(cash),
                      "receivable": float(receivable), "expense_reserve": float(reserved),
                      "tax_committed_and_provisional": float(tax.liability), "qty": position,
                      "investable_cash": float(max(Decimal(0), cash - tax.liability))})
    tax.finish(previous_month)
    final = money(curve[-1]["wealth"])
    years: dict[str, Decimal] = {}
    prev = initial
    for point in curve:
        y = point["date"][:4]
        current = money(point["wealth"])
        years[y] = years.get(y, Decimal(0)) + current - prev
        prev = current
    return {"status": "CONDITIONAL_SIMULATION", "arm": arm, "capital": float(initial),
            "start": rows[0]["date"], "end": rows[-1]["date"], "sessions": len(rows),
            "final_wealth": float(final), "profit": float(final - initial),
            "max_drawdown": float(max_dd), "minimum_wealth": float(min_wealth),
            "fees": float(fees), "expenses": float(expenses), "tax": float(tax.committed),
            "loss_carry": float(tax.loss), "order_count": sum(x["kind"] in {"BUY", "SELL"} for x in ledger),
            "exposure_fraction": sum(x["qty"] > 0 for x in curve) / len(curve),
            "year_profit": {y: float(v) for y, v in years.items()},
            "ledger": ledger, "tax_ledger": tax.ledger, "curve": curve,
            "source_gates": "Events/cost completeness are external; not certified by this simulator"}
