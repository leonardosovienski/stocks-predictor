"""Verify and restore the Stocks export to a NEW folder, without touching originals."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sqlite3
import subprocess
import sys
import time
import zipfile


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def safe_path(root, name):
    parts = PurePosixPath(name).parts
    if not parts or name.startswith("/") or "\\" in name or ":" in name or "\x00" in name or any(p in (".", "..") for p in parts):
        raise ValueError(f"Unsafe path: {name!r}")
    if any(p.endswith((".", " ")) or re.fullmatch(r"(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(\..*)?", p) for p in parts):
        raise ValueError(f"Unsafe Windows name: {name!r}")
    path = root.joinpath(*parts).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Path leaves destination: {name!r}")
    return path


def verify_controls(package):
    controls = read(package / "CHECKSUMS.json")
    for name, expected in controls.items():
        path = safe_path(package, name)
        if not path.is_file() or path.stat().st_size != expected["bytes"] or digest(path) != expected["sha256"]:
            raise ValueError(f"Missing or changed transfer file: {name}")
    return controls


def write_json(path, data):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def restore(package, destination=None):
    if destination is not None:
        destination = destination.resolve()
        if destination.exists():
            raise FileExistsError("Choose a NEW destination directory; existing files are never overwritten")
        if destination.is_relative_to(package.resolve()):
            raise ValueError("Restore outside the transfer package")
    print("Verificando hashes dos arquivos de transporte...", flush=True)
    controls = verify_controls(package)
    manifest = read(package / "MANIFESTO.json")
    rows = manifest["files"]
    expected = {}
    for row in rows:
        safe_path(destination or package, row["path"])
        if row["path"] in expected:
            raise ValueError("Duplicate manifest member")
        if not re.fullmatch(r"stocks-\d{3}\.zip", row["archive"]) or row["archive"] not in controls:
            raise ValueError("Unverified archive")
        expected[row["path"]] = row
    if len(expected) != manifest["file_count"] or sum(r["size"] for r in rows) != manifest["uncompressed_bytes"]:
        raise ValueError("Inconsistent inventory totals")
    for name in manifest.get("empty_directories", []):
        safe_path(destination or package, name)
    if destination is not None:
        anchor = destination.parent
        while not anchor.exists():
            anchor = anchor.parent
        if shutil.disk_usage(anchor).free < manifest["uncompressed_bytes"] + 1_000_000_000:
            raise RuntimeError("Insufficient destination disk space")
        destination.mkdir(parents=True, exist_ok=False)
        for name in manifest.get("empty_directories", []):
            safe_path(destination, name).mkdir(parents=True, exist_ok=True)
    seen = set()
    count = 0
    last = time.monotonic()
    for archive in sorted({r["archive"] for r in rows}):
        with zipfile.ZipFile(package / archive) as source:
            for info in source.infolist():
                name = info.filename
                if name not in expected or name in seen:
                    raise ValueError(f"Unexpected or duplicate archive member: {name}")
                row = expected[name]
                if row["archive"] != archive or info.is_dir() or info.file_size != row["size"]:
                    raise ValueError(f"Wrong archive metadata: {name}")
                seen.add(name)
                target_path = safe_path(destination, name) if destination else None
                target = None
                if target_path is not None:
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    target = target_path.open("xb")
                sha = hashlib.sha256()
                copied = 0
                try:
                    with source.open(info) as stream:
                        while chunk := stream.read(1024 * 1024):
                            copied += len(chunk)
                            sha.update(chunk)
                            if target is not None:
                                target.write(chunk)
                finally:
                    if target is not None:
                        target.close()
                if copied != row["size"] or sha.hexdigest() != row["sha256"]:
                    raise ValueError(f"Changed payload: {name}")
                if target_path is not None:
                    os.utime(target_path, ns=(row["mtime_ns"], row["mtime_ns"]))
                count += 1
                if time.monotonic() - last > 10:
                    print(json.dumps({"phase": "restore" if destination else "verify", "files": count,
                                      "total": len(rows), "part": archive}), flush=True)
                    last = time.monotonic()
    if seen != set(expected):
        raise ValueError("Archive is missing manifest members")
    receipt = {"status": "VERIFIED", "payloads_verified": count,
               "bytes_verified": manifest["uncompressed_bytes"],
               "manifest_sha256": digest(package / "MANIFESTO.json"),
               "original_sources_modified": False}
    if destination is None:
        print(json.dumps(receipt), flush=True)
        return receipt
    # Only relocated Git administrative pointers change, after byte verification.
    main = destination / "project"
    research = main / ".local-research/stocks-session-20260907/work/stocks-predictor"
    admin = main / ".git/worktrees/stocks-predictor"
    git_changes = []
    for path, content in ((research / ".git", "gitdir: " + os.path.relpath(admin, research).replace("\\", "/") + "\n"),
                          (admin / "gitdir", str(research / ".git").replace("\\", "/") + "\n")):
        before = digest(path)
        path.write_text(content, encoding="utf-8", newline="\n")
        git_changes.append({"path": path.relative_to(destination).as_posix(), "before": before, "after": digest(path)})
    state = read(package / "ESTADO_PARA_RETOMADA.json")
    git_results = {}
    if shutil.which("git"):
        for label, root in (("main", main), ("research", research)):
            def git(*args):
                return subprocess.check_output(["git", "-C", str(root), *args], encoding="utf-8",
                                               env=os.environ | {"GIT_OPTIONAL_LOCKS": "0"}).strip()
            head = git("rev-parse", "HEAD")
            status = git("status", "--porcelain=v1")
            if head != state["git"][label]["head"] or status != state["git"][label]["status"]:
                raise RuntimeError(f"Restored Git state differs: {label}")
            git_results[label] = {"head": head, "status_matches_original": True}
        subprocess.run(["git", "-C", str(main), "fsck", "--full"], check=True, capture_output=True)
    else:
        git_results["not_checked"] = "Git is not installed; file restoration succeeded"
    database_checks = []
    for row in rows:
        if not row["path"].endswith((".db", ".sqlite", ".sqlite3")):
            continue
        path = safe_path(destination, row["path"])
        with path.open("rb") as stream:
            if stream.read(16) != b"SQLite format 3\x00":
                continue
        wal = path.with_name(path.name + "-wal")
        if wal.exists() and wal.stat().st_size:
            raise RuntimeError("Nonempty WAL was not expected in this snapshot")
        connection = sqlite3.connect(path.as_uri() + "?mode=ro&immutable=1", uri=True)
        try:
            result = connection.execute("PRAGMA quick_check").fetchall()
        finally:
            connection.close()
        if result != [("ok",)] or digest(path) != row["sha256"]:
            raise RuntimeError(f"Restored database integrity failure: {row['path']}")
        database_checks.append({"path": row["path"], "quick_check": "ok", "unchanged": True})
    # Copy the transport instructions as a separate directory, not over archived evidence.
    guide = destination / "migration-guide"
    guide.mkdir()
    for name in controls:
        if not name.startswith("stocks-") and name not in {"MANIFESTO.json", "HISTORICO_GIT.bundle"}:
            shutil.copyfile(package / name, guide / name)
    old_root = state["roots"]["project"] + r"\.local-research\stocks-session-20260907"
    mapping = {state["roots"]["project"]: str(main), state["roots"]["session"]: str(destination / "session"),
               old_root: str(main / ".local-research/stocks-session-20260907"),
               r"C:\Users\Superleo13\Documents\Codex\2026-09-06\files-pasted-by-the-user-autonomous": str(main / ".local-research/stocks-session-20260907")}
    write_json(destination / "MAPEAMENTO_CAMINHOS.json", mapping)
    receipt.update({"destination": str(destination), "git": git_results, "git_pointer_changes": git_changes,
                    "sqlite_databases": database_checks, "sqlite_count": len(database_checks),
                    "historical_evidence_paths_rewritten": False})
    write_json(destination / "RECIBO_RESTAURACAO.json", receipt)
    print(json.dumps(receipt, ensure_ascii=False), flush=True)
    return receipt


def main():
    if sys.version_info[:2] != (3, 13):
        raise RuntimeError("Use Python global 3.13, sem venv")
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    options = parser.add_mutually_exclusive_group(required=True)
    options.add_argument("--destination", type=Path, help="NEW directory, for example C:\\Stocks")
    options.add_argument("--verify-only", action="store_true", help="Verify everything without extracting")
    args = parser.parse_args()
    restore(Path(__file__).resolve().parent, args.destination)


if __name__ == "__main__":
    main()
