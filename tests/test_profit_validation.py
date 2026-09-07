from copy import deepcopy
import pytest

from stocks_predictor.profit_validation import compound_path, entitlement_book


def test_independent_book_chain_and_cash_are_conserved():
    member = {"ticker": "A", "isin": "a"}
    bars = {"A": {"2020-01-01": (20., 22.)}, "C": {"2020-04-01": (8., 7.)}}
    terms = {"events": [
        {"ticker": "A", "isin": "a", "ex_date": "2020-02-01", "removes_original": True,
         "stocks": [{"ticker": "B", "isin": "b", "ratio": 2}], "cash": [{"amount_brl": 1}]},
        {"ticker": "B", "isin": "b", "ex_date": "2020-03-01", "removes_original": True,
         "stocks": [{"ticker": "C", "isin": "c", "ratio": .5}], "cash": [{"amount_brl": 2}]}]}
    # A splits 1:2, then 2 A -> 4 B + 2 cash -> 2 C + 10 cash.
    factors = {"A": {"2020-01-10": .5}}
    copy = deepcopy((bars, factors, terms))
    result = entitlement_book(member, "2020-01-01", "2020-04-01", bars, factors, terms)
    assert result["stocks"] == {"C": 2}
    assert result["cash"] == 10
    assert result["return"] == pytest.approx(.3)
    worst = entitlement_book(member, "2020-01-01", "2020-04-01", bars, factors, terms, "worst")
    assert worst["return"] == pytest.approx(24/22-1)
    assert (bars, factors, terms) == copy


def test_ex_entry_does_not_receive_cash_or_duplicate_split():
    bars = {"A": {"2020-02-01": (5., 6.), "2020-03-01": (5., 6.)}}
    terms = {"events": []}
    result = entitlement_book({"ticker": "A", "isin": "a"}, "2020-02-01", "2020-03-01",
                              bars, {"A": {"2020-02-01": .5}}, terms)
    assert result["return"] == 0
    assert result["stocks"] == {"A": 1}


def test_split_at_exit_is_included():
    result = entitlement_book({"ticker": "A", "isin": "a"}, "2020-01-01", "2020-02-01",
                              {"A": {"2020-01-01": (10, 10), "2020-02-01": (5, 5)}},
                              {"A": {"2020-02-01": .5}}, {"events": []})
    assert result["return"] == 0


def test_missing_entry_requires_documented_cessation():
    member = {"ticker": "A", "isin": "a"}
    with pytest.raises(ValueError, match="unexplained"):
        entitlement_book(member, "2020-01-01", "2020-02-01", {}, {}, {"events": []})
    terms = {"events": [{"ticker": "A", "isin": "a", "removes_original": True, "ex_date": "2019-12-31"}]}
    assert entitlement_book(member, "2020-01-01", "2020-02-01", {}, {}, terms)["return"] == 0


def test_compounding_does_not_replace_geometric_loss_with_arithmetic_mean():
    result = compound_path([1., -.5], "2020-01-01", "2022-01-01")
    assert result["cumulative_return"] == 0
    assert result["period_mark_max_drawdown"] == -.5


def test_retained_original_spinoff_not_double_counted():
    terms = {"events": [{"ticker": "A", "isin": "a", "ex_date": "2020-01-02", "removes_original": False,
                         "stocks": [{"ticker": "A", "isin": "a", "ratio": 1},
                                    {"ticker": "B", "isin": "b", "ratio": 1}], "cash": []}]}
    bars = {"A": {"2020-01-01": (10, 10), "2020-01-03": (6, 6)}, "B": {"2020-01-03": (4, 4)}}
    result = entitlement_book({"ticker": "A", "isin": "a"}, "2020-01-01", "2020-01-03", bars, {}, terms)
    assert result["return"] == 0
    assert result["stocks"] == {"A": 1, "B": 1}
