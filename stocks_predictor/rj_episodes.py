"""Detecção de episódios: fundo local -> outcome (rally | censurado | sem rally).

Implementa a definição CANÔNICA única do protocolo (config.yaml `rally`):
fechamento ajustado -> fechamento ajustado, dentro de uma janela máxima a
partir do fundo. Sem isso, cada caso do relatório original usava uma régua
diferente (PMAM3 intraday, AMER3 fechamento) — não comparável entre si.

DOIS DATASETS DISTINTOS (correção de 2026-08-23, revisão externa):

1. `find_local_trough` (EX-POST): escolhe a mínima OLHANDO A SÉRIE INTEIRA da
   janela de observação. Válido para descrever o fenômeno retrospectivamente
   ("o que caracterizou o fundo desses episódios?") — mas contém lookahead:
   se a série faz R$3→R$2→R$2,50→R$1→R$1,40→R$1,60, só sabemos que R$1 foi
   "o fundo" depois de ver R$1,40 e R$1,60 acontecerem. Não é executável em
   tempo real.

2. `point_in_time_candidates` (PREDITIVO): em cada `asof` D, pergunta "D é um
   candidato a fundo usando SOMENTE dados <= D?" — D entra como candidato se
   for a mínima de uma janela retroativa fixa terminando em D (backward-only).
   Nenhuma informação de D+1 em diante participa da decisão de que D é
   candidato. Este é o dataset que qualquer família/feature "antecedente"
   deve consumir se a pergunta for "dá para prever antes?".

As famílias contemporâneas (medidas NO candidato, ex.: volume do próprio dia)
continuam válidas para o dataset (1) — descrever o fundo — mas não podem
alimentar um modelo que se pretenda executável, porque o candidato só é
confirmado como "o" fundo depois do fato. Ver `families.py` para a versão
antecedente correspondente.

Regra de censura POR EPISÓDIO (protocolo, risco #3, IMPLEMENTADA aqui): um
episódio só entra no grupo "sem rally" se sua janela de observação — desde
o FUNDO até `rally.primary_window_trading_days`/`secondary_window_trading_days`
pregões depois, OU até hoje (o que vier primeiro) — já COMPLETOU a janela
(ver `classify_episode`). Episódio recente demais não teve tempo de
"falhar" — fica marcado `censored`, fora do grupo controle definitivo.

Regra de censura POR EMPRESA (`docs/RJ_DESIGN.md` §5): empresas sem candidato
ficam em `rj_company_observations`. Antes de completar
`censoring_horizon_trading_days` são `censored`; depois são
`no_candidate_control`. Nunca se fabrica um trough para representá-las.
"""


def find_local_trough(dates: list[str], closes: list[float],
                       start_date: str, end_date: str | None = None) -> tuple[str, float] | None:
    """[EX-POST — dataset descritivo, não preditivo] Mínima da série ajustada
    em [start_date, end_date). Olha a janela INTEIRA para decidir o fundo —
    contém lookahead por construção. Usar apenas para caracterizar episódios
    já ocorridos, nunca como gatilho de decisão simulada em tempo real."""
    idxs = [i for i, d in enumerate(dates)
            if d >= start_date and (end_date is None or d < end_date)]
    if not idxs:
        return None
    j = min(idxs, key=lambda i: closes[i])
    return dates[j], closes[j]


def point_in_time_candidates(dates: list[str], closes: list[float],
                              rj_request_date: str, backward_lookback: int = 40) -> list[str]:
    """[POINT-IN-TIME — dataset preditivo] Datas D tais que close[D] é a
    mínima da janela [D-backward_lookback, D] — usando SOMENTE dados <= D.

    Exige JANELA COMPLETA (revisão externa, ponto 2 da segunda rodada): sem
    isso, o 1º pregão pós-RJ é candidato trivial (janela de 1 ponto = mínimo
    de si mesmo), o 2º também se cair, etc. — uma enxurrada de "fundos"
    causada só pela empresa ter acabado de entrar no universo, não por
    nenhuma propriedade real da série. Um candidato só é gerado a partir do
    pregão em que já existem `backward_lookback` pregões de histórico DESDE
    o pedido de RJ (`i - idx_rj >= backward_lookback`).

    Cada D retornado é um candidato a fundo "conhecível no próprio dia D",
    sem olhar o que acontece depois. Isso pode gerar VÁRIOS candidatos por
    empresa — a escolha do episódio PRIMÁRIO entre eles é regra separada e
    independente do outcome (ver `select_primary_episode`), nunca decidida
    reolhando qual candidato "deu certo"."""
    idx_rj = next((i for i, d in enumerate(dates) if d >= rj_request_date), None)
    if idx_rj is None:
        return []
    candidates = []
    for i in range(idx_rj, len(dates)):
        if i - idx_rj < backward_lookback:
            continue    # janela incompleta — não é candidato válido ainda
        lo = i - backward_lookback
        window = closes[lo:i + 1]
        if window and closes[i] == min(window):
            candidates.append(dates[i])
    return candidates


def select_primary_episode(candidates: list[str]) -> str | None:
    """Regra de seleção do episódio PRIMÁRIO (revisão externa, ponto 3):
    o PRIMEIRO candidato cronologicamente — critério fixado a priori,
    totalmente independente de qual candidato eventualmente teve rally.
    Escolher com base em "qual deu certo" reintroduziria lookahead pela
    porta dos fundos (o próprio problema que a separação ex-post/preditivo
    resolveu). None se não houver candidato."""
    return candidates[0] if candidates else None


def select_secondary_episodes(candidates: list[str], all_dates: list[str],
                               min_separation_trading_days: int) -> list[str]:
    """Candidatos SECUNDÁRIOS (protocolo empresa->episódios): a partir do
    primário, mantém um candidato subsequente só se estiver a pelo menos
    `min_separation_trading_days` pregões do último candidato mantido —
    evita contar como "episódios distintos" uma sequência de mínimas locais
    que são na prática o mesmo movimento (regra fixada a priori, não
    depende do outcome de nenhum candidato)."""
    if not candidates:
        return []
    idx_of = {d: i for i, d in enumerate(all_dates)}
    kept = [candidates[0]]
    for c in candidates[1:]:
        if idx_of[c] - idx_of[kept[-1]] >= min_separation_trading_days:
            kept.append(c)
    return kept



def first_rally_after_trough(dates: list[str], closes: list[float],
                              trough_idx: int, threshold_pct: float,
                              max_window_trading_days: int) -> tuple[str, float, int] | None:
    """Primeiro fechamento >= trough*(1+threshold) dentro da janela máxima
    (em PREGÕES, não dias corridos — evita ambiguidade de feriado/fim de
    semana). Retorna (data, ganho_realizado, pregões_decorridos) ou None se
    não ocorreu dentro da janela."""
    trough_price = closes[trough_idx]
    if trough_price <= 0:
        return None
    target = trough_price * (1.0 + threshold_pct)
    limit = min(len(dates), trough_idx + 1 + max_window_trading_days)
    for i in range(trough_idx + 1, limit):
        if closes[i] >= target:
            return dates[i], closes[i] / trough_price - 1.0, i - trough_idx
    return None


def classify_episode(dates: list[str], closes: list[float], trough_date: str,
                      cfg: dict, asof_today: str, window_key: str = "primary_window_trading_days") -> dict:
    """Classifica UM episódio (fundo já identificado) em outcome + campos de
    `episodes`. `asof_today` é a data de corte da observação — necessária
    para decidir censura vs. "sem rally definitivo" (protocolo §3 da crítica).
    `window_key` seleciona qual janela do config usar (primária 60 pregões
    ou secundária 252) — outcome de +50% em janela larga mistura rally
    explosivo com deriva lenta de 11 meses (revisão externa, ponto 3);
    ambas são calculadas e guardadas separadamente, nunca fundidas.

    Regra de censura (limpa na 2ª revisão — variável morta `window_closed`
    removida): a janela está COMPLETA sse existem `max_window` pregões de
    preço DEPOIS do fundo na série (`trough_idx + max_window <= len(dates)-1`).
    Só então "sem rally dentro da janela" vira outcome definitivo
    (`no_rally_observed`); caso contrário é `censored` — não sabemos ainda,
    não é "nunca". `dates` deve, por contrato do chamador, não se estender
    além de `asof_today` (a série de preço já é truncada em hoje) — o assert
    abaixo torna esse contrato fail-closed: uma série que se estende além do
    corte é lookahead estrutural, não detalhe de implementação.

    Preço de fundo <= 0 é dado QUEBRADO (pregão corrompido), não "empresa
    que não teve rally": o outcome é `invalid_data` e o episódio deve ser
    contabilizado como excluído/missing pelo chamador — NUNCA como controle
    (`no_rally_observed` fabricaria denominador falso no judge)."""
    # `assert` seria removido com -O/PYTHONOPTIMIZE, apagando este guard
    # anti-lookahead estrutural em produção (achado de revisão de código
    # 2026-08-28) — usa raise explícito, nunca stripado pelo interpretador.
    if dates and dates[-1] > asof_today:
        raise AssertionError(
            f"série estende além do asof ({dates[-1]} > {asof_today}) — "
            "lookahead estrutural; truncar a série no chamador")
    rcfg = cfg["rally"]
    max_window = rcfg[window_key]
    trough_idx = dates.index(trough_date)
    if closes[trough_idx] <= 0:
        return {"outcome": "invalid_data", "rally_pct": None,
                "rally_date": None, "trading_days_to_rally": None,
                "censored": 0}
    hit = first_rally_after_trough(
        dates, closes, trough_idx, rcfg["threshold_pct"], max_window)
    if hit is not None:
        rally_date, rally_pct, td = hit
        return {"outcome": "rally", "rally_pct": rally_pct,
                "rally_date": rally_date, "trading_days_to_rally": td,
                "censored": 0}

    window_end_idx = trough_idx + max_window
    if window_end_idx <= len(dates) - 1:
        return {"outcome": "no_rally_observed", "rally_pct": None,
                "rally_date": None, "trading_days_to_rally": None,
                "censored": 0}
    return {"outcome": "censored", "rally_pct": None, "rally_date": None,
            "trading_days_to_rally": None, "censored": 1}
