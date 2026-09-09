"""Recover unique archived databases and named evidence bundles without changing originals."""
from __future__ import annotations

import argparse
from collections import defaultdict
from contextlib import closing
import datetime as dt
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import time
import zipfile

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.data_transfer import digest, read_manifest, validate_name

DB_SUFFIXES = (".db", ".sqlite", ".sqlite3")
SIDECARS = ("-wal", "-shm", "-journal")


def quoted(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def inspect_database(path: Path, *, pending_journal: bool = False) -> dict:
    """Immutable mode is safe only when no nonempty transaction journal was archived."""
    if pending_journal:
        return {"status": "REQUIRES_JOURNAL_AWARE_NORMALIZATION", "economic_readiness": False}
    before = digest(path)
    started = time.monotonic()
    with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)) as conn:
        conn.execute("PRAGMA query_only=ON")
        conn.execute("PRAGMA trusted_schema=OFF")
        conn.set_progress_handler(lambda: int(time.monotonic() - started > 90), 10000)
        integrity = [r[0] for r in conn.execute("PRAGMA integrity_check")]
        foreign = conn.execute("PRAGMA foreign_key_check").fetchall()
        tables = {}
        for (name,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
            if name.startswith("sqlite_"):
                continue
            cols = [r[1] for r in conn.execute("PRAGMA table_info(" + quoted(name) + ")")]
            row = {"columns": cols, "rows": conn.execute("SELECT COUNT(*) FROM " + quoted(name)).fetchone()[0]}
            # Date ranges measure coverage only; never inspect return/profit values or ledger decisions.
            for col in ("date", "asof_date", "asof", "ex_date", "payment_date", "dt_refer"):
                if col in cols:
                    mn, mx, n = conn.execute("SELECT MIN(" + quoted(col) + "),MAX(" + quoted(col) + "),COUNT(DISTINCT " + quoted(col) + ") FROM " + quoted(name)).fetchone()
                    row.setdefault("date_ranges", {})[col] = {"min": mn, "max": mx, "distinct": n}
            if "ticker" in cols:
                row["distinct_tickers"] = conn.execute("SELECT COUNT(DISTINCT ticker) FROM " + quoted(name)).fetchone()[0]
            tables[name] = row
    if digest(path) != before:
        raise ValueError("Read-only database inspection changed bytes")
    return {"status": "INTEGRITY_PASS" if integrity == ["ok"] and not foreign else "INTEGRITY_FAILURE",
            "integrity_check": integrity, "foreign_key_violations": len(foreign), "sha256_after_read": before,
            "tables": tables, "economic_readiness": False}


def restore(archive_path: Path, archive_sha256: str, destination: Path,
            bundles: dict[str, str] | None = None, max_bytes: int = 6_000_000_000) -> dict:
    bundles = bundles or {}
    destination = destination.absolute()
    if destination.exists():
        raise FileExistsError(destination)
    if any(p.is_symlink() or p.is_junction() for p in (destination, *destination.parents)):
        raise ValueError("Destination traverses a link")
    if digest(archive_path) != archive_sha256:
        raise ValueError("Archive checksum mismatch")
    for label, prefix in bundles.items():
        validate_name(label)
        validate_name(prefix)
        if "/" in label:
            raise ValueError("Bundle label must be one path component")
    with zipfile.ZipFile(archive_path) as archive:
        manifest, _ = read_manifest(archive)
        all_rows = {r["path"].casefold(): r for r in manifest["files"]}
        db_rows = [r for r in manifest["files"] if r["path"].lower().endswith(DB_SUFFIXES)]
        selected = {r["path"]: r for r in db_rows}
        for row in db_rows:
            for suffix in SIDECARS:
                name = row["path"] + suffix
                if name.casefold() in all_rows:
                    sidecar = all_rows[name.casefold()]
                    selected[sidecar["path"]] = sidecar
        bundle_rows = {}
        for label, prefix in bundles.items():
            rows = [r for r in manifest["files"] if r["path"].startswith(prefix + "/")]
            if not rows:
                raise ValueError("Empty evidence bundle: " + label)
            bundle_rows[label] = rows
            selected.update({r["path"]: r for r in rows})
        unique = {r["sha256"]: r for r in selected.values()}
        required = sum(r["size"] for r in unique.values()) + sum(r["size"] for rows in bundle_rows.values() for r in rows)
        parent = next(p for p in destination.parents if p.exists())
        if required > max_bytes or shutil.disk_usage(parent).free < required + 1024**3:
            raise ValueError("Restoration exceeds budget or disk space")
        destination.mkdir(parents=True)
        objects = destination / "objects"
        objects.mkdir()
        print(json.dumps({"stage": "restoration_started", "unique_objects": len(unique), "planned_bytes": required}), flush=True)
        for i, (sha, row) in enumerate(unique.items(), 1):
            target = objects / sha
            with archive.open("objects/" + sha) as source, target.open("xb") as sink:
                shutil.copyfileobj(source, sink, 1024 * 1024)
            if target.stat().st_size != row["size"] or digest(target) != sha:
                raise ValueError("Restored object hash differs: " + sha)
            if i % 100 == 0:
                print(json.dumps({"verified_objects": i}), flush=True)
        for label, rows in bundle_rows.items():
            prefix = bundles[label]
            for row in rows:
                relative = row["path"][len(prefix) + 1:]
                target = destination / "bundles" / label / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                with (objects / row["sha256"]).open("rb") as source, target.open("xb") as sink:
                    shutil.copyfileobj(source, sink)
                if digest(target) != row["sha256"]:
                    raise ValueError("Bundle copy hash differs")
    aliases = defaultdict(list)
    for row in db_rows:
        aliases[row["sha256"]].append(row["path"])
    databases = []
    for sha, names in aliases.items():
        journals = [all_rows[(name + suffix).casefold()] for name in names
                    for suffix in ("-wal", "-journal") if (name + suffix).casefold() in all_rows]
        path = objects / sha
        inspection = inspect_database(path, pending_journal=any(r["size"] for r in journals))
        databases.append({"sha256": sha, "local_path": str(path), "original_aliases": names, "inspection": inspection})
        print(json.dumps({"database": sha[:12], "status": inspection["status"]}), flush=True)
    result = {"schema_version": 1, "created_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "archive_sha256": archive_sha256, "archive_path": str(archive_path),
              "database_paths": len(db_rows), "database_unique_objects": len(databases),
              "restored_unique_objects": len(unique), "restored_bytes_including_bundle_copies": required,
              "databases": databases, "bundles": {k: {"local_path": str(destination / "bundles" / k),
              "source_prefix": bundles[k], "files": len(rows)} for k, rows in bundle_rows.items()},
              "path_map": {name: {"local_path": str(objects / row["sha256"]), "sha256": row["sha256"], "size": row["size"]} for name, row in selected.items()},
              "originals_modified": False, "source_completeness_certified": False, "new_economic_valuations": 0}
    (destination / "catalog.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--archive-sha256", required=True)
    parser.add_argument("--bundle", action="append", default=[], help="label=original/prefix")
    args = parser.parse_args()
    bundles = dict(item.split("=", 1) for item in args.bundle)
    result = restore(args.archive, args.archive_sha256, args.destination, bundles)
    print(json.dumps({"database_paths": result["database_paths"], "database_unique_objects": result["database_unique_objects"], "restored_unique_objects": result["restored_unique_objects"]}), flush=True)


if __name__ == "__main__":
    main()
