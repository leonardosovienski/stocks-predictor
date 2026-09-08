"""Complete synthetic books, not historical observations or estimates of alpha."""
from copy import deepcopy
from decimal import Decimal as D
import json

import pytest

from stocks_predictor.continuous_cash import run_continuous
from stocks_predictor.h20_continuous import (
    H20Policy, canonical_digest, make_plans, run_h20_book, validate_source_review,
)
from stocks_predictor.h20_research import sha256
from stocks_predictor.value_profitability import ARMS
from tests.test_continuous_cash import tape, dividend, bonus
from tests.test_corporate_auction_tax import auction


def fixture(capital=1000, tax_class="equity"):
    data = tape()
    data["capital"] = capital
    members = [{"ticker": f"A{i:02}", "isin": f"ID{i:02}", "lot": 100,
                "tax_class": tax_class} for i in range(20)]
    data["quotes"] = {(d, m["ticker"]): {**q, "isin": m["isin"]}
                      for (d, _), q in data["quotes"].items() for m in members}
    for p in data["plans"][:-1]:
        p["members"] = deepcopy(members)
    rows = [{**m, "cnpj": f"ISSUER{i}", "available_at": "2019-12-31", "rank": i+1}
            for i, m in enumerate(members)]
    rankings = {p["asof"]: deepcopy(rows) for p in data["plans"][:-1]}
    return data, rankings


def reorder(rankings, order):
    rows = {r["ticker"]: r for r in rankings["2020-01-31"]}
    rankings["2020-01-31"] = [{**rows[t], "rank": i+1} for i, t in enumerate(order)]


def price(data, predicate, value):
    for (day, ticker), quote in data["quotes"].items():
        if predicate(day, ticker):
            quote.update(standard=value, fractional=value, close=value)


@pytest.mark.parametrize("arm", ARMS)
def test_cash_entitlement_final_liquidation_and_uncharged_retention(arm):
    data, ranks = fixture()
    data["cash_events"] = [{**dividend(), "ticker": "A00", "isin": "ID00"}]
    r = run_h20_book(data, ranks, arm)
    # Four lots of 25 shares: sale 1,100 + paid 12.50 - initial 1,000.
    assert r["profit_excluding_unpaid_receivables"] == D("112.5")
    assert len(r["trades"]) == 8
    assert r["traded_notional_brl"] == 2100
    assert r["modeled_trading_cost_brl"] == 0
    assert r["terminal"]["unpaid_receivables"] == 0
    assert r["future_profit_projection"] is None
    assert r["signal_decisions"][-1]["targets"] == {}
    assert all(v["settled_cash"] >= 0 for v in r["snapshots"])


def test_new_sale_taxes_reserved_before_buys_and_dividend_paid_after_exit():
    data, ranks = fixture(5000, "bdr")
    price(data, lambda d, t: d >= "2020-01-31", "10")
    price(data, lambda d, t: d >= "2020-01-31" and t < "A04", "20")
    reorder(ranks, [f"A{i:02}" for i in [*range(4, 20), *range(4)]])
    data["cash_events"] = [{**dividend(), "ticker": "A00", "isin": "ID00"}]
    r = run_h20_book(data, ranks, ARMS[2])
    buys = [t for t in r["trades"] if t["date"] == "2020-02-03" and t["quantity"] > 0]
    # 500 shares bought for 5,000, sold for 10,000. Fixture BDR tax=750.
    # Only 9,250 can fund new buys; the pending dividend 125*0.5 cannot.
    assert [b["quantity"] for b in buys] == [250, 250, 250, 175]
    assert sum(t["gross"] for t in buys) == 9250
    assert sum(t["tax"] for t in r["tax_assessments"]) == 750
    assert r["profit_excluding_unpaid_receivables"] == D("4312.5")
    assert r["cleared_cash_on_last_obligation_date"] == D("9312.5")
    assert not r["unpaid_receivables"]


def test_planned_but_unfilled_name_is_not_retained_at_next_signal():
    data, ranks = fixture()
    price(data, lambda d, t: d == "2020-01-03" and t == "A03", "1001")
    reorder(ranks, [f"A{i:02}" for i in [0, 1, 2, 4, 3, *range(5, 20)]])
    r = run_h20_book(data, ranks, ARMS[2])
    first, second, _ = r["signal_decisions"]
    assert first["targets"]["A03"] == 25
    assert "A03" not in second["actual_incumbents"]
    assert set(second["targets"]) == {"A00", "A01", "A02", "A04"}
    assert any(t["ticker"] == "A04" and t["quantity"] > 0 for t in r["trades"])


def test_rank_retention_is_based_on_real_holdings_and_weight_band_suppresses_small_orders():
    data, ranks = fixture()
    price(data, lambda d, t: d >= "2020-01-31", "10")
    price(data, lambda d, t: d >= "2020-01-31" and t == "A00", "10.8")
    reorder(ranks, [f"A{i:02}" for i in [0, 1, 2, 4, 3, *range(5, 20)]])
    r = run_h20_book(data, ranks, ARMS[2])
    second = r["signal_decisions"][1]
    assert "A03" in second["targets"] and "A04" not in second["targets"]
    assert second["original_targets"]["A00"] == 23
    assert second["targets"]["A00"] == 25
    assert second["suppressed"] == (("A00", -2, D("21.6")),)
    assert not any(t["date"] == "2020-02-03" for t in r["trades"])
    assert sum(t["quantity"] for t in r["trades"] if t["date"] == "2020-03-03") == -100
    plain = run_h20_book(data, ranks, ARMS[1])
    assert "A03" not in plain["signal_decisions"][1]["targets"]
    assert plain["traded_notional_brl"] > r["traded_notional_brl"]


def test_unpaid_claim_does_not_fund_targets_or_terminal_cash():
    data, ranks = fixture()
    data["cash_events"] = [{**dividend("2020-04-30", "2020-05-04"),
                            "ticker": "A00", "isin": "ID00"}]
    r = run_h20_book(data, ranks, ARMS[2])
    assert r["profit_excluding_unpaid_receivables"] == 100
    assert r["profit_including_unpaid_receivables_at_face"] == D("112.5")
    assert r["unpaid_receivables"]["div-1"]["net"] == D("12.5")
    assert r["signal_decisions"][1]["sizing_capital_excluding_unpaid_claims"] == 1100


def test_reviewed_bonus_delivery_survives_policy_and_later_liquidation():
    data, ranks = fixture(2000)
    action = bonus()
    action.update(ticker="A00", isin="ID00")
    action["stocks"][0].update(ticker="A00", isin="ID00")
    data["actions"] = [action]
    r = run_h20_book(data, ranks, ARMS[2])
    assert r["signal_decisions"][1]["actual_incumbents"]["A00"]["quantity"] == 55
    assert r["profit_excluding_unpaid_receivables"] == 255  # 205 shares at 11.
    assert r["corporate_log"][0]["event"] == "bonus"


def test_locked_delivery_and_untransformed_signal_units_fail_closed():
    data, ranks = fixture(2000)
    action = bonus()
    action.update(ticker="A00", isin="ID00")
    action["stocks"][0].update(ticker="A00", isin="ID00", credit_date="2020-04-01")
    data["actions"] = [action]
    with pytest.raises(ValueError, match="delivered position"):
        run_h20_book(data, ranks, ARMS[2])
    action.update(ex_date="2020-01-03", terms_known_on="2020-01-02")
    with pytest.raises(ValueError, match="reviewed order transformation"):
        run_h20_book(data, ranks, ARMS[2])


def test_successor_and_fraction_auction_use_actual_basis_and_later_tax_dates():
    data, ranks = fixture(4000)
    # Four positions of 100; no intermediate strategy trade masks the auction.
    data["plans"].pop(1)
    _, action = auction()
    action.update(ticker="A00", isin="ID00")
    leg = action["stocks"][0]
    leg["ratio"] = ".065"
    leg["fraction_settlement"].update(gross_cash_per_fraction="500", fees_per_fraction="0", irrf_per_fraction="0")
    data["actions"] = [action]
    for day in data["sessions"]:
        data["quotes"][(day, "B")] = {"date": day, "isin": "B-ISIN", "standard": "100",
            "fractional": "100", "close": "100", "lot": 100}
    r = run_h20_book(data, ranks, ARMS[2])
    # 3,300 original equity sales + 600 successor + 250 auction - 25.96 tax - 4,000.
    assert r["profit_excluding_unpaid_receivables"] == D("124.04")
    assert r["signal_decisions"][-1]["actual_incumbents"]["B"]["quantity"] == 6
    # Repeating decimal: conservation is exact within the 28-digit context.
    assert abs(r["corporate_disposals"][0]["basis"] - D(1000)/13) < D("1e-23")
    assert all(type(t["quantity"]) is int for t in r["trades"])


def test_execution_quotes_cannot_rewrite_frozen_signal_targets():
    data, ranks = fixture()
    original = run_h20_book(data, ranks, ARMS[2])
    price(data, lambda d, t: d == "2020-01-03", "1001")
    shocked = run_h20_book(data, ranks, ARMS[2])
    assert original["signal_decisions"][0] == shocked["signal_decisions"][0]
    assert not any(t["date"] == "2020-01-03" for t in shocked["trades"])


@pytest.mark.parametrize("failure", ["coverage", "middle_quote", "future_rank", "identity", "missing_rank", "insufficient"])
def test_missing_evidence_and_noncausal_inputs_cannot_emit_partial_profit(failure):
    data, ranks = fixture()
    if failure == "coverage":
        data["coverage_ready"] = False
    elif failure == "middle_quote":
        del data["quotes"][("2020-02-10", "A00")]
    elif failure == "future_rank":
        ranks["2020-01-31"][0]["available_at"] = "2020-02-01"
    elif failure == "identity":
        ranks["2020-01-31"][0]["isin"] = "DIFFERENT_SECURITY"
    elif failure == "missing_rank":
        del ranks["2020-01-31"]
    else:
        ranks["2020-01-31"] = ranks["2020-01-31"][:19]
        data["plans"][1]["members"] = data["plans"][1]["members"][:19]
    with pytest.raises((ValueError, KeyError)):
        run_h20_book(data, ranks, ARMS[2])


@pytest.mark.parametrize("bad", ["empty", "negative", "foreign", "bool"])
def test_signal_policy_cannot_bypass_the_order_contract(bad):
    data = tape()
    def policy(plan, book, *args):
        members = deepcopy(plan["members"])
        quantities = {"A": 100}
        if bad == "empty":
            members, quantities = [], {}
        elif bad == "foreign":
            members[0]["isin"] = "OTHER"
        else:
            quantities["A"] = -1 if bad == "negative" else True
        book.cash += D(1000000)  # Cannot modify the real portfolio.
        return {"members": members, "targets": quantities}
    with pytest.raises(ValueError, match="order contract"):
        run_continuous(**data, selection_policy=policy)


def test_h19_default_has_identical_results_when_no_policy_is_supplied():
    data = tape()
    assert run_continuous(**data) == run_continuous(**data, selection_policy=None)
    assert "signal_decisions" not in run_continuous(**data)


def test_plan_builder_exposes_leading_gap_but_rejects_an_internal_gap():
    data, ranks = fixture()
    periods = [{"asof": p["asof"], "arms": {a: {"selection_available": True,
        "ranking": ranks[p["asof"]]} for a in ARMS}} for p in data["plans"][:-1]]
    gap = {"asof": "2019-12-30", "arms": {a: {"selection_available": False} for a in ARMS}}
    plans, _, omitted = make_plans({"periods": [gap, *periods]}, {"plans": {"comparison": data["plans"]}})
    assert len(plans) == 3 and omitted[0]["asof"] == "2019-12-30"
    with pytest.raises(ValueError, match="internal H20 signal gap"):
        make_plans({"periods": [periods[0], gap, periods[1]]}, {"plans": {"comparison": data["plans"]}})


def test_source_attestation_cannot_be_a_boolean_or_an_unbound_declaration(tmp_path):
    requirement = {"signals_sha256": "registered", "execution_manifest_sha256": "source",
                   "conservative_intervals_sha256": canonical_digest([["A", "ID", "start", "end"]]),
                   "scope": "continuous H20", "reviewed": False, "sources": []}
    assert validate_source_review(None, requirement)[0]["kind"].endswith("MISSING")
    path = tmp_path / "review.json"
    def save(row):
        path.write_text(json.dumps(row), encoding="utf-8")
    save({"reviewed": True})
    with pytest.raises(ValueError, match="exact required inputs"):
        validate_source_review(path, requirement)
    save(requirement)
    assert validate_source_review(path, requirement)[0]["kind"].endswith("UNREVIEWED")
    source = tmp_path / "reviewed-source.txt"
    source.write_text("SYNTHETIC evidence only", encoding="utf-8")
    review = {**requirement, "reviewed": True, "reviewer": "SYNTHETIC_REVIEWER",
              "reviewed_on": "2020-01-01", "sources": [{"path": source.name, "sha256": sha256(source)}]}
    save(review)
    assert not validate_source_review(path, requirement)
    source.write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="changed"):
        validate_source_review(path, requirement)
    review["sources"][0]["path"] = "../escape.txt"
    save(review)
    with pytest.raises(ValueError, match="outside review directory"):
        validate_source_review(path, requirement)


def test_policy_rejects_unknown_arm():
    with pytest.raises(ValueError, match="unregistered"):
        H20Policy("BEST_AFTER_LOOKING", {})
