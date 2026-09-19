"""Outcome-neutral contracts for BIG_WINNER_DETECTION_V1.

This module deliberately contains no winner or forward-return logic so it can be
imported by the signal stage without crossing the outcome firewall.
"""

from __future__ import annotations

import calendar
import datetime as dt
import hashlib
import json
import math
from pathlib import Path


SIGNAL_FIELDS = (
    "signal_asof", "execution_time", "ticker", "detector_id",
    "replay_fidelity", "scientific_historical_status", "universe_eligible",
    "detector_scorable", "not_scorable_reason", "required_input_status",
    "score", "rank", "percentile", "selected", "universe_size",
    "scorable_size", "selection_size", "selection_rule_version",
    "input_hash", "config_hash", "code_commit", "dataset_versions",
    "created_by_stage",
)

NOT_SCORABLE_REASONS = {
    "NOT_SCORABLE_MISSING_PIT_INPUT",
    "NOT_SCORABLE_INVALID_INPUT",
    "NOT_SCORABLE_INSUFFICIENT_HISTORY",
    "NOT_SCORABLE_MAPPING_UNRESOLVED",
    "NOT_SCORABLE_CORPORATE_ACTION_UNRESOLVED",
    "NOT_SCORABLE_OTHER_DOCUMENTED_REASON",
}


def iso_day(value: str) -> str:
    parsed = dt.date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError(f"non-canonical ISO date: {value!r}")
    return value


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_hash(value) -> str:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def add_calendar_months(day: str, months: int) -> str:
    source = dt.date.fromisoformat(iso_day(day))
    index = source.year * 12 + source.month - 1 + months
    year, month0 = divmod(index, 12)
    terminal_day = min(source.day, calendar.monthrange(year, month0 + 1)[1])
    return dt.date(year, month0 + 1, terminal_day).isoformat()


def first_session_after(day: str, sessions: list[str]) -> str:
    iso_day(day)
    for session in sorted(set(sessions)):
        iso_day(session)
        if session > day:
            return session
    raise ValueError(f"no eligible next-open session after {day}")


def conservative_available_at(publication_date: str, sessions: list[str]) -> str:
    """Date-only publications become available on the next trading session."""
    return first_session_after(publication_date, sessions)


def validate_scorability(row: dict) -> None:
    eligible = bool(row.get("universe_eligible"))
    scorable = bool(row.get("detector_scorable"))
    score = row.get("score")
    reason = row.get("not_scorable_reason") or ""
    if scorable and not eligible:
        raise ValueError("scorable observation must be universe eligible")
    if scorable:
        if reason:
            raise ValueError("scorable observation cannot have a failure reason")
        if score is None or not isinstance(score, (int, float)) or not math.isfinite(score):
            raise ValueError("scorable observation requires a finite score")
    else:
        if score is not None:
            raise ValueError("missing/invalid inputs cannot be substituted by a score")
        if eligible and reason not in NOT_SCORABLE_REASONS:
            raise ValueError("eligible unscorable observation requires a registered reason")


def rank_top_twenty(rows: list[dict], direction: str) -> list[dict]:
    """Rank a single detector/asof cross-section without changing its rows."""
    if direction not in {"HIGHER_IS_BETTER", "LOWER_IS_BETTER"}:
        raise ValueError("unregistered score direction")
    if not rows:
        return []
    keys = {(r["detector_id"], r["signal_asof"]) for r in rows}
    if len(keys) != 1:
        raise ValueError("rank_top_twenty accepts one detector/asof only")
    for row in rows:
        validate_scorability(row)
    scorable = [r for r in rows if r["detector_scorable"]]
    reverse_score = direction == "HIGHER_IS_BETTER"
    ordered = sorted(scorable, key=lambda r: r["ticker"])
    ordered.sort(key=lambda r: r["score"], reverse=reverse_score)
    n = len(ordered)
    k = math.ceil(0.20 * n) if n else 0
    positions = {id(row): i for i, row in enumerate(ordered, 1)}
    result = []
    for source in rows:
        row = dict(source)
        pos = positions.get(id(source))
        row["rank"] = pos
        row["percentile"] = ((n - pos + 1) / n if reverse_score else pos / n) if pos else None
        row["selected"] = bool(pos and pos <= k)
        row["universe_size"] = sum(bool(r["universe_eligible"]) for r in rows)
        row["scorable_size"] = n
        row["selection_size"] = k
        row["selection_rule_version"] = "TOP_20_PERCENT_V1"
        row["created_by_stage"] = "SIGNAL_GENERATION"
        result.append(row)
    return result
