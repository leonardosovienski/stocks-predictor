"""M4 — Motor interpretável: momentum 12-1 (série AJUSTADA, point-in-time).

Sinal em `asof` = retorno acumulado de [asof-252, asof-21] (12 meses excluindo o último
— o clássico, evita a reversão de curtíssimo prazo). UM fator só; zoológico proibido até
a H1 ser julgada. Usa apenas preços <= asof.

H2 (pré-registro 2026-07-16, H1 já julgada): `realized_vol` — desvio-padrão dos
retornos diários dos últimos `lookback` pregões ≤ asof. Mesma disciplina
point-in-time; a carteira da H2 toma o quintil INFERIOR (baixa volatilidade).
"""
import statistics


def _idx_le(dates, asof):
    """Índice do último pregão <= asof (dates asc), ou None."""
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


def realized_vol(dates, closes, asof, lookback=252):
    """Desvio-padrão dos retornos diários da janela [asof-lookback, asof] na série
    ajustada. None se histórico insuficiente ou preço <=0 na janela (sinal
    indefinido > sinal distorcido). Point-in-time: nada após asof entra."""
    i = _idx_le(dates, asof)
    if i is None or i - lookback < 0:
        return None
    window = closes[i - lookback:i + 1]
    if any(c <= 0 for c in window):
        return None
    rets = [window[j] / window[j - 1] - 1.0 for j in range(1, len(window))]
    return statistics.pstdev(rets)


def vol_signals(series_by_ticker, asof, lookback=252):
    """{ticker: vol realizada} para os tickers com histórico suficiente em asof."""
    out = {}
    for t, (dates, closes) in series_by_ticker.items():
        v = realized_vol(dates, closes, asof, lookback)
        if v is not None:
            out[t] = v
    return out
