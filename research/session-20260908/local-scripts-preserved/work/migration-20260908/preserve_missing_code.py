"""Preserve authored helpers omitted from earlier commits; never execute them."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

MAIN = Path(r"C:\Users\Superleo13\stocks-predictor-work")
CHAT = Path(r"C:\Users\Superleo13\Documents\Codex\2026-09-07\lei-2")
DEST = MAIN / "research/session-20260908/local-scripts-preserved"
tracked = subprocess.check_output(["git", "-C", str(MAIN), "ls-files", "-z"]).decode().split("\0")
hashes = {}
for name in tracked:
    path = MAIN / name
    if path.is_file() and path.suffix.lower() in {".py", ".ps1", ".sh", ".cmd", ".bat"}:
        hashes.setdefault(hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest(), name)
files = list((CHAT / "work").glob("*.py")) + list((CHAT / "work").glob("*.ps1"))
files += [p for p in (CHAT / "work/continuation-14").iterdir() if p.suffix in {".py", ".ps1"}]
files += list((CHAT / "work/migration-20260908").glob("*.py"))
files += list(Path(r"E:\EXPORTACAO_STOCKS_20260908").glob("*.py"))
rows = []
for src in sorted(files):
    payload = src.read_bytes()
    normalized = hashlib.sha256(payload.replace(b"\r\n", b"\n")).hexdigest()
    existing = hashes.get(normalized)
    if not existing:
        if src.is_relative_to(CHAT):
            relative = src.relative_to(CHAT)
        else:
            relative = Path("full-export") / src.name
        dst = DEST / relative
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        existing = dst.relative_to(MAIN).as_posix()
        hashes[normalized] = existing
    rows.append({"original_path": str(src), "git_path": existing,
                 "sha256_original": hashlib.sha256(payload).hexdigest(),
                 "sha256_lf": normalized})
DEST.mkdir(parents=True, exist_ok=True)
(DEST / "ORIGENS.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(DEST / "README.md").write_text(
    "# Scripts históricos preservados na main\n\n"
    "Este acervo completa os helpers autorais que ainda estavam somente no chat. "
    "ORIGENS.json também aponta as cópias já versionadas, comparando conteúdo com LF. "
    "Scripts antigos mantêm seus bytes, caminhos absolutos e comportamento histórico. "
    "Alguns escrevem bancos ou consomem evidência: não executar automaticamente.\n\n"
    "Os helpers de exportação integral são registros da primeira migração, que incluía código. "
    "Para a entrega separada atual, usar tools/data_transfer.py e docs/continuation/MIGRACAO_MAIN.md. "
    "Bibliotecas instaladas e cópias de wheels não são código autoral deste repositório.\n",
    encoding="utf-8")
print(json.dumps({"mapped": len(rows), "new_scripts": len(list(DEST.rglob("*.py"))) + len(list(DEST.rglob("*.ps1")))}, indent=2))
