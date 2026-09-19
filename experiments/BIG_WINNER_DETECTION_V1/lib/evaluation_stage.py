"""EVALUATION_STAGE: confirmatory metrics and dependence-preserving controls."""

from __future__ import annotations

import math
import random
import statistics


def cross_sectional_metrics(rows: list[dict]) -> dict:
    usable = [r for r in rows if r.get("detector_scorable") and
              r.get("outcome_estimable", True) and r.get("BIG_WINNER_12M") is not None]
    selected = [r for r in usable if r.get("selected")]
    winners = sum(bool(r["BIG_WINNER_12M"]) for r in usable)
    selected_winners = sum(bool(r["BIG_WINNER_12M"]) for r in selected)
    base = winners / len(usable) if usable else None
    precision = selected_winners / len(selected) if selected else None
    lift = precision / base if precision is not None and base else None
    returns = [float(r["forward_total_return_12m"]) for r in usable]
    selected_returns = [float(r["forward_total_return_12m"]) for r in selected]
    return {
        "scorable_observations": len(usable), "selected_observations": len(selected),
        "winner_observations": winners, "precision": precision, "base_rate": base,
        "precision_minus_base_rate": precision - base if precision is not None and base is not None else None,
        "lift": lift,
        "mean_forward_return_selected": statistics.mean(selected_returns) if selected_returns else None,
        "median_forward_return_selected": statistics.median(selected_returns) if selected_returns else None,
        "mean_forward_return_scorable_universe": statistics.mean(returns) if returns else None,
        "median_forward_return_scorable_universe": statistics.median(returns) if returns else None,
    }


def matched_random(rows: list[dict], simulations: int = 10_000, seed: int = 20260919) -> list[float]:
    groups = {}
    for row in rows:
        if row.get("detector_scorable") and row.get("BIG_WINNER_12M") is not None:
            groups.setdefault(row["signal_asof"], []).append(row)
    rng = random.Random(seed)
    distribution = []
    for _ in range(simulations):
        chosen = []
        for group in groups.values():
            k_values = {int(r["selection_size"]) for r in group}
            if len(k_values) != 1:
                raise ValueError("selection size is not constant within asof")
            chosen.extend(rng.sample(group, min(k_values.pop(), len(group))))
        distribution.append(sum(bool(r["BIG_WINNER_12M"]) for r in chosen) / len(chosen) if chosen else math.nan)
    return distribution


def permuted_score_control(rows: list[dict], seed: int = 20260920) -> list[dict]:
    rng = random.Random(seed)
    output = []
    groups = {}
    for row in rows:
        groups.setdefault((row["detector_id"], row["signal_asof"]), []).append(row)
    for group in groups.values():
        scorable = [r for r in group if r.get("detector_scorable")]
        flags = [bool(r.get("selected")) for r in scorable]
        rng.shuffle(flags)
        replacement = dict(zip((id(r) for r in scorable), flags))
        for row in group:
            copy = dict(row)
            copy["selected"] = replacement.get(id(row), False)
            output.append(copy)
    return output


def moving_block_bootstrap(months: list, statistic, *, block_length: int = 12,
                           simulations: int = 10_000, seed: int = 20260921) -> list[float]:
    """Resample complete monthly cross-sections, never individual security rows."""
    if block_length < 1 or not months:
        raise ValueError("invalid block bootstrap input")
    rng = random.Random(seed)
    n = len(months)
    result = []
    for _ in range(simulations):
        sample = []
        while len(sample) < n:
            start = rng.randrange(n)
            sample.extend(months[(start + offset) % n] for offset in range(block_length))
        result.append(statistic(sample[:n]))
    return result


def holm_adjust(p_values: dict[str, float]) -> dict[str, float]:
    ordered = sorted(p_values.items(), key=lambda pair: pair[1])
    adjusted, running = {}, 0.0
    count = len(ordered)
    for index, (name, value) in enumerate(ordered):
        running = max(running, min(1.0, (count - index) * value))
        adjusted[name] = running
    return adjusted
