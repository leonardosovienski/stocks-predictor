"""Métricas de estratégia em excesso da taxa livre de risco, líquidas de custos.

Referências (a fórmula está no docstring de cada função):
- Sharpe do retorno em excesso: Sharpe (1994), "The Sharpe Ratio", Journal of Portfolio Management 21(1).
- PSR: Bailey & López de Prado (2012), "The Sharpe Ratio Efficient Frontier", Journal of Risk 15(2). Sobre
  séries, usa o contrato do core ``predictor_core.measurement.stats.probabilistic_sharpe_ratio``.
- DSR: Bailey & López de Prado (2014), "The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest
  Overfitting and Non-Normality", Journal of Portfolio Management 40(5). E[max SR] vem do core
  (``predictor_core.measurement.trials.expected_max_sharpe``).
- Limiar t > 3 para fator novo: Harvey, Liu & Zhu (2016), "... and the Cross-Section of Expected Returns",
  Review of Financial Studies 29(1).
- beta/alpha: regressão CAPM (MQO) do excesso da estratégia sobre o excesso do índice de referência.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import NormalDist, variance

from predictor_core.measurement.stats import probabilistic_sharpe_ratio
from predictor_core.measurement.trials import DeflationNotEstimableError, expected_max_sharpe

from .engine import BacktestResult
from .riskfree import RiskFreeSeries, excess_returns


def moments(xs: list[float]) -> tuple[int, float, float, float, float]:
    """(n, média, desvio populacional, assimetria γ3, curtose γ4 — não o excesso), como o PSR do core."""
    n = len(xs)
    mean = sum(xs) / n
    m2 = sum((x - mean) ** 2 for x in xs) / n
    if m2 == 0:
        return n, mean, 0.0, 0.0, 3.0
    m3 = sum((x - mean) ** 3 for x in xs) / n
    m4 = sum((x - mean) ** 4 for x in xs) / n
    return n, mean, math.sqrt(m2), m3 / m2 ** 1.5, m4 / m2 ** 2


def sharpe_per_period(xs: list[float]) -> float | None:
    """média / desvio amostral (n − 1); ``None`` sem dispersão."""
    if len(xs) < 2:
        return None
    mean = sum(xs) / len(xs)
    sd = math.sqrt(sum((x - mean) ** 2 for x in xs) / (len(xs) - 1))
    return mean / sd if sd > 0 else None


def psr_from_moments(sr: float, n: int, skew: float, kurt: float, benchmark: float = 0.0) -> float:
    """PSR(SR*) = Φ[(SR − SR*)·√(n − 1) / √(1 − γ3·SR + (γ4 − 1)/4·SR²)] — Bailey & López de Prado (2012).

    SR e SR* por período; γ4 é a curtose (normal = 3). Mesma fórmula do core, a partir dos momentos (serve para
    conferir exemplos publicados que só informam momentos).
    """
    denominator = 1 - skew * sr + (kurt - 1) / 4 * sr * sr
    if n < 2 or denominator <= 0:
        raise ValueError("PSR indefinido: n < 2 ou variância do estimador não positiva")
    return NormalDist().cdf((sr - benchmark) * math.sqrt(n - 1) / math.sqrt(denominator))


def t_stat(xs: list[float]) -> float | None:
    """t = média / (desvio amostral / √n). Supõe independência; com sobreposição de janelas, superestima."""
    sr = sharpe_per_period(xs)
    return None if sr is None else sr * math.sqrt(len(xs))


def beta_alpha(strategy: list[float], benchmark: list[float], periods_per_year: int) -> dict:
    """MQO: y = α + β·x. β = cov(x, y)/var(x); α por período = ȳ − β·x̄; α anualizado = α × períodos/ano."""
    n = len(strategy)
    if n != len(benchmark) or n < 3:
        raise ValueError("séries alinhadas com n >= 3")
    mx, my = sum(benchmark) / n, sum(strategy) / n
    sxx = sum((x - mx) ** 2 for x in benchmark)
    if sxx == 0:
        raise ValueError("índice sem variância")
    sxy = sum((x - mx) * (y - my) for x, y in zip(benchmark, strategy))
    syy = sum((y - my) ** 2 for y in strategy)
    beta = sxy / sxx
    alpha = my - beta * mx
    return {"beta": beta, "alpha_per_period": alpha, "alpha_ann": alpha * periods_per_year,
            "r2": sxy * sxy / (sxx * syy) if syy > 0 else None, "n": n}


def n_trials_grid(n_lower_bound: int, multipliers: list[int], n_upper: int | None) -> list[int]:
    """N, 2N, 5N… sobre o limite inferior conhecido, mais o N_upper declarado."""
    if n_lower_bound < 1 or not multipliers or any(m < 1 for m in multipliers):
        raise ValueError("N >= 1 e multiplicadores >= 1")
    grid = {n_lower_bound * m for m in multipliers}
    if n_upper is not None:
        grid.add(n_upper)
    return sorted(grid)


def dsr_sensitivity(excess: list[float], trial_sharpes: list[float | None], n_values: list[int]) -> dict:
    """DSR para cada N: PSR(SR0), SR0 = E[max SR] = √V[SR]·((1 − γ)·Φ⁻¹(1 − 1/N) + γ·Φ⁻¹(1 − 1/(N·e))).

    ``trial_sharpes``: Sharpe por período das tentativas conhecidas (V[SR] só com as numéricas). O pior caso é
    o menor DSR da grade — a decisão usa esse. Menos de duas numéricas: ``DeflationNotEstimableError``.
    """
    finite = [s for s in trial_sharpes if s is not None and math.isfinite(s)]
    if len(finite) < 2:
        raise DeflationNotEstimableError(f"V[SR] exige >= 2 Sharpes de tentativas; há {len(finite)}")
    var = variance(finite)
    rows = []
    for n in sorted(set(n_values)):
        sr0 = expected_max_sharpe(n, var)
        rows.append({"n": n, "sr0": sr0, "dsr": probabilistic_sharpe_ratio(excess, benchmark_sharpe=sr0)})
    return {"var_trial_sharpe": var, "n_trial_sharpes": len(finite), "rows": rows,
            "worst": min(rows, key=lambda row: row["dsr"])}


@dataclass(frozen=True)
class NetSeries:
    """Retornos diários líquidos de uma execução (do motor ou do ledger) e suas métricas do motor."""

    name: str
    sessions: list[str]
    returns: list[float]
    metrics: dict

    @classmethod
    def from_result(cls, result: BacktestResult) -> "NetSeries":
        return cls(result.strategy["name"], result.sessions, result.returns, result.metrics)


def strategy_report(result: NetSeries, rf: RiskFreeSeries, *, periods: int = 252,
                    benchmark: NetSeries | None = None) -> dict:
    """Métricas líquidas da estratégia em excesso de ``rf``; beta/alpha contra ``benchmark`` (mesmos pregões)."""
    excess = excess_returns(result.sessions, result.returns, rf)
    n = len(excess)
    sr = sharpe_per_period(excess)
    mean = sum(excess) / n if n else 0.0
    sd = math.sqrt(sum((x - mean) ** 2 for x in excess) / (n - 1)) if n > 1 else 0.0
    report = {
        "sessions": n,
        "risk_free": rf.to_dict(),
        "ann_excess_return": mean * periods,
        "total_return_net": result.metrics["total_return"],
        "risk_free_compounded": rf.compounded(result.sessions),
        "ann_vol": sd * math.sqrt(periods),
        "sharpe_excess_per_period": sr,
        "sharpe_excess_ann": None if sr is None else sr * math.sqrt(periods),
        "psr_vs_zero": probabilistic_sharpe_ratio(excess, 0.0) if n >= 3 else None,
        "t_stat_excess": t_stat(excess),
        "max_drawdown": result.metrics["max_drawdown"],
        "turnover_ann": result.metrics["turnover_ann"],
        "costs_total": result.metrics["costs_total"],
        "net_of_costs": True,
    }
    if benchmark is not None:
        if benchmark.sessions != result.sessions:
            raise ValueError("benchmark precisa dos mesmos pregões")
        report["vs_benchmark"] = beta_alpha(excess, excess_returns(benchmark.sessions, benchmark.returns, rf), periods) \
            | {"benchmark": benchmark.name}
    return report


__all__ = ["NetSeries", "beta_alpha", "dsr_sensitivity", "moments", "n_trials_grid", "psr_from_moments",
           "sharpe_per_period", "strategy_report", "t_stat"]
