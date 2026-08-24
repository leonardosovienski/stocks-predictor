"""Configuração comum dos testes — código local em src/, Core/Ops via wheels."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
