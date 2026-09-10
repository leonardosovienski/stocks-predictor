"""M3 — Liquidity universe with strict date cutoffs and preserved legacy replay.

Prices and quarantine resolutions must precede asof in the default path. This is
not a certificate of historical source availability or complete identities.
Recent-window activity filters stale instruments; it does not prove a listing
status. Four-character prefix deduplication is a historical issuer heuristic,
not a CNPJ/ISIN identity map. Event-complete research needs its separate evidence.
"""
from stocks_predictor.validation import iso_day, positive_integer

# COTAHIST TPMERC '010' = mercado À VISTA. Defesa em camada de LEITURA: o ingest já
# filtra (cotahist.avista_only), mas um banco carregado com avista_only=False traria
# opções/termo (~98% do arquivo) direto para o ranking de liquidez sem este predicado.
SPOT_MARKET = "010"


def _median(xs):
    s = sorted(xs)
    n = len(s)
    if n == 0:
        return 0.0
    m = n // 2
    return s[m] if n % 2 else (s[m - 1] + s[m]) / 2.0


def rank_universe(conn, asof, lookback=126, min_history=252, *, legacy_resolution_state=False):
    """Rank pre-asof liquidity using resolutions recorded before the cutoff.

    This temporal guard does not certify source completeness, historical identity,
    or when a reconstructed corporate event was public. A later source correction
    may be valid for retrospective reconciliation, but it is not evidence that
    the quarantine had already been cleared in a past decision. Frozen legacy
    runners explicitly retain their latest-resolution reconstruction policy.
    """
    iso_day(asof, 'asof')
    positive_integer(lookback, 'lookback')
    positive_integer(min_history, 'min_history')
    resolution = "resolved_at IS NULL" if legacy_resolution_state else "(resolved_at IS NULL OR resolved_at >= ?)"
    params = (asof,) if legacy_resolution_state else (asof, asof)
    quarantined = {r[0] for r in conn.execute(
        "SELECT DISTINCT ticker FROM quarantine WHERE date < ? AND " + resolution,
        params)}
    # janela de liquidez é do CALENDÁRIO real (pregões que existem no banco antes de
    # asof), não "os últimos N registros de cada ticker" — senão um papel deslistado
    # há anos passa a janela usando pregões antigos como se fossem recentes.
    window_dates = [r[0] for r in conn.execute(
        "SELECT DISTINCT date FROM prices_raw WHERE date < ? AND market_type = ? "
        "ORDER BY date DESC LIMIT ?", (asof, SPOT_MARKET, lookback))]
    if len(window_dates) < lookback:
        return []
    window_start = window_dates[-1]

    # agregados de uma passada (não N+1 por ticker): contagem de pregões p/
    # min_history, último pregão p/ deslistagem. GROUP BY date dedupa re-ingest.
    hist = {r[0]: (r[1], r[2]) for r in conn.execute(
        "SELECT ticker, COUNT(DISTINCT date), MAX(date) FROM prices_raw "
        "WHERE date < ? AND market_type = ? GROUP BY ticker ORDER BY ticker",
        (asof, SPOT_MARKET))}
    # ORDER BY ticker: dedup ON/PN abaixo mantém o PRIMEIRO em empate de
    # liquidez — sem ordenação determinística o vencedor do empate dependia
    # da ordem física de leitura do SQLite (irreproduzível entre máquinas).
    vols: dict[str, list[float]] = {}
    for tk, _d, v in conn.execute(
            "SELECT ticker, date, MAX(volume_fin) FROM prices_raw "
            "WHERE date >= ? AND date < ? AND market_type = ? GROUP BY ticker, date",
            (window_start, asof, SPOT_MARKET)):
        vols.setdefault(tk, []).append(v)

    meds = {}
    for tk, (n_hist, last_date) in hist.items():
        if tk in quarantined or n_hist < min_history:
            continue
        if last_date < window_start:
            continue    # deslistado/parou de negociar antes da janela de liquidez
        # sessão do calendário SEM negócio deste papel = volume 0 naquele dia —
        # senão um papel que negociou 1x na janela ganharia "mediana" de um único
        # print gigante e furaria o ranking de liquidez.
        v = vols.get(tk, [])
        meds[tk] = _median(v + [0.0] * (lookback - len(v)))
    # dedup ON/PN: por prefixo de 4 letras, fica o de maior liquidez
    best = {}
    for tk, med in meds.items():
        root = tk[:4]
        if root not in best or med > best[root][1]:
            best[root] = (tk, med)
    return sorted(best.values(), key=lambda x: -x[1])


def select_universe(conn, asof, top_n=60, lookback=126, min_history=252):
    positive_integer(top_n, 'top_n')
    return [t for t, _ in rank_universe(conn, asof, lookback, min_history)[:top_n]]


def legacy_select_universe(conn, asof, top_n=60, lookback=126, min_history=252):
    """Frozen reconstruction: latest quarantine state, NOT a strict temporal claim."""
    positive_integer(top_n, 'top_n')
    return [t for t, _ in rank_universe(conn, asof, lookback, min_history,
                                      legacy_resolution_state=True)[:top_n]]


def materialize_snapshot(conn, asof, top_n=60, lookback=126, min_history=252):
    """Persist one coherent snapshot; conflicting replay requires an isolated DB.

    The historical schema has no run/version key. It cannot represent a second
    composition for the same date. Never append its new members to the old one,
    and never return a computed composition different from the persisted evidence.
    Savepoint rollback preserves any transaction already owned by the caller.
    """
    positive_integer(top_n, 'top_n')
    conn.execute("SAVEPOINT stocks_universe_snapshot")
    try:
        ranked = rank_universe(conn, asof, lookback, min_history)[:top_n]
        if not ranked:
            raise ValueError("empty universe cannot establish a persisted snapshot")
        expected = [(tk, med, rank) for rank, (tk, med) in enumerate(ranked, 1)]
        existing = [tuple(row) for row in conn.execute(
            "SELECT ticker,median_vol,rank FROM universe_snapshots WHERE asof_date=? ORDER BY rank,ticker",
            (asof,))]
        if existing and existing != expected:
            raise ValueError("snapshot conflicts with preserved evidence; use a separately versioned database")
        if not existing:
            conn.executemany(
                "INSERT INTO universe_snapshots(asof_date,ticker,median_vol,rank) VALUES(?,?,?,?)",
                [(asof, *row) for row in expected])
    except BaseException:
        conn.execute("ROLLBACK TO stocks_universe_snapshot")
        conn.execute("RELEASE stocks_universe_snapshot")
        raise
    conn.execute("RELEASE stocks_universe_snapshot")
    return [t for t, _ in ranked]
