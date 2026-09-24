"""Combinatorial Purged Cross-Validation (CPCV) — López de Prado (2018), "Advances in Financial Machine Learning",
cap. 7 (purge e embargo) e cap. 12 (CPCV e caminhos de backtest).

Cada amostra carrega o intervalo de informação do seu rótulo em índices de pregão: ``t0`` = pregão da decisão,
``t1`` = último pregão cujo preço entra no rótulo (execução em ``t0 + lag``, horizonte h → ``t1 = t0 + lag + h``).
O purge usa esse intervalo real, não um número fixo de observações:

    purge     remove do treino toda amostra cujo [t0, t1] cruza o intervalo de um bloco contíguo de teste
              [min t0, max t1];
    embargo   remove do treino as amostras com t0 em (fim do bloco, fim do bloco + embargo] — dependência serial
              além da sobreposição de rótulos.

``derive_purge_embargo`` documenta os tamanhos a partir do horizonte do rótulo, do passo de rebalanceamento e da
autocorrelação da série de dependência (IC ou retorno por período). Não há valor escolhido por parecer razoável.

Com N grupos e k de teste há C(N, k) divisões e φ = C(N − 1, k − 1) caminhos completos de backtest. Cada grupo
aparece exatamente uma vez em cada caminho.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from itertools import combinations

from .walkforward import LeakageError


@dataclass(frozen=True)
class Sample:
    t0: int
    t1: int

    def __post_init__(self):
        if self.t1 < self.t0:
            raise ValueError("t1 < t0")


@dataclass(frozen=True)
class CPCVSplit:
    index: int
    test_groups: tuple[int, ...]
    train: tuple[int, ...]
    test: tuple[int, ...]
    purged: tuple[int, ...]
    embargoed: tuple[int, ...]


def autocorrelation(series: list[float], max_lag: int) -> list[float]:
    """ρ(ℓ) = Σ (x_t − x̄)(x_{t+ℓ} − x̄) / Σ (x_t − x̄)², ℓ = 0..max_lag (estimador usual, viesado)."""
    n = len(series)
    if n < 3 or max_lag < 1:
        raise ValueError("série com >= 3 pontos e max_lag >= 1")
    mean = sum(series) / n
    denominator = sum((x - mean) ** 2 for x in series)
    if denominator == 0:
        return [1.0] + [0.0] * max_lag
    return [sum((series[t] - mean) * (series[t + lag] - mean) for t in range(n - lag)) / denominator
            for lag in range(min(max_lag, n - 1) + 1)]


def derive_purge_embargo(label_horizon: int, lag: int, rebalance_step: int, dependence: list[float], *,
                         z: float = 1.96, max_lag: int = 12) -> dict:
    """Tamanhos derivados, em pregões.

    purge_size   = lag + h: o rótulo de t0 usa preços até t0 + lag + h; é a largura do intervalo purgado.
    embargo_size = (L − 1) × passo, com L = primeira defasagem (em períodos de rebalanceamento) em que
                   |ρ(L)| < z/√n (banda de Bartlett). ρ(1) já insignificante → embargo 0; sem defasagem
                   insignificante até ``max_lag`` → embargo = max_lag × passo, sinalizado.
    """
    if label_horizon < 1 or lag < 1 or rebalance_step < 1:
        raise ValueError("horizonte, lag e passo >= 1")
    acf = autocorrelation(dependence, max_lag)
    band = z / math.sqrt(len(dependence))
    first_insignificant = next((lag_ for lag_ in range(1, len(acf)) if abs(acf[lag_]) < band), None)
    exhausted = first_insignificant is None
    lags_embargoed = (len(acf) - 1) if exhausted else first_insignificant - 1
    return {
        "purge_size": lag + label_horizon,
        "embargo_size": lags_embargoed * rebalance_step,
        "label_horizon": label_horizon, "execution_lag": lag, "rebalance_step": rebalance_step,
        "acf": acf, "band": band, "z": z, "n": len(dependence),
        "first_insignificant_lag": first_insignificant, "max_lag_exhausted": exhausted,
        "rule": "purge = lag + h; embargo = (primeira defasagem com |ρ| < z/√n − 1) × passo",
    }


def _groups(n: int, n_groups: int) -> list[range]:
    bounds = [g * n // n_groups for g in range(n_groups + 1)]
    return [range(bounds[g], bounds[g + 1]) for g in range(n_groups)]


def cpcv_splits(samples: list[Sample], n_groups: int, k_test: int, *, embargo: int) -> list[CPCVSplit]:
    """C(N, k) divisões; amostras ordenadas por t0 e divididas em N grupos contíguos de tamanho ±1."""
    if not 2 <= n_groups <= len(samples) or not 1 <= k_test < n_groups or embargo < 0:
        raise ValueError("2 <= N <= amostras, 1 <= k < N, embargo >= 0")
    if any(a.t0 > b.t0 for a, b in zip(samples, samples[1:])):
        raise ValueError("amostras ordenadas por t0")
    groups = _groups(len(samples), n_groups)
    splits = []
    for number, chosen in enumerate(combinations(range(n_groups), k_test)):
        test = [i for g in chosen for i in groups[g]]
        spans = block_spans(samples, test)
        test_set = set(test)
        train, purged, embargoed = [], [], []
        for i, s in enumerate(samples):
            if i in test_set:
                continue
            if any(s.t0 <= b1 and s.t1 >= b0 for b0, b1 in spans):
                purged.append(i)
            elif any(b1 < s.t0 <= b1 + embargo for _b0, b1 in spans):
                embargoed.append(i)
            else:
                train.append(i)
        split = CPCVSplit(number, chosen, tuple(train), tuple(test), tuple(purged), tuple(embargoed))
        assert_no_leakage(samples, split, embargo)
        splits.append(split)
    return splits


def block_spans(samples: list[Sample], test: list[int]) -> list[tuple[int, int]]:
    """[min t0, max t1] de cada bloco de índices de teste consecutivos."""
    spans, run = [], []
    for i in sorted(test):
        if run and i != run[-1] + 1:
            spans.append(run)
            run = []
        run.append(i)
    if run:
        spans.append(run)
    return [(min(samples[i].t0 for i in r), max(samples[i].t1 for i in r)) for r in spans]


def assert_no_leakage(samples: list[Sample], split: CPCVSplit, embargo: int) -> None:
    """Nenhum intervalo de treino cruza o de uma amostra de teste; nenhum treino começa no embargo de um bloco."""
    spans = block_spans(samples, list(split.test))
    for i in split.train:
        a = samples[i]
        for j in split.test:
            if a.t0 <= samples[j].t1 and a.t1 >= samples[j].t0:
                raise LeakageError(f"treino {i} cruza teste {j}")
        for _b0, b1 in spans:
            if b1 < a.t0 <= b1 + embargo:
                raise LeakageError(f"treino {i} dentro do embargo após um bloco de teste")


def cpcv_paths(n_groups: int, k_test: int) -> list[list[tuple[int, int]]]:
    """φ = C(N − 1, k − 1) caminhos; cada caminho é [(grupo, índice da divisão)] cobrindo todos os grupos."""
    splits = list(combinations(range(n_groups), k_test))
    occurrences = {g: [s for s, chosen in enumerate(splits) if g in chosen] for g in range(n_groups)}
    phi = math.comb(n_groups - 1, k_test - 1)
    if any(len(v) != phi for v in occurrences.values()):
        raise AssertionError("contagem de ocorrências inconsistente")
    return [[(g, occurrences[g][p]) for g in range(n_groups)] for p in range(phi)]


def run_cpcv(samples: list[Sample], n_groups: int, k_test: int, *, embargo: int,
             fit_predict: Callable[[list[int], list[int]], dict[int, float]],
             performance: Callable[[list[float]], float]) -> dict:
    """Ajusta em cada divisão só com o treino purgado/embargado e monta os φ caminhos de teste.

    ``fit_predict(treino, teste)`` devolve o resultado fora da amostra de cada índice de teste (exatamente
    esses). Cada caminho concatena os grupos na ordem do tempo; ``performance`` resume cada caminho.
    """
    splits = cpcv_splits(samples, n_groups, k_test, embargo=embargo)
    groups = _groups(len(samples), n_groups)
    predictions = []
    for split in splits:
        out = fit_predict(list(split.train), list(split.test))
        if set(out) != set(split.test):
            raise ValueError("fit_predict deve prever exatamente os índices de teste")
        predictions.append(out)
    paths = []
    for path in cpcv_paths(n_groups, k_test):
        series = [predictions[s][i] for g, s in path for i in groups[g]]
        paths.append({"performance": performance(series), "n": len(series)})
    return {"n_splits": len(splits), "n_paths": len(paths), "paths": paths,
            "splits": [{"index": s.index, "test_groups": list(s.test_groups), "train": len(s.train),
                        "test": len(s.test), "purged": len(s.purged), "embargoed": len(s.embargoed)}
                       for s in splits]}


def label_samples(signal_indices: list[int], lag: int, horizon: int) -> list[Sample]:
    """Amostras de rebalanceamento: decisão em t0, rótulo até t0 + lag + h."""
    return [Sample(t0, t0 + lag + horizon) for t0 in signal_indices]


__all__ = ["CPCVSplit", "Sample", "assert_no_leakage", "autocorrelation", "cpcv_paths", "cpcv_splits",
           "derive_purge_embargo", "label_samples", "block_spans", "run_cpcv"]
