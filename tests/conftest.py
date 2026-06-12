"""Configuração comum dos testes — paths de vendor/ e src/."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent.parent
for p in (ROOT / "vendor", ROOT / "src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
