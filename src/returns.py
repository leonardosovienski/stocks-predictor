"""M3 — Matriz de retornos a partir da série ajustada (mensal, base do momentum)."""


def month_end_dates(dates):
    """Último pregão de cada mês (chave YYYY-MM), em ordem. `dates` ordenado asc."""
    last = {}
    for d in dates:
        last[d[:7]] = d
    return [last[k] for k in sorted(last)]


def monthly_returns(dates, closes):
    """[(month_end, ret)] — retorno entre fechamentos de meses consecutivos."""
    me = month_end_dates(dates)
    price = dict(zip(dates, closes))
    out = []
    for prev, cur in zip(me, me[1:]):
        if price[prev] > 0:
            out.append((cur, price[cur] / price[prev] - 1.0))
    return out


def returns_matrix(series_by_ticker):
    """{ticker: (dates, closes)} -> {ticker: {month_end: ret}}."""
    return {t: dict(monthly_returns(dates, closes))
            for t, (dates, closes) in series_by_ticker.items()}
