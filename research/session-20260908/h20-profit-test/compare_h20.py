"""Frozen H20 mark comparison. Research only: never produces net profit."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import statistics

from stocks_predictor.profit_validation import compound_path

PROTOCOL_SHA256 = "a914124230bea0e416542e90279d86a24997f475b1da5ebc98bfa718850e5c98"
ARMS = ("VALUE_COMMON_UNIVERSE", "VALUE_PROFITABILITY", "VALUE_PROFITABILITY_BUFFER")
GROUPS = (*ARMS, "COMMON_EQUAL_WEIGHT", "H19_ORIGINAL")
PAIRS = [(ARMS[1], ARMS[0]), (ARMS[2], ARMS[0]), (ARMS[2], ARMS[1])]
PAIRS += [(a, b) for a in ARMS for b in GROUPS[3:]]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def unique(rows, field):
    result = {r[field]: r for r in rows}
    if len(result) != len(rows):
        raise ValueError("duplicate " + field)
    return result


def adjusted(value, cost):
    if not math.isfinite(value) or value < -1 or not 0 <= cost < 1:
        raise ValueError("invalid mark or assumed cost")
    return (1 + value) * (1 - cost) / (1 + cost) - 1


def join_period(signal, marks, original):
    """A missing/failed common name blocks every paired selection, without imputation."""
    row = {"asof": signal["asof"], "entry": None, "exit": None, "eligible_signal": True,
           "status": "BLOCKED", "reasons": [], "returns": {}, "groups": {}, "cells": []}
    if not all(signal["arms"][a]["selection_available"] for a in ARMS):
        row["eligible_signal"] = False
        row["reasons"] = ["INSUFFICIENT_FEATURE_COVERAGE"]
        return row
    if marks is None or original is None:
        row["reasons"] = ["MISSING_AUDITED_PERIOD"]
        return row
    if (marks["asof"] != signal["asof"] or original["asof"] != signal["asof"]
            or (marks["entry"], marks["exit"]) != (original["entry"], original["exit"])
            or not signal["asof"] < marks["entry"] < marks["exit"]):
        raise ValueError("noncausal or mismatched interval")
    row.update(entry=marks["entry"], exit=marks["exit"])
    ranked = [unique(signal["arms"][a]["ranking"], "ticker") for a in ARMS]
    identities = [{t: (r["cnpj"], r["isin"]) for t, r in group.items()} for group in ranked]
    if not identities[0] == identities[1] == identities[2]:
        raise ValueError("asymmetric common universe")
    source = unique(marks["members"], "ticker")
    original_names = unique(original["members"], "ticker")
    for a in ARMS:
        selected = unique(signal["arms"][a]["members"], "ticker")
        if not selected or any(t not in ranked[0] or r["isin"] != ranked[0][t]["isin"]
                               or r["cnpj"] != ranked[0][t]["cnpj"] for t, r in selected.items()):
            raise ValueError("selection differs from archived common identities")
        row["groups"][a] = list(selected)
    row["groups"]["COMMON_EQUAL_WEIGHT"] = list(ranked[0])
    row["groups"]["H19_ORIGINAL"] = [r["ticker"] for r in original["members"] if r["selected"]]
    required = set(ranked[0]) | set(row["groups"]["H19_ORIGINAL"])
    usable, failures = {}, {}
    for ticker in sorted(required):
        m, old = source.get(ticker), original_names.get(ticker)
        reason = None
        if m is None or old is None:
            reason = "MISSING_NAME"
        elif m["cnpj"] != old["cnpj"] or m["selected"] != old["selected"]:
            reason = "AUDIT_IDENTITY_OR_SELECTION_MISMATCH"
        elif ticker in ranked[0] and (old["cnpj"], old["isin"]) != identities[0][ticker]:
            reason = "SIGNAL_IDENTITY_MISMATCH"
        elif m["failed_entry"]:
            reason = "FAILED_ENTRY_NOT_ZERO"
        elif not isinstance(m["return"], (int, float)) or not math.isfinite(m["return"]) or m["return"] < -1:
            reason = "INVALID_OR_MISSING_RETURN"
        if reason:
            failures[ticker] = reason
        else:
            usable[ticker] = m["return"]
        row["cells"].append({"ticker": ticker, "isin": old["isin"] if old else None,
                             "mark_return": None if reason else m["return"], "reason": reason})
    common_failures = {t: r for t, r in failures.items() if t in ranked[0]}
    if common_failures:
        row["reasons"] = [{"ticker": t, "reason": r} for t, r in sorted(common_failures.items())]
        return row
    for group, names in row["groups"].items():
        row["returns"][group] = (statistics.mean(usable[t] for t in names)
                                  if names and all(t in usable for t in names) else None)
    row["contextual_reference_failures"] = failures
    row["status"] = "COMPLETE_MARK_DIAGNOSTIC_NOT_NET_PROFIT"
    return row


def summarize(periods, group, cost, capital):
    expected = [p for p in periods if p["eligible_signal"]]
    available = [p for p in expected if p["returns"].get(group) is not None]
    values = [adjusted(p["returns"][group], cost) for p in available]
    complete = (len(available) == len(expected) and bool(available)
                and all(a["exit"] == b["entry"] for a, b in zip(available, available[1:])))
    path = compound_path(values, available[0]["entry"], available[-1]["exit"]) if complete else None
    by_year = {}
    for year in sorted({p["asof"][:4] for p in expected}):
        subset = [p for p in available if p["asof"][:4] == year]
        by_year[year] = {"available_periods": len(subset), "expected_periods": sum(p["asof"][:4] == year for p in expected),
                         "mean_quarter_mark": statistics.mean(adjusted(p["returns"][group], cost) for p in subset) if subset else None}
    return {"available_periods": len(values), "expected_periods": len(expected),
            "conditional_on_available_periods": not complete,
            "mean_quarter_mark_after_assumed_cost": statistics.mean(values) if values else None,
            "positive_quarters": sum(v > 0 for v in values), "synthetic_path": path,
            "synthetic_terminal_brl_not_profit": {str(c): c * path["terminal_multiple"] for c in capital} if path else None,
            "calendar_signal_years": by_year, "profit": None, "future_profit_projection": None}


def compare(periods, lhs, rhs, bootstrap):
    expected = [p for p in periods if p["eligible_signal"]]
    paired = [p for p in expected if p["returns"].get(lhs) is not None and p["returns"].get(rhs) is not None]
    values = [p["returns"][lhs] - p["returns"][rhs] for p in paired]
    # Calendar gaps are not compressed into artificial adjacent bootstrap periods.
    contiguous = (len(paired) == len(expected) and bool(paired)
                  and all(a["exit"] == b["entry"] for a, b in zip(paired, paired[1:])))
    interval = None
    if contiguous and len(values) >= 4:
        lo, hi, draws = bootstrap(values, statistics.mean, scheme="stationary", block_length=4,
                                  n_boot=10000, seed=20260908)
        if len(draws) != 10000:
            raise ValueError("unexpected discarded bootstrap draws")
        interval = [lo, hi]
    halves = []
    for dates in (expected[:15], expected[15:]):
        keep = {p["asof"] for p in dates}
        vals = [p["returns"][lhs] - p["returns"][rhs] for p in paired if p["asof"] in keep]
        halves.append({"expected_periods": len(dates), "available_periods": len(vals),
                       "mean_quarter_difference": statistics.mean(vals) if vals else None})
    return {"left": lhs, "right": rhs, "paired_periods": len(values), "expected_periods": len(expected),
            "mean_quarter_difference": statistics.mean(values) if values else None,
            "positive_difference_quarters": sum(v > 0 for v in values), "fixed_halves": halves,
            "descriptive_unadjusted_bootstrap_95pct": interval, "bootstrap_contiguous": contiguous}


def verify_sources(root, protocol_path):
    if digest(protocol_path) != PROTOCOL_SHA256:
        raise ValueError("frozen comparison protocol changed")
    protocol = read(protocol_path)
    paths = {}
    for key, spec in protocol["inputs"].items():
        path = (root / spec["path"]).resolve()
        if not path.is_relative_to(root.resolve()) or digest(path) != spec["sha256"]:
            raise ValueError("registered source changed: " + key)
        paths[key] = path
    manifest_path = paths["audited_package_manifest"]
    manifest = read(manifest_path)
    for name, expected in manifest["files"].items():
        path = (manifest_path.parent / name).resolve()
        if not path.is_relative_to(manifest_path.parent) or digest(path) != expected:
            raise ValueError("audited source package changed: " + name)
    return protocol, paths, len(manifest["files"])


def run(root, protocol_path, gate_path):
    protocol, paths, verified = verify_sources(root, protocol_path)
    h20, audit, original = (read(paths[k]) for k in ("h20_signals", "audited_marks", "identity_observation"))
    h19 = next(t for t in audit["trials"] if t["family"] == "H19" and t["holding_months"] == 3)
    originals = unique(next(t for t in original["trials"] if t["family"] == "H19" and t["holding_months"] == 3)["periods"], "asof")
    boot_path = paths["audited_package_manifest"].parent / "validator/bootstrap.py"
    spec = importlib.util.spec_from_file_location("frozen_h20_test_bootstrap", boot_path)
    boot = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(boot)
    results = {}
    for mode in protocol["price_modes"]:
        source_periods = unique(h19["modes"][mode]["periods"], "asof")
        periods = [join_period(p, source_periods.get(p["asof"]), originals.get(p["asof"])) for p in h20["periods"]]
        differences = [compare(periods, a, b, boot.bootstrap_ci) for a, b in PAIRS]
        scenarios = []
        for cost in protocol["one_way_cost_rates"]:
            scale = (1-cost)/(1+cost)
            comparisons = []
            for d in differences:
                comparisons.append({**d,
                    "mean_quarter_difference_after_assumed_cost": d["mean_quarter_difference"] * scale if d["mean_quarter_difference"] is not None else None,
                    "descriptive_bootstrap_95pct_after_assumed_cost": [v*scale for v in d["descriptive_unadjusted_bootstrap_95pct"]] if d["descriptive_unadjusted_bootstrap_95pct"] else None})
            scenarios.append({"one_way_assumed_cost": cost,
                "groups": {g: summarize(periods, g, cost, protocol["capital_brl"]) for g in GROUPS},
                "comparisons": comparisons})
        results[mode] = {"period_status_counts": dict(Counter(p["status"] for p in periods)),
                         "periods": periods, "scenarios": scenarios}
    gate = read(gate_path)
    evidence = read(root / "work/stocks-final-review-bundle/inputs/evidence.json")
    intervals = {a: [] for a in ARMS}
    for p in results["open"]["periods"]:
        if p["entry"]:
            ids = {m["ticker"]: m["isin"] for m in p["cells"]}
            for a in ARMS:
                intervals[a].extend([[t, ids[t], p["entry"], p["exit"]] for t in p["groups"][a]])
    # These are independent quarter requirements, not certification of longer buffered holdings.
    code_hash = digest(Path(__file__))
    return {"protocol": protocol, "protocol_sha256": PROTOCOL_SHA256,
        "measurement_code_sha256": code_hash, "run_id": PROTOCOL_SHA256[:12]+"-"+code_hash[:12],
        "audited_source_files_verified": verified, "bootstrap_source_sha256": digest(boot_path),
        "modes": results, "planned_quarter_holding_intervals": intervals,
        "available_cash_inventory_certificates": len(evidence["cash_coverage"]),
        "h19_gate": {k: gate[k] for k in ("status", "profit", "issue_counts", "validated_quote_records")},
        "h20_continuous_profit_certified": False, "profit": None, "future_profit_projection": None,
        "status": "HISTORICAL_MARK_COMPARISON_ONLY_NET_PROFIT_INCONCLUSIVE",
        "new_diagnostic_return_evaluations": 18, "configurations_minimum": 53, "return_evaluations_minimum": 55,
        "limitations": ["Ordinary dividends/JCP are omitted, not assumed zero in net-profit accounting.",
            "Corporate entitlements are marked at face value before verified delivery and taxes.",
            "Equal-weight synthetic full reinvestment and full-rotation cost scenario, no retail fills or maintenance.",
            "BUFFER is frozen planned membership; the 2.5% weight band and actual prior holdings are not executed.",
            "H19_ORIGINAL uses its original larger/different universe and is contextual, not a clean factor comparison.",
            "The same history was already repeatedly exposed. Bootstrap intervals are descriptive, not selection-adjusted Proof.",
            "No CAGR extrapolation is a future profit projection. Missing/failed names block the common comparison."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("root", "protocol", "gate", "output"):
        parser.add_argument("--"+name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("observations are append-only")
    result = run(args.root, args.protocol, args.gate)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "modes": {k: v["period_status_counts"] for k, v in result["modes"].items()},
                      "source_files": result["audited_source_files_verified"], "output_sha256": digest(args.output)}))


if __name__ == "__main__":
    main()
