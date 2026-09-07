# predictor-stocks — Relatório do veredito da H15

- **run_id:** `n/d`
- **pregões pareados:** 2131
- **veredito H15:** **não comprovada (IC cruza 0 / negativo; DSR 0.2826 < 0.95)**

## Pedágio de 2 lentes

- **Lente 1 (PSR):** 0.5228  — P(Sharpe estratégia > Sharpe benchmark), corrige não-normalidade
- **Lente 2 (IC 95% da diferença de Sharpe, block bootstrap pareado, bloco 21):** [-0.2527, 0.3129]
  - H15 comprovada só se o IC não cruzar zero → CRUZA zero / negativo
- **Critério (ii) — DSR (Deflated Sharpe Ratio):** 0.2826 contra E[max SR | N=14] = 0.0257 por-período (mínimo pré-registrado: 0.95)

## Estratégia vs. benchmark (equiponderado do universo)

| métrica | estratégia | benchmark |
|---|---|---|
| Sharpe (anual.) | 0.2090 | 0.1891 |
| Sortino (anual.) | 0.2796 | 0.2570 |
| retorno total | 18.71% | 14.51% |
| max drawdown | 50.56% | 48.26% |

## Ressalvas registradas (não-negociáveis)

- Retorno **só-preço** (rota (b)): dividendos/JCP omitidos; SEM direção declarada a priori — a relação entre surto de volume e política de dividendos de empresas B3 não foi estabelecida nesta rodada. Viés não quantificado, registrado como limitação honesta (declarado no pré-registro da H15, 2026-09-04) — não inferir sinal.
- Custo proporcional ao turnover real; execução na abertura de D+1.
- Veredito real da H15 exige COTAHIST **real** da B3 — sintético só valida a máquina.
