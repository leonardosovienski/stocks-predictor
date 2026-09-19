"""Adversarial controls shared by the pre-freeze audit and test suite."""

from __future__ import annotations

from signal_stage import require_available


def positive_leakage_control() -> bool:
    synthetic = {
        "signal_asof": "2020-01-31",
        "available_at": "2021-01-31",
        "future_feature": 1.0,
    }
    try:
        require_available(synthetic, synthetic["signal_asof"])
    except ValueError:
        return True
    return False


def corporate_action_signal_guard(events: list[dict], signal_asof: str) -> None:
    for event in events:
        require_available(event, signal_asof)
