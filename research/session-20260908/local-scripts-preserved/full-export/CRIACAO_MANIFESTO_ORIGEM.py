"""Finalize the completed ZIPs on E after C had insufficient free space."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
import zipfile

OUT = Path(r"E:\EXPORTACAO_STOCKS_20260908")
CHAT = Path(r"C:\Users\Superleo13\Documents\Codex\2026-09-07\lei-2")
spec = importlib.util.spec_from_file_location("builder", CHAT / "work/migration-20260908/build_export.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    entries, empty_dirs = builder.inventory()
    if len(entries) != 56217 or sum(e["size"] for e in entries) != 25914517899:
        raise RuntimeError("Source inventory changed since the completed archive build")
    archive_entries = {}
    for path in sorted(OUT.glob("stocks-*.zip")):
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                if info.filename in archive_entries:
                    raise RuntimeError("Duplicate archive path")
                archive_entries[info.filename] = (path.name, info.file_size)
    if set(archive_entries) != {e["path"] for e in entries}:
        raise RuntimeError("ZIP inventory differs from complete source inventory")
    records = []
    last = time.monotonic()
    for index, entry in enumerate(entries):
        archive, size = archive_entries[entry["path"]]
        if size != entry["size"]:
            raise RuntimeError("Changed source size")
        sha = builder.digest(entry["source"])
        stat = entry["source"].stat()
        if (stat.st_size, stat.st_mtime_ns) != (entry["size"], entry["mtime_ns"]):
            raise RuntimeError("Source changed during hashing")
        records.append({k: v for k, v in entry.items() if k != "source"} | {"archive": archive, "sha256": sha})
        if time.monotonic() - last > 10:
            print(json.dumps({"phase": "source-hash", "files": index + 1, "total": len(entries)}), flush=True)
            last = time.monotonic()
    after, empty_after = builder.inventory()
    if [(e["path"], e["size"], e["mtime_ns"]) for e in entries] != [(e["path"], e["size"], e["mtime_ns"]) for e in after] or empty_after != empty_dirs:
        raise RuntimeError("Source snapshot changed")
    state = json.loads((OUT / "ESTADO_PARA_RETOMADA.json").read_text(encoding="utf-8"))
    for label, root in (("main", builder.MAIN), ("research", builder.RESEARCH)):
        if builder.git(root, "rev-parse", "HEAD") != state["git"][label]["head"] or builder.git(root, "status", "--porcelain=v1") != state["git"][label]["status"]:
            raise RuntimeError("Git state changed")
    manifest = {"format": 1, "files": records, "file_count": len(records),
                "uncompressed_bytes": sum(r["size"] for r in records), "empty_directories": empty_dirs,
                "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "source_snapshot_unchanged": True,
                "all_source_files_hashed": True,
                "payload_verification": "Pending full restore: every archived payload must match this source hash"}
    builder.write_json(OUT / "MANIFESTO.json", manifest)
    print(json.dumps({"phase": "transport-hash", "parts": 18}), flush=True)
    controls = {p.name: {"sha256": builder.digest(p), "bytes": p.stat().st_size}
                for p in sorted(OUT.iterdir()) if p.is_file() and p.name not in {"CHECKSUMS.json", "SHA256SUMS.txt"}}
    builder.write_json(OUT / "CHECKSUMS.json", controls)
    (OUT / "SHA256SUMS.txt").write_text("".join(f"{v['sha256']}  {k}\n" for k, v in controls.items()) +
                                      f"{builder.digest(OUT / 'CHECKSUMS.json')}  CHECKSUMS.json\n", encoding="utf-8")
    print(json.dumps({"phase": "ready-for-restore", "manifest_sha256": builder.digest(OUT / "MANIFESTO.json")}), flush=True)


if __name__ == "__main__":
    main()
