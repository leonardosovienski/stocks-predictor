"""Validação estatística do protocolo v2 sob o TrialLedger.

    python -m stocks_predictor.v2.validation --config PROTOCOLO.json --validation VALIDACAO.json \
        --dataset DATASET.json|synthetic --riskfree RF.json|synthetic --policy POLITICA.json \
        --ledger LEDGER.jsonl [--hypothesis-id ID] [--output SAIDA.json]

Todas as etapas usam o mesmo dataset, janela, custos e convenção de execução:

1. Baselines exigidos pela política, cada um uma execução no ledger.
2. Família de configurações declarada **antes**, com o candidato pré-declarado dentro dela: uma execução por
   configuração. Nada é escolhido pelo resultado.
3. Relatório em excesso da taxa livre de risco; beta/alpha do candidato contra o índice.
4. Cross-section do candidato: IC, Rank IC, ICIR, decaimento e quantis; t do long-short como diagnóstico
   (Harvey, Liu & Zhu).
5. CPCV do procedimento "escolher no treino a configuração de melhor long-short e aplicá-la no teste". Purge pelo
   intervalo real do rótulo; embargo derivado da autocorrelação do Rank IC do candidato.
6. DSR na grade de N (prior da política + todas as execuções do ledger); PBO por CSCV na matriz de excesso
   diário da família.
7. Decisão da política, registrada no ledger com versão e sha256.

Com ``--hypothesis-id``, cada configuração da família é uma variante da hipótese: o ledger exige o pré-registro e
recusa variantes além de ``max_variants``. Hipótese nova só é avaliada assim.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import median

from predictor_core.measurement.trials import DeflationNotEstimableError

from . import synthetic
from .config import load_config
from .baselines import EqualWeightUniverse, IndexBuyAndHold, Momentum12_1
from .costs import CostModel
from .cpcv import derive_purge_embargo, label_samples, run_cpcv
from .dataset import PITDataset
from .engine import ProtocolConfig, Strategy, run_backtest
from .factor_metrics import cross_section
from .manifest import TrialLedger, run_evaluation
from .metrics import NetSeries, dsr_sensitivity, n_trials_grid, sharpe_per_period, strategy_report
from .pbo import pbo_cscv, sharpe_or_mean
from .policy import Policy, decide, load_policy
from .riskfree import RiskFreeSeries, excess_returns

BASELINE_FAMILY = "baselines-protocol-v2"
PERIODS_PER_YEAR = {"weekly": 52, "monthly": 12, "quarterly": 4}
_SPEC = {"index_id", "candidate", "family", "family_name", "horizons", "n_quantiles"}


def evaluate_with_series(dataset: PITDataset, strategy: Strategy, config: ProtocolConfig) -> dict:
    """Líquido (com a série diária) e bruto (mesma estratégia com custo zero), mais o digest reprodutível."""
    net = run_backtest(dataset, strategy, config)
    gross = run_backtest(dataset, strategy, config.with_costs(CostModel.zero()))
    return {"net": net.metrics, "gross": gross.metrics, "result_digest": net.digest, "sessions": net.sessions,
            "returns": net.returns, "cost_drag_total_return": gross.metrics["total_return"] - net.metrics["total_return"]}


def load_spec(raw: dict) -> dict:
    if set(raw) != _SPEC:
        raise ValueError(f"validação: campos exatos {sorted(_SPEC)}")
    names = [Momentum12_1(**params).name for params in raw["family"]]
    if len(set(names)) != len(names) or len(names) < 2:
        raise ValueError("família com >= 2 configurações distintas")
    if Momentum12_1(**raw["candidate"]).name not in names:
        raise ValueError("o candidato pré-declarado precisa pertencer à família")
    if not raw["horizons"] or raw["n_quantiles"] < 2:
        raise ValueError("horizontes e >= 2 quantis")
    return raw


def run_validation(dataset: PITDataset, config: ProtocolConfig, rf: RiskFreeSeries, policy: Policy,
                   ledger: TrialLedger, spec: dict, *, git: dict | None = None,
                   hypothesis_id: str | None = None) -> dict:
    identity = policy.identity()
    run_ids: list[str] = []
    periods = config.costs.sessions_per_year

    def ledgered(strategy: Strategy, family: str, candidates: list[str]) -> NetSeries:
        selection = {"family": family, "candidate_set": candidates,
                     "selection_metric": "NONE (pré-declarado, sem seleção pelo resultado)",
                     "selected_candidate": Momentum12_1(**spec["candidate"]).name if family == spec["family_name"]
                     else "NONE"}
        out = run_evaluation(ledger, dataset, strategy, config, family=family, runner=evaluate_with_series,
                             selection=selection, git=git, decision_policy=identity,
                             validation={"scheme": "single_window", "window": [config.start, config.end],
                                         "stage": "prompt3b", "risk_free": rf.to_dict()},
                             hypothesis_id=hypothesis_id if family == spec["family_name"] else None)
        run_ids.append(out["run_id"])
        m = out["metrics"]
        return NetSeries(strategy.name, m["sessions"], m["returns"], m["net"])

    required = policy.section("baselines")["required"]
    known = {"ew_universe": EqualWeightUniverse(), "index_buy_and_hold": IndexBuyAndHold(spec["index_id"])}
    baselines = {name: ledgered(known[name], BASELINE_FAMILY, required) for name in required}
    family = [Momentum12_1(**params) for params in spec["family"]]
    names = [m.name for m in family]
    series = {m.name: ledgered(m, spec["family_name"], names) for m in family}
    candidate = Momentum12_1(**spec["candidate"])
    index = baselines.get("index_buy_and_hold")
    reports = {name: strategy_report(s, rf, periods=periods) for name, s in baselines.items()}
    candidate_report = strategy_report(series[candidate.name], rf, periods=periods, benchmark=index)

    horizons = spec["horizons"]
    ppy = PERIODS_PER_YEAR[config.rebalance]
    cs = cross_section(dataset, config, candidate.scores, horizons, n_quantiles=spec["n_quantiles"],
                       periods_per_year=ppy)
    main = horizons[0]
    variant_ls = {m.name: {p["signal_session"]: p.get("long_short") for p in
                           cross_section(dataset, config, m.scores, [main], n_quantiles=spec["n_quantiles"],
                                         periods_per_year=ppy)["periods"]} for m in family}
    aligned = [p for p in cs["periods"] if p["rank_ic"][main] is not None
               and all(variant_ls[n].get(p["signal_session"]) is not None for n in names)]
    signals = [dataset.position(p["signal_session"]) for p in aligned]
    lag = config.execution.lag_sessions
    cpcv_rules = policy.section("cpcv")
    cpcv = None
    sizes = None
    if len(aligned) >= max(cpcv_rules["n_groups"], 3):
        step = int(median(b - a for a, b in zip(signals, signals[1:])))
        sizes = derive_purge_embargo(main, lag, step, [p["rank_ic"][main] for p in aligned], z=cpcv_rules["z"],
                                     max_lag=min(cpcv_rules["max_lag"], len(aligned) - 1))
        outcomes = {n: [variant_ls[n][p["signal_session"]] for p in aligned] for n in names}

        def best_on_train(train: list[int], test: list[int]) -> dict[int, float]:
            scored = {n: sharpe_or_mean([outcomes[n][i] for i in train]) if train else float("-inf") for n in names}
            chosen = max(names, key=lambda n: (scored[n], -names.index(n)))
            return {i: outcomes[chosen][i] for i in test}

        cpcv = run_cpcv(label_samples(signals, lag, main), cpcv_rules["n_groups"], cpcv_rules["k_test"],
                        embargo=sizes["embargo_size"], fit_predict=best_on_train, performance=sharpe_or_mean)

    dsr_rules = policy.section("dsr")
    excess = {n: excess_returns(s.sessions, s.returns, rf) for n, s in series.items()}
    n_known = dsr_rules["n_prior_lower_bound"] + len(ledger.started())
    grid = n_trials_grid(n_known, dsr_rules["n_multipliers"], max(dsr_rules["n_upper"], n_known))
    try:
        dsr = dsr_sensitivity(excess[candidate.name], [sharpe_per_period(x) for x in excess.values()], grid)
    except DeflationNotEstimableError as exc:
        dsr = None
        dsr_error = str(exc)
    else:
        dsr_error = None
    matrix = [list(row) for row in zip(*(excess[n] for n in names))]
    try:
        pbo = pbo_cscv(matrix, policy.section("pbo")["n_splits"])
    except ValueError as exc:
        pbo, pbo_error = None, str(exc)
    else:
        pbo_error = None
    evidence = {
        "dataset_version": dataset.version, "risk_free_series_id": rf.series_id,
        "sessions": len(series[candidate.name].sessions), "strategy": candidate_report, "baselines": reports,
        "dsr": dsr, "pbo": pbo, "t_stat": cs["long_short"]["t"],
    }
    decision = decide(evidence, policy)
    ledger.record_decision(decision, run_ids)
    return {
        "dataset": {"hash": dataset.hash, "version": dataset.version, "data_cutoff": dataset.cutoff},
        "risk_free": rf.to_dict(), "policy": identity, "config": config.to_dict(),
        "candidate": candidate.describe(), "family": [m.describe() for m in family],
        "baselines": reports, "candidate_report": candidate_report,
        "family_sharpe_excess_ann": {n: strategy_report(s, rf, periods=periods)["sharpe_excess_ann"]
                                     for n, s in series.items()},
        "cross_section": {k: v for k, v in cs.items() if k != "periods"} | {"n_periods": len(cs["periods"])},
        "purge_embargo": sizes, "cpcv": cpcv,
        "n_trials": {"prior_lower_bound": dsr_rules["n_prior_lower_bound"], "ledger_started": len(ledger.started()),
                     "grid": grid},
        "dsr": dsr, "dsr_error": dsr_error, "pbo": None if pbo is None else {k: v for k, v in pbo.items()
                                                                           if k not in ("logits", "selected")},
        "pbo_error": pbo_error, "decision": decision, "run_ids": run_ids,
        "ledger": {"records": len(ledger.records), "head": ledger.records[-1]["hash"]},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m stocks_predictor.v2.validation",
                                     description="Validação estatística do protocolo v2 sob o TrialLedger.")
    for flag in ("--config", "--validation", "--policy", "--ledger"):
        parser.add_argument(flag, required=True, type=Path)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--riskfree", required=True)
    parser.add_argument("--hypothesis-id", help="hipótese pré-registrada no ledger (família = variantes)")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.output is not None and args.output.exists():
        parser.error(f"{args.output} já existe: nada é sobrescrito")
    config, _baselines = load_config(json.loads(args.config.read_text(encoding="utf-8")))
    spec = load_spec(json.loads(args.validation.read_text(encoding="utf-8")))
    raw = synthetic.build() if args.dataset == "synthetic" else json.loads(Path(args.dataset).read_bytes())
    rf_raw = synthetic.riskfree() if args.riskfree == "synthetic" else json.loads(Path(args.riskfree).read_bytes())
    report = run_validation(PITDataset(raw), config, RiskFreeSeries(rf_raw), load_policy(args.policy),
                            TrialLedger(args.ledger), spec, hypothesis_id=args.hypothesis_id)
    text = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output is not None:
        with args.output.open("x", encoding="utf-8") as handle:
            handle.write(text)
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
