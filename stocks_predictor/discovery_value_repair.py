"""Remeasure frozen H18/H19 cohorts after explicitly registered source repairs."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

from stocks_predictor.discovery_h17 import adjustment_map, digest, identity_at, read_json
from stocks_predictor.discovery_value import group_events, load_market, period_statistics, summarize

PROTOCOL_ID = "H18-H19-MEASUREMENT-REPAIR-1"
PROTOCOL_SHA256 = "1f4ad50cd682f4611f16676f64cf56de1c37a5eeab9704b8f7257fc816c1ab0f"


def score(member, entry, exit_day, bars, identities, events, legacy, reviewed_moves):
    ticker = member["ticker"]
    quotes = bars.get(ticker, {})
    reasons, notes = [], []
    if entry not in quotes or exit_day not in quotes:
        reasons.append("MISSING_EXECUTION_ENDPOINT")
    check_days = [entry, exit_day] + [r["first_date"] for r in identities.get(ticker, [])
                                    if entry < r["first_date"] < exit_day]
    if any(identity_at(identities, ticker, d) != member["isin"] for d in check_days):
        reasons.append("INSTRUMENT_IDENTITY_BREAK_OR_MISSING")
    factors, conflicts = adjustment_map(events, legacy)
    for day, errors in conflicts.items():
        if entry < day <= exit_day:
            reasons.extend(errors)
    for event in events:
        if entry < event["ex_date"] <= exit_day and event["price_factor"] is None:
            reasons.append("UNMODELLED_"+event["label"].replace(" ", "_"))
    period = sorted(d for d in quotes if entry <= d <= exit_day)
    for previous, day in zip(period, period[1:]):
        factor = math.prod(v for d, v in factors.items() if previous < d <= day)
        gap = quotes[day][0]/(quotes[previous][1]*factor)-1
        if abs(gap) <= 0.30:
            continue
        review = reviewed_moves.get((ticker, day))
        if (review and review["previous_date"] == previous and review["isin"] == member["isin"]
                and review["previous_close"] == quotes[previous][1] and review["next_open"] == quotes[day][0]
                and review["price_factor"] == factor):
            notes.append({"code": "PRIMARY_QUOTE_CONFIRMED_LARGE_MOVE", "date": day, "overnight_return": gap})
        else:
            reasons.append("UNRESOLVED_OVERNIGHT_GT_30PCT")
    if reasons:
        return {"price_return": None, "quality_reasons": sorted(set(reasons)), "quality_notes": notes}
    factor = math.prod(v for d, v in factors.items() if entry < d <= exit_day)
    result = quotes[exit_day][0]/(quotes[entry][0]*factor)-1
    if not math.isfinite(result) or result <= -1:
        raise ValueError("invalid remeasured return")
    return {"price_return": result, "quality_reasons": [], "quality_notes": notes}


def run(first_path, db, identity_dir, panel_path, reviews_path, protocol_path, output):
    output = Path(output)
    if output.exists():
        raise FileExistsError("Observations are append-only")
    protocol = read_json(protocol_path)
    canonical = json.dumps(protocol, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    if protocol["protocol_id"] != PROTOCOL_ID or hashlib.sha256(canonical).hexdigest() != PROTOCOL_SHA256:
        raise ValueError("unsupported measurement-repair registration")
    paths = [Path(p) for p in (first_path, db, panel_path, reviews_path, protocol_path, __file__)]
    paths += [Path(__file__).with_name(name) for name in ("discovery_h17.py", "discovery_value.py")]
    paths += sorted(Path(identity_dir).glob("identity-*.jsonl"))
    hashes = {str(p.resolve()): digest(p) for p in paths}
    actual = {p.name: hashes[str(p.resolve())] for p in paths}
    if any(actual.get(Path(p).name) != sha for p, sha in protocol["input_sha256"].items()):
        raise ValueError("measurement dataset differs from registration")
    first = read_json(first_path)
    _, bars, identities = load_market(db, identity_dir)
    events, legacy = group_events(read_json(panel_path))
    reviews = {(r["ticker"], r["date"]): r for r in read_json(reviews_path)}
    trials, differences = [], []
    for trial in first["trials"]:
        horizon = trial["holding_months"]
        periods = []
        for period in trial["periods"]:
            if not period["members"]:
                periods.append(period)
                continue
            members = []
            for old in period["members"]:
                outcome = score(old, period["entry"], period["exit"], bars, identities,
                                events[old["ticker"]], legacy[old["ticker"]], reviews)
                members.append({**old, **outcome})
                if outcome["price_return"] != old["price_return"]:
                    differences.append({"family": trial["family"], "holding_months": horizon, "asof": period["asof"],
                                        "ticker": old["ticker"], "selected": old["selected"], "old_return": old["price_return"],
                                        "new_return": outcome["price_return"], "old_reasons": old["quality_reasons"],
                                        "new_reasons": outcome["quality_reasons"]})
            stats = period_statistics(members, horizon)
            periods.append({**period, "members": members, **stats,
                            "status": "COMPLETE_PRICE_MEASUREMENT" if stats["complete"] else "INCOMPLETE_PRICE_MEASUREMENT"})
        trials.append({"family": trial["family"], "holding_months": horizon,
                       "summary": summarize(periods, horizon), "periods": periods})
    result = {"protocol_id": PROTOCOL_ID, "observed_at_utc": datetime.now(timezone.utc).isoformat(),
              "mode": "FROZEN_COHORT_PRICE_REMEASUREMENT_NOT_EXECUTABLE_BACKTEST", "input_sha256": hashes,
              "protocol": protocol, "features": first["features"], "feature_coverage": first["feature_coverage"],
              "trials": trials, "changed_returns": differences,
              "unchanged_selection_and_factor_values": True}
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError("input changed during observation")
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
    return [{"family": t["family"], "holding_months": t["holding_months"], **t["summary"]} for t in trials]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("first", "db", "identity-dir", "events", "reviews", "protocol", "output"):
        parser.add_argument("--"+key, required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.first, args.db, args.identity_dir, args.events, args.reviews,
                         args.protocol, args.output), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
