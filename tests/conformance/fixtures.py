"""Frozen conformance vectors for the stocks research contract.

Deterministic synthetic PIT panels (contract conformance, not scientific evidence):
    positive      persistent drifts: momentum top quintile beats the EW universe (gross)
    case_a        drifts redrawn every period: no persistence -> Core CI crosses zero
    case_b        = positive panel with an expensive cost model (gross > 0, net <= 0)
    insufficient  fewer rebalances than the model's minimum sample
    future_canary positive panel + one bar available after as_of (FUTURE_CANARY_STOCKS_001)
Lifecycle events inside every panel: S13 IPO (bars before listing), S14 delisted, S12
ticker change, S11 issuer CNPJ change (reorganization), S16 second class of issuer C01.
Everything is provisioned through the real operator boundary (ReferenceStore.put_operator_bytes).
"""

from __future__ import annotations

import base64
import copy
import hashlib
import io
import json
import os
import random
import shutil
import subprocess
import sys
import zipfile
from datetime import date, timedelta
from pathlib import Path

from stocks_predictor.research_contract import canonical
from stocks_predictor.research_execution import EXEC_DIR, EXPERIMENTS_DIR, OPS_DIR, ReferenceStore, experiment_dir

CANARY = "FUTURE_CANARY_STOCKS_001"
HYPOTHESIS = "stocks:QUAL-PIT-MOM-001"
COLLECTION_HYPOTHESIS = "stocks:QUAL-EI-COLLECTION-001"
FAMILY = "stocks-qualification-momentum-12-1-pit"
FEE_BPS, SLIPPAGE_BPS = 3, 15
SESSIONS = 700
START = date(2021, 1, 4)
BACKTEST_HANDLER = "stocks.handlers.pit_factor_backtest.v1"
COLLECT_HANDLER = "stocks.handlers.external_collection.v1"
MATRIX_PATH = Path(__file__).resolve().parents[2] / "EXTERNAL_INTELLIGENCE_TRIAL_READINESS_MATRIX.json"


def calendar(n: int = SESSIONS) -> list[str]:
    out, day = [], START
    while len(out) < n:
        if day.weekday() < 5:
            out.append(day.isoformat())
        day += timedelta(days=1)
    return out


def as_of_for(sessions: list[str]) -> str:
    last = date.fromisoformat(sessions[-1])
    return (last + timedelta(days=1)).isoformat() + "T00:00:00Z"


def _at(session: str, clock: str = "21:30:00") -> str:
    return f"{session}T{clock}Z"


def panel(name: str = "positive", *, sessions: int = SESSIONS, seed: int = 20260924) -> dict:
    """A deterministic stocks-pit-panel/1 object."""
    cal = calendar(sessions)
    rng = random.Random(seed)
    securities, tickers, identities, bars = [], [], [], []
    drifts = {f"S{i:02d}": -0.0015 + 0.0003 * i for i in range(1, 17)}
    for i in range(1, 17):
        sid = f"S{i:02d}"
        listed = cal[0]
        listing_at = _at(cal[0], "12:00:00")
        delisted = delisting_at = None
        if sid == "S13":  # IPO at session 200 (announced 5 sessions earlier); bars exist before it
            listed, listing_at = cal[200], _at(cal[195])
        if sid == "S14" and len(cal) > 402:  # delisted at session 400, known two sessions later
            delisted, delisting_at = cal[400], _at(cal[402])
        securities.append({"security_id": sid, "listed_on": listed, "listing_available_at": listing_at,
                           "delisted_on": delisted, "delisting_available_at": delisting_at})
        tickers.append({"security_id": sid, "ticker": f"TK{i:02d}3", "effective_on": cal[0],
                        "available_at": _at(cal[0], "12:00:00")})
        issuer = "C01" if sid == "S16" else f"C{i:02d}"
        identities.append({"security_id": sid, "issuer_cnpj": f"{issuer}.000.000/0001-{i:02d}",
                           "effective_on": cal[0], "available_at": _at(cal[0], "12:00:00"),
                           "source": "CVM_FCA"})
        close = 20.0 + i
        for k, session in enumerate(cal):
            if name == "case_a":
                if k % 21 == 0:
                    drifts[sid] = rng.gauss(0.0, 0.004)
                drift = drifts[sid]
            else:
                drift = drifts[sid]
            close *= 1.0 + drift + rng.gauss(0.0, 0.01)
            if delisted is not None and session > delisted:
                continue
            weight = {"S11": 30, "S12": 29, "S13": 28, "S14": 27, "S15": 26, "S16": 3}.get(sid, 17 - i)
            volume = 1_000_000.0 * weight * (1.0 + 0.1 * rng.random())
            bars.append({"security_id": sid, "session": session, "close": round(close, 6),
                         "volume_fin": round(volume, 2), "available_at": _at(session)})
    # S12 changes ticker at 300 (announced at 290); S11 issuer reorganized to a new CNPJ at 350.
    tickers.append({"security_id": "S12", "ticker": "NW123", "effective_on": cal[300], "available_at": _at(cal[290])})
    identities.append({"security_id": "S11", "issuer_cnpj": "C99.000.000/0001-11", "effective_on": cal[350],
                       "available_at": _at(cal[350], "12:00:00"), "source": "CVM_FCA"})
    as_of = as_of_for(cal)
    value = {
        "schema": "stocks-pit-panel/1",
        "dataset_version": f"conformance-{name}-v1",
        "data_cutoff": as_of,
        "pit_classes": {"securities": "PIT_RECONSTRUCTED", "ticker_events": "PIT_RECONSTRUCTED",
                        "identity_events": "PIT_RECONSTRUCTED", "bars": "PIT_RECONSTRUCTED"},
        "securities": securities,
        "ticker_events": tickers,
        "identity_events": identities,
        "bars": bars,
    }
    if name == "future_canary":
        future = (date.fromisoformat(as_of[:10]) + timedelta(days=3)).isoformat()
        value["bars"].append({"security_id": "S01", "session": future, "close": 987.654321,
                              "volume_fin": 123456789.0, "available_at": _at(future)})
        value["canary"] = {"token": CANARY, "security_id": "S01", "session": future, "close": 987.654321}
    return value


def dataset_object(name: str) -> dict:
    if name == "insufficient":
        return panel("insufficient", sessions=400)
    base = "positive" if name in ("positive", "case_b", "future_canary") else name
    value = panel(base) if name != "future_canary" else panel("future_canary")
    value["dataset_version"] = f"conformance-{name}-v1"
    return value


def matrix() -> dict:
    return json.loads(MATRIX_PATH.read_text(encoding="utf-8"))


def ready_matrix(family: str = "CVM_VLMO") -> dict:
    """A counterfactual matrix where `family` is READY with effective PIT_STRICT (unit probes)."""
    value = copy.deepcopy(matrix())
    for entry in value["eligible_families"]:
        if entry["source"] == family:
            entry["readiness"] = "READY"
            entry["protocol_effective_PIT"] = {"PIT_STRICT": 100, "PIT_RECONSTRUCTED": 0, "HISTORICAL_ONLY": 0,
                                               "reason": "counterfactual conformance probe"}
    return value


def vlmo_zip(year: int = 2026) -> bytes:
    """Official-shaped VLMO archive, same rows as tests/test_external_intelligence.py."""
    from stocks_predictor import external_intelligence as external

    cnpj = "33.000.167/0001-01"
    main = [cnpj, "PETROBRAS", "2026-08-31", "1", "9512", "VLMO", "Mensal", "2026-09-10",
            "AP", "", "VLMO-1", "https://example.invalid/vlmo"]
    detail = [cnpj, "PETROBRAS", "2026-08-31", "1", "Administrador", "PESSOA", "Diretor",
              "Saldo Inicial", "Posicao", "Compra", "Acoes", "PN", "BANCO", "2026-08-29",
              "10", "25,50", "255,00"]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, columns, row in ((f"vlmo_cia_aberta_{year}.csv", external.VLMO_MAIN, main),
                                   (f"vlmo_cia_aberta_con_{year}.csv", external.VLMO_DETAIL, detail)):
            info = zipfile.ZipInfo(name, date_time=(2026, 9, 1, 0, 0, 0))
            text = ";".join(columns) + "\n" + ";".join(row) + "\n"
            archive.writestr(info, text.encode("latin-1"))
    return buffer.getvalue()


def source_object(payload: bytes, collector: str = "cvm-vlmo", file_name: str = "vlmo_cia_aberta_2026.zip") -> dict:
    return {"schema": "stocks-ei-source/1", "collector": collector, "file_name": file_name,
            "payload_b64": base64.b64encode(payload).decode("ascii"),
            "payload_sha256": hashlib.sha256(payload).hexdigest()}


def objects() -> dict[tuple[str, str], dict]:
    out = {
        ("universe", "conformance"): {"universe_id": "stocks:UNIVERSE-CONFORMANCE", "top_n": 10,
                                      "liquidity_lookback_sessions": 20, "min_history_sessions": 40,
                                      "rebalance_every_sessions": 21, "identity": "SECURITY_ID_ISSUER_CNPJ_DEDUP"},
        ("features", "momentum"): {"feature_version": "momentum-60-5-v1", "feature": "MOMENTUM_12_1",
                                   "lookback": 60, "skip": 5},
        ("model", "quintile"): {
            "handler": BACKTEST_HANDLER, "model_version": "top-quintile-ew-v1", "quantile": 0.2, "take": "top",
            "minimum_sample": 24, "hypothesis_family": FAMILY, "minimum_price_pit_class": "PIT_RECONSTRUCTED",
            "external_intelligence_bindings": [],
            "statistics": {"scheme": "stationary", "block_length": 3, "n_boot": 2000, "confidence": 0.95, "seed": 42},
            "selection_path": {"family": FAMILY, "candidate_set": ["top-quintile-ew-v1"],
                               "selection_metric": "predeclared", "selected_candidate": "top-quintile-ew-v1"},
        },
        ("baseline", "ew-universe"): {"baseline_id": "stocks:BASELINE-EW-UNIVERSE", "method": "EQUAL_WEIGHT_UNIVERSE"},
        ("cost_model", "h1-frozen"): {"b3_fee_pct": 0.0003, "spread_slippage_pct": 0.0015},
        ("cost_model", "expensive"): {"b3_fee_pct": 0.01, "spread_slippage_pct": 0.04},
        ("readiness", "matrix-20260921"): matrix(),
        ("readiness", "counterfactual-vlmo-ready"): ready_matrix("CVM_VLMO"),
        ("source", "vlmo-2026"): source_object(vlmo_zip(2026)),
    }
    for name in ("positive", "case_a", "case_b", "insufficient", "future_canary"):
        out[("dataset", name.replace("_", "-"))] = dataset_object(name)
    return out


def build(root: Path, *, timeout_seconds: int = 300, max_retries: int = 2, max_pending: int = 1000,
          extra_objects: dict | None = None) -> dict:
    root = Path(root)
    store = ReferenceStore(root / "objects")
    registry = []
    for (kind, name), value in sorted({**objects(), **(extra_objects or {})}.items()):
        object_hash = store.put_operator_bytes(canonical(value))
        registry.append({"kind": kind, "name": name, "version": "v1",
                         "revision_id": f"{kind}:{name}:conformance-v1", "content_hash": object_hash})
    policy = {
        "schema_version": "StocksResearchAdmissionPolicyV1",
        "policy_id": "stocks-conformance",
        "policy_version": 1,
        "owner": "STOCKS_OPERATOR",
        "requester_trust": "LOCAL_FILE_ONLY",
        "handlers": {"BACKTEST_PIT_FACTOR": BACKTEST_HANDLER, "COLLECT_EXTERNAL_INTELLIGENCE": COLLECT_HANDLER},
        "hypotheses": {
            HYPOTHESIS: {"hypothesis_family": FAMILY, "purpose": "qualification probe; not a scientific hypothesis"},
            COLLECTION_HYPOTHESIS: {"hypothesis_family": "stocks-ei-collection-only",
                                    "purpose": "External Intelligence collection monitoring; never a trial"},
        },
        "registry": registry,
        "limits": {"max_pending_requests": max_pending, "max_request_bytes": 16384, "max_parameter_bytes": 1024,
                   "max_concurrency": 1, "cpu_seconds": 300, "memory_mb": 1024, "disk_mb": 512,
                   "timeout_seconds": timeout_seconds, "max_retries": max_retries, "max_priority": "NORMAL"},
        "allowed_collectors": ["cvm-vlmo"],
    }
    policy_path = root / "policy.json"
    policy_path.write_text(json.dumps(policy, indent=1), encoding="utf-8")
    (root / "requests").mkdir(exist_ok=True)
    return {"root": root, "policy": policy_path, "objects": root / "objects", "state": root / "s",
            "requests": root / "requests"}


def request(request_id: str, dataset: str = "positive", **overrides) -> dict:
    as_of = dataset_object(dataset)["data_cutoff"] if dataset != "future_canary" else panel("positive")["data_cutoff"]
    value = {
        "schema_version": "stocks-research-request/1",
        "request_id": request_id,
        "request_type": "BACKTEST_PIT_FACTOR",
        "research_id": "stocks:RESEARCH-CONFORMANCE",
        "hypothesis_id": HYPOTHESIS,
        "references": {
            "dataset": {"name": dataset.replace("_", "-"), "version": "v1"},
            "universe": {"name": "conformance", "version": "v1"},
            "features": {"name": "momentum", "version": "v1"},
            "model": {"name": "quintile", "version": "v1"},
            "baseline": {"name": "ew-universe", "version": "v1"},
            "cost_model": {"name": "h1-frozen", "version": "v1"},
            "readiness": {"name": "matrix-20260921", "version": "v1"},
        },
        "as_of": as_of,
        "pit": {"availability_rule": "AVAILABLE_AT_LE_DECISION_TIME", "minimum_pit_class": "PIT_RECONSTRUCTED"},
        "parameters": {"target": "NEXT_REBALANCE_RETURN", "fee_bps": FEE_BPS, "slippage_bps": SLIPPAGE_BPS,
                       "max_securities": 100, "external_intelligence": {"mode": "NONE", "families": []}},
        "priority_hint": "NORMAL",
    }
    if dataset == "case_b":
        value["references"]["cost_model"] = {"name": "expensive", "version": "v1"}
        value["parameters"]["fee_bps"], value["parameters"]["slippage_bps"] = 100, 400
    value.update(overrides)
    return value


def collection_request(request_id: str, **overrides) -> dict:
    value = {
        "schema_version": "stocks-research-request/1",
        "request_id": request_id,
        "request_type": "COLLECT_EXTERNAL_INTELLIGENCE",
        "research_id": "stocks:RESEARCH-EI-COLLECTION",
        "hypothesis_id": COLLECTION_HYPOTHESIS,
        "references": {"source": {"name": "vlmo-2026", "version": "v1"},
                       "readiness": {"name": "matrix-20260921", "version": "v1"}},
        "as_of": "2026-09-20T00:00:00Z",
        "pit": {"availability_rule": "AVAILABLE_AT_LE_DECISION_TIME", "minimum_pit_class": "PIT_STRICT"},
        "parameters": {"collector": "cvm-vlmo", "period": "2026", "observed_at": "2026-09-19T12:00:00Z"},
        "priority_hint": "NORMAL",
    }
    value.update(overrides)
    return value


def write_request(env: dict, name: str, value: dict | str) -> Path:
    path = env["requests"] / f"{name}.json"
    path.write_text(value if isinstance(value, str) else json.dumps(value, indent=1), encoding="utf-8")
    return path


def experiments(env: dict) -> Path:
    return env["state"] / EXEC_DIR / EXPERIMENTS_DIR


def ops_runtime(env: dict) -> Path:
    return env["state"] / EXEC_DIR / OPS_DIR


def work_dir(env: dict, logical_hash: str) -> Path:
    return experiment_dir(env["state"] / EXEC_DIR, logical_hash)


def child_environment(**extra: str) -> dict:
    """Environment of the processes under test: no fault unless asked, no coverage plumbing."""
    environment = {key: value for key, value in os.environ.items()
                   if not key.startswith("COV_CORE_") and key not in {"COVERAGE_PROCESS_START", "STOCKS_RESEARCH_FAULT"}}
    environment["PYTHONUTF8"] = "1"
    environment.update(extra)
    return environment


def console_script() -> str:
    """The installed `stocks-research` console script next to the running interpreter."""
    folder = Path(sys.executable).parent
    candidate = folder / ("stocks-research.exe" if os.name == "nt" else "stocks-research")
    found = str(candidate) if candidate.exists() else shutil.which("stocks-research")
    if not found:
        raise RuntimeError("stocks-research console script is not installed")
    return found


def cli(env: dict, *args: str, fault: str | None = None, timeout: float = 900) -> tuple[int, list[dict]]:
    """Run the installed entrypoint in a NEW process; returns (exit code, JSON lines)."""
    command = [console_script(), "--state", str(env["state"]), *args]
    if args and args[0] in {"process", "run"}:
        command[4:4] = ["--policy", str(env["policy"]), "--objects", str(env["objects"])]
    environment = child_environment(**({"STOCKS_RESEARCH_FAULT": fault} if fault else {}))
    completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout, env=environment,
                               cwd=env["root"], encoding="utf-8", errors="replace")
    lines = []
    for line in completed.stdout.splitlines():
        line = line.strip()
        if line.startswith("{"):
            lines.append(json.loads(line))
    if completed.returncode not in (0, 2, 3, 4, 5, 86):
        raise AssertionError(f"unexpected exit {completed.returncode}: {completed.stderr[-3000:]}")
    return completed.returncode, lines
