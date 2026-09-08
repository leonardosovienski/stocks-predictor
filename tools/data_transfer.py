"""Offline data transfer: deduplicated ZIP data, with program code kept in Git.

The builder reads a previously verified full-export snapshot and its manifest.
Old mixed delivery ZIPs are decomposed; their data members remain recoverable.
Original scientific ZIPs containing only data remain byte-identical.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile
import zipfile

CODE_SUFFIXES = frozenset({
    ".py", ".pyc", ".pyo", ".pyi", ".ps1", ".psm1", ".psd1", ".sh", ".bash",
    ".bat", ".cmd", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".ipynb",
    ".exe", ".dll", ".pyd", ".so", ".whl", ".bundle", ".patch", ".diff",
})
CODE_PARTS = frozenset({
    ".git", "__pycache__", ".pytest_cache", ".ruff_cache", "node_modules",
    "python313-packages", "predictor_core", "stocks_predictor", "vendor",
    "runtime", "checks", "lint",
})
RESERVED = re.compile(r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)", re.I)
CHUNK = 1024 * 1024


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def validate_name(name: str) -> str:
    if not isinstance(name, str) or not name or "\\" in name:
        raise ValueError(f"Unsafe path: {name!r}")
    parts = name.split("/")
    if any(not p or p in {".", ".."} or p.endswith((" ", "."))
           or RESERVED.match(p) or any(ord(c) < 32 or c in ':<>\"|?*' for c in p)
           for p in parts):
        raise ValueError(f"Unsafe path: {name!r}")
    return name


def excluded(name: str) -> bool:
    p = PurePosixPath(name.lower())
    return (p.suffix in CODE_SUFFIXES or bool(set(p.parts) & CODE_PARTS)
            or any(x.endswith((".dist-info", ".egg-info")) for x in p.parts)
            or p.name.startswith(".coverage") or p.name in {".ds_store"})


def data_zip_only(archive: zipfile.ZipFile) -> bool:
    """Nested containers are expanded, so opaque code cannot hide in the ZIP."""
    for info in archive.infolist():
        if info.is_dir():
            continue
        validate_name(info.filename)
        if excluded(info.filename) or info.filename.lower().endswith(".zip"):
            return False
    return True


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build(snapshot: Path, original_manifest: Path, destination: Path) -> dict:
    """Create a new archive; neither source files nor existing exports are changed."""
    if destination.exists():
        raise FileExistsError(destination)
    source_manifest = json.loads(original_manifest.read_text(encoding="utf-8"))
    destination.parent.mkdir(parents=True, exist_ok=True)
    records, omissions, objects = [], [], {}
    seen_names = set()
    manifest = {"format": "stocks-data-only-v1", "source_manifest_sha256": digest(original_manifest),
                "files": records, "omissions": omissions,
                "mixed_archives": "Data members stored under unpacked-archives; original containers remain in full backup."}
    mixed_cache = {}

    def add(name, stream, size, expected=None, mtime_ns=0, origin=None):
        validate_name(name)
        if name.casefold() in seen_names:
            raise ValueError(f"Duplicate destination: {name}")
        seen_names.add(name.casefold())
        h = hashlib.sha256()
        count = 0
        # Unknown member hashes need a bounded spool before naming their object.
        with tempfile.SpooledTemporaryFile(max_size=16 * CHUNK, dir=destination.parent) as spool:
            direct = expected and expected not in objects
            writer = output.open("objects/" + expected, "w", force_zip64=True) if direct else None
            try:
                while block := stream.read(CHUNK):
                    h.update(block)
                    count += len(block)
                    if writer is not None:
                        writer.write(block)
                    elif expected is None:
                        spool.write(block)
            finally:
                if writer is not None:
                    writer.close()
            sha = h.hexdigest()
            if count != size or (expected and sha != expected):
                raise ValueError(f"Source changed: {name}")
            if sha not in objects:
                if not direct:
                    spool.seek(0)
                    with output.open("objects/" + sha, "w", force_zip64=True) as target:
                        shutil.copyfileobj(spool, target, CHUNK)
                objects[sha] = size
            elif objects[sha] != size:
                raise ValueError(f"Conflicting size: {name}")
        records.append({"path": name, "size": size, "sha256": sha,
                        "mtime_ns": mtime_ns, "origin": origin or name})

    def unpack(archive, origin, prefix, depth=0):
        if depth > 8:
            raise ValueError("Nested archive depth exceeds 8")
        for info in archive.infolist():
            if info.is_dir():
                continue
            validate_name(info.filename)
            name = prefix + "/" + info.filename
            source = origin + "!" + info.filename
            if excluded(info.filename):
                omissions.append({"path": source, "reason": "code/dependency/cache"})
            elif info.filename.lower().endswith(".zip"):
                with archive.open(info) as stream, tempfile.SpooledTemporaryFile(
                    max_size=16 * CHUNK, dir=destination.parent
                ) as nested:
                    shutil.copyfileobj(stream, nested, CHUNK)
                    nested.seek(0)
                    with zipfile.ZipFile(nested) as inner:
                        if data_zip_only(inner):
                            nested.seek(0)
                            add(name, nested, info.file_size, origin=source)
                        else:
                            omissions.append({"path": source, "reason": "mixed container expanded"})
                            unpack(inner, source, name + ".contents", depth + 1)
            else:
                with archive.open(info) as stream:
                    add(name, stream, info.file_size, origin=source)

    with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=1, allowZip64=True) as output:
        for i, row in enumerate(source_manifest["files"], 1):
            name = validate_name(row["path"])
            if excluded(name):
                omissions.append({"path": name, "reason": "code/dependency/cache"})
                continue
            src = snapshot.joinpath(*name.split("/"))
            if src.is_symlink() or src.is_junction() or not src.is_relative_to(snapshot):
                raise ValueError(f"Unsafe source: {src}")
            if name.lower().endswith(".zip"):
                if digest(src) != row["sha256"]:
                    raise ValueError(f"Source changed: {name}")
                with zipfile.ZipFile(src) as nested:
                    if not data_zip_only(nested):
                        omissions.append({"path": name, "reason": "mixed container expanded"})
                        # Duplicate containers reuse data aliases without decompression.
                        previous = mixed_cache.get(row["sha256"])
                        prefix = "unpacked-archives/" + name + ".contents"
                        if previous:
                            old_prefix, old_rows = previous
                            for item in old_rows:
                                alias = item.copy()
                                alias["path"] = prefix + item["path"][len(old_prefix):]
                                alias["origin"] = name + item["origin"][item["origin"].find("!"):]
                                validate_name(alias["path"])
                                if alias["path"].casefold() in seen_names:
                                    raise ValueError("Duplicate expanded destination")
                                seen_names.add(alias["path"].casefold())
                                records.append(alias)
                        else:
                            start = len(records)
                            unpack(nested, name, prefix)
                            mixed_cache[row["sha256"]] = (prefix, records[start:])
                        continue
            with src.open("rb") as stream:
                add(name, stream, row["size"], row["sha256"], row.get("mtime_ns", 0))
            if i % 2000 == 0:
                print(f"Source entries {i}/{len(source_manifest['files'])}; unique data objects {len(objects)}", flush=True)
        manifest.update(file_count=len(records), unique_objects=len(objects),
                        restored_bytes=sum(r["size"] for r in records), unique_bytes=sum(objects.values()))
        output.writestr("MANIFESTO_DADOS.json", json.dumps(manifest, ensure_ascii=False))
    result = {"archive": destination.name, "sha256": digest(destination), "bytes": destination.stat().st_size,
              "file_count": len(records), "unique_objects": len(objects),
              "restored_bytes": manifest["restored_bytes"], "unique_bytes": manifest["unique_bytes"]}
    write_json(destination.with_suffix(".json"), result)
    return result


def read_manifest(archive):
    manifest = json.loads(archive.read("MANIFESTO_DADOS.json"))
    if manifest.get("format") != "stocks-data-only-v1":
        raise ValueError("Unsupported manifest")
    objects, paths = {}, set()
    for row in manifest["files"]:
        name = validate_name(row["path"])
        if excluded(name) or name.casefold() in paths:
            raise ValueError(f"Code or duplicate path: {name}")
        paths.add(name.casefold())
        sha, size = row["sha256"], row["size"]
        if not re.fullmatch(r"[0-9a-f]{64}", sha) or not isinstance(size, int) or size < 0:
            raise ValueError("Invalid object declaration")
        if sha in objects and objects[sha] != size:
            raise ValueError("Conflicting object sizes")
        objects[sha] = size
    names = archive.namelist()
    if len(set(names)) != len(names) or set(names) != {"MANIFESTO_DADOS.json"} | {"objects/" + h for h in objects}:
        raise ValueError("Undeclared, duplicate or missing ZIP member")
    if manifest["file_count"] != len(paths) or manifest["restored_bytes"] != sum(r["size"] for r in manifest["files"]):
        raise ValueError("Inconsistent manifest counts")
    return manifest, objects


def verify(path: Path, destination: Path | None = None, prefix: str | None = None) -> dict:
    if destination is not None and destination.exists():
        raise FileExistsError(destination)
    checksum = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
    if path.stat().st_size != checksum["bytes"] or digest(path) != checksum["sha256"]:
        raise ValueError("Archive checksum mismatch")
    with zipfile.ZipFile(path) as archive:
        manifest, objects = read_manifest(archive)
        zip_hashes = {r["sha256"] for r in manifest["files"] if r["path"].lower().endswith(".zip")}
        for sha, size in objects.items():
            with archive.open("objects/" + sha) as stream:
                h, count = hashlib.sha256(), 0
                with tempfile.SpooledTemporaryFile(max_size=16 * CHUNK) as spool:
                    while block := stream.read(CHUNK):
                        h.update(block)
                        count += len(block)
                        if sha in zip_hashes:
                            spool.write(block)
                    if h.hexdigest() != sha or count != size:
                        raise ValueError(f"Corrupt data object: {sha}")
                    if sha in zip_hashes:
                        spool.seek(0)
                        with zipfile.ZipFile(spool) as inner:
                            if not data_zip_only(inner):
                                raise ValueError("Code or nested archive in data ZIP")
        selected = [r for r in manifest["files"] if not prefix or
                    r["path"] == prefix or r["path"].startswith(prefix.rstrip("/") + "/")]
        restored = 0
        if destination is not None:
            if not selected:
                raise ValueError("No files match the requested prefix")
            parent = destination.parent
            while not parent.exists():
                parent = parent.parent
            if shutil.disk_usage(parent).free < sum(r["size"] for r in selected) + 1024**3:
                raise OSError("Insufficient disk space to restore data")
            destination.mkdir(parents=True, exist_ok=False)
            for row in selected:
                target = destination.joinpath(*row["path"].split("/"))
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open("objects/" + row["sha256"]) as source, target.open("xb") as sink:
                    shutil.copyfileobj(source, sink, CHUNK)
                if digest(target) != row["sha256"]:
                    raise ValueError(f"Restored file checksum mismatch: {target}")
                if row.get("mtime_ns"):
                    os.utime(target, ns=(row["mtime_ns"], row["mtime_ns"]))
                restored += 1
            write_json(destination / "RECIBO_DADOS.json", {"archive_sha256": checksum["sha256"],
                       "restored_files": restored, "prefix": prefix})
        return {"verified_objects": len(objects), "data_paths": len(manifest["files"]),
                "restored_files": restored, "project_code_in_zip": False, "archive_sha256": checksum["sha256"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("build")
    create.add_argument("--snapshot", type=Path, required=True)
    create.add_argument("--manifest", type=Path, required=True)
    create.add_argument("--output", type=Path, required=True)
    check = sub.add_parser("verify")
    check.add_argument("archive", type=Path)
    check.add_argument("--destination", type=Path)
    check.add_argument("--prefix")
    args = parser.parse_args()
    result = (build(args.snapshot.resolve(), args.manifest, args.output) if args.command == "build"
              else verify(args.archive, args.destination, args.prefix))
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
