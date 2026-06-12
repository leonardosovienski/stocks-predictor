"""predictor-core.stats — estimadores estatísticos: ci_mean (iid) e block bootstrap."""
import math
import random
import logging
from typing import Callable

logger = logging.getLogger(__name__)


def ci_mean(data: list[float], confidence: float = 0.95,
            n_boot: int = 10_000, seed: int = 42) -> tuple[float, float]:
    """IC bootstrap iid para a média. INVÁLIDO para séries autocorrelacionadas — use block_bootstrap."""
    rng = random.Random(seed)
    n = len(data)
    means = sorted(
        sum(rng.choices(data, k=n)) / n
        for _ in range(n_boot)
    )
    alpha = (1 - confidence) / 2
    lo = means[int(alpha * n_boot)]
    hi = means[int((1 - alpha) * n_boot)]
    return lo, hi


def block_bootstrap_ci(
    series: list[float],
    statistic: Callable[[list[float]], float],
    block_length: int = 21,
    n_boot: int = 10_000,
    confidence: float = 0.95,
    seed: int = 42,
    method: str = "moving",
) -> tuple[float, float, list[float]]:
    """IC bootstrap em blocos para estatística arbitrária sobre série temporal.

    method='moving'    — Moving Block Bootstrap (blocos fixos de tamanho block_length)
    method='stationary' — Stationary Bootstrap (comprimentos ~ Geométrica(p=1/block_length),
                          índices circulares conforme Politis & Romano 1994)

    Retorna (lo, hi, distribuição bootstrap).
    """
    rng = random.Random(seed)
    n = len(series)
    if n < block_length:
        raise ValueError(f"series length {n} < block_length {block_length}")

    p = 1.0 / block_length  # parâmetro geométrica para stationary bootstrap

    boot_stats: list[float] = []
    for _ in range(n_boot):
        resampled: list[float] = []
        while len(resampled) < n:
            start = rng.randrange(n)
            if method == "stationary":
                length = _geom_sample(rng, p)
            else:
                length = block_length
            for j in range(length):
                if len(resampled) >= n:
                    break
                resampled.append(series[(start + j) % n])
        boot_stats.append(statistic(resampled[:n]))

    boot_stats.sort()
    alpha = (1 - confidence) / 2
    lo = boot_stats[max(0, int(alpha * n_boot))]
    hi = boot_stats[min(n_boot - 1, int((1 - alpha) * n_boot))]
    return lo, hi, boot_stats


def _geom_sample(rng: random.Random, p: float) -> int:
    """Amostra de distribuição Geométrica(p) — mínimo 1."""
    k = 1
    while rng.random() > p:
        k += 1
    return k


def sharpe(returns: list[float], periods_per_year: int = 252) -> float:
    """Sharpe anualizado (assume risk-free=0). Série constante ≠ 0 → sinal do retorno."""
    if len(returns) < 2:
        return float("nan")
    n = len(returns)
    mean = sum(returns) / n
    var = sum((r - mean) ** 2 for r in returns) / (n - 1)
    if var == 0:
        # série constante: retorno positivo → +inf, negativo → -inf, zero → nan
        if mean > 0:
            return float("inf")
        if mean < 0:
            return float("-inf")
        return float("nan")
    std = math.sqrt(var)
    return (mean / std) * math.sqrt(periods_per_year)


def sortino(returns: list[float], periods_per_year: int = 252) -> float:
    """Sortino anualizado (assume MAR=0)."""
    if len(returns) < 2:
        return float("nan")
    n = len(returns)
    mean = sum(returns) / n
    downside_sq = sum(r ** 2 for r in returns if r < 0)
    downside_std = math.sqrt(downside_sq / n)
    if downside_std == 0:
        return float("nan")
    return (mean / downside_std) * math.sqrt(periods_per_year)


def max_drawdown(cum_returns: list[float]) -> float:
    """Max drawdown sobre série de retornos acumulados (equity curve)."""
    peak = float("-inf")
    mdd = 0.0
    for v in cum_returns:
        if v > peak:
            peak = v
        dd = (peak - v) / peak if peak > 0 else 0.0
        if dd > mdd:
            mdd = dd
    return mdd
