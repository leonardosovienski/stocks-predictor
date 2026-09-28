"""Métricas cross-section de um ranqueador de ações, por período de rebalanceamento.

Para cada sinal agendado ``D`` da janela: universo PIT da decisão, escores da ``PITView`` e retorno realizado de
h pregões a partir do preço de execução em ``D + lag`` (``baselines.forward_return``: eventos e proventos
realizados; bruto de custos — é diagnóstico do sinal, não resultado de carteira).

    IC        correlação de Pearson entre escore e retorno futuro no corte transversal
    Rank IC   correlação de Spearman (Pearson dos postos médios; empates recebem a média dos postos)
    ICIR      média(IC) / desvio(IC) por período; anualizado × √(períodos por ano)
    t(IC)     média / (desvio / √n) — com h maior que o passo de rebalanceamento as janelas se sobrepõem e o t
              fica inflado; a autocorrelação do IC entra no embargo do CPCV
    decaimento Rank IC médio por horizonte h
    quantis   retorno médio por quantil de escore (Q1 = pior); long-short = Q_topo − Q_base; long-only = Q_topo
              (e seu excesso sobre a média do universo)

Referência: Grinold & Kahn (2000), "Active Portfolio Management", 2ª ed., cap. 6 (IC) e cap. 16 (ICIR).
"""

from __future__ import annotations

import math
from collections.abc import Callable

from .baselines import forward_return
from .dataset import PITDataset, PITView
from .engine import ProtocolConfig, decision_universe, rebalance_signals

Scorer = Callable[[PITView, tuple[str, ...]], dict[str, float]]


def average_ranks(values: list[float]) -> list[float]:
    """Postos 1..n; empates recebem a média dos postos que ocupariam."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return ranks


def pearson(x: list[float], y: list[float]) -> float | None:
    n = len(x)
    if n != len(y) or n < 3:
        return None
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx == 0 or syy == 0:
        return None
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / math.sqrt(sxx * syy)


def spearman(x: list[float], y: list[float]) -> float | None:
    return pearson(average_ranks(x), average_ranks(y))


def summarize(series: list[float], periods_per_year: float) -> dict:
    n = len(series)
    if n < 2:
        return {"n": n, "mean": series[0] if series else None, "std": None, "ir": None, "ir_ann": None, "t": None,
                "hit_rate": None}
    mean = sum(series) / n
    sd = math.sqrt(sum((x - mean) ** 2 for x in series) / (n - 1))
    ir = mean / sd if sd > 0 else None
    return {"n": n, "mean": mean, "std": sd, "ir": ir, "ir_ann": None if ir is None else ir * math.sqrt(periods_per_year),
            "t": None if ir is None else ir * math.sqrt(n), "hit_rate": sum(1 for x in series if x > 0) / n}


def quantile_buckets(pairs: list[tuple[str, float, float]], n_quantiles: int) -> list[list[float]]:
    """Divide (id, escore, retorno) ordenados por escore (desempate pelo id) em n grupos de tamanho ±1."""
    ordered = sorted(pairs, key=lambda p: (p[1], p[0]))
    n = len(ordered)
    return [[r for _sid, _s, r in ordered[q * n // n_quantiles:(q + 1) * n // n_quantiles]] for q in range(n_quantiles)]


def cross_section(dataset: PITDataset, config: ProtocolConfig, scorer: Scorer, horizons: list[int], *,
                  n_quantiles: int = 5, periods_per_year: float = 12.0) -> dict:
    """IC, Rank IC, ICIR, decaimento e quantis por período. ``horizons[0]`` é o horizonte principal."""
    if not horizons or any(h < 1 for h in horizons) or n_quantiles < 2:
        raise ValueError("horizontes >= 1 e ao menos 2 quantis")
    cal = dataset.calendar
    first, last = dataset.position(config.start), dataset.position(config.end)
    lag, price = config.execution.lag_sessions, config.execution.price
    periods = []
    for signal in rebalance_signals(cal, first - 1, last - lag - min(horizons), config.rebalance):
        view = dataset.view(cal[signal + 1])
        universe = decision_universe(view, config.liquidity)
        scores = scorer(view, universe)
        row = {"signal_session": cal[signal], "execution_session": cal[signal + lag], "n_scored": len(scores),
               "ic": {}, "rank_ic": {}}
        for h in horizons:
            if signal + lag + h > last:  # o rótulo não pode passar do fim da janela
                row["ic"][h] = row["rank_ic"][h] = None
                continue
            pairs = [(sid, s, r) for sid, s in sorted(scores.items())
                     if (r := forward_return(dataset, sid, signal + lag, h, price)) is not None]
            row["ic"][h] = pearson([p[1] for p in pairs], [p[2] for p in pairs])
            row["rank_ic"][h] = spearman([p[1] for p in pairs], [p[2] for p in pairs])
            if h == horizons[0]:
                row["n_pairs"] = len(pairs)
                if len(pairs) >= n_quantiles:
                    buckets = quantile_buckets(pairs, n_quantiles)
                    means = [sum(b) / len(b) for b in buckets]
                    universe_mean = sum(p[2] for p in pairs) / len(pairs)
                    row["quantile_returns"] = means
                    row["long_short"] = means[-1] - means[0]
                    row["long_only"] = means[-1]
                    row["long_only_excess"] = means[-1] - universe_mean
        periods.append(row)
    main = horizons[0]
    summary = {}
    for h in horizons:
        summary[h] = {"ic": summarize([p["ic"][h] for p in periods if p["ic"][h] is not None], periods_per_year),
                      "rank_ic": summarize([p["rank_ic"][h] for p in periods if p["rank_ic"][h] is not None],
                                           periods_per_year)}
    with_q = [p for p in periods if "quantile_returns" in p]
    quantiles = [sum(p["quantile_returns"][q] for p in with_q) / len(with_q) for q in range(n_quantiles)] \
        if with_q else None
    return {
        "horizons": horizons, "main_horizon": main, "n_quantiles": n_quantiles, "periods": periods,
        "summary": summary,
        "decay_rank_ic": {h: summary[h]["rank_ic"]["mean"] for h in horizons},
        "quantile_mean_returns": quantiles,
        "long_short": summarize([p["long_short"] for p in with_q], periods_per_year),
        "long_only": summarize([p["long_only"] for p in with_q], periods_per_year),
        "long_only_excess": summarize([p["long_only_excess"] for p in with_q], periods_per_year),
        "gross_of_costs": True,
    }


__all__ = ["average_ranks", "cross_section", "pearson", "quantile_buckets", "spearman", "summarize"]
