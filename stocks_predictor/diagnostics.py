"""Offline environment diagnostics using only the standard library.

Metadata compatibility is not proof that a dependency imports or that financial
operations are ready. Database inspection is opt-in and never runs migrations.
"""
import argparse
from contextlib import closing
from importlib import metadata
import json
from pathlib import Path
import re
import sqlite3
import sys


def _dependency(name: str, minimum: tuple[int, int], maximum_major: int) -> dict:
    try:
        version = metadata.version(name)
    except metadata.PackageNotFoundError:
        return {"version": None, "metadata_compatible": False, "status": "missing"}
    match = re.fullmatch(r"(\d+)\.(\d+)(?:\.(\d+))?", version)
    compatible = bool(match and minimum <= (int(match[1]), int(match[2])) < (maximum_major, 0))
    return {"version": version, "metadata_compatible": compatible,
            "status": "compatible_stable_release" if compatible else "unsupported_or_unverified_version"}


def inspect_database(path: Path) -> dict:
    path = path.resolve()
    result = {"path": str(path), "status": "missing", "read_only": True}
    if not path.is_file():
        return result
    try:
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=1.0)) as conn:
            conn.execute("PRAGMA query_only=ON")
            integrity = [row[0] for row in conn.execute("PRAGMA quick_check")]
            tables = [row[0] for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        result.update(status="ok" if integrity == ["ok"] else "integrity_failed",
                      quick_check=integrity, tables=tables)
    except sqlite3.Error as exc:
        result.update(status="unreadable", error=str(exc))
    return result


def diagnose(db_path: Path | None = None) -> dict:
    dependencies = {"predictor-core": _dependency("predictor-core", (3, 2), 4),
                    "PyYAML": _dependency("PyYAML", (6, 0), 7)}
    supported = (3, 13) <= sys.version_info[:2] < (3, 15)
    return {
        "python": {"version": sys.version.split()[0], "executable": sys.executable,
                   "supported": supported, "required": ">=3.13,<3.15"},
        "sqlite_version": sqlite3.sqlite_version,
        "dependencies": dependencies,
        "runtime_metadata_compatible": supported and all(
            dep["metadata_compatible"] for dep in dependencies.values()),
        "database": inspect_database(db_path) if db_path is not None else {"status": "not_requested"},
        "scope": "Offline metadata and optional SQLite quick_check; no dependency import, migration, or operational certification.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, help="Inspect this existing SQLite database in read-only mode")
    parser.add_argument("--check", action="store_true", help="Exit 1 for incompatible metadata or a failed requested DB inspection")
    args = parser.parse_args(argv)
    result = diagnose(args.db)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    database_ok = result["database"]["status"] in ("not_requested", "ok")
    return int(args.check and not (result["runtime_metadata_compatible"] and database_ok))


if __name__ == "__main__":
    raise SystemExit(main())
