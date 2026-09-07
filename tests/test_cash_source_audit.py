from decimal import Decimal
import json
from pathlib import Path

import pytest

from cash_source_audit import (
    br_date,
    br_decimal,
    match_installments,
    match_payment,
    next_exchange_session,
    normalize_b3_history,
)


def event(**overrides):
    return {
        "typeStock": "UNT",
        "dateApproval": "06/08/2026",
        "valueCash": "0,50000000000",
        "ratio": "1",
        "quotedPerShares": "1",
        "corporateAction": "DIVIDENDO",
        "lastDatePriorEx": "11/08/2026",
        **overrides,
    }


def test_real_b3_unit_event_matches_energisa_workbook_cells():
    path = Path(__file__).parent / "fixtures/cvm_source_history/cash_source_sample.json"
    source = json.loads(path.read_text(encoding="utf-8"))
    sessions = ["2026-08-11", "2026-08-12"]
    observed = normalize_b3_history(source["b3"], sessions)
    v = source["ri_values_D_to_J"]
    payment = {
        "security_class": "UNT",
        "action": "DIVIDENDO",
        "approval_date": v[0][:10],
        "last_cum": v[1][:10],
        "ex_date": v[2][:10],
        "payment_date": v[3][:10],
        "value_per_share": str(v[6]),
    }
    matched = match_payment(payment, [observed], sessions)
    assert matched["value_per_share"] == "0.5"
    assert matched["payment_date"] == "2026-08-24"
    assert Decimal(str(v[4])) == Decimal("0.1")  # An ON amount cannot replace a unit amount.


def test_cum_date_uses_exchange_calendar_across_carnival_not_ticker_next_quote():
    sessions = ["2020-02-20", "2020-02-21", "2020-02-26", "2020-02-27"]
    assert next_exchange_session("2020-02-21", sessions) == "2020-02-26"
    with pytest.raises(ValueError, match="outside"):
        next_exchange_session("2020-02-24", sessions)
    with pytest.raises(ValueError, match="outside"):
        next_exchange_session("2020-02-27", sessions)
    with pytest.raises(ValueError, match="gap"):
        next_exchange_session("2020-02-21", ["2020-02-21", "2020-03-10"])


def test_source_amount_per_thousand_does_not_become_per_share():
    sessions = ["2026-08-11", "2026-08-12"]
    result = normalize_b3_history(
        event(valueCash="500,00000000", ratio="1000", quotedPerShares="1000"), sessions
    )
    assert Decimal(result["value_per_share"]) == Decimal("0.5")
    assert result["payment_date"] is None and result["complete_coverage"] is False
    with pytest.raises(ValueError, match="basis"):
        normalize_b3_history(event(ratio="1000"), sessions)


@pytest.mark.parametrize("value", [None, "", "12/13/2026", "2026-08-12"])
def test_missing_or_invalid_source_date_is_not_imputed(value):
    with pytest.raises(ValueError):
        br_date(value)


@pytest.mark.parametrize("value", ["NaN", "Inf", "0.1", "1.00,1", ""])
def test_brazilian_decimal_rejects_ambiguous_or_nonfinite_values(value):
    with pytest.raises(ValueError):
        br_decimal(value)


def test_payment_match_requires_class_date_amount_and_unique_event():
    sessions = ["2026-08-11", "2026-08-12"]
    history = normalize_b3_history(event(), sessions)
    payment = {
        "security_class": "UNT",
        "action": "DIVIDENDO",
        "last_cum": "2026-08-11",
        "ex_date": "2026-08-12",
        "payment_date": "2026-08-24",
        "value_per_share": "0.5",
    }
    assert match_payment(payment, [history], sessions)["reconciliation"] == "MATCHED"
    for wrong in ({"security_class": "ON"}, {"value_per_share": "0.1"}):
        with pytest.raises(ValueError, match="got 0"):
            match_payment({**payment, **wrong}, [history], sessions)
    with pytest.raises(ValueError, match="got 2"):
        match_payment(payment, [history, history], sessions)
    with pytest.raises(ValueError, match="precedes"):
        match_payment({**payment, "payment_date": "2025-08-24"}, [history], sessions)
    with pytest.raises(ValueError, match="ex-date"):
        match_payment({**payment, "ex_date": "2026-08-13"}, [history], sessions)


def test_real_ambev_installment_amounts_reconcile_without_using_net_as_gross():
    sessions = ["2025-12-18", "2025-12-19"]
    history = normalize_b3_history(
        event(
            typeStock="ON",
            dateApproval="09/12/2025",
            lastDatePriorEx="18/12/2025",
            valueCash="0,269",
            corporateAction="JRS CAP PROPRIO",
        ),
        sessions,
    )
    base = {
        "security_class": "ON",
        "action": "JRS CAP PROPRIO",
        "approval_date": "2025-12-09",
        "last_cum": "2025-12-18",
        "ex_date": "2025-12-19",
    }
    payments = [
        {**base, "payment_date": day, "value_per_share": value}
        for day, value in [("2026-04-06", "0.075"), ("2026-07-06", "0.0755"), ("2026-10-06", "0.1185")]
    ]
    result = match_installments(payments, [history], sessions)
    assert len(result) == 3 and {r["entitlement_total"] for r in result} == {"0.2690"}
    with pytest.raises(ValueError, match="got 0"):
        match_installments([{**p, "value_per_share": "0.063"} for p in payments], [history], sessions)
    with pytest.raises(ValueError, match="duplicate"):
        match_installments([payments[0], payments[0]], [history], sessions)
