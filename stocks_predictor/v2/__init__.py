"""Protocolo de avaliação v2 (aditivo): dados point-in-time, execução explícita, custos, baselines,
walk-forward e manifesto por execução.

Nada aqui altera os motores legados (`backtest.legacy_walk_forward`, `simulation.walk_forward`) nem o
circuito de pesquisa qualificado (`research_*`); vereditos congelados continuam reproduzíveis byte a byte.

Módulos:
    dataset      PITDataset / PITView — só o que era conhecido no instante da decisão
    execution    ExecutionConvention — sinal até o fechamento de D, execução em D+lag (lag >= 1)
    costs        CostModel / LiquidityRule — corretagem, emolumentos, spread, slippage, impacto vs ADV, aluguel
    engine       ProtocolConfig / run_backtest — carteira por quantidades, caixa, custos, eventos
    baselines    EW do universo, buy-and-hold do índice, momentum 12-1, carteiras aleatórias, forecast ingênuo
    walkforward  splits temporais com separação estrita (horizonte + embargo)
    manifest     RunManifest / TrialLedger — toda execução avaliativa registrada, append-only
"""

SCHEMA = "stocks-pit-dataset/2"

__all__ = ["SCHEMA"]
