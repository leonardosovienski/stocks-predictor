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

Validação estatística (Prompt 3b):
    riskfree        série livre de risco versionada e retorno em excesso
    metrics         Sharpe em excesso, PSR, sensibilidade do DSR, t, beta/alpha
    factor_metrics  IC, Rank IC, ICIR, decaimento e quantis por rebalanceamento
    cpcv            CPCV com purge pelo intervalo real do rótulo e embargo derivado
    pbo             PBO por CSCV
    policy          política de decisão versionada (PASS / REJECT / NO_DECISION)
    validation      orquestração sob o ledger

Previsão e execução real (Prompt 3c):
    cotahist_dataset  dataset PIT v2 a partir de um COTAHIST local com hash (limitações declaradas)
    forecast_metrics  perda quantílica, CRPS por quantis, WQL, cobertura
    forecasting       tarefas PIT, baselines probabilísticos, previsões externas com proveniência, contaminação
    forecast_eval     execução sob o ledger e a política, com a tabela de entrega
"""

SCHEMA = "stocks-pit-dataset/2"

__all__ = ["SCHEMA"]
