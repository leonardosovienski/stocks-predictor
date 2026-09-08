"""Run the frozen H20 source/selection and entry-only diagnostics, offline.

Writes one new JSON observation; never opens a database or calculates returns.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from stocks_predictor.continuous_research import inspect_inputs, load_quotes, read
from stocks_predictor.value_profitability import ARMS, accounting_index, prepare_snapshot, rank_snapshot, select_members

PROTOCOL_SHA256 = "521a2cf4d3a5210df9e4c4f9336ec3a9e43b5d96ccb35427820fcf75b9a7e04e"
ENTRY_ADDENDUM_SHA256 = "717b84e606f11e91de63c83849e1ee9e38a8c7f700571a20207eafcc47e8d0d7"


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify_sources(protocol_path, features_path, accounting_path, source_dir, execution_dir):
    if sha256(protocol_path) != PROTOCOL_SHA256:
        raise ValueError("frozen H20 registration changed")
    spec = read(protocol_path)
    for key, path in (("features", features_path), ("accounting", accounting_path),
                      ("execution_manifest", execution_dir / "SHA256.json")):
        expected = spec["inputs"][key]
        if path.name != expected["filename"] or sha256(path) != expected["sha256"]:
            raise ValueError("registered input changed: " + key)
    accounting = read(accounting_path)
    archives = accounting["archive_sha256"]
    for filename, digest in archives.items():
        source = (source_dir / filename).resolve()
        if not source.is_relative_to(source_dir.resolve()) or sha256(source) != digest:
            raise ValueError("accounting raw archive mismatch: " + filename)
    for row in accounting["rows"]:
        sources = [*row["equity_sources"], *([row["earnings_source"]] if row["earnings_source"] else [])]
        if any(archives.get(s["archive"]) != s["archive_sha256"] for s in sources):
            raise ValueError("source row not bound to a verified accounting archive")
    return spec, read(features_path), accounting


def signal_diagnostics(features, accounting):
    indexed = accounting_index(accounting["rows"])
    dates = [s["asof"] for s in features]
    if dates != sorted(set(dates)):
        raise ValueError("unique chronological feature snapshots required")
    previous = {arm: {} for arm in ARMS}
    periods = []
    for snapshot in features:
        if snapshot["asof"][5:7] not in {"03", "06", "09", "12"}:
            continue
        prepared = prepare_snapshot(snapshot, indexed)
        period = {"asof": snapshot["asof"], "source_cells": len(prepared["members"]),
                  "eligible_names": sum(r["eligible"] for r in prepared["members"]),
                  "excluded": [r for r in prepared["members"] if not r["eligible"]], "arms": {}}
        for arm in ARMS:
            ranked = rank_snapshot(prepared, arm)
            prior = previous[arm]
            # This is explicitly a path of intended membership, never a holdings ledger.
            selection = select_members(ranked, prior, buffered=arm == ARMS[2])
            fresh = select_members(ranked, {}, buffered=arm == ARMS[2])
            current = {r["ticker"]: r["isin"] for r in selection["members"]}
            before = set(prior.items())
            after = set(current.items())
            period["arms"][arm] = {**selection, "ranking": ranked,
                "fresh_entry_members": fresh["members"],
                "membership_comparison_available": bool(prior) and selection["selection_available"],
                "planned_additions": sorted(after - before) if prior and selection["selection_available"] else None,
                "planned_removals": sorted(before - after) if prior and selection["selection_available"] else None,
                "actual_continuous_turnover": None,
                "incumbent_basis": "previous intended membership; not executed positions"}
            # An unavailable date breaks the diagnostic chain; it is not a liquidation.
            previous[arm] = current if selection["selection_available"] else {}
        periods.append(period)
    return periods


def entry_diagnostics(periods, index, quotes, requirements, spec, unit_reviews=()):
    # Reuse the same primary quote/lot/settlement machinery as H19's cost-only tool.
    # Import lazily to keep pure signal inspection independent of execution.
    from stocks_predictor.entry_feasibility import entry_case

    entries = []
    sessions = index["sessions"]
    for period in periods:
        asof = period["asof"]
        entry = sessions[sessions.index(asof) + 1] if asof in sessions and asof != sessions[-1] else None
        for arm in ARMS:
            selected = period["arms"][arm]
            for capital in spec["orders"]["capital_brl"]:
                for cost in spec["orders"]["one_way_cost_rates"]:
                    base = {"arm": arm, "signal_date": asof, "capital_brl": capital,
                            "one_way_cost_rate": cost, "profit": None}
                    if not selected["selection_available"] or entry is None:
                        entries.append({**base, "status": "BLOCKED",
                                        "reason": "INSUFFICIENT_COMMON_FEATURE_COVERAGE_OR_CALENDAR"})
                        continue
                    # Start each entry in cash. The buffer must equal the unbuffered
                    # quality arm here; retention savings need an actual prior book.
                    members = [{"ticker": m["ticker"], "isin": m["isin"], "lot": 100,
                                "tax_class": "equity"} for m in selected["fresh_entry_members"]]
                    plan = {"asof": asof, "entry": entry, "members": members}
                    case = entry_case(capital, cost, plan, quotes, index["settlements"][entry],
                                      requirements, unit_reviews)
                    entries.append({**case, "arm": arm, "incumbent_basis": "independent empty book",
                                    "source_certification": "entry feasibility only; incomplete event inventory"})
    return entries


def run(features_path, accounting_path, source_dir, execution_dir, protocol_path, entry_unit_review=None):
    spec, features, accounting = verify_sources(protocol_path, features_path, accounting_path,
                                                source_dir, execution_dir)
    _, index, _, _, _, gate, files = inspect_inputs(execution_dir)
    quotes, quote_count = load_quotes(execution_dir, index)
    periods = signal_diagnostics(features, accounting)
    evidence = read(execution_dir / "evidence.json")
    unit_reviews = []
    extra = {}
    if entry_unit_review is not None:
        from stocks_predictor.entry_feasibility import load_unit_reviews
        addendum_path = protocol_path.with_name("2026-09-08-h20-entry-source-addendum.json")
        if sha256(addendum_path) != ENTRY_ADDENDUM_SHA256:
            raise ValueError("registered entry source addendum changed")
        addendum = read(addendum_path)
        if sha256(entry_unit_review) != addendum["review_sha256"]:
            raise ValueError("registered entry unit review changed")
        unit_reviews = load_unit_reviews(entry_unit_review)
        extra = {"entry_source_addendum_sha256": ENTRY_ADDENDUM_SHA256,
                 "entry_unit_review_sha256": addendum["review_sha256"]}
    entries = entry_diagnostics(periods, index, quotes, evidence["required_actions"], spec, unit_reviews)
    summaries = {}
    for arm in ARMS:
        rows = [p["arms"][arm] for p in periods]
        cases = [r for r in entries if r["arm"] == arm]
        summaries[arm] = {"eligible_signal_dates": sum(r["selection_available"] for r in rows),
            "comparable_membership_transitions": sum(r["membership_comparison_available"] for r in rows),
            "planned_additions": sum(len(r["planned_additions"] or []) for r in rows),
            "planned_removals": sum(len(r["planned_removals"] or []) for r in rows),
            "entry_status_counts": dict(Counter(r["status"] for r in cases)),
            "actual_continuous_turnover": None, "profit": None}
    return {**extra, "status": "COMPLETE_H20_SIGNAL_AND_FEASIBILITY_DIAGNOSTIC_NOT_RETURN_EVIDENCE",
        "protocol_id": spec["protocol_id"], "protocol_sha256": PROTOCOL_SHA256,
        "registered_inputs": spec["inputs"], "accounting_archives_verified": len(accounting["archive_sha256"]),
        "execution_input_files_verified": files, "execution_quote_records_validated": quote_count,
        "quarterly_signal_dates": len(periods), "source_cells": sum(p["source_cells"] for p in periods),
        "eligible_cells": sum(p["eligible_names"] for p in periods),
        "exclusion_counts": dict(Counter(r["reason"] for p in periods for r in p["excluded"])),
        "summaries": summaries, "periods": periods, "entry_cases": entries,
        "h19_evidence_ready": gate["ready"], "h20_history_evidence_certified": False,
        "profit": None, "actual_continuous_turnover": None, "new_historical_return_evaluations": 0,
        "minimum_registered_configurations": 35, "minimum_historical_return_evaluations": 37,
        "limitations": ["The shared history was already exposed. No fresh holdout or measured alpha.",
            "Value uses stale disclosed-capital proxy; profitability uses end-period equity, not average equity.",
            "No sector neutralization; ranks can shift sector risk. Negative profits remain eligible.",
            "Membership changes are planned-name changes, not realized shares, turnover or costs saved.",
            "Fresh entries do not exercise retention or weight bands. Synthetic paired books do.",
            "Inherited quote/action sources do not certify H20's continuous holdings, income or tax path.",
            "Missing dates and cases remain visible. No bulk reconstruction or missing-as-zero fallback."]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("features", "accounting", "source-dir", "execution-inputs", "protocol", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--entry-unit-review", type=Path)
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error("observations are append-only; output already exists")
    result = run(args.features, args.accounting, args.source_dir, args.execution_inputs,
                 args.protocol, args.entry_unit_review)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, default=str)
        stream.write("\n")
    print(json.dumps({k: v for k, v in result.items() if k not in {"periods", "entry_cases"}}, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
