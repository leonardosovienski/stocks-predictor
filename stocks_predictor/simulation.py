"""Causal, self-financing long-only measurement; no ledger or verdict writes.

Signals at close are traded strictly later. Quantities drift with prices until
the next scheduled trade. Unquoted holdings retain their last mark and weight;
unfilled orders retain cash. A stale final holding makes valuation incomplete.
"""

from bisect import bisect_right
import math


ENGINE_VERSION = "stocks-causal-execution-v2"


def load_bars(conn, ticker, end=None):
    args = [ticker]
    cutoff = ""
    if end:
        cutoff = " AND date<=?"
        args.append(end)
    rows = conn.execute(
        "SELECT date,open,close,quote_factor FROM prices_raw"
        " WHERE market_type='010' AND ticker=?" + cutoff + " ORDER BY date",
        args,
    )
    bars = {}
    for day, opening, closing, quote_factor in rows:
        if quote_factor is None or not math.isfinite(quote_factor) or quote_factor <= 0:
            raise ValueError(f"invalid quote factor: {ticker}/{day}")
        values = opening / quote_factor, closing / quote_factor
        if any(not math.isfinite(p) or p <= 0 for p in values):
            raise ValueError(f"invalid OHLC: {ticker}/{day}")
        if day in bars and bars[day] != values:
            raise ValueError(f"ambiguous normalized prices: {ticker}/{day}")
        bars[day] = values
    return bars


def split_events(conn, ticker, end):
    result = {}
    for ex, factor in conn.execute(
        "SELECT ex_date,factor FROM adjustments WHERE ticker=?"
        " AND type IN ('split','grupamento') AND approved_by IS NOT NULL"
        " AND ex_date<=? ORDER BY ex_date",
        (ticker, end),
    ):
        if not math.isfinite(factor) or factor <= 0:
            raise ValueError("invalid approved split")
        result[ex] = result.get(ex, 1.0) * factor
    return result


def point_in_time_series(conn, ticker, asof):
    bars = load_bars(conn, ticker, end=asof)
    dates = sorted(bars)
    splits = split_events(conn, ticker, asof)
    closes = []
    for day in dates:
        close = bars[day][1]
        for ex, factor in splits.items():
            if day < ex <= asof:
                close *= factor
        closes.append(close)
    return dates, closes


def simulate_portfolio(
    dates,
    bars,
    targets,
    *,
    cost_per_side=0.0018,
    price_mode="next_open",
    splits=None,
    cash_events=None,
    initial_cash=1.0,
    require_final_quotes=True,
):
    """Return daily NAV returns, executions and pending-order diagnostics.

    At the first session after each signal, reserve target notionals from NAV
    net of estimated turnover costs. Sell before buying. Missing quotes delay
    just those orders; their notionals remain fixed until filled or superseded.
    No borrowed cash, silent renormalization, daily equal-weight reset or free
    disposal of an illiquid holding. Worst-of-open/close is an adverse scenario,
    not a claim that future closing prices are executable at the open.
    """
    if price_mode not in {"next_open", "next_close", "worst"}:
        raise ValueError("unsupported execution price")
    if not math.isfinite(cost_per_side) or not 0 <= cost_per_side < 0.1:
        raise ValueError("invalid transaction cost")
    if initial_cash <= 0 or not math.isfinite(initial_cash):
        raise ValueError("invalid initial cash")
    if dates != sorted(set(dates)):
        raise ValueError("session dates must be unique and sorted")
    for weights in targets.values():
        if any(not math.isfinite(w) or w < 0 for w in weights.values()) or sum(weights.values()) > 1 + 1e-10:
            raise ValueError("weights must be long-only, sum <= 1")
    cash = previous_nav = initial_cash
    holdings, marks, last_quote = {}, {}, {}
    pending, active_signal, target_values = {}, None, {}
    signal_dates = sorted(targets)
    signal_index = 0
    returns, navs, executions, stale_marks, receivables = [], [], [], [], []
    splits = splits or {}
    cash_events = cash_events or {}
    last_day = dates[0] if dates else None
    for day in dates:
        # Apply actions during quote gaps as well as on the next trading day.
        for ticker in list(holdings):
            for ex, multiplier in sorted(splits.get(ticker, {}).items()):
                if last_day < ex <= day:
                    if multiplier <= 0 or not math.isfinite(multiplier):
                        raise ValueError("invalid split factor")
                    holdings[ticker] /= multiplier
                    if ticker in marks:
                        marks[ticker] *= multiplier
            # Event amounts are on the post-split ex-date share base. Obtain
            # the entitlement before today's trades; purchases ex-date get none.
            for ex, pay, amount in cash_events.get(ticker, []):
                if last_day < ex <= day:
                    later_splits = math.prod(f for d, f in splits.get(ticker, {}).items() if ex < d <= day)
                    entitled = holdings[ticker] * later_splits
                    receivables.append((pay, entitled * amount))
        cash += sum(amount for pay, amount in receivables if pay <= day)
        receivables = [(pay, amount) for pay, amount in receivables if pay > day]
        receivable_value = sum(amount for _, amount in receivables)
        # Signals dated today are unavailable for execution until a later date.
        new_signal = None
        while signal_index < len(signal_dates) and signal_dates[signal_index] < day:
            new_signal = signal_dates[signal_index]
            signal_index += 1

        def mark(ticker):
            quote = bars.get(ticker, {}).get(day)
            if quote:
                return quote[1] if price_mode == "next_close" else quote[0]
            return marks.get(ticker, 0.0)

        if new_signal is not None:
            active_signal = new_signal
            weights = targets[new_signal]
            nav = cash + receivable_value + sum(q * mark(t) for t, q in holdings.items())
            investable = nav - receivable_value
            # Solve self-financing target weights, including resizing names
            # that remain members but whose weights drifted since last month.
            post_cost = investable
            names = set(weights) | set(holdings)
            for _ in range(100):
                turnover = sum(
                    abs(weights.get(t, 0) * post_cost - holdings.get(t, 0) * mark(t)) for t in names
                )
                next_value = investable - cost_per_side * turnover
                if abs(next_value - post_cost) < 1e-13 * initial_cash:
                    post_cost = next_value
                    break
                post_cost = next_value
            if post_cost < 0:
                raise ValueError("transaction costs exhaust capital")
            target_values = {t: weights.get(t, 0) * post_cost for t in names}
            pending = dict(target_values)
        # Execute reductions before additions. A missing sale cannot finance a purchase.
        for buying in (False, True):
            for ticker in sorted(list(pending)):
                quote = bars.get(ticker, {}).get(day)
                if not quote:
                    continue
                opening, closing = quote
                mid = closing if price_mode == "next_close" else opening
                current = holdings.get(ticker, 0.0)
                desired_value = pending[ticker]
                is_buy = desired_value > current * mid + initial_cash * 1e-12
                if is_buy != buying:
                    continue
                price = (max(quote) if buying else min(quote)) if price_mode == "worst" else mid
                desired = desired_value / mid
                delta = desired - current
                if abs(delta * price) < initial_cash * 1e-12:
                    pending.pop(ticker)
                    continue
                if delta > 0:
                    delta = min(delta, max(0.0, cash) / (price * (1 + cost_per_side)))
                if abs(delta * price) < initial_cash * 1e-12:
                    continue
                cost = abs(delta) * price * cost_per_side
                cash -= delta * price + cost
                if cash < -initial_cash * 1e-10:
                    raise AssertionError("self-financing invariant violated")
                cash = max(cash, 0.0)
                holdings[ticker] = current + delta
                if holdings[ticker] < initial_cash * 1e-12:
                    holdings.pop(ticker)
                executions.append(
                    {
                        "signal_date": active_signal,
                        "exec_date": day,
                        "ticker": ticker,
                        "quantity": delta,
                        "price": price,
                        "cost": cost,
                        "cash_after": cash,
                    }
                )
                if abs((desired - (current + delta)) * price) <= initial_cash * 1e-10:
                    pending.pop(ticker)
        for ticker in holdings:
            quote = bars.get(ticker, {}).get(day)
            if quote:
                marks[ticker] = quote[1]
                last_quote[ticker] = day
            elif ticker not in marks:
                raise ValueError("holding has no valuation price")
            else:
                stale_marks.append((day, ticker, last_quote.get(ticker)))
        nav = cash + receivable_value + sum(q * marks[t] for t, q in holdings.items())
        if not math.isfinite(nav) or nav <= 0:
            raise ValueError("nonpositive portfolio NAV")
        returns.append(nav / previous_nav - 1.0)
        navs.append(nav)
        previous_nav, last_day = nav, day
    if dates and require_final_quotes:
        stale = [t for t in holdings if last_quote.get(t) != dates[-1]]
        if stale:
            raise ValueError(f"incomplete final valuation; stale holdings: {stale}")
    return {
        "returns": returns,
        "nav": navs,
        "executions": executions,
        "pending_orders": pending,
        "holdings": holdings,
        "cash": cash,
        "receivables": receivables,
        "stale_marks": stale_marks,
        "engine_version": ENGINE_VERSION,
    }


def walk_forward(conn, cfg, signal_fn=None, take="top", portfolio_fn=None, series_fn=None):
    if __package__:
        from . import adjust, factor, portfolio, universe
        from .returns import month_end_dates
        from .cash_events import require_coverage
    else:
        import adjust
        import factor
        import portfolio
        import universe
        from returns import month_end_dates
        from cash_events import require_coverage

    adjust.require_scanned(conn)
    bt, execution, u = cfg["backtest"], cfg["execution"], cfg["universe"]
    # This instrument has no estimator fitting. Explicit train_end enables an
    # embargo; otherwise nonzero purge settings cannot silently be ignored.
    months = bt.get("purge_embargo_months", 0)
    test_start = bt.get("test_start", "0001-01-01")
    if months:
        from datetime import date

        if "train_end" not in bt:
            raise ValueError("purge_embargo_months requires explicit train_end; inert settings are forbidden")
        train_end = date.fromisoformat(bt["train_end"])
        # First eligible month after N complete embargo months.
        month_index = train_end.year * 12 + train_end.month + months
        cutoff = date(month_index // 12, month_index % 12 + 1, 1).isoformat()
        test_start = max(test_start, cutoff)
    all_dates = [
        r[0]
        for r in conn.execute("SELECT DISTINCT date FROM prices_raw WHERE market_type='010' ORDER BY date")
    ]
    end = bt.get("test_end") or (all_dates[-1] if all_dates else test_start)
    dates = [d for d in all_dates if test_start <= d <= end]
    rebalances = [d for d in month_end_dates(all_dates) if test_start <= d < end]
    targets, bench_targets, bars, splits, events = {}, {}, {}, {}, {}
    mode = execution.get("return_mode", "price")
    if mode not in {"price", "total"}:
        raise ValueError("unknown return mode")
    if series_fn and mode != "total":
        raise ValueError("custom total-return signal source requires total execution return_mode")
    if signal_fn is None:
        f = cfg.get("factor", {})
        signal_fn = lambda sub, asof: factor.signals(
            sub, asof, f.get("lookback_days", 252), f.get("skip_days", 21)
        )
    for asof in rebalances:
        tickers = universe.select_universe(
            conn,
            asof,
            u.get("top_n", 60),
            u.get("lookback_trading_days", 126),
            u.get("min_history_days", 252),
        )
        sub = {}
        for ticker in tickers:
            if ticker not in bars:
                bars[ticker] = load_bars(conn, ticker, end=end)
                splits[ticker] = split_events(conn, ticker, end)
                if mode == "total":
                    require_coverage(conn, ticker, dates[0], end)
                    events[ticker] = conn.execute(
                        "SELECT ex_date,payment_date,value_per_share FROM cash_events"
                        " WHERE ticker=? ORDER BY ex_date",
                        (ticker,),
                    ).fetchall()
            if series_fn:
                ds, ps = series_fn(conn, ticker, asof=asof)
            elif mode == "total":
                ds, ps = adjust.total_return_series(conn, ticker, asof=asof)
            else:
                ds, ps = point_in_time_series(conn, ticker, asof)
            cutoff = bisect_right(ds, asof)
            sub[ticker] = (ds[:cutoff], ps[:cutoff])
        if portfolio_fn:
            weights = portfolio_fn(sub, asof)
        else:
            chosen = list(portfolio.select_portfolio(signal_fn(sub, asof), 0.2, take=take))
            weights = {t: 1 / len(chosen) for t in chosen}
        if not set(weights).issubset(tickers):
            raise ValueError("portfolio contains an out-of-universe security")
        targets[asof] = weights
        bench_targets[asof] = {t: 1 / len(tickers) for t in tickers}
    settings = {
        "cost_per_side": execution.get("b3_fee_pct", 0.0003) + execution.get("spread_slippage_pct", 0.0015),
        "price_mode": execution.get("price", "next_open"),
        "splits": splits,
        "cash_events": events,
    }
    strategy = simulate_portfolio(dates, bars, targets, **settings)
    benchmark = simulate_portfolio(dates, bars, bench_targets, **settings)
    return strategy["returns"], benchmark["returns"]
