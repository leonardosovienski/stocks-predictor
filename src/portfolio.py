"""M4 — Construção de carteira: quintil superior, equiponderado, long-only.

Quintil (não decil): com N=60 o decil daria 6 papéis (concentração excessiva); o quintil
(12) garante diversificação mínima sem diluir o sinal. Long-only — short na B3 envolve
aluguel, adiado deliberadamente.
"""


def select_portfolio(signals, quantile=0.2):
    """Top quintil (default 20%) por momentum, equiponderado, long-only. {ticker: peso}."""
    ranked = sorted((s, t) for t, s in signals.items() if s is not None)
    if not ranked:
        return {}
    k = max(1, round(len(ranked) * quantile))
    top = [t for _, t in ranked[-k:]]            # os maiores momentums
    w = 1.0 / len(top)
    return {t: w for t in top}
