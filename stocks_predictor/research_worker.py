"""Closed local worker for admitted stocks research (handler pit_factor_backtest.v1).

The executor, never the request, chooses this module; predictor_ops runs it as a child
process. It consumes operator-materialized references and writes one immutable,
deterministic domain effect plus one Core trial row. No network, trading, dynamic import,
SQL from the request or arbitrary command.

Pipeline (walk-forward on the PIT panel, research_pit):
  PIT universe at each rebalance -> momentum signal (factor.signals, real domain code)
  -> quantile portfolio (portfolio.select_portfolio) -> holding-period return measured
  with data known at as_of -> equal-weight turnover costs (execution) for the strategy
  AND the EW-universe baseline -> excess over the baseline, gross and net.

Core participation (predictor_core, frozen wheel):
  * temporal validation: predictor_core.measurement.replay — every panel record must be
    available at the cutoff (LookaheadError otherwise), rebalance decisions must be
    monotonic and each decision may only use records available at its decision instant;
  * decisions are produced by replay (the handler receives a PastView of rebalances);
  * statistics: bootstrap_ci (stationary blocks) of gross and net excess, max_drawdown;
  * trial identity: predictor_core.contracts.trial_v2 (dataset_fingerprint, TrialRegistryV2).

External Intelligence: a family is consumed only if research_readiness says so (never,
while no family is READY and bound to the model); otherwise the result is NOT_READY and
no trial exists. COLLECTION_ONLY families are recorded as observed-not-consumed.

Exit codes: 0 effect written; 4 temporal integrity violation; 5 contract refusal;
6 reference integrity violation. 4/5/6 write worker-refusal.json and never an effect.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import time
from pathlib import Path

from predictor_core.contracts.trial_v2 import TRIAL_SCHEMA_VERSION, TrialRegistryV2, dataset_fingerprint
from predictor_core.measurement.bootstrap import bootstrap_ci
from predictor_core.measurement.replay import LookaheadError, replay
from predictor_core.measurement.stats import max_drawdown

from . import execution, factor, portfolio
from .research_contract import BACKTEST
from .research_io import atomic_write, strict_json_loads
from .research_pit import DataQualityProblem, Panel, TemporalViolation, rebalance_sessions
from .research_readiness import ReadinessError, classify, consumption_decision

HANDLER = "stocks.handlers.pit_factor_backtest.v1"
EXIT_TEMPORAL = 4
EXIT_REFUSED = 5
EXIT_INTEGRITY = 6
KINDS = ("dataset", "universe", "features", "model", "baseline", "cost_model", "readiness")


class Refusal(ValueError):
    pass


class IntegrityViolation(ValueError):
    pass


def _load(path: Path) -> dict:
    value = strict_json_loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Refusal("materialized reference must be a JSON object")
    return value


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _bps(value: float) -> int:
    return round(value * 10_000)


def temporal_validation(panel: Panel) -> dict:
    """Core replay: every record of the admitted panel was available at the cutoff."""
    # every record is <= as_of iff the latest availability is; one event keeps the Core check
    # linear in the panel size (replay hands a growing PastView to the handler per event)
    latest = max(panel.available) if panel.available else panel.as_of
    try:
        replay((latest,), lambda past: None, key=lambda _e: panel.as_of, available_at=lambda e: e)
    except LookaheadError as exc:
        raise TemporalViolation(f"LookaheadError: {exc}") from exc
    return {
        "method": "predictor_core.measurement.replay",
        "inequality": "available_at <= as_of for every record; each decision uses only records with "
        "available_at <= decision_at; bar available_at >= session close",
        "records": len(panel.available),
        "as_of": panel.as_of,
        "max_available_at": latest,
        "status": "PASS",
    }


def _check_configs(refs: dict, params: dict) -> None:
    model, universe, features, costs = refs["model"], refs["universe"], refs["features"], refs["cost_model"]
    if model.get("handler") != HANDLER:
        raise Refusal("model does not authorize this handler")
    for key in ("top_n", "liquidity_lookback_sessions", "min_history_sessions", "rebalance_every_sessions"):
        if type(universe.get(key)) is not int or universe[key] < 1:
            raise Refusal(f"universe.{key}")
    if features.get("feature") != "MOMENTUM_12_1":
        raise Refusal("features: only MOMENTUM_12_1 is compiled in this handler")
    for key in ("lookback", "skip"):
        if type(features.get(key)) is not int or features[key] < 1:
            raise Refusal(f"features.{key}")
    if not (0 < float(model.get("quantile", 0)) <= 1) or model.get("take") not in ("top", "bottom"):
        raise Refusal("model quantile/take")
    if refs["baseline"].get("method") != "EQUAL_WEIGHT_UNIVERSE":
        raise Refusal("baseline method")
    fee_bps, slip_bps = round(float(costs["b3_fee_pct"]) * 10_000), round(float(costs["spread_slippage_pct"]) * 10_000)
    if (fee_bps, slip_bps) != (params["fee_bps"], params["slippage_bps"]):
        raise Refusal("admitted cost model conflicts with request parameters")


def _not_evaluated(base: dict, state: str, problem: str, extra: dict | None = None) -> dict:
    return base | {
        "result_state": state,
        "scientific_state": "NOT_EVALUATED",
        "economic_state": "NOT_EVALUATED",
        "data_quality": {"ok": state != "INCONCLUSIVE_DATA_QUALITY", "problem": problem},
        "trial": None,
        "metrics": None,
        "costs": None,
        "baseline_comparison": None,
        **(extra or {}),
    }


def walk_forward(panel: Panel, refs: dict, control: dict | None) -> dict:
    universe_cfg, features, model = refs["universe"], refs["features"], refs["model"]
    one_way = execution.one_way_cost(float(refs["cost_model"]["b3_fee_pct"]),
                                     float(refs["cost_model"]["spread_slippage_pct"]))
    warmup = universe_cfg["min_history_sessions"] + universe_cfg["liquidity_lookback_sessions"]
    schedule = rebalance_sessions(panel.calendar, universe_cfg["rebalance_every_sessions"], warmup)
    kind = control["kind"] if control else None
    seed = control["seed"] if control else None

    def decide(past):
        index = past.asof_index
        session = past.latest[1]
        uni = panel.universe(session, universe_cfg)
        members = [m["security_id"] for m in uni["members"]]
        if kind == "UNIVERSE_PERTURBATION" and members:
            rng = random.Random(seed * 1_000_003 + index)
            drop = set(rng.sample(members, int(len(members) * 0.2)))
            members = [m for m in members if m not in drop]
        series = {sid: uni["series"][sid] for sid in members}
        if kind == "FEATURE_ABLATION":
            rng = random.Random(seed * 1_000_003 + index)
            scores = {sid: rng.random() for sid in sorted(series)}
        else:
            scores = factor.signals(series, session, features["lookback"], features["skip"])
        chosen = portfolio.select_portfolio(scores, float(model["quantile"]), take=model["take"])
        return {"session": session, "decision_at": uni["decision_at"], "universe": uni, "members": members,
                "portfolio": sorted(chosen), "scores_hash": hashlib.sha256(
                    json.dumps(sorted(scores.items()), allow_nan=False).encode()).hexdigest(),
                "max_available_used": uni["max_available_used"]}

    points = tuple((s + "T12:00:00Z", s) for s in schedule)
    decisions = replay(points, decide, key=lambda e: e[0])
    # Core check that each decision used only what was available at its instant.
    replay(tuple((d["decision_at"], d["max_available_used"] or d["decision_at"]) for d in decisions),
           lambda past: None, key=lambda e: e[0], available_at=lambda e: e[1])
    if kind == "TEMPORAL_ABLATION":
        lagged = [None] + [d["portfolio"] for d in decisions[:-1]]
        for d, previous in zip(decisions, lagged):
            d["portfolio"] = previous or []

    periods, rebalances = [], []
    prev_port: set = set()
    prev_uni: set = set()
    for k, (d, nxt) in enumerate(zip(decisions, decisions[1:])):
        start, end = d["session"], nxt["session"]
        members = d["members"]
        rets = {}
        for sid in sorted(set(members) | set(d["portfolio"])):
            entry, exit_ = panel.label_close(sid, start), panel.label_close(sid, end)
            if entry is not None and exit_ is not None:
                rets[sid] = exit_ / entry - 1.0
            else:
                rets[sid] = 0.0  # no known price: held as cash (never dropped from the denominator)
        if kind == "SHUFFLED_LABELS" and members:
            rng = random.Random(seed * 1_000_003 + k)
            shuffled = [rets[sid] for sid in members]
            rng.shuffle(shuffled)
            rets.update(zip(members, shuffled))
        port = d["portfolio"]
        rebalances.append({"session": start, "decision_at": d["decision_at"],
                           "universe_identity_hash": d["universe"]["universe_identity_hash"],
                           "universe_size": len(members), "members": members, "portfolio": port,
                           "excluded": d["universe"]["excluded"]})
        if not members or not port:
            prev_port, prev_uni = set(port), set(members)
            continue
        strat_gross = _mean([rets[sid] for sid in port])
        bench_gross = _mean([rets[sid] for sid in members])
        strat_cost = execution.equal_weight_turnover_cost(prev_port, set(port), one_way)
        bench_cost = execution.equal_weight_turnover_cost(prev_uni, set(members), one_way)
        prev_port, prev_uni = set(port), set(members)
        periods.append({"start": start, "end": end, "strat_gross": strat_gross, "bench_gross": bench_gross,
                        "strat_cost": strat_cost, "bench_cost": bench_cost,
                        "strat_net": strat_gross - strat_cost, "bench_net": bench_gross - bench_cost})
    last = decisions[-1]["universe"] if decisions else None
    return {"periods": periods, "rebalances": rebalances, "schedule": list(schedule),
            "last_universe": None if last is None else {k: v for k, v in last.items() if k != "series"}}


def evaluate(request: dict) -> dict:
    expected = {"schema", "experiment_id", "trial_id", "request", "references", "identities",
                "registered_at", "code_version"}
    if set(request) != expected or request["schema"] != "stocks-admitted-backtest/1":
        raise Refusal("invalid closed worker request")
    task = request["request"]
    if task["request_type"] != BACKTEST:
        raise Refusal("handler mismatch")
    for item in request["references"]:
        observed = hashlib.sha256(Path(item["path"]).read_bytes()).hexdigest()
        if observed != request["identities"].get(item["kind"]):
            raise IntegrityViolation(f"reference {item['kind']} changed after materialization")
    refs = {item["kind"]: _load(Path(item["path"])) for item in request["references"]}
    if set(refs) != set(KINDS):
        raise Refusal("exact admitted reference kinds required")
    params = task["parameters"]
    _check_configs(refs, params)
    model = refs["model"]
    control = params.get("negative_control")
    base = {
        "schema": "stocks-domain-effect/1",
        "experiment_id": request["experiment_id"],
        "as_of": task["as_of"],
        "temporal_validation": None,
        "identities": request["identities"],
        "negative_control": control,
        "external_intelligence": None,
    }
    # External Intelligence gate first: data that is not ready never becomes a signal.
    try:
        axes = classify(refs["readiness"], model_bindings=tuple(model.get("external_intelligence_bindings", ())))
    except (ReadinessError, KeyError, TypeError) as exc:
        raise Refusal(f"readiness matrix: {exc}") from exc
    ei = params["external_intelligence"]
    decisions = {family: consumption_decision(axes, family) for family in ei["families"]}
    base["external_intelligence"] = {
        "mode": ei["mode"],
        "families": ei["families"],
        "ready_families": axes["ready_families"],
        "consumed_families": [],
        "consumed_observations": 0,
        "decisions": {f: {"consume": ok, "reason": reason} for f, (ok, reason) in decisions.items()},
        "axes": {f: axes["families"][f]["axes"] for f in ei["families"] if f in axes["families"]},
    }
    if ei["mode"] == "TRIAL_CONSUMPTION":
        refused = {f: reason for f, (ok, reason) in decisions.items() if not ok}
        if refused:
            return _not_evaluated(base, "NOT_READY", "; ".join(f"{f}: {r}" for f, r in sorted(refused.items())))
    minimum = task["pit"]["minimum_pit_class"]
    if model.get("minimum_price_pit_class") == "PIT_STRICT":
        minimum = "PIT_STRICT"
    try:
        panel = Panel(refs["dataset"], as_of=task["as_of"], minimum_pit_class=minimum)
    except DataQualityProblem as exc:
        return _not_evaluated(base, "INCONCLUSIVE_DATA_QUALITY", str(exc))
    if len(panel.securities) > params["max_securities"]:
        raise Refusal("dataset exceeds max_securities")
    base["temporal_validation"] = temporal_validation(panel)  # before any statistic
    try:
        wf = walk_forward(panel, refs, control)
    except DataQualityProblem as exc:
        return _not_evaluated(base, "INCONCLUSIVE_DATA_QUALITY", str(exc))
    except LookaheadError as exc:
        raise TemporalViolation(f"LookaheadError in a decision: {exc}") from exc
    periods = wf["periods"]
    stats_cfg = model["statistics"]
    minimum_sample = int(model["minimum_sample"])
    domain = {"rebalances": wf["rebalances"], "last_universe": wf["last_universe"],
              "panel": {"securities": len(panel.securities), "sessions": len(panel.calendar),
                        "counters": panel.counters, "pit_classes": panel.pit_classes,
                        "dataset_version": panel.dataset_version}}
    if len(periods) < max(minimum_sample, stats_cfg["block_length"]):
        return base | domain | {
            "result_state": "CLOSED_INSUFFICIENT_SAMPLE", "scientific_state": "INSUFFICIENT_SAMPLE",
            "economic_state": "NOT_EVALUATED", "data_quality": {"ok": True}, "trial": None,
            "metrics": {"periods": len(periods), "minimum_sample": minimum_sample},
            "costs": None, "baseline_comparison": None,
        }
    excess_gross = [p["strat_gross"] - p["bench_gross"] for p in periods]
    excess_net = [p["strat_net"] - p["bench_net"] for p in periods]
    ci = {"scheme": stats_cfg["scheme"], "block_length": stats_cfg["block_length"], "n_boot": stats_cfg["n_boot"],
          "confidence": stats_cfg["confidence"], "seed": stats_cfg["seed"]}
    g_lo, g_hi, _ = bootstrap_ci(excess_gross, _mean, **ci)
    n_lo, n_hi, _ = bootstrap_ci(excess_net, _mean, **ci)
    equity, current = [], 1.0
    for p in periods:
        current *= 1.0 + p["strat_net"]
        equity.append(current)
    scientific = "SUPPORTED" if g_lo > 0 else "REFUTED" if g_hi < 0 else "INCONCLUSIVE"
    economic = "WATCH" if scientific == "SUPPORTED" and n_lo > 0 else "NO_EDGE"
    result_state = {
        ("SUPPORTED", "WATCH"): "WATCH_NO_CAPITAL",
        ("SUPPORTED", "NO_EDGE"): "NO_EDGE",
        ("INCONCLUSIVE", "NO_EDGE"): "INCONCLUSIVE",
        ("REFUTED", "NO_EDGE"): "REFUTED",
    }[(scientific, economic)]
    fields = ("kind", "security_id", "at", "available_at", "value")
    dataset_hash = dataset_fingerprint(panel.rows_for_fingerprint, fields=fields).removeprefix("sha256:")
    result_stats = {
        "mean_excess_gross": _mean(excess_gross), "excess_gross_ci_low": g_lo, "excess_gross_ci_high": g_hi,
        "mean_excess_net": _mean(excess_net), "excess_net_ci_low": n_lo, "excess_net_ci_high": n_hi,
    }
    trial = {
        "schema_version": TRIAL_SCHEMA_VERSION,
        "experiment_id": request["experiment_id"],
        "hypothesis_id": task["hypothesis_id"],
        "hypothesis_family": model["hypothesis_family"],
        "trial_id": request["trial_id"],
        "registered_at": request["registered_at"],
        "executed_at": request["registered_at"],
        "seed": ci["seed"],
        "forecast_horizon": f"P{refs['universe']['rebalance_every_sessions']}SESSIONS",
        "data_cutoff": task["as_of"],
        "label_start": periods[0]["start"] + "T00:00:00Z",
        "label_end": periods[-1]["end"] + "T23:59:59Z",
        "dataset_hash": dataset_hash,
        "dataset_version": panel.dataset_version,
        "feature_version": refs["features"]["feature_version"],
        "model_version": model["model_version"],
        "code_version": request["code_version"],
        "params": params,
        "selection_path": model["selection_path"],
        "n_trials_family": 1,
        "n_trials_domain": 1,
        "n_trials_ecosystem": 1,
        "metric": "mean_excess_gross_over_ew_universe",
        "result": result_stats,
        "status": scientific,
        "notes": f"negative control {control['kind']} seed {control['seed']}" if control
        else "qualification probe; no capital permission",
    }
    mean = _mean
    return base | domain | {
        "result_state": result_state,
        "scientific_state": scientific,
        "economic_state": economic,
        "data_quality": {"ok": True},
        "trial": trial,
        "metrics": {
            "periods": len(periods),
            "strategy_gross_bps": _bps(mean([p["strat_gross"] for p in periods])),
            "strategy_net_bps": _bps(mean([p["strat_net"] for p in periods])),
            "baseline_gross_bps": _bps(mean([p["bench_gross"] for p in periods])),
            "baseline_net_bps": _bps(mean([p["bench_net"] for p in periods])),
            "excess_gross_bps": _bps(mean(excess_gross)),
            "excess_net_bps": _bps(mean(excess_net)),
            "excess_gross_ci_bps": [_bps(g_lo), _bps(g_hi)],
            "excess_net_ci_bps": [_bps(n_lo), _bps(n_hi)],
            "ci": ci,
            "strategy_max_drawdown_bps": -_bps(max_drawdown(equity)),
            "hit_rate_excess_net": sum(1 for x in excess_net if x > 0) / len(excess_net),
        },
        "costs": {
            "model": "stocks_predictor.execution.one_way_cost + equal_weight_turnover_cost",
            "b3_fee_bps_per_side": params["fee_bps"],
            "slippage_bps_per_side": params["slippage_bps"],
            "strategy_mean_cost_bps": _bps(mean([p["strat_cost"] for p in periods])),
            "baseline_mean_cost_bps": _bps(mean([p["bench_cost"] for p in periods])),
        },
        "baseline_comparison": {
            "baseline_id": refs["baseline"]["baseline_id"],
            "method": "EQUAL_WEIGHT_UNIVERSE",
            "outcome": "BEATS" if mean(excess_net) > 0 else "LOSES" if mean(excess_net) < 0 else "TIES",
        },
    }


def _refuse(path: Path, code: int, error: Exception) -> int:
    atomic_write(path, json.dumps({"exit_code": code, "kind": type(error).__name__,
                                   "reason": str(error)[:1000]}, sort_keys=True).encode())
    return code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--effect", type=Path, required=True)
    parser.add_argument("--trial-registry", type=Path, required=True)
    parser.add_argument("--fault", choices=("crash", "hang", "slow", "partial"))
    args = parser.parse_args(argv)
    if args.fault == "crash":
        os._exit(97)
    if args.fault == "hang":
        time.sleep(600)
    if args.fault == "slow":
        time.sleep(8)  # qualification: keeps the job running while the host process is killed
    refusal = args.effect.with_name("worker-refusal.json")
    try:
        effect = evaluate(_load(args.request))
    except TemporalViolation as exc:
        return _refuse(refusal, EXIT_TEMPORAL, exc)
    except IntegrityViolation as exc:
        return _refuse(refusal, EXIT_INTEGRITY, exc)
    except Refusal as exc:
        return _refuse(refusal, EXIT_REFUSED, exc)
    raw = (json.dumps(effect, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
    if args.fault == "partial":
        # qualification: the worker dies mid-write; only a temporary sibling is left behind
        partial = args.effect.with_name(f".{args.effect.name}.partial.tmp")
        partial.write_bytes(raw[: len(raw) // 2])
        os._exit(98)
    if effect["trial"] is not None:
        registry = TrialRegistryV2(args.trial_registry)
        existing = next((row for row in registry.load() if row["trial_id"] == effect["trial"]["trial_id"]), None)
        if existing is None:
            registry.register(effect["trial"])
        elif existing != effect["trial"]:
            raise ValueError("existing trial identity conflicts")
    expected = hashlib.sha256(raw).hexdigest()
    if args.effect.exists():
        if hashlib.sha256(args.effect.read_bytes()).hexdigest() != expected:
            raise ValueError("existing domain effect conflicts")
        return 0
    atomic_write(args.effect, raw)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
