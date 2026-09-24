"""Stocks-specific rows of the frozen FAILURE_MATRIX (F-ART-1, F-DSK-1, F-LCK-1, F-ORD-1).

Faults are injected at the edge: the real worker dies mid-write under predictor_ops, the
disk refuses the result write, another process holds the state database, and an old
request is re-delivered after a newer one. Nothing mocks predictor_core or predictor_ops.
"""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import time

from conformance.fixtures import build, cli, experiments, ops_runtime, request, write_request


def _only(lines):
    assert len(lines) == 1, lines
    return lines[0]


def _results(env) -> int:
    with sqlite3.connect(env["state"] / "results.sqlite") as db:
        return db.execute("SELECT count(*) FROM results").fetchone()[0]


def _ops_successes(env) -> int:
    total = 0
    for events in ops_runtime(env).glob("stocks-research-*/events.jsonl"):
        for line in events.read_text(encoding="utf-8").splitlines():
            if line.strip() and json.loads(line).get("run_status") == "SUCCEEDED":
                total += 1
    return total


def test_worker_dies_mid_effect_write_leaves_no_effect_and_retry_produces_one(tmp_path):
    env = build(tmp_path)
    path = write_request(env, "r", request("stocks:REQ-PARTIAL-001"))
    code, lines = cli(env, "process", str(path), fault="ops_worker_partial_effect")
    failed = _only(lines)
    assert code == 3 and failed["status"] == "OPS_FAILED_RETRYABLE"
    assert not list(experiments(env).rglob("domain-effect.json"))
    assert not list(experiments(env).rglob("trials-v2.json"))  # no trial before the effect exists
    assert _results(env) == 0
    code, lines = cli(env, "process", str(path))
    assert code == 0 and _only(lines)["status"] == "RESULT"
    assert len(list(experiments(env).rglob("domain-effect.json"))) == 1
    assert _ops_successes(env) == 1 and _results(env) == 1
    assert cli(env, "reconcile")[0] == 0


def test_disk_full_on_result_write_stores_nothing_and_retry_stores_once(tmp_path):
    env = build(tmp_path)
    path = write_request(env, "r", request("stocks:REQ-DISK-001"))
    code, lines = cli(env, "process", str(path), fault="disk_write_error")
    failed = _only(lines)
    assert code == 3 and failed["status"] == "STORAGE_FAILED_RETRYABLE"
    assert failed["scientific_state"] == "NOT_EVALUATED" and failed["economic_state"] == "NOT_EVALUATED"
    assert not list(experiments(env).rglob("research-result.json"))
    assert _results(env) == 0
    code, lines = cli(env, "process", str(path))
    outcome = _only(lines)
    assert code == 0 and outcome["status"] == "RESULT"
    assert _ops_successes(env) == 1 and _results(env) == 1  # Ops is not re-run: the effect was kept
    code, lines = cli(env, "show", "stocks:REQ-DISK-001")
    assert code == 0 and _only(lines)["result"]["result_id"] == outcome["result_id"]


def _hold_exclusive_lock(database, seconds: float) -> subprocess.Popen:
    code = (
        "import sqlite3,sys,time\n"
        "db=sqlite3.connect(sys.argv[1], timeout=1, isolation_level=None)\n"
        "db.execute('BEGIN EXCLUSIVE')\n"
        "print('LOCKED', flush=True)\n"
        "time.sleep(float(sys.argv[2]))\n"
        "db.execute('ROLLBACK')\n"
    )
    holder = subprocess.Popen([sys.executable, "-c", code, str(database), str(seconds)],
                              stdout=subprocess.PIPE, text=True)
    assert holder.stdout.readline().strip() == "LOCKED"
    return holder


def test_db_lock_shorter_than_busy_timeout_waits_and_succeeds(tmp_path):
    env = build(tmp_path)
    first = write_request(env, "a", request("stocks:REQ-LOCK-000"))
    assert cli(env, "process", str(first))[0] == 0
    holder = _hold_exclusive_lock(env["state"] / "admission.sqlite", 3)
    started = time.monotonic()
    code, lines = cli(env, "process", str(write_request(env, "b", request("stocks:REQ-LOCK-001", dataset="case_a"))))
    holder.wait(30)
    assert code == 0 and _only(lines)["status"] == "RESULT"
    assert time.monotonic() - started >= 2.5
    assert _results(env) == 2


def test_db_lock_longer_than_busy_timeout_is_retryable_and_leaves_no_partial_state(tmp_path):
    env = build(tmp_path)
    first = write_request(env, "a", request("stocks:REQ-LOCK-100"))
    assert cli(env, "process", str(first))[0] == 0
    holder = _hold_exclusive_lock(env["state"] / "admission.sqlite", 45)
    path = write_request(env, "b", request("stocks:REQ-LOCK-101", dataset="case_a"))
    try:
        code, lines = cli(env, "process", str(path))
    finally:
        holder.kill()
        holder.wait(30)
    outcome = _only(lines)
    assert code == 3 and outcome["status"] == "STATE_BUSY_RETRYABLE"
    with sqlite3.connect(env["state"] / "admission.sqlite") as db:
        assert db.execute("SELECT count(*) FROM request_inbox WHERE request_id='stocks:REQ-LOCK-101'").fetchone()[0] == 0
    code, lines = cli(env, "process", str(path))
    assert code == 0 and _only(lines)["status"] == "RESULT"
    assert _results(env) == 2


def test_out_of_order_redelivery_never_changes_the_newer_result(tmp_path):
    env = build(tmp_path)
    old = write_request(env, "old", request("stocks:REQ-ORDER-001", dataset="case_a"))
    new = write_request(env, "new", request("stocks:REQ-ORDER-002"))
    assert cli(env, "process", str(new))[0] == 0
    newer = _only(cli(env, "show", "stocks:REQ-ORDER-002")[1])["result_sha256"]
    code, lines = cli(env, "process", str(old))
    assert code == 0 and _only(lines)["status"] == "RESULT"
    code, lines = cli(env, "process", str(new), str(old))
    assert code == 0 and [line["status"] for line in lines] == ["DUPLICATE", "DUPLICATE"]
    assert _only(cli(env, "show", "stocks:REQ-ORDER-002")[1])["result_sha256"] == newer
    assert _results(env) == 2 and _ops_successes(env) == 2
