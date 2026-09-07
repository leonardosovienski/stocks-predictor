"""Cash distributions require security-specific ex-dates, amounts and coverage.

The old FRE payment-date/float-denominator approximation is never consulted.
An empty events table cannot assert a zero-dividend history without coverage.
"""

import csv
import hashlib
import io
import math

if __package__:
    from .cvm_pit import append_rows, iso_date
else:
    from cvm_pit import append_rows, iso_date


def import_verified_events(conn, payload, coverage):
    """Offline UTF-8 CSV plus source-backed inclusive coverage intervals.

    coverage = [{ticker,start_date,end_date,source}]. Each source must identify
    the underlying security-level history, including periods with no events.
    The caller is responsible for verifying that evidence; this cannot infer
    an ex-date from a payment date or a per-share amount from company totals.
    """
    sha = hashlib.sha256(payload).hexdigest()
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig")))
    required = {"ticker", "event_id", "ex_date", "payment_date", "value_per_share", "source"}
    if not required.issubset(reader.fieldnames or []):
        raise ValueError("cash events need ticker/event_id/ex_date/payment_date/value_per_share/source")
    intervals = []
    for interval in coverage:
        start, end = iso_date(interval["start_date"]), iso_date(interval["end_date"])
        if start > end or not interval["source"].strip() or not interval["ticker"].strip():
            raise ValueError("invalid cash-event coverage")
        intervals.append({**interval, "source_sha256": sha})
    events = []
    seen = {}
    for row in reader:
        if None in row or any(row.get(k) is None for k in required):
            raise ValueError("malformed cash-event CSV")
        ex, pay = iso_date(row["ex_date"]), iso_date(row["payment_date"])
        amount = float(row["value_per_share"])
        if pay < ex or not math.isfinite(amount) or amount <= 0:
            raise ValueError("invalid dividend dates/amount")
        if not all(row[k].strip() for k in ("ticker", "event_id", "source")):
            raise ValueError("cash-event identity/source is missing")
        if not any(
            c["ticker"] == row["ticker"] and c["start_date"] <= ex <= c["end_date"] for c in intervals
        ):
            raise ValueError("event lies outside verified coverage")
        record = {k: row[k].strip() for k in ("ticker", "event_id", "source")}
        record.update(ex_date=ex, payment_date=pay, value_per_share=amount, source_sha256=sha)
        key = record["ticker"], record["event_id"]
        if key in seen:
            raise ValueError(f"duplicate event identity in input: {key}")
        seen[key] = record
        events.append(record)
    # Both tables are committed or neither is, including conflicts against prior files.
    conn.execute("SAVEPOINT cash_import")
    try:
        n = append_rows(conn, "cash_events", events, ("ticker", "event_id"))
        append_rows(conn, "cash_event_coverage", intervals, ("ticker", "start_date", "end_date"))
        conn.execute("RELEASE cash_import")
    except Exception:
        conn.execute("ROLLBACK TO cash_import")
        conn.execute("RELEASE cash_import")
        raise
    return n


def require_coverage(conn, ticker, start, end):
    from datetime import date, timedelta

    iso_date(start)
    iso_date(end)
    cursor = date.fromisoformat(start)
    for lo, hi in conn.execute(
        "SELECT start_date,end_date FROM cash_event_coverage WHERE ticker=? ORDER BY start_date", (ticker,)
    ):
        lo, hi = date.fromisoformat(lo), date.fromisoformat(hi)
        if lo > cursor:
            break
        if hi >= cursor:
            cursor = hi + timedelta(days=1)
        if cursor > date.fromisoformat(end):
            return
    raise ValueError(f"missing verified cash-event coverage: {ticker} {start}..{end}")


def total_return_series(conn, ticker, *, asof=None):
    """Gross ex-date reinvestment index for measurement, not a cash execution price.

    All cash events on a date are summed before compounding. Split factors and
    per-share cash stay in their contemporaneous bases, including multiple
    corporate actions between two quotes. No future split rescales past cash.
    """
    if __package__:
        from .simulation import load_bars, split_events
    else:
        from simulation import load_bars, split_events

    bars = load_bars(conn, ticker, end=asof)
    if not bars:
        return [], []
    dates = sorted(bars)
    require_coverage(conn, ticker, dates[0], dates[-1])
    splits = split_events(conn, ticker, dates[-1])
    dividends = {}
    for ex, amount in conn.execute(
        "SELECT ex_date,value_per_share FROM cash_events WHERE ticker=?"
        " AND ex_date>? AND ex_date<=? ORDER BY ex_date",
        (ticker, dates[0], dates[-1]),
    ):
        dividends[ex] = dividends.get(ex, 0.0) + amount
    values = [bars[dates[0]][1]]
    for prev, cur in zip(dates, dates[1:]):
        units, cash = 1.0, 0.0
        for day in sorted(d for d in set(splits) | set(dividends) if prev < d <= cur):
            units /= splits.get(day, 1.0)
            cash += units * dividends.get(day, 0.0)
        gross = (units * bars[cur][1] + cash) / bars[prev][1]
        values.append(values[-1] * gross)
    return dates, values
