"""Immutable-by-hash signal freeze contract."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from common import SIGNAL_FIELDS, canonical_hash, sha256_file


def freeze_rows(rows: list[dict], directory: str | Path, metadata: dict) -> Path:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    if any(directory.iterdir()):
        raise FileExistsError("frozen_signals must be empty before the one-time freeze")
    signal_file = directory / "signals.csv"
    with signal_file.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=SIGNAL_FIELDS, extrasaction="raise")
        writer.writeheader()
        for row in rows:
            if row.get("created_by_stage") != "SIGNAL_GENERATION":
                raise ValueError("only SIGNAL_GENERATION rows can be frozen")
            encoded = {}
            for field in SIGNAL_FIELDS:
                value = row.get(field)
                if isinstance(value, bool):
                    value = "true" if value else "false"
                elif isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False, sort_keys=True,
                                       separators=(",", ":"))
                elif value is None:
                    value = ""
                encoded[field] = value
            writer.writerow(encoded)
    periods = sorted({row["signal_asof"] for row in rows})
    detectors = sorted({row["detector_id"] for row in rows})
    manifest = {
        "schema_version": "BIG_WINNER_SIGNAL_FREEZE_V1",
        "status": "FROZEN",
        "file": signal_file.name,
        "sha256": sha256_file(signal_file),
        "row_count": len(rows),
        "detectors": detectors,
        "period": {"start": periods[0] if periods else None,
                   "end": periods[-1] if periods else None},
        "code_commit": metadata["code_commit"],
        "config_hash": metadata["config_hash"],
        "dataset_hashes": metadata["dataset_hashes"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    manifest["manifest_payload_sha256"] = canonical_hash(manifest)
    manifest_path = directory / "MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                             encoding="utf-8")
    return manifest_path


def verify_freeze(manifest_path: str | Path) -> dict:
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload_hash = manifest.pop("manifest_payload_sha256", None)
    if canonical_hash(manifest) != payload_hash:
        raise ValueError("SIGNAL_FREEZE_INVALID: manifest payload hash mismatch")
    signal_file = manifest_path.parent / manifest["file"]
    if sha256_file(signal_file) != manifest["sha256"]:
        raise ValueError("SIGNAL_FREEZE_INVALID: signal file hash mismatch")
    with signal_file.open(newline="", encoding="utf-8") as stream:
        count = sum(1 for _ in csv.DictReader(stream))
    if count != manifest["row_count"]:
        raise ValueError("SIGNAL_FREEZE_INVALID: row count mismatch")
    return {**manifest, "manifest_payload_sha256": payload_hash, "FREEZE_VALID": True}
