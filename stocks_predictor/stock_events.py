"""Explicit bonus entitlements, with a separate date of share delivery."""

import hashlib
import json
import math

if __package__:
    from .cvm_pit import append_rows, iso_date
else:
    from cvm_pit import append_rows, iso_date


def import_bonus_events(conn, payload):
    sha = hashlib.sha256(payload).hexdigest()
    rows = json.loads(payload)
    records, seen = [], set()
    for row in rows:
        ex, credit = iso_date(row["ex_date"]), iso_date(row["credit_date"])
        ratio = row["new_shares_per_old"]
        if credit < ex or not math.isfinite(ratio) or ratio <= 0:
            raise ValueError("invalid stock bonus dates/ratio")
        if not all(row.get(k, "").strip() for k in ("ticker", "event_id", "source")):
            raise ValueError("missing stock bonus identity/source")
        key = row["ticker"], row["event_id"]
        if key in seen:
            raise ValueError("duplicate stock bonus identity")
        seen.add(key)
        records.append({k: row[k] for k in (
            "ticker", "event_id", "ex_date", "credit_date", "new_shares_per_old", "source"
        )} | {"source_sha256": sha})
    return append_rows(conn, "stock_bonus_events", records, ("ticker", "event_id"))


def bonus_events(conn, ticker, end):
    return [tuple(row) for row in conn.execute(
        "SELECT ex_date,credit_date,new_shares_per_old FROM stock_bonus_events"
        " WHERE ticker=? AND ex_date<=? ORDER BY ex_date,credit_date,event_id", (ticker, end)
    )]
