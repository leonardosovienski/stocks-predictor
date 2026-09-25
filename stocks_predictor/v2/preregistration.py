"""Pré-registro, holdout selado e deduplicação — integridade experimental do Prompt 4.

- **Pré-registro** (``PREREGISTERED`` no TrialLedger, antes do primeiro backtest): ID imutável, descrição,
  mecanismo econômico, features, alvo, regra de universo, período, custos, convenção de execução, protocolo de
  validação, métrica primária e secundárias, política (versão e sha256), número máximo de variantes, sementes,
  holdout e critérios GO, NO_GO e NO_DECISION. ``require_preregistration`` recusa avaliar sem ele.
- **Holdout selado** (``HOLDOUT_SEALED``): intervalo, conteúdo (sha256 do dado, ou ``FUTURE`` para período
  ainda não ocorrido, com o hash gravado na abertura), condições de abertura e sha256 do próprio selo. A
  abertura (``HOLDOUT_OPENED``) exige aprovação humana registrada e acontece uma única vez; não há consulta
  iterativa.
- **Aplicação:** ``run_evaluation(..., hypothesis_id=...)`` recusa execução sem pré-registro ou além de
  ``max_variants``; toda execução é recusada se o dataset ou a janela alcançar um holdout selado e não aberto.
- **Deduplicação** antes do backtest: |ρ| entre a candidata e cada fator existente, só no período de
  desenvolvimento. Com |ρ| ≥ limiar, a candidata é ``REJECTED_REDUNDANT``, sem gastar backtest nem holdout. O filtro
  só controla redundância.
"""

from __future__ import annotations

import hashlib

from .dataset import canonical
from .factor_metrics import pearson
from .manifest import LedgerError, TrialLedger, utc_now

PREREG_FIELDS = ("hypothesis_id", "description", "economic_mechanism", "features", "target", "universe_rule",
                 "period", "costs", "execution_convention", "validation_protocol", "primary_metric",
                 "secondary_metrics", "policy", "max_variants", "seeds", "holdout", "criteria")
APPROVAL_FIELDS = ("approved_by", "approved_at", "reason", "channel")


def preregister(ledger: TrialLedger, record: dict) -> dict:
    if set(record) != set(PREREG_FIELDS) or any(record[k] in (None, "", [], {}) for k in PREREG_FIELDS):
        raise LedgerError(f"pré-registro: campos exatos e não vazios {list(PREREG_FIELDS)}")
    if set(record["criteria"]) != {"GO", "NO_GO", "NO_DECISION"}:
        raise LedgerError("critérios GO, NO_GO e NO_DECISION obrigatórios")
    if not {"version", "sha256"} <= set(record["policy"]):
        raise LedgerError("política com versão e sha256")
    if not isinstance(record["max_variants"], int) or record["max_variants"] < 1:
        raise LedgerError("max_variants inteiro >= 1")
    if preregistration(ledger, record["hypothesis_id"]) is not None:
        raise LedgerError("ID de hipótese já pré-registrado: imutável")
    return ledger.append_record("PREREGISTERED", "prereg:" + record["hypothesis_id"],
                                {"record": record, "record_sha256": hashlib.sha256(canonical(record)).hexdigest(),
                                 "registered_at": utc_now()})


def preregistration(ledger: TrialLedger, hypothesis_id: str) -> dict | None:
    ledger.refresh()
    return ledger.preregistration(hypothesis_id)


def require_preregistration(ledger: TrialLedger, hypothesis_id: str) -> dict:
    found = preregistration(ledger, hypothesis_id)
    if found is None:
        raise LedgerError(f"{hypothesis_id}: sem pré-registro no ledger; nenhum backtest antes dele")
    return found


def seal_holdout(ledger: TrialLedger, *, holdout_id: str, interval: list[str], content: str, conditions: str) -> dict:
    if len(interval) != 2 or interval[0] > interval[1] or not content or not conditions:
        raise LedgerError("holdout: intervalo [início, fim], conteúdo e condições")
    if _holdout_records(ledger, holdout_id, "HOLDOUT_SEALED"):
        raise LedgerError("holdout já selado: o selo é imutável")
    body = {"holdout_id": holdout_id, "interval": interval, "content": content, "conditions": conditions,
            "sealed_at": utc_now()}
    return ledger.append_record("HOLDOUT_SEALED", "holdout:" + holdout_id,
                                body | {"seal_sha256": hashlib.sha256(canonical(body)).hexdigest()})


def open_holdout(ledger: TrialLedger, holdout_id: str, approval: dict, data_sha256: str) -> dict:
    """Abertura única, só com aprovação humana registrada (quem, quando, motivo, canal)."""
    if not _holdout_records(ledger, holdout_id, "HOLDOUT_SEALED"):
        raise LedgerError("holdout não selado")
    if _holdout_records(ledger, holdout_id, "HOLDOUT_OPENED"):
        raise LedgerError("holdout já aberto: não há segunda consulta")
    if set(approval) != set(APPROVAL_FIELDS) or any(not approval[k] for k in APPROVAL_FIELDS):
        raise LedgerError(f"aprovação humana com {list(APPROVAL_FIELDS)}")
    if len(data_sha256) != 64:
        raise LedgerError("sha256 do dado aberto")
    return ledger.append_record("HOLDOUT_OPENED", "holdout:" + holdout_id,
                                {"holdout_id": holdout_id, "approval": approval, "data_sha256": data_sha256,
                                 "opened_at": utc_now()})


def _holdout_records(ledger: TrialLedger, holdout_id: str, kind: str) -> list[dict]:
    ledger.refresh()
    return ledger.holdout_records(holdout_id, kind)


def dedup_check(candidate: list[float], existing: dict[str, list[float]], *, threshold: float,
                period: tuple[str, str]) -> dict:
    """|ρ| de Pearson entre séries alinhadas do período de desenvolvimento."""
    if not 0 < threshold <= 1 or not existing:
        raise ValueError("limiar em (0, 1] e ao menos um fator existente")
    scores = {}
    for name, series in existing.items():
        if len(series) != len(candidate):
            raise ValueError(f"{name}: série desalinhada")
        rho = pearson(candidate, series)
        scores[name] = None if rho is None else abs(rho)
    finite = {k: v for k, v in scores.items() if v is not None}
    nearest = max(finite, key=lambda k: finite[k]) if finite else None
    value = finite.get(nearest) if nearest else None
    return {"status": "REJECTED_REDUNDANT" if value is not None and value >= threshold else "DISTINCT",
            "most_similar": nearest, "metric": "|pearson|", "value": value, "threshold": threshold,
            "period": list(period), "scores": scores}


def main(argv: list[str] | None = None) -> int:
    """``python -m stocks_predictor.v2.preregistration seal --ledger L --holdout-id ID --start D --end D
    --content FUTURE|sha256 --conditions TEXTO``: sela um holdout no ledger. A abertura é outra ação, humana."""
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(prog="python -m stocks_predictor.v2.preregistration")
    sub = parser.add_subparsers(dest="command", required=True)
    seal = sub.add_parser("seal")
    for flag in ("--holdout-id", "--start", "--end", "--content", "--conditions"):
        seal.add_argument(flag, required=True)
    seal.add_argument("--ledger", required=True, type=Path)
    args = parser.parse_args(argv)
    record = seal_holdout(TrialLedger(args.ledger), holdout_id=args.holdout_id, interval=[args.start, args.end],
                          content=args.content, conditions=args.conditions)
    print(json.dumps({"seq": record["seq"], "hash": record["hash"], "seal_sha256": record["payload"]["seal_sha256"],
                      "sealed_at": record["payload"]["sealed_at"]}))
    return 0


__all__ = ["APPROVAL_FIELDS", "PREREG_FIELDS", "dedup_check", "main", "open_holdout", "preregister",
           "preregistration", "require_preregistration", "seal_holdout"]


if __name__ == "__main__":
    raise SystemExit(main())
