"""Frozen, outcome-blind BIG_WINNER V2 candidate.

The model is deliberately simple: the unchanged M12-1 baseline selected before
this module existed.  It never imports labels, outcomes, or evaluation code.
"""
from __future__ import annotations

import bisect
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path

MODEL_ID = "BIG_WINNER_V2_MOMENTUM_12_1_BASELINE"
SCIENTIFIC_STATUS = "UNVALIDATED_PROSPECTIVE_CANDIDATE"


def canonical_hash(value) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_selection_freeze(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data["v2_identifier"] != MODEL_ID:
        raise ValueError("unexpected V2 identity")
    expected = data["artifact_hash"]
    payload = dict(data); payload.pop("artifact_hash")
    if canonical_hash(payload) != expected:
        raise ValueError("V2_SELECTION_FREEZE hash mismatch")
    return data


def momentum_12_1(dates: list[str], closes: list[float], asof: str) -> float | None:
    """252-to-21 session return using observations strictly before ``asof``."""
    end = bisect.bisect_left(dates, asof)
    window_dates = dates[:end]; window = closes[:end]
    if len(window_dates) < 253 or len(window) != len(window_dates):
        return None
    start_value, end_value = window[-253], window[-22]
    if start_value <= 0 or end_value <= 0:
        return None
    return end_value / start_value - 1.0


def apply_share_count_continuity(dates: list[str], closes: list[float], adjustments: list[tuple[str, float]], asof: str) -> list[float]:
    values=list(closes)
    for ex_date,factor in adjustments:
        if factor <= 0: raise ValueError("invalid corporate-action factor")
        if ex_date <= asof:
            values=[value*factor if day<ex_date else value for day,value in zip(dates,values)]
    return values


def rank(scores: dict[str, float | None]) -> list[dict]:
    valid = [(ticker, score) for ticker, score in scores.items()
             if score is not None and math.isfinite(score)]
    ordered = sorted(valid, key=lambda item: item[0])
    ordered.sort(key=lambda item: item[1], reverse=True)
    count = len(ordered); selected_count = math.ceil(0.20 * count) if count else 0
    result = []
    for position, (ticker, score) in enumerate(ordered, 1):
        result.append({"ticker": ticker, "score": score, "rank": position,
            "percentile": position / count, "selected": position <= selected_count,
            "scorable_size": count, "selection_size": selected_count})
    return result


def generate_decision(asof: str, execution_time: str, series: dict[str, tuple[list[str], list[float]]],
                      identities: dict[str, dict], metadata: dict) -> dict:
    scores = {ticker: momentum_12_1(dates, closes, asof)
              for ticker, (dates, closes) in series.items()}
    ranking = rank(scores)
    rows = []
    for row in ranking:
        identity = identities.get(row["ticker"])
        rows.append({**row, "security_identity": identity or {"ticker": row["ticker"],
            "identity_status": "TICKER_ONLY_PIT_IDENTITY_NOT_AVAILABLE"}})
    decision = {"schema_version":"BIG_WINNER_V2_DECISION_V1", "model_identity":MODEL_ID,
        "scientific_status":SCIENTIFIC_STATUS, "signal_asof":asof,
        "execution_time":execution_time, "pit_cutoff":asof,
        "eligible_universe":sorted(series), "ranking":rows,
        "decision_reason":"FROZEN_M12_TOP20", **metadata}
    decision["decision_payload_hash"] = canonical_hash(decision)
    return decision
