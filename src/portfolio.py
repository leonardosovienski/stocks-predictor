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


def momentum_lowvol_double_filter(mom_signals: dict, vol_signals: dict,
                                  momentum_quantile: float = 0.4,
                                  vol_quantile: float = 0.5) -> dict:
    """H8 — filtro duplo: primeiro o top `momentum_quantile` do universo por
    momentum, depois a fração `vol_quantile` de menor volatilidade DENTRO
    desse subconjunto (não do universo inteiro). Equiponderado, long-only.

    Só tickers com AMBOS os sinais entram na 1ª seleção — sem isso um ticker
    com momentum sem histórico de vol suficiente (ou vice-versa) seria
    rankeado num filtro e sumiria no outro sem essa interseção explícita.
    {} se não houver nenhum ticker com os dois sinais."""
    common = [t for t in mom_signals if t in vol_signals]
    if not common:
        return {}
    ranked_mom = sorted(common, key=lambda t: mom_signals[t], reverse=True)
    k_mom = max(1, round(len(ranked_mom) * momentum_quantile))
    top_mom = ranked_mom[:k_mom]
    ranked_vol = sorted(top_mom, key=lambda t: vol_signals[t])
    k_vol = max(1, round(len(ranked_vol) * vol_quantile))
    chosen = ranked_vol[:k_vol]
    w = 1.0 / len(chosen)
    return {t: w for t in chosen}


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
