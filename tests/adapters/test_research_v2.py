"""Stage B adapter (stocks_predictor.adapters.research_v2) through the real adapter_api.

The frozen conformance environment (tests/conformance/fixtures.py, read-only reuse) provisions the operator policy
and objects; the adapter submits the task's canonical request bytes through ``Circuit.submit_request`` and re-reads
the authoritative result through ``Circuit.show``. Nothing here is envelope code: the V2 wrapping and the byte
identity check against ``show`` belong to the transport consumer (ecosystem-predictor).
"""

from __future__ import annotations

import hashlib
import json
from importlib.metadata import version

import pytest
from conformance.fixtures import build, request

from stocks_predictor.adapters import research_v2 as adapter
from stocks_predictor.research_contract import canonical

TASK_ID = "stocks:TASK-" + "0" * 32


def _task(request_id: str = "stocks:REQ-ADAPTER-001", **payload_overrides) -> dict:
    payload = request(request_id) | payload_overrides
    payload["client_ref"] = {"schema": adapter.CLIENT_REF_SCHEMA, "task_id": TASK_ID}
    return {"schema": adapter.TASK_SCHEMA, "domain": "stocks", "task_id": TASK_ID, "payload": payload}


def _config(env: dict) -> dict:
    return {"state": str(env["state"]), "policy": str(env["policy"]), "objects": str(env["objects"])}


def test_identity_names_the_installed_distribution_and_module():
    assert adapter.identity() == {"distribution": "stocks-predictor", "version": version("stocks-predictor"),
                                  "module": "stocks_predictor.adapters.research_v2"}
    assert adapter.DOMAIN == "stocks"


def test_request_bytes_are_the_canonical_payload_with_the_envelope_client_ref():
    task = _task()
    raw = adapter.request_bytes(task)
    assert raw == canonical(task["payload"])
    assert json.loads(raw)["client_ref"] == {"schema": "research-client-ref/2", "task_id": TASK_ID}


@pytest.mark.parametrize(
    "mutate",
    [
        lambda t: t.update(schema="research-task/1"),
        lambda t: t.update(domain="crypto"),
        lambda t: t.pop("payload"),
        lambda t: t.update(task_id=None),
        lambda t: t["payload"].pop("client_ref"),
        lambda t: t["payload"].update(client_ref={"schema": "research-client-ref/2", "task_id": "stocks:TASK-x"}),
    ],
)
def test_malformed_tasks_are_refused_before_the_domain(tmp_path, mutate):
    task = _task()
    mutate(task)
    config = {"state": str(tmp_path / "s"), "policy": str(tmp_path / "p.json"), "objects": str(tmp_path / "o")}
    with pytest.raises(adapter.AdapterRefusal):
        adapter.submit_task(task, config)
    assert not (tmp_path / "s").exists()


def test_submit_task_goes_through_the_adapter_api_and_the_reread_is_byte_identical(tmp_path):
    env = build(tmp_path)
    task = _task()
    outcome = adapter.submit_task(task, _config(env))
    assert outcome["status"] == "RESULT" and outcome["exit_code"] == 0
    assert outcome["submission_sha256"] == hashlib.sha256(adapter.request_bytes(task)).hexdigest()
    assert outcome["submission_file"] == f"research-task-v2:{TASK_ID}"
    assert outcome["client_ref"] == task["payload"]["client_ref"]
    assert outcome["capital_permission"] is False and outcome["result"]["capital_permission"] is False
    code, shown = adapter.reread(task["payload"]["request_id"], _config(env))
    assert code == 0 and shown["status"] == "RESULT"
    assert shown["result_sha256"] == hashlib.sha256(canonical(outcome["result"])).hexdigest()


def test_resubmitting_the_same_task_is_a_duplicate_with_the_same_authoritative_result(tmp_path):
    env = build(tmp_path)
    task = _task("stocks:REQ-ADAPTER-002")
    first = adapter.submit_task(task, _config(env))
    second = adapter.submit_task(task, _config(env))
    assert first["status"] == "RESULT" and second["status"] == "DUPLICATE"
    assert second["result_id"] == first["result_id"] and second["result"] == first["result"]
    assert second["client_ref"] == task["payload"]["client_ref"]


def test_a_request_the_domain_refuses_comes_back_unchanged(tmp_path):
    env = build(tmp_path)
    task = _task("stocks:REQ-ADAPTER-003", hypothesis_id="stocks:H9")
    outcome = adapter.submit_task(task, _config(env))
    assert outcome["status"] == "REJECTED" and outcome["reason"] == "HYPOTHESIS_CLOSED"
    assert adapter.reread("stocks:REQ-ADAPTER-003", _config(env))[0] == 3
