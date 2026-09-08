"""Account for historical authored source copies, without vendoring dependencies."""
import hashlib
import json
from pathlib import Path
import subprocess

REPO = Path(r"C:\Users\Superleo13\stocks-predictor-work")
SNAP = Path(r"E:\Stocks-Restore-Test-20260908")
DEST = REPO / "research/session-20260908/historical-code-preserved"
manifest = json.loads(Path(r"E:\EXPORTACAO_STOCKS_20260908\MANIFESTO.json").read_text(encoding="utf-8"))
objects = subprocess.check_output(["git", "-C", str(REPO), "rev-list", "--objects", "--all"], encoding="utf-8").splitlines()
blobs = {}
suffixes = {".py", ".ps1", ".sh", ".cmd", ".bat"}
for row in objects:
    obj, _, name = row.partition(" ")
    if Path(name).suffix.lower() in suffixes:
        blobs[obj] = name
batch = subprocess.run(["git", "-C", str(REPO), "cat-file", "--batch"], input=("\n".join(blobs) + "\n").encode(), capture_output=True, check=True).stdout
known = {}
offset = 0
for obj, name in blobs.items():
    end = batch.index(b"\n", offset)
    header = batch[offset:end].decode().split()
    size = int(header[2])
    payload = batch[end + 1:end + 1 + size]
    offset = end + size + 2
    assert header[0] == obj and header[1] == "blob"
    sha = hashlib.sha256(payload.replace(b"\r\n", b"\n")).hexdigest()
    known.setdefault(sha, {"git_blob": obj, "git_path": name})
for p in (REPO / "research/session-20260908/local-scripts-preserved").rglob("*"):
    if p.is_file() and p.suffix in suffixes:
        known.setdefault(hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest(), {"git_path": p.relative_to(REPO).as_posix()})
mapping, copied = [], 0
for row in manifest["files"]:
    name = row["path"]
    p = Path(name)
    if p.suffix.lower() not in suffixes:
        continue
    if set(p.parts) & {"python313-packages", "predictor_core", "vendor", "runtime", "checks", "lint", ".git"}:
        continue
    source = SNAP / name
    payload = source.read_bytes()
    assert hashlib.sha256(payload).hexdigest() == row["sha256"]
    sha = hashlib.sha256(payload.replace(b"\r\n", b"\n")).hexdigest()
    match = known.get(sha)
    if match is None:
        dst = DEST / row["sha256"][:16] / p.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(payload)
        match = {"git_path": dst.relative_to(REPO).as_posix()}
        known[sha] = match
        copied += 1
    mapping.append({"original_path": name, "sha256_original": row["sha256"], "sha256_lf": sha, **match})
DEST.mkdir(parents=True, exist_ok=True)
(DEST / "ORIGENS.json").write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(DEST / "README.md").write_text(
    "# Cópias históricas de código\n\n"
    "ORIGENS.json localiza no Git todos os arquivos autorais Python/PowerShell/shell "
    "do snapshot de exportação. Versões já presentes no histórico apontam para seu blob Git; "
    "somente conteúdos ausentes foram acrescentados aqui. A comparação LF evita duplicar CRLF. "
    "Os arquivos mantêm comportamento e caminhos antigos e não devem ser executados automaticamente. "
    "Bibliotecas de terceiros, Core instalado e vendor são dependências, fora deste inventário.\n",
    encoding="utf-8")
print(json.dumps({"historical_blobs_examined": len(blobs), "authored_paths_mapped": len(mapping), "additional_contents_preserved": copied}))
