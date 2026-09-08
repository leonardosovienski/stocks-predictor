"""Archive the complete Stocks workspace without modifying any source files."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import sysconfig
import time
import zipfile

CHAT = Path(__file__).resolve().parents[2]
MAIN = Path(r"C:\Users\Superleo13\stocks-predictor-work")
RESEARCH = MAIN / ".local-research/stocks-session-20260907/work/stocks-predictor"
OUT = CHAT / "outputs/EXPORTACAO_STOCKS_20260908"
STAGING = Path(r"E:\Stocks-Export-Staging-20260908")
ROOTS = {"project": MAIN, "session": CHAT,
         "python313-packages": Path(sysconfig.get_paths()["purelib"])}
LIMIT = 1_500_000_000
COMPRESSED = {".zip", ".whl", ".gz", ".png", ".jpg", ".jpeg", ".7z"}


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path, value):
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def git(path, *args):
    return subprocess.check_output(["git", "-C", str(path), *args], encoding="utf-8",
                                   env=os.environ | {"GIT_OPTIONAL_LOCKS": "0"}).strip()


def inventory():
    entries = []
    empty_directories = []
    for label, root in ROOTS.items():
        for directory, dirs, names in os.walk(root, followlinks=False,
                                               onerror=lambda error: (_ for _ in ()).throw(error)):
            base = Path(directory)
            for name in dirs[:]:
                child = base / name
                if child.resolve() == OUT.resolve():
                    dirs.remove(name)
                elif child.is_symlink() or child.is_junction():
                    raise RuntimeError(f"Unreviewed filesystem link: {child}")
            dirs.sort()
            if not dirs and not names:
                empty_directories.append(label + "/" + base.relative_to(root).as_posix())
            for name in sorted(names):
                path = base / name
                if path.is_symlink():
                    raise RuntimeError(f"Unreviewed file link: {path}")
                stat = path.stat()
                if name.endswith(("-wal", "-journal")) and stat.st_size:
                    raise RuntimeError(f"Live database journal requires a consistent snapshot: {path}")
                entries.append({"path": label + "/" + path.relative_to(root).as_posix(),
                                "source": path, "size": stat.st_size,
                                "mtime_ns": stat.st_mtime_ns})
    return entries, empty_directories


def main():
    if sys.version_info[:2] != (3, 13):
        raise RuntimeError("Use global Python 3.13")
    sys.stdout.reconfigure(encoding="utf-8")
    if list(OUT.glob("stocks-*.zip")) or (OUT / "MANIFESTO.json").exists():
        raise FileExistsError("An export already exists; never overwrite it")
    STAGING.mkdir(parents=True, exist_ok=False)
    OUT.mkdir(parents=True, exist_ok=True)
    snapshots = {
        label: {"head": git(path, "rev-parse", "HEAD"),
                "branch": git(path, "branch", "--show-current"),
                "status": git(path, "status", "--porcelain=v1"),
                "refs": git(path, "show-ref")}
        for label, path in (("main", MAIN), ("research", RESEARCH))
    }
    subprocess.run(["git", "-C", str(MAIN), "bundle", "create",
                    str(OUT / "HISTORICO_GIT.bundle"), "--all"], check=True)
    subprocess.run(["git", "-C", str(MAIN), "bundle", "verify",
                    str(OUT / "HISTORICO_GIT.bundle")], check=True, capture_output=True)
    shutil.copyfile(Path(r"C:\Users\Superleo13\.codex\attachments\c289c038-e493-40cb-886b-5052bebfb6ff\pasted-text.txt"),
                    OUT / "PEDIDO_ORIGINAL.md")
    write_json(OUT / "AMBIENTE_ORIGINAL.json", {
        "python": sys.version, "python_executable": sys.executable,
        "platform": platform.platform(), "machine": platform.machine(),
        "packages": sorted([{"name": d.metadata["Name"], "version": d.version}
                            for d in importlib.metadata.distributions()], key=lambda x: x["name"].lower()),
        "core_precedence": "project/.local-research/stocks-session-20260907/work/runtime (Core 3.2.0) before archived global packages (Core 3.1.0)",
        "python_installer_included": False, "global_packages_are_a_snapshot_not_an_installation": True,
    })
    write_json(OUT / "ESTADO_PARA_RETOMADA.json", {
        "git": snapshots, "roots": {k: str(v) for k, v in ROOTS.items()},
        "research_checkout": "project/.local-research/stocks-session-20260907/work/stocks-predictor",
        "research_root": "project/.local-research/stocks-session-20260907",
        "main_database": "project/data/stocks.db",
        "source_revision_13": "fully validated and integrated; checkout HEAD 68ce89dbdd7b32341fd3e848bd444d0a88bc5444",
        "source_revision_14": "source audit validated with global Python 3.13.14 during migration; not integrated into original checkout",
        "source_manifest_14": "3b36e2416e44f2b0a30e88d4306e00cdc74a7302c6e9b0e33950a893ea169bda",
        "audit_14": "session/work/migration-20260908/validation-14/auditoria-fontes-14.json",
        "audit_14_sha256": "f27461eeef0c86d5df0727dae73b3d1c4b9ed817b2c8423f2d2649c88d6a67a8",
        "remaining": {"payment_dates": 24, "net_values": 52, "corporate_action_entries": 28,
                      "uncertified_inventory_intervals": 1248},
        "economic_status": "BLOCKED_MISSING_EVIDENCE", "profit": None, "future_profit_projection": None,
        "new_historical_return_evaluations_during_migration": 0,
        "frozen_hypotheses": "H1-H20", "administrative_search_counts": [53, 55],
        "intact_holdout_established": False,
        "tests_last_code_revision": {"code": "d2edbea804623a412b3ff3fe90c8b7638074b885", "full_suite": 735, "wheel_suite": 166},
        "original_sources_modified": False,
        "scope": "Stocks project, complete preserved research, this task's local files, original request, Git and Python package snapshot. Not a backup of all personal files or Windows.",
        "exclusions": ["this export directory (prevents recursive self-inclusion)",
                       "Windows/Python/Git installations, account credentials and unrelated user folders"],
        "legacy_paths": "Keep historical evidence bytes unchanged; resolve original path prefixes using MAPEAMENTO_CAMINHOS.json generated by restoration.",
    })
    entries, empty_directories = inventory()
    total = sum(e["size"] for e in entries)
    print(json.dumps({"phase": "inventory", "files": len(entries), "bytes": total}), flush=True)
    if shutil.disk_usage(STAGING).free < total + 1_000_000_000:
        # Compression is expected to help, but never assume it for disk safety.
        raise RuntimeError("Insufficient worst-case free space for export")
    archive = None
    parts = []
    records = []
    processed = 0
    last_progress = time.monotonic()
    part_bytes = 0
    try:
        for i, entry in enumerate(entries):
            if archive is None or part_bytes + entry["size"] > LIMIT:
                if archive is not None:
                    archive.close()
                name = f"stocks-{len(parts) + 1:03}.zip"
                parts.append(name)
                archive = zipfile.ZipFile(STAGING / name, "x", allowZip64=True, compresslevel=1)
                part_bytes = 0
            path = entry["source"]
            stat = path.stat()
            if (stat.st_size, stat.st_mtime_ns) != (entry["size"], entry["mtime_ns"]):
                raise RuntimeError(f"Source changed before archiving: {path}")
            info = zipfile.ZipInfo.from_file(path, entry["path"], strict_timestamps=False)
            info.compress_type = zipfile.ZIP_STORED if path.suffix.lower() in COMPRESSED else zipfile.ZIP_DEFLATED
            info.compress_level = 1
            sha = hashlib.sha256()
            copied = 0
            with path.open("rb") as source, archive.open(info, "w", force_zip64=True) as target:
                while chunk := source.read(1024 * 1024):
                    sha.update(chunk)
                    copied += len(chunk)
                    target.write(chunk)
            stat = path.stat()
            if copied != entry["size"] or (stat.st_size, stat.st_mtime_ns) != (entry["size"], entry["mtime_ns"]):
                raise RuntimeError(f"Source changed while archiving: {path}")
            records.append({k: v for k, v in entry.items() if k != "source"} |
                           {"archive": name, "sha256": sha.hexdigest()})
            processed += copied
            part_bytes += copied
            if time.monotonic() - last_progress > 10:
                print(json.dumps({"phase": "archive", "files": i + 1, "total_files": len(entries),
                                  "bytes": processed, "total_bytes": total, "part": name}), flush=True)
                last_progress = time.monotonic()
    finally:
        if archive is not None:
            archive.close()
    after, empty_after = inventory()
    if [(e["path"], e["size"], e["mtime_ns"]) for e in entries] != [(e["path"], e["size"], e["mtime_ns"]) for e in after]:
        raise RuntimeError("Workspace changed during snapshot; export is not certified")
    if empty_directories != empty_after:
        raise RuntimeError("Directory inventory changed during snapshot")
    for label, path in (("main", MAIN), ("research", RESEARCH)):
        if git(path, "rev-parse", "HEAD") != snapshots[label]["head"] or git(path, "show-ref") != snapshots[label]["refs"]:
            raise RuntimeError("Git refs changed during snapshot")
    protected = [r for r in records if r["path"].endswith((".db", ".db-wal", ".db-shm", ".sqlite", ".sqlite3"))]
    for record in protected:
        label, rel = record["path"].split("/", 1)
        if digest(ROOTS[label] / rel) != record["sha256"]:
            raise RuntimeError("Protected database bytes changed")
    archive_bytes = sum((STAGING / name).stat().st_size for name in parts)
    if shutil.disk_usage(OUT).free < archive_bytes + 1_000_000_000:
        raise RuntimeError("Archives preserved on E; insufficient C space for final transfer folder")
    for name in parts:
        shutil.copyfile(STAGING / name, OUT / name)
        if digest(STAGING / name) != digest(OUT / name):
            raise RuntimeError("Archive changed while copying from staging")
    write_json(OUT / "MANIFESTO.json", {"format": 1, "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "files": records, "file_count": len(records), "uncompressed_bytes": total,
               "empty_directories": empty_directories,
               "protected_database_files_rehashed": len(protected), "source_snapshot_unchanged": True})
    controls = {p.name: {"sha256": digest(p), "bytes": p.stat().st_size}
                for p in sorted(OUT.iterdir()) if p.is_file() and p.name not in {"CHECKSUMS.json", "SHA256SUMS.txt"}}
    write_json(OUT / "CHECKSUMS.json", controls)
    (OUT / "SHA256SUMS.txt").write_text("".join(f"{v['sha256']}  {k}\n" for k, v in controls.items()) +
                                       f"{digest(OUT / 'CHECKSUMS.json')}  CHECKSUMS.json\n", encoding="utf-8")
    print(json.dumps({"phase": "complete", "files": len(records), "uncompressed_bytes": total,
                      "parts": len(parts), "archive_bytes": sum((OUT / n).stat().st_size for n in parts),
                      "manifest_sha256": digest(OUT / "MANIFESTO.json")}), flush=True)


if __name__ == "__main__":
    main()
