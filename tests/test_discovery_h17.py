import copy
import hashlib
import json
from pathlib import Path

import pytest

from stocks_predictor import discovery_h17 as h17


def test_first_observation_protocol_is_sealed():
    path = Path(__file__).parents[1]/"docs/research/2026-09-07-h17-discovery-protocol.json"
    protocol = json.loads(path.read_text(encoding="utf-8"))
    canonical = json.dumps(protocol, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    assert hashlib.sha256(canonical).hexdigest() == h17.PROTOCOL_SHA256
    assert protocol["family"] == "H17"
    assert protocol["nominal_trials_after_this_observation_minimum"] == 16


def event(day, factor, label="DESDOBRAMENTO"):
    return {"ticker": "AAAA3", "ex_date": day, "price_factor": factor, "label": label}


def identity(ticker="AAAA3"):
    return {ticker: [{"first_date": "2020-01-01", "last_date": "2021-12-31", "isin": "ISIN_A"}]}


def member():
    return {"ticker": "AAAA3", "isin": "ISIN_A", "cnpj": "1", "accruals": 0.01}


def test_ranks_average_ties_and_reverse_direction():
    assert h17.ranks([5, 2, 2, 7]) == [3, 1.5, 1.5, 4]
    assert h17.spearman([1, 2, 3], [3, 2, 1]) == pytest.approx(-1)
    assert h17.spearman([1, 1, 1], [1, 2, 3]) is None


@pytest.mark.parametrize("factor,expected", [(0.5, 2), (0.25, 4), (1/3, 3), (10, 0.1)])
def test_quantity_price_basis_inverse(factor, expected):
    values, issues = h17.adjustment_map([event("2021-02-15", factor)], [])
    assert 1/values["2021-02-15"] == pytest.approx(expected)
    assert not issues


def test_vivt_real_same_day_split_and_group_compose_without_legacy_double_count():
    # B3 VIVT3, last-cum 14/04/2025: +7900% shares and grouping 0.025.
    events = [event("2025-04-15", 1/80), event("2025-04-15", 40, "GRUPAMENTO")]
    factors, issues = h17.adjustment_map(events, [{"ex_date": "2025-04-15", "factor": 1/80,
                                                "type": "split", "approved_by": "historical"}])
    assert factors == {"2025-04-15": 0.5}
    assert not issues


def test_conflicting_sources_are_not_silently_chosen():
    _, issues = h17.adjustment_map([event("2021-02-15", 0.5)], [
        {"ex_date": "2021-02-15", "factor": 0.25, "type": "split", "approved_by": "historical"}
    ])
    assert issues == {"2021-02-15": ["CONFLICTING_CORPORATE_ACTION_FACTORS"]}


@pytest.mark.parametrize("ticker,day", [("MULT3", "2018-07-23"), ("TOTS3", "2020-05-04"),
                                      ("CSMG3", "2020-11-26")])
def test_real_legacy_rounded_thirds_match_b3_without_changing_b3(ticker, day):
    factors, issues = h17.adjustment_map([event(day, 1/3)], [
        {"ticker": ticker, "ex_date": day, "factor": 0.333333, "type": "split", "approved_by": "historical"}
    ])
    assert factors[day] == 1/3
    assert not issues


def test_real_vivt_legacy_net_factor_matches_b3_components():
    factors, issues = h17.adjustment_map(
        [event("2025-04-15", 1/80), event("2025-04-15", 40, "GRUPAMENTO")],
        [{"ex_date": "2025-04-15", "factor": 0.5, "type": "split", "approved_by": "historical"}])
    assert factors["2025-04-15"] == 0.5
    assert not issues


def test_split_adjustment_and_ex_date_entry_boundary():
    bars = {"AAAA3": {"2021-02-01": (100, 100), "2021-02-15": (50, 50), "2021-03-01": (55, 55)}}
    result = h17.score_outcome(member(), "2021-02-01", "2021-03-01", bars, identity(),
                               [event("2021-02-15", 0.5)], [])
    assert result["price_return"] == pytest.approx(0.1)
    # Buying after the ex-date adjustment creates no extra share entitlement.
    result = h17.score_outcome(member(), "2021-02-15", "2021-03-01", bars, identity(),
                               [event("2021-02-15", 0.5)], [])
    assert result["price_return"] == pytest.approx(0.1)


def test_missing_endpoint_is_retained_as_missing_not_zero():
    result = h17.score_outcome(member(), "2021-02-01", "2021-03-01", {}, identity(), [], [])
    assert result["price_return"] is None
    assert "MISSING_EXECUTION_ENDPOINT" in result["quality_reasons"]


@pytest.mark.parametrize("issue", ["identity", "unsupported", "gap"])
def test_corrupt_or_incomplete_outcomes_cannot_be_scored(issue):
    bars = {"AAAA3": {"2021-02-01": (100, 100), "2021-03-01": (100, 100)}}
    ids, events = identity(), []
    if issue == "identity":
        ids["AAAA3"][0]["last_date"] = "2021-02-28"
    elif issue == "unsupported":
        events = [event("2021-02-15", None, "CIS RED CAP")]
    else:
        bars["AAAA3"]["2021-03-01"] = (50, 50)
    result = h17.score_outcome(member(), "2021-02-01", "2021-03-01", bars, ids, events, [])
    assert result["price_return"] is None
    assert result["quality_reasons"]


def screen_inputs():
    members, bars, ids = [], {}, {}
    for i in range(20):
        ticker = f"T{i:03}3"
        members.append({"ticker": ticker, "isin": "ISIN_A", "cnpj": str(i), "accruals": i,
                        "filing": {"cnpj": str(i), "accruals": i,
                                    "available_at": "2021-01-30", "ref_date": "2020-12-31"},
                        "security_documents": [{"available_at": "2020-01-01"}]})
        bars[ticker] = {"2021-02-01": (100, 100), "2021-03-01": (100+i, 100+i)}
        ids.update(identity(ticker))
    dates = ["2021-01-29", "2021-02-01", "2021-02-26", "2021-03-01"]
    return [{"asof": "2021-01-29", "universe": members}], dates, bars, ids, {"events": [], "legacy_adjustments": []}


def test_future_financial_and_security_filings_block_observation():
    inputs = screen_inputs()
    with pytest.raises(ValueError, match="future financial"):
        h17.build_cross_sections(*inputs)
    for m in inputs[0][0]["universe"]:
        m["filing"]["available_at"] = "2021-01-29"
    inputs[0][0]["universe"][0]["security_documents"][0]["available_at"] = "2021-02-01"
    with pytest.raises(ValueError, match="future security"):
        h17.build_cross_sections(*inputs)


def test_next_open_selection_missingness_and_same_family_quality_verdict():
    inputs = screen_inputs()
    for m in inputs[0][0]["universe"]:
        m["filing"]["available_at"] = "2021-01-29"
    result = h17.build_cross_sections(*inputs)[0]
    assert result["entry"] == "2021-02-01"
    assert result["exit"] == "2021-03-01"
    assert [r["ticker"] for r in result["members"] if r["selected"]] == ["T0003", "T0013", "T0023", "T0033"]
    assert result["available_case_ic"] == pytest.approx(-1)
    damaged = copy.deepcopy(inputs)
    del damaged[2]["T0003"]["2021-03-01"]
    result = h17.build_cross_sections(*damaged)[0]
    assert result["complete_case_price_spread"] is None
    assert result["selected_names"] == 4  # No replacement for a missing selected outcome.
    summary = h17.summarize([result])
    assert summary["status"] == "INCONCLUSIVE_DATA_QUALITY"
    assert summary["overall"]["unscored_selected_cells"] == 1
    assert not summary["investable_alpha_claim"]


def test_existing_observation_is_never_overwritten(tmp_path):
    output = tmp_path / "observed.json"
    output.write_text("original", encoding="utf-8")
    with pytest.raises(FileExistsError, match="append-only"):
        h17.run("missing", "missing", "missing", "missing", "missing", output)
    assert output.read_text(encoding="utf-8") == "original"
