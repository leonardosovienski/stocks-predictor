import copy
import hashlib
import json
from pathlib import Path

import pytest

from stocks_predictor import discovery_value as value
from stocks_predictor.disclosed_accounting import owner_accounts
from stocks_predictor.document_panel import capital_from_viewer


def test_protocol_fixed_before_first_value_observation():
    p = Path(__file__).parents[1]/"docs/research/2026-09-07-value-discovery-protocol.json"
    protocol = json.loads(p.read_text(encoding="utf-8"))
    canonical = json.dumps(protocol, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    assert hashlib.sha256(canonical).hexdigest() == value.PROTOCOL_SHA256
    assert protocol["search_budget"]["observed_evaluations_after_minimum"] == 21
    assert protocol["search_budget"]["new_configurations"] == 4
    assert not protocol["candidate_results_observed_before_registration"]


def fixture():
    filing = {"cnpj": "1", "ref_date": "2020-12-31", "document_version": 1,
              "received_at": "2021-03-01", "available_at": "2021-03-02", "source_sha256": "archive"}
    member = {"ticker": "AAAA3", "cnpj": "1", "isin": "BRAAAAACNOR0", "median_volume": 2_000_000,
              "filing": filing, "security_documents": [{"cnpj": "1", "available_at": "2020-01-02"}]}
    capital = {**filing, "status": "ACQUIRED", "document_id": "11", "basis_date": "2020-12-31",
               "preferred": 0, "outstanding_ordinary": 100, "rounding_unit_shares": 1, "source_sha256": "capital"}
    account = {**filing, "document_id": "11", "owner_earnings_brl": 100, "owner_equity_brl": 500,
               "earnings_source": {"period_start": "2020-01-01", "period_end": "2020-12-31", "archive_sha256": "archive"},
               "equity_sources": [{"archive_sha256": "archive"}]}
    bars = {"AAAA3": {"2020-12-30": (10, 10), "2021-03-31": (10, 10)}}
    identity = {"AAAA3": [{"first_date": "2020-01-01", "last_date": "2025-12-31", "isin": "BRAAAAACNOR0"}]}
    key = value.document_key(filing)
    return member, "2021-03-31", {key: capital}, {key: account}, bars, identity, [], []


def test_disclosed_value_uses_shares_not_free_float():
    result = value.value_feature(*fixture())
    assert result["H18"] == pytest.approx(0.1)
    assert result["H19"] == pytest.approx(0.5)
    assert result["capital_proxy_brl"] == 1000


def test_split_changes_units_without_creating_valuation_signal():
    args = fixture()
    args[4]["AAAA3"]["2021-03-31"] = (5, 5)
    args[6].append({"ex_date": "2021-02-01", "label": "DESDOBRAMENTO", "price_factor": 0.5})
    result = value.value_feature(*args)
    assert result["translated_reported_shares"] == 200
    assert result["H18"] == pytest.approx(0.1)


def test_future_prices_and_future_actions_do_not_change_signal():
    args = fixture()
    expected = value.value_feature(*args)
    args[4]["AAAA3"]["2022-01-01"] = (1, 1)
    args[6].append({"ex_date": "2022-01-01", "label": "SUBSCRICAO", "price_factor": None})
    assert value.value_feature(*args) == expected


@pytest.mark.parametrize("mutation", ["future_filing", "future_security", "wrong_capital_receipt", "wrong_archive"])
def test_document_mismatches_and_lookahead_rejected(mutation):
    args = fixture()
    if mutation == "future_filing":
        args[0]["filing"]["available_at"] = "2021-04-01"
    elif mutation == "future_security":
        args[0]["security_documents"][0]["available_at"] = "2021-04-01"
    elif mutation == "wrong_capital_receipt":
        next(iter(args[2].values()))["received_at"] = "2021-03-02"
    else:
        next(iter(args[3].values()))["earnings_source"]["archive_sha256"] = "wrong"
    with pytest.raises(ValueError):
        value.value_feature(*args)


def test_date_only_receipt_is_not_usable_same_day():
    args = list(fixture())
    args[1] = "2021-03-01"
    args[0]["filing"]["available_at"] = "2021-03-01"  # Even corrupt upstream availability cannot bypass receipt.
    with pytest.raises(ValueError, match="not public"):
        value.value_feature(*args)


@pytest.mark.parametrize("mutation,reason", [
    ("preferred", "NOT_SINGLE_ORDINARY_SHARE_CLASS"),
    ("missing", "NO_VALID_EXACT_DOCUMENT_CAPITAL"),
    ("unsupported_past", "PAST_UNMODELLED_CAPITAL_EVENT"),
    ("identity", "PAST_INSTRUMENT_IDENTITY_BREAK"),
    ("gap", "PAST_UNRESOLVED_OVERNIGHT_GT_30PCT"),
])
def test_causal_data_abstention_has_reason(mutation, reason):
    args = fixture()
    if mutation == "preferred":
        next(iter(args[2].values()))["preferred"] = 1
    elif mutation == "missing":
        args[2].clear()
    elif mutation == "unsupported_past":
        args[6].append({"ex_date": "2021-02-01", "price_factor": None, "label": "SUBSCRICAO"})
    elif mutation == "identity":
        args[5]["AAAA3"][0]["first_date"] = "2021-01-01"
    else:
        args[4]["AAAA3"]["2021-03-31"] = (2, 2)
    result = value.value_feature(*args)
    assert not result["eligible"]
    assert result["reason"] == reason


def test_missing_newest_earnings_has_no_zero_or_older_fallback():
    args = fixture()
    account = next(iter(args[3].values()))
    account.update(owner_earnings_brl=None, earnings_source=None)
    older = {**account, "document_version": 0, "owner_earnings_brl": 10000}
    args[3][value.document_key(older)] = older
    result = value.value_feature(*args)
    assert result["H18"] is None
    assert result["H19"] == 0.5


def test_nonannual_profit_not_compared_to_annual_profit():
    args = fixture()
    next(iter(args[3].values()))["earnings_source"]["period_start"] = "2020-10-01"
    assert value.value_feature(*args)["H18"] is None


@pytest.mark.parametrize("doc,ordinary,rounding", [("133944", 2853776040, 1), ("134335", 15749449000, 1000)])
def test_original_cvm_treasury_and_capital_units(doc, ordinary, rounding):
    p = Path(__file__).parent/"fixtures/real_integration"/f"capital-{doc}.html"
    row = capital_from_viewer(p.read_bytes(), {"ref_date": "2023-12-31"}, "fixture")
    assert row["outstanding_ordinary"] == ordinary
    assert row["rounding_unit_shares"] == rounding


def test_owner_attribution_uses_bank_layout_and_subtracts_nci():
    # Original BBAS DFP 2023, consolidated values in BRL; not the individual statement.
    bpp = {"2.07": {"account": "2.07", "description": "Patrimônio Líquido Consolidado", "value_brl": 173570326000},
           "2.07.09": {"account": "2.07.09", "description": "Participação dos Acionistas Não Controladores", "value_brl": 4335047000}}
    dre = {"3.11": {"account": "3.11", "description": "Lucro/Prejuízo Consolidado do Período", "value_brl": 33165591000},
           "3.11.01": {"account": "3.11.01", "description": "Atribuído a Sócios da Empresa Controladora", "value_brl": 29860965000}}
    result = owner_accounts(bpp, dre)
    assert result["owner_equity_brl"] == 169235279000
    assert result["owner_earnings_brl"] == 29860965000
    # Same owner semantics in older bank DRE 3.09, without a universal 3.11 assumption.
    older_layout = {k.replace("3.11", "3.09"): {**r, "account": r["account"].replace("3.11", "3.09")}
                    for k, r in dre.items()}
    assert owner_accounts(bpp, older_layout)["owner_earnings_brl"] == 29860965000
    del bpp["2.07.09"]
    assert owner_accounts(bpp, dre)["owner_equity_brl"] is None


def test_adverse_missing_scenario_assigns_same_return_in_both_cohorts():
    members = [{"ticker": "A", "factor": 3, "selected": True, "price_return": None},
               {"ticker": "B", "factor": 2, "selected": False, "price_return": 0.1},
               {"ticker": "C", "factor": 1, "selected": False, "price_return": None}]
    stats = value.period_statistics(members, 3)
    assert not stats["complete"]
    assert stats["complete_case_spread"] is None
    expected = -1-(-1+0.1+1)/3
    assert stats["adverse_missing_scenario_spread"] == pytest.approx(expected)
    assert stats["adverse_spread_after_72bp_per_month"] == pytest.approx((expected-0.0072)/3)


def test_quarterly_execution_begins_after_signal_and_holds_three_months():
    members = [{"ticker": f"A{i:02}3", "cnpj": str(i), "isin": str(i), "H18": i/100} for i in range(20)]
    dates = ["2021-03-31", "2021-04-01", "2021-04-30", "2021-05-03", "2021-05-31", "2021-06-01", "2021-06-30", "2021-07-01"]
    bars = {m["ticker"]: {d: (10, 10) for d in dates} for m in members}
    identity = {m["ticker"]: [{"first_date": dates[0], "last_date": dates[-1], "isin": m["isin"]}] for m in members}
    rows = value.observe([{"asof": dates[0], "members": members}], "H18", 3, dates, bars, identity,
                         {"events": [], "legacy_adjustments": []})
    assert rows[0]["entry"] == "2021-04-01"
    assert rows[0]["exit"] == "2021-07-01"
    assert {m["ticker"] for m in rows[0]["members"] if m["selected"]} == {"A163", "A173", "A183", "A193"}
    changed = copy.deepcopy(rows[0]["members"])
    changed[0]["price_return"] = None
    assert value.period_statistics(changed, 3)["complete_case_spread"] is None
