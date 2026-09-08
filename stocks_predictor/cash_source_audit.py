"""Validate source cash records without asserting complete return coverage.

Dates are distinct: approval, last cum-entitlement session, ex-session and
payment. Cross-source matches are evidence observations, never auto-approval.
"""

from bisect import bisect_right
from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import re
import unicodedata


def parse_b3_credit_pages(pages, bulletin_date):
    """Extract supported B3 credit rows, never infer an empty income inventory.

    A valid PDF or a Clearing title is insufficient: historical section URLs
    sometimes contain only exchange-rate data. Keep that absence explicit.
    """
    if date.fromisoformat(bulletin_date).isoformat() != bulletin_date:
        raise ValueError("invalid bulletin date")
    numbers = [p["page"] for p in pages]
    if numbers != sorted(set(numbers)) or any(type(n) is not int or n < 1 for n in numbers):
        raise ValueError("unique chronological PDF pages required")
    expression = re.compile(
        r"\b(BR[A-Z0-9]{10})\s+(?:\d+\s+)?"
        r"(DIVIDENDO|RENDIMENTO|JUROS\s+SOBRE\s+CAPITAL\s+PROPRIO)\s+"
        r"(\d{2}/\d{2}/\d{4})\s+([\d.,]+)\s+(\d{2}/\d{2}/\d{4})"
    )
    rows, rejected = [], []
    heading = active = False
    for page in pages:
        text = " ".join(unicodedata.normalize("NFKD", page["text"])
                        .encode("ascii", "ignore").decode().upper().split())
        start = text.find("CREDITO DE PROVENTOS")
        if start >= 0:
            heading = active = True
            text = text[start:]
        if not active:
            continue
        end = re.search(r"CUSTODIA FUNGIVEL|PRAZO PARA DEPOSITO DE TITULOS", text)
        if end:
            text, active = text[:end.start()], False
        for match in expression.finditer(text):
            try:
                approval, payment = br_date(match[3]), br_date(match[5])
                gross = br_decimal(match[4])
                if payment != bulletin_date or approval > payment or gross <= 0:
                    raise ValueError("credit chronology or amount differs from bulletin")
            except ValueError as exc:
                rejected.append({"page": page["page"], "excerpt": match[0], "reason": str(exc)})
                continue
            rows.append({"isin": match[1],
                "action": "JRS CAP PROPRIO" if match[2].startswith("JUROS") else match[2],
                "approval_date": approval, "payment_date": payment,
                "gross_per_share": str(gross), "page": page["page"], "source_excerpt": match[0]})
    status = ("CREDIT_SECTION_MISSING" if not heading else
              "CREDIT_ROWS_EXTRACTED" if rows else "NO_RECOGNIZED_CREDIT_ROWS")
    return {"status": status, "rows": rows, "rejected": rejected,
            "complete_cash_inventory": False, "net_amount_inferred": False}


def expand_reviewed_installments(events, schedules, sessions):
    """Materialize reviewed payments without paying their aggregate parent twice.

    Raw rows remain immutable. An explicit lineage records any issuer rounding
    difference; a tolerance alone cannot authorize changing the entitlement.
    No payment/tax/source field is inferred from a different distribution.
    """
    if sessions != sorted(set(sessions)):
        raise ValueError("exchange sessions must be sorted and unique")
    parents = {r["event_id"]: r for r in events}
    if len(parents) != len(events):
        raise ValueError("duplicate parent entitlement")
    replacements, lineage = {}, []
    identity = ("ticker", "isin", "ex_date", "action")
    for spec in schedules:
        parent_id = spec["parent_event_id"]
        if parent_id not in parents or parent_id in replacements:
            raise ValueError("unknown or repeated installment parent")
        parent = parents[parent_id]
        if parent.get("payment_date"):
            raise ValueError("dated parent requires a separate supersession review")
        parts = spec["payments"]
        if len(parts) < 2 or spec.get("source_review") is not True or not spec.get("sources"):
            raise ValueError("reviewed multiple-payment schedule required")
        days = [p["payment_date"] for p in parts]
        if days != sorted(set(days)):
            raise ValueError("unique chronological installment dates required")
        total = Decimal(0)
        children = []
        for n, part in enumerate(parts, 1):
            if any(part.get(k) != parent[k] for k in identity):
                raise ValueError("installment belongs to a different entitlement")
            gross = Decimal(str(part["gross_per_share"]))
            if not gross.is_finite() or gross <= 0:
                raise ValueError("invalid installment gross")
            total += gross
            day = date.fromisoformat(part["payment_date"]).isoformat()
            known = date.fromisoformat(part["known_on"]).isoformat()
            if day != part["payment_date"] or not parent["ex_date"] <= day or known > day:
                raise ValueError("invalid installment chronology")
            if not part.get("sources"):
                raise ValueError("installment source required")
            net = part.get("net_per_share")
            if net is not None:
                net = Decimal(str(net))
                if not net.is_finite() or not 0 <= net <= gross or not part.get("tax_source"):
                    raise ValueError("invalid or unsupported installment net")
            if part.get("source_review") is True and net is None:
                raise ValueError("reviewed installment requires net evidence")
            pos = bisect_right(sessions, day)
            child_id = f"{parent_id}:payment:{n}"
            if child_id in parents:
                raise ValueError("installment identity collision")
            children.append({**deepcopy(parent), **deepcopy(part),
                "event_id": child_id, "parent_event_id": parent_id,
                "installment_number": n,
                "available_on": sessions[pos] if pos < len(sessions) else None})
        original = Decimal(str(parent["gross_per_share"]))
        if not original.is_finite() or original <= 0:
            raise ValueError("invalid parent gross")
        delta = total - original
        if delta:
            rounding = spec.get("published_rounding", {})
            if (not delta.is_finite() or abs(delta) > Decimal("0.000000001")
                    or rounding.get("reviewed") is not True or not rounding.get("sources")
                    or not rounding.get("reason") or Decimal(str(rounding.get("delta"))) != delta):
                raise ValueError("installments do not reconcile with parent")
        replacements[parent_id] = children
        lineage.append({"parent_event_id": parent_id, "parent_gross_per_share": str(original),
            "child_event_ids": [r["event_id"] for r in children], "payment_total": str(total),
            "published_rounding_delta": str(delta), "raw_parent_preserved": True,
            "parent_in_execution": False, "sources": deepcopy(spec["sources"])})
    expanded = [child for row in events for child in replacements.get(row["event_id"], [deepcopy(row)])]
    if len({r["event_id"] for r in expanded}) != len(expanded):
        raise ValueError("duplicate materialized cash event")
    return expanded, lineage


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
