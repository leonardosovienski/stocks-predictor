"""Synthetic selector tests; no operational database or scientific execution."""

from contextlib import closing
import hashlib
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stocks_predictor import operational_store
from cain_bundle_selection import BACKUP, select_metadata


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir="C:/STOCKS/work")
        self.area = Path(self.temp.name)
        self.root = self.area / "repo"
        self.root.mkdir()
        self.path = self.area / BACKUP
        self.path.parent.mkdir(parents=True)
        operational_store.initialize(self.path)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute(
                "INSERT INTO source_versions VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    "TEST-SOURCE",
                    "TEST",
                    "TEST",
                    "v1",
                    "test-policy",
                    "0" * 64,
                    "https://example.invalid",
                    "test",
                    "2026-09-10T00:00:00Z",
                ),
            )
            db.execute(
                "INSERT INTO prices_raw VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                ("2026-09-09", "TEST3", "02", "010", 10, 11, 9, 10, 100, 10, 1, "TEST-SOURCE"),
            )
        self.sha = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.spec = dict(
            source_ids=["TEST-SOURCE"],
            observed_before="2026-09-11T00:00:00Z",
            start="2026-09-09",
            end="2026-09-09",
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_exact_existing_selector_and_preservation(self):
        first = select_metadata(self.root, self.sha, self.spec)
        assert first == select_metadata(self.root, self.sha, self.spec)
        assert first["row_count"] == 1 and first["redistribution"] == "UNKNOWN"
        from research_bundle import bounded

        bounded(first)
        assert "bars" not in first and first["capital_enabled"] is False
        assert hashlib.sha256(self.path.read_bytes()).hexdigest() == self.sha

    def test_future_source_rejected(self):
        self.spec["observed_before"] = "2026-09-09T23:00:00Z"
        with self.assertRaisesRegex(ValueError, "after the cutoff"):
            select_metadata(self.root, self.sha, self.spec)

    def test_unpinned_or_wide_or_missing_selection_rejected(self):
        for expected, spec in [
            ("1" * 64, self.spec),
            (self.sha, dict(self.spec, end="2026-09-10")),
            (self.sha, dict(self.spec, source_ids=["ABSENT"])),
        ]:
            with self.subTest(spec=spec), self.assertRaises(ValueError):
                select_metadata(self.root, expected, spec)

    def test_row_budget_is_enforced_before_materialization(self):
        from unittest.mock import patch
        with closing(sqlite3.connect(self.path)) as db, db:
            db.executemany('INSERT INTO prices_raw VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                           [('2026-09-09', f'BUDGET{i}', '02', '010', 10, 11, 9, 10, 100, 10, 1, 'TEST-SOURCE')
                            for i in range(500)])
        sha = hashlib.sha256(self.path.read_bytes()).hexdigest()
        with patch('stocks_predictor.dataset_selection.materialize', side_effect=AssertionError('must not load')):
            with self.assertRaisesRegex(ValueError, 'row budget'):
                select_metadata(self.root, sha, self.spec)

    def test_nonempty_journal_rejected(self):
        Path(str(self.path) + "-journal").write_bytes(b"UNCOMMITTED")
        with self.assertRaisesRegex(ValueError, "standalone"):
            select_metadata(self.root, self.sha, self.spec)


if __name__ == "__main__":
    unittest.main()

