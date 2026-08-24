"""8 famílias pré-registradas (config.yaml `families`) — condensam as 114
hipóteses do relatório de Fase 1 em métricas computáveis e testáveis, cada
uma com direção esperada declarada ANTES de qualquer rodada.

Regra estrita: cada família aqui é UMA métrica. Novas sub-hipóteses das 114
ficam guardadas como exploratórias (docs/DESIGN.md) mas NÃO entram como
testes independentes — é exatamente o problema de multiplicidade que o
protocolo resolve (114 hipóteses vs. ~19-40 casos = achado espúrio garantido).

Toda função é point-in-time: usa somente dados <= trough_date (o momento de
decisão hipotético). Nada após o fundo entra no cálculo do score — senão a
família estaria usando informação do próprio desfecho para "prever" o
desfecho (vazamento, não sinal).
"""
import statistics


def _closes_upto(dates, closes, asof):
    idx = [i for i, d in enumerate(dates) if d <= asof]
    return idx[-1] if idx else None


def drawdown(dates: list[str], closes: list[float], trough_date: str,
             pre_rj_high_date: str) -> float | None:
    """H1-H10 do banco original condensadas: 1 - preço_fundo / máxima pré-RJ.
    `pre_rj_high_date` é a data da máxima ANTES do pedido de RJ (fornecida
    pelo chamador a partir de rj_universe.rj_request_date — não recalculada
    aqui para não acoplar este módulo a I/O de banco)."""
    i_t = _closes_upto(dates, closes, trough_date)
    i_h = _closes_upto(dates, closes, pre_rj_high_date)
    if i_t is None or i_h is None or closes[i_h] <= 0:
        return None
    return 1.0 - closes[i_t] / closes[i_h]


def liquidity(volumes_fin: list[float], dates: list[str], trough_date: str,
              free_float_estimate: float, lookback: int = 60) -> float | None:
    """H11-H20 condensadas: giro diário mediano (60 pregões antes do fundo)
    sobre free float estimado. `free_float_estimate` vem de fonte externa
    (CVM/RI da companhia) — parâmetro explícito, não inferido aqui."""
    if free_float_estimate is None or free_float_estimate <= 0:
        return None
    idx = [i for i, d in enumerate(dates) if d < trough_date]
    if len(idx) < lookback:
        return None
    window = [volumes_fin[i] for i in idx[-lookback:]]
    return statistics.median(window) / free_float_estimate


def volume_dynamics(volumes_fin: list[float], dates: list[str], trough_date: str,
                     lookback: int = 20) -> float | None:
    """[DESCRITIVO, NÃO PREDITIVO — revisão externa, ponto 2] H21-H30
    condensadas: volume do PRÓPRIO dia do fundo sobre a mediana dos
    `lookback` pregões imediatamente anteriores. Caracteriza o fundo depois
    de sabermos que é o fundo — não é um sinal executável em tempo real,
    porque o dia D só é reconhecido como fundo olhando o futuro de D. Usar
    apenas no dataset descritivo (find_local_trough). Para a versão
    executável, ver `volume_dynamics_antecedent`."""
    idx = [i for i, d in enumerate(dates) if d <= trough_date]
    if len(idx) < lookback + 1:
        return None
    day_vol = volumes_fin[idx[-1]]
    prior = volumes_fin[idx[-1 - lookback]:idx[-1]]
    med = statistics.median(prior) if prior else 0.0
    if med <= 0:
        return None
    return day_vol / med


def volume_dynamics_antecedent(volumes_fin: list[float], dates: list[str], asof: str,
                                near: int = 5, far: int = 25) -> float | None:
    """[POINT-IN-TIME — dataset preditivo] Mediana de volume em D-near:D-1
    sobre mediana em D-far:D-near-1, ambas ANTES de `asof` (exclusive).
    Responde "o volume já começou a mudar antes de D?" sem usar nada de D
    em diante — a versão que a revisão externa pediu explicitamente
    (ponto 2): "median(volume D-5:D-1) / median(volume D-25:D-6)"."""
    idx = [i for i, d in enumerate(dates) if d < asof]
    if len(idx) < far:
        return None
    near_window = [volumes_fin[i] for i in idx[-near:]]
    far_window = [volumes_fin[i] for i in idx[-far:-near]]
    if not near_window or not far_window:
        return None
    med_far = statistics.median(far_window)
    if med_far <= 0:
        return None
    return statistics.median(near_window) / med_far


def rj_stage(trough_date: str, plan_presented_date: str | None,
             plan_approved_date: str | None, rj_end_date: str | None) -> str:
    """H31-H50 condensadas em estágio CATEGÓRICO no momento do fundo (revisão
    externa, ponto 4): 'requested'|'plan_presented'|'plan_approved'|'exited'.
    Deliberadamente NÃO um inteiro ordinal — estágio mais avançado não
    implica por construção maior chance de rally (a suposição de monotonia
    era injustificada). Testado por associação categórica em judge.py, não
    por diferença de médias."""
    stage = "requested"
    if plan_presented_date and trough_date >= plan_presented_date:
        stage = "plan_presented"
    if plan_approved_date and trough_date >= plan_approved_date:
        stage = "plan_approved"
    if rj_end_date and trough_date >= rj_end_date:
        stage = "exited"
    return stage


def ownership(events: list[dict], trough_date: str, window_days: int = 90) -> int:
    """H51-H60 condensadas: indicador binário — entrada de investidor >=5%
    CONHECIDA (rj_events.known_at, não event_date — revisão externa, ponto 7:
    um evento datado de 10/05 mas publicado em 11/05 não existia em 10/05)
    nos `window_days` corridos ANTES do fundo. `events` = lista de dicts já
    filtrada por ticker (evita acoplar este módulo a SQL)."""
    from datetime import date
    try:
        td = date.fromisoformat(trough_date)
    except ValueError:
        return 0
    for e in events:
        if e.get("event_type") != "investidor_5pct":
            continue
        known = e.get("known_at") or e.get("event_date")
        try:
            ed = date.fromisoformat(known)
        except (KeyError, TypeError, ValueError):
            continue
        if 0 <= (td - ed).days <= window_days:
            return 1
    return 0


def momentum_volatility(dates: list[str], closes: list[float], trough_date: str,
                         short: int = 60, long: int = 252) -> float | None:
    """H9-H10 e H101-H110 parcialmente condensadas: razão vol realizada curta
    sobre longa, medida ATÉ o fundo (não depois). <1 = compressão de
    volatilidade antes do fundo; direção esperada negativa (compressão
    precede rally, hipótese de 'calma antes da explosão')."""
    idx = [i for i, d in enumerate(dates) if d <= trough_date]
    if len(idx) < long + 1:
        return None
    series = [closes[i] for i in idx[-(long + 1):]]
    rets = [series[j] / series[j - 1] - 1.0 for j in range(1, len(series)) if series[j - 1] > 0]
    if len(rets) < long:
        return None
    vol_long = statistics.pstdev(rets)
    vol_short = statistics.pstdev(rets[-short:])
    if vol_long <= 0:
        return None
    return vol_short / vol_long


def time_since_rj(rj_request_date: str, trough_date: str, all_dates: list[str]) -> int | None:
    """H89-H100 condensadas: pregões ÚTEIS (não dias corridos) entre o pedido
    de RJ e o fundo. Direção esperada declarada como AMBÍGUA no config —
    o banco original tem H89 (logo após) e H92 (anos depois) competindo."""
    idx = [i for i, d in enumerate(all_dates) if rj_request_date <= d <= trough_date]
    return len(idx) - 1 if idx else None


def info_trigger(events: list[dict], trough_date: str, window_days: int = 10) -> int:
    """H31 (nova versão do plano) e o "gatilho informacional" da seção 11 do
    relatório original: indicador binário — fato relevante CONHECIDO
    (known_at, não event_date) nos `window_days` corridos ANTES do fundo."""
    from datetime import date
    try:
        td = date.fromisoformat(trough_date)
    except ValueError:
        return 0
    for e in events:
        if e.get("event_type") != "fato_relevante":
            continue
        known = e.get("known_at") or e.get("event_date")
        try:
            ed = date.fromisoformat(known)
        except (KeyError, TypeError, ValueError):
            continue
        if 0 <= (td - ed).days <= window_days:
            return 1
    return 0


# nome -> função, na mesma ordem/chaves do config.yaml `families`
REGISTRY = {
    "drawdown": drawdown,
    "liquidity": liquidity,
    "volume_dynamics_contemporaneous": volume_dynamics,
    "volume_dynamics_antecedent": volume_dynamics_antecedent,
    "rj_stage": rj_stage,   # CATEGÓRICO — judge.py trata via família separada
    "ownership": ownership,
    "momentum_volatility": momentum_volatility,
    "time_since_rj": time_since_rj,
    "info_trigger": info_trigger,
}

# famílias cujo valor é categórico (str), não numérico — judge.py precisa
# rotear para o teste de associação categórica em vez de diferença de médias.
CATEGORICAL_FAMILIES = {"rj_stage"}

# famílias DESCRITIVAS (revisão externa, 2ª rodada, ponto 1): computáveis e
# reportáveis, mas fora do conjunto de 8 testes PREDITIVOS que o FDR
# desconta — porque são medidas contemporaneamente ao candidato (só
# reconhecível como "o fundo" depois do fato), não executáveis em tempo
# real. Contá-las junto das preditivas no FDR faria o pré-registro dizer
# "8 famílias" enquanto o registry tinha 9 entradas — inconsistência
# corrigida aqui, não silenciada.
DESCRIPTIVE_ONLY_FAMILIES = {"volume_dynamics_contemporaneous"}

PREDICTIVE_FAMILIES = set(REGISTRY.keys()) - DESCRIPTIVE_ONLY_FAMILIES
assert len(PREDICTIVE_FAMILIES) == 8, (
    f"esperado exatamente 8 famílias preditivas, encontrado {len(PREDICTIVE_FAMILIES)} "
    f"— o pré-registro (DESIGN.md) declara '8 famílias'; se REGISTRY mudar, "
    "atualizar DESCRIPTIVE_ONLY_FAMILIES ou o número no DESIGN junto")
