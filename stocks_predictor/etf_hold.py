"""Conditional, unlevered ETF buy/hold accounting; never a forecast or order API.

ETF-level events must be reconciled separately. Daily quotes do not certify fills,
and unknown maintenance expenses are not silently set to zero in a net-profit claim.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_UP


def number(value):
    if isinstance(value, bool):
        raise ValueError("Boolean financial input")
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError("Nonfinite financial input")
    return result


def cents(value):
    return number(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def settlement(trade_date, sessions, lag):
    days = sorted(set(sessions))
    if trade_date not in days or days.index(trade_date) + lag >= len(days):
        raise ValueError("Settlement calendar incomplete")
    return days[days.index(trade_date) + lag]


def validate_quotes(records, sessions, entry, exit_date, isin):
    if not records or entry >= exit_date:
        raise ValueError("Empty or invalid holding interval")
    dates = [r["date"] for r in records]
    for day in dates:
        date.fromisoformat(day)
    if dates != sorted(set(dates)) or dates[0] != entry or dates[-1] != exit_date:
        raise ValueError("Duplicate, unsorted or absent endpoint")
    expected = {day for day in sessions if entry <= day <= exit_date}
    if set(dates) != expected:
        raise ValueError("Missing quote coverage")
    for rec in records:
        if rec["isin"] != isin or rec["quote_factor"] != 1 or rec["currency"] != "R$":
            raise ValueError("Identity, currency or quote basis changed")
        if rec["ticker"] != "BOVA11" or rec["market_type"] != "010":
            raise ValueError("Wrong instrument/market")
        op, close, low, high, volume = [number(rec[k]) for k in ("open", "close", "low", "high", "volume_fin")]
        if not 0 < low <= min(op, close) <= max(op, close) <= high or volume <= 0:
            raise ValueError("Invalid OHLC or liquidity observation")


def simulate(records, sessions, *, capital, rate, mode, entry_signal, exit_signal,
             tax_rate="0.15", lot=10):
    """One specified path; caller must freeze it before reading outcomes.

    Cash, fees and tax are rounded to cents at each cash event. The historical
    lot constraint applies to sizing, including the cost reserve. No paid costs,
    execution capacity, complete event history or future outcome is asserted.
    """
    capital, rate, tax_rate = number(capital), number(rate), number(tax_rate)
    if capital <= 0 or not 0 <= rate < 1 or not 0 <= tax_rate <= 1:
        raise ValueError("Invalid capital/cost/tax")
    if isinstance(lot, bool) or not isinstance(lot, int) or lot < 1:
        raise ValueError("Invalid lot")
    if mode not in {"open", "worst_open_close"}:
        raise ValueError("Unsupported execution scenario")
    if not records:
        raise ValueError("Empty holding interval")
    date.fromisoformat(entry_signal)
    date.fromisoformat(exit_signal)
    entry, exit_date = records[0]["date"], records[-1]["date"]
    validate_quotes(records, sessions, entry, exit_date, "BRBOVACTF003")
    if not entry_signal < entry or not entry <= exit_signal < exit_date:
        raise ValueError("Decision must precede trade")
    buy = number(records[0]["open"])
    sell = number(records[-1]["open"])
    if mode == "worst_open_close":
        buy = max(buy, number(records[0]["close"]))
        sell = min(sell, number(records[-1]["close"]))
    units = int((capital / (buy * (1 + rate) * lot)).to_integral_value(rounding=ROUND_FLOOR)) * lot
    buy_notional = cents(units * buy)
    buy_cost = cents(buy_notional * rate)
    while units > 0 and buy_notional + buy_cost > capital:
        units -= lot
        buy_notional = cents(units * buy)
        buy_cost = cents(buy_notional * rate)
    next_notional = cents((units + lot) * buy)
    if next_notional + cents(next_notional * rate) <= capital:
        units += lot
        buy_notional = next_notional
        buy_cost = cents(buy_notional * rate)
    if units <= 0:
        raise ValueError("No affordable lot; not a zero-return observation")
    basis = buy_notional + buy_cost
    residual = capital - basis
    sale_notional = cents(units * sell)
    sale_cost = cents(sale_notional * rate)
    sale_receivable = sale_notional - sale_cost
    pretax = sale_receivable - basis
    tax = cents(max(Decimal(0), pretax) * tax_rate)
    final_equity = residual + sale_receivable - tax
    profit = final_equity - capital
    if profit != pretax - tax:
        raise ArithmeticError("Wealth and realized-profit paths disagree")
    buy_settlement = settlement(entry, sessions, 3 if entry < "2019-05-27" else 2)
    sell_settlement = settlement(exit_date, sessions, 3 if exit_date < "2019-05-27" else 2)
    curve, deltas, annual = [], [], {}
    peak, previous, worst, min_equity = capital, capital, Decimal(0), capital
    peak_date, worst_dates = entry, None
    underwater = longest_underwater = 0
    for i, rec in enumerate(records):
        # At exit the ETF is already sold; no later close may enter valuation.
        equity = final_equity if i == len(records) - 1 else residual + units * number(rec["close"])
        delta = equity - previous
        deltas.append((rec["date"], delta))
        year = rec["date"][:4]
        annual[year] = annual.get(year, Decimal(0)) + delta
        if equity >= peak:
            peak, peak_date, underwater = equity, rec["date"], 0
        else:
            underwater += 1
            longest_underwater = max(longest_underwater, underwater)
        drawdown = (peak - equity) / peak
        if drawdown > worst:
            worst, worst_dates = drawdown, {"peak": peak_date, "trough": rec["date"]}
        min_equity = min(min_equity, equity)
        curve.append({"date": rec["date"], "equity_brl": float(equity), "drawdown": float(drawdown)})
        previous = equity
    if sum(annual.values()) != profit:
        raise ArithmeticError("Calendar attribution does not reconcile")
    days = (date.fromisoformat(exit_date) - date.fromisoformat(entry)).days
    years = days / 365.25
    top5 = sorted(deltas, key=lambda item: item[1], reverse=True)[:5]
    early = sum((v for d, v in deltas if d < "2022-01-01"), Decimal(0))
    late = sum((v for d, v in deltas if d >= "2022-01-01"), Decimal(0))
    volumes = [number(r["volume_fin"]) for r in records]
    last20 = sum(volumes[-21:-1]) / len(volumes[-21:-1]) if len(volumes) > 1 else None
    return {
        "capital_brl": float(capital), "mode": mode, "one_way_cost_rate": float(rate),
        "entry": entry, "exit": exit_date, "holding_calendar_days": days, "holding_years": years,
        "units": units, "lot_at_entry": lot, "buy_reference_brl": float(buy),
        "sell_reference_brl": float(sell), "buy_notional_brl": float(buy_notional),
        "buy_cost_brl": float(buy_cost), "tax_basis_brl": float(basis),
        "residual_cash_brl": float(residual), "sale_notional_brl": float(sale_notional),
        "sale_cost_brl": float(sale_cost), "sale_receivable_brl": float(sale_receivable),
        "modeled_pretax_profit_brl": float(pretax), "tax_obligation_brl": float(tax),
        "end_equity_after_tax_reserve_brl": float(final_equity),
        "conditional_profit_before_unknown_expenses_brl": float(profit),
        "cumulative_conditional_return": float(profit / capital),
        "historical_annualized_conditional_return": (float(final_equity / capital) ** (1 / years)) - 1,
        "unknown_additional_expenses_brl": None, "fully_net_executable_profit_brl": None,
        "expected_future_profit_brl": None, "event_inventory_certified": False,
        "equity_reconciliation_difference_brl": 0,
        "entry_capital_committed_brl": float(basis), "entry_equity_exposure_fraction": float(buy_notional / capital),
        "entry_daily_volume_participation": float(buy_notional / volumes[0]),
        "exit_daily_volume_participation": float(sale_notional / volumes[-1]),
        "exit_prior20_mean_volume_participation": float(sale_notional / last20) if last20 else None,
        "minimum_daily_volume_brl": float(min(volumes)), "certified_capacity_brl": None,
        "max_marked_drawdown": float(worst), "max_drawdown_dates": worst_dates,
        "longest_underwater_observations": longest_underwater,
        "largest_marked_loss_from_initial_brl": float(capital - min_equity),
        "calendar_year_pnl_brl": {k: float(v) for k, v in annual.items()},
        "pre_2022_pnl_brl": float(early), "from_2022_pnl_brl": float(late),
        "top5_positive_daily_pnl": [{"date": d, "pnl_brl": float(v)} for d, v in top5 if v > 0],
        "top5_positive_share_of_net_profit": float(sum(v for _, v in top5 if v > 0) / profit) if profit > 0 else None,
        "historical_undiscounted_expense_break_even_brl": float(profit),
        "historical_expense_budget_per_year_brl": float(profit) / years,
        "historical_hours_per_month_at_25_brl": max(0, float(profit)) / years / 12 / 25,
        "historical_hours_per_month_at_50_brl": max(0, float(profit)) / years / 12 / 50,
        "cash_timeline": [
            {"date": entry, "event": "BUY_RESERVED", "cash_available": float(residual),
             "cash_reserved": float(basis), "purchase_payable": float(basis),
             "etf_units_receivable": units, "position_value_at_trade": float(buy_notional),
             "equity": float(capital - buy_cost)},
            {"date": buy_settlement, "event": "BUY_SETTLED", "cash_available": float(residual),
             "cash_reserved": 0, "purchase_payable": 0, "etf_units": units},
            {"date": exit_date, "event": "SALE_UNSETTLED_TAX_RESERVED", "cash_available": float(residual),
             "etf_units": 0, "sale_receivable": float(sale_receivable), "tax_obligation": float(tax),
             "equity": float(final_equity)},
            {"date": sell_settlement, "event": "SALE_SETTLED_TAX_STILL_RESERVED",
             "cash_total": float(residual + sale_receivable), "sale_receivable": 0,
             "tax_obligation": float(tax), "cash_after_tax_reserve": float(final_equity)}],
        "notes": ["One purchase/one sale; all alternatives reuse the same hypothetical initial capital.",
                  "Conditional on unchanged ETF units and no external ETF distributions; not a complete event audit.",
                  "No investor dividend credit added to accumulating-fund prices; fund expenses not charged twice.",
                  "Withholding credits are part of total tax, not an additional tax charge. Payment timing not simulated.",
                  "Marked drawdown is at daily closes (terminal sale after tax); intraday loss can be larger.",
                  "Maintenance budget is an undiscounted historical ceiling, not spendable recurring income or a forecast.",
                  "Full capital reserved at entry; residual cash unremunerated; no early use of unsettled sale proceeds."],
        "equity_curve": curve,
    }


def selic_reference(data, sessions, entry, exit_date):
    """Gross official daily rate reference, not a tradable net benchmark."""
    rates = {}
    for row in data:
        day, month, year = row["data"].split("/")
        key = f"{year}-{month}-{day}"
        date.fromisoformat(key)
        if key in rates:
            raise ValueError("Duplicate Selic observation")
        value = number(row["valor"]) / 100
        if value <= -1 or not entry <= key < exit_date:
            raise ValueError("Invalid Selic date/rate")
        rates[key] = value
    if not rates or min(rates) != entry:
        raise ValueError("Incomplete Selic endpoints")
    missing = sorted({d for d in sessions if entry <= d < exit_date} - rates.keys())
    if missing:
        raise ValueError(f"Selic missing trading dates: {missing}")
    factor = Decimal(1)
    for key in sorted(rates):
        factor *= 1 + rates[key]
    return {"series": 11, "n_observations": len(rates), "start_inclusive": entry,
            "end_exclusive": exit_date, "gross_factor": float(factor),
            "label": "Gross overnight Selic opportunity reference; no investable product, fees, tax or equal equity risk implied."}
