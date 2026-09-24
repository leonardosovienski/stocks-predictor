"""Política de decisão versionada (schema ``stocks-evaluation-policy/1``).

O core 3.2.1 não tem arquivo de política de decisão: esta é a versão local mínima, registrada como dívida
técnica. Os limiares vivem só no arquivo JSON versionado (``policy/stocks-evaluation-policy-v1.json``). Toda
decisão carrega a versão, o status e o sha256 do arquivo (bytes com CRLF normalizado para LF).

Decisões:
    NO_DECISION   falta insumo: baseline exigido ausente, taxa livre de risco não admitida, dataset sintético,
                  amostra curta, DSR ou PBO não estimáveis, métrica indefinida
    REJECT        algum gate reprovou
    PASS          todos os gates passaram (não habilita capital; é a entrada da etapa seguinte)

Gates: vencer cada baseline exigido na métrica da política (estritamente), PSR ≥ mínimo, DSR no pior N ≥ mínimo,
PBO ≤ máximo. O t de Harvey, Liu & Zhu é diagnóstico, a menos que ``t_stat.role`` seja ``"gate"``.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from .manifest import utc_now

SCHEMA = "stocks-evaluation-policy/1"
DECISIONS = ("PASS", "REJECT", "NO_DECISION")
_SECTIONS = {"schema", "policy_version", "status", "created_at", "scope", "data", "risk_free", "baselines", "psr",
             "dsr", "pbo", "t_stat", "cpcv"}


class PolicyError(ValueError):
    """Arquivo de política inválido."""


class Policy:
    def __init__(self, raw: dict, sha256: str, path: str):
        if type(raw) is not dict or raw.get("schema") != SCHEMA or set(raw) != _SECTIONS:
            raise PolicyError(f"política não é {SCHEMA} com as seções {sorted(_SECTIONS)}")
        self.raw, self.sha256, self.path = raw, sha256, path
        self.version, self.status = raw["policy_version"], raw["status"]
        _probability(raw["psr"]["min_probability"], "psr.min_probability")
        _probability(raw["dsr"]["min_probability"], "dsr.min_probability")
        _probability(raw["pbo"]["max"], "pbo.max")
        if not raw["baselines"]["required"] or raw["baselines"]["rule"] != "strictly_greater_than_each":
            raise PolicyError("baselines.required não vazio e rule = strictly_greater_than_each")
        if raw["dsr"]["aggregation"] != "worst_case" or not raw["dsr"]["n_multipliers"]:
            raise PolicyError("dsr: aggregation = worst_case e multiplicadores não vazios")
        if raw["t_stat"]["role"] not in ("diagnostic", "gate"):
            raise PolicyError("t_stat.role: diagnostic | gate")
        if raw["pbo"]["n_splits"] % 2 or raw["pbo"]["n_splits"] < 2:
            raise PolicyError("pbo.n_splits par >= 2")

    def section(self, name: str) -> dict:
        return self.raw[name]

    def identity(self) -> dict:
        return {"policy_version": self.version, "policy_status": self.status, "policy_sha256": self.sha256,
                "policy_path": self.path}


def _probability(value, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
        raise PolicyError(f"{name} em [0, 1]")


def load_policy(path: Path | str) -> Policy:
    data = Path(path).read_bytes().replace(b"\r\n", b"\n")
    return Policy(json.loads(data), hashlib.sha256(data).hexdigest(), Path(path).as_posix())


def _finite(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def decide(evidence: dict, policy: Policy) -> dict:
    """``evidence``: dataset_version, risk_free_series_id, sessions, strategy (relatório), baselines
    {nome: relatório}, dsr (``metrics.dsr_sensitivity`` ou None), pbo (``pbo_cscv`` ou None), t_stat (ou None)."""
    missing = []
    data, baselines = policy.section("data"), policy.section("baselines")
    metric = baselines["metric"]
    absent = [name for name in baselines["required"] if name not in (evidence.get("baselines") or {})]
    if absent:
        missing.append(f"sem comparação com baseline: faltam {absent}")
    if evidence.get("risk_free_series_id") not in policy.section("risk_free")["allowed_series"]:
        missing.append(f"taxa livre de risco não admitida: {evidence.get('risk_free_series_id')!r}")
    if data["forbid_synthetic_dataset"] and str(evidence.get("dataset_version", "")).startswith("synthetic"):
        missing.append("dataset sintético não sustenta decisão")
    if not isinstance(evidence.get("sessions"), int) or evidence["sessions"] < data["min_sessions"]:
        missing.append(f"amostra com menos de {data['min_sessions']} pregões")
    if evidence.get("dsr") is None:
        missing.append("DSR não estimável")
    if evidence.get("pbo") is None:
        missing.append("PBO não estimável")
    strategy_value = (evidence.get("strategy") or {}).get(metric)
    if not _finite(strategy_value):
        missing.append(f"métrica {metric} da estratégia indefinida")
    checks = []
    if not missing:
        for name in baselines["required"]:
            value = evidence["baselines"][name].get(metric)
            if not _finite(value):
                missing.append(f"métrica {metric} do baseline {name} indefinida")
                continue
            checks.append({"gate": f"beats:{name}", "value": strategy_value, "threshold": value,
                           "passed": strategy_value > value})
        psr = evidence["strategy"].get("psr_vs_zero")
        checks.append({"gate": "psr", "value": psr, "threshold": policy.section("psr")["min_probability"],
                       "passed": _finite(psr) and psr >= policy.section("psr")["min_probability"]})
        worst = evidence["dsr"]["worst"]
        checks.append({"gate": "dsr_worst_case", "value": worst["dsr"], "n": worst["n"],
                       "threshold": policy.section("dsr")["min_probability"],
                       "passed": _finite(worst["dsr"]) and worst["dsr"] >= policy.section("dsr")["min_probability"]})
        pbo = evidence["pbo"]["pbo"]
        checks.append({"gate": "pbo", "value": pbo, "threshold": policy.section("pbo")["max"],
                       "passed": pbo <= policy.section("pbo")["max"]})
    t_rule = policy.section("t_stat")
    t_value = evidence.get("t_stat")
    t_check = {"gate": "t_stat", "value": t_value, "threshold": t_rule["threshold"], "role": t_rule["role"],
               "passed": _finite(t_value) and t_value > t_rule["threshold"]}
    if missing:
        decision = "NO_DECISION"
    else:
        gating = checks + ([t_check] if t_rule["role"] == "gate" else [])
        decision = "PASS" if all(c["passed"] for c in gating) else "REJECT"
    return policy.identity() | {
        "decision": decision, "decided_at": utc_now(), "no_decision_reasons": missing, "checks": checks,
        "diagnostics": [t_check] if t_rule["role"] == "diagnostic" else [],
        "failed": [c["gate"] for c in checks if not c["passed"]],
    }


__all__ = ["DECISIONS", "Policy", "PolicyError", "decide", "load_policy"]
