"""Probabilidade de overfitting de backtest (PBO) por CSCV.

Referência: Bailey, Borwein, López de Prado & Zhu (2017), "The Probability of Backtest Overfitting", Journal of
Computational Finance 20(4), seção 2 (CSCV). Implementação local: o ``pypbo`` é AGPL e o ``mlfinlab``, proprietário;
nenhum dos dois é usado.

Matriz M (T períodos × N configurações da mesma família, retornos líquidos no mesmo protocolo):

1. particione as T linhas em S blocos contíguos de mesmo tamanho (S par; sobras do fim descartadas e reportadas);
2. para cada uma das C(S, S/2) combinações de S/2 blocos: J = dentro da amostra (IS), J̄ = o resto (OOS);
3. n* = argmax do desempenho IS (empate → menor índice);
4. ω̄ = posto de n* no OOS / (N + 1), postos crescentes 1..N (empates → posto médio);
5. λ = ln(ω̄ / (1 − ω̄)).

PBO = fração das combinações com λ ≤ 0: o melhor IS ficou na metade de baixo fora da amostra. λ = 0 conta
como overfitting (escolha conservadora; em N par não ocorre sem empate). Desempenho padrão: Sharpe por período
(média / desvio amostral; sem dispersão → média).
"""

from __future__ import annotations

import math
from collections.abc import Callable
from itertools import combinations

from .factor_metrics import average_ranks


def sharpe_or_mean(xs: list[float]) -> float:
    n = len(xs)
    mean = sum(xs) / n
    if n < 2:
        return mean
    sd = math.sqrt(sum((x - mean) ** 2 for x in xs) / (n - 1))
    return mean / sd if sd > 0 else mean


def pbo_cscv(matrix: list[list[float]], n_splits: int, performance: Callable[[list[float]], float] = sharpe_or_mean) -> dict:
    t = len(matrix)
    if n_splits < 2 or n_splits % 2 or t < n_splits:
        raise ValueError("S par, >= 2 e <= número de períodos")
    n = len(matrix[0]) if matrix else 0
    if n < 2 or any(len(row) != n for row in matrix):
        raise ValueError("matriz retangular com >= 2 configurações")
    if any(not math.isfinite(x) for row in matrix for x in row):
        raise ValueError("matriz com valores não finitos")
    size = t // n_splits
    blocks = [list(range(b * size, (b + 1) * size)) for b in range(n_splits)]
    logits, selected, oos_of_selected = [], [], []
    for chosen in combinations(range(n_splits), n_splits // 2):
        inside = [r for b in chosen for r in blocks[b]]
        outside = [r for b in range(n_splits) if b not in chosen for r in blocks[b]]
        is_perf = [performance([matrix[r][c] for r in inside]) for c in range(n)]
        oos_perf = [performance([matrix[r][c] for r in outside]) for c in range(n)]
        best = max(range(n), key=lambda c: (is_perf[c], -c))
        omega = average_ranks(oos_perf)[best] / (n + 1)
        logits.append(math.log(omega / (1 - omega)))
        selected.append(best)
        oos_of_selected.append(oos_perf[best])
    return {
        "pbo": sum(1 for lam in logits if lam <= 0) / len(logits),
        "logits": logits,
        "combinations": len(logits),
        "n_splits": n_splits,
        "configurations": n,
        "rows_used": size * n_splits,
        "rows_dropped": t - size * n_splits,
        "selected": selected,
        "prob_oos_loss": sum(1 for p in oos_of_selected if p < 0) / len(oos_of_selected),
    }


__all__ = ["pbo_cscv", "sharpe_or_mean"]
