# predictor-stocks — Relatório do veredito da H14

- **run_id:** `n/d`
- **pregões pareados:** 2131
- **veredito H14:** **não comprovada (IC cruza 0 / negativo; DSR 0.3249 < 0.95)**

## Pedágio de 2 lentes

- **Lente 1 (PSR):** 0.5800  — P(Sharpe estratégia > Sharpe benchmark), corrige não-normalidade
- **Lente 2 (IC 95% da diferença de Sharpe, block bootstrap pareado, bloco 21):** [-0.2424, 0.3864]
  - H14 comprovada só se o IC não cruzar zero → CRUZA zero / negativo
- **Critério (ii) — DSR (Deflated Sharpe Ratio):** 0.3249 contra E[max SR | N=13] = 0.0263 por-período (mínimo pré-registrado: 0.95)

## Estratégia vs. benchmark (equiponderado do universo)

| métrica | estratégia | benchmark |
|---|---|---|
| Sharpe (anual.) | 0.2591 | 0.1891 |
| Sortino (anual.) | 0.3494 | 0.2570 |
| retorno total | 31.01% | 14.51% |
| max drawdown | 38.78% | 48.26% |

## Ressalvas registradas (não-negociáveis)

- Retorno **só-preço** (rota (b)): dividendos/JCP omitidos; papel próximo da máxima de 52 semanas tende a ter yield mais BAIXO (preço subiu recentemente), na mesma direção do viés já declarado no pré-registro da H1 pra momentum — mecanismo semelhante, não quantificado aqui separadamente.
- Custo proporcional ao turnover real; execução na abertura de D+1.
- Veredito real da H14 exige COTAHIST **real** da B3 — sintético só valida a máquina.
