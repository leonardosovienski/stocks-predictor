"""M4 — Modelo de execução e custos: abertura de D+1, custo ida-e-volta.

Sinal no fechamento de `asof`; execução na ABERTURA do primeiro pregão SEGUINTE (D+1).
Garante exec_ts > signal_ts — o invariante anti-lookahead capital.
"""
import logging

logger = logging.getLogger(__name__)

_MAX_GAP_WARN = 3  # pregões — gap maior que isso é logado como anomalia de liquidez


def next_open_after(dates, opens, signal_date):
    """(exec_date, exec_price, gap_days) = abertura do PRIMEIRO pregão estritamente após
    signal_date. None se não houver D+1. exec_date > signal_date por construção.

    gap_days = posição do pregão encontrado na lista (1 = D+1 normal). Valores > 3
    indicam suspensão ou baixa liquidez — logados como warning para auditoria.
    """
    for gap, (d, o) in enumerate(zip(dates, opens), start=0):
        if d > signal_date:
            if gap > _MAX_GAP_WARN:
                logger.warning("gap de liquidez: %d pregões até exec após %s", gap, signal_date)
            return d, o, gap
    return None


def roundtrip_cost(fee_pct, slippage_pct):
    """Custo total ida-e-volta (2 lados): 2 × (emolumentos+liquidação + spread/slippage)."""
    return 2.0 * (fee_pct + slippage_pct)


def one_way_cost(fee_pct, slippage_pct):
    """Custo por lado (entrada OU saída): emolumentos+liquidação + spread/slippage."""
    return fee_pct + slippage_pct


def calculate_turnover_cost(prev_port, curr_port, cost_per_side):
    """Custo de transação proporcional ao turnover REAL entre dois rebalanceamentos.

    SÓ posições que de fato entraram ou saíram pagam — papéis que permanecem na carteira
    não geram operação, logo custo zero. Blinda contra a fraude clássica de cobrar custo
    sobre o portfólio inteiro (que subestima high-turnover e superestima buy-and-hold).

    prev_port / curr_port: conjuntos de tickers. cost_per_side = fee + slippage por lado.
    Retorna o custo SOMADO em unidades de "lado por posição" — o chamador normaliza pelo
    peso (1/n) para obter o arrasto sobre o retorno equiponderado do portfólio.

    Carteira inicial (prev vazio): todas as posições entram => cobra entrada de cada uma.
    """
    prev_port, curr_port = set(prev_port), set(curr_port)
    exiting = len(prev_port - curr_port)
    entering = len(curr_port - prev_port)
    return (exiting + entering) * cost_per_side


def net_return(entry_price, exit_price, fee_pct, slippage_pct):
    """Retorno LÍQUIDO de custos de uma posição comprada (backtest bruto é teatro)."""
    if entry_price <= 0:
        raise ValueError(f"entry_price inválido: {entry_price}")
    gross = exit_price / entry_price - 1.0
    return gross - roundtrip_cost(fee_pct, slippage_pct)
