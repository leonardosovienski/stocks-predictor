"""H20 on the dated cash/tax engine; historical readiness never invents profit.

The policy is pure and uses actual positions at each signal. The public CLI audits
the preserved historical inputs; absent H20 coverage stops before portfolio returns.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from stocks_predictor.buffered_rebalance import freeze_rebalance
from stocks_predictor.continuous_cash import run_continuous
from stocks_predictor.continuous_research import inspect_inputs, load_quotes, read, verify_manifest
from stocks_predictor.h20_research import verify_sources, sha256
from stocks_predictor.retail_cash import iso
from stocks_predictor.value_profitability import ARMS, select_members

SIGNALS_SHA = "13acee7062dddbf96c81356588f36806e758ea9e5c6c8f395e7891620b1f6a8f"


class H20Policy:
    """Fixed ranks and bands; no output returns or future holdings enter selection."""

    def __init__(self, arm, rankings):
        if arm not in ARMS:
            raise ValueError("unregistered H20 arm")
        self.arm = arm
        self.rankings = deepcopy(rankings)

    def __call__(self, plan, book, capital, signal_quotes, settlement):
        if book.day != plan["asof"]:
            raise ValueError("policy requires the actual signal-date book")
        incumbents = {t: h.isin for t, h in book.positions.items() if h.quantity > 0}
        allowed = {m["ticker"]: m for m in plan["members"]}
        if allowed:
            rows = self.rankings[plan["asof"]]
            if (len({r["cnpj"] for r in rows}) != len(rows)
                    or set(allowed) != {r["ticker"] for r in rows}
                    or any(r["isin"] != allowed[r["ticker"]]["isin"]
                           or iso(r["available_at"]) > book.day for r in rows)):
                raise ValueError("ranking differs from the causal common universe")
            selection = select_members(rows, incumbents, buffered=self.arm == ARMS[2])
            if not selection["selection_available"]:
                raise ValueError("insufficient H20 coverage is not a liquidation")
            members = [allowed[r["ticker"]] for r in selection["members"]]
        else:
            members = []  # Explicit terminal liquidation, never a missing ranking.
        frozen = freeze_rebalance(book, members, signal_quotes, plan["entry"], settlement,
                                  capital, buffered=self.arm == ARMS[2])
        return {"arm": self.arm, "members": members, "targets": dict(frozen.targets),
                "original_targets": dict(frozen.original_targets), "suppressed": frozen.suppressed,
                "actual_incumbents": {t: {"isin": h.isin, "quantity": h.quantity}
                                       for t, h in book.positions.items()},
                "sizing_capital_excluding_unpaid_claims": frozen.sizing_capital,
                "weight_band": frozen.weight_band}


def run_h20_book(tape, rankings, arm):
    """Low-level accounting replay; caller must supply the reviewed coverage gate.

    Synthetic tests supply fully declared fixture evidence. This function is not
    the historical evidence gate or a future-profit estimator.
    """
    result = run_continuous(**tape, selection_policy=H20Policy(arm, rankings))
    return {"arm": arm, "method": "ACTUAL_HOLDINGS_CONTINUOUS_CASH_TAX",
            "source_completeness_certified_by_this_engine": False,
            "future_profit_projection": None, **result}


def make_plans(signals, index):
    """Only causal source availability selects dates; unavailable dates stay visible."""
    source_plans = {p["asof"]: p for p in index["plans"]["comparison"]}
    plans, omitted, rankings = [], [], {a: {} for a in ARMS}
    for period in signals["periods"]:
        if not all(period["arms"][a]["selection_available"] for a in ARMS):
            omitted.append({"asof": period["asof"], "reason": "INSUFFICIENT_FEATURE_COVERAGE"})
            # An internal gap cannot silently become an unobserved holding period.
            if plans:
                raise ValueError("internal H20 signal gap requires a registered holding policy")
            continue
        source = source_plans[period["asof"]]
        allowed = {m["ticker"]: m for m in source["members"]}
        common = period["arms"][ARMS[0]]["ranking"]
        ids = {(m["ticker"], m["isin"], m["cnpj"]) for m in common}
        for a in ARMS:
            rows = period["arms"][a]["ranking"]
            if {(r["ticker"], r["isin"], r["cnpj"]) for r in rows} != ids:
                raise ValueError("H20 arms have different eligible universes")
            rankings[a][period["asof"]] = rows
        if any(m["ticker"] not in allowed or allowed[m["ticker"]]["isin"] != m["isin"] for m in common):
            raise ValueError("H20 identity lacks reviewed execution classification")
        plans.append({"asof": source["asof"], "entry": source["entry"],
                      "members": [allowed[m["ticker"]] for m in common]})
    if not plans or index["plans"]["comparison"][-1]["members"]:
        raise ValueError("eligible H20 periods and explicit source liquidation required")
    plans.append(deepcopy(index["plans"]["comparison"][-1]))
    return plans, rankings, omitted


def canonical_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     default=str).encode("utf-8")).hexdigest()


def validate_source_review(path, requirement):
    """Check an explicit human source review; hashes do not establish completeness.

    This supplements, and never replaces, the event-level coverage checks.
    Evidence files must be local to the review directory and byte-identified.
    """
    if path is None:
        return [{"kind": "H20_CONTINUOUS_SOURCE_ATTESTATION_MISSING"}]
    review = read(path)
    if any(review.get(k) != v for k, v in requirement.items()
           if k not in {"reviewed", "sources"}):
        raise ValueError("H20 source review does not bind the exact required inputs")
    if (review.get("reviewed") is not True or not review.get("reviewer")
            or not review.get("reviewed_on") or not review.get("sources")):
        return [{"kind": "H20_CONTINUOUS_SOURCE_ATTESTATION_UNREVIEWED"}]
    iso(review["reviewed_on"])
    for source in review["sources"]:
        evidence_path = (path.parent / source["path"]).resolve()
        if (not evidence_path.is_relative_to(path.parent.resolve())
                or not evidence_path.is_file() or sha256(evidence_path) != source["sha256"]):
            raise ValueError("H20 source review evidence absent, outside review directory or changed")
    return []


def historical_readiness(root, source_review=None):
    """Verify source bytes and list every unresolved economic dependency, offline."""
    repo = root / "work/stocks-predictor"
    base = root / "work/stocks-final-review-bundle/inputs"
    verify_sources(repo / "docs/research/2026-09-08-h20-implementation-protocol.json",
                   root / "work/value-prepared-features.json",
                   root / "work/value-capital-source/accounting-v2.json",
                   root / "work/source-acquisition", base)
    initial_manifest_sha = sha256(base / "SHA256.json")
    initial_review_sha = sha256(source_review) if source_review else None
    source = root / "work/h20-implementation-20260908/observation-02.json"
    if sha256(source) != SIGNALS_SHA:
        raise ValueError("frozen H20 signals changed")
    signals = read(source)
    _, index, _, _, _, gate, count = inspect_inputs(base)
    _, quote_count = load_quotes(base, index)
    plans, _, omitted = make_plans(signals, index)
    common = [[m["ticker"], m["isin"], p["entry"], nxt["entry"]]
              for p, nxt in zip(plans, plans[1:]) for m in p["members"]]
    evidence = read(base / "evidence.json")
    # Conservative union includes the older comparison's known successor paths.
    # A later source review can register a narrower scope; this repair cannot.
    required = sorted({tuple(i) for i in common + evidence["required_intervals"]})
    verified = {tuple(r["interval"]) for r in evidence["cash_coverage"]
                if r.get("verified") is True and r.get("sources")}
    extra_intervals = sorted(set(required) - {tuple(i) for i in evidence["required_intervals"]})
    issues = list(gate["issues"])
    issues.extend({"kind": "H20_ADDITIONAL_CASH_INTERVAL", "interval": i}
                  for i in extra_intervals if i not in verified)
    review_requirement = {"signals_sha256": SIGNALS_SHA,
        "execution_manifest_sha256": sha256(base / "SHA256.json"),
        "conservative_intervals_sha256": canonical_digest(required),
        "scope": "all common eligible holdings and known successor intervals; continuous H20 cash, corporate terms and tax path",
        "reviewed": False, "sources": []}
    issues.extend(validate_source_review(source_review, review_requirement))
    # Do not publish a diagnosis assembled while its source bytes were changing.
    verify_manifest(base)
    if (sha256(source) != SIGNALS_SHA
            or sha256(base / "SHA256.json") != initial_manifest_sha
            or (source_review and sha256(source_review) != initial_review_sha)):
        raise ValueError("frozen H20 signals changed during readiness")
    return {"status": ("BLOCKED_H20_HISTORICAL_NET_PROFIT" if issues
                       else "SOURCE_CHECKS_PASSED_NO_HISTORICAL_RETURN_EXECUTED"), "profit": None,
        "future_profit_projection": None, "full_history_executed": False,
        "new_historical_return_evaluations": 0, "administrative_counts": [53, 55],
        "verified_input_files": count, "validated_quote_records": quote_count,
        "quarterly_rebalance_dates": len(plans)-1, "unavailable_signal_dates": omitted,
        "common_universe_intervals": len(common), "conservative_required_intervals": required,
        "certified_intervals": len(set(required) & verified),
        "issue_counts": dict(Counter(r["kind"] for r in issues)), "issues": issues,
        "code_integration": "actual-position selection, rank/weight bands, dated cash, corporate actions, taxes before buys, fractional execution and final liquidation share the tested continuous engine",
        "economic_limits": "Missing source coverage is not zero income. Prospective evidence and actual maintenance costs are not supplied by code.",
        "required_h20_source_review": review_requirement}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-review", type=Path)
    args = parser.parse_args(argv)
    if args.output.exists():
        raise FileExistsError("diagnostics are append-only")
    result = historical_readiness(args.root, args.source_review)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False, default=str)
        stream.write("\n")
    print(json.dumps({k: v for k, v in result.items() if k not in {"issues", "conservative_required_intervals"}}, default=str))
    return 2 if result["issues"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
