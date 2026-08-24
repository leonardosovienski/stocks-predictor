"""Outcomes auxiliares e validação walk-forward do domínio RJ.

1. `market_adjusted_rally`: outcome AUXILIAR (não é o outcome primário nem o
   secundário, ambos congelados em config_rj.yaml): excesso de retorno sobre
   o índice >= threshold dentro da janela. Um +50% absoluto num mês em que o
   Ibovespa subiu 40% não é o fenômeno especulativo idiossincrático que o
   estudo quer isolar. Reportado junto, nunca fundido — misturá-lo com o
   outcome congelado seria nova hipótese sem pré-registro.

2. `walk_forward_splits`: esquema de validação para a fase em que existir
   MODELO (hoje há só comparação de médias — LOCO já mede influência, e o
   próprio judge documenta que LOCO não é validação preditiva). Expanding
   window: treina em [0, t), testa em [t, t+step) — nunca o contrário, e a
   fronteira é sempre em datas conhecidas no momento da decisão.
"""


def market_adjusted_rally(dates: list[str], closes: list[float],
                          index_dates: list[str], index_closes: list[float],
                          trough_date: str, threshold_pct: float,
                          max_window_trading_days: int) -> dict:
    """Primeiro dia em que (retorno do papel desde o fundo) - (retorno do
    índice desde o fundo) >= threshold_pct, dentro da janela. Alinha índice
    por DATA (pregões do papel que não existem no índice são ignorados —
    melhor que interpolar e fabricar retorno de benchmark)."""
    idx_map = {d: i for i, d in enumerate(index_dates)}
    if trough_date not in dates or trough_date not in idx_map:
        return {"outcome": "index_unavailable", "excess_pct": None,
                "date": None, "trading_days": None}
    t0 = dates.index(trough_date)
    i0 = idx_map[trough_date]
    if closes[t0] <= 0 or index_closes[i0] <= 0:
        return {"outcome": "index_unavailable", "excess_pct": None,
                "date": None, "trading_days": None}
    limit = min(len(dates), t0 + 1 + max_window_trading_days)
    for i in range(t0 + 1, limit):
        d = dates[i]
        if d not in idx_map:
            continue
        stock_ret = closes[i] / closes[t0] - 1.0
        idx_ret = index_closes[idx_map[d]] / index_closes[i0] - 1.0
        excess = stock_ret - idx_ret
        if excess >= threshold_pct:
            return {"outcome": "rally_market_adjusted", "excess_pct": excess,
                    "date": d, "trading_days": i - t0}
    return {"outcome": "no_market_adjusted_rally", "excess_pct": None,
            "date": None, "trading_days": None}


def walk_forward_splits(n_obs: int, min_train: int, step: int):
    """Gera (train_range, test_range) de índices em expanding window.

    Invariante temporal: todo índice de teste é ESTRITAMENTE posterior a todo
    índice de treino, e o treino nunca encolhe (expanding, não rolling — o
    conhecimento acumulado não é esquecido). Útil quando houver modelo; hoje
    serve para definir a mecânica da validação futura sem lookahead."""
    start = min_train
    while start < n_obs:
        end = min(start + step, n_obs)
        yield range(0, start), range(start, end)
        start = end


def walk_forward_evaluate(units, fit_fn, score_fn, min_train: int = 10,
                          step: int = 5) -> list[dict]:
    """Avaliação walk-forward genérica: `fit_fn(train_units) -> model`,
    `score_fn(model, test_units) -> float` (métrica escolhida pelo chamador,
    ex.: AUC ou correlação ranqueada). `units` DEVE estar ordenado no tempo —
    a recusa de embaralhar é a proteção anti-lookahead estrutural. Se as
    units carregam campo de data (dicts com chave "date", ou tuplas cujo
    1º elemento é uma data ISO), a monotonicidade é VERIFICADA (fail-closed:
    ValueError); sem campo de data, o contrato de ordenação é do chamador
    (documentado aqui, não verificável)."""
    dates = None
    if units and isinstance(units[0], dict) and "date" in units[0]:
        dates = [u["date"] for u in units]
    elif (units and isinstance(units[0], (tuple, list)) and units[0]
            and isinstance(units[0][0], str) and len(units[0][0]) == 10
            and units[0][0][4] == "-"):
        dates = [u[0] for u in units]
    if dates is not None and any(b < a for a, b in zip(dates, dates[1:])):
        raise ValueError(
            "units fora de ordenação temporal — walk-forward exige sequência "
            "monotônica não-decrescente de datas (anti-lookahead)")
    results = []
    for train, test in walk_forward_splits(len(units), min_train, step):
        model = fit_fn([units[i] for i in train])
        score = score_fn(model, [units[i] for i in test])
        results.append({"train_end": train.stop, "test_size": len(test),
                        "score": score})
    return results
