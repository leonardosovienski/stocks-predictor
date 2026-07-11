"""M4 — Construção de carteira: quintil superior, equiponderado, long-only.

Quintil (não decil): com N=60 o decil daria 6 papéis (concentração excessiva); o quintil
(12) garante diversificação mínima sem diluir o sinal. Long-only — short na B3 envolve
aluguel, adiado deliberadamente.
"""
import logging

logger = logging.getLogger(__name__)

_MIN_PORTFOLIO_SIZE = 5  # abaixo disso o período é degenerado — logar warning


def select_portfolio(signals, quantile=0.2):
    """Top quintil (default 20%) por momentum, equiponderado, long-only. {ticker: peso}.

    Retorna dict vazio se signals vazio. Loga warning se o portfólio resultante
    tiver menos de _MIN_PORTFOLIO_SIZE papéis — indica problema upstream (quarentena
    excessiva, universo insuficiente) que pode distorcer o backtest.

    Desempate por score idêntico: ordem lexicográfica do ticker (determinístico).
    """
    ranked = sorted((s, t) for t, s in signals.items() if s is not None)
    if not ranked:
        return {}
    k = max(1, round(len(ranked) * quantile))
    top = [t for _, t in ranked[-k:]]            # os maiores momentums
    if len(top) < _MIN_PORTFOLIO_SIZE:
        logger.warning(
            "portfólio degenerado: %d papel(is) (universo=%d, quintil=%.0f%%) — "
            "período pode distorcer o IC bootstrap",
            len(top), len(ranked), quantile * 100)
    w = 1.0 / len(top)
    return {t: w for t in top}
