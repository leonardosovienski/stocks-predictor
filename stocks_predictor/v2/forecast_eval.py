"""Execução do Prompt 3c: previsão de séries (baselines + modelo pré-treinado opcional) e carteiras de referência
no protocolo v2, sob o TrialLedger e a política de decisão.

    python -m stocks_predictor.v2.forecast_eval --spec SPEC.json --config PROTOCOLO.json \
        --dataset synthetic|cotahist:ARQUIVO.ZIP --policy POLITICA.json --ledger LEDGER.jsonl \
        [--riskfree RF.json] [--forecasts PREVISOES.json ...] [--output SAIDA.json]

A especificação (versionada, com hash no manifesto) fixa antes de qualquer resultado: horizonte, contexto, níveis,
limiar de salto e sua origem, baseline de comparação, desenho de poder, regra do período e sha256 da fonte.
Sem ``--riskfree``, as métricas em excesso de rf ficam N/A e a política devolve NO_DECISION. Um modelo
pré-treinado só entra via ``--forecasts``, gerado fora com proveniência completa; nada é baixado aqui.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from . import synthetic
from .__main__ import load_config
from .baselines import EqualWeightUniverse, IndexBuyAndHold
from .cotahist_dataset import build_from_cotahist
from .dataset import PITDataset, canonical
from .engine import ProtocolConfig, Strategy
from .forecasting import (EmpiricalRandomWalk, ForecastRankStrategy, GaussianRandomWalk, build_tasks,
                          contamination_status, evaluate_predictions, load_forecasts, predict_all)
from .manifest import TrialLedger, run_evaluation
from .metrics import NetSeries, beta_alpha, strategy_report
from .policy import Policy, decide, load_policy
from .riskfree import RiskFreeSeries
from .validation import PERIODS_PER_YEAR, evaluate_with_series

FAMILY = "forecast-prompt3c"
_SPEC = {"horizon", "context_length", "levels", "jump_threshold", "jump_threshold_source", "baseline", "design",
         "period_rule", "source_sha256", "index_ticker", "rank_quantile"}
_BASELINES = {"gaussian_random_walk": GaussianRandomWalk, "empirical_random_walk": EmpiricalRandomWalk}
NA = "N/A"


class ForecasterRun(Strategy):
    """Identidade de um previsor no manifesto (não gera carteira)."""

    def __init__(self, description: dict):
        self._description = description
        self.name = description["name"]

    def describe(self) -> dict:
        return dict(self._description)

    def targets(self, ctx):
        raise NotImplementedError("previsor não gera carteira")


def load_spec(raw: dict) -> dict:
    if set(raw) != _SPEC or set(raw["design"]) != {"alpha", "power", "min_detectable_relative_improvement"}:
        raise ValueError(f"especificação: campos exatos {sorted(_SPEC)}")
    if raw["baseline"] not in _BASELINES or raw["period_rule"] not in ("full_context_to_end", "config"):
        raise ValueError("baseline ou regra de período desconhecidos")
    if 0.5 not in raw["levels"]:
        raise ValueError("os níveis precisam incluir a mediana (0,5)")
    return raw


def _row(candidate: str, **values) -> dict:
    keys = ("protocol", "period", "universe", "costs", "forecast_metric", "ic_rank_ic", "sharpe_net_excess_rf",
            "max_drawdown", "turnover_ann", "beta", "psr", "dsr_worst", "pbo", "decision", "run_id")
    return {"candidate": candidate} | {k: values.get(k, NA) for k in keys}


def run_forecast_evaluation(dataset: PITDataset, config: ProtocolConfig, spec: dict, policy: Policy,
                            ledger: TrialLedger, *, dataset_meta: dict, rf: RiskFreeSeries | None = None,
                            external: list[dict] | None = None, git: dict | None = None) -> dict:
    cal = dataset.calendar
    if spec["period_rule"] == "full_context_to_end":
        config = config.with_window(cal[spec["context_length"]], cal[-1])
    horizon, levels = spec["horizon"], spec["levels"]
    spec_sha = hashlib.sha256(canonical(spec)).hexdigest()
    tasks, task_stats = build_tasks(dataset, config, horizon=horizon, context_length=spec["context_length"],
                                    jump_threshold=spec["jump_threshold"])
    ppy = PERIODS_PER_YEAR[config.rebalance]
    identity = policy.identity()
    validation = {"scheme": "forecast_origins", "spec_sha256": spec_sha, "tasks": task_stats,
                  "dataset_meta": {k: v for k, v in dataset_meta.items()}, "stage": "prompt3c"}
    period = f"{config.start}..{config.end}"
    universe = ("sem deslistagens conhecidas (limitação da fonte)" if dataset_meta.get("limitations")
                else "com deslistadas (PIT)")
    costs = f"emol {config.costs.exchange_fee_bps} + spread {config.costs.spread_bps} + slip {config.costs.slippage_bps} bps/lado"
    protocol = f"v2 + spec {spec_sha[:12]}"
    predictions = {name: predict_all(cls(), tasks, horizon, levels) for name, cls in _BASELINES.items()}
    baseline = predictions[spec["baseline"]]
    models: dict[str, tuple[dict, dict | None]] = {name: (cls().describe(), None) for name, cls in _BASELINES.items()}
    for raw in external or []:
        preds, meta = load_forecasts(raw, tasks, horizon=horizon, levels=levels)
        name = f"{meta['id']}@{meta['revision'][:12]}"
        predictions[name] = preds
        models[name] = ({"name": name, "kind": "pretrained_zero_shot", "pretrained": True, "model": meta}, meta)
    forecasts, rows, run_ids = {}, [], []
    for name, (description, meta) in models.items():
        preds = predictions[name]
        design = spec["design"]
        full = evaluate_predictions(tasks, preds, levels, baseline=None if preds is baseline else baseline,
                                    design=design, periods_per_year=ppy)
        n_required = (full.get("vs_baseline") or {}).get("n_required")
        contamination = contamination_status(meta, tasks, n_required)
        clean_tasks = tasks if meta is None else [t for t in tasks if t.origin > contamination["cutoff"]]
        clean = full if meta is None else evaluate_predictions(clean_tasks, preds, levels, baseline=baseline,
                                                                design=design, periods_per_year=ppy)
        digest = hashlib.sha256(canonical({"predictions": sorted((k[0], k[1], v) for k, v in preds.items()),
                                           "metrics": full})).hexdigest()
        result = {"all_tasks": full, "clean": clean, "contamination": contamination, "result_digest": digest}
        out = run_evaluation(ledger, dataset, ForecasterRun(description), config, family=FAMILY,
                             runner=lambda _d, _s, _c, result=result: result, metric="crps",
                             primary=lambda r: r["clean"].get("crps") if r["clean"].get("n") else r["all_tasks"]["crps"],
                             git=git, decision_policy=identity, validation=validation)
        run_ids.append(out["run_id"])
        forecasts[name] = result | {"run_id": out["run_id"], "trial_number": out["trial_number"]}
        ic = clean.get("rank_ic")
        rows.append(_row(name, protocol=protocol, period=period, universe=universe, costs="N/A (previsão)",
                         forecast_metric={"crps": clean.get("crps"), "wql_price": clean.get("wql_price"),
                                          "n": clean.get("n"), "contamination": contamination["status"]},
                         ic_rank_ic="N/A (mediana prevista constante no corte transversal)" if not ic else
                         {"ic": (clean.get("ic") or {}).get("mean"), "rank_ic": ic.get("mean"), "n_origins": ic.get("n")},
                         decision="NO_DECISION (previsão não é carteira; política decide carteira)",
                         run_id=out["run_id"]))
    portfolios = {"ew_universe": EqualWeightUniverse(), "index_buy_and_hold": IndexBuyAndHold(dataset_meta["index_isin"])}
    for name, (_description, meta) in models.items():
        if meta is not None:
            portfolios[f"rank:{name}"] = ForecastRankStrategy(f"rank:{name}", predictions[name], levels.index(0.5),
                                                              spec["rank_quantile"])
    series = {}
    for name, strategy in portfolios.items():
        out = run_evaluation(ledger, dataset, strategy, config, family=FAMILY, runner=evaluate_with_series, git=git,
                             decision_policy=identity, validation=validation)
        run_ids.append(out["run_id"])
        m = out["metrics"]
        series[name] = (NetSeries(name, m["sessions"], m["returns"], m["net"]), out["run_id"])
    index_series = series["index_buy_and_hold"][0]
    reports = {}
    for name, (s, run_id) in series.items():
        beta = beta_alpha(s.returns, index_series.returns, config.costs.sessions_per_year)["beta"] \
            if name != "index_buy_and_hold" else 1.0
        report = strategy_report(s, rf, periods=config.costs.sessions_per_year) if rf is not None else None
        reports[name] = report
        evidence = {"dataset_version": dataset.version, "risk_free_series_id": rf.series_id if rf else None,
                    "sessions": len(s.sessions), "strategy": report or {},
                    "baselines": {k: v for k, v in reports.items() if k in ("ew_universe", "index_buy_and_hold")
                                  and v is not None and k != name},
                    "dsr": None, "pbo": None, "t_stat": None}
        decision = decide(evidence, policy)
        ledger.record_decision(decision, [run_id])
        rows.append(_row(name, protocol=protocol, period=period, universe=universe, costs=costs,
                         sharpe_net_excess_rf=report["sharpe_excess_ann"] if report else "N/A (sem série de rf local)",
                         max_drawdown=s.metrics["max_drawdown"], turnover_ann=s.metrics["turnover_ann"], beta=beta,
                         psr=report["psr_vs_zero"] if report else NA,
                         decision=f"{decision['decision']}: " + "; ".join(decision["no_decision_reasons"] or decision["failed"]),
                         run_id=run_id))
    return {"dataset": {"hash": dataset.hash, "version": dataset.version, "data_cutoff": dataset.cutoff,
                        "meta": dataset_meta},
            "config": config.to_dict(), "spec": spec, "spec_sha256": spec_sha, "policy": identity,
            "tasks": task_stats, "forecasts": forecasts,
            "portfolios": {n: {"net": s.metrics, "run_id": r} for n, (s, r) in series.items()},
            "table": rows, "run_ids": run_ids, "n_trials_ledger": len(ledger.started()),
            "ledger": {"records": len(ledger.records), "head": ledger.records[-1]["hash"]}}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m stocks_predictor.v2.forecast_eval",
                                     description="Execução de previsão do protocolo v2 sob o TrialLedger.")
    for flag in ("--spec", "--config", "--policy", "--ledger"):
        parser.add_argument(flag, required=True, type=Path)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--riskfree", type=Path)
    parser.add_argument("--forecasts", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.output is not None and args.output.exists():
        parser.error(f"{args.output} já existe: nada é sobrescrito")
    spec = load_spec(json.loads(args.spec.read_text(encoding="utf-8")))
    config, _unused = load_config(json.loads(args.config.read_text(encoding="utf-8")))
    if args.dataset == "synthetic":
        raw, meta = synthetic.build(), {"source_file": "synthetic", "index_isin": "IDX11", "limitations": []}
    elif args.dataset.startswith("cotahist:"):
        raw, meta = build_from_cotahist(args.dataset.split(":", 1)[1], expected_sha256=spec["source_sha256"],
                                        index_ticker=spec["index_ticker"])
    else:
        parser.error("--dataset: synthetic | cotahist:ARQUIVO.ZIP")
    rf = RiskFreeSeries(json.loads(args.riskfree.read_bytes())) if args.riskfree else None
    external = [json.loads(p.read_bytes()) for p in args.forecasts]
    report = run_forecast_evaluation(PITDataset(raw), config, spec, load_policy(args.policy), TrialLedger(args.ledger),
                                     dataset_meta=meta, rf=rf, external=external)
    text = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output is not None:
        with args.output.open("x", encoding="utf-8") as handle:
            handle.write(text)
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
