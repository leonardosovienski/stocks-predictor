"""Measurement safeguards with hand-computable data, before historical observation."""
import copy
import math
import pytest

from compare_h20 import ARMS, adjusted, compare, join_period, summarize, verify_sources


def fixture():
    members = [{"ticker": f"T{i}", "cnpj": f"C{i}", "isin": f"I{i}"} for i in range(20)]
    arms = {a: {"selection_available": True, "ranking": copy.deepcopy(members),
                "members": copy.deepcopy(members[offset:offset+4])}
            for a, offset in zip(ARMS, (0, 4, 8))}
    signal = {"asof": "2020-03-31", "arms": arms}
    original = {"asof": signal["asof"], "entry": "2020-04-01", "exit": "2020-07-01",
                "members": [{**m, "selected": i < 4} for i, m in enumerate(members)]}
    marks = {k: v for k, v in original.items() if k != "members"}
    marks["members"] = [{"ticker": m["ticker"], "cnpj": m["cnpj"], "selected": i < 4,
                          "failed_entry": False, "return": i/100} for i, m in enumerate(members)]
    return signal, marks, original


def test_paired_means_and_symmetric_full_rotation_cost_are_hand_calculable():
    row = join_period(*fixture())
    assert row["returns"][ARMS[0]] == pytest.approx(.015)
    assert row["returns"][ARMS[1]] == pytest.approx(.055)
    assert row["returns"][ARMS[2]] == pytest.approx(.095)
    assert row["returns"]["COMMON_EQUAL_WEIGHT"] == pytest.approx(.095)
    assert adjusted(.1, .0018) == pytest.approx(110*0.9982/100.18 - 1)
    assert adjusted(.055, .0018)-adjusted(.015, .0018) == pytest.approx(.04*.9982/1.0018)


@pytest.mark.parametrize("defect", ["missing", "failed", "identity", "nan", "null"])
def test_even_unselected_bad_common_name_blocks_without_shrinking_universe(defect):
    signal, marks, original = fixture()
    if defect == "missing":
        marks["members"].pop()
    elif defect == "failed":
        marks["members"][-1].update(failed_entry=True, **{"return": 0})
    elif defect == "identity":
        original["members"][-1]["isin"] = "WRONG"
    else:
        marks["members"][-1]["return"] = math.nan if defect == "nan" else None
    row = join_period(signal, marks, original)
    assert row["status"] == "BLOCKED"
    assert row["returns"] == {}
    assert row["cells"][-1]["mark_return"] is None or any(c["mark_return"] is None for c in row["cells"])


def test_mismatched_universe_and_future_execution_rejected():
    signal, marks, original = fixture()
    signal["arms"][ARMS[1]]["ranking"].pop()
    with pytest.raises(ValueError, match="asymmetric"):
        join_period(signal, marks, original)
    signal, marks, original = fixture()
    marks["entry"] = signal["asof"]
    with pytest.raises(ValueError, match="noncausal"):
        join_period(signal, marks, original)


def test_missing_terminal_period_stays_in_denominator_and_prevents_shortened_cagr():
    signal, marks, original = fixture()
    first = join_period(signal, marks, original)
    signal["asof"] = "2020-06-30"
    missing = join_period(signal, None, None)
    result = summarize([first, missing], ARMS[0], .0018, [5000])
    assert result["expected_periods"] == 2
    assert result["available_periods"] == 1
    assert result["synthetic_path"] is None
    assert result["profit"] is None
    pair = compare([first, missing], ARMS[1], ARMS[0], lambda *a, **k: pytest.fail("gapped bootstrap"))
    assert pair["descriptive_unadjusted_bootstrap_95pct"] is None


def test_noncontiguous_observed_periods_cannot_be_compounded():
    first = join_period(*fixture())
    second = copy.deepcopy(first)
    second.update(asof="2020-09-30", entry="2020-10-01", exit="2021-01-04")
    assert summarize([first, second], ARMS[0], 0, [5000])["synthetic_path"] is None


def test_insufficient_features_do_not_become_zero_return():
    signal, marks, original = fixture()
    for a in ARMS:
        signal["arms"][a]["selection_available"] = False
    row = join_period(signal, marks, original)
    assert not row["eligible_signal"]
    assert row["returns"] == {}


def test_protocol_tampering_rejected_before_sources_are_read(tmp_path):
    protocol = tmp_path / "protocol.json"
    protocol.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="frozen comparison"):
        verify_sources(tmp_path, protocol)
