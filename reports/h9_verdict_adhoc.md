# predictor-stocks — Relatório do veredito da H9

- **run_id:** `n/d`
- **pregões pareados:** 1826
- **veredito H9:** **não comprovada (IC cruza 0 / negativo; DSR 0.3479 < 0.95)**

## Pedágio de 2 lentes

- **Lente 1 (PSR):** 0.3987  — P(Sharpe estratégia > Sharpe benchmark), corrige não-normalidade
- **Lente 2 (IC 95% da diferença de Sharpe, block bootstrap pareado, bloco 21):** [-0.3724, 0.1602]
  - H9 comprovada só se o IC não cruzar zero → CRUZA zero / negativo
- **Critério (ii) — DSR (Deflated Sharpe Ratio):** 0.3479 contra E[max SR | N=8] = 0.0143 por-período (mínimo pré-registrado: 0.95)

## Estratégia vs. benchmark (equiponderado do universo)

| métrica | estratégia | benchmark |
|---|---|---|
| Sharpe (anual.) | 0.0810 | 0.1766 |
| Sortino (anual.) | 0.1104 | 0.2391 |
| retorno total | -8.01% | 9.45% |
| max drawdown | 46.91% | 48.26% |

## Ressalvas registradas (não-negociáveis)

- Retorno **só-preço** (rota (b)): dividendos/JCP omitidos; SEM direção declarada a priori — mesma limitação da H7 (a relação entre baixa alavancagem e política de dividendos de empresas B3 não foi estabelecida nesta rodada; empresa pouco endividada poderia distribuir mais OU menos, sem prior claro). Viés não quantificado, registrado como limitação honesta (declarado no pré-registro da H9, 2026-09-04) — não inferir sinal. Mesmo embargo de divulgação de 90 dias sobre `ref_date` da H7 (`h9_factor.disclosure_embargo_days`, mesma fonte DFP/CVM), mesma limitação de não cobrir a data REAL de entrega à CVM.
- Custo proporcional ao turnover real; execução na abertura de D+1.
- Veredito real da H9 exige COTAHIST **real** da B3 — sintético só valida a máquina.
