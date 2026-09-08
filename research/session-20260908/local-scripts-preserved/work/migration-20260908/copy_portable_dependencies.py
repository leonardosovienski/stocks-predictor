"""Copy existing dependency files alongside (never inside) the data ZIP."""
import hashlib
import json
from pathlib import Path
import shutil

SNAP = Path(r"E:\Stocks-Restore-Test-20260908")
OUT = Path(r"E:\STOCKS_MIGRACAO_MAIN_20260908")
manifest = json.loads(Path(r"E:\EXPORTACAO_STOCKS_20260908\MANIFESTO.json").read_text(encoding="utf-8"))
prefixes = {
    "python313-packages/": "DEPENDENCIAS/python313-packages/",
    "project/.local-research/stocks-session-20260907/work/runtime/": "DEPENDENCIAS/research-runtime/",
    "project/.local-research/stocks-session-20260907/work/checks/": "DEPENDENCIAS/checks/",
    "project/.local-research/stocks-session-20260907/work/lint/": "DEPENDENCIAS/lint/",
}
rows = []
for item in manifest["files"]:
    name = item["path"]
    target = next((dest + name[len(prefix):] for prefix, dest in prefixes.items() if name.startswith(prefix)), None)
    if name.startswith("project/.local-research/stocks-session-20260907/work/source-acquisition/") and Path(name).suffix in {".js", ".map"}:
        target = "FONTES_WEB_ORIGINAIS/" + Path(name).name
    if target is None:
        continue
    source = SNAP / name
    dst = OUT / target
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        raise FileExistsError(dst)
    shutil.copy2(source, dst)
    with dst.open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if actual != item["sha256"]:
        raise ValueError(f"Changed source: {name}")
    rows.append({"original_path": name, "path": target, "size": item["size"], "sha256": actual})
(OUT / "MANIFESTO_DEPENDENCIAS.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"files": len(rows), "bytes": sum(r["size"] for r in rows)}))
