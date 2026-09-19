"""One-time, hash-verified signal freeze."""
from __future__ import annotations
import csv, json
from datetime import datetime, timezone
from pathlib import Path
from common import SIGNAL_FIELDS, canonical_hash, sha256_file

def freeze_rows(rows, directory, metadata):
    directory = Path(directory); directory.mkdir(parents=True, exist_ok=True)
    if any(directory.iterdir()):
        raise FileExistsError("frozen_signals is not empty")
    target = directory / "signals.csv"
    with target.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SIGNAL_FIELDS, extrasaction="raise")
        writer.writeheader()
        for row in rows:
            if row["created_by_stage"] != "SIGNAL_GENERATION":
                raise ValueError("invalid signal producer")
            writer.writerow({k: ("true" if v is True else "false" if v is False else
                "" if v is None else v) for k, v in row.items()})
    manifest = {"schema_version":"BIG_WINNER_PRICE_SIGNAL_FREEZE_V1", "status":"FROZEN",
        "file":"signals.csv", "sha256":sha256_file(target), "row_count":len(rows),
        "detectors":sorted({r["detector_id"] for r in rows}),
        "period":{"start":min(r["signal_asof"] for r in rows), "end":max(r["signal_asof"] for r in rows)},
        **metadata, "created_at":datetime.now(timezone.utc).isoformat()}
    manifest["manifest_payload_sha256"] = canonical_hash(manifest)
    path = directory / "MANIFEST.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    return path

def verify_freeze(path):
    path = Path(path); manifest = json.loads(path.read_text(encoding="utf-8"))
    expected = manifest.pop("manifest_payload_sha256")
    if canonical_hash(manifest) != expected:
        raise ValueError("SIGNAL_FREEZE_INVALID: manifest")
    target = path.parent / manifest["file"]
    if sha256_file(target) != manifest["sha256"]:
        raise ValueError("SIGNAL_FREEZE_INVALID: signals")
    with target.open(newline="", encoding="utf-8") as f:
        if sum(1 for _ in csv.DictReader(f)) != manifest["row_count"]:
            raise ValueError("SIGNAL_FREEZE_INVALID: row count")
    return {**manifest, "manifest_payload_sha256":expected, "FREEZE_VALID":True}
