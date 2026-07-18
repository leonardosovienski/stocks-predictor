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
