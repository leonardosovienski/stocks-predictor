"""Integridade do vendor como INVARIANTE de CI, não disciplina manual.

Um byte alterado em vendor/predictor_core sem re-carimbo deliberado
(scripts/sync_core.py --stamp, que exige bump de VERSION) deixa a suíte vermelha.
Fecha o risco de dessincronização silenciosa apontado na auditoria de 2026-07-02
(o sync_core.py original tinha sumido do repositório e ninguém percebeu).
"""
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
VENDOR = ROOT / "vendor" / "predictor_core"
MANIFEST = VENDOR / "CORE_MANIFEST.json"


def _manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_every_manifest_hash_matches_vendor_file():
    """Cada arquivo listado existe e o SHA256 bate — 1 byte de diferença = vermelho."""
    for name, expected in _manifest()["files"].items():
        path = VENDOR / name
        assert path.exists(), f"arquivo do manifesto ausente no vendor: {name}"
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == expected, (
            f"vendor dessincronizado: {name} (manifesto={expected[:12]}, "
            f"atual={actual[:12]}) — mudança deliberada? bump de VERSION + "
            f"`python scripts/sync_core.py --stamp`")


def test_no_untracked_files_in_vendor():
    """Todo fonte do vendor está no manifesto — arquivo novo fora do manifesto é
    dessincronização tanto quanto um hash divergente."""
    tracked = set(_manifest()["files"])
    present = {p.name for p in VENDOR.glob("*.py")} | {"VERSION"}
    untracked = present - tracked
    assert not untracked, f"arquivos no vendor fora do manifesto: {sorted(untracked)}"


def test_manifest_version_consistent_with_vendor_version():
    """O VERSION do vendor corresponde ao último carimbo do manifesto (sync ou
    evolução local) — VERSION órfão indica carimbo esquecido."""
    m = _manifest()
    version = (VENDOR / "VERSION").read_text(encoding="utf-8").strip()
    stamped = {m.get("source_version")}
    if m.get("local_evolution"):
        stamped.add(m["local_evolution"].get("version"))
    assert version in stamped, (
        f"VERSION do vendor ({version}) não corresponde a nenhum carimbo do "
        f"manifesto ({stamped}) — rodar sync_core.py --stamp")


def test_sync_core_check_detects_corruption(tmp_path, monkeypatch):
    """Simulação de falha: corromper 1 byte de uma cópia do vendor faz --check
    acusar. Testa a DEFESA, não só o estado atual."""
    import shutil
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    import sync_core

    fake_vendor = tmp_path / "vendor" / "predictor_core"
    shutil.copytree(VENDOR, fake_vendor)
    monkeypatch.setattr(sync_core, "VENDOR", fake_vendor)
    monkeypatch.setattr(sync_core, "MANIFEST", fake_vendor / "CORE_MANIFEST.json")
    assert sync_core.check() == 0, "cópia intacta deveria passar no --check"

    stats = fake_vendor / "stats.py"
    stats.write_bytes(stats.read_bytes() + b"#")   # 1 byte
    assert sync_core.check() == 1, "--check deixou passar vendor corrompido"
