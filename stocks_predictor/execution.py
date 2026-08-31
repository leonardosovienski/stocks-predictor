"""M4 — Modelo de execução e custos: abertura de D+1, custo ida-e-volta.

Sinal no fechamento de `asof`; execução na ABERTURA do primeiro pregão SEGUINTE (D+1).
Garante exec_ts > signal_ts — o invariante anti-lookahead capital.
"""


def next_open_after(dates, opens, signal_date):
    """(exec_date, exec_price) = abertura do PRIMEIRO pregão estritamente após
    signal_date. None se não houver D+1. exec_date > signal_date por construção."""
    for d, o in zip(dates, opens):
        if d > signal_date:
            return d, o
    return None


def roundtrip_cost(fee_pct, slippage_pct):
    """Custo total ida-e-volta (2 lados): 2 × (emolumentos+liquidação + spread/slippage)."""
    return 2.0 * (fee_pct + slippage_pct)


def one_way_cost(fee_pct, slippage_pct):
    """Custo por lado (entrada OU saída): emolumentos+liquidação + spread/slippage."""
    return fee_pct + slippage_pct


def calculate_turnover_cost(prev_port, curr_port, cost_per_side):
    """Custo de transação BRUTO (não-normalizado) proporcional ao turnover REAL entre
    dois rebalanceamentos: só posições que de fato entraram ou saíram pagam.

    ATENÇÃO (achado de revisão de código 2026-08-28): esta função retorna a contagem
    SOMADA (exits+entries) × cost_per_side, em unidades de "lado por posição" — NÃO é
    o arrasto pronto para somar ao retorno da carteira. Dividir esse total por um único
    denominador (ex.: `len(curr_port)`) foi exatamente o bug diagnosticado e corrigido no
    `backtest.py` (superestimava o custo das saídas quando a carteira encolhia e
    subestimava quando crescia). Para o arrasto NORMALIZADO e correto de uma carteira
    EQUIPONDERADA, use `equal_weight_turnover_cost` abaixo — não reimplemente a
    normalização aqui.

    prev_port / curr_port: conjuntos de tickers. cost_per_side = fee + slippage por lado.
    Carteira inicial (prev vazio): todas as posições entram => cobra entrada de cada uma.
    """
    prev_port, curr_port = set(prev_port), set(curr_port)
    exiting = len(prev_port - curr_port)
    entering = len(curr_port - prev_port)
    return (exiting + entering) * cost_per_side


def equal_weight_turnover_cost(prev_port, curr_port, cost_per_side):
    """Arrasto de turnover NORMALIZADO para carteira EQUIPONDERADA — o arrasto pronto
    para subtrair do retorno do período (não a contagem bruta de `calculate_turnover_cost`
    acima). Cada SAÍDA pesa 1/len(prev_port) (peso que ela tinha), cada ENTRADA pesa
    1/len(curr_port) (peso que ela passa a ter). Dividir tudo por um único denominador
    (bug histórico, ver `calculate_turnover_cost`) superestimava o custo das saídas
    quando a carteira encolhia e subestimava quando crescia.

    Carteira inicial (prev vazio): tudo é entrada => 1 × cost_per_side, independente do
    tamanho — mesma convenção de `weighted_turnover_cost`.
    """
    prev_port, curr_port = set(prev_port), set(curr_port)
    exits = len(prev_port - curr_port)
    entries = len(curr_port - prev_port)
    cost = entries * cost_per_side / len(curr_port) if curr_port else 0.0
    if prev_port:
        cost += exits * cost_per_side / len(prev_port)
    return cost


def weighted_turnover_cost(prev_weights, curr_weights, cost_per_side):
    """Custo de transação para carteiras PONDERADAS (H4): cada unidade de peso
    negociada paga um lado. turnover = Σ|w_novo − w_antigo| sobre a união dos
    tickers; carteira inicial (prev vazio, Σw=1) paga exatamente 1 × lado.

    É a generalização contínua de `calculate_turnover_cost` (que conta posições
    equiponderadas inteiras); retorna o ARRASTO direto sobre o retorno do
    período (já normalizado, pois os pesos somam 1)."""
    tickers = set(prev_weights) | set(curr_weights)
    turnover = sum(abs(curr_weights.get(t, 0.0) - prev_weights.get(t, 0.0))
                   for t in tickers)
    return turnover * cost_per_side


def net_return(entry_price, exit_price, fee_pct, slippage_pct):
    """Retorno LÍQUIDO de custos de uma posição comprada (backtest bruto é teatro)."""
    if entry_price <= 0:
        raise ValueError(f"entry_price inválido: {entry_price}")
    gross = exit_price / entry_price - 1.0
    return gross - roundtrip_cost(fee_pct, slippage_pct)
