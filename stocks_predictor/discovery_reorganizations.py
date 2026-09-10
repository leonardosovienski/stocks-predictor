"""Diagnostic entitlement valuation of frozen cohorts, without operational DB writes.

Fractional quantities and gross receivables are research marks, not executable cash.
Ordinary dividends and subscription-right proceeds are outside this estimand.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

from stocks_predictor.discovery_h17 import adjustment_map, digest, identity_at, read_json
from stocks_predictor.discovery_value import group_events, load_market, period_statistics, summarize
from stocks_predictor.discovery_value_repair import score as price_score

PROTOCOL_ID = "H18-H19-REORGANIZATION-DIAGNOSTIC-1"
PROTOCOL_SHA256 = "c714aee9fde793fd1e612426782dac61abe5f6231c6a0d2429e115618622a2f4"


def validate_terms(terms):
    keys = set()
    for event in terms["events"]:
        key = event["ticker"], event["isin"], event["ex_date"]
        if key in keys or not event["last_cum"] < event["ex_date"]:
            raise ValueError("duplicate event or invalid entitlement dates")
        keys.add(key)
        if not event["sources"] or not (event["stocks"] or event["cash"]):
            raise ValueError("event lacks evidence or consideration")
        if any(not s.get("sha256") or not s.get("url") for s in event["sources"]):
            raise ValueError("source provenance missing")
        for stock in event["stocks"]:
            if not math.isfinite(stock["ratio"]) or stock["ratio"] <= 0 or not stock["isin"]:
                raise ValueError("invalid successor ratio or identity")
            if stock["credit_date"] is not None and stock["credit_date"] < event["last_cum"]:
                raise ValueError("credit precedes entitlement")
        for cash in event["cash"]:
            if (not math.isfinite(cash["amount_brl"]) or cash["amount_brl"] < 0
                    or cash["payment_date"] < event["last_cum"]):
                raise ValueError("invalid cash consideration")


def score(member, entry, exit_day, bars, identities, events, legacy, reviews, terms):
    """Value one requested stock allocation, keeping unresolved cells and evidence.

    Follow only verified compulsory consideration. A failed entry receives neither
    successor stock nor cash entitlements. A future payment is never spendable cash.
    """
    if not entry < exit_day:
        raise ValueError("invalid holding interval")
    ticker, isin = member["ticker"], member["isin"]
    reorganizations = terms["events"]
    subscriptions = {(r["ticker"], r["isin"], r["ex_date"]) for r in terms["subscriptions"]}
    actions = [r for r in reorganizations if (r["ticker"], r["isin"]) == (ticker, isin)]
    ceased = [r for r in actions if r["removes_original"] and r["ex_date"] <= entry]
    if ceased and entry not in bars.get(ticker, {}):
        return {"diagnostic_return": 0.0, "quality_reasons": [],
                "quality_notes": [{"code": "CONFIRMED_CEASED_INSTRUMENT_ORDER_REMAINS_CASH",
                                   "event_date": max(r["ex_date"] for r in ceased)}],
                "entitlement_ledger": [], "mark": {"uninvested_fraction": 1.0}}
    relevant = any(entry < r["ex_date"] <= exit_day for r in actions)
    relevant |= any(t == ticker and i == isin and entry < day <= exit_day for t, i, day in subscriptions)
    if not relevant:
        original = price_score(member, entry, exit_day, bars, identities, events[ticker], legacy[ticker], reviews)
        value = original.pop("price_return")
        return {"diagnostic_return": value, **original, "entitlement_ledger": []}

    reasons, notes, ledger, stock_marks, cash_marks = [], [], [], [], []

    def segment(symbol, identity, start, end, quantity, end_close=False):
        quotes = bars.get(symbol, {})
        if start not in quotes or end not in quotes:
            reasons.append("MISSING_EXECUTION_ENDPOINT:"+symbol)
        check_days = [start, end] + [r["first_date"] for r in identities.get(symbol, [])
                                    if start < r["first_date"] < end]
        if any(identity_at(identities, symbol, day) != identity for day in check_days):
            reasons.append("INSTRUMENT_IDENTITY_BREAK_OR_MISSING:"+symbol)
        factors, conflicts = adjustment_map(events[symbol], legacy[symbol])
        for day, errors in conflicts.items():
            if start < day <= end:
                reasons.extend(errors)
        for event in events[symbol]:
            if not start < event["ex_date"] <= end or event["price_factor"] is not None:
                continue
            if event["label"] == "SUBSCRICAO" and (symbol, identity, event["ex_date"]) in subscriptions:
                notes.append({"code": "RIGHTS_ZERO_MARK_NO_EXERCISE_NO_SALE", "ticker": symbol,
                              "ex_date": event["ex_date"], "economic_rights_value_unknown": True})
            else:
                reasons.append("UNMODELLED_"+event["label"].replace(" ", "_"))
        days = sorted(d for d in quotes if start <= d <= end)
        for previous, day in zip(days, days[1:]):
            factor = math.prod(v for d, v in factors.items() if previous < d <= day)
            gap = quotes[day][0]/(quotes[previous][1]*factor)-1
            if abs(gap) <= 0.30:
                continue
            review = reviews.get((symbol, day))
            if (review and review["previous_date"] == previous and review["isin"] == identity
                    and review["previous_close"] == quotes[previous][1] and review["next_open"] == quotes[day][0]
                    and review["price_factor"] == factor):
                notes.append({"code": "PRIMARY_QUOTE_CONFIRMED_LARGE_MOVE", "ticker": symbol, "date": day})
            else:
                reasons.append("UNRESOLVED_OVERNIGHT_GT_30PCT:"+symbol)
        final_qty = quantity/math.prod(v for d, v in factors.items() if start < d <= end)
        value = final_qty*quotes[end][int(end_close)] if end in quotes else None
        return final_qty, value

    def follow(symbol, identity, start, end, quantity, credit_date, depth=0):
        if depth > 20:
            raise ValueError("cyclic or excessive reorganization chain")
        changes = sorted((r for r in reorganizations if (r["ticker"], r["isin"]) == (symbol, identity)
                          and start < r["ex_date"] <= end), key=lambda r: r["ex_date"])
        if not changes:
            final_qty, value = segment(symbol, identity, start, end, quantity)
            stock_marks.append({"ticker": symbol, "isin": identity, "quantity": final_qty,
                                "mark_date": end, "opening_value_brl": value, "credit_date": credit_date,
                                "physical_credit_verified_before_exit": credit_date is not None and credit_date < end})
            return
        event = changes[0]
        if event["last_cum"] < start:
            reasons.append("ENTITLEMENT_DATE_BEFORE_ACQUISITION")
            return
        at_event, before = segment(symbol, identity, start, event["last_cum"], quantity, end_close=True)
        # A known conversion may not suppress unrelated same-day actions or conflicts.
        for row in events[symbol]:
            if row["ex_date"] == event["ex_date"] and row["label"] not in event["covered_panel_labels"]:
                reasons.append("UNRESOLVED_SIMULTANEOUS_REORGANIZATION_ACTION")
        if any(row["ex_date"] == event["ex_date"] and row["approved_by"] for row in legacy[symbol]):
            reasons.append("UNRESOLVED_LEGACY_ADJUSTMENT_AT_CONVERSION")
        boundary = sum(c["amount_brl"]*at_event for c in event["cash"])
        complete_boundary = True
        for stock in event["stocks"]:
            quote = bars.get(stock["ticker"], {}).get(event["ex_date"])
            if quote is None or identity_at(identities, stock["ticker"], event["ex_date"]) != stock["isin"]:
                complete_boundary = False
                reasons.append("MISSING_OR_WRONG_SUCCESSOR_AT_CONVERSION:"+stock["ticker"])
            else:
                boundary += at_event*stock["ratio"]*quote[0]
        if before and complete_boundary and abs(boundary/before-1) > 0.30:
            reasons.append("UNRESOLVED_REORGANIZATION_BASKET_JUMP_GT_30PCT")
        ledger.append({"ticker": symbol, "isin": identity, "ex_date": event["ex_date"],
                       "quantity_before": at_event, "stock_entitlements": event["stocks"],
                       "gross_cash_entitlements": event["cash"], "source_names": event["source_names"]})
        for cash in event["cash"]:
            cash_marks.append({**cash, "ticker": symbol, "total_brl": at_event*cash["amount_brl"],
                               "status_at_exit_open": "PAYMENT_SCHEDULE_PRECEDES_EXIT" if cash["payment_date"] < end
                               else "UNPAID_RECEIVABLE_AT_EXIT_OPEN"})
        for stock in event["stocks"]:
            stock_credit = (credit_date if not event["removes_original"] and
                            (stock["ticker"], stock["isin"]) == (symbol, identity) else stock["credit_date"])
            follow(stock["ticker"], stock["isin"], event["ex_date"], end,
                   at_event*stock["ratio"], stock_credit, depth+1)

    follow(ticker, isin, entry, exit_day, 1.0, entry)
    initial = bars.get(ticker, {}).get(entry)
    if initial is None:
        reasons.append("MISSING_EXECUTION_ENDPOINT:"+ticker)
    if reasons or initial is None:
        value = None
    else:
        terminal = sum(s["opening_value_brl"] for s in stock_marks) + sum(c["total_brl"] for c in cash_marks)
        value = terminal/initial[0]-1
        if not math.isfinite(value) or value < -1:
            raise ValueError("invalid entitlement return")
    return {"diagnostic_return": value, "quality_reasons": sorted(set(reasons)), "quality_notes": notes,
            "entitlement_ledger": ledger, "mark": {"stocks": stock_marks, "gross_cash": cash_marks,
            "receivables_are_not_spendable": True, "fractional_units_are_theoretical": True}}


def merged_market(db, identity_dir, successor_db, successor_identity_dir):
    _, bars, identities = load_market(db, identity_dir)
    _, more, more_identities = load_market(successor_db, successor_identity_dir)
    for ticker, quotes in more.items():
        for day, values in quotes.items():
            if day in bars[ticker] and bars[ticker][day] != values:
                raise ValueError("successor extract changes existing price")
            bars[ticker][day] = values
    for ticker, blocks in more_identities.items():
        for block in blocks:
            if block not in identities[ticker]:
                identities[ticker].append(block)
    return bars, identities


def run(first_path, db, identity_dir, successor_db, successor_identity_dir, panel_path,
        reviews_path, terms_path, protocol_path, output):
    output = Path(output)
    if output.exists():
        raise FileExistsError("Observations are append-only")
    protocol = read_json(protocol_path)
    canonical = json.dumps(protocol, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    if protocol["protocol_id"] != PROTOCOL_ID or hashlib.sha256(canonical).hexdigest() != PROTOCOL_SHA256:
        raise ValueError("unsupported reorganization registration")
    paths = [Path(p) for p in (first_path, db, successor_db, panel_path, reviews_path, terms_path, protocol_path, __file__)]
    paths += [Path(__file__).with_name(n) for n in ("discovery_h17.py", "discovery_value.py", "discovery_value_repair.py")]
    paths += sorted(Path(identity_dir).glob("identity-*.jsonl")) + sorted(Path(successor_identity_dir).glob("identity-*.jsonl"))
    source_root = Path(terms_path).parent
    paths += [source_root/name for name in protocol["primary_source_sha256"]]
    hashes = {str(p.resolve()): digest(p) for p in paths}
    expected_inputs = {"first": first_path, "db": db, "successor_db": successor_db,
                       "events": panel_path, "reviews": reviews_path, "terms": terms_path}
    if any(digest(expected_inputs[key]) != value for key, value in protocol["input_sha256"].items()):
        raise ValueError("measurement dataset differs from registration")
    for directory, key in ((identity_dir, "identities"), (successor_identity_dir, "successor_identities")):
        actual = {p.name: digest(p) for p in sorted(Path(directory).glob("identity-*.jsonl"))}
        if actual != protocol[key]:
            raise ValueError("historical identities differ from registration")
    if any(digest(source_root/name) != sha for name, sha in protocol["primary_source_sha256"].items()):
        raise ValueError("primary event source differs from registration")
    first, terms = read_json(first_path), read_json(terms_path)
    validate_terms(terms)
    bars, identities = merged_market(db, identity_dir, successor_db, successor_identity_dir)
    events, legacy = group_events(read_json(panel_path))
    reviews = {(r["ticker"], r["date"]): r for r in read_json(reviews_path)}
    trials, differences = [], []
    for trial in first["trials"]:
        periods = []
        for period in trial["periods"]:
            if not period["members"]:
                periods.append(period)
                continue
            members = []
            for old in period["members"]:
                outcome = score(old, period["entry"], period["exit"], bars, identities, events, legacy, reviews, terms)
                members.append({**old, **outcome, "price_return": outcome["diagnostic_return"]})
                if outcome["diagnostic_return"] != old["price_return"]:
                    differences.append({"family": trial["family"], "holding_months": trial["holding_months"],
                                        "asof": period["asof"], "ticker": old["ticker"], "selected": old["selected"],
                                        "old_return": old["price_return"], "new_return": outcome["diagnostic_return"],
                                        "old_reasons": old["quality_reasons"], "new_reasons": outcome["quality_reasons"]})
            stats = period_statistics(members, trial["holding_months"])
            periods.append({**period, "members": members, **stats,
                            "status": "COMPLETE_DIAGNOSTIC_MEASUREMENT" if stats["complete"] else "INCOMPLETE_DIAGNOSTIC_MEASUREMENT"})
        summary = summarize(periods, trial["holding_months"])
        for period in periods:
            for member in period["members"]:
                member.pop("price_return")
        trials.append({"family": trial["family"], "holding_months": trial["holding_months"], "summary": summary, "periods": periods})
    result = {"protocol_id": PROTOCOL_ID, "observed_at_utc": datetime.now(timezone.utc).isoformat(),
              "mode": "FROZEN_COHORT_PRICE_PLUS_REORGANIZATION_ENTITLEMENTS_NOT_TOTAL_RETURN_OR_EXECUTABLE_PROFIT",
              "input_sha256": hashes, "protocol": protocol, "trials": trials, "changed_returns": differences,
              "unchanged_selection_and_factor_values": True}
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError("input changed during observation")
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
    return [{"family": t["family"], "holding_months": t["holding_months"], **t["summary"]} for t in trials]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("first", "db", "identity-dir", "successor-db", "successor-identity-dir", "events", "reviews", "terms", "protocol", "output"):
        parser.add_argument("--"+key, required=True, type=Path)
    a = parser.parse_args()
    print(json.dumps(run(a.first, a.db, a.identity_dir, a.successor_db, a.successor_identity_dir,
                         a.events, a.reviews, a.terms, a.protocol, a.output), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
