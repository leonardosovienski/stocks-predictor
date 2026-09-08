from copy import deepcopy
from decimal import Decimal as D

import pytest

from stocks_predictor.buffered_rebalance import book_digest, execute_rebalance, freeze_rebalance
from stocks_predictor.h20_research import signal_diagnostics, verify_sources
from stocks_predictor.retail_cash import Holding, RetailBook
from stocks_predictor.value_profitability import (
    ARMS, accounting_index, prepare_snapshot, rank_snapshot, select_members,
)


def financial_fixture():
    source = {"archive_sha256": "a" * 64, "period_end": "2020-12-31", "value_brl": 10,
              "period_start": "2020-01-01"}
    account = {"cnpj": "issuer", "ref_date": "2020-12-31", "document_version": 1,
               "document_id": "doc", "received_at": "2021-03-23", "owner_earnings_brl": 10,
               "owner_equity_brl": 100, "earnings_source": source,
               "equity_sources": [{**source, "value_brl": 120}, {**source, "value_brl": 20}]}
    member = {"ticker": "A", "cnpj": "issuer", "isin": "I", "eligible": True,
              "ref_date": "2020-12-31", "document_version": 1, "document_id": "doc",
              "available_at": "2021-03-24", "capital_proxy_brl": 1000,
              "signal_close": 10, "H18": .01, "H19": .1,
              "accounting_source_sha256": "a" * 64, "capital_source_sha256": "b" * 64}
    return {"asof": "2021-03-31", "members": [member]}, account


def test_owner_profitability_from_matching_annual_source_and_negative_profit_is_ranked():
    snapshot, account = financial_fixture()
    row = prepare_snapshot(snapshot, accounting_index([account]))["members"][0]
    assert row["value"] == D(".1") and row["profitability"] == D(".1")
    account["owner_earnings_brl"] = -10
    account["earnings_source"]["value_brl"] = -10
    snapshot["members"][0]["H18"] = -.01
    row = prepare_snapshot(snapshot, accounting_index([account]))["members"][0]
    assert row["eligible"] and row["profitability"] == D("-.1")


@pytest.mark.parametrize("change", ["future", "version", "hash", "numerator", "source_arithmetic", "nan"])
def test_financial_provenance_and_future_data_are_not_repaired_silently(change):
    snapshot, account = financial_fixture()
    member = snapshot["members"][0]
    if change == "future":
        member["available_at"] = "2021-04-01"
    elif change == "version":
        account["document_id"] = "different-doc"
    elif change == "hash":
        account["earnings_source"]["archive_sha256"] = "c" * 64
    elif change == "numerator":
        member["H18"] = .5
    elif change == "source_arithmetic":
        account["equity_sources"][1]["value_brl"] = 0
    else:
        account["owner_earnings_brl"] = "NaN"
    with pytest.raises(ValueError):
        prepare_snapshot(snapshot, accounting_index([account]))


@pytest.mark.parametrize("missing", ["document", "earnings", "equity", "annual", "stale"])
def test_unavailable_financial_cells_remain_explicit(missing):
    snapshot, account = financial_fixture()
    if missing == "earnings":
        account["owner_earnings_brl"] = None
    elif missing == "equity":
        account["owner_equity_brl"] = 0
    elif missing == "annual":
        account["earnings_source"]["period_start"] = "2020-10-01"
    elif missing == "stale":
        snapshot["asof"] = "2023-03-31"
    result = prepare_snapshot(snapshot, accounting_index([] if missing == "document" else [account]))
    assert len(result["members"]) == 1
    assert result["members"][0]["eligible"] is False
    assert result["members"][0]["reason"]
    assert "value" not in result["members"][0]


def test_equal_rank_blend_and_ties_are_deterministic_and_use_same_universe():
    rows = [{"ticker": t, "isin": t, "eligible": True, "value": v, "profitability": p}
            for t, v, p in [("A", 40, 1), ("B", 30, 4), ("C", 20, 3), ("D", 10, 2)]]
    snapshot = {"members": rows}
    ranks = rank_snapshot(snapshot, ARMS[1])
    assert [r["ticker"] for r in ranks] == ["B", "A", "C", "D"]
    assert [r["combined_rank_score"] for r in ranks] == [D("1.5"), D("2.5"), D("2.5"), D("3.5")]
    rows.reverse()
    assert rank_snapshot(snapshot, ARMS[1]) == ranks
    for row in rows:
        row["value"] = 1
    assert {r["value_rank"] for r in rank_snapshot(snapshot, ARMS[0])} == {D("2.5")}
    assert [{r["ticker"] for r in rank_snapshot(snapshot, arm)} for arm in ARMS] == [set("ABCD")] * 3


def ranked_twenty():
    return [{"ticker": f"S{i:02}", "isin": f"I{i}", "rank": i} for i in range(1, 21)]


def test_rank_buffer_keeps_near_cutoff_names_but_forces_departures_and_limits_count():
    ranked = ranked_twenty()
    incumbents = {f"S{i:02}": f"I{i}" for i in (2, 5, 6, 7)}
    chosen = select_members(ranked, incumbents, buffered=True)
    assert [r["rank"] for r in chosen["members"]] == [1, 2, 5, 6]
    assert chosen["forced_exit_tickers"] == ["S07"]
    assert [r["rank"] for r in select_members(ranked, incumbents)["members"]] == [1, 2, 3, 4]
    crowded = {r["ticker"]: r["isin"] for r in ranked[:7]}
    assert [r["rank"] for r in select_members(ranked, crowded, buffered=True)["members"]] == [1, 2, 3, 4]
    wrong = {"S05": "OLD_ISIN"}
    assert "S05" in select_members(ranked, wrong, buffered=True)["forced_exit_tickers"]
    assert select_members(ranked[:19], incumbents, buffered=True)["selection_available"] is False


def book_fixture():
    book = RetailBook(20, "2021-03-31")
    book.positions = {"A": Holding("IA", 510, D(5100)), "B": Holding("IB", 490, D(4900))}
    members = [{"ticker": t, "isin": "I" + t, "lot": 100, "tax_class": "equity"} for t in "AB"]
    signals = {t: {"date": book.day, "isin": "I" + t, "close": 10, "lot": 100} for t in "AB"}
    execution = {t: {"date": "2021-04-01", "isin": "I" + t, "standard": 10, "fractional": 10} for t in "AB"}
    return book, members, signals, execution


def freeze(book, members, signals, buffered=True):
    return freeze_rebalance(book, members, signals, "2021-04-01", "2021-04-05", 10000, buffered=buffered)


def test_paired_books_avoid_small_trades_with_independent_cost_arithmetic():
    original, members, signals, quotes = book_fixture()
    plain, buffered = deepcopy(original), deepcopy(original)
    plain_plan, buffer_plan = freeze(plain, members, signals, False), freeze(buffered, members, signals)
    assert dict(plain_plan.targets) == {"A": 500, "B": 500}
    assert dict(buffer_plan.targets) == {"A": 510, "B": 490}
    plain.advance("2021-04-01"); buffered.advance("2021-04-01")
    a = execute_rebalance(plain, plain_plan, quotes, ".0018", order_units_reviewed=True)
    b = execute_rebalance(buffered, buffer_plan, quotes, ".0018", order_units_reviewed=True)
    assert [r["quantity"] for r in a["trades"]] == [-10, 10]
    assert a["traded_notional_brl"] == 200
    assert a["modeled_cost_brl"] == D(".36") and a["cleared_cash_brl"] == D("19.64")
    assert b["trades"] == [] and b["modeled_cost_brl"] == 0 and b["cleared_cash_brl"] == 20
    assert b["profit"] is None
    assert buffered.positions == original.positions


def test_weight_band_does_not_suppress_small_mandatory_exit_or_liquidation():
    book, members, signals, quotes = book_fixture()
    book.positions["C"] = Holding("IC", 1, D(10))
    signals["C"] = {"date": book.day, "isin": "IC", "close": 10, "lot": 100}
    quotes["C"] = {"date": "2021-04-01", "isin": "IC", "standard": 10, "fractional": 10}
    plan = freeze(book, members, signals)
    book.advance("2021-04-01")
    result = execute_rebalance(book, plan, quotes, ".0018", order_units_reviewed=True)
    assert [(r["ticker"], r["quantity"]) for r in result["trades"]] == [("C", -1)]
    book, _, signals, quotes = book_fixture()
    plan = freeze(book, [], signals)
    book.advance("2021-04-01")
    execute_rebalance(book, plan, quotes, ".0018", order_units_reviewed=True)
    assert book.positions == {}


@pytest.mark.parametrize("failure", ["missing_quote", "identity", "stale_basis", "tax_reserve", "units", "cost"])
def test_even_suppressed_trades_fail_atomically_on_bad_state(failure):
    book, members, signals, quotes = book_fixture()
    plan = freeze(book, members, signals)
    book.advance("2021-04-01")
    if failure == "missing_quote":
        del quotes["B"]
    elif failure == "identity":
        quotes["B"]["isin"] = "different"
    elif failure == "stale_basis":
        book.positions["A"].basis += 1
    elif failure == "tax_reserve":
        book.cash_buffer += 1
    before = book_digest(book)
    with pytest.raises((ValueError, KeyError)):
        execute_rebalance(book, plan, quotes, "NaN" if failure == "cost" else ".0018",
                          order_units_reviewed=failure != "units")
    assert book_digest(book) == before


def test_signal_quotes_capital_and_identity_cannot_use_future_or_receivables():
    book, members, signals, _ = book_fixture()
    signals["A"]["date"] = "2021-04-01"
    with pytest.raises(ValueError, match="signal quote"):
        freeze(book, members, signals)
    signals["A"]["date"] = book.day
    members[0]["isin"] = "NEW"
    with pytest.raises(ValueError, match="conversion"):
        freeze(book, members, signals)
    empty = RetailBook(0, "2021-03-31")
    empty.rights["later"] = {"available_on": "2021-04-06", "net": D(10000)}
    with pytest.raises(ValueError, match="sizing capital"):
        freeze(empty, [], {})


def test_unaffordable_gap_buy_remains_unfilled_and_keeps_integer_funding():
    book = RetailBook(100, "2021-03-31")
    members = [{"ticker": "A", "isin": "I", "lot": 100}]
    signals = {"A": {"date": book.day, "isin": "I", "close": 10}}
    plan = freeze_rebalance(book, members, signals, "2021-04-01", "2021-04-05", 100, buffered=True)
    book.advance("2021-04-01")
    quote = {"A": {"date": book.day, "isin": "I", "standard": 10, "fractional": 20}}
    row = execute_rebalance(book, plan, quote, 0, order_units_reviewed=True)
    assert row["filled_quantities"] == {"A": 5} and row["unfilled_shares"] == {"A": 5}
    assert row["cleared_cash_brl"] == 0


def test_missing_feature_date_cannot_become_a_liquidation_or_an_omitted_success():
    snapshot, account = financial_fixture()
    result = signal_diagnostics([snapshot], {"rows": [account]})
    assert len(result) == 1
    assert result[0]["eligible_names"] == 1
    for row in result[0]["arms"].values():
        assert row["selection_available"] is False
        assert row["planned_removals"] is None
        assert row["actual_continuous_turnover"] is None


def test_modified_registration_fails_before_data_reads(tmp_path):
    path = tmp_path / "protocol.json"
    path.write_text('{}', encoding="utf-8")
    with pytest.raises(ValueError, match="registration changed"):
        verify_sources(path, tmp_path / "absent", tmp_path / "absent", tmp_path, tmp_path)
