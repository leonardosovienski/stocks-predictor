"""M4 — Motor interpretável: momentum 12-1 (série AJUSTADA, point-in-time).

Sinal em `asof` = retorno acumulado de [asof-252, asof-21] (12 meses excluindo o último
— o clássico, evita a reversão de curtíssimo prazo). UM fator só; zoológico proibido até
a H1 ser julgada. Usa apenas preços <= asof.
"""


def _idx_le(dates, asof):
    """Índice do último pregão <= asof (dates asc), ou None.

    PRÉ-CONDIÇÃO: dates deve estar em ordem crescente (garantido pela query
    ORDER BY date em adjusted_series). A asserção abaixo detecta violações em
    desenvolvimento; em produção com -O é removida automaticamente.
    """
    assert all(dates[i] <= dates[i + 1] for i in range(len(dates) - 1)), \
        "dates fora de ordem — violação de pré-condição de _idx_le"
    res = None
    for i, d in enumerate(dates):
        if d <= asof:
            res = i
        else:
            break
    return res


def momentum_12_1(dates, closes, asof, lookback=252, skip=21):
    """Retorno de [asof-lookback] a [asof-skip] na série ajustada. None se histórico
    insuficiente. Point-in-time: nada após asof entra."""
    i = _idx_le(dates, asof)
    if i is None:
        return None
    i_end, i_start = i - skip, i - lookback
    if i_start < 0 or closes[i_start] <= 0:
        return None
    return closes[i_end] / closes[i_start] - 1.0


def signals(series_by_ticker, asof, lookback=252, skip=21):
    """{ticker: momentum} para os tickers com histórico suficiente em asof."""
    out = {}
    for t, (dates, closes) in series_by_ticker.items():
        m = momentum_12_1(dates, closes, asof, lookback, skip)
        if m is not None:
            out[t] = m
    return out
