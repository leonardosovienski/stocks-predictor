"""Conformance vectors: E2E, IDEMPOTENCY, ADMISSION, AUTHORITY, FUTURE_CANARY, TEMPORAL_INTEGRITY,
External Intelligence NOT_READY and COLLECTION_ONLY.

Every call goes through the installed `stocks-research` console script in a new process
(no pipeline assembled by hand, no mocks of predictor_core or predictor_ops).
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from conformance.fixtures import (
    CANARY,
    HYPOTHESIS,
    build,
    cli,
    collection_request,
    experiments,
    ops_runtime,
    request,
    write_request,
)


@pytest.fixture()
def env(tmp_path):
    return build(tmp_path)


def _only(lines):
    assert len(lines) == 1, lines
    return lines[0]


def _result(outcome):
    """Full result as written in the outcome file (stdout carries a summary line)."""
    return json.loads(Path(outcome["outcome_file"]).read_text(encoding="utf-8"))["result"]


def _all_text(root: Path) -> str:
    chunks = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in {".json", ".jsonl"}:
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(chunks)


def _ops_successes(env) -> int:
    total = 0
    for events in ops_runtime(env).glob("stocks-research-*/events.jsonl"):
        for line in events.read_text(encoding="utf-8").splitlines():
            if line.strip() and json.loads(line).get("run_status") == "SUCCEEDED":
                total += 1
    return total


def test_e2e_result_is_reread_identically_after_restart(env):
    path = write_request(env, "e2e", request("stocks:REQ-E2E-001", client_ref={"ticket": 7}))
    code, lines = cli(env, "process", str(path))
    outcome = _only(lines)
    assert code == 0 and outcome["status"] == "RESULT"
    assert outcome["client_ref"] == {"ticket": 7}
    assert outcome["result_id"].startswith("stocks:RESULT-")
    assert outcome["experiment_id"].startswith("stocks:EXP-")
    assert outcome["operational_state"] == "SUCCEEDED" and outcome["capital_permission"] is False
    stored = _result(outcome)
    code, lines = cli(env, "show", "stocks:REQ-E2E-001")
    shown = _only(lines)
    assert code == 0 and shown["source"] == "authoritative_result_store"
    assert shown["result"] == stored
    assert stored["scientific_state"] == "SUPPORTED"
    assert stored["core_facts"]["trial_ids"] and stored["core_facts"]["scientific_state_source"] == "core_trial_registry"
    assert stored["core_facts"]["temporal_validation"]["method"] == "predictor_core.measurement.replay"
    assert stored["ops_facts"]["ops_run_id"] and stored["ops_facts"]["operational_state"] == "SUCCEEDED"
    assert stored["ops_facts"]["economic_lock_id"].startswith("economic-")
    facts = stored["domain_facts"]
    metrics = facts["metrics"]
    assert metrics["periods"] >= 24
    assert metrics["excess_net_ci_bps"][0] <= metrics["excess_net_bps"] <= metrics["excess_net_ci_bps"][1]
    assert metrics["excess_gross_bps"] > metrics["excess_net_bps"]  # costs are charged
    assert facts["external_intelligence"]["consumed_families"] == [] and stored["trial_eligible"] is False
    assert all(len(r["members"]) <= 10 for r in facts["rebalances"])
    for block in ("core_facts", "ops_facts", "domain_facts", "provenance"):
        assert stored[block]
    code, lines = cli(env, "reconcile")
    assert code == 0 and _only(lines)["findings"] == []


def test_idempotency_duplicate_retry_and_conflict(env):
    first = write_request(env, "a", request("stocks:REQ-IDEM-001", client_ref="first"))
    code, lines = cli(env, "process", str(first))
    original = _only(lines)
    assert code == 0 and original["status"] == "RESULT"
    again = write_request(env, "b", request("stocks:REQ-IDEM-001", client_ref="second"))
    for _ in range(2):
        code, lines = cli(env, "process", str(again))
        duplicate = _only(lines)
        assert code == 0 and duplicate["status"] == "DUPLICATE"
        assert duplicate["client_ref"] == "second" and duplicate["result_id"] == original["result_id"]
        assert _result(duplicate) == _result(original)
    changed = request("stocks:REQ-IDEM-001", dataset="case_a")
    code, lines = cli(env, "process", str(write_request(env, "c", changed)))
    assert code == 2 and _only(lines)["status"] == "CONFLICT"
    code, lines = cli(env, "show", "stocks:REQ-IDEM-001")
    assert _only(lines)["result"] == _result(original)
    assert len(list(experiments(env).iterdir())) == 1
    assert _ops_successes(env) == 1
    with sqlite3.connect(env["state"] / "results.sqlite") as db:
        assert db.execute("SELECT count(*) FROM results").fetchone()[0] == 1
    trials = list(experiments(env).rglob("trials-v2.json"))
    assert len(trials) == 1 and len(json.loads(trials[0].read_text(encoding="utf-8"))) == 1


def test_future_canary_fails_closed_and_never_leaks(env):
    path = write_request(env, "canary", request("stocks:REQ-CANARY-001", dataset="future_canary"))
    code, lines = cli(env, "process", str(path))
    outcome = _only(lines)
    assert code == 4 and outcome["status"] == "TEMPORAL_INTEGRITY_VIOLATION"
    assert outcome["scientific_state"] == "NOT_EVALUATED" and outcome["economic_state"] == "NOT_EVALUATED"
    assert "LookaheadError" in outcome["reason"]
    assert cli(env, "show", "stocks:REQ-CANARY-001")[0] == 3
    assert not list(experiments(env).rglob("domain-effect.json"))
    assert not list(experiments(env).rglob("trials-v2.json"))
    ok = write_request(env, "ok", request("stocks:REQ-CANARY-OK"))
    assert cli(env, "process", str(ok))[0] == 0
    downstream = [p for p in experiments(env).rglob("*") if p.is_file() and "references" not in p.parts]
    text = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in downstream)
    assert CANARY not in text and "987.654321" not in text
    results_db = (env["state"] / "results.sqlite").read_bytes()
    assert CANARY.encode() not in results_db and b"987.654321" not in results_db
    assert CANARY not in _all_text(env["state"] / "outcomes")


def test_temporal_integrity_as_of_mismatch_fails_closed(env):
    mismatch = request("stocks:REQ-ASOF-001", as_of="2026-09-30T00:00:00Z")
    code, lines = cli(env, "process", str(write_request(env, "m", mismatch)))
    outcome = _only(lines)
    assert code == 4 and outcome["status"] == "TEMPORAL_INTEGRITY_VIOLATION"
    assert "data_cutoff" in outcome["reason"]


@pytest.mark.parametrize(
    ("dataset", "result_state", "scientific", "economic"),
    [
        ("case_a", "INCONCLUSIVE", "INCONCLUSIVE", "NO_EDGE"),
        ("case_b", "NO_EDGE", "SUPPORTED", "NO_EDGE"),
        ("insufficient", "CLOSED_INSUFFICIENT_SAMPLE", "INSUFFICIENT_SAMPLE", "NOT_EVALUATED"),
    ],
)
def test_authority_states_stay_separate(env, dataset, result_state, scientific, economic):
    path = write_request(env, dataset, request(f"stocks:REQ-{dataset.upper().replace('_', '-')}", dataset=dataset))
    code, lines = cli(env, "process", str(path))
    outcome = _only(lines)
    assert code == 0 and outcome["operational_state"] == "SUCCEEDED"
    assert (outcome["result_state"], outcome["scientific_state"], outcome["economic_state"]) == (
        result_state, scientific, economic)
    stored = _result(outcome)
    assert stored["capital_permission"] is False
    if dataset == "case_b":
        metrics = stored["domain_facts"]["metrics"]
        assert metrics["excess_gross_ci_bps"][0] > 0 and metrics["excess_net_bps"] <= 0
    if dataset == "insufficient":
        assert stored["core_facts"]["trial_ids"] == []


@pytest.mark.parametrize(
    ("mutate", "reason"),
    [
        (lambda r: r | {"command": "powershell.exe -c calc"}, "SCHEMA_INVALID"),
        (lambda r: r | {"handler": "os.system"}, "SCHEMA_INVALID"),
        (lambda r: r | {"module": "stocks_predictor.backtest"}, "SCHEMA_INVALID"),
        (lambda r: r | {"sql": "DROP TABLE prices_raw"}, "SCHEMA_INVALID"),
        (lambda r: r | {"capital_permission": True}, "SCHEMA_INVALID"),
        (lambda r: r | {"budget": {"timeout_seconds": 99999}}, "SCHEMA_INVALID"),
        (lambda r: r | {"parameters": r["parameters"] | {"path": "C:/STOCKS/data"}}, "SCHEMA_INVALID"),
        (lambda r: r | {"parameters": r["parameters"] | {"url": "https://example.invalid"}}, "SCHEMA_INVALID"),
        (lambda r: r | {"schema_version": "stocks-research-request/2"}, "SCHEMA_INVALID"),
        (lambda r: r | {"request_type": "RUN_SHELL"}, "REQUEST_TYPE_NOT_ALLOWED"),
        (lambda r: r | {"request_id": "REQ-NO-DOMAIN"}, "SCHEMA_INVALID"),
        (lambda r: r | {"request_id": "crypto:REQ-OTHER-DOMAIN"}, "SCHEMA_INVALID"),
        (lambda r: r | {"hypothesis_id": "stocks:H1"}, "HYPOTHESIS_CLOSED"),
        (lambda r: r | {"hypothesis_id": "stocks:H7"}, "HYPOTHESIS_CLOSED"),
        (lambda r: r | {"hypothesis_id": "stocks:H17"}, "HYPOTHESIS_NOT_ACTIVE"),
        (lambda r: r | {"hypothesis_id": "stocks:H99"}, "HYPOTHESIS_NOT_ACTIVE"),
        (lambda r: r | {"hypothesis_id": "stocks:NOT-IN-POLICY"}, "HYPOTHESIS_NOT_ADMITTED"),
        (lambda r: r | {"references": r["references"] | {"dataset": {"name": "unknown", "version": "v1"}}},
         "REFERENCE_UNAUTHORIZED_OR_UNKNOWN"),
        (lambda r: r | {"parameters": r["parameters"] | {"fee_bps": 10_000}}, "PARAMETER_OUT_OF_BOUNDS"),
        (lambda r: r | {"pit": {"availability_rule": "ANY", "minimum_pit_class": "PIT_STRICT"}}, "SCHEMA_INVALID"),
        (lambda r: r | {"pit": r["pit"] | {"minimum_pit_class": "HISTORICAL_ONLY"}}, "SCHEMA_INVALID"),
    ],
)
def test_admission_rejects_before_any_execution(env, mutate, reason):
    value = mutate(request("stocks:REQ-BAD-001"))
    code, lines = cli(env, "process", str(write_request(env, "bad", value)))
    outcome = _only(lines)
    assert code == 2 and outcome["status"] == "REJECTED"
    assert outcome["reason"].startswith(reason)
    assert not ops_runtime(env).exists()


def test_collector_outside_policy_is_rejected(env):
    value = collection_request("stocks:REQ-COLL-BAD", parameters={"collector": "cvm-ipe", "period": "2026",
                                                                  "observed_at": "2026-09-19T12:00:00Z"})
    code, lines = cli(env, "process", str(write_request(env, "c", value)))
    assert code == 2 and _only(lines)["reason"] == "COLLECTOR_NOT_ALLOWED"


def test_invalid_json_and_duplicate_keys_are_rejected(env):
    for text in ("{not json", '{"request_id": "stocks:A", "request_id": "stocks:B"}', "[]", '{"a": NaN}'):
        code, lines = cli(env, "process", str(write_request(env, "raw", text)))
        assert code == 2 and _only(lines)["status"] == "REJECTED"


def test_hypothesis_constant_is_frozen():
    assert HYPOTHESIS == "stocks:QUAL-PIT-MOM-001"


def test_duplicate_after_policy_change_returns_the_stored_result(env):
    path = write_request(env, "p", request("stocks:REQ-POLICY-001", client_ref="before"))
    code, lines = cli(env, "process", str(path))
    original = _only(lines)
    assert code == 0 and original["status"] == "RESULT"
    policy = json.loads(env["policy"].read_text(encoding="utf-8"))
    policy["policy_version"] += 1
    env["policy"].write_text(json.dumps(policy, indent=1), encoding="utf-8")
    code, lines = cli(env, "process", str(write_request(env, "p2", request("stocks:REQ-POLICY-001",
                                                                           client_ref="after"))))
    duplicate = _only(lines)
    assert code == 0 and duplicate["status"] == "DUPLICATE"
    assert duplicate["client_ref"] == "after" and _result(duplicate) == _result(original)
    pending = write_request(env, "q", request("stocks:REQ-POLICY-002"))
    policy["policy_version"] += 1
    assert cli(env, "process", str(pending), fault="after_admission")[0] == 86
    env["policy"].write_text(json.dumps(policy, indent=1), encoding="utf-8")
    code, lines = cli(env, "process", str(pending))
    assert code == 2 and _only(lines)["reason"] == "POLICY_CHANGED"


@pytest.mark.parametrize("readiness", ["matrix-20260921", "counterfactual-vlmo-ready"])
def test_external_intelligence_not_ready_never_becomes_a_signal(env, readiness):
    value = request(f"stocks:REQ-EI-{readiness[:6].upper()}")
    value["references"]["readiness"] = {"name": readiness, "version": "v1"}
    value["parameters"]["external_intelligence"] = {"mode": "TRIAL_CONSUMPTION", "families": ["CVM_VLMO"]}
    code, lines = cli(env, "process", str(write_request(env, "ei", value)))
    outcome = _only(lines)
    assert code == 0 and outcome["result_state"] == "NOT_READY"
    assert (outcome["scientific_state"], outcome["economic_state"]) == ("NOT_EVALUATED", "NOT_EVALUATED")
    stored = _result(outcome)
    assert stored["core_facts"]["trial_ids"] == [] and stored["trial_eligible"] is False
    ei = stored["domain_facts"]["external_intelligence"]
    assert ei["consumed_families"] == [] and ei["consumed_observations"] == 0
    reason = ei["decisions"]["CVM_VLMO"]["reason"]
    assert reason.startswith("FAMILY_NOT_READY" if readiness == "matrix-20260921" else "FAMILY_NOT_BOUND_TO_MODEL")
    assert not list(experiments(env).rglob("trials-v2.json"))


def test_collection_only_collects_persists_and_never_feeds_a_trial(env):
    path = write_request(env, "col", collection_request("stocks:REQ-COLLECT-001"))
    code, lines = cli(env, "process", str(path))
    outcome = _only(lines)
    assert code == 0 and outcome["status"] == "RESULT" and outcome["result_state"] == "COLLECTION_RECORDED"
    stored = _result(outcome)
    facts = stored["domain_facts"]
    assert facts["collection_status"] == "SUCCESS" and facts["domain_cli_exit"] == 0
    assert facts["mode"] == "COLLECTION_ONLY" and facts["trial_eligible"] is False
    assert facts["feeds"] == {"trial": False, "ranking": False, "portfolio": False, "capital": False}
    assert facts["family_axes"]["trial_eligibility"] == "NOT_READY"
    assert stored["core_facts"]["trial_ids"] == [] and stored["trial_eligible"] is False
    staging = env["state"] / "x" / "ei" / "external.sqlite"
    with sqlite3.connect(staging) as db:
        assert db.execute("SELECT count(*) FROM external_receipts").fetchone()[0] >= 1
    code, lines = cli(env, "process", str(path))
    assert code == 0 and _only(lines)["status"] == "DUPLICATE"
    assert _ops_successes(env) == 1
