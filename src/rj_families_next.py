"""Famílias NEXT-GEN do domínio RJ — NÃO pré-registradas.

Origem: literatura de distressed/lottery stocks (Campbell-Hilscher-Szilagyi
2008; Bali-Cakici-Whitelaw MAX; Coelho-John-Taffler sobre base acionária de
falidas; "MAX on Steroids" sobre emissão de ações) — ver relatório de
revisão 2026-08-24.

REGRA INVIOLÁVEL: estas famílias NÃO entram no FDR das 8 pré-registradas
(`families.PREDICTIVE_FAMILIES`). São computadas e reportadas como
EXPLORATÓRIAS — candidatas a um NOVO pré-registro (nova rodada, nova
hipótese), jamais somadas à rodada vigente retroativamente. O assert no fim
do módulo garante a disjunção em código, mesmo padrão do assert das 8.

Todas são point-in-time: somente dados <= asof (ou filtrados por known_at).
"""
import statistics

NEXT_GEN_DIRECTIONS = {
    "max_lottery": "positive",        # apetite por loteria pré-fundo -> rally
    "equity_issuance": "ambiguous",   # diluição financia rally mas destrói valor
    "retail_migration": "positive",   # base migrando p/ pessoa física -> rally
    "altman_z": "negative",           # distress contábil maior (Z menor) -> ?
    "chs_nimta": "negative",          # NI/MTA mais negativo -> mais distress
}


def _returns_before(dates: list[str], closes: list[float], asof: str,
                    window: int) -> list[float]:
    """Retornos diários dos `window` pregões estritamente ANTES de asof."""
    idx = [i for i, d in enumerate(dates) if d < asof]
    if len(idx) < window + 1:
        return []
    j = idx[-1]
    rets = []
    for i in range(max(1, j - window + 1), j + 1):
        if closes[i - 1] > 0:
            rets.append(closes[i] / closes[i - 1] - 1.0)
    return rets


def max_lottery(dates: list[str], closes: list[float], asof: str,
                k: int = 5, window: int = 21) -> float | None:
    """MAX de Bali-Cakici-Whitelaw adaptado: média dos `k` maiores retornos
    diários dos `window` pregões antes de asof. Proxy do apetite especulativo
    recente no papel — mensurável em tempo real, ao contrário de reconhecer
    o rally depois dele."""
    rets = _returns_before(dates, closes, asof, window)
    if len(rets) < k:
        return None
    return statistics.mean(sorted(rets, reverse=True)[:k])


def equity_issuance(events: list[dict], trough_date: str,
                    window_days: int = 180) -> int | None:
    """Binário: emissão de ações / aumento de capital CONHECIDO (known_at)
    nos `window_days` corridos antes do fundo. "MAX on Steroids" (2026)
    mostrou que retornos extremos concentrados carregam emissão junto —
    separar isso de fato_relevante genérico é o refinamento que a família
    info_trigger original não faz.

    Fail-closed informacional (mesma regra do pré-registro §8/§10): evento
    sem known_at válido não é elegível — event_date nunca substitui known_at.
    trough_date inválida -> None (indisponível), nunca 0."""
    from datetime import date
    try:
        td = date.fromisoformat(trough_date)
    except (TypeError, ValueError):
        return None
    kinds = {"emissao_acoes", "aumento_capital", "oferta_acoes"}
    for e in events:
        if e.get("event_type") not in kinds:
            continue
        known = e.get("known_at")
        if not known:
            continue    # sem known_at válido o evento não é elegível
        try:
            ed = date.fromisoformat(known)
        except (TypeError, ValueError):
            continue
        if 0 <= (td - ed).days <= window_days:
            return 1
    return 0


def retail_migration(ownership_snapshots: list[dict], trough_date: str,
                     pre_rj_date: str) -> float | None:
    """Delta da participação de pessoa física: snapshot mais recente ANTES do
    fundo menos o mais recente ANTES do pedido de RJ (ambos point-in-time,
    ex.: FREs da CVM). Positivo = base migrando para retail — o combustível
    documentado por Coelho-John-Taffler (>90% retail pós-filing nos EUA).

    ownership_snapshots: [{"ref_date": ..., "pct_retail": 0..1}], já do
    ticker certo. Sem snapshot em alguma das duas pontas: None (não inventa).
    """
    before_rj = [s for s in ownership_snapshots
                 if s.get("ref_date") and s["ref_date"] < pre_rj_date
                 and s.get("pct_retail") is not None]
    before_trough = [s for s in ownership_snapshots
                     if s.get("ref_date") and pre_rj_date <= s["ref_date"] < trough_date
                     and s.get("pct_retail") is not None]
    if not before_rj or not before_trough:
        return None
    a = max(before_rj, key=lambda s: s["ref_date"])["pct_retail"]
    b = max(before_trough, key=lambda s: s["ref_date"])["pct_retail"]
    return b - a


def altman_z(financials: dict) -> float | None:
    """Z-Score clássico (1968) — distress contábil medido no ÚLTIMO
    demonstrativo publicado (o chamador garante known_at: passar só números
    de DFP/ITR já entregues à CVM antes de asof).

    financials: working_capital, retained_earnings, ebit, equity_value
    (valor de mercado do equity; o valor contábil é fallback declarado pelo
    chamador), total_liabilities, sales, total_assets.
    Falta qualquer componente: None — nunca imputa zero (zero fabricaria
    distress artificial; ver rj_coda para tratamento explícito de zeros)."""
    keys = ("working_capital", "retained_earnings", "ebit",
            "equity_value", "total_liabilities", "sales", "total_assets")
    if any(financials.get(k) is None for k in keys):
        return None
    ta = financials["total_assets"]
    if not ta or financials["total_liabilities"] == 0:
        return None
    x1 = financials["working_capital"] / ta
    x2 = financials["retained_earnings"] / ta
    x3 = financials["ebit"] / ta
    x4 = financials["equity_value"] / financials["total_liabilities"]
    x5 = financials["sales"] / ta
    return 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 1.0 * x5


def chs_nimta(financials: dict) -> float | None:
    """NIMTA de Campbell-Hilscher-Szilagyi: lucro líquido / ativo total de
    mercado (MTA ≈ passivo + valor de mercado do equity). Mais negativo =
    maior distress. Mesma disciplina de known_at do altman_z."""
    ni = financials.get("net_income")
    tl = financials.get("total_liabilities")
    eq = financials.get("equity_value")
    if ni is None or tl is None or eq is None:
        return None
    mta = tl + eq
    if mta is None or mta <= 0:
        # MTA <= 0 (equity de mercado negativo o suficiente) inverte o sinal
        # da razão — distress maior pareceria "melhor". Indisponível, não
        # número distorcido.
        return None
    return ni / mta


NEXT_GEN_REGISTRY = {
    "max_lottery": max_lottery,
    "equity_issuance": equity_issuance,
    "retail_migration": retail_migration,
    "altman_z": altman_z,
    "chs_nimta": chs_nimta,
}

# disjunção com o pré-registro vigente, travada em código (mesmo padrão do
# assert das 8 famílias): se alguém mover uma família entre módulos sem novo
# pré-registro, o import quebra na hora, não depois do resultado.
import rj_families as _preregistered  # noqa: E402

_overlap = set(NEXT_GEN_REGISTRY) & set(_preregistered.REGISTRY)
assert not _overlap, (
    f"família(s) {_overlap} em AMBOS os registries — next-gen não pode "
    "colidir com as pré-registradas sem novo pré-registro formal")
