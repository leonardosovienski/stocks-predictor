"""M3 — Universo point-in-time por liquidez (mediana de volume financeiro).

Regra inviolável: em cada `asof`, usa SOMENTE dados < asof — nada do futuro toca a
seleção (anti-lookahead estrutural). Exclui quarentenados, papéis com histórico curto
E papéis DESLISTADOS (sem pregão dentro da janela de liquidez recente — um papel cujo
último negócio foi anos antes do asof não pode ser tratado como ativo hoje só porque
tem `min_history` linhas em algum ponto do passado). Dedup ON/PN pelo prefixo de 4
letras (fica o de maior liquidez na janela).
"""

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


def rank_universe(conn, asof, lookback=126, min_history=252):
    """[(ticker, median_vol)] ranqueado por liquidez, POINT-IN-TIME (só dados < asof)."""
    # só quarentena NÃO resolvida exclui — um split adjudicado (adjustments +
    # resolved_at) já corrige a série, então o papel volta a ser elegível.
    quarantined = {r[0] for r in conn.execute(
        "SELECT DISTINCT ticker FROM quarantine WHERE date < ? AND resolved_at IS NULL",
        (asof,))}
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
        "WHERE date < ? AND market_type = ? GROUP BY ticker", (asof, SPOT_MARKET))}
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
    return [t for t, _ in rank_universe(conn, asof, lookback, min_history)[:top_n]]


def materialize_snapshot(conn, asof, top_n=60, lookback=126, min_history=252):
    """Grava o universo point-in-time em universe_snapshots (auditável para sempre).

    INSERT OR IGNORE: snapshot é IMUTÁVEL — re-executar com código novo não
    reescreve o passado registrado; um recálculo deliberado é um novo run."""
    ranked = rank_universe(conn, asof, lookback, min_history)[:top_n]
    for rank, (tk, med) in enumerate(ranked, 1):
        conn.execute(
            "INSERT OR IGNORE INTO universe_snapshots(asof_date,ticker,median_vol,rank) "
            "VALUES(?,?,?,?)", (asof, tk, med, rank))
    conn.commit()
    return [t for t, _ in ranked]
