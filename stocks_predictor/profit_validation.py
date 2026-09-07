"""Independent arithmetic and fragility audit; never an executable profit claim.

The chronological book deliberately does not call the original return scorer.
It values fractional stock entitlements and gross compulsory cash at face value.
Ordinary cash, retail fills, delivery and taxes require separate evidence.
"""

from collections import defaultdict
from datetime import date
import math
import statistics


def entitlement_book(member, entry, exit_day, bars, factors, terms, mode="open"):
    """Track one initial share through the dated action book, including chains."""
    if mode not in {"open", "close", "worst"} or not entry < exit_day:
        raise ValueError("invalid mark mode or interval")
    ticker, isin = member["ticker"], member["isin"]
    if entry not in bars.get(ticker, {}):
        ceased = any(e["ticker"] == ticker and e["isin"] == isin and e["removes_original"]
                     and e["ex_date"] <= entry for e in terms["events"])
        if ceased:
            return {"return": 0.0, "stocks": {}, "cash": 0.0, "failed_entry": True}
        raise ValueError("unexplained missing entry")
    opening, closing = bars[ticker][entry]
    paid = opening if mode == "open" else closing if mode == "close" else max(opening, closing)
    stocks, identities = {ticker: 1.0}, {ticker: isin}
    cash, log = 0.0, []
    action_days = sorted({e["ex_date"] for e in terms["events"] if entry < e["ex_date"] <= exit_day}
                         | {d for f in factors.values() for d in f if entry < d <= exit_day})
    for day in action_days:
        before = dict(stocks)
        for symbol, quantity in before.items():
            stocks[symbol] = quantity / factors.get(symbol, {}).get(day, 1.0)
        changes = [e for e in terms["events"] if e["ex_date"] == day
                   and e["ticker"] in before and identities[e["ticker"]] == e["isin"]]
        if len({e["ticker"] for e in changes}) != len(changes):
            raise ValueError("multiple same-instrument conversions")
        for event in changes:
            symbol = event["ticker"]
            if factors.get(symbol, {}).get(day, 1.0) != 1:
                raise ValueError("simultaneous base change needs explicit conversion terms")
            quantity = stocks.pop(symbol)
            identities.pop(symbol)
            # Terms list the whole resulting basket, including any retained original.
            for leg in event["stocks"]:
                successor = leg["ticker"]
                if successor in identities and identities[successor] != leg["isin"]:
                    raise ValueError("colliding successor identities")
                stocks[successor] = stocks.get(successor, 0) + quantity * leg["ratio"]
                identities[successor] = leg["isin"]
            cash += quantity * sum(c["amount_brl"] for c in event["cash"])
            log.append({"ticker": symbol, "ex_date": day, "quantity_before": quantity})
    value = cash
    for symbol, quantity in stocks.items():
        opening, closing = bars[symbol][exit_day]
        mark = opening if mode == "open" else closing if mode == "close" else min(opening, closing)
        value += quantity * mark
    result = value / paid - 1
    if not math.isfinite(result) or result < -1:
        raise ValueError("invalid holding mark")
    return {"return": result, "stocks": stocks, "cash": cash, "entry_price": paid,
            "events": log, "failed_entry": False}


def compound_path(returns, start, end):
    """Synthetic reinvestment of marks, not cash flows; period endpoints only."""
    wealth = peak = 1.0
    worst = 0.0
    for value in returns:
        if not math.isfinite(value) or value < -1:
            raise ValueError("invalid path return")
        wealth *= 1 + value
        peak = max(peak, wealth)
        worst = min(worst, wealth / peak - 1)
    years = (date.fromisoformat(end) - date.fromisoformat(start)).days / 365.25
    if not returns or years <= 0:
        raise ValueError("empty or nonpositive time span")
    return {"terminal_multiple": wealth, "cumulative_return": wealth - 1,
            "annualized_geometric_return": wealth ** (1 / years) - 1,
            "period_mark_max_drawdown": worst, "years": years}


def summarize_audit_periods(periods, horizon, bootstrap):
    """All periods, identical paired block draws, descriptive intervals only."""
    if any(a["exit"] != b["entry"] for a, b in zip(periods, periods[1:])):
        raise ValueError("non-contiguous periods cannot be silently compounded")
    start, end = periods[0]["entry"], periods[-1]["exit"]
    strategy = [p["strategy"] for p in periods]
    benchmark = [p["benchmark"] for p in periods]
    spread = [a - b for a, b in zip(strategy, benchmark)]
    stressed = [(x - .0072) / horizon for x in spread]
    low, high, draws = bootstrap(stressed, statistics.mean, scheme="stationary",
                                block_length=12 // horizon, n_boot=10000, seed=20260907)
    years = defaultdict(list)
    for p in periods:
        years[p["asof"][:4]].append(p)
    annual = [{"signal_year": y, "periods": len(rows),
               "mean_strategy_return_per_period": statistics.mean(p["strategy"] for p in rows),
               "mean_spread_after_72bp_per_month": statistics.mean((p["strategy"]-p["benchmark"]-.0072)/horizon for p in rows)}
              for y, rows in sorted(years.items())]
    contributions = defaultdict(float)
    for p in periods:
        n, k = len(p["members"]), sum(m["selected"] for m in p["members"])
        for m in p["members"]:
            weight = (1/k if m["selected"] else 0) - 1/n
            contributions[m["cnpj"]] += weight*m["return"]/len(periods)/horizon
    return {
        "periods": len(periods), "start": start, "end": end,
        "mean_strategy_return_per_period": statistics.mean(strategy),
        "mean_benchmark_return_per_period": statistics.mean(benchmark),
        "gross_spread_per_month": statistics.mean(spread)/horizon,
        "spread_after_36bp_per_month": (statistics.mean(spread)-.0036)/horizon,
        "spread_after_72bp_per_month": statistics.mean(stressed),
        "descriptive_stationary_bootstrap_95pct_after_72bp": [low, high],
        "valid_bootstrap_draws": len(draws),
        "unadjusted_for_adaptive_search": True,
        "positive_strategy_periods": sum(r > 0 for r in strategy),
        "positive_excess_after_72bp_periods": sum(r > 0 for r in stressed),
        "worst_strategy_period": min(strategy),
        "synthetic_strategy_gross": compound_path(strategy, start, end),
        "synthetic_benchmark_gross": compound_path(benchmark, start, end),
        "synthetic_strategy_after_flat_72bp": compound_path([r-.0072 for r in strategy], start, end),
        "calendar_years": annual,
        "issuer_contribution_to_mean_monthly_gross_spread": sorted(
            [{"cnpj": c, "contribution": v} for c, v in contributions.items()],
            key=lambda r: -r["contribution"]),
        "limitation": "Synthetic compounding assumes every marked entitlement can fund the next period. It is not executable wealth or net profit. Drawdown is measured only at holding-period endpoints; intraperiod losses may be worse.",
    }


def audit_trials(observation, bars, factors, terms, bootstrap):
    results, max_error, checked = [], 0.0, 0
    for trial in observation["trials"]:
        per_mode = {mode: [] for mode in ("open", "close", "worst")}
        horizon = trial["holding_months"]
        for period in trial["periods"]:
            members = period["members"]
            if not members:
                continue
            if not period["asof"] < period["entry"] < period["exit"]:
                raise ValueError("noncausal execution")
            ranked = sorted(members, key=lambda m: (-m["factor"], m["ticker"]))
            if len({m["cnpj"] for m in members}) != len(members):
                raise ValueError("duplicate issuer")
            if len(members) < 20 or any(m["selected"] != (i < len(members)//5) for i, m in enumerate(ranked)):
                raise ValueError("selection differs from frozen rule")
            for mode, rows in per_mode.items():
                values = []
                for member in members:
                    book = entitlement_book(member, period["entry"], period["exit"], bars, factors, terms, mode)
                    if mode == "open":
                        error = abs(book["return"] - member["diagnostic_return"])
                        max_error = max(error, max_error)
                        checked += 1
                        if error > 1e-10:
                            raise ValueError(f"independent return mismatch: {member['ticker']} {period['entry']}")
                    values.append({"ticker": member["ticker"], "cnpj": member["cnpj"],
                                   "selected": member["selected"], **book})
                strategy = statistics.mean(m["return"] for m in values if m["selected"])
                benchmark = statistics.mean(m["return"] for m in values)
                if mode == "open" and abs(strategy-benchmark-period["complete_case_spread"]) > 1e-10:
                    raise ValueError("independent cross-section mismatch")
                rows.append({"asof": period["asof"], "entry": period["entry"], "exit": period["exit"],
                             "strategy": strategy, "benchmark": benchmark, "members": values})
        results.append({"family": trial["family"], "holding_months": horizon,
                        "modes": {m: {"summary": summarize_audit_periods(p, horizon, bootstrap), "periods": p}
                                  for m, p in per_mode.items()}})
    return {"independently_verified_cells": checked, "max_absolute_return_difference": max_error,
            "trials": results, "executable_profit_demonstrated": False}
