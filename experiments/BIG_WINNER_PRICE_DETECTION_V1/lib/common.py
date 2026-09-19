"""Outcome-neutral contracts for the price-only big-winner experiment."""
from __future__ import annotations

import bisect
import calendar
import datetime as dt
import hashlib
import json
import math
from pathlib import Path

DETECTORS = {
    "MOMENTUM_12_1": ("HIGHER_IS_BETTER", "SEMANTICALLY_EQUIVALENT"),
    "MOMENTUM_6_1": ("HIGHER_IS_BETTER", "SEMANTICALLY_EQUIVALENT"),
    "LOW_VOL_252": ("LOWER_IS_BETTER", "SEMANTICALLY_EQUIVALENT"),
    "REVERSAL_21": ("LOWER_IS_BETTER", "SEMANTICALLY_EQUIVALENT"),
    "MOMENTUM_LOW_VOL": ("HIGHER_IS_BETTER", "SEMANTICALLY_EQUIVALENT"),
    "52W_HIGH": ("HIGHER_IS_BETTER", "SEMANTICALLY_EQUIVALENT"),
    "VOLUME_SURGE": ("HIGHER_IS_BETTER", "EXACT"),
}

SIGNAL_FIELDS = (
    "signal_asof", "execution_time", "ticker", "detector_id",
    "replay_fidelity", "historical_scientific_status", "universe_eligible",
    "detector_scorable", "not_scorable_reason", "score", "rank", "percentile",
    "selected", "universe_size", "scorable_size", "selection_size",
    "direction", "selection_rule", "tie_break_rule", "input_hash",
    "config_hash", "code_commit", "dataset_hash", "created_by_stage",
)

def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(",", ":")).encode()).hexdigest()

def add_months(day, months):
    d = dt.date.fromisoformat(day)
    index = d.year * 12 + d.month - 1 + months
    year, month0 = divmod(index, 12)
    return dt.date(year, month0 + 1, min(d.day, calendar.monthrange(year, month0 + 1)[1])).isoformat()

def next_session(day, sessions):
    i = bisect.bisect_right(sessions, day)
    if i >= len(sessions):
        raise ValueError("no next-open session")
    return sessions[i]

def rank_rows(rows, direction):
    scorable = [row for row in rows if row["detector_scorable"]]
    reverse = direction == "HIGHER_IS_BETTER"
    ordered = sorted(scorable, key=lambda r: r["ticker"])
    ordered.sort(key=lambda r: r["score"], reverse=reverse)
    n = len(ordered)
    k = math.ceil(0.20 * n) if n else 0
    positions = {id(row): i for i, row in enumerate(ordered, 1)}
    out = []
    for source in rows:
        row = dict(source)
        pos = positions.get(id(source))
        row.update(rank=pos, percentile=(pos / n if pos else None),
                   selected=bool(pos and pos <= k), universe_size=len(rows),
                   scorable_size=n, selection_size=k,
                   direction=direction, selection_rule="TOP_20_PERCENT_CEIL_V1",
                   tie_break_rule="SCORE_THEN_TICKER_ASC_V1",
                   created_by_stage="SIGNAL_GENERATION")
        out.append(row)
    return out

def partial_id(selected, universe):
    s = len(selected); n = len(universe)
    ws = sum(r.get("BIG_WINNER_PRICE_12M") is True for r in selected)
    us = sum(r.get("BIG_WINNER_PRICE_12M") is None for r in selected)
    w = sum(r.get("BIG_WINNER_PRICE_12M") is True for r in universe)
    u = sum(r.get("BIG_WINNER_PRICE_12M") is None for r in universe)
    pl, pu = ((ws / s, (ws + us) / s) if s else (None, None))
    bl, bu = ((w / n, (w + u) / n) if n else (None, None))
    ll = pl / bu if pl is not None and bu else None
    lu = pu / bl if pu is not None and bl else None
    return {"selected_n": s, "selected_known_winners": ws, "selected_unknown": us,
            "universe_n": n, "universe_known_winners": w, "universe_unknown": u,
            "precision_lower": pl, "precision_upper": pu,
            "base_rate_lower": bl, "base_rate_upper": bu,
            "lift_outer_lower": ll, "lift_outer_upper": lu}
