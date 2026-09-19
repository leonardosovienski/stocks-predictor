"""Create a read-only receipt for the two dataset identities used by the gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DATASETS = {
    "ORIGINAL_PROJECT_DB": {
        "path": Path(r"C:\STOCKS\data\recovery-r2\objects\a22739794ba4a43a11544338d4a91e14cb6a0b1f7b132ab460f96d3359f63cf4"),
        "expected_sha256": "a22739794ba4a43a11544338d4a91e14cb6a0b1f7b132ab460f96d3359f63cf4",
    },
    "HISTORY_2016_2026": {
        "path": Path(r"C:\STOCKS\data\recovery-r2\objects\e21a89c38f2792c826291baa1175da4fe9dfbf626316635a536f7c28b250146a"),
        "expected_sha256": "e21a89c38f2792c826291baa1175da4fe9dfbf626316635a536f7c28b250146a",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def scalar(conn, statement, params=()):
    return conn.execute(statement, params).fetchone()[0]


def inspect(name: str, definition: dict) -> dict:
    path = definition["path"]
    before = sha256(path)
    if before != definition["expected_sha256"]:
        raise ValueError(f"{name}: source hash differs from catalog identity")
    uri = path.resolve().as_uri() + "?mode=ro&immutable=1"
    conn = sqlite3.connect(uri, uri=True)
    try:
        tables = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")}
        receipt = {
            "path": str(path), "sha256_before": before,
            "sqlite_quick_check": scalar(conn, "PRAGMA quick_check"),
            "tables": sorted(tables),
        }
        if "prices_raw" in tables:
            receipt["prices_raw"] = {
                "rows": scalar(conn, "SELECT COUNT(*) FROM prices_raw"),
                "distinct_dates": scalar(conn, "SELECT COUNT(DISTINCT date) FROM prices_raw"),
                "coverage_start": scalar(conn, "SELECT MIN(date) FROM prices_raw"),
                "coverage_end": scalar(conn, "SELECT MAX(date) FROM prices_raw"),
                "distinct_tickers": scalar(conn, "SELECT COUNT(DISTINCT ticker) FROM prices_raw"),
            }
        for table in ("adjustments", "fundamentals", "quarantine", "cash_events", "cash_event_coverage"):
            if table in tables:
                receipt[table] = {"rows": scalar(conn, f"SELECT COUNT(*) FROM {table}")}
    finally:
        conn.close()
    receipt["sha256_after"] = sha256(path)
    receipt["source_unchanged"] = receipt["sha256_after"] == before
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    catalog = Path(r"C:\STOCKS\data\CATALOG.json")
    result = {
        "schema_version": "BIG_WINNER_DATA_AUDIT_V1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "access_policy": "sqlite mode=ro&immutable=1",
        "catalog_path": str(catalog),
        "catalog_sha256": sha256(catalog),
        "datasets": {name: inspect(name, definition) for name, definition in DATASETS.items()},
        "economic_completeness_certified": False,
        "real_signal_generation_authorized_by_gate": False,
        "real_outcome_generation_authorized_by_gate": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
