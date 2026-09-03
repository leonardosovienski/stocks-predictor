"""Migração NÃO-DESTRUTIVA e IDEMPOTENTE de trials.json para o schema prospectivo canônico.

Lê trials.json (schema legado) e escreve trials_v2.json (schema canônico), sem alterar
ou remover o arquivo original. Campos que não existiam no registro legado e não podem
ser inferidos com segurança recebem o literal "UNKNOWN" — nunca um valor inventado
(seed, selection_path, dataset_hash e hypothesis_family nunca são adivinhados).

Uso:
    python tools/migrate_trials_schema.py [--check]

--check: não escreve nada, só valida que a migração é idempotente (roda de novo sobre
         trials_v2.json existente e compara byte-a-byte).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEGACY_PATH = ROOT / "trials.json"
CANONICAL_PATH = ROOT / "trials_v2.json"

UNKNOWN = "UNKNOWN"

# hypothesis_family: só preenchido quando o nome do trial deixa a família inequívoca
# (mapeamento factual dos nomes já registrados em trials.json / HANDOFF.md, não uma
# nova classificação). Não estende para hipóteses futuras.
_FAMILY_BY_PREFIX = {
    "h1-momentum": "momentum_12_1",
    "h6-momentum": "momentum_6_1",
    "h2-lowvol": "low_vol_252",
    "h4-invvol": "vol_target_sizing",
    "h5-strev": "reversal_21d",
    "h8-mom-lowvol": "momentum_lowvol_intersection",
}


def _hypothesis_family(name: str) -> str:
    for prefix, family in _FAMILY_BY_PREFIX.items():
        if name.startswith(prefix):
            return family
    return UNKNOWN


def _hypothesis_id(name: str) -> str:
    # Os nomes legados já embutem o id da hipótese como prefixo antes do primeiro "-"
    # após "h<N>", ex.: "h1-momentum-12-1" -> "H1". Extração determinística, sem inferência.
    head = name.split("-", 1)[0]
    return head.upper() if head else UNKNOWN


def migrate_trial(legacy: dict) -> dict:
    name = legacy.get("name", UNKNOWN)
    test_period = legacy.get("test_period") or [UNKNOWN, UNKNOWN]
    label_start = test_period[0] if len(test_period) > 0 else UNKNOWN
    label_end = test_period[1] if len(test_period) > 1 else UNKNOWN
    params = legacy.get("params", {})

    # result/status são derivados apenas do que já está registrado em notes/sharpe,
    # nunca de uma nova avaliação do sinal (pesquisa está congelada).
    notes = legacy.get("notes", "")
    if "não comprovada" in notes or "nao comprovada" in notes:
        result = "NOT_SUPPORTED"
        status = "JUDGED"
    else:
        result = UNKNOWN
        status = UNKNOWN

    return {
        # --- campos preservados do schema legado, verbatim ---
        "legacy_name": name,
        "legacy_sharpe": legacy.get("sharpe", UNKNOWN),
        "legacy_notes": notes,
        "legacy_pipeline_fingerprint": legacy.get("pipeline_fingerprint", UNKNOWN),
        # --- schema prospectivo canônico ---
        "experiment_id": name,
        "hypothesis_id": _hypothesis_id(name),
        "hypothesis_family": _hypothesis_family(name),
        "trial_id": name,  # legado só tem 1 trial por hipótese; sem run_id distinto por trial
        "registered_at": legacy.get("registered_at", UNKNOWN),
        "executed_at": UNKNOWN,  # não registrado separadamente de registered_at no legado
        "seed": UNKNOWN,  # seed global (config.yaml) não foi carimbada por trial
        "forecast_horizon": UNKNOWN,
        "data_cutoff": label_end,
        "label_start": label_start,
        "label_end": label_end,
        "dataset_hash": UNKNOWN,
        "dataset_version": UNKNOWN,
        "feature_version": UNKNOWN,
        "model_version": UNKNOWN,
        "code_version": UNKNOWN,
        "params": params,
        "selection_path": UNKNOWN,
        "n_trials_family": 1,
        "n_trials_domain": len(_FAMILY_BY_PREFIX),
        "n_trials_ecosystem": UNKNOWN,
        "metric": legacy.get("metric", UNKNOWN),
        "result": result,
        "status": status,
        "notes": notes,
    }


def migrate() -> list[dict]:
    legacy_trials = json.loads(LEGACY_PATH.read_text(encoding="utf-8"))
    return [migrate_trial(t) for t in legacy_trials]


def main() -> int:
    check = "--check" in sys.argv
    migrated = migrate()
    serialized = json.dumps(migrated, indent=2, ensure_ascii=False) + "\n"

    if check:
        if not CANONICAL_PATH.exists():
            print("trials_v2.json não existe ainda — nada a checar.")
            return 0
        existing = CANONICAL_PATH.read_text(encoding="utf-8")
        if existing == serialized:
            print("OK: migração é idempotente (trials_v2.json já reflete trials.json).")
            return 0
        print("DRIFT: trials_v2.json está desatualizado em relação a trials.json.")
        return 1

    CANONICAL_PATH.write_text(serialized, encoding="utf-8")
    print(f"Escrito {CANONICAL_PATH} ({len(migrated)} trials). trials.json NÃO foi alterado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
