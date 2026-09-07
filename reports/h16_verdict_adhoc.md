# predictor-stocks — Relatório do veredito da H16

- **run_id:** `n/d`
- **pregões pareados:** 2132
- **veredito H16:** **não comprovada (IC cruza 0 / negativo; DSR 0.0052 < 0.95)**

## Pedágio de 2 lentes

- **Lente 1 (PSR):** 0.0427  — P(Sharpe estratégia > Sharpe benchmark), corrige não-normalidade
- **Lente 2 (IC 95% da diferença de Sharpe, block bootstrap pareado, bloco 21):** [-1.4044, 0.2011]
  - H16 comprovada só se o IC não cruzar zero → CRUZA zero / negativo
- **Critério (ii) — DSR (Deflated Sharpe Ratio):** 0.0052 contra E[max SR | N=15] = 0.0308 por-período (mínimo pré-registrado: 0.95)

## Estratégia vs. benchmark (equiponderado do universo)

| métrica | estratégia | benchmark |
|---|---|---|
| Sharpe (anual.) | -0.3941 | 0.1981 |
| Sortino (anual.) | -0.5454 | 0.2698 |
| retorno total | -29.10% | 16.91% |
| max drawdown | 33.72% | 47.07% |

## Ressalvas registradas (não-negociáveis)

- Retorno **só-preço** (rota (b)): dividendos/JCP omitidos — irrelevante pro mecanismo desta hipótese (TIMING, não seleção de papel; estratégia e benchmark usam o MESMO universo, diferem só em quais dias contam o retorno). Custo simplificado: cobra 1 perna (`one_way`) em cada transição cash/posicionado, ignora turnover de composição do universo entre rebalances mensais (ver `backtest.run_h16`) — aproximação declarada, não escondida.
- Custo proporcional ao turnover real; execução na abertura de D+1.
- Veredito real da H16 exige COTAHIST **real** da B3 — sintético só valida a máquina.
