"""Explicit, read-only H17 price diagnostic. This is not a trading backtest.

All members and outcome-quality exclusions are retained. Available-case results
cannot certify an investable strategy or replace the frozen proof runners.
"""

import argparse
from bisect import bisect_right
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import statistics


PROTOCOL_ID = "H17-DISCOVERY-PRICE-DIAGNOSTIC-1"
PROTOCOL_SHA256 = "a35f166a0a9ae8d38e6fe13b21ac77e63629673ae66a20f8820123c062c9072b"


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def ranks(values):
    result = [0.0] * len(values)
    ordered = sorted(range(len(values)), key=lambda i: values[i])
    i = 0
    while i < len(ordered):
        j = i + 1
        while j < len(ordered) and values[ordered[j]] == values[ordered[i]]:
            j += 1
        for index in ordered[i:j]:
            result[index] = (i + j - 1) / 2 + 1
        i = j
    return result


def spearman(xs, ys):
    if len(xs) != len(ys):
        raise ValueError("correlation length mismatch")
    if len(xs) < 3 or len(set(xs)) < 2 or len(set(ys)) < 2:
        return None
    return statistics.correlation(ranks(xs), ranks(ys))


def identity_at(identities, ticker, day):
    matches = {r["isin"] for r in identities.get(ticker, [])
               if r["first_date"] <= day <= r["last_date"]}
    return next(iter(matches)) if len(matches) == 1 else None


def adjustment_map(events, legacy):
    """Compose separate same-day actions; cross-check rather than double apply."""
    factors, reasons = defaultdict(lambda: 1.0), defaultdict(list)
    by_type = defaultdict(lambda: 1.0)
    for row in events:
        if row["price_factor"] is None:
            continue
        value = row["price_factor"]
        if not math.isfinite(value) or value <= 0:
            raise ValueError("invalid corporate action factor")
        key = row["ex_date"], row["label"]
        by_type[key] *= value
        factors[row["ex_date"]] *= value
    for row in legacy:
        if not row["approved_by"]:
            continue
        label = {"split": "DESDOBRAMENTO", "grupamento": "GRUPAMENTO"}.get(row["type"])
        if label is None:
            continue
        key = row["ex_date"], label
        if key in by_type:
            # Legacy records can describe the net share-base change, while B3
            # lists component actions (VIVT: +7900% then grouping 0.025).
            # The B3 factor already applied above remains authoritative here.
            matches_component = math.isclose(row["factor"], by_type[key], rel_tol=1e-4)
            matches_net = math.isclose(row["factor"], factors[row["ex_date"]], rel_tol=1e-4)
            if not (matches_component or matches_net):
                reasons[row["ex_date"]].append("CONFLICTING_CORPORATE_ACTION_FACTORS")
        else:
            if not math.isfinite(row["factor"]) or row["factor"] <= 0:
                raise ValueError("invalid legacy factor")
            factors[row["ex_date"]] *= row["factor"]
    return dict(factors), dict(reasons)


def score_outcome(member, entry, exit_day, bars, identities, events, legacy):
    """Keep an unscored cell on any unresolved measurement issue, never zero it."""
    ticker = member["ticker"]
    quotes = bars.get(ticker, {})
    reasons = []
    if entry not in quotes or exit_day not in quotes:
        reasons.append("MISSING_EXECUTION_ENDPOINT")
    identity_days = [entry, exit_day] + [
        r["first_date"] for r in identities.get(ticker, []) if entry < r["first_date"] < exit_day
    ]
    if any(identity_at(identities, ticker, d) != member["isin"] for d in identity_days):
        reasons.append("INSTRUMENT_IDENTITY_BREAK_OR_MISSING")
    factors, conflicts = adjustment_map(events, legacy)
    for day, errors in conflicts.items():
        if entry < day <= exit_day:
            reasons.extend(errors)
    unsupported = [r for r in events if entry < r["ex_date"] <= exit_day and r["price_factor"] is None]
    reasons.extend("UNMODELLED_" + r["label"].replace(" ", "_") for r in unsupported)
    period = sorted(d for d in quotes if entry <= d <= exit_day)
    for previous, day in zip(period, period[1:]):
        factor = math.prod(v for d, v in factors.items() if previous < d <= day)
        overnight = quotes[day][0] / (quotes[previous][1] * factor) - 1
        if abs(overnight) > 0.30:
            reasons.append("UNRESOLVED_OVERNIGHT_GT_30PCT")
    if reasons:
        return {"price_return": None, "quality_reasons": sorted(set(reasons))}
    factor = math.prod(v for d, v in factors.items() if entry < d <= exit_day)
    value = quotes[exit_day][0] / (quotes[entry][0] * factor) - 1
    if not math.isfinite(value) or value <= -1:
        raise ValueError("invalid price return")
    return {"price_return": value, "quality_reasons": []}


def build_cross_sections(snapshots, dates, bars, identities, panel):
    events, legacy = defaultdict(list), defaultdict(list)
    for row in panel["events"]:
        events[row["ticker"]].append(row)
    for row in panel["legacy_adjustments"]:
        legacy[row["ticker"]].append(row)
    for row in panel.get("secondary_action_audit", []):
        if row["status"] == "CROSSCHECK_CONFLICT":
            events[row["ticker"]].append({"ex_date": row["date"], "price_factor": None,
                                          "label": "CROSS_SOURCE_FACTOR_CONFLICT"})
    months = {d[:7]: d for d in dates}
    month_keys = sorted(months)
    results = []
    for snap in snapshots:
        asof = snap["asof"]
        candidates = []
        for member in snap["universe"]:
            filing = member.get("filing", {})
            if filing and (filing["available_at"] > asof or filing["ref_date"] > asof):
                raise ValueError("future financial filing")
            if filing and (filing["cnpj"] != member["cnpj"] or filing["accruals"] != member["accruals"]):
                raise ValueError("factor or issuer differs from source filing")
            for document in member.get("security_documents", []):
                if document["available_at"] > asof:
                    raise ValueError("future security filing")
            value = member["accruals"]
            if value is not None:
                if not math.isfinite(value):
                    raise ValueError("invalid accruals")
                candidates.append(member)
        candidates.sort(key=lambda m: (m["accruals"], m["ticker"]))
        record = {"asof": asof, "universe_names": len(snap["universe"]),
                  "factor_names": len(candidates), "missing_factor_names": len(snap["universe"])-len(candidates)}
        if len(candidates) < 20:
            results.append({**record, "status": "INSUFFICIENT_PIT_FACTOR_COVERAGE", "members": []})
            continue
        next_month = month_keys[bisect_right(month_keys, asof[:7])]
        entry = dates[bisect_right(dates, asof)]
        exit_day = dates[bisect_right(dates, months[next_month])]
        if not asof < entry < exit_day:
            raise ValueError("noncausal execution dates")
        n_selected = len(candidates) // 5
        members = []
        for i, member in enumerate(candidates):
            outcome = score_outcome(member, entry, exit_day, bars, identities,
                                    events[member["ticker"]], legacy[member["ticker"]])
            members.append({"ticker": member["ticker"], "cnpj": member["cnpj"],
                            "isin": member["isin"], "accruals": member["accruals"],
                            "selected": i < n_selected, **outcome})
        scored = [r for r in members if r["price_return"] is not None]
        complete = len(scored) == len(members)
        ic = spearman([-r["accruals"] for r in scored], [r["price_return"] for r in scored])
        selected_mean = statistics.mean(r["price_return"] for r in members if r["selected"]) if complete else None
        benchmark_mean = statistics.mean(r["price_return"] for r in members) if complete else None
        results.append({**record, "entry": entry, "exit": exit_day, "selected_names": n_selected,
                        "status": "COMPLETE_PRICE_MEASUREMENT" if complete else "INCOMPLETE_PRICE_MEASUREMENT",
                        "scored_names": len(scored), "available_case_ic": ic,
                        "complete_case_quintile_price_return": selected_mean,
                        "complete_case_universe_price_return": benchmark_mean,
                        "complete_case_price_spread": selected_mean-benchmark_mean if complete else None,
                        "members": members})
    return results


def summarize(cross_sections):
    def subset_stats(rows):
        eligible = [r for r in rows if r["members"]]
        ic = [r["available_case_ic"] for r in eligible if r["available_case_ic"] is not None]
        complete = [r for r in eligible if r["status"] == "COMPLETE_PRICE_MEASUREMENT"]
        selected = [r["complete_case_quintile_price_return"] for r in complete]
        spreads = [r["complete_case_price_spread"] for r in complete]
        members = [m for r in eligible for m in r["members"]]
        scored = [m for m in members if m["price_return"] is not None]
        missing = [m for m in members if m["price_return"] is None]
        return {"scheduled_months": len(rows), "eligible_months": len(eligible),
                "complete_months": len(complete), "factor_cells": len(members), "scored_cells": len(scored),
                "coverage": len(scored)/len(members) if members else None,
                "unscored_selected_cells": sum(m["selected"] for m in missing),
                "unscored_other_cells": sum(not m["selected"] for m in missing),
                "available_case_mean_ic": statistics.mean(ic) if ic else None,
                "complete_case_mean_monthly_spread": statistics.mean(spreads) if spreads else None,
                "complete_case_mean_monthly_quintile_price_return": statistics.mean(selected) if selected else None,
                "diagnostic_36bp_haircut": statistics.mean(selected)-0.0036 if selected else None,
                "diagnostic_72bp_haircut": statistics.mean(selected)-0.0072 if selected else None,
                "missing_reasons": dict(Counter(reason for m in missing for reason in m["quality_reasons"]))}
    overall = subset_stats(cross_sections)
    halves = {"2018_2021": subset_stats([r for r in cross_sections if r["asof"] < "2022-01-01"]),
              "2022_2025": subset_stats([r for r in cross_sections if r["asof"] >= "2022-01-01"])}
    if overall["complete_months"] != overall["eligible_months"]:
        status = "INCONCLUSIVE_DATA_QUALITY"
    else:
        values = [h[k] for h in halves.values()
                  for k in ("available_case_mean_ic", "complete_case_mean_monthly_spread")]
        if any(v is None for v in values):
            status = "INCONCLUSIVE_SIGNAL"
        elif all(v <= 0 for v in values):
            status = "REJECT_PRICE_SCREEN"
        elif all(v > 0 for v in values):
            status = "PROMISING_PRICE_SCREEN"
        else:
            status = "INCONCLUSIVE_SIGNAL"
    return {"status": status, "overall": overall, "fixed_halves": halves,
            "investable_alpha_claim": False, "executable_profit_estimate": None}


def run(db, snapshots_path, panel_path, identity_dir, protocol_path, output):
    """Write one new immutable observation, without importing operational DB code."""
    output = Path(output)
    if output.exists():
        raise FileExistsError("Choose a new observation path; results are append-only")
    protocol = read_json(protocol_path)
    canonical = json.dumps(protocol, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    if protocol["protocol_id"] != PROTOCOL_ID or hashlib.sha256(canonical).hexdigest() != PROTOCOL_SHA256:
        raise ValueError("unsupported preregistration")
    sources = [Path(db), Path(snapshots_path), Path(panel_path), Path(protocol_path), Path(__file__)]
    identity_files = sorted(Path(identity_dir).glob("identity-*.jsonl"))
    if not identity_files:
        raise ValueError("missing raw COTAHIST identity extract")
    hashes = {str(p.resolve()): digest(p) for p in sources + identity_files}
    snapshots = read_json(snapshots_path)
    expected_months = [f"{y}-{m:02}" for y in range(2018, 2026) for m in range(1, 13)]
    if [s["asof"][:7] for s in snapshots] != expected_months:
        raise ValueError("snapshot window differs from preregistration")
    for snapshot in snapshots:
        members = snapshot["universe"]
        if len(members) > 60 or len({m["cnpj"] for m in members}) != len(members):
            raise ValueError("universe size or issuer deduplication differs from preregistration")
        for member in members:
            if not member.get("security_documents") or (member["accruals"] is not None and not member.get("filing")):
                raise ValueError("missing contemporaneous document provenance")
    identities = defaultdict(list)
    for path in identity_files:
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            identities[row["ticker"]].append(row)
    needed = {m["ticker"] for s in snapshots for m in s["universe"]}
    bars = defaultdict(dict)
    with sqlite3.connect(Path(db).resolve().as_uri()+"?mode=ro", uri=True) as conn:
        dates = [r[0] for r in conn.execute("SELECT DISTINCT date FROM prices_raw ORDER BY date")]
        for ticker, day, opening, closing, scale in conn.execute(
            "SELECT ticker,date,open,close,quote_factor FROM prices_raw WHERE market_type='010'"
        ):
            if ticker not in needed:
                continue
            if scale is None or not math.isfinite(scale) or scale <= 0:
                raise ValueError("invalid quote factor")
            value = opening/scale, closing/scale
            if any(not math.isfinite(v) or v <= 0 for v in value):
                raise ValueError("invalid normalized prices")
            if day in bars[ticker] and bars[ticker][day] != value:
                raise ValueError("conflicting normalized quotes")
            bars[ticker][day] = value
    cross_sections = build_cross_sections(snapshots, dates, bars, identities, read_json(panel_path))
    result = {"protocol_id": PROTOCOL_ID, "observed_at_utc": datetime.now(timezone.utc).isoformat(),
              "mode": "DISCOVERY_PRICE_DIAGNOSTIC_NOT_EXECUTABLE_BACKTEST", "input_sha256": hashes,
              "protocol": protocol, "summary": summarize(cross_sections), "cross_sections": cross_sections}
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError("input changed during observation")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
    return result["summary"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ("db", "snapshots", "events", "identity-dir", "protocol", "output"):
        parser.add_argument("--"+argument, required=True, type=Path)
    args = parser.parse_args()
    summary = run(args.db, args.snapshots, args.events, args.identity_dir, args.protocol, args.output)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
