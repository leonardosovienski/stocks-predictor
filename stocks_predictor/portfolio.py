"""M4 — Construção de carteira: quintil superior, equiponderado, long-only.

Quintil (não decil): com N=60 o decil daria 6 papéis (concentração excessiva); o quintil
(12) garante diversificação mínima sem diluir o sinal. Long-only — short na B3 envolve
aluguel, adiado deliberadamente.

`take` (H2+): "top" = maiores sinais (H1, momentum); "bottom" = menores sinais
(H2, baixa volatilidade). O default preserva a H1 byte a byte.
"""


def inverse_vol_weights(vols):
    """H4 — sizing por volatility targeting: peso ∝ 1/vol, normalizado (Σw=1).

    `vols`: {ticker: vol realizada}. Vol None/<=0 fica FORA (peso indefinido >
    peso distorcido — declarado no pré-registro da H4). {} se nada sobrar."""
    inv = {t: 1.0 / v for t, v in vols.items() if v is not None and v > 0}
    total = sum(inv.values())
    if total <= 0:
        return {}
    return {t: x / total for t, x in inv.items()}


def double_filter(primary_signals: dict, secondary_signals: dict,
                  primary_quantile: float, secondary_quantile: float,
                  primary_take: str = "top", secondary_take: str = "top") -> dict:
    """Motor comum de filtro duplo (H8: momentum∩baixa-vol; H10:
    ROE∩baixa-alavancagem): 1ª etapa seleciona `primary_quantile` do universo
    por `primary_signals` (`primary_take`="top"/"bottom"); 2ª etapa seleciona
    `secondary_quantile` DENTRO desse subconjunto por `secondary_signals`
    (não do universo inteiro). Equiponderado, long-only.

    Só tickers com AMBOS os sinais entram na 1ª seleção — sem isso um ticker
    com sinal primário sem sinal secundário (ou vice-versa) seria rankeado
    num filtro e sumiria no outro sem essa interseção explícita. {} se não
    houver nenhum ticker com os dois sinais."""
    common = [t for t in primary_signals if t in secondary_signals]
    if not common:
        return {}
    ranked_1 = sorted(common, key=lambda t: primary_signals[t],
                      reverse=(primary_take == "top"))
    k1 = max(1, round(len(ranked_1) * primary_quantile))
    stage1 = ranked_1[:k1]
    ranked_2 = sorted(stage1, key=lambda t: secondary_signals[t],
                      reverse=(secondary_take == "top"))
    k2 = max(1, round(len(ranked_2) * secondary_quantile))
    chosen = ranked_2[:k2]
    w = 1.0 / len(chosen)
    return {t: w for t in chosen}


def momentum_lowvol_double_filter(mom_signals: dict, vol_signals: dict,
                                  momentum_quantile: float = 0.4,
                                  vol_quantile: float = 0.5) -> dict:
    """H8 — filtro duplo: primeiro o top `momentum_quantile` do universo por
    momentum, depois a fração `vol_quantile` de menor volatilidade DENTRO
    desse subconjunto (não do universo inteiro). Equiponderado, long-only.
    Wrapper fino sobre `double_filter` (refactor 2026-09-04 — comportamento
    idêntico, byte a byte, ao original; H8 já julgada, não mexe no veredito)."""
    return double_filter(mom_signals, vol_signals, momentum_quantile, vol_quantile,
                         primary_take="top", secondary_take="bottom")


def roe_lowlev_double_filter(roe_signals: dict, leverage_signals: dict,
                             roe_quantile: float = 0.4,
                             leverage_quantile: float = 0.5) -> dict:
    """H10 — filtro duplo: primeiro o top `roe_quantile` do universo por ROE,
    depois a fração `leverage_quantile` de MENOR alavancagem DENTRO desse
    subconjunto. Equiponderado, long-only. Mesma maquinaria de
    `double_filter` (H8), aplicada às duas variáveis contábeis da H7/H9 em
    vez de momentum/vol — hipótese distinta de ambas isoladas."""
    return double_filter(roe_signals, leverage_signals, roe_quantile, leverage_quantile,
                         primary_take="top", secondary_take="bottom")


def select_portfolio(signals, quantile=0.2, take="top"):
    """Quintil (default 20%) por sinal, equiponderado, long-only. {ticker: peso}."""
    if take not in ("top", "bottom"):
        raise ValueError(f"take inválido: {take!r} — use 'top' ou 'bottom'")
    ranked = sorted((s, t) for t, s in signals.items() if s is not None)
    if not ranked:
        return {}
    k = max(1, round(len(ranked) * quantile))
    chosen = ranked[-k:] if take == "top" else ranked[:k]
    top = [t for _, t in chosen]
    w = 1.0 / len(top)
    return {t: w for t in top}
