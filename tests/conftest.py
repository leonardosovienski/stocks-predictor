"""Configuração comum dos testes — código local em src/, Core/Ops via wheels."""
import pathlib
import sys

# Carrega as dependências compartilhadas antes de qualquer módulo legado que
# ainda tenha um sys.path histórico apontando para vendor/. Assim a suíte
# exercita as wheels oficiais durante a migração, sem depender da ordem dos
# testes nem reescrever ciência para satisfazer packaging.
import predictor_core
import predictor_ops

ROOT = pathlib.Path(__file__).parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

assert "vendor" not in pathlib.Path(predictor_core.__file__).parts
assert "vendor" not in pathlib.Path(predictor_ops.__file__).parts
