"""Telemetria do domínio — envelope rígido do core.obs, destino data/events.jsonl.

Cada ponto de decisão do pipeline (ingestão, quarentena, walk-forward, veredito)
emite um evento JSONL correlacionável por run_id. Sem isto o cron do M6 é uma
caixa-preta: a saúde da rodada só seria reconstruível lendo stdout.

Destino: $PREDICTOR_EVENTS_PATH (os testes apontam para tmp via conftest) ou
data/events.jsonl (append-only, fora do git como todo data/).
"""
import os
import pathlib

import db
from predictor_core import obs

ROOT = pathlib.Path(__file__).parent.parent
DOMAIN = "predictor-stocks"

_code_version: str | None = None


def emit(event: str, *, run_id: str | None = None,
         metrics: dict | None = None, metadata: dict | None = None) -> dict:
    """Emite um evento do domínio. metrics: só números e sem None (filtrados aqui
    para conveniência dos chamadores); contexto não-numérico vai em metadata."""
    global _code_version
    if _code_version is None:
        _code_version = db.get_code_version()
    metrics = {k: v for k, v in (metrics or {}).items() if v is not None}
    path = os.getenv(obs.EVENTS_ENV) or ROOT / "data" / "events.jsonl"
    return obs.emit_event(DOMAIN, event, run_id=run_id, code_version=_code_version,
                          metrics=metrics, metadata=metadata, path=path)
