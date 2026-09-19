from __future__ import annotations

import csv
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))

import common
import controls
import evaluation_stage
import freeze
import outcome_stage
import signal_stage


def base_row(ticker="AAA3", score=1.0):
    return {
        "detector_id": "D", "signal_asof": "2020-01-31", "ticker": ticker,
        "universe_eligible": True, "detector_scorable": score is not None,
        "not_scorable_reason": "" if score is not None else "NOT_SCORABLE_MISSING_PIT_INPUT",
        "score": score,
    }


class ProtocolTests(unittest.TestCase):
    def test_signal_stage_cannot_read_outcomes(self):
        with self.assertRaises(PermissionError):
            signal_stage.assert_outcome_firewall(["labels/winner_labels.csv"])
        signal_stage.assert_module_dependency_firewall(ROOT / "lib" / "signal_stage.py")

    def test_available_at_contract_and_positive_control(self):
        signal_stage.require_available({"available_at": "2020-01-30"}, "2020-01-31")
        with self.assertRaises(ValueError):
            signal_stage.require_available({"available_at": "2020-02-01"}, "2020-01-31")
        self.assertTrue(controls.positive_leakage_control())

    def test_date_only_availability_is_next_session(self):
        sessions = ["2020-01-31", "2020-02-03", "2020-02-04"]
        self.assertEqual(common.conservative_available_at("2020-01-31", sessions), "2020-02-03")

    def test_next_open_execution(self):
        self.assertEqual(common.first_session_after("2020-01-31", ["2020-01-31", "2020-02-03"]),
                         "2020-02-03")

    def test_scorability_and_no_missing_as_zero(self):
        common.validate_scorability(base_row(score=1.0))
        row = base_row(score=None)
        common.validate_scorability(row)
        row["score"] = 0.0
        with self.assertRaises(ValueError):
            common.validate_scorability(row)

    def test_top20_and_tie_breaking(self):
        rows = [base_row(ticker=f"T{i:02d}3", score=1.0) for i in range(6)]
        ranked = common.rank_top_twenty(rows, "HIGHER_IS_BETTER")
        selected = [r["ticker"] for r in ranked if r["selected"]]
        self.assertEqual(selected, ["T003", "T013"])
        self.assertTrue(all(r["selection_size"] == 2 for r in ranked))

    def test_lower_is_better(self):
        rows = [base_row(ticker=f"T{i}3", score=float(i)) for i in range(5)]
        ranked = common.rank_top_twenty(rows, "LOWER_IS_BETTER")
        self.assertEqual([r["ticker"] for r in ranked if r["selected"]], ["T03"])

    def test_freeze_hashes_and_label_gate(self):
        metadata = {"code_commit": "abc", "config_hash": "cfg", "dataset_hashes": {"d": "hash"}}
        complete = {field: "" for field in common.SIGNAL_FIELDS}
        complete.update({"signal_asof": "2020-01-31", "ticker": "AAA3", "detector_id": "D",
                         "universe_eligible": True, "detector_scorable": True,
                         "selected": True, "created_by_stage": "SIGNAL_GENERATION"})
        with tempfile.TemporaryDirectory() as tmp:
            manifest = freeze.freeze_rows([complete], Path(tmp) / "frozen_signals", metadata)
            self.assertTrue(outcome_stage.require_valid_freeze(manifest)["FREEZE_VALID"])
            loaded = outcome_stage.load_frozen_signals(manifest)
            self.assertIs(loaded[0]["selected"], True)
            signal_file = manifest.parent / "signals.csv"
            signal_file.write_text(signal_file.read_text(encoding="utf-8") + "tamper\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "SIGNAL_FREEZE_INVALID"):
                outcome_stage.require_valid_freeze(manifest)

    def test_labels_cannot_precede_freeze(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                outcome_stage.require_valid_freeze(Path(tmp) / "MANIFEST.json")

    def test_corporate_action_separation(self):
        controls.corporate_action_signal_guard([{"available_at": "2020-01-30"}], "2020-01-31")
        with self.assertRaises(ValueError):
            controls.corporate_action_signal_guard([{"available_at": "2020-02-01"}], "2020-01-31")

    def test_outcome_horizon_last_session_on_or_before(self):
        values = [("2020-01-31", 100), ("2021-01-29", 131), ("2021-02-01", 140)]
        result = outcome_stage.calculate_path_outcome("2020-01-31", values)
        self.assertEqual(result["horizon_end"], "2021-01-29")
        self.assertTrue(result["BIG_WINNER_12M"])

    def test_nonstandard_terminal_is_not_estimable(self):
        result = outcome_stage.calculate_path_outcome("2020-01-31", [], "DELISTING_UNRESOLVED")
        self.assertFalse(result["outcome_estimable"])

    def test_episode_creation(self):
        rows = [
            {"ticker": "A3", "signal_asof": f"2020-0{i}-28", "BIG_WINNER_12M": value}
            for i, value in enumerate([True, True, False, True], 1)
        ]
        episodes = outcome_stage.create_winner_episodes(rows)
        self.assertEqual(len(episodes), 2)
        self.assertEqual(episodes[0]["episode_end"], "2020-02-28")

    def test_episode_detection_and_early_hit(self):
        episode = {"ticker": "A3", "episode_id": "A3-1", "episode_start": "2020-01-31",
                   "episode_end": "2020-03-31"}
        signals = [{"ticker": "A3", "signal_asof": "2020-02-28",
                    "detector_scorable": True, "selected": True}]
        result = outcome_stage.classify_episode(episode, signals, 100, 200, 140)
        self.assertEqual(result["classification"], "EARLY_HIT")
        self.assertAlmostEqual(result["fraction_of_move_remaining"], 0.6)

    def test_matched_random_preserves_universe_and_k(self):
        rows = []
        for asof in ("2020-01-31", "2020-02-28"):
            for i in range(5):
                rows.append({"signal_asof": asof, "detector_scorable": True,
                             "selection_size": 1, "BIG_WINNER_12M": i == 0})
        dist = evaluation_stage.matched_random(rows, simulations=25, seed=1)
        self.assertEqual(len(dist), 25)
        self.assertTrue(all(0 <= value <= 1 for value in dist))

    def test_bootstrap_preserves_cross_sections(self):
        months = [[{"month": i, "ticker": j} for j in range(3)] for i in range(5)]
        observed = evaluation_stage.moving_block_bootstrap(
            months, lambda sample: sum(len(month) for month in sample),
            block_length=2, simulations=10, seed=1)
        self.assertEqual(observed, [15] * 10)

    def test_negative_score_permutation_control(self):
        rows = [{"detector_id": "D", "signal_asof": "2020-01-31",
                 "detector_scorable": True, "selected": i < 2} for i in range(6)]
        shuffled = evaluation_stage.permuted_score_control(rows, seed=1)
        self.assertEqual(sum(r["selected"] for r in shuffled), 2)

    def test_holm_is_monotone(self):
        adjusted = evaluation_stage.holm_adjust({"a": 0.01, "b": 0.02, "c": 0.5})
        self.assertLessEqual(adjusted["a"], adjusted["b"])
        self.assertLessEqual(adjusted["b"], adjusted["c"])


if __name__ == "__main__":
    unittest.main()
