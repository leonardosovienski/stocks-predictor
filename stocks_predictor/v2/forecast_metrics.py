"""Métricas de previsão probabilística por quantis (implementação pequena e testada).

    perda quantílica  ρ_τ(y − q) = τ·(y − q) se y ≥ q, senão (1 − τ)·(q − y)
    CRPS (quantis)    CRPS ≈ (2/K)·Σ_k ρ_{τ_k}(y − q_{τ_k}), média sobre as previsões — aproximação do CRPS pela
                      integral da perda quantílica (Gneiting & Raftery 2007, JASA 102(477); Gneiting 2011)
    WQL               WQL = 2·Σ_t Σ_k ρ_{τ_k}(y_t − q_{t,τ_k}) / (K·Σ_t |y_t|) — definição usada no Chronos
                      (Ansari et al. 2024, TMLR) e no fev; exige série de nível positivo (aqui: preço)
    cobertura         fração de alvos dentro de [q_baixo, q_alto]

O ``fev`` (Apache-2.0) não foi adotado: traria datasets e pandas para duas fórmulas de poucas linhas, e o alvo aqui
(retorno em log e nível de preço por janela) não é o formato de tarefa dele.
"""

from __future__ import annotations

import math


def pinball(y: float, q: float, tau: float) -> float:
    return tau * (y - q) if y >= q else (1 - tau) * (q - y)


def _check(targets: list[float], quantiles: list[list[float]], levels: list[float]) -> None:
    if not targets or len(targets) != len(quantiles):
        raise ValueError("alvos e previsões com o mesmo tamanho, não vazios")
    if not levels or any(not 0 < t < 1 for t in levels) or levels != sorted(levels):
        raise ValueError("níveis em (0, 1), crescentes")
    for row in quantiles:
        if len(row) != len(levels) or any(not math.isfinite(v) for v in row):
            raise ValueError("uma previsão por nível, finita")
        if any(b < a for a, b in zip(row, row[1:])):
            raise ValueError("quantis cruzados")


def crps_quantile(targets: list[float], quantiles: list[list[float]], levels: list[float]) -> float:
    _check(targets, quantiles, levels)
    k = len(levels)
    return sum(2 / k * sum(pinball(y, q, t) for q, t in zip(row, levels))
               for y, row in zip(targets, quantiles)) / len(targets)


def crps_each(targets: list[float], quantiles: list[list[float]], levels: list[float]) -> list[float]:
    _check(targets, quantiles, levels)
    k = len(levels)
    return [2 / k * sum(pinball(y, q, t) for q, t in zip(row, levels)) for y, row in zip(targets, quantiles)]


def wql(targets: list[float], quantiles: list[list[float]], levels: list[float]) -> float:
    _check(targets, quantiles, levels)
    scale = sum(abs(y) for y in targets)
    if scale == 0:
        raise ValueError("WQL indefinido: Σ|y| = 0")
    k = len(levels)
    loss = sum(pinball(y, q, t) for y, row in zip(targets, quantiles) for q, t in zip(row, levels))
    return 2 * loss / (k * scale)


def coverage(targets: list[float], lower: list[float], upper: list[float]) -> float:
    if not targets or not len(targets) == len(lower) == len(upper):
        raise ValueError("séries com o mesmo tamanho")
    return sum(1 for y, lo, hi in zip(targets, lower, upper) if lo <= y <= hi) / len(targets)


__all__ = ["coverage", "crps_each", "crps_quantile", "pinball", "wql"]
