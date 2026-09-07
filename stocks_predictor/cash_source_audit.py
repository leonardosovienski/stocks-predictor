"""Validate source cash records without asserting complete return coverage.

Dates are distinct: approval, last cum-entitlement session, ex-session and
payment. Cross-source matches are evidence observations, never auto-approval.
"""

from bisect import bisect_right
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import re


def br_decimal(value):
    text = str(value).strip()
    if not re.fullmatch(r"-?(?:\d+|\d{1,3}(?:\.\d{3})+)(?:,\d+)?", text):
        raise ValueError("invalid Brazilian decimal")
    try:
        result = Decimal(text.replace(".", "").replace(",", "."))
    except InvalidOperation as exc:
        raise ValueError("invalid Brazilian decimal") from exc
    if not result.is_finite():
        raise ValueError("nonfinite amount")
    return result


def br_date(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{2}/\d{2}/\d{4}", value):
        raise ValueError("missing or invalid Brazilian date")
    return datetime.strptime(value, "%d/%m/%Y").date().isoformat()


def next_exchange_session(last_cum, sessions):
    """Require an observed exchange session, never the next quote of one stock."""
    if sessions != sorted(set(sessions)):
        raise ValueError("exchange sessions must be sorted and unique")
    index = bisect_right(sessions, last_cum)
    if not index or sessions[index - 1] != last_cum or index == len(sessions):
        raise ValueError("cum/ex date outside observed exchange calendar")
    following = sessions[index]
    if (date.fromisoformat(following) - date.fromisoformat(last_cum)).days > 7:
        raise ValueError("exchange calendar has an unverified gap")
    return following


def normalize_b3_history(row, sessions):
    if any(
        not isinstance(row.get(k), str) or not row[k].strip()
        for k in (
            "lastDatePriorEx",
            "ratio",
            "quotedPerShares",
            "valueCash",
            "typeStock",
            "corporateAction",
            "dateApproval",
        )
    ):
        raise ValueError("missing B3 cash-event field")
    last_cum = br_date(row["lastDatePriorEx"])
    approval = br_date(row["dateApproval"])
    if approval > last_cum:
        raise ValueError("approval follows entitlement date")
    ratio, quoted = br_decimal(row["ratio"]), br_decimal(row["quotedPerShares"])
    amount = br_decimal(row["valueCash"])
    if ratio <= 0 or ratio != quoted or amount <= 0:
        raise ValueError("unsupported B3 amount or quotation basis")
    return {
        "security_class": row["typeStock"].strip(),
        "action": row["corporateAction"].strip(),
        "approval_date": approval,
        "last_cum": last_cum,
        "ex_date": next_exchange_session(last_cum, sessions),
        "reported_amount": str(amount),
        "quoted_per_shares": str(quoted),
        "value_per_share": str(amount / quoted),
        "payment_date": None,
        "complete_coverage": False,
    }


def validate_payment(row, sessions):
    for field in ("last_cum", "ex_date", "payment_date"):
        if date.fromisoformat(row[field]).isoformat() != row[field]:
            raise ValueError("invalid ISO cash-event date")
    expected = next_exchange_session(row["last_cum"], sessions)
    if row["ex_date"] != expected:
        raise ValueError("source ex-date differs from exchange calendar")
    if row["payment_date"] < row["ex_date"]:
        raise ValueError("payment precedes entitlement")
    amount = Decimal(str(row["value_per_share"]))
    if not amount.is_finite() or amount <= 0:
        raise ValueError("invalid payment amount")
    return row


def match_payment(payment, history, sessions):
    validate_payment(payment, sessions)
    candidates = [
        r
        for r in history
        if r["security_class"] == payment["security_class"]
        and r["action"] == payment["action"]
        and r["last_cum"] == payment["last_cum"]
        and r["ex_date"] == payment["ex_date"]
        and abs(Decimal(r["value_per_share"]) - Decimal(str(payment["value_per_share"])))
        <= Decimal("0.00000000001")
    ]
    if len(candidates) != 1:
        raise ValueError(
            f"cash event requires one unambiguous class/date/amount match; got {len(candidates)}"
        )
    return {
        **payment,
        "b3_approval_date": candidates[0]["approval_date"],
        "reconciliation": "MATCHED",
        "complete_coverage": False,
        "eligible_for_total_return": False,
    }


def match_installments(payments, history, sessions):
    """Each installment is a distinct receivable; their sum must match one right."""
    if len(payments) < 2:
        raise ValueError("multiple installments required")
    fields = ("security_class", "action", "approval_date", "last_cum", "ex_date")
    if len({tuple(p.get(k) for k in fields) for p in payments}) != 1:
        raise ValueError("installments must belong to one entitlement")
    if len({p["payment_date"] for p in payments}) != len(payments):
        raise ValueError("duplicate installment payment date")
    for payment in payments:
        validate_payment(payment, sessions)
    total = sum(Decimal(str(p["value_per_share"])) for p in payments)
    match = match_payment({**payments[0], "value_per_share": str(total)}, history, sessions)
    return [
        {
            **p,
            "b3_approval_date": match["b3_approval_date"],
            "entitlement_total": str(total),
            "installment_number": index,
            "reconciliation": "MATCHED_INSTALLMENT",
            "complete_coverage": False,
            "eligible_for_total_return": False,
        }
        for index, p in enumerate(sorted(payments, key=lambda p: p["payment_date"]), 1)
    ]
