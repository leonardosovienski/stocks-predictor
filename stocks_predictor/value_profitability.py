"""H20 signal-only value/profitability ranking on exact disclosed documents.

This is a closing-equity ROE proxy, not a replica of any commercial model.
No function reads returns, writes a database or certifies executable profit.
"""
from datetime import date, timedelta
from decimal import Decimal

from stocks_predictor.retail_cash import iso, number

ARMS = ("VALUE_COMMON_UNIVERSE", "VALUE_PROFITABILITY", "VALUE_PROFITABILITY_BUFFER")


def accounting_index(rows):
    result = {}
    for row in rows:
        key = (row["cnpj"], row["ref_date"], row["document_version"])
        if key in result:
            raise ValueError("duplicate exact accounting document")
        result[key] = row
    return result


def _close(actual, expected):
    return abs(number(actual) - expected) <= max(Decimal("1e-12"), abs(expected) * Decimal("1e-10"))


def prepare_snapshot(snapshot, accounts):
    """Preserve unavailable cells, validate source arithmetic, then expose ratios."""
    asof = iso(snapshot["asof"])
    members = snapshot["members"]
    if (len({m["ticker"] for m in members}) != len(members)
            or len({m["cnpj"] for m in members}) != len(members)):
        raise ValueError("duplicate ticker or issuer in signal universe")
    rows = []
    for member in members:
        base = {k: member[k] for k in ("ticker", "cnpj", "isin")}
        if member.get("eligible") is not True:
            rows.append({**base, "eligible": False, "reason": member.get("reason") or "SOURCE_INELIGIBLE"})
            continue
        ref = iso(member["ref_date"])
        if iso(member["available_at"]) > asof or ref > asof:
            raise ValueError("future filing in signal features")
        age = (date.fromisoformat(asof) - date.fromisoformat(ref)).days
        if age > 550:
            rows.append({**base, "eligible": False, "reason": "REPORT_OLDER_THAN_550_DAYS"})
            continue
        account = accounts.get((member["cnpj"], ref, member["document_version"]))
        if account is None:
            rows.append({**base, "eligible": False, "reason": "NO_EXACT_ACCOUNTING_DOCUMENT"})
            continue
        received = date.fromisoformat(iso(account["received_at"]))
        available = (received + timedelta(days=1)).isoformat()
        if (available > asof or available != member["available_at"]
                or str(account["document_id"]) != str(member["document_id"])):
            raise ValueError("accounting document identity or availability mismatch")
        earnings, equity = account["owner_earnings_brl"], account["owner_equity_brl"]
        if earnings is None or equity is None:
            rows.append({**base, "eligible": False, "reason": "MISSING_OWNER_EARNINGS_OR_EQUITY"})
            continue
        earnings, equity = number(earnings), number(equity)
        if equity <= 0:
            rows.append({**base, "eligible": False, "reason": "NONPOSITIVE_OWNER_EQUITY"})
            continue
        income = account["earnings_source"]
        equity_sources = account["equity_sources"]
        if not income or len(equity_sources) != 2:
            raise ValueError("owner attribution requires explicit source rows")
        sources = [income, *equity_sources]
        if any(r["archive_sha256"] != member["accounting_source_sha256"]
               or iso(r["period_end"]) != ref for r in sources):
            raise ValueError("accounting source hash or period mismatch")
        if (abs(number(income["value_brl"]) - earnings) > Decimal(".01")
                or abs(number(equity_sources[0]["value_brl"])
                       - number(equity_sources[1]["value_brl"]) - equity) > Decimal(".01")):
            raise ValueError("owner accounting source arithmetic mismatch")
        duration = (date.fromisoformat(ref) - date.fromisoformat(iso(income["period_start"]))).days + 1
        if not 330 <= duration <= 400:
            rows.append({**base, "eligible": False, "reason": "EARNINGS_NOT_ANNUAL"})
            continue
        cap = number(member["capital_proxy_brl"])
        close = number(member["signal_close"])
        if cap <= 0 or close <= 0:
            raise ValueError("nonpositive disclosed capitalization or signal price")
        if (member.get("H18") is None or member.get("H19") is None
                or not _close(member["H18"], earnings / cap)
                or not _close(member["H19"], equity / cap)):
            raise ValueError("prepared factors differ from exact accounting numerators")
        rows.append({**base, "eligible": True, "reason": None, "value": equity / cap,
                     "profitability": earnings / equity, "signal_close": close,
                     "owner_earnings_brl": earnings, "owner_equity_brl": equity,
                     "capital_proxy_brl": cap, "ref_date": ref, "available_at": available,
                     "document_id": str(member["document_id"]),
                     "document_version": member["document_version"], "report_age_days": age,
                     "accounting_source_sha256": member["accounting_source_sha256"],
                     "capital_source_sha256": member["capital_source_sha256"]})
    return {"asof": asof, "members": rows}


def _midranks(rows, field):
    ordered = sorted(rows, key=lambda r: (-number(r[field]), r["ticker"]))
    result = {}
    start = 0
    while start < len(ordered):
        end = start + 1
        while end < len(ordered) and number(ordered[end][field]) == number(ordered[start][field]):
            end += 1
        rank = Decimal(start + 1 + end) / 2
        for row in ordered[start:end]:
            result[row["ticker"]] = rank
        start = end
    return result


def rank_snapshot(snapshot, arm):
    if arm not in ARMS:
        raise ValueError("unregistered H20 arm")
    rows = [r for r in snapshot["members"] if r["eligible"]]
    value, profitability = _midranks(rows, "value"), _midranks(rows, "profitability")
    ranked = []
    for row in rows:
        ticker = row["ticker"]
        score = value[ticker] if arm == ARMS[0] else (value[ticker] + profitability[ticker]) / 2
        ranked.append({**row, "value_rank": value[ticker], "profitability_rank": profitability[ticker],
                       "combined_rank_score": score})
    ranked.sort(key=lambda r: (r["combined_rank_score"], r["ticker"]))
    return [{**r, "rank": i + 1} for i, r in enumerate(ranked)]


def select_members(ranked, incumbents, *, buffered=False):
    """incumbents maps actual held tickers to ISIN; planned-path use must be labelled."""
    if len({r["ticker"] for r in ranked}) != len(ranked):
        raise ValueError("duplicate ranked ticker")
    if [r["rank"] for r in ranked] != list(range(1, len(ranked) + 1)):
        raise ValueError("ordered consecutive ranks required")
    if len(ranked) < 20:
        return {"status": "INSUFFICIENT_COMMON_FEATURE_COVERAGE", "members": [],
                "forced_exit_tickers": [], "selection_available": False}
    count = len(ranked) // 5
    cutoff = (3 * len(ranked) + 9) // 10  # ceil(0.30*N), integer arithmetic
    retained = [r for r in ranked[:cutoff] if incumbents.get(r["ticker"]) == r["isin"]][:count]
    keep = {r["ticker"] for r in retained} if buffered else set()
    for row in ranked:
        if len(keep) == count:
            break
        keep.add(row["ticker"])
    selected = [{**r, "selection_reason": "RETAINED_WITHIN_RANK_BUFFER"
                 if buffered and r in retained else "BEST_AVAILABLE_RANK"} for r in ranked if r["ticker"] in keep]
    pairs = {(r["ticker"], r["isin"]) for r in selected}
    return {"status": "SIGNAL_SELECTION_ONLY", "selection_available": True, "members": selected,
            "target_count": count, "retention_rank_cutoff": cutoff if buffered else count,
            "forced_exit_tickers": sorted(t for t, isin in incumbents.items() if (t, isin) not in pairs)}
