"""Seal current code hashes and fresh operational validation receipts."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.verify_operational_evidence import canonical_sha, code_paths  # noqa: E402


def _relative(path: Path) -> str:
    resolved = path.resolve()
    if not resolved.is_relative_to(ROOT.resolve()):
        raise ValueError("operational evidence must be stored inside the repository")
    return resolved.relative_to(ROOT.resolve()).as_posix()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--real", type=Path, required=True)
    parser.add_argument("--capacity", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    real = json.loads(args.real.read_text(encoding="utf-8"))
    capacity = json.loads(args.capacity.read_text(encoding="utf-8"))
    if real.get("status") != "PASS" or real.get("rows") != 55986:
        raise ValueError("real operational validation is not the preserved 55,986-row population")
    if capacity.get("status") != "PASS" or capacity.get("rows") != 250000:
        raise ValueError("capacity validation is not the required 250,000-row run")
    hashes = [
        {"path": name, "sha256": canonical_sha(ROOT / name)} for name in sorted(code_paths(ROOT))
    ]
    canonical = json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode("utf-8")
    record = {
        "schema_version": "current-operational-evidence/1",
        "status": "LOCAL_VALIDATED_CI_PENDING",
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "code_text_hash_policy": "UTF-8 file bytes with CRLF normalized to LF",
        "code_population_sha256": hashlib.sha256(canonical).hexdigest(),
        "current_code_sha256_lf": hashes,
        "real_validation": _relative(args.real),
        "capacity_validation": _relative(args.capacity),
        "capital_enabled": False,
        "profit_certified": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": "PASS", "code_files": len(hashes), "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
