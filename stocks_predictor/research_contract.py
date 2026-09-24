"""STOCKS research contract: request/result schemas owned by the stocks domain.

No envelope, transport, signing or CAIN concepts live here (qualification stage A).
Requests arrive as local files (requester trust LOCAL_FILE_ONLY). Every identifier that
leaves the domain is qualified with the ``stocks:`` prefix.

A request declares intent only: request type, hypothesis, references by (name, version)
to operator-provisioned immutable objects (dataset snapshot, universe definition,
features, ranking/selection model, baseline, costs, External Intelligence readiness),
the PIT cutoff ``as_of``, PIT metadata and bounded parameters. It never names a command,
module, path, URL, SQL, handler, final budget, final priority or capital permission.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import datetime
from typing import Any

DOMAIN_PREFIX = "stocks"
REQUEST_SCHEMA = "stocks-research-request/1"
RESULT_SCHEMA = "stocks-research-result/1"
OUTCOME_SCHEMA = "stocks-research-outcome/1"
REQUESTER_TRUST = "LOCAL_FILE_ONLY"

BACKTEST = "BACKTEST_PIT_FACTOR"
COLLECT = "COLLECT_EXTERNAL_INTELLIGENCE"
REQUEST_TYPES = (BACKTEST, COLLECT)
REFERENCE_KINDS = {
    BACKTEST: ("dataset", "universe", "features", "model", "baseline", "cost_model", "readiness"),
    COLLECT: ("source", "readiness"),
}
PRIORITIES = ("LOW", "NORMAL", "HIGH")
PIT_CLASSES = ("PIT_STRICT", "PIT_RECONSTRUCTED", "HISTORICAL_ONLY")
EI_MODES = ("NONE", "COLLECTION_ONLY", "TRIAL_CONSUMPTION")
EI_FAMILIES = (
    "B3_LENDING",
    "CVM_VLMO",
    "CVM_BUYBACK",
    "CVM_CDA",
    "CVM_ENTREGA",
    "CVM_FCA_IDENTITY",
    "CVM_IPE_METADATA",
)
COLLECTORS = {
    "cvm-vlmo": ("CVM_VLMO", "year"),
    "cvm-buyback": ("CVM_BUYBACK", "none"),
    "cvm-ipe": ("CVM_IPE_METADATA", "year"),
    "cvm-fca-identity": ("CVM_FCA_IDENTITY", "year"),
    "cvm-cda": ("CVM_CDA", "month"),
    "cvm-entrega": ("CVM_ENTREGA", "month"),
}
NEGATIVE_CONTROLS = ("SHUFFLED_LABELS", "TEMPORAL_ABLATION", "FEATURE_ABLATION", "UNIVERSE_PERTURBATION")

# Closed enum of terminal research results (C24.1 result_states). None of them is a
# capital authorization; WATCH_NO_CAPITAL is the most favourable and still forbids capital.
RESULT_STATES = (
    "WATCH_NO_CAPITAL",
    "NO_EDGE",
    "INCONCLUSIVE",
    "REFUTED",
    "NOT_READY",
    "CLOSED_INSUFFICIENT_SAMPLE",
    "INCONCLUSIVE_DATA_QUALITY",
    "FAILED_OPERATIONAL",
    "COLLECTION_RECORDED",
)
# Non-terminal or refusal outcomes reported for one submission (never a stored result).
OUTCOME_STATUSES = (
    "RESULT",
    "DUPLICATE",
    "REJECTED",
    "CONFLICT",
    "NOT_READY",
    "OPS_FAILED_RETRYABLE",
    "STATE_BUSY_RETRYABLE",
    "STORAGE_FAILED_RETRYABLE",
    "TEMPORAL_INTEGRITY_VIOLATION",
    "RECONCILIATION_REQUIRED",
)
EXIT_CODES = {
    "RESULT": 0,
    "DUPLICATE": 0,
    "REJECTED": 2,
    "CONFLICT": 2,
    "NOT_READY": 3,
    "OPS_FAILED_RETRYABLE": 3,
    "STATE_BUSY_RETRYABLE": 3,
    "STORAGE_FAILED_RETRYABLE": 3,
    "TEMPORAL_INTEGRITY_VIOLATION": 4,
    "RECONCILIATION_REQUIRED": 5,
}
OPERATIONAL_STATES = ("SUCCEEDED", "FAILED", "TIMEOUT", "SKIPPED_ALREADY_SUCCEEDED")
SCIENTIFIC_STATES = ("SUPPORTED", "REFUTED", "INCONCLUSIVE", "INSUFFICIENT_SAMPLE", "NOT_EVALUATED")
ECONOMIC_STATES = ("WATCH", "NO_EDGE", "NOT_EVALUATED")

_ID = re.compile(r"^stocks:[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_NAME = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,63}$")
_HASH = re.compile(r"^[0-9a-f]{64}$")
_AS_OF = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")

BACKTEST_PARAMETERS = {
    "target": ("NEXT_REBALANCE_RETURN",),
    "fee_bps": (0, 1000),
    "slippage_bps": (0, 1000),
    "max_securities": (1, 5000),
}


class ContractError(ValueError):
    """A request or result does not match the stocks contract (fail closed)."""

    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason


def canonical(value: Any) -> bytes:
    """Canonical UTF-8 JSON: sorted keys, no whitespace, no NaN/Infinity."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def content_hash(value: Any) -> str:
    return digest(canonical(value))


def loads_strict(raw: bytes | str) -> Any:
    """Parse JSON rejecting duplicate keys and non-finite constants."""

    def pairs(items):
        out = {}
        for key, val in items:
            if key in out:
                raise ContractError("SCHEMA_INVALID", f"duplicate key {key!r}")
            out[key] = val
        return out

    def constant(name):
        raise ContractError("SCHEMA_INVALID", f"non-finite constant {name}")

    try:
        text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError("SCHEMA_INVALID", "invalid JSON") from exc


def utc(value: Any, field: str) -> datetime:
    if type(value) is not str or not value.endswith("Z"):
        raise ContractError("SCHEMA_INVALID", f"{field} must be ISO-8601 UTC ending in Z")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError("SCHEMA_INVALID", f"{field} is not a timestamp") from exc
    offset = parsed.utcoffset()
    if offset is None or offset.total_seconds() != 0:
        raise ContractError("SCHEMA_INVALID", f"{field} must be UTC")
    return parsed


def _keys(value: Any, required: set[str], optional: set[str], label: str) -> None:
    if type(value) is not dict:
        raise ContractError("SCHEMA_INVALID", f"{label} must be an object")
    missing = required - set(value)
    extra = set(value) - required - optional
    if missing or extra:
        raise ContractError(
            "SCHEMA_INVALID", f"{label}: missing {sorted(missing)} unknown {sorted(extra)}"
        )


def qualified_id(value: Any, field: str) -> str:
    if type(value) is not str or not _ID.fullmatch(value):
        raise ContractError("SCHEMA_INVALID", f"{field} must be a stocks:-qualified identifier")
    return value


def _int(value: Any, bounds: tuple[int, int], field: str) -> int:
    low, high = bounds
    if type(value) is not int or not low <= value <= high:
        raise ContractError("PARAMETER_OUT_OF_BOUNDS", field)
    return value


def _backtest_parameters(params: Any) -> None:
    _keys(params, {"target", "fee_bps", "slippage_bps", "max_securities", "external_intelligence"},
          {"negative_control"}, "parameters")
    if params["target"] not in BACKTEST_PARAMETERS["target"]:
        raise ContractError("SCHEMA_INVALID", "parameters.target")
    for field in ("fee_bps", "slippage_bps", "max_securities"):
        _int(params[field], BACKTEST_PARAMETERS[field], f"parameters.{field}")
    ei = params["external_intelligence"]
    _keys(ei, {"mode", "families"}, set(), "parameters.external_intelligence")
    if ei["mode"] not in EI_MODES:
        raise ContractError("SCHEMA_INVALID", "parameters.external_intelligence.mode")
    families = ei["families"]
    if (
        type(families) is not list
        or len(families) != len(set(families))
        or any(item not in EI_FAMILIES for item in families)
    ):
        raise ContractError("SCHEMA_INVALID", "parameters.external_intelligence.families")
    if (ei["mode"] == "NONE") != (not families):
        raise ContractError("SCHEMA_INVALID", "families must be empty exactly when mode is NONE")
    if "negative_control" in params:
        control = params["negative_control"]
        _keys(control, {"kind", "seed"}, set(), "parameters.negative_control")
        if control["kind"] not in NEGATIVE_CONTROLS:
            raise ContractError("SCHEMA_INVALID", "parameters.negative_control.kind")
        _int(control["seed"], (0, 1_000_000), "parameters.negative_control.seed")


def _collect_parameters(params: Any) -> None:
    _keys(params, {"collector", "period", "observed_at"}, set(), "parameters")
    collector = COLLECTORS.get(params["collector"]) if type(params["collector"]) is str else None
    if collector is None:
        raise ContractError("SCHEMA_INVALID", "parameters.collector")
    period, kind = params["period"], collector[1]
    patterns = {"year": r"[0-9]{4}", "month": r"[0-9]{4}-[0-9]{2}", "none": r"ALL"}
    if type(period) is not str or not re.fullmatch(patterns[kind], period):
        raise ContractError("SCHEMA_INVALID", "parameters.period")
    utc(params["observed_at"], "parameters.observed_at")


def validate_request(request: Any) -> dict:
    """Validate a stocks research request. Returns it unchanged or raises ContractError."""
    _keys(
        request,
        {
            "schema_version",
            "request_id",
            "request_type",
            "research_id",
            "hypothesis_id",
            "references",
            "as_of",
            "pit",
            "parameters",
            "priority_hint",
        },
        {"client_ref"},
        "request",
    )
    if request["schema_version"] != REQUEST_SCHEMA:
        raise ContractError("SCHEMA_INVALID", "schema_version")
    for field in ("request_id", "research_id", "hypothesis_id"):
        qualified_id(request[field], field)
    if request["request_type"] not in REQUEST_TYPES:
        raise ContractError("REQUEST_TYPE_NOT_ALLOWED", str(request["request_type"])[:64])
    kinds = REFERENCE_KINDS[request["request_type"]]
    refs = request["references"]
    _keys(refs, set(kinds), set(), "references")
    for kind in kinds:
        _keys(refs[kind], {"name", "version"}, set(), f"references.{kind}")
        for field in ("name", "version"):
            if type(refs[kind][field]) is not str or not _NAME.fullmatch(refs[kind][field]):
                raise ContractError("SCHEMA_INVALID", f"references.{kind}.{field}")
    if type(request["as_of"]) is not str or not _AS_OF.fullmatch(request["as_of"]):
        raise ContractError("SCHEMA_INVALID", "as_of must be YYYY-MM-DDTHH:MM:SSZ")
    utc(request["as_of"], "as_of")
    pit = request["pit"]
    _keys(pit, {"availability_rule", "minimum_pit_class"}, set(), "pit")
    if pit["availability_rule"] != "AVAILABLE_AT_LE_DECISION_TIME":
        raise ContractError("SCHEMA_INVALID", "pit.availability_rule")
    if pit["minimum_pit_class"] not in ("PIT_STRICT", "PIT_RECONSTRUCTED"):
        raise ContractError("SCHEMA_INVALID", "pit.minimum_pit_class")
    if request["request_type"] == BACKTEST:
        _backtest_parameters(request["parameters"])
    else:
        _collect_parameters(request["parameters"])
    if request["priority_hint"] not in PRIORITIES:
        raise ContractError("SCHEMA_INVALID", "priority_hint")
    if "client_ref" in request:
        try:
            raw = canonical(request["client_ref"])
        except (TypeError, ValueError) as exc:
            raise ContractError("SCHEMA_INVALID", "client_ref must be JSON") from exc
        if len(raw) > 1024:
            raise ContractError("SCHEMA_INVALID", "client_ref larger than 1024 bytes")
    return request


def idempotency_key(request: dict) -> str:
    """Two submissions are the same logical request iff they share request_id."""
    return request["request_id"]


def request_content_hash(request: dict) -> str:
    """Content identity of a request; client_ref is excluded (opaque, echoed back)."""
    return content_hash({key: value for key, value in request.items() if key != "client_ref"})


def _finite(value: Any, path: str = "result") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ContractError("RESULT_INVALID", f"non-finite value at {path}")
    if isinstance(value, dict):
        for key, item in value.items():
            _finite(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _finite(item, f"{path}[{index}]")


RESULT_FIELDS = {
    "schema_version",
    "result_id",
    "request_id",
    "admission_id",
    "experiment_id",
    "research_id",
    "hypothesis_id",
    "request_type",
    "as_of",
    "result_state",
    "operational_state",
    "scientific_state",
    "economic_state",
    "capital_permission",
    "trial_eligible",
    "produced_at",
    "core_facts",
    "ops_facts",
    "domain_facts",
    "provenance",
}


def validate_result(result: Any) -> dict:
    """Validate a stocks research result, including authority separation invariants."""
    _keys(result, RESULT_FIELDS, set(), "result")
    if result["schema_version"] != RESULT_SCHEMA:
        raise ContractError("RESULT_INVALID", "schema_version")
    for field in ("result_id", "request_id", "admission_id", "experiment_id", "research_id", "hypothesis_id"):
        qualified_id(result[field], field)
    if result["request_type"] not in REQUEST_TYPES:
        raise ContractError("RESULT_INVALID", "request_type")
    utc(result["as_of"], "as_of")
    for field, allowed in (
        ("result_state", RESULT_STATES),
        ("operational_state", OPERATIONAL_STATES),
        ("scientific_state", SCIENTIFIC_STATES),
        ("economic_state", ECONOMIC_STATES),
    ):
        if result[field] not in allowed:
            raise ContractError("RESULT_INVALID", field)
    if result["capital_permission"] is not False:
        raise ContractError("RESULT_INVALID", "capital_permission must be false")
    if type(result["trial_eligible"]) is not bool:
        raise ContractError("RESULT_INVALID", "trial_eligible must be boolean")
    utc(result["produced_at"], "produced_at")
    for block in ("core_facts", "ops_facts", "domain_facts", "provenance"):
        if type(result[block]) is not dict:
            raise ContractError("RESULT_INVALID", f"{block} must be an object")
    science, economy, state = result["scientific_state"], result["economic_state"], result["result_state"]
    # Authority separation: operations never imply science; science never implies edge.
    if result["operational_state"] not in ("SUCCEEDED", "SKIPPED_ALREADY_SUCCEEDED"):
        if (science, economy, state) != ("NOT_EVALUATED", "NOT_EVALUATED", "FAILED_OPERATIONAL"):
            raise ContractError("RESULT_INVALID", "failed operation cannot carry scientific or economic state")
    if state == "FAILED_OPERATIONAL" and result["operational_state"] in ("SUCCEEDED", "SKIPPED_ALREADY_SUCCEEDED"):
        raise ContractError("RESULT_INVALID", "FAILED_OPERATIONAL requires a failed operation")
    if economy == "WATCH" and science != "SUPPORTED":
        raise ContractError("RESULT_INVALID", "economic WATCH requires SUPPORTED science")
    if (state == "WATCH_NO_CAPITAL") != (economy == "WATCH"):
        raise ContractError("RESULT_INVALID", "WATCH_NO_CAPITAL iff economic WATCH")
    if state in ("NOT_READY", "INCONCLUSIVE_DATA_QUALITY", "COLLECTION_RECORDED", "FAILED_OPERATIONAL"):
        if (science, economy) != ("NOT_EVALUATED", "NOT_EVALUATED"):
            raise ContractError("RESULT_INVALID", f"{state} cannot carry scientific or economic state")
    if state == "CLOSED_INSUFFICIENT_SAMPLE" and (science, economy) != ("INSUFFICIENT_SAMPLE", "NOT_EVALUATED"):
        raise ContractError("RESULT_INVALID", "CLOSED_INSUFFICIENT_SAMPLE state mismatch")
    if state == "COLLECTION_RECORDED" and (result["request_type"] != COLLECT or result["trial_eligible"]):
        raise ContractError("RESULT_INVALID", "COLLECTION_RECORDED is collection-only and never trial eligible")
    if result["request_type"] == COLLECT and state not in ("COLLECTION_RECORDED", "FAILED_OPERATIONAL", "NOT_READY"):
        raise ContractError("RESULT_INVALID", "collection results never carry research states")
    if result["trial_eligible"] and (result["request_type"] != BACKTEST or not result["core_facts"].get("trial_ids")):
        raise ContractError("RESULT_INVALID", "trial_eligible requires a Core trial of a backtest")
    for field in ("content_hash", "request_content_hash"):
        value = result["provenance"].get(field)
        if value is not None and not _HASH.fullmatch(str(value)):
            raise ContractError("RESULT_INVALID", f"provenance.{field}")
    _finite(result)
    canonical(result)
    return result


__all__ = [
    "DOMAIN_PREFIX",
    "REQUEST_SCHEMA",
    "RESULT_SCHEMA",
    "OUTCOME_SCHEMA",
    "REQUESTER_TRUST",
    "BACKTEST",
    "COLLECT",
    "REQUEST_TYPES",
    "REFERENCE_KINDS",
    "PIT_CLASSES",
    "EI_MODES",
    "EI_FAMILIES",
    "COLLECTORS",
    "NEGATIVE_CONTROLS",
    "RESULT_STATES",
    "OUTCOME_STATUSES",
    "EXIT_CODES",
    "OPERATIONAL_STATES",
    "SCIENTIFIC_STATES",
    "ECONOMIC_STATES",
    "ContractError",
    "canonical",
    "digest",
    "content_hash",
    "loads_strict",
    "utc",
    "qualified_id",
    "validate_request",
    "validate_result",
    "idempotency_key",
    "request_content_hash",
]
