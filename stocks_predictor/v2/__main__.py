"""Baselines do protocolo v2 sob o TrialLedger.

    python -m stocks_predictor.v2 --config CONFIG.json --dataset DATASET.json --ledger LEDGER.jsonl [--output OUT.json]

``--dataset synthetic`` usa o dataset sintético (demonstração, nunca evidência empírica). A configuração é
explícita e completa — nenhum custo, liquidez ou convenção vem de padrão escondido:

    {"start", "end", "rebalance", "execution": {"lag_sessions", "price"},
     "costs": {todos os campos de CostModel}, "liquidity": {"min_adv", "adv_lookback", "max_participation",
     "statistic"}, "initial_cash", "seed", "allow_short",
     "baselines": {"index_id", "random_positions", "forecast_horizon",
                   "momentum": {"lookback", "skip", "quantile", "max_stale"}}}

Cada baseline é uma execução avaliativa (manifesto + trial no ledger). ``--output`` nunca sobrescreve.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import synthetic
from .baselines import EqualWeightUniverse, ForecastBaselines, IndexBuyAndHold, Momentum12_1, RandomPortfolio
from .costs import CostModel, LiquidityRule
from .dataset import PITDataset
from .engine import ProtocolConfig
from .execution import ExecutionConvention
from .manifest import TrialLedger, run_evaluation, sha256_json

_TOP = {"start", "end", "rebalance", "execution", "costs", "liquidity", "initial_cash", "seed", "allow_short",
        "baselines"}
_BASELINES = {"index_id", "random_positions", "forecast_horizon", "momentum"}
FAMILY = "baselines-protocol-v2"


def load_config(raw: dict) -> tuple[ProtocolConfig, dict]:
    if set(raw) != _TOP or set(raw["baselines"]) != _BASELINES:
        raise ValueError(f"configuração: campos exatos {sorted(_TOP)} e baselines {sorted(_BASELINES)}")
    config = ProtocolConfig(start=raw["start"], end=raw["end"], rebalance=raw["rebalance"],
                            execution=ExecutionConvention(**raw["execution"]), costs=CostModel.from_dict(raw["costs"]),
                            liquidity=LiquidityRule(**raw["liquidity"]), initial_cash=raw["initial_cash"],
                            seed=raw["seed"], allow_short=raw["allow_short"])
    return config, raw["baselines"]


def run(config: ProtocolConfig, baselines: dict, dataset: PITDataset, ledger: TrialLedger,
        git: dict | None = None) -> dict:
    strategies = [EqualWeightUniverse(), IndexBuyAndHold(baselines["index_id"]),
                  Momentum12_1(**baselines["momentum"]), RandomPortfolio(baselines["random_positions"])]
    candidates = [s.name for s in strategies]
    selection = {"family": FAMILY, "candidate_set": candidates, "selection_metric": "NONE (baselines, sem seleção)",
                 "selected_candidate": "NONE"}
    results = {}
    for strategy in strategies:
        out = run_evaluation(ledger, dataset, strategy, config, family=FAMILY, selection=selection, git=git,
                             validation={"scheme": "single_window", "window": [config.start, config.end]})
        net, gross = out["metrics"]["net"], out["metrics"]["gross"]
        results[strategy.name] = {
            "run_id": out["run_id"], "trial_number": out["trial_number"],
            "result_digest": out["metrics"]["result_digest"],
            "net": {k: net[k] for k in ("total_return", "cagr", "ann_vol", "sharpe_ann_rf0", "max_drawdown",
                                        "turnover_ann", "costs_total", "trades_filled", "orders_unfilled")},
            "gross_total_return": gross["total_return"]}
    forecast = ForecastBaselines(baselines["forecast_horizon"])
    out = run_evaluation(ledger, dataset, forecast, config, family=FAMILY, runner=ForecastBaselines.runner,
                         metric="random_walk_mse", primary=ForecastBaselines.primary, git=git,
                         validation={"scheme": "single_window", "horizon": baselines["forecast_horizon"]})
    results[forecast.name] = {"run_id": out["run_id"], "trial_number": out["trial_number"],
                              "result_digest": out["metrics"]["result_digest"],
                              "excluded_pairs": out["metrics"]["excluded_pairs"], "metrics": out["metrics"]["metrics"]}
    return {"dataset": {"hash": dataset.hash, "version": dataset.version, "data_cutoff": dataset.cutoff},
            "config_hash": sha256_json(config.to_dict()), "config": config.to_dict(), "results": results,
            "ledger": {"path": str(ledger.path), "records": len(ledger.records),
                       "head": ledger.records[-1]["hash"] if ledger.records else None}}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m stocks_predictor.v2",
                                     description="Baselines do protocolo v2 sob o TrialLedger.")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.output is not None and args.output.exists():
        parser.error(f"{args.output} já existe: nada é sobrescrito")
    config, baselines = load_config(json.loads(args.config.read_text(encoding="utf-8")))
    raw = synthetic.build() if args.dataset == "synthetic" else json.loads(Path(args.dataset).read_bytes())
    summary = run(config, baselines, PITDataset(raw), TrialLedger(args.ledger))
    text = json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output is not None:
        with args.output.open("x", encoding="utf-8") as handle:
            handle.write(text)
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
