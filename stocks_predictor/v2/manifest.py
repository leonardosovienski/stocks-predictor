"""RunManifest e TrialLedger: toda execução avaliativa fica registrada, inclusive falhas e crashes.

``TrialLedger`` é um JSONL só de acréscimo com cadeia de hashes (``prev`` → ``hash``): cada linha é escrita com
``O_APPEND`` + ``fsync`` e nada é reescrito. Ao abrir, a cadeia inteira é verificada; linha adulterada,
truncada ou fora de ordem levanta ``LedgerError`` (falha fechada, sem reparo automático).

Ciclo de uma execução (``run_evaluation``): ``STARTED`` (manifesto completo e número do trial) antes de rodar;
depois ``COMPLETED`` (métricas líquidas e brutas + digest do resultado) ou ``FAILED`` (tipo e mensagem do erro;
a exceção é relançada). Um ``STARTED`` sem desfecho cujo processo já morreu vira ``ABANDONED`` na próxima
abertura — o crash fica no ledger. Todo ``STARTED`` conta como trial, qualquer que seja o desfecho.

Cada registro terminal leva também a linha ``trial-registry/2.0.0`` validada por
``predictor_core.contracts.trial_v2.require_trial_v2`` (contrato do core). O core 3.2.1 não tem RunManifest nem
ledger com ciclo de vida: estes dois são a versão mínima local, registrada como dívida técnica.
"""

from __future__ import annotations

import hashlib
import json
import os
import socket
import subprocess
import uuid
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from predictor_core.contracts.trial_v2 import NOT_APPLICABLE, TRIAL_SCHEMA_VERSION, require_trial_v2

from . import SCHEMA
from .dataset import PITDataset, canonical
from .engine import ENGINE_VERSION, ProtocolConfig, Strategy, evaluate

POLICY_VERSION = "stocks-evaluation-protocol-v2/3a.1"
LEDGER_SCHEMA = "stocks-trial-ledger/1"
TERMINAL = ("COMPLETED", "FAILED", "ABANDONED")
MANIFEST_SCHEMA = "stocks-run-manifest/1"
EXPERIMENT_ID = "stocks-protocol-v2"
# Prompt 2 (docs/evidence/2026-09-24-prompt2-auditoria.md): 71 trials observados no domínio, limite inferior.
PRIOR_DOMAIN_TRIALS_LOWER_BOUND = 71
_ROOT = Path(__file__).resolve().parents[2]


class LedgerError(RuntimeError):
    """Ledger adulterado, truncado ou uso fora do ciclo STARTED → COMPLETED/FAILED."""


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def sha256_json(value) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def git_state(repo: Path | str | None = None) -> dict:
    """Commit e sujeira do checkout que executa; ``UNKNOWN`` (nunca inventado) fora de um checkout Git."""
    cwd = Path(repo) if repo is not None else _ROOT
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=cwd, check=True, capture_output=True,
                                text=True).stdout.strip()
        status = subprocess.run(["git", "status", "--porcelain"], cwd=cwd, check=True, capture_output=True,
                                text=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return {"commit": "UNKNOWN", "dirty": None}
    return {"commit": commit, "dirty": bool(status.strip())}


def package_version() -> str:
    try:
        return version("stocks-predictor")
    except PackageNotFoundError:
        return "uninstalled"


def build_manifest(dataset: PITDataset, strategy: Strategy, config: ProtocolConfig, *, validation: dict,
                   family: str, git: dict | None = None, run_id: str | None = None,
                   decision_policy: dict | None = None) -> dict:
    """Manifesto de uma execução avaliativa (sem métricas nem número de trial: o ledger os atribui).

    ``policy_version`` é a versão do protocolo; ``decision_policy`` (versão, status e sha256 do arquivo de
    política) entra quando a execução é avaliada sob uma política de decisão.
    """
    config_dict = config.to_dict()
    return {
        "decision_policy": decision_policy,
        "schema": MANIFEST_SCHEMA,
        "run_id": run_id or uuid.uuid4().hex,
        "created_at": utc_now(),
        "git": git if git is not None else git_state(),
        "package_version": package_version(),
        "config": config_dict,
        "config_hash": sha256_json(config_dict),
        "dataset": {"schema": SCHEMA, "hash": dataset.hash, "version": dataset.version,
                    "data_cutoff": dataset.cutoff},
        "universe": {"kind": "equity", "as_of": "PITView pré-abertura do pregão seguinte ao sinal",
                     "survivorship": "listados conhecidos na decisão, deslistados incluídos enquanto negociaram",
                     "liquidity": config.liquidity.to_dict(), "cutoff": dataset.cutoff},
        "interval": {"start": config.start, "end": config.end, "rebalance": config.rebalance},
        "seed": config.seed,
        "model": strategy.describe() | {"family": family},
        "costs": config.costs.to_dict(),
        "execution": config.execution.to_dict(),
        "validation": validation,
        "engine_version": ENGINE_VERSION,
        "policy_version": POLICY_VERSION,
    }


class TrialLedger:
    def __init__(self, path: Path | str, *, host: str | None = None):
        self.path = Path(path)
        self.host = host or socket.gethostname()
        self._records = self._load()

    # -- leitura verificada ------------------------------------------------------------------------
    def _load(self) -> list[dict]:
        if not self.path.exists():
            return []
        raw = self.path.read_bytes()
        if raw and not raw.endswith(b"\n"):
            raise LedgerError("última linha incompleta: ledger truncado")
        records, previous = [], None
        for number, line in enumerate(raw.splitlines(), start=1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise LedgerError(f"linha {number} não é JSON") from exc
            body = {k: v for k, v in record.items() if k != "hash"}
            if record.get("schema") != LEDGER_SCHEMA or record.get("seq") != number \
                    or record.get("prev") != previous or record.get("hash") != sha256_json(body):
                raise LedgerError(f"linha {number}: cadeia de hashes quebrada")
            records.append(record)
            previous = record["hash"]
        return records

    @property
    def records(self) -> list[dict]:
        return [dict(r) for r in self._records]

    def refresh(self) -> None:
        """Relê o disco: outro processo pode ter acrescentado, mas o prefixo conhecido tem de estar intacto."""
        on_disk = self._load()
        known = [r["hash"] for r in self._records]
        if [r["hash"] for r in on_disk[: len(known)]] != known:
            raise LedgerError("ledger mudou por fora desta instância de forma incompatível")
        self._records = on_disk

    def _append(self, kind: str, run_id: str, payload: dict) -> dict:
        self.refresh()
        on_disk = self._records
        body = {"schema": LEDGER_SCHEMA, "seq": len(on_disk) + 1,
                "prev": on_disk[-1]["hash"] if on_disk else None, "kind": kind, "run_id": run_id,
                "recorded_at": utc_now(), "payload": payload}
        record = body | {"hash": sha256_json(body)}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
        try:
            os.write(fd, canonical(record) + b"\n")
            os.fsync(fd)
        finally:
            os.close(fd)
        self._records.append(record)
        return record

    # -- consultas --------------------------------------------------------------------------------
    def started(self, family: str | None = None) -> list[dict]:
        return [r for r in self._records if r["kind"] == "STARTED"
                and (family is None or r["payload"]["manifest"]["model"]["family"] == family)]

    def open_runs(self) -> list[dict]:
        closed = {r["run_id"] for r in self._records if r["kind"] in TERMINAL}
        return [r for r in self.started() if r["run_id"] not in closed]

    def outcome(self, run_id: str) -> str | None:
        kinds = [r["kind"] for r in self._records if r["run_id"] == run_id and r["kind"] in TERMINAL]
        return kinds[-1] if kinds else ("STARTED" if any(r["run_id"] == run_id for r in self.started()) else None)

    def decisions(self) -> list[dict]:
        return [r for r in self._records if r["kind"] == "DECISION"]

    # -- ciclo de vida ------------------------------------------------------------------------------
    def recover_abandoned(self) -> list[str]:
        """``STARTED`` sem desfecho cujo processo (neste host) já não existe → ``ABANDONED``."""
        abandoned = []
        for record in self.open_runs():
            owner = record["payload"]["process"]
            if owner["host"] == self.host and not _alive(owner["pid"]):
                self._append("ABANDONED", record["run_id"], {"detected_at": utc_now(),
                                                              "reason": "processo terminou sem desfecho (crash)"})
                abandoned.append(record["run_id"])
        return abandoned

    def start(self, manifest: dict) -> int:
        self.refresh()
        self.recover_abandoned()
        if any(r["run_id"] == manifest["run_id"] for r in self._records):
            raise LedgerError("run_id já registrado: nada é sobrescrito")
        trial_number = len(self.started()) + 1
        self._append("STARTED", manifest["run_id"], {
            "trial_number": trial_number, "manifest": manifest,
            "process": {"host": self.host, "pid": os.getpid()}})
        return trial_number

    def _require_open(self, run_id: str) -> dict:
        match = [r for r in self.open_runs() if r["run_id"] == run_id]
        if not match:
            raise LedgerError(f"{run_id} não está em andamento")
        return match[0]

    def complete(self, run_id: str, result: dict, trial_v2: dict) -> dict:
        self._require_open(run_id)
        return self._append("COMPLETED", run_id, {"result": result, "trial_v2": trial_v2})

    def fail(self, run_id: str, error: BaseException, trial_v2: dict) -> dict:
        self._require_open(run_id)
        return self._append("FAILED", run_id, {"error_type": type(error).__name__, "error": str(error)[:2000],
                                               "trial_v2": trial_v2})

    def record_decision(self, decision: dict, evaluated_run_ids: list[str]) -> dict:
        """Decisão da política sobre execuções já concluídas (``COMPLETED``); registro próprio, append-only."""
        self.refresh()
        for run_id in evaluated_run_ids:
            if self.outcome(run_id) != "COMPLETED":
                raise LedgerError(f"decisão sobre {run_id} sem execução concluída")
        if "policy_sha256" not in decision or "decision" not in decision:
            raise LedgerError("decisão sem política identificada")
        return self._append("DECISION", "decision:" + uuid.uuid4().hex,
                            {"decision": decision, "evaluated_run_ids": list(evaluated_run_ids)})


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def trial_v2_row(ledger: TrialLedger, manifest: dict, trial_number: int, *, status: str, result: dict,
                 metric: str, selection: dict, notes: str = "") -> dict:
    """Linha ``trial-registry/2.0.0`` do core para esta execução, validada (``require_trial_v2``)."""
    family = manifest["model"]["family"]
    git = manifest["git"]
    code = (f"git:{git['commit']}{';dirty' if git['dirty'] else ''}" if git["commit"] != "UNKNOWN"
            else f"package:stocks-predictor=={manifest['package_version']}")
    known = PRIOR_DOMAIN_TRIALS_LOWER_BOUND + len(ledger.started())
    horizon = manifest["validation"].get("horizon")
    return require_trial_v2({
        "schema_version": TRIAL_SCHEMA_VERSION,
        "experiment_id": EXPERIMENT_ID,
        "hypothesis_id": manifest["model"]["name"],
        "hypothesis_family": family,
        "trial_id": manifest["run_id"],
        "registered_at": manifest["created_at"],
        "executed_at": utc_now(),
        "seed": manifest["seed"],
        "forecast_horizon": f"{horizon} sessions" if horizon else NOT_APPLICABLE,
        "data_cutoff": manifest["dataset"]["data_cutoff"],
        "label_start": manifest["interval"]["start"] + "T00:00:00Z",
        "label_end": manifest["interval"]["end"] + "T23:59:59Z",
        "dataset_hash": "sha256:" + manifest["dataset"]["hash"],
        "dataset_version": manifest["dataset"]["version"],
        "feature_version": f"pit-view/{SCHEMA}",
        "model_version": "sha256:" + sha256_json(manifest["model"]),
        "code_version": code,
        "params": {"config": manifest["config"], "model": manifest["model"]},
        "selection_path": selection,
        "n_trials_family": len(ledger.started(family)),
        "n_trials_domain": f"known_trials >= {known}",
        "n_trials_ecosystem": f"known_trials >= {known}",
        "metric": metric,
        "result": result,
        "status": status,
        "notes": notes or f"trial_number={trial_number}; policy={manifest['policy_version']}",
    })


def _net_total_return(result: dict):
    return result["net"]["total_return"]


def run_evaluation(ledger: TrialLedger, dataset: PITDataset, strategy: Strategy, config: ProtocolConfig, *,
                   family: str, validation: dict | None = None, runner=evaluate, metric: str = "net_total_return",
                   primary=_net_total_return, selection: dict | None = None, git: dict | None = None,
                   decision_policy: dict | None = None) -> dict:
    """Executa ``runner(dataset, strategy, config)`` sob o ledger. Falha → ``FAILED`` registrado e relançada.

    ``runner`` devolve um dict JSON nativo com ``result_digest``; ``primary(result)`` é o valor de ``metric``.
    """
    validation = validation or {"scheme": "single_window"}
    selection = selection or {"family": family, "candidate_set": [strategy.name],
                              "selection_metric": NOT_APPLICABLE, "selected_candidate": NOT_APPLICABLE}
    manifest = build_manifest(dataset, strategy, config, validation=validation, family=family, git=git,
                              decision_policy=decision_policy)
    trial_number = ledger.start(manifest)
    try:
        result = runner(dataset, strategy, config)
        value = primary(result)
    except BaseException as exc:
        row = trial_v2_row(ledger, manifest, trial_number, status="FAILED",
                           result={"error_type": type(exc).__name__}, metric=metric, selection=selection)
        ledger.fail(manifest["run_id"], exc, row)
        raise
    row = trial_v2_row(ledger, manifest, trial_number, status="COMPLETED",
                       result={metric: value, "result_digest": result["result_digest"]}, metric=metric,
                       selection=selection)
    ledger.complete(manifest["run_id"], result, row)
    return manifest | {"trial_number": trial_number, "status": "COMPLETED", "metrics": result}


__all__ = ["EXPERIMENT_ID", "LEDGER_SCHEMA", "LedgerError", "MANIFEST_SCHEMA", "POLICY_VERSION", "TERMINAL",
           "TrialLedger", "build_manifest", "git_state", "run_evaluation", "trial_v2_row"]
