"""Configuração comum dos testes — paths de vendor/ e src/."""
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).parent.parent
for p in (ROOT / "vendor", ROOT / "src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


@pytest.fixture(autouse=True)
def _events_to_tmp(tmp_path, monkeypatch):
    """Telemetria dos testes vai para tmp — nenhum teste polui data/events.jsonl."""
    monkeypatch.setenv("PREDICTOR_EVENTS_PATH", str(tmp_path / "events.jsonl"))
