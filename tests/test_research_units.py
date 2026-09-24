"""In-process units of the stocks research circuit (complement to tests/conformance).

The conformance suite drives the installed `stocks-research` entrypoint in new processes;
these tests call the same public functions in the test process so the components are
also measured by coverage. predictor_core and predictor_ops are the real wheels; the Ops
job still runs the worker as a child process.
"""

from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from conformance.fixtures import build, collection_request, panel, request, write_request  # noqa: E402
from stocks_predictor import research_contract as contract  # noqa: E402
from stocks_predictor import research_runner, research_worker  # noqa: E402
from stocks_predictor.research_admission import AdmissionStore, closed_hypotheses, load_policy  # noqa: E402
from stocks_predictor.research_execution import ReferenceStore, ResearchExecutor  # noqa: E402
from stocks_predictor.research_io import atomic_write, strict_json_loads  # noqa: E402
from stocks_predictor.research_readiness import ReadinessError, classify  # noqa: E402


def _main(*argv: str) -> tuple[int, list[dict]]:
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        code = research_runner.main(list(argv))
    return code, [json.loads(line) for line in buffer.getvalue().splitlines() if line.startswith("{")]


def _process(env, *files) -> tuple[int, list[dict]]:
    return _main("--state", str(env["state"]), "process", "--policy", str(env["policy"]),
                 "--objects", str(env["objects"]), *map(str, files))


def test_in_process_circuit_end_to_end_duplicate_backup_and_restore(tmp_path):
    env = build(tmp_path)
    path = write_request(env, "e2e", request("stocks:REQ-UNIT-001", client_ref=[1, 2]))
    code, lines = _process(env, path)
    assert code == 0 and lines[0]["status"] == "RESULT" and lines[0]["client_ref"] == [1, 2]
    code, lines = _process(env, path)
    assert code == 0 and lines[0]["status"] == "DUPLICATE"
    code, lines = _main("--state", str(env["state"]), "show", "stocks:REQ-UNIT-001")
    assert code == 0 and lines[0]["result"]["capital_permission"] is False
    assert _main("--state", str(env["state"]), "show", "stocks:REQ-NOPE")[0] == 3
    code, lines = _main("--state", str(env["state"]), "reconcile")
    assert code == 0 and lines[0]["findings"] == []
    bundle = tmp_path / "bundle"
    code, lines = _main("--state", str(env["state"]), "backup", "--out", str(bundle))
    assert code == 0 and lines[0]["files"] > 0
    restored = tmp_path / "restored"
    code, lines = _main("--state", str(env["state"]), "restore", "--bundle", str(bundle), "--into", str(restored))
    assert code == 0 and lines[0]["status"] == "RESTORED_TO_NEW_ROOT"
    with pytest.raises(FileExistsError):
        _main("--state", str(env["state"]), "restore", "--bundle", str(bundle), "--into", str(restored))


def test_in_process_inbox_run_rejections_and_put_object(tmp_path):
    env = build(tmp_path)
    write_request(env, "a", request("stocks:REQ-UNIT-RUN-1", dataset="insufficient"))
    write_request(env, "b", request("stocks:REQ-UNIT-RUN-2", hypothesis_id="stocks:H9"))
    write_request(env, "c", "{broken")
    code, lines = _main("--state", str(env["state"]), "run", "--policy", str(env["policy"]),
                        "--objects", str(env["objects"]), "--inbox", str(env["requests"]))
    statuses = {line.get("request_id"): (line["status"], line.get("reason")) for line in lines}
    assert code == 2
    assert statuses["stocks:REQ-UNIT-RUN-1"] == ("RESULT", None)
    assert statuses["stocks:REQ-UNIT-RUN-2"] == ("REJECTED", "HYPOTHESIS_CLOSED")
    assert statuses[None][0] == "REJECTED"
    obj = tmp_path / "obj.json"
    obj.write_text('{"k": 1}', encoding="utf-8")
    code, lines = _main("--state", str(env["state"]), "put-object", "--objects", str(env["objects"]), str(obj))
    assert code == 0 and len(lines[0]["object_hash"]) == 64


def test_in_process_collection_and_not_ready(tmp_path):
    env = build(tmp_path)
    code, lines = _process(env, write_request(env, "col", collection_request("stocks:REQ-UNIT-COL")))
    assert code == 0 and lines[0]["result_state"] == "COLLECTION_RECORDED"
    value = request("stocks:REQ-UNIT-EI")
    value["parameters"]["external_intelligence"] = {"mode": "COLLECTION_ONLY", "families": ["B3_LENDING"]}
    code, lines = _process(env, write_request(env, "ei", value))
    assert code == 0 and lines[0]["scientific_state"] == "SUPPORTED"  # observed-not-consumed never gates science
    result = json.loads(Path(lines[0]["outcome_file"]).read_text(encoding="utf-8"))["result"]
    assert result["domain_facts"]["external_intelligence"]["consumed_families"] == []


def _admitted_worker_request(tmp_path, env, request_id, **overrides):
    store = AdmissionStore(env["state"] / "admission.sqlite", env["policy"])
    receipt = store.submit(request(request_id, **overrides))
    assert receipt["decision"] == "ACCEPTED"
    context = store.admitted_context(request_id)
    materialized = ReferenceStore(env["objects"]).materialize(receipt["resolved_references"], tmp_path / "refs")
    return {
        "schema": "stocks-admitted-backtest/1", "experiment_id": "stocks:EXP-UNIT", "trial_id": "stocks:TRIAL-UNIT",
        "request": {k: v for k, v in context["request"].items() if k != "client_ref"},
        "references": [{"kind": m["kind"], "path": m["path"]} for m in materialized],
        "identities": {m["kind"]: m["content_hash"] for m in materialized},
        "registered_at": "2026-09-24T00:00:00.000000Z", "code_version": "stocks-predictor==unit",
    }


@pytest.mark.parametrize("control", [None, "SHUFFLED_LABELS", "TEMPORAL_ABLATION", "FEATURE_ABLATION",
                                     "UNIVERSE_PERTURBATION"])
def test_worker_in_process_writes_effect_and_core_trial(tmp_path, control):
    env = build(tmp_path / "env")
    overrides = {}
    if control:
        params = request("x")["parameters"] | {"negative_control": {"kind": control, "seed": 7}}
        overrides["parameters"] = params
    worker_request = _admitted_worker_request(tmp_path, env, f"stocks:REQ-W-{control or 'REF'}", **overrides)
    request_file = tmp_path / "worker-request.json"
    request_file.write_text(json.dumps(worker_request), encoding="utf-8")
    effect = tmp_path / "effect.json"
    trials = tmp_path / "trials.json"
    assert research_worker.main(["--request", str(request_file), "--effect", str(effect),
                                 "--trial-registry", str(trials)]) == 0
    written = json.loads(effect.read_text(encoding="utf-8"))
    assert written["trial"]["trial_id"] == "stocks:TRIAL-UNIT" and written["negative_control"] == (
        {"kind": control, "seed": 7} if control else None)
    assert json.loads(trials.read_text(encoding="utf-8"))[0]["status"] == written["scientific_state"]
    # idempotent rerun: same bytes, same single trial
    assert research_worker.main(["--request", str(request_file), "--effect", str(effect),
                                 "--trial-registry", str(trials)]) == 0
    assert len(json.loads(trials.read_text(encoding="utf-8"))) == 1


def test_worker_refusals_write_a_refusal_and_no_effect(tmp_path):
    env = build(tmp_path / "env")
    worker_request = _admitted_worker_request(tmp_path, env, "stocks:REQ-W-TEMPORAL", dataset="future_canary")
    request_file = tmp_path / "worker-request.json"
    request_file.write_text(json.dumps(worker_request), encoding="utf-8")
    effect = tmp_path / "effect.json"
    code = research_worker.main(["--request", str(request_file), "--effect", str(effect), "--trial-registry",
                                 str(tmp_path / "t.json")])
    assert code == research_worker.EXIT_TEMPORAL and not effect.exists()
    assert "LookaheadError" in json.loads((tmp_path / "worker-refusal.json").read_text(encoding="utf-8"))["reason"]
    tampered = dict(worker_request, identities=dict(worker_request["identities"], dataset="0" * 64))
    request_file.write_text(json.dumps(tampered), encoding="utf-8")
    assert research_worker.main(["--request", str(request_file), "--effect", str(effect), "--trial-registry",
                                 str(tmp_path / "t.json")]) == research_worker.EXIT_INTEGRITY
    request_file.write_text(json.dumps({"schema": "other"}), encoding="utf-8")
    assert research_worker.main(["--request", str(request_file), "--effect", str(effect), "--trial-registry",
                                 str(tmp_path / "t.json")]) == research_worker.EXIT_REFUSED


def test_contract_validation_rules():
    good = request("stocks:REQ-C-1")
    assert contract.validate_request(good) is good
    assert contract.request_content_hash(good) == contract.request_content_hash(good | {"client_ref": "x"})
    assert contract.idempotency_key(good) == "stocks:REQ-C-1"
    for bad, reason in (
        (good | {"as_of": "2026-01-01"}, "SCHEMA_INVALID"),
        (good | {"priority_hint": "URGENT"}, "SCHEMA_INVALID"),
        (good | {"client_ref": "x" * 2000}, "SCHEMA_INVALID"),
        (good | {"parameters": good["parameters"] | {"negative_control": {"kind": "NOPE", "seed": 1}}}, "SCHEMA_INVALID"),
        (good | {"parameters": good["parameters"] | {"external_intelligence": {"mode": "NONE", "families": ["CVM_VLMO"]}}},
         "SCHEMA_INVALID"),
        (collection_request("stocks:REQ-C-2", parameters={"collector": "cvm-vlmo", "period": "26",
                                                          "observed_at": "2026-09-19T12:00:00Z"}), "SCHEMA_INVALID"),
    ):
        with pytest.raises(contract.ContractError) as error:
            contract.validate_request(bad)
        assert error.value.reason == reason
    with pytest.raises(contract.ContractError):
        contract.loads_strict(b"\xff")
    result = {
        "schema_version": contract.RESULT_SCHEMA, "result_id": "stocks:R", "request_id": "stocks:Q",
        "admission_id": "stocks:A", "experiment_id": "stocks:E", "research_id": "stocks:S", "hypothesis_id": "stocks:H",
        "request_type": contract.BACKTEST, "as_of": "2026-01-01T00:00:00Z", "result_state": "WATCH_NO_CAPITAL",
        "operational_state": "SUCCEEDED", "scientific_state": "SUPPORTED", "economic_state": "WATCH",
        "capital_permission": False, "trial_eligible": False, "produced_at": "2026-01-01T00:00:00Z",
        "core_facts": {"x": 1}, "ops_facts": {"x": 1}, "domain_facts": {"x": 1}, "provenance": {"x": 1},
    }
    assert contract.validate_result(result) is result
    for change in ({"capital_permission": True}, {"economic_state": "NO_EDGE"},
                   {"operational_state": "FAILED"}, {"scientific_state": "INCONCLUSIVE"},
                   {"result_state": "COLLECTION_RECORDED", "economic_state": "NOT_EVALUATED",
                    "scientific_state": "NOT_EVALUATED"},
                   {"trial_eligible": True}, {"core_facts": {"x": float("nan")}}):
        with pytest.raises(contract.ContractError):
            contract.validate_result(result | change)


def test_policy_and_readiness_fail_closed(tmp_path):
    env = build(tmp_path)
    policy = json.loads(env["policy"].read_text(encoding="utf-8"))
    for change in ({"owner": "CAIN"}, {"handlers": {"X": "y"}}, {"hypotheses": {"stocks:H7": {"hypothesis_family": "f",
                                                                                          "purpose": "p"}}},
                   {"requester_trust": "NETWORK"}, {"allowed_collectors": ["curl"]}):
        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps(policy | change), encoding="utf-8")
        with pytest.raises(ValueError):
            load_policy(bad)
    assert closed_hypotheses()["stocks:H17"].startswith("PAUSED")
    with pytest.raises(ReadinessError):
        classify({"matrix_version": "other"})
    matrix = json.loads(Path(__file__).resolve().parents[1].joinpath(
        "EXTERNAL_INTELLIGENCE_TRIAL_READINESS_MATRIX.json").read_text(encoding="utf-8"))
    axes = classify(matrix)
    assert axes["ready_families"] == []
    assert axes["families"]["CVM_FCA_IDENTITY"]["axes"]["trial_eligibility"] == "NOT_ELIGIBLE_SUPPORT_ROLE"
    assert axes["families"]["CVM_IPE_METADATA"]["axes"]["trial_eligibility"] == "NOT_ELIGIBLE"
    for family, entry in axes["families"].items():
        assert entry["axes"]["contract_use"] == "COLLECTION_ONLY", family


def test_io_helpers(tmp_path):
    target = tmp_path / "a" / "b.json"
    atomic_write(target, b'{"x": 1}')
    assert strict_json_loads(target.read_bytes()) == {"x": 1}
    with pytest.raises(ValueError):
        strict_json_loads('{"x": 1, "x": 2}')
    with pytest.raises(ValueError):
        strict_json_loads('{"x": Infinity}')


def test_executor_logical_identity_is_stable(tmp_path):
    env = build(tmp_path)
    store = AdmissionStore(env["state"] / "admission.sqlite", env["policy"])
    store.submit(request("stocks:REQ-ID-1"))
    context = store.admitted_context("stocks:REQ-ID-1")
    assert ResearchExecutor.logical_identity(context) == ResearchExecutor.logical_identity(context)
    assert panel()["schema"] == "stocks-pit-panel/1"
