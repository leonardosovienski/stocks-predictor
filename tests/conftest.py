"""Configuração comum dos testes — código local em stocks_predictor/, Core/Ops via wheels."""
import pathlib
import sys

# Carrega as dependências compartilhadas antes de qualquer módulo legado que
# ainda tenha um sys.path histórico apontando para vendor/. Assim a suíte
# exercita as wheels oficiais durante a migração, sem depender da ordem dos
# testes nem reescrever ciência para satisfazer packaging.
import predictor_core

ROOT = pathlib.Path(__file__).parent.parent
SRC = ROOT / "stocks_predictor"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import os
if os.environ.get("STOCKS_ALLOW_VENDOR_SHIM") != "1":
    assert "vendor" not in pathlib.Path(predictor_core.__file__).parts
