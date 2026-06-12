"""Sincroniza vendor/predictor_core a partir de um checkout do predictor-core.

Uso:
    python scripts/sync_core.py <caminho-do-checkout-do-core> [versao]

Copia os .py do core para vendor/predictor_core/ e carimba o VERSION com
versão + data. Mudanças locais no vendor (evolução por demanda, ex.: block
bootstrap) devem ser levadas para upstream ANTES do sync — este script
SOBRESCREVE o vendor. Ele aborta se houver diff local não commitado no vendor.
"""
import datetime
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).parent.parent
VENDOR = ROOT / "vendor" / "predictor_core"


def vendor_is_dirty() -> bool:
    out = subprocess.run(
        ["git", "status", "--porcelain", str(VENDOR)],
        cwd=ROOT, capture_output=True, text=True,
    )
    return bool(out.stdout.strip())


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    source = pathlib.Path(sys.argv[1])
    version = sys.argv[2] if len(sys.argv) > 2 else "0.0.0"
    if not source.is_dir():
        print(f"ERRO: diretório de origem não existe: {source}")
        return 1
    if vendor_is_dirty():
        print("ERRO: vendor/predictor_core tem mudanças não commitadas.")
        print("Commit (ou leve para upstream) antes do sync — o sync sobrescreve.")
        return 1

    copied = []
    for py in sorted(source.glob("*.py")):
        shutil.copy2(py, VENDOR / py.name)
        copied.append(py.name)
    stamp = datetime.date.today().strftime("%Y%m%d")
    (VENDOR / "VERSION").write_text(f"{version}-vendored-{stamp}\n", encoding="utf-8")
    print(f"sync ok: {len(copied)} arquivos ({', '.join(copied)})")
    print(f"VERSION: {version}-vendored-{stamp}")
    print("Revisar o diff e commitar. Rodar a suíte antes: python -m pytest tests/ -v")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
