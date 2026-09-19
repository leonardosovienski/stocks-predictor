"""SIGNAL_GENERATION_STAGE.

Only decision-time observations are accepted. Outcome artifacts and vocabulary
are rejected before any ranking is produced.
"""

from __future__ import annotations

import ast
import csv
import math
from pathlib import Path

from common import canonical_hash, first_session_after, rank_top_twenty


FORBIDDEN_ARTIFACT_TOKENS = {
    "future_returns", "winner_labels", "winner_episodes", "winner_lists",
    "future_peak", "future_drawdown", "winner_cards", "labels", "outcomes",
}


def assert_outcome_firewall(input_paths) -> None:
    for raw in input_paths:
        normalized = str(raw).replace("\\", "/").lower()
        parts = set(Path(normalized).parts)
        if any(token in normalized or token in parts for token in FORBIDDEN_ARTIFACT_TOKENS):
            raise PermissionError(f"outcome artifact forbidden in signal stage: {raw}")


def assert_module_dependency_firewall(path: str | Path) -> None:
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name.lower() for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [(node.module or "").lower()]
        else:
            continue
        if any("outcome_stage" in name or "evaluation_stage" in name for name in names):
            raise AssertionError("signal stage imports a post-freeze module")


def require_available(record: dict, signal_asof: str) -> None:
    available = record.get("available_at")
    if not available:
        raise ValueError("input lacks available_at")
    if available > signal_asof:
        raise ValueError("future information crossed signal_asof")


def score_input(record: dict, definition: dict) -> float | None:
    """Read a pre-registered score field; no outcome-aware transformations."""
    require_available(record, record["signal_asof"])
    value = record.get(definition["score_field"])
    if value is None:
        return None
    value = float(value)
    return value if math.isfinite(value) else None


def generate_rankings(records: list[dict], detector_registry: dict,
                      sessions: list[str], metadata: dict) -> list[dict]:
    staged = []
    for source in records:
        detector_id = source["detector_id"]
        definition = detector_registry[detector_id]
        asof = source["signal_asof"]
        eligible = bool(source.get("universe_eligible"))
        try:
            score = score_input(source, definition) if eligible else None
        except ValueError:
            score = None
            reason = "NOT_SCORABLE_MISSING_PIT_INPUT"
        else:
            reason = "" if score is not None else source.get(
                "not_scorable_reason", "NOT_SCORABLE_MISSING_PIT_INPUT")
        staged.append({
            "signal_asof": asof,
            "execution_time": first_session_after(asof, sessions),
            "ticker": source["ticker"],
            "detector_id": detector_id,
            "replay_fidelity": definition["replay_fidelity"],
            "scientific_historical_status": definition["scientific_historical_status"],
            "universe_eligible": eligible,
            "detector_scorable": eligible and score is not None,
            "not_scorable_reason": reason if eligible and score is None else "",
            "required_input_status": "AVAILABLE_PIT" if score is not None else "UNAVAILABLE",
            "score": score,
            "input_hash": canonical_hash(source),
            "config_hash": metadata["config_hash"],
            "code_commit": metadata["code_commit"],
            "dataset_versions": metadata["dataset_versions"],
        })
    output = []
    groups = {}
    for row in staged:
        groups.setdefault((row["detector_id"], row["signal_asof"]), []).append(row)
    for (detector_id, _), rows in sorted(groups.items()):
        output.extend(rank_top_twenty(rows, detector_registry[detector_id]["direction"]))
    return sorted(output, key=lambda row: (
        row["detector_id"], row["signal_asof"], row["ticker"]))


def read_decision_inputs(path: str | Path) -> list[dict]:
    assert_outcome_firewall([path])
    with Path(path).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))
