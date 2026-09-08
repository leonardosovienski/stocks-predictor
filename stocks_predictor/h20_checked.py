"""Reproduce the frozen H20 diagnostic only after verifying all evidence inputs.

The archived measurement and prior observations stay unchanged. This entry point
adds integrity checks, not a new strategy, source approval or profit calculation.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from stocks_predictor.continuous_research import verify_manifest

MANIFEST_SHA = "7edf2f20546e9dee910e4f2d1aa6a4a748efcc07dfd2b2a04b393f41a644b6e7"
GATE_SHA = "585c72395fc2fefc2e0bbd90b6756c516e58d0f1e29ada3d6de196f46ea49c27"
CODE_SHA = "359517909d7d3630d8dadef203cfa5df40ec48c5013d407560806ee341de4cba"
OBSERVATION_SHA = "aa184580bf5ba69b515a20cc40115453396bdefa470ac0f5408c0d3ced15e1a3"


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify_evidence(base, gate):
    if digest(base / "SHA256.json") != MANIFEST_SHA:
        raise ValueError("frozen execution manifest changed")
    verified = verify_manifest(base)
    if "evidence.json" not in verified:
        raise ValueError("evidence inventory absent from manifest")
    if digest(gate) != GATE_SHA:
        raise ValueError("frozen financial gate changed")
    return len(verified)


def run_checked(root, gate):
    repo = root / "work/stocks-predictor"
    base = root / "work/stocks-final-review-bundle/inputs"
    verify_evidence(base, gate)
    code = repo / "research/session-20260908/h20-profit-test/compare_h20.py"
    if digest(code) != CODE_SHA:
        raise ValueError("frozen measurement code changed")
    spec = importlib.util.spec_from_file_location("frozen_h20_checked_comparison", code)
    if spec is None or spec.loader is None:
        raise ValueError("cannot load the frozen measurement module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.run(root, repo / "docs/research/2026-09-08-h20-profit-test-protocol.json", gate)
    verify_evidence(base, gate)
    raw = (json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False)+"\n").encode("utf-8")
    if hashlib.sha256(raw).hexdigest() != OBSERVATION_SHA:
        raise ValueError("result differs from the frozen diagnostic; no replacement published")
    return raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("root", "gate", "output"):
        parser.add_argument("--"+name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("observations are append-only")
    raw = run_checked(args.root, args.gate)
    with args.output.open("xb") as stream:
        stream.write(raw)
    print(json.dumps({"status": "REPRODUCED_WITH_FULL_EVIDENCE_INTEGRITY",
                      "sha256": OBSERVATION_SHA, "profit": None,
                      "new_historical_return_evaluations": 0}))


if __name__ == "__main__":
    main()
