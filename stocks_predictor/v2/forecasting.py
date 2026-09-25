"""Avaliação de previsão de séries no protocolo v2.

Tarefa (papel, origem D), para cada sinal agendado D da janela e cada papel do universo PIT da decisão:

- contexto: os últimos ``context_length`` fechamentos ajustados conhecidos na ``PITView`` da decisão, em pregões
  consecutivos do calendário, sem lacuna;
- alvo da previsão: log(fechamento(D+h)/fechamento(D)), realizado e ajustado pelos eventos realizados no caminho;
- alvo do ranking: retorno desde o preço de execução em D+lag (``forward_return``), o mesmo do cross-section.

Janelas com algum retorno diário |r| acima do limiar, no contexto ou no caminho do alvo, são excluídas e contadas.
O limiar é o do detector congelado do legado (``config.yaml``, ``jump_detector.threshold_abs`` = 0,30): dado sem
evento societário ajustado não pode virar erro de previsão.

Previsores devolvem quantis do log-retorno em h pregões:
    gaussian_random_walk   N(0, σ̂·√h), com σ̂ o desvio dos log-retornos diários do contexto
    empirical_random_walk  quantis empíricos (tipo 7) dos log-retornos de h pregões do contexto, centrados na mediana
    arquivo externo        ``stocks-forecasts/1``: previsões de um modelo pré-treinado geradas fora (ex.: Chronos
                           num ambiente isolado), com proveniência obrigatória

Contaminação: o corte é a data mais recente entre o commit dos pesos e a publicação. Só tarefas com origem depois do
corte são evidência limpa. Poder: n necessário para detectar a melhora relativa mínima de CRPS contra o baseline num
teste pareado bilateral, com o desvio observado das diferenças. Supõe independência entre tarefas, o que é otimista
no corte transversal.
"""

from __future__ import annotations

import hashlib
import math
from collections import Counter
from dataclasses import dataclass
from statistics import NormalDist, median, stdev

from .baselines import forward_return
from .dataset import PITDataset, canonical
from .engine import DecisionContext, ProtocolConfig, Strategy, decision_universe, rebalance_signals
from .factor_metrics import pearson, spearman, summarize
from .forecast_metrics import coverage, crps_each, wql

FORECAST_SCHEMA = "stocks-forecasts/1"
TASKS_SCHEMA = "stocks-forecast-tasks/1"
MODEL_FIELDS = {"id", "revision", "weights_sha256", "license", "license_verified_at", "weights_committed_at",
                "published_at", "source", "library", "library_version"}


@dataclass(frozen=True)
class Task:
    security_id: str
    origin: str
    origin_index: int
    context: tuple[float, ...]
    target_log_return: float
    target_exec_return: float

    @property
    def key(self) -> tuple[str, str]:
        return self.security_id, self.origin


def build_tasks(dataset: PITDataset, config: ProtocolConfig, *, horizon: int, context_length: int,
                jump_threshold: float) -> tuple[list[Task], dict]:
    if horizon < 1 or context_length < 2 or not 0 < jump_threshold:
        raise ValueError("horizon >= 1, context_length >= 2, limiar > 0")
    cal = dataset.calendar
    first, last = dataset.position(config.start), dataset.position(config.end)
    lag = config.execution.lag_sessions
    tasks, excluded, origins = [], Counter(), 0
    for signal in rebalance_signals(cal, first - 1, last - lag - horizon, config.rebalance):
        view = dataset.view(cal[signal + 1])
        universe = decision_universe(view, config.liquidity)
        if signal - context_length + 1 < 0:
            excluded["short_history"] += len(universe)
            continue
        origins += 1
        window = list(cal[signal - context_length + 1: signal + 1])
        for sid in universe:
            sessions, _opens, closes, _volumes = view.history(sid)
            if sessions[-context_length:] != window:
                excluded["context_gap"] += 1
                continue
            context = closes[-context_length:]
            if any(abs(b / a - 1) > jump_threshold for a, b in zip(context, context[1:])):
                excluded["jump_context"] += 1
                continue
            reason, previous, factor = None, context[-1], 1.0
            for i in range(signal + 1, signal + horizon + 1):
                for multiplier in dataset.realized_actions(sid, cal[i]):
                    factor *= multiplier
                bar = dataset.realized_bar(sid, cal[i])
                if bar is None:
                    reason = "target_gap"
                    break
                adjusted = bar.close * factor
                if abs(adjusted / previous - 1) > jump_threshold:
                    reason = "jump_target"
                    break
                previous = adjusted
            if reason:
                excluded[reason] += 1
                continue
            realized = forward_return(dataset, sid, signal + lag, horizon, config.execution.price)
            if realized is None:
                excluded["no_execution_target"] += 1
                continue
            tasks.append(Task(sid, cal[signal], signal, tuple(context), math.log(previous / context[-1]), realized))
    return tasks, {"tasks": len(tasks), "origins": origins, "excluded": dict(sorted(excluded.items())),
                   "horizon": horizon, "context_length": context_length, "jump_threshold": jump_threshold}


def _quantile(ordered: list[float], p: float) -> float:
    """Quantil tipo 7 (interpolação linear) de uma lista ordenada."""
    position = (len(ordered) - 1) * p
    low = math.floor(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


class GaussianRandomWalk:
    name = "gaussian_random_walk"

    def predict(self, context: tuple[float, ...], horizon: int, levels: list[float]) -> list[float]:
        returns = [math.log(b / a) for a, b in zip(context, context[1:])]
        sd = stdev(returns) if len(returns) > 1 else 0.0
        return [sd * math.sqrt(horizon) * NormalDist().inv_cdf(t) for t in levels]

    def describe(self) -> dict:
        return {"name": self.name, "kind": "baseline", "pretrained": False}


class EmpiricalRandomWalk:
    name = "empirical_random_walk"

    def predict(self, context: tuple[float, ...], horizon: int, levels: list[float]) -> list[float]:
        returns = [math.log(context[i + horizon] / context[i]) for i in range(len(context) - horizon)]
        if len(returns) < 2:
            raise ValueError("contexto curto demais para o baseline empírico")
        center = median(returns)
        ordered = sorted(r - center for r in returns)
        return [_quantile(ordered, t) for t in levels]

    def describe(self) -> dict:
        return {"name": self.name, "kind": "baseline", "pretrained": False}


def predict_all(forecaster, tasks: list[Task], horizon: int, levels: list[float]) -> dict[tuple[str, str], list[float]]:
    return {t.key: forecaster.predict(t.context, horizon, levels) for t in tasks}


def tasks_sha256(tasks: list[Task]) -> str:
    """Identidade das tarefas exatas (papel, origem, contexto) que um modelo externo recebeu."""
    return hashlib.sha256(canonical([{"security_id": t.security_id, "origin_session": t.origin,
                                      "context": list(t.context)} for t in tasks])).hexdigest()


def tasks_payload(tasks: list[Task], *, horizon: int, levels: list[float], dataset_hash: str, spec_sha256: str) -> dict:
    """Arquivo ``stocks-forecast-tasks/1`` entregue ao ambiente isolado do modelo externo."""
    return {"schema": TASKS_SCHEMA, "horizon": horizon, "levels": levels, "dataset_hash": dataset_hash,
            "spec_sha256": spec_sha256, "tasks_sha256": tasks_sha256(tasks),
            "tasks": [{"security_id": t.security_id, "origin_session": t.origin, "context": list(t.context)}
                      for t in tasks]}


def load_forecasts(raw: dict, tasks: list[Task], *, horizon: int, levels: list[float]) -> tuple[dict, dict]:
    """Previsões externas com proveniência, amarradas às tarefas exatas (``tasks_sha256``). Toda tarefa precisa
    de previsão; nada a mais nem a menos."""
    if type(raw) is not dict or raw.get("schema") != FORECAST_SCHEMA:
        raise ValueError(f"arquivo de previsões não é {FORECAST_SCHEMA}")
    model = raw.get("model")
    if type(model) is not dict or set(model) != MODEL_FIELDS or any(not model[k] for k in MODEL_FIELDS):
        raise ValueError(f"proveniência do modelo: campos exatos {sorted(MODEL_FIELDS)}")
    if raw.get("horizon") != horizon or raw.get("levels") != levels:
        raise ValueError("horizonte ou níveis diferentes do protocolo")
    if raw.get("tasks_sha256") != tasks_sha256(tasks):
        raise ValueError("previsões geradas para outras tarefas (tasks_sha256 diferente)")
    predictions = {}
    for entry in raw.get("entries", []):
        key = (entry["security_id"], entry["origin_session"])
        if key in predictions:
            raise ValueError(f"previsão duplicada {key}")
        predictions[key] = [float(v) for v in entry["quantiles"]]
    expected = {t.key for t in tasks}
    if set(predictions) != expected:
        raise ValueError(f"previsões ≠ tarefas: faltam {len(expected - set(predictions))}, "
                         f"sobram {len(set(predictions) - expected)}")
    return predictions, model | {"forecasts_sha256": hashlib.sha256(canonical(raw)).hexdigest()}


def evaluate_predictions(tasks: list[Task], predictions: dict, levels: list[float], *,
                         baseline: dict | None = None, design: dict | None = None,
                         periods_per_year: float = 12.0) -> dict:
    """CRPS (log-retorno), WQL (nível de preço), cobertura 80%, IC/Rank IC da mediana contra o retorno desde a
    execução e, contra ``baseline``, a diferença pareada de CRPS e o n necessário para o poder pedido."""
    if not tasks:
        return {"n": 0}
    targets = [t.target_log_return for t in tasks]
    quantiles = [predictions[t.key] for t in tasks]
    crps = crps_each(targets, quantiles, levels)
    prices = [t.context[-1] * math.exp(y) for t, y in zip(tasks, targets)]
    price_q = [[t.context[-1] * math.exp(q) for q in row] for t, row in zip(tasks, quantiles)]
    report = {"n": len(tasks), "origins": len({t.origin for t in tasks}), "crps": sum(crps) / len(crps),
              "wql_price": wql(prices, price_q, levels)}
    if 0.1 in levels and 0.9 in levels:
        lo, hi = levels.index(0.1), levels.index(0.9)
        report["coverage_80"] = coverage(targets, [r[lo] for r in quantiles], [r[hi] for r in quantiles])
    if 0.5 in levels:
        mid = levels.index(0.5)
        ics, rank_ics = [], []
        for origin in sorted({t.origin for t in tasks}):
            group = [t for t in tasks if t.origin == origin]
            forecast = [predictions[t.key][mid] for t in group]
            realized = [t.target_exec_return for t in group]
            ic, ric = pearson(forecast, realized), spearman(forecast, realized)
            if ic is not None:
                ics.append(ic)
            if ric is not None:
                rank_ics.append(ric)
        report["ic"] = summarize(ics, periods_per_year) if ics else None
        report["rank_ic"] = summarize(rank_ics, periods_per_year) if rank_ics else None
    if baseline is not None:
        base = crps_each(targets, [baseline[t.key] for t in tasks], levels)
        diffs = [a - b for a, b in zip(crps, base)]
        mean_base = sum(base) / len(base)
        mean_d = sum(diffs) / len(diffs)
        sd_d = stdev(diffs) if len(diffs) > 1 else 0.0
        paired = {"baseline_crps": mean_base, "mean_diff": mean_d, "sd_diff": sd_d,
                  "t": mean_d / (sd_d / math.sqrt(len(diffs))) if sd_d > 0 else None,
                  "relative_improvement": 1 - report["crps"] / mean_base if mean_base > 0 else None}
        if design is not None and sd_d > 0 and mean_base > 0:
            z = NormalDist().inv_cdf(1 - design["alpha"] / 2) + NormalDist().inv_cdf(design["power"])
            delta = design["min_detectable_relative_improvement"] * mean_base
            paired["n_required"] = math.ceil((z * sd_d / delta) ** 2)
        report["vs_baseline"] = paired
    return report


def contamination_status(model: dict | None, tasks: list[Task], n_required: int | None) -> dict:
    """Modelos sem pré-treino: NOT_APPLICABLE. Pré-treinados: só origens depois do corte contam."""
    if model is None:
        return {"status": "NOT_APPLICABLE", "reason": "baseline sem pré-treino"}
    cutoff = max(model["weights_committed_at"][:10], model["published_at"][:10])
    post = [t for t in tasks if t.origin > cutoff]
    if not post:
        status = "POTENTIALLY_CONTAMINATED"
    elif n_required is None or len(post) < n_required:
        status = "INSUFFICIENT_SAMPLE"
    else:
        status = "CLEAN_POST_CUTOFF"
    return {"status": status, "cutoff": cutoff, "tasks_post_cutoff": len(post), "tasks_total": len(tasks),
            "n_required": n_required}


class ForecastRankStrategy(Strategy):
    """Carteira long-only EW no quantil superior da mediana prevista (as previsões vêm prontas por (papel, origem))."""

    def __init__(self, name: str, predictions: dict, median_index: int, quantile: float = 0.2):
        self.name, self._predictions, self._mid, self.quantile = name, predictions, median_index, quantile

    def describe(self) -> dict:
        return {"name": self.name, "kind": "forecast_rank", "quantile": self.quantile}

    def targets(self, ctx: DecisionContext) -> dict[str, float]:
        scored = {sid: self._predictions[(sid, ctx.signal_session)][self._mid] for sid in ctx.universe
                  if (sid, ctx.signal_session) in self._predictions}
        if len(set(scored.values())) < 2:
            return {}
        ranked = sorted(scored, key=lambda sid: (-scored[sid], sid))
        top = ranked[: max(1, math.ceil(len(ranked) * self.quantile))]
        return {sid: 1 / len(top) for sid in top}


__all__ = ["EmpiricalRandomWalk", "FORECAST_SCHEMA", "ForecastRankStrategy", "GaussianRandomWalk", "MODEL_FIELDS",
           "TASKS_SCHEMA", "Task", "build_tasks", "contamination_status", "evaluate_predictions", "load_forecasts",
           "predict_all", "tasks_payload", "tasks_sha256"]
