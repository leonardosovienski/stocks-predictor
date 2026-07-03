"""sync_core — integridade e sincronização do vendor/predictor_core.

Três modos (stdlib puro):

  --check          verifica os SHA256 do vendor contra CORE_MANIFEST.json (read-only).
                   Exit 1 em qualquer divergência. É o mesmo invariante coberto por
                   tests/test_core_manifest.py — aqui como ferramenta de linha de
                   comando (cron de rede limpa, pré-sync).
  --stamp          re-carimba o manifesto após uma EVOLUÇÃO POR DEMANDA deliberada do
                   vendor (regra do CLAUDE.md: mudança local exige carimbo no VERSION
                   e marcação para upstream). Recusa se o VERSION não mudou desde o
                   último carimbo — evolução silenciosa continua impossível. Registra
                   os arquivos alterados em `local_evolution.pending_upstream`.
  --sync SOURCE    importa o core de um checkout upstream (copia *.py + VERSION),
                   recusando se o vendor local tiver diff não commitado (proteção
                   contra perder evolução por demanda não levada a upstream). Escreve
                   manifesto novo com synced_at + source_version.

O aggregate do manifesto = sha256("nome:hash\n" ordenado)[:16] — recibo curto da
árvore inteira para comparação visual entre domínios.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENDOR = ROOT / "vendor" / "predictor_core"
MANIFEST = VENDOR / "CORE_MANIFEST.json"

# O que compõe o vendor rastreado: fontes + carimbo de versão (não o próprio manifesto).
TRACKED_GLOBS = ("*.py", "VERSION")


def _tracked_files() -> list[Path]:
    files: set[Path] = set()
    for pattern in TRACKED_GLOBS:
        files.update(VENDOR.glob(pattern))
    return sorted(files)


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _current_hashes() -> dict[str, str]:
    return {p.name: _hash_file(p) for p in _tracked_files()}


def _aggregate(hashes: dict[str, str]) -> str:
    canon = "".join(f"{name}:{hashes[name]}\n" for name in sorted(hashes))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()[:16]


def _load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _write_manifest(data: dict) -> None:
    MANIFEST.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")


def _vendor_has_uncommitted_diff() -> bool:
    out = subprocess.run(
        ["git", "status", "--porcelain", "--", str(VENDOR.relative_to(ROOT))],
        cwd=ROOT, capture_output=True, text=True, timeout=30)
    return bool(out.stdout.strip())


def check() -> int:
    manifest = _load_manifest()
    expected = manifest["files"]
    actual = _current_hashes()
    problems = []
    for name, want in sorted(expected.items()):
        have = actual.get(name)
        if have is None:
            problems.append(f"AUSENTE   {name}")
        elif have != want:
            problems.append(f"DIVERGE   {name}  manifesto={want[:12]} atual={have[:12]}")
    for name in sorted(set(actual) - set(expected)):
        problems.append(f"NÃO-RASTREADO  {name} (existe no vendor, fora do manifesto)")
    if problems:
        print("vendor DESSINCRONIZADO do CORE_MANIFEST.json:")
        for p in problems:
            print(f"  {p}")
        return 1
    print(f"vendor OK — {len(expected)} arquivos batem com o manifesto "
          f"(aggregate {manifest.get('aggregate', '?')})")
    return 0


def stamp() -> int:
    old = _load_manifest()
    actual = _current_hashes()
    changed = sorted(
        name for name in actual
        if old["files"].get(name) != actual[name]
    ) + sorted(set(old["files"]) - set(actual))
    if not changed:
        print("nada a carimbar — vendor já bate com o manifesto")
        return 0
    new_version = (VENDOR / "VERSION").read_text(encoding="utf-8").strip()
    if "VERSION" not in changed:
        print(f"RECUSADO: o vendor mudou ({', '.join(changed)}) mas o VERSION não foi "
              f"carimbado ({new_version}). Evolução por demanda exige bump de VERSION "
              f"antes do --stamp (CLAUDE.md).")
        return 1
    pending = sorted(set(
        (old.get("local_evolution") or {}).get("pending_upstream", [])
    ) | {c for c in changed if c != "VERSION"})
    new = {
        "files": actual,
        "aggregate": _aggregate(actual),
        "synced_at": old.get("synced_at"),
        "source_version": old.get("source_version"),
        "stamped_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "local_evolution": {"version": new_version, "pending_upstream": pending},
    }
    _write_manifest(new)
    print(f"carimbado: {new_version} — pendente para upstream: {', '.join(pending)}")
    return 0


def sync(source: str) -> int:
    src = Path(source).expanduser().resolve()
    if not (src / "VERSION").exists():
        print(f"fonte inválida: {src} (sem VERSION)")
        return 1
    if _vendor_has_uncommitted_diff():
        print("RECUSADO: vendor/ tem diff não commitado — commite (ou reverta) antes "
              "do sync, senão a evolução por demanda local se perde.")
        return 1
    manifest_old = _load_manifest() if MANIFEST.exists() else {}
    pending = (manifest_old.get("local_evolution") or {}).get("pending_upstream", [])
    if pending:
        print(f"AVISO: evolução local pendente de upstream ({', '.join(pending)}) — "
              f"confirme que o upstream já a incorporou antes de sobrescrever.")
    copied = []
    for pattern in TRACKED_GLOBS:
        for f in sorted(src.glob(pattern)):
            (VENDOR / f.name).write_bytes(f.read_bytes())
            copied.append(f.name)
    hashes = _current_hashes()
    source_version = (VENDOR / "VERSION").read_text(encoding="utf-8").strip()
    _write_manifest({
        "files": hashes,
        "aggregate": _aggregate(hashes),
        "synced_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_version": source_version,
    })
    print(f"sync de {src} — {len(copied)} arquivos, source_version={source_version}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true", help="verifica hashes (read-only)")
    g.add_argument("--stamp", action="store_true",
                   help="re-carimba manifesto após evolução local (exige VERSION novo)")
    g.add_argument("--sync", metavar="SOURCE",
                   help="importa do checkout upstream do predictor-core")
    args = ap.parse_args(argv)
    if args.check:
        return check()
    if args.stamp:
        return stamp()
    return sync(args.sync)


if __name__ == "__main__":
    sys.exit(main())
