"""One-off, read-only inventory plus preservation of both HANDOFF merge sides."""
import hashlib
import json
from pathlib import Path
import subprocess

MAIN = Path(r"C:\Users\Superleo13\stocks-predictor-work")
CHAT = Path(r"C:\Users\Superleo13\Documents\Codex\2026-09-07\lei-2")

path = MAIN / "HANDOFF.md"
lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
markers = [line.rstrip() for line in lines if line.startswith(("<<<<<<<", "|||||||", "=======", ">>>>>>>"))]
assert markers == ["<<<<<<< HEAD", "||||||| d48d05d", "=======", ">>>>>>> origin/main"], markers
assert lines[lines.index("||||||| d48d05d\n") + 1] == "=======\n"
path.write_text("".join(line for line in lines if line.rstrip() not in markers), encoding="utf-8", newline="\n")

tracked = subprocess.check_output(["git", "-C", str(MAIN), "ls-files", "-z"]).decode().split("\0")
hashes = {}
for name in tracked:
    p = MAIN / name
    if p.is_file() and p.suffix.lower() in {".py", ".ps1", ".sh", ".cmd", ".bat", ".js", ".ts"}:
        hashes.setdefault(hashlib.sha256(p.read_bytes()).hexdigest(), []).append(name)
manifest = json.loads(Path(r"E:\EXPORTACAO_STOCKS_20260908\MANIFESTO.json").read_text(encoding="utf-8"))
unknown = {}
for f in manifest["files"]:
    p = f["path"]
    if Path(p).suffix.lower() not in {".py", ".ps1", ".sh", ".cmd", ".bat", ".js", ".ts"}:
        continue
    if p.startswith("python313-packages/") or "/.git/" in p:
        continue
    if f["sha256"] in hashes:
        continue
    unknown.setdefault(f["sha256"], []).append(p)
rows = [{"sha256": h, "paths": sorted(v, key=lambda p: (len(p), p))} for h, v in unknown.items()]
(CHAT / "work/migration-20260908/untracked-code-inventory.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
for r in rows:
    p = r["paths"][0]
    if any(part in p for part in ("/predictor_core/", "/stocks_predictor/", "/_pytest/", "/pip/", "/yaml/", "/pyright/", "/coverage/", "/nodeenv.py", "/ruff/", "/vendor/", "/runtime/", "/checks/", "/lint/")):
        continue
    print(p)
print(f"Unknown code contents: {len(rows)}; tracked code contents: {len(hashes)}")
