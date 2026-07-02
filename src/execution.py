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


def turnover(prev_weights, new_weights):
    """Fração da carteira TROCADA no rebalance: 1 − sobreposição de pesos.

    Primeira carteira (prev vazio) = 1.0 (compra tudo). Carteira idêntica = 0.0
    (nada a negociar, nada a pagar). O custo do rebalance = roundtrip × turnover —
    debitar o roundtrip inteiro todo mês assumiria giro de 100%, o que distorce a
    sensibilidade a custo (2×) exigida pelo design §7."""
    if not new_weights:
        return 0.0
    if not prev_weights:
        return 1.0
    overlap = sum(min(prev_weights.get(t, 0.0), w) for t, w in new_weights.items())
    return 1.0 - overlap


def net_return(entry_price, exit_price, fee_pct, slippage_pct):
    """Retorno LÍQUIDO de custos de uma posição comprada (backtest bruto é teatro)."""
    gross = exit_price / entry_price - 1.0
    return gross - roundtrip_cost(fee_pct, slippage_pct)
