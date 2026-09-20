"""Deterministic post-mortem tables from the immutable V1_PRICE artifacts."""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

PROGRAM = Path(__file__).resolve().parents[1]
REPO = PROGRAM.parents[1]
PRICE = REPO / "experiments" / "BIG_WINNER_PRICE_DETECTION_V1"
OUT = PROGRAM / "analysis"


def load_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_csv(name: str, rows: list[dict], fields: list[str]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / name).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def month_number(day: str) -> int:
    year, month, _ = map(int, day.split("-"))
    return year * 12 + month


def main() -> None:
    labels = load_csv(PRICE / "labels" / "price_outcomes.csv")
    detectors = sorted({row["detector_id"] for row in labels})
    by_detector_month: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in labels:
        by_detector_month[(row["detector_id"], row["signal_asof"])].append(row)

    overlap = []
    for i, left in enumerate(detectors):
        for right in detectors[i + 1:]:
            monthly = []
            for asof in sorted({r["signal_asof"] for r in labels}):
                a = {r["ticker"] for r in by_detector_month[(left, asof)] if r["selected"] == "true"}
                b = {r["ticker"] for r in by_detector_month[(right, asof)] if r["selected"] == "true"}
                monthly.append(len(a & b) / len(a | b) if a | b else 0.0)
            overlap.append({"detector_a": left, "detector_b": right,
                            "mean_monthly_jaccard": f"{sum(monthly) / len(monthly):.9f}"})
    write_csv("detector_overlap.csv", overlap, list(overlap[0]))

    yearly = []
    for detector in detectors:
        groups: dict[str, list[dict]] = defaultdict(list)
        for row in labels:
            if row["detector_id"] == detector and row["detector_scorable"] == "true":
                groups[row["signal_asof"][:4]].append(row)
        for year, rows in sorted(groups.items()):
            known = [r for r in rows if r["BIG_WINNER_PRICE_12M"] in {"true", "false"}]
            selected = [r for r in known if r["selected"] == "true"]
            precision = sum(r["BIG_WINNER_PRICE_12M"] == "true" for r in selected) / len(selected) if selected else None
            base = sum(r["BIG_WINNER_PRICE_12M"] == "true" for r in known) / len(known) if known else None
            yearly.append({"detector": detector, "year": year, "known_n": len(known),
                           "selected_n": len(selected), "precision": precision,
                           "base_rate": base, "lift": precision / base if precision is not None and base else None})
    write_csv("yearly_regime_metrics.csv", yearly, list(yearly[0]))

    canonical = json.loads((PRICE / "metrics" / "episode_detection" / "MOMENTUM_12_1.json").read_text(encoding="utf-8"))["episodes"]
    trajectories = []
    miss_map = []
    lookup = {(r["detector_id"], r["ticker"], r["signal_asof"]): r for r in labels}
    ticker_rows: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in labels:
        ticker_rows[(row["detector_id"], row["ticker"])].append(row)
    for episode in canonical:
        ticker = episode["ticker"]
        start = episode["episode_start"]
        for detector in detectors:
            in_episode = [r for r in ticker_rows[(detector, ticker)]
                          if episode["episode_start"] <= r["signal_asof"] <= episode["episode_end"]
                          and r["detector_scorable"] == "true"]
            selected = sorted((r for r in in_episode if r["selected"] == "true"), key=lambda r: r["signal_asof"])
            if episode.get("boundary_uncertain"):
                result = {**episode, "classification": "BOUNDARY_UNCERTAIN_EXCLUDED"}
            elif not in_episode:
                result = {**episode, "classification": "NOT_SCORABLE_BY_DETECTOR"}
            elif not selected:
                result = {**episode, "classification": "MISS"}
            else:
                reference = float(lookup[(detector, ticker, start)]["execution_price"])
                peak = float(lookup[(detector, ticker, start)]["peak_price"])
                signal_value = float(selected[0]["execution_price"])
                remaining = (peak - signal_value) / (peak - reference) if peak > reference else None
                result = {**episode, "classification": ("EARLY_HIT" if remaining is not None and remaining >= .5 else "LATE_HIT"),
                          "fraction_of_move_remaining": remaining}
            relevant = [r for r in ticker_rows[(detector, ticker)]
                        if -3 <= month_number(r["signal_asof"]) - month_number(start) <= 3]
            for row in relevant:
                trajectories.append({"episode_id": episode["episode_id"], "ticker": ticker,
                    "detector": detector, "signal_asof": row["signal_asof"],
                    "months_relative_to_episode_start": month_number(row["signal_asof"]) - month_number(start),
                    "rank": row["rank"], "percentile": row["percentile"], "score": row["score"],
                    "selected": row["selected"], "outcome": row["BIG_WINNER_PRICE_12M"]})
            at_start = lookup.get((detector, ticker, start))
            classification = result["classification"]
            if classification == "BOUNDARY_UNCERTAIN_EXCLUDED": reason = "OUTCOME_UNCERTAINTY"
            elif classification == "NOT_SCORABLE_BY_DETECTOR": reason = "INSUFFICIENT_HISTORY"
            elif classification == "MISS" and at_start and at_start["detector_scorable"] == "true": reason = "RANK_TOO_LOW"
            elif classification == "MISS": reason = "NO_SIGNAL"
            else: reason = "DETECTED"
            miss_map.append({"episode_id": episode["episode_id"], "ticker": ticker,
                "episode_start": start, "episode_end": episode["episode_end"], "detector": detector,
                "classification": classification, "demonstrable_reason": reason,
                "rank_at_start": at_start["rank"] if at_start else "",
                "percentile_at_start": at_start["percentile"] if at_start else "",
                "score_at_start": at_start["score"] if at_start else "",
                "selected_at_start": at_start["selected"] if at_start else "",
                "fraction_of_move_remaining": result.get("fraction_of_move_remaining", ""),
                "forward_price_return_12m": at_start["forward_price_return_12m"] if at_start else "",
                "sector_pit": "NOT_AVAILABLE_PIT", "market_cap_pit": "NOT_AVAILABLE_PIT",
                "liquidity_pit": "UNIVERSE_ELIGIBLE_ONLY", "regime_pit": f"CALENDAR_YEAR_{start[:4]}"})
    write_csv("pre_winner_rank_trajectories.csv", trajectories, list(trajectories[0]))
    write_csv("hit_miss_map.csv", miss_map, list(miss_map[0]))

    m12 = {(r["signal_asof"], r["ticker"]): r for r in labels if r["detector_id"] == "MOMENTUM_12_1"}
    m6 = {(r["signal_asof"], r["ticker"]): r for r in labels if r["detector_id"] == "MOMENTUM_6_1"}
    common = sorted(set(m12) & set(m6))
    contribution = {"common_observations": len(common), "both_selected": 0, "m12_only_selected": 0,
                    "m6_only_selected": 0, "neither_selected": 0, "m6_only_known_winners": 0,
                    "m12_only_known_winners": 0}
    for key in common:
        a, b = m12[key]["selected"] == "true", m6[key]["selected"] == "true"
        bucket = "both_selected" if a and b else "m12_only_selected" if a else "m6_only_selected" if b else "neither_selected"
        contribution[bucket] += 1
        if a and not b and m12[key]["BIG_WINNER_PRICE_12M"] == "true": contribution["m12_only_known_winners"] += 1
        if b and not a and m6[key]["BIG_WINNER_PRICE_12M"] == "true": contribution["m6_only_known_winners"] += 1
    (OUT / "momentum_unique_contribution.json").write_text(json.dumps(contribution, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
