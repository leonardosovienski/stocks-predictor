"""STOCKS_PIT_ADVERSARIAL, STOCKS_UNIVERSE_IDENTITY and TEMPORAL_INTEGRITY vectors (frozen).

Each case breaks the positive panel on purpose (FROZEN_PARAMETERS pit_adversarial_vectors
PIT-01..PIT-15) and checks the PIT view the production handler uses
(stocks_predictor.research_pit.Panel, called by research_worker) or the whole circuit
through the installed entrypoint. One violation is enough to fail.
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys

import pytest

from conformance.fixtures import build, calendar, cli, panel, ready_matrix, request, write_request
from stocks_predictor.research_pit import DataQualityProblem, Panel, TemporalViolation
from stocks_predictor.research_readiness import classify, consumption_decision

UNIVERSE = {"top_n": 10, "liquidity_lookback_sessions": 20, "min_history_sessions": 40}
CAL = calendar()


def _panel(raw, minimum="PIT_RECONSTRUCTED"):
    return Panel(raw, as_of=raw["data_cutoff"], minimum_pit_class=minimum)


def _members(p: Panel, session: str) -> list[str]:
    return [m["security_id"] for m in p.universe(session, UNIVERSE)["members"]]


def _at(session, clock="21:30:00"):
    return f"{session}T{clock}Z"


def test_pit01_future_constituent_is_absent_until_its_listing_is_known():
    raw = panel()
    s = next(x for x in raw["securities"] if x["security_id"] == "S15")
    s["listing_available_at"] = _at(CAL[500])  # listed since day 0 but only known at session 500
    p = _panel(raw)
    assert "S15" not in _members(p, CAL[400]) and "S15" not in _members(p, CAL[500])
    assert "S15" in _members(p, CAL[501])


def test_pit02_future_ticker_does_not_relabel_before_it_is_known():
    p = _panel(panel())
    early = {m["security_id"]: m["ticker"] for m in p.universe(CAL[295], UNIVERSE)["members"]}
    late = {m["security_id"]: m["ticker"] for m in p.universe(CAL[305], UNIVERSE)["members"]}
    assert early.get("S12") == "TK123" and late.get("S12") == "NW123"
    raw = panel()
    event = next(e for e in raw["ticker_events"] if e["ticker"] == "NW123")
    event["available_at"] = _at(CAL[320])  # effective at 300, known only at 320
    p2 = _panel(raw)
    at_310 = {m["security_id"]: m["ticker"] for m in p2.universe(CAL[310], UNIVERSE)["members"]}
    assert at_310.get("S12") == "TK123"
    # identity is the security, not the label: membership is unchanged by the relabel
    assert _members(p2, CAL[310]) == _members(p, CAL[310])


def test_pit03_delisted_security_is_present_while_it_existed():
    p = _panel(panel())
    assert "S14" in _members(p, CAL[380])
    assert "S14" in _members(p, CAL[401])  # delisted at 400 but not yet known before 402's decision
    assert "S14" not in _members(p, CAL[420])
    assert p.label_close("S14", CAL[450]) == p.label_close("S14", CAL[400])  # last price, then cash


def test_pit04_bars_before_the_listing_are_ignored():
    p = _panel(panel())
    sessions, _closes, _vol, _late = p.closes_known("S13", CAL[260], CAL[260] + "T12:00:00Z")
    assert sessions and min(sessions) >= CAL[200]
    assert "S13" not in _members(p, CAL[196])  # listing known at 195 but effective at 200
    assert "S13" not in _members(p, CAL[230])  # listed, but fewer than 40 sessions of its own history


def test_pit05_pit06_future_cnpj_document_is_ignored_until_available():
    raw = panel()
    event = next(e for e in raw["identity_events"] if e["issuer_cnpj"].startswith("C99"))
    event["available_at"] = _at(CAL[380])  # reorganization effective at 350, CVM filing at 380
    p = _panel(raw)
    at_360 = {m["security_id"]: m["issuer_cnpj"] for m in p.universe(CAL[360], UNIVERSE)["members"]}
    at_390 = {m["security_id"]: m["issuer_cnpj"] for m in p.universe(CAL[390], UNIVERSE)["members"]}
    assert at_360["S11"].startswith("C11") and at_390["S11"].startswith("C99")


def test_pit07_pit08_late_delivery_and_backfill_are_invisible_before_they_arrive():
    base = _panel(panel())
    raw = panel()
    s02 = [b for b in raw["bars"] if b["security_id"] == "S02"]
    for bar in s02[250:320]:  # a whole block delivered late / backfilled at session 330
        bar["available_at"] = _at(CAL[330])
    p = _panel(raw)
    sessions, *_ = p.closes_known("S02", CAL[325], CAL[325] + "T12:00:00Z")
    assert CAL[260] not in sessions and CAL[249] in sessions
    late_universe = p.universe(CAL[325], UNIVERSE)
    assert late_universe["excluded"]["late_bars_ignored"] >= 70
    assert late_universe["max_available_used"] <= CAL[325] + "T12:00:00Z"
    # after arrival the view equals the on-time view
    assert p.universe(CAL[340], UNIVERSE)["universe_view_hash"] == base.universe(CAL[340], UNIVERSE)["universe_view_hash"]


def test_pit09_pit10_republication_uses_the_revision_known_at_decision():
    raw = panel()
    original = next(b for b in raw["bars"] if b["security_id"] == "S03" and b["session"] == CAL[300])
    revised = dict(original, close=original["close"] * 3, available_at=_at(CAL[330]))
    raw["bars"].append(revised)
    p = _panel(raw)
    _s, closes_310, *_ = p.closes_known("S03", CAL[310], CAL[310] + "T12:00:00Z")
    _s, closes_340, *_ = p.closes_known("S03", CAL[340], CAL[340] + "T12:00:00Z")
    index = _s.index(CAL[300])
    assert closes_310[index] == original["close"] and closes_340[index] == revised["close"]


@pytest.mark.parametrize("corrupt", [
    lambda bar: bar.update(available_at=bar["session"] + "T10:00:00Z"),   # before the session closed
    lambda bar: bar.update(available_at=None),                            # missing
    lambda bar: bar.update(available_at="2023-13-45T00:00:00Z"),          # malformed
    lambda bar: bar.update(available_at=bar["session"] + "T21:30:00-03:00"),  # not UTC
])
def test_pit11_corrupted_availability_is_a_temporal_violation(corrupt):
    raw = panel()
    corrupt(raw["bars"][1234])
    with pytest.raises(TemporalViolation):
        _panel(raw)


def test_pit12_pit15_declared_strict_but_effective_historical_is_never_consumed():
    matrix = ready_matrix("CVM_VLMO")
    entry = next(e for e in matrix["eligible_families"] if e["source"] == "CVM_VLMO")
    entry["protocol_effective_PIT"] = {"PIT_STRICT": 0, "PIT_RECONSTRUCTED": 0, "HISTORICAL_ONLY": 38621}
    axes = classify(matrix, model_bindings=("CVM_VLMO",))
    family = axes["families"]["CVM_VLMO"]
    assert family["declared_PIT"]["PIT_STRICT"] == 38621 and family["downgraded_from_declared"]
    assert family["axes"]["pit_storage"] == "HISTORICAL_ONLY_EFFECTIVE"
    assert family["axes"]["contract_use"] == "COLLECTION_ONLY"
    ok, reason = consumption_decision(axes, "CVM_VLMO")
    assert not ok and reason.startswith("FAMILY_EFFECTIVE_PIT_BELOW_THRESHOLD")
    # the price panel: a record type below the admitted minimum is never evaluated
    raw = panel()
    raw["pit_classes"]["bars"] = "HISTORICAL_ONLY"
    with pytest.raises(DataQualityProblem, match="PIT_CLASS_BELOW_MINIMUM"):
        _panel(raw)
    with pytest.raises(DataQualityProblem, match="PIT_CLASS_BELOW_MINIMUM"):
        _panel(panel(), minimum="PIT_STRICT")


def test_pit13_duplicate_official_record_identical_collapses_divergent_fails():
    raw = panel()
    raw["bars"].append(dict(raw["bars"][100]))
    p = _panel(raw)
    assert p.counters["duplicate_records_collapsed"] == 1
    assert p.universe(CAL[300], UNIVERSE)["universe_view_hash"] == _panel(panel()).universe(CAL[300], UNIVERSE)["universe_view_hash"]
    raw["bars"].append(dict(raw["bars"][100], close=raw["bars"][100]["close"] + 1))
    with pytest.raises(DataQualityProblem, match="conflicting duplicate bar"):
        _panel(raw)


@pytest.mark.parametrize("conflict", ["two_issuers_same_instant", "one_ticker_two_securities", "unknown_security"])
def test_pit14_identity_conflicts_are_data_quality_problems(conflict):
    raw = panel()
    if conflict == "two_issuers_same_instant":
        first = next(e for e in raw["identity_events"] if e["security_id"] == "S05")
        raw["identity_events"].append(dict(first, issuer_cnpj="C77.000.000/0001-05"))
    elif conflict == "one_ticker_two_securities":
        raw["ticker_events"].append({"security_id": "S06", "ticker": "TK053", "effective_on": CAL[0],
                                     "available_at": _at(CAL[0], "12:00:00")})
    else:
        raw["bars"].append(dict(raw["bars"][0], security_id="S99"))
    with pytest.raises(DataQualityProblem):
        _panel(raw)


def test_data_quality_problem_is_an_inconclusive_result_through_the_entrypoint(tmp_path):
    raw = panel()
    raw["dataset_version"] = "conformance-conflict-v1"
    raw["bars"].append(dict(raw["bars"][100], close=raw["bars"][100]["close"] + 1))
    env = build(tmp_path, extra_objects={("dataset", "conflict"): raw})
    code, lines = cli(env, "process", str(write_request(env, "dq", request("stocks:REQ-DQ-001", dataset="conflict"))))
    outcome = lines[0]
    assert code == 0 and outcome["result_state"] == "INCONCLUSIVE_DATA_QUALITY"
    assert (outcome["scientific_state"], outcome["economic_state"]) == ("NOT_EVALUATED", "NOT_EVALUATED")


def test_decision_never_uses_data_available_after_it():
    p = _panel(panel())
    for session in CAL[60::21]:
        uni = p.universe(session, UNIVERSE)
        assert uni["max_available_used"] is None or uni["max_available_used"] <= uni["decision_at"]


# ---- STOCKS_UNIVERSE_IDENTITY ------------------------------------------------------------

def test_universe_is_deterministic_across_three_fresh_processes():
    code = (
        "import json,sys\n"
        "sys.path.insert(0, sys.argv[1])\n"
        "from conformance.fixtures import panel, calendar\n"
        "from stocks_predictor.research_pit import Panel\n"
        "raw = panel(); cal = calendar()\n"
        "p = Panel(raw, as_of=raw['data_cutoff'], minimum_pit_class='PIT_RECONSTRUCTED')\n"
        "cfg = {'top_n': 10, 'liquidity_lookback_sessions': 20, 'min_history_sessions': 40}\n"
        "print(json.dumps([p.universe(s, cfg)['universe_view_hash'] for s in cal[60::21]]))\n"
    )
    tests_root = str(__import__("pathlib").Path(__file__).resolve().parents[1])
    outputs = {subprocess.run([sys.executable, "-c", code, tests_root], capture_output=True, text=True,
                              check=True).stdout.strip() for _ in range(3)}
    assert len(outputs) == 1 and json.loads(outputs.pop())


def test_universe_changes_only_through_events_available_at_decision():
    p = _panel(panel())
    raw = copy.deepcopy(panel())
    s = next(x for x in raw["securities"] if x["security_id"] == "S15")
    s["listing_available_at"] = _at(CAL[-1])  # a listing known only at the very end
    q = _panel(raw)
    for session in CAL[60:-2:21]:
        assert "S15" not in _members(q, session)
        assert _members(p, session) == _members(q, session) or "S15" in _members(p, session)


def test_ticker_and_cnpj_changes_preserve_security_identity():
    p = _panel(panel())
    before = p.universe(CAL[295], UNIVERSE)
    after = p.universe(CAL[365], UNIVERSE)
    ids_before = {m["security_id"] for m in before["members"]}
    ids_after = {m["security_id"] for m in after["members"]}
    assert {"S11", "S12"} <= ids_before and {"S11", "S12"} <= ids_after
    # one issuer, two share classes: only the more liquid class enters (dedup by CNPJ, not ticker prefix)
    assert not ({"S01", "S16"} <= ids_after)
