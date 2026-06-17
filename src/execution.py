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


def net_return(entry_price, exit_price, fee_pct, slippage_pct):
    """Retorno LÍQUIDO de custos de uma posição comprada (backtest bruto é teatro)."""
    gross = exit_price / entry_price - 1.0
    return gross - roundtrip_cost(fee_pct, slippage_pct)
