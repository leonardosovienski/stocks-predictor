"""Recover exact archived COTAHIST objects; never open or change a database.

Auxiliary stdlib tool compatible with Python 3.12+, not a production-runtime test.
Raw/licensed source files remain outside Git. Download and measurement are separate.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[3]


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def extract(archive_path, destination):
    if destination.exists():
        raise FileExistsError(destination)
    metadata = json.loads(archive_path.with_suffix(".json").read_text(encoding="utf-8-sig"))
    if archive_path.stat().st_size != metadata["bytes"] or sha256(archive_path) != metadata["sha256"]:
        raise ValueError("Archive hash/size mismatch")
    spec = importlib.util.spec_from_file_location("stocks_data_transfer", ROOT / "tools/data_transfer.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    names = {f"project/data/COTAHIST_A{year}.ZIP" for year in range(2018, 2027)}
    with zipfile.ZipFile(archive_path) as archive:
        manifest, _ = module.read_manifest(archive)
        selected = [row for row in manifest["files"] if row["path"] in names]
        if {row["path"] for row in selected} != names:
            raise ValueError("Missing required COTAHIST object; no endpoint substitution")
        destination.mkdir(parents=True)
        for row in selected:
            data = archive.read("objects/" + row["sha256"])
            if len(data) != row["size"] or hashlib.sha256(data).hexdigest() != row["sha256"]:
                raise ValueError("Corrupt selected object")
            target = destination / Path(row["path"]).name
            with target.open("xb") as stream:
                stream.write(data)
            if sha256(target) != row["sha256"]:
                raise ValueError("Restored object mismatch")
            print(target.name, row["size"], "SHA256 PASS", flush=True)
    receipt = {"archive_sha256": metadata["sha256"], "source_manifest_sha256": hashlib.sha256(
        json.dumps(manifest, sort_keys=True).encode()).hexdigest(), "manifest_hash_kind": "canonical JSON serialization",
        "selected_files": selected, "restored_bytes": sum(row["size"] for row in selected),
        "scope": "Whole archive hash and manifest validated; selected objects CRC, SHA256 and written bytes validated. Other objects not decompressed. No complete restoration claim."}
    (destination / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def download(url, destination):
    if destination.exists():
        raise FileExistsError(destination)
    request = urllib.request.Request(url, headers={"User-Agent": "StocksResearch/1.0 public-source-validation"})
    with urllib.request.urlopen(request, timeout=45) as response:
        data = response.read()
        content_type = response.headers.get("Content-Type")
        final_url = response.url
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as stream:
        stream.write(data)
    receipt = {"url": url, "final_url": final_url, "content_type": content_type,
               "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    destination.with_suffix(destination.suffix + ".source.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    restore = sub.add_parser("extract")
    restore.add_argument("archive", type=Path)
    restore.add_argument("destination", type=Path)
    fetch = sub.add_parser("download")
    fetch.add_argument("url")
    fetch.add_argument("destination", type=Path)
    args = parser.parse_args()
    if args.command == "extract":
        extract(args.archive, args.destination)
    else:
        download(args.url, args.destination)
