"""M3 — Universo point-in-time por liquidez (mediana de volume financeiro).

Regra inviolável: em cada `asof`, usa SOMENTE dados < asof — nada do futuro toca a
seleção (anti-lookahead estrutural). Exclui quarentenados e papéis com histórico curto.
Dedup ON/PN pelo prefixo de 4 letras (fica o de maior liquidez na janela).
"""


def _median(xs):
    s = sorted(xs)
    n = len(s)
    if n == 0:
        return 0.0
    m = n // 2
    return s[m] if n % 2 else (s[m - 1] + s[m]) / 2.0


def rank_universe(conn, asof, lookback=126, min_history=252):
    """[(ticker, median_vol)] ranqueado por liquidez, POINT-IN-TIME (só dados < asof)."""
    quarantined = {r[0] for r in conn.execute(
        "SELECT DISTINCT ticker FROM quarantine WHERE date < ?", (asof,))}
    tickers = [r[0] for r in conn.execute("SELECT DISTINCT ticker FROM prices_raw")]
    meds = {}
    for tk in tickers:
        if tk in quarantined:
            continue
        vols = [r[0] for r in conn.execute(
            "SELECT volume_fin FROM prices_raw WHERE ticker=? AND date < ? ORDER BY date",
            (tk, asof))]
        if len(vols) < min_history:
            continue
        meds[tk] = _median(vols[-lookback:])
    # dedup ON/PN: por prefixo de 4 letras, fica o de maior liquidez
    best = {}
    for tk, med in meds.items():
        root = tk[:4]
        if root not in best or med > best[root][1]:
            best[root] = (tk, med)
    return sorted(best.values(), key=lambda x: -x[1])


def select_universe(conn, asof, top_n=60, lookback=126, min_history=252):
    return [t for t, _ in rank_universe(conn, asof, lookback, min_history)[:top_n]]


def materialize_snapshot(conn, asof, top_n=60, lookback=126, min_history=252):
    """Grava o universo point-in-time em universe_snapshots (auditável para sempre)."""
    ranked = rank_universe(conn, asof, lookback, min_history)[:top_n]
    for rank, (tk, med) in enumerate(ranked, 1):
        conn.execute(
            "INSERT OR REPLACE INTO universe_snapshots(asof_date,ticker,median_vol,rank) "
            "VALUES(?,?,?,?)", (asof, tk, med, rank))
    conn.commit()
    return [t for t, _ in ranked]
