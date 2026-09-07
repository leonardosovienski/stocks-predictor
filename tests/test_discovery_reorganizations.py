from collections import defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from stocks_predictor import discovery_reorganizations as reorg

FIXTURE = Path(__file__).parent/"fixtures/reorganization_source_cases.json"


def real_case(ticker, entry, exit_day):
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    member = {"ticker": ticker, "isin": next(e["isin"] for e in data["events"] if e["ticker"] == ticker)}
    return reorg.score(member, entry, exit_day, data["bars"], data["identities"], defaultdict(list),
                       defaultdict(list), {}, data)


def synthetic():
    event = {"ticker": "OLD3", "isin": "OLD", "last_cum": "2020-01-03", "ex_date": "2020-01-06",
             "stocks": [{"ticker": "NEW3", "isin": "NEW", "ratio": 2.0, "credit_date": "2020-01-08"}],
             "cash": [{"amount_brl": 1.0, "payment_date": "2020-01-15", "label": "COMPULSORY_CASH"}],
             "removes_original": True, "covered_panel_labels": ["INCORPORACAO"], "source_names": ["synthetic"],
             "sources": [{"url": "test-fixture", "sha256": "fixture"}]}
    bars = {"OLD3": {"2020-01-02": (10., 10.), "2020-01-03": (10., 10.)},
            "NEW3": {"2020-01-06": (4.5, 4.5), "2020-01-07": (4.5, 4.5),
                     "2020-01-08": (4.5, 4.5), "2020-01-15": (4.5, 4.5), "2020-02-03": (5., 5.)}}
    identities = {s: [{"isin": i, "first_date": min(bars[s]), "last_date": max(bars[s])}]
                  for s, i in [("OLD3", "OLD"), ("NEW3", "NEW")]}
    return bars, identities, {"events": [event], "subscriptions": []}


def run_synthetic(bars, identities, terms, entry="2020-01-02", exit_day="2020-02-03", events=None):
    return reorg.score({"ticker": "OLD3", "isin": "OLD"}, entry, exit_day, bars, identities,
                       events or defaultdict(list), defaultdict(list), {}, terms)


def test_real_golden_quotes_are_exact_original_b3_prices_and_identities():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    raw = FIXTURE.with_suffix(".txt").read_bytes().splitlines()
    assert len(raw) == 131
    for line in raw:
        ticker = line[12:24].decode("ascii").strip()
        d = line[2:10].decode("ascii")
        day = f"{d[:4]}-{d[4:6]}-{d[6:]}"
        factor = int(line[210:217])
        assert data["bars"][ticker][day] == [int(line[56:69])/100/factor, int(line[108:121])/100/factor]
        assert reorg.identity_at(data["identities"], ticker, day) == line[230:242].decode("ascii")


def test_gndi_final_ratio_and_both_gross_receivables_are_preserved():
    result = real_case("GNDI3", "2022-02-01", "2022-03-02")
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))["bars"]
    expected = (5.24364185943*data["HAPV3"]["2022-03-02"][0]+5.16614751932+1.613026961)/data["GNDI3"]["2022-02-01"][0]-1
    assert result["diagnostic_return"] == pytest.approx(expected)
    assert not result["quality_reasons"]
    assert len(result["mark"]["gross_cash"]) == 2
    assert all(c["status_at_exit_open"] == "UNPAID_RECEIVABLE_AT_EXIT_OPEN" for c in result["mark"]["gross_cash"])


def test_soma_exit_on_successor_first_trade_marks_uncredited_entitlement():
    result = real_case("SOMA3", "2024-07-01", "2024-08-01")
    assert result["diagnostic_return"] is not None
    assert result["mark"]["stocks"][0]["quantity"] == 0.121695988348
    assert result["mark"]["stocks"][0]["credit_date"] == "2024-08-05"
    assert not result["mark"]["stocks"][0]["physical_credit_verified_before_exit"]


def test_soma_entry_after_last_trade_cannot_receive_merger_proceeds():
    result = real_case("SOMA3", "2024-08-01", "2024-09-02")
    assert result["diagnostic_return"] == 0
    assert result["mark"] == {"uninvested_fraction": 1.0}
    assert not result["entitlement_ledger"]


def test_carrefour_default_cash_redemption_has_no_phantom_stock_sale():
    result = real_case("CRFB3", "2025-04-01", "2025-07-01")
    entry = json.loads(FIXTURE.read_text(encoding="utf-8"))["bars"]["CRFB3"]["2025-04-01"][0]
    assert result["diagnostic_return"] == pytest.approx(8.5/entry-1)
    assert result["mark"]["stocks"] == []
    assert result["mark"]["gross_cash"][0]["payment_date"] == "2025-06-10"


def test_natura_does_not_double_or_miss_one_to_one_exchange():
    result = real_case("NTCO3", "2025-07-01", "2025-08-01")
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))["bars"]
    assert result["diagnostic_return"] == pytest.approx(data["NATU3"]["2025-08-01"][0]/data["NTCO3"]["2025-07-01"][0]-1)
    assert result["mark"]["stocks"][0]["quantity"] == 1


@pytest.mark.parametrize("exit_day,paid", [("2020-01-07",False),("2020-01-15",False),("2020-02-03",True)])
def test_payment_day_open_is_still_a_receivable_not_reinvestment_cash(exit_day, paid):
    result = run_synthetic(*synthetic(), exit_day=exit_day)
    assert result["diagnostic_return"] is not None
    assert (result["mark"]["gross_cash"][0]["status_at_exit_open"] == "PAYMENT_SCHEDULE_PRECEDES_EXIT") == paid
    assert result["mark"]["receivables_are_not_spendable"]


def test_missing_quote_is_not_automatically_zero_return():
    bars, identities, terms = synthetic()
    del bars["OLD3"]["2020-01-02"]
    result = run_synthetic(bars, identities, terms)
    assert result["diagnostic_return"] is None
    assert "MISSING_EXECUTION_ENDPOINT:OLD3" in result["quality_reasons"]


def test_wrong_successor_identity_stays_unresolved():
    bars, identities, terms = synthetic()
    identities["NEW3"][0]["isin"] = "DIFFERENT_ISSUER"
    result = run_synthetic(bars, identities, terms)
    assert result["diagnostic_return"] is None
    assert "MISSING_OR_WRONG_SUCCESSOR_AT_CONVERSION:NEW3" in result["quality_reasons"]


def test_compulsory_conversion_does_not_mask_unrelated_jump():
    bars, identities, terms = synthetic()
    bars["NEW3"]["2020-02-03"] = (10., 10.)
    result = run_synthetic(bars, identities, terms)
    assert result["diagnostic_return"] is None
    assert "UNRESOLVED_OVERNIGHT_GT_30PCT:NEW3" in result["quality_reasons"]


def test_spinoff_keeps_original_stock_and_adds_successor_once():
    bars, identities, terms = synthetic()
    bars["OLD3"].update({d:(6.,6.) for d in bars["NEW3"]})
    identities["OLD3"][0]["last_date"] = "2020-02-03"
    event = terms["events"][0]
    event["stocks"][0]["ratio"] = 2/3
    event["stocks"].append({"ticker":"OLD3", "isin":"OLD", "ratio":1, "credit_date":None})
    event["removes_original"] = False
    result = run_synthetic(bars, identities, terms)
    assert result["diagnostic_return"] == pytest.approx((6+2/3*5+1)/10-1)
    old = next(s for s in result["mark"]["stocks"] if s["ticker"] == "OLD3")
    assert old["quantity"] == 1
    assert old["physical_credit_verified_before_exit"]


def test_subscription_never_creates_free_shares_or_debits_external_capital():
    bars = {"OLD3":{"2020-01-02":(10.,10.),"2020-01-03":(9.,9.),"2020-02-03":(9.,9.)}}
    identities = {"OLD3":[{"isin":"OLD","first_date":"2020-01-02","last_date":"2020-02-03"}]}
    event = {"ticker":"OLD3","isin":"OLD","ex_date":"2020-01-03","label":"SUBSCRICAO","price_factor":None}
    events = defaultdict(list, OLD3=[event])
    result = run_synthetic(bars, identities, {"events":[],"subscriptions":[event]}, events=events)
    assert result["diagnostic_return"] == pytest.approx(-.1)
    assert result["mark"]["stocks"][0]["quantity"] == 1
    assert result["mark"]["gross_cash"] == []
    assert result["quality_notes"][0]["code"] == "RIGHTS_ZERO_MARK_NO_EXERCISE_NO_SALE"
    unknown = run_synthetic(bars, identities, {"events":[],"subscriptions":[]}, events=events)
    assert unknown["diagnostic_return"] is None


def test_duplicate_terms_and_nonfinite_ratios_are_rejected():
    terms = synthetic()[2]
    reorg.validate_terms(terms)
    invalid = deepcopy(terms)
    invalid["events"].append(deepcopy(invalid["events"][0]))
    with pytest.raises(ValueError, match="duplicate"):
        reorg.validate_terms(invalid)
    invalid = deepcopy(terms)
    invalid["events"][0]["stocks"][0]["ratio"] = float("nan")
    with pytest.raises(ValueError, match="ratio"):
        reorg.validate_terms(invalid)


def test_split_before_conversion_changes_both_stock_and_cash_entitlements():
    bars, identities, terms = synthetic()
    bars["OLD3"]["2020-01-03"] = (5.,5.)
    bars["NEW3"] = {d:(2.25,2.25) for d in bars["NEW3"]}
    bars["NEW3"]["2020-02-03"] = (2.5,2.5)
    terms["events"][0]["cash"][0]["amount_brl"] = .5
    events = defaultdict(list, OLD3=[{"ex_date":"2020-01-03", "label":"DESDOBRAMENTO", "price_factor":.5}])
    result = run_synthetic(bars, identities, terms, events=events)
    assert result["diagnostic_return"] == pytest.approx(.1)
    assert result["mark"]["stocks"][0]["quantity"] == 4
    assert result["mark"]["gross_cash"][0]["total_brl"] == 1


def test_known_conversion_does_not_clear_simultaneous_unmodelled_action():
    events = defaultdict(list, OLD3=[{"ex_date":"2020-01-06", "label":"OTHER_ACTION", "price_factor":None}])
    result = run_synthetic(*synthetic(), events=events)
    assert result["diagnostic_return"] is None
    assert "UNRESOLVED_SIMULTANEOUS_REORGANIZATION_ACTION" in result["quality_reasons"]


def test_new_policy_is_separately_registered_and_counted():
    path = Path(__file__).parents[1]/"docs/research/2026-09-07-reorganization-protocol.json"
    protocol = json.loads(path.read_text(encoding="utf-8"))
    canonical = json.dumps(protocol,sort_keys=True,separators=(",", ":"),ensure_ascii=False).encode()
    assert hashlib.sha256(canonical).hexdigest() == reorg.PROTOCOL_SHA256
    assert protocol["budget"]["historical_return_evaluations_minimum_after"] == 29
    assert protocol["budget"]["nominal_configurations_minimum_after"] == 24
