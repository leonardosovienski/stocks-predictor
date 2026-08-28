# predictor-stocks — Relatório do veredito da H6

- **run_id:** `n/d`
- **pregões pareados:** 2131
- **veredito H6:** **não comprovada (IC cruza 0 / negativo; DSR 0.4565 < 0.95)**

## Pedágio de 2 lentes

- **Lente 1 (PSR):** 0.4898  — P(Sharpe estratégia > Sharpe benchmark), corrige não-normalidade
- **Lente 2 (IC 95% da diferença de Sharpe, block bootstrap pareado, bloco 21):** [-0.3526, 0.3256]
  - H6 comprovada só se o IC não cruzar zero → CRUZA zero / negativo
- **Critério (ii) — DSR (Deflated Sharpe Ratio):** 0.4565 contra E[max SR | N=6] = 0.0137 por-período (mínimo pré-registrado: 0.95)

## Estratégia vs. benchmark (equiponderado do universo)

| métrica | estratégia | benchmark |
|---|---|---|
| Sharpe (anual.) | 0.1802 | 0.1891 |
| Sortino (anual.) | 0.2414 | 0.2570 |
| retorno total | 11.03% | 14.51% |
| max drawdown | 49.65% | 48.26% |

## Ressalvas registradas (não-negociáveis)

- Retorno **só-preço** (rota (b)): dividendos/JCP omitidos; papéis de momentum tendem a MENOR yield, logo o viés FAVORECE a estratégia de momentum 6-1 contra o benchmark — mesma direção e racional da H1 (não fixado explicitamente no pré-registro original da H6; nota técnica adicionada na revisão de código de 2026-08-28).
- Custo proporcional ao turnover real; execução na abertura de D+1.
- Veredito real da H6 exige COTAHIST **real** da B3 — sintético só valida a máquina.
