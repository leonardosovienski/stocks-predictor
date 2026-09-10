"""Read-only sources; reconstruct the split archive at its actual root."""
import hashlib
import json
from pathlib import Path
import zipfile

root = Path(r"C:\STOCKS")
meta = json.loads((root / "FONTES_WEB_ORIGINAIS/PARTES.json").read_text(encoding="utf-8-sig"))
target = root / "DADOS_STOCKS.zip"
temporary = root / "work/DADOS_STOCKS.zip.reunindo"
if not target.exists():
    total = hashlib.sha256()
    count = 0
    with temporary.open("xb") as out:
        for part in meta["parts"]:
            source = root / part["name"]
            assert source.stat().st_size == part["bytes"]
            digest = hashlib.sha256()
            with source.open("rb") as stream:
                while block := stream.read(8 * 1024**2):
                    digest.update(block)
                    total.update(block)
                    count += len(block)
                    out.write(block)
            assert digest.hexdigest() == part["sha256"]
            print(part["name"], digest.hexdigest(), "PASS", flush=True)
    assert count == meta["bytes"] and total.hexdigest() == meta["sha256"]
    with temporary.open("rb") as stream:
        assert hashlib.file_digest(stream, "sha256").hexdigest() == meta["sha256"]
    temporary.rename(target)
with target.open("rb") as stream:
    assert target.stat().st_size == meta["bytes"]
    assert hashlib.file_digest(stream, "sha256").hexdigest() == meta["sha256"]
with zipfile.ZipFile(target) as archive:
    raw = archive.read("MANIFESTO_DADOS.json")
    manifest = json.loads(raw)
    (root / "work/MANIFESTO_DADOS.json").write_bytes(raw)
    selected = [row for row in manifest["files"] if "cotahist" in row["path"].lower() or row["path"].lower().endswith(".db")]
    (root / "work/data_candidates.json").write_text(json.dumps(selected, indent=2), encoding="utf-8")
    print(json.dumps({"archive_sha256": meta["sha256"], "files": len(manifest["files"]), "candidates": len(selected), "candidate_examples": selected[:12]}, indent=2))
