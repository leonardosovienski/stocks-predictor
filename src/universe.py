"""M3 — Universo point-in-time por liquidez (mediana de volume financeiro).

Regra inviolável: em cada `asof`, usa SOMENTE dados < asof — nada do futuro toca a
seleção (anti-lookahead estrutural). Exclui quarentenados e papéis com histórico curto.
Dedup ON/PN pelo prefixo de 4 letras (fica o de maior liquidez na janela).
"""
import logging

logger = logging.getLogger(__name__)

# COTAHIST TPMERC '010' = mercado À VISTA. Sem este filtro, prices_raw mistura
# opções (070/080) e termo (012/013) no universo — ~130k "tickers" que NÃO são
# ações investíveis (Red Team Achado 6). Filtra na fonte. NOTA DE ESCOPO: dentro
# do à vista ainda há BDR (bdi 34) e ETF — incluí-los ou não é decisão de
# estratégia (não um bug); por ora o universo à vista é completo.
SPOT_MARKET = "010"


def _median(xs):
    s = sorted(xs)
    n = len(s)
    if n == 0:
        return 0.0
    m = n // 2
    return s[m] if n % 2 else (s[m - 1] + s[m]) / 2.0


def rank_universe(conn, asof, lookback=126, min_history=252):
    """[(ticker, median_vol)] ranqueado por liquidez, POINT-IN-TIME (só dados < asof).

    min_history=252: mínimo de pregões de histórico exigido pelo design §5.
    Papéis em quarentena são excluídos por design §5 — dado quebrado não alimenta o fator.
    """
    # Point-in-time: só eventos de quarentena ANTERIORES a asof excluem o papel.
    # Um salto quarentenado no futuro não pode tocar a seleção de hoje (anti-lookahead).
    # resolved_at IS NULL: quarentena resolvida pelo humano (ajuste registrado) não exclui.
    quarantined = {r[0] for r in conn.execute(
        "SELECT DISTINCT ticker FROM quarantine WHERE date < ? AND resolved_at IS NULL",
        (asof,))}

    tickers = [r[0] for r in conn.execute(
                   "SELECT DISTINCT ticker FROM prices_raw WHERE market_type=?",
                   (SPOT_MARKET,))
               if r[0] not in quarantined]

    meds = {}
    for tk in tickers:
        vols = [r[0] for r in conn.execute(
            "SELECT volume_fin FROM prices_raw WHERE ticker=? AND date < ? "
            "AND market_type=? ORDER BY date",
            (tk, asof, SPOT_MARKET))]
        if len(vols) < min_history:
            continue
        meds[tk] = _median(vols[-lookback:])

    logger.debug("rank_universe asof=%s: %d tickers qualificados (de %d, %d quarentenados)",
                 asof, len(meds), len(tickers) + len(quarantined), len(quarantined))

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

    INSERT OR IGNORE: snapshots são imutáveis. Re-executar não sobrescreve o passado;
    para recalcular com código novo, use novo run_id (design §5).
    """
    ranked = rank_universe(conn, asof, lookback, min_history)[:top_n]
    for rank, (tk, med) in enumerate(ranked, 1):
        conn.execute(
            "INSERT OR IGNORE INTO universe_snapshots(asof_date,ticker,median_vol,rank) "
            "VALUES(?,?,?,?)", (asof, tk, med, rank))
    existing = conn.execute(
        "SELECT COUNT(*) FROM universe_snapshots WHERE asof_date=?", (asof,)).fetchone()[0]
    if existing > len(ranked):
        logger.warning("materialize_snapshot: snapshot de %s já existia — mantido intacto", asof)
    conn.commit()
    return [t for t, _ in ranked]