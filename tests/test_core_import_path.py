"""Prova, de forma explícita e nomeada, qual Core é resolvido em runtime.

`tests/conftest.py` já faz esse assert como efeito colateral de import (nível de módulo,
antes de qualquer teste rodar). Este arquivo o torna um TESTE nomeado e independente
(RESEARCH_FREEZE.md §6/§12) — mais fácil de rodar isolado
(`pytest tests/test_core_import_path.py -v`), de citar num relatório de auditoria, e de
não perder de vista se o conftest for reestruturado no futuro.

Regra do vendor (RESEARCH_FREEZE.md §5): `vendor/predictor_core/` é um arquivo histórico
read-only para reprodução de `poc_leak.py` — nenhum caminho de runtime deve resolver o
import `predictor_core` para lá. Se este teste falhar, o runtime está acidentalmente
usando o Core congelado (1.3.0-ga) em vez do Core real instalado (>=3.0,<4).
"""
import os
import pathlib
import subprocess
import sys

import predictor_core


def test_predictor_core_does_not_resolve_to_vendor():
    if os.environ.get("STOCKS_ALLOW_VENDOR_SHIM") == "1":
        import pytest
        pytest.skip(
            "STOCKS_ALLOW_VENDOR_SHIM=1 setado explicitamente — shim histórico "
            "permitido de propósito (ex.: reproduzir poc_leak.py), não drift acidental."
        )
    resolved = pathlib.Path(predictor_core.__file__)
    assert "vendor" not in resolved.parts, (
        f"predictor_core resolveu para {resolved} — isso é o vendor/ congelado "
        "(1.3.0-ga), não o Core real instalado (predictor-core>=3.0,<4). Um import "
        "acidental de vendor em runtime é exatamente o risco que RESEARCH_FREEZE.md "
        "§5 (ST_VENDOR_STATE) existe para prevenir."
    )


def test_predictor_core_version_is_at_least_3():
    version = getattr(predictor_core, "__version__", None)
    assert version is not None, (
        "predictor_core não expõe __version__ — não dá para confirmar que é o Core "
        "3.0.0+ declarado em pyproject.toml sem essa informação."
    )
    major = int(str(version).split(".")[0])
    assert major >= 3, (
        f"predictor_core.__version__ == {version!r}, esperado major >= 3 "
        "(pyproject.toml declara predictor-core>=3.0,<4)."
    )


def test_importing_historical_poc_does_not_mutate_import_path():
    root = pathlib.Path(__file__).resolve().parents[1]
    probe = (
        "import sys; before=list(sys.path); import poc_leak; "
        "assert sys.path == before; "
        "assert not any(__import__('pathlib').Path(p).name == 'vendor' for p in sys.path if p)"
    )
    subprocess.run([sys.executable, "-c", probe], cwd=root, check=True)
