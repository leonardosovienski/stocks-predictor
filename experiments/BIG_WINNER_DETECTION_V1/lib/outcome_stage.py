"""OUTCOME_GENERATION_STAGE. Importing signal generation is forbidden."""

from __future__ import annotations

import bisect
import csv
from pathlib import Path

from common import add_calendar_months
from freeze import verify_freeze


def _terminal_index(dates: list[str], target: str) -> int | None:
    index = bisect.bisect_right(dates, target) - 1
    return index if index >= 0 else None


def calculate_path_outcome(execution_time: str, values: list[tuple[str, float]],
                           terminal_status: str = "NORMALLY_TRADABLE") -> dict:
    if terminal_status != "NORMALLY_TRADABLE":
        return {"outcome_estimable": False, "terminal_status": terminal_status}
    dates = [day for day, _ in values]
    levels = [float(value) for _, value in values]
    start = bisect.bisect_left(dates, execution_time)
    if start >= len(dates) or dates[start] != execution_time:
        return {"outcome_estimable": False, "terminal_status": "MISSING_EXECUTION_VALUE"}
    target = add_calendar_months(execution_time, 12)
    end = _terminal_index(dates, target)
    if end is None or end <= start or levels[start] <= 0:
        return {"outcome_estimable": False, "terminal_status": "INCOMPLETE_HORIZON"}
    path = levels[start:end + 1]
    returns = [value / levels[start] - 1 for value in path]
    running_peak = path[0]
    max_drawdown = 0.0
    for value in path:
        running_peak = max(running_peak, value)
        max_drawdown = min(max_drawdown, value / running_peak - 1)
    def first_cross(threshold):
        for i, value in enumerate(returns):
            if value >= threshold:
                return dates[start + i]
        return None
    peak_offset = max(range(len(path)), key=path.__getitem__)
    terminal_return = levels[end] / levels[start] - 1
    six_month_end = _terminal_index(dates, add_calendar_months(execution_time, 6))
    six_month_return = (
        levels[six_month_end] / levels[start] - 1
        if six_month_end is not None and six_month_end > start else None
    )
    return {
        "outcome_estimable": True,
        "horizon_end": dates[end],
        "forward_total_return_12m": terminal_return,
        "maximum_total_return_within_12m": max(returns),
        "time_to_10pct": first_cross(0.10),
        "time_to_20pct": first_cross(0.20),
        "time_to_30pct": first_cross(0.30),
        "time_to_peak": dates[start + peak_offset],
        "maximum_drawdown_after_execution": max_drawdown,
        "BIG_WINNER_12M": terminal_return >= 0.30,
        "BIG_WINNER_6M_30": six_month_return >= 0.30 if six_month_return is not None else None,
        "BIG_WINNER_12M_50": terminal_return >= 0.50,
        "BIG_WINNER_12M_100": terminal_return >= 1.00,
        "terminal_status": terminal_status,
    }


def require_valid_freeze(manifest_path: str | Path) -> dict:
    return verify_freeze(manifest_path)


def load_frozen_signals(manifest_path: str | Path) -> list[dict]:
    manifest = require_valid_freeze(manifest_path)
    path = Path(manifest_path).parent / manifest["file"]
    with path.open(newline="", encoding="utf-8") as stream:
        return [_decode_signal_row(row) for row in csv.DictReader(stream)]


def _decode_signal_row(row: dict) -> dict:
    decoded = dict(row)
    for field in ("universe_eligible", "detector_scorable", "selected"):
        value = decoded[field].lower()
        if value not in {"true", "false"}:
            raise ValueError(f"invalid frozen boolean: {field}")
        decoded[field] = value == "true"
    for field in ("rank", "universe_size", "scorable_size", "selection_size"):
        decoded[field] = int(decoded[field]) if decoded[field] else None
    for field in ("score", "percentile"):
        decoded[field] = float(decoded[field]) if decoded[field] else None
    return decoded


def create_winner_episodes(rows: list[dict], negative_gap: int = 1) -> list[dict]:
    """Create episodes from monthly primary labels, independently per ticker."""
    if negative_gap < 1:
        raise ValueError("negative gap must be positive")
    episodes = []
    by_ticker = {}
    for row in rows:
        by_ticker.setdefault(row["ticker"], []).append(row)
    for ticker, ticker_rows in sorted(by_ticker.items()):
        current, negatives = [], 0
        for row in sorted(ticker_rows, key=lambda item: item["signal_asof"]):
            if row.get("BIG_WINNER_12M") is True:
                if current and negatives >= negative_gap:
                    episodes.append(_episode(ticker, current, len(episodes) + 1))
                    current = []
                current.append(row)
                negatives = 0
            elif current:
                negatives += 1
        if current:
            episodes.append(_episode(ticker, current, len(episodes) + 1))
    return episodes


def _episode(ticker: str, rows: list[dict], ordinal: int) -> dict:
    return {"ticker": ticker, "episode_id": f"{ticker}-{ordinal:04d}",
            "episode_start": rows[0]["signal_asof"],
            "episode_end": rows[-1]["signal_asof"]}


def classify_episode(episode: dict, signal_rows: list[dict], reference_value: float,
                     peak_value: float, signal_value: float | None) -> dict:
    relevant = [r for r in signal_rows if r["ticker"] == episode["ticker"] and
                episode["episode_start"] <= r["signal_asof"] <= episode["episode_end"] and
                r.get("detector_scorable")]
    if not relevant:
        return {**episode, "scorable": False, "classification": "NOT_SCORABLE_BY_DETECTOR"}
    selected = sorted((r for r in relevant if r.get("selected")),
                      key=lambda r: r["signal_asof"])
    if not selected:
        return {**episode, "scorable": True, "classification": "MISS"}
    if signal_value is None or peak_value - reference_value <= 0:
        return {**episode, "scorable": True, "classification": "PRECOCITY_NOT_ESTIMABLE"}
    remaining = (peak_value - signal_value) / (peak_value - reference_value)
    return {**episode, "scorable": True,
            "first_qualified_signal": selected[0]["signal_asof"],
            "fraction_of_move_remaining": remaining,
            "classification": "EARLY_HIT" if remaining >= 0.50 else "LATE_HIT"}
