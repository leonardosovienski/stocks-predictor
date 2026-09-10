"""Independent integer-cent replay; does not import the simulation engine."""
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP


def cents(value):
    return int((Decimal(str(value)) * 100).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def verify(result, inputs, spec):
    if result["status"] == "INFEASIBLE_EXPENSE_RESERVE":
        assert result["required_expense_reserve"] > result["capital"]
        return {"status": "EXPECTED_INFEASIBLE"}
    quotes = {r["date"]: r for r in inputs["records"]}
    calendar = inputs["calendar"]
    index = {d: i for i, d in enumerate(calendar)}
    last = {}
    for day in calendar:
        last[day[:7]] = day
    completed = [d for d in last.values() if d in quotes]
    signal = {}
    for i in range(9, len(completed)):
        d = completed[i]
        signal[calendar[index[d] + 1]] = cents(quotes[d]["close"]) * 10 > sum(
            cents(quotes[x]["close"]) for x in completed[i - 9:i + 1])
    capital = cents(result["capital"])
    monthly = cents(spec["monthly_expense_brl"])
    months = len({p["date"][:7] for p in result["curve"]})
    reserve = monthly * months
    cash = capital - reserve
    position = basis = total_fees = expense_paid = tax = loss = month_gain = 0
    pending = []
    flows = 0
    current_month = None
    events = defaultdict(list)
    for entry in result["ledger"]:
        events[entry["date"]].append(entry)
    last_state = False
    target = signal[max(d for d in signal if d <= result["start"])]
    fee_ppm = int(Decimal(str(spec["one_way_variable_cost"])) * 1000000)
    fixed = cents(spec["fixed_cost_per_order_brl"])

    def fee(gross):
        return (gross * fee_ppm + 500000) // 1000000 + fixed

    peak = capital
    max_dd = 0.0
    min_wealth = capital
    for point in result["curve"]:
        day = point["date"]
        month = day[:7]
        cash += sum(amount for due, amount in pending if due <= day)
        pending = [(due, amount) for due, amount in pending if due > day]
        if month != current_month:
            tax += (max(0, month_gain - loss) * 15 + 50) // 100
            loss = max(0, loss - month_gain)
            month_gain = 0
            current_month = month
            reserve -= monthly
            expense_paid += monthly
            flows -= monthly
            assert [e["amount"] for e in events[day] if e["kind"] == "EXPENSE"] == [monthly / 100]
        else:
            assert not any(e["kind"] == "EXPENSE" for e in events[day])
        if day in signal:
            target = signal[day]
        state = True if result["arm"] == "hold" else target
        if day == result["end"]:
            state = False
        trade_entries = [e for e in events[day] if e["kind"] != "EXPENSE"]
        needs_trade = state != last_state and (state or position > 0)
        assert len(trade_entries) == int(needs_trade)
        for entry in trade_entries:
            buy = state
            price = cents(quotes[day]["open"])
            if spec["price_mode"] == "worst_open_close":
                close = cents(quotes[day]["close"])
                price = max(price, close) if buy else min(price, close)
            liability = tax + (max(0, month_gain - loss) * 15 + 50) // 100
            available = max(0, cash - liability)
            if entry["kind"] == "REJECTED_BUY":
                assert buy and price * 10 + fee(price * 10) > available
                continue
            qty = entry["qty"]
            gross = price * qty
            actual_fee = fee(gross)
            assert entry["kind"] == ("BUY" if buy else "SELL")
            assert cents(entry["price"]) == price and cents(entry["fee"]) == actual_fee
            assert qty > 0 and qty % 10 == 0
            total_fees += actual_fee
            if buy:
                assert not position
                assert gross + actual_fee <= available
                assert price * (qty + 10) + fee(price * (qty + 10)) > available
                position = qty
                basis = gross + actual_fee
                cash -= basis
                flows -= basis
            else:
                assert qty == position
                proceeds = gross - actual_fee
                assert cents(entry["basis"]) == basis
                assert cents(entry["realized_gain"]) == proceeds - basis
                month_gain += proceeds - basis
                due = calendar[index[day] + (3 if day < "2019-05-27" else 2)]
                assert entry["settlement_date"] == due
                pending.append((due, proceeds))
                flows += proceeds
                position = basis = 0
        last_state = state
        liability = tax + (max(0, month_gain - loss) * 15 + 50) // 100
        receivable = sum(amount for _, amount in pending)
        wealth = cash + reserve + receivable + position * cents(quotes[day]["close"]) - liability
        for key, expected in [("wealth", wealth), ("cash_gross", cash), ("expense_reserve", reserve),
                              ("receivable", receivable), ("tax_committed_and_provisional", liability),
                              ("investable_cash", max(0, cash - liability))]:
            assert cents(point[key]) == expected, (day, key, point[key], expected)
        assert point["qty"] == position
        peak = max(peak, wealth)
        min_wealth = min(min_wealth, wealth)
        max_dd = max(max_dd, 1 - wealth / peak)
    tax += (max(0, month_gain - loss) * 15 + 50) // 100
    assert position == 0 and reserve == 0
    assert cents(result["final_wealth"]) == capital + flows - tax
    assert cents(result["profit"]) == flows - tax
    assert cents(result["tax"]) == tax
    assert cents(result["fees"]) == total_fees
    assert cents(result["expenses"]) == expense_paid
    assert cents(result["minimum_wealth"]) == min_wealth
    assert abs(result["max_drawdown"] - max_dd) < 1e-12
    assert sum(cents(v) for v in result["year_profit"].values()) == flows - tax
    return {"status": "PASS", "checked_sessions": len(result["curve"]),
            "method": "Separate integer-cent replay, signal chronology, max lot, settlement, expenses, monthly taxes, wealth and drawdown"}
