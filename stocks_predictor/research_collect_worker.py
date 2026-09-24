"""Closed local worker for External Intelligence collection (handler external_collection.v1).

COLLECTION_ONLY: the worker collects, validates, persists and monitors one official source
file through the real domain CLI (``python -m stocks_predictor external collect ...``,
here called in-process as ``operations.main``) into the circuit's staging database. It
never produces a trial, a ranking, a portfolio or a capital decision: its effect records
the collection receipt and the family's readiness axes, with ``trial_eligible = false``.

The operator provisions the official file as an immutable reference object
(``stocks-ei-source/1``: collector, base64 payload and its sha256); the request only
selects it. No network is used (``--source-file``).
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path

from .research_contract import COLLECT, COLLECTORS
from .research_io import atomic_write, strict_json_loads
from .research_readiness import ReadinessError, classify

HANDLER = "stocks.handlers.external_collection.v1"
EXIT_REFUSED = 5
EXIT_INTEGRITY = 6


class Refusal(ValueError):
    pass


def evaluate(request: dict, staging: Path) -> dict:
    expected = {"schema", "experiment_id", "request", "references", "identities", "registered_at", "code_version"}
    if set(request) != expected or request["schema"] != "stocks-admitted-collection/1":
        raise Refusal("invalid closed worker request")
    task = request["request"]
    if task["request_type"] != COLLECT:
        raise Refusal("handler mismatch")
    refs = {}
    for item in request["references"]:
        raw = Path(item["path"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != request["identities"].get(item["kind"]):
            raise ValueError(f"INTEGRITY: reference {item['kind']} changed after materialization")
        refs[item["kind"]] = strict_json_loads(raw)
    params = task["parameters"]
    family, period_kind = COLLECTORS[params["collector"]]
    source = refs["source"]
    if source.get("schema") != "stocks-ei-source/1" or source.get("collector") != params["collector"]:
        raise Refusal("source object does not match the requested collector")
    payload = base64.b64decode(source["payload_b64"], validate=True)
    if hashlib.sha256(payload).hexdigest() != source.get("payload_sha256"):
        raise ValueError("INTEGRITY: source payload hash mismatch")
    try:
        axes = classify(refs["readiness"])
    except (ReadinessError, KeyError, TypeError) as exc:
        raise Refusal(f"readiness matrix: {exc}") from exc
    work = staging / "sources" / request["experiment_id"].split(":")[-1]
    work.mkdir(parents=True, exist_ok=True)
    source_file = work / source.get("file_name", "source.zip")
    atomic_write(source_file, payload)
    receipt_path = work / "receipt.json"
    argv = ["external", "collect", params["collector"], "--db", str(staging / "external.sqlite"),
            "--raw-root", str(staging / "raw"), "--receipt", str(receipt_path),
            "--source-file", str(source_file), "--observed-at", params["observed_at"]]
    if period_kind == "year":
        argv += ["--year", params["period"]]
    elif period_kind == "month":
        argv += ["--month", params["period"]]
    from .operations import main as domain_cli

    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        code = domain_cli(argv)
    receipt = strict_json_loads(receipt_path.read_text(encoding="utf-8")) if receipt_path.exists() else None
    family_axes = axes["families"].get(family, {}).get("axes")
    return {
        "schema": "stocks-collection-effect/1",
        "experiment_id": request["experiment_id"],
        "as_of": task["as_of"],
        "mode": "COLLECTION_ONLY",
        "collector": params["collector"],
        "family": family,
        "period": params["period"],
        "source_payload_sha256": source["payload_sha256"],
        "domain_cli_exit": code,
        "collection_status": (receipt or {}).get("status", "NO_RECEIPT"),
        "receipt": receipt,
        "family_axes": family_axes,
        "trial_eligible": False,
        "consumed_by_trial": 0,
        "feeds": {"trial": False, "ranking": False, "portfolio": False, "capital": False},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--effect", type=Path, required=True)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--fault", choices=("crash", "hang", "slow", "partial"))
    args = parser.parse_args(argv)
    if args.fault == "crash":
        os._exit(97)
    refusal = args.effect.with_name("worker-refusal.json")
    try:
        effect = evaluate(strict_json_loads(args.request.read_text(encoding="utf-8")), args.staging)
    except Refusal as exc:
        atomic_write(refusal, json.dumps({"exit_code": EXIT_REFUSED, "kind": "Refusal", "reason": str(exc)[:1000]},
                                         sort_keys=True).encode())
        return EXIT_REFUSED
    except ValueError as exc:
        if str(exc).startswith("INTEGRITY"):
            atomic_write(refusal, json.dumps({"exit_code": EXIT_INTEGRITY, "kind": "IntegrityViolation",
                                              "reason": str(exc)[:1000]}, sort_keys=True).encode())
            return EXIT_INTEGRITY
        raise
    raw = (json.dumps(effect, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
    if args.effect.exists():
        return 0  # effect already committed by an earlier attempt: never rewritten
    atomic_write(args.effect, raw)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
