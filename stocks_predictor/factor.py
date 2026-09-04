"""M4 — Motor interpretável: momentum 12-1 (série AJUSTADA, point-in-time).

Sinal em `asof` = retorno acumulado de [asof-252, asof-21] (12 meses excluindo o último
— o clássico, evita a reversão de curtíssimo prazo). UM fator só; zoológico proibido até
a H1 ser julgada. Usa apenas preços <= asof.

H2 (pré-registro 2026-07-16, H1 já julgada): `realized_vol` — desvio-padrão dos
retornos diários dos últimos `lookback` pregões ≤ asof. Mesma disciplina
point-in-time; a carteira da H2 toma o quintil INFERIOR (baixa volatilidade).
"""
import datetime
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
    # i_end<0 só ocorre se skip>lookback (config malformada — nenhuma
    # hipótese registrada usa isso hoje); sem esta guarda, `closes[i_end]`
    # indexava por trás (Python) e lia um preço fora da janela pretendida.
    if i_start < 0 or i_end < 0 or closes[i_start] <= 0 or closes[i_end] <= 0:
        return None   # preço <= 0 em qualquer ponta = retorno indefinido
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


def _fundamental_signals(conn, tickers, asof, disclosure_embargo_days, column):
    """Motor comum de sinal contábil point-in-time (H7 ROE, H9 alavancagem):
    {ticker: valor de `column` em `fundamentals`} usando a linha mais recente
    cujo embargo de divulgação já venceu em `asof`.

    `fundamentals.ref_date` é o fim do exercício, não a data de publicação real
    (a DFP só é PUBLICADA meses depois — ver `ingest_cvm.py`). Usar `ref_date`
    puro como `known_at` seria otimista/lookahead. `disclosure_embargo_days`
    soma um embargo fixo: só entra no sinal em `asof` a linha mais recente com
    `ref_date + embargo <= asof` (comparação lexicográfica de datas ISO, dias
    corridos). Ticker sem nenhuma linha elegível fica FORA (dado indisponível
    > dado inventado, mesma disciplina de `vol_signals`/`ownership`)."""
    if column not in ("roe", "leverage"):
        raise ValueError(f"coluna de fundamentals não suportada: {column!r}")
    out = {}
    for t in tickers:
        rows = conn.execute(
            f"SELECT ref_date, {column} FROM fundamentals WHERE ticker = ?"
            f" AND {column} IS NOT NULL ORDER BY ref_date DESC", (t,)).fetchall()
        for ref_date, value in rows:
            known_at = (datetime.date.fromisoformat(ref_date)
                       + datetime.timedelta(days=disclosure_embargo_days)).isoformat()
            if known_at <= asof:
                out[t] = value
                break
    return out


def roe_signals(conn, tickers, asof, disclosure_embargo_days=90):
    """H7 (pré-registro 2026-09-03) — {ticker: roe} point-in-time."""
    return _fundamental_signals(conn, tickers, asof, disclosure_embargo_days, "roe")


def leverage_signals(conn, tickers, asof, disclosure_embargo_days=90):
    """H9 (pré-registro 2026-09-04) — {ticker: leverage} point-in-time.
    `leverage = (passivo_total - patrimonio_liquido) / ativo_total`
    (ver `ingest_cvm.compute_fundamentals` — exclui o PL do passivo, senão
    o índice daria sempre ~1.0 por identidade contábil)."""
    return _fundamental_signals(conn, tickers, asof, disclosure_embargo_days, "leverage")
