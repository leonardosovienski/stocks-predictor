"""PoC histórico do lookahead na implementação vendorizada legada.

STATUS = HISTORICAL_POC
TARGET = LEGACY_VENDORED_IMPLEMENTATION
CURRENT_CORE_SCOPE = NOT_AFFECTED_BY_THIS_POC

O vendor só entra no ``sys.path`` quando este arquivo é executado explicitamente.
Importar ``poc_leak`` é inerte e não pode alterar a resolução normal do Core.
"""

from __future__ import annotations

import sys
from pathlib import Path


def testar_vazamento() -> None:
    vendor = Path(__file__).resolve().parent / "vendor"
    sys.path.insert(0, str(vendor))

    from predictor_core.replay import LookaheadError, PastView, replay

    def handler_malicioso(past: PastView) -> str:
        hoje = past.latest
        asof = past.asof_index

        try:
            _ = past[asof + 1]
        except LookaheadError:
            pass

        oraculo = past._data[-1]
        print(
            f"[Passo {asof}] Estamos no evento '{hoje}'. "
            f"Mas eu espiei a tupla e sei que no final vai acontecer um '{oraculo}'!"
        )
        return f"Apostei tudo em {hoje} porque sei sobre {oraculo}"

    eventos = [
        "Dia 1 (Mercado Calmo)",
        "Dia 2 (Pequena Alta)",
        "Dia 3 (Estabilidade)",
        "Dia 4 (CRASH GLOBAL)",
    ]

    print("--- INICIANDO POC HISTÓRICO CONTRA O VENDOR LEGADO ---")
    replay(eventos, handler_malicioso)
    print("--- POC HISTÓRICO CONCLUÍDO ---")


if __name__ == "__main__":
    testar_vazamento()
