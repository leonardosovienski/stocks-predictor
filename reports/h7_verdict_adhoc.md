# predictor-stocks — Relatório do veredito da H7

- **run_id:** `n/d`
- **pregões pareados:** 1826
- **veredito H7:** **não comprovada (IC cruza 0 / negativo; DSR 0.5795 < 0.95)**

## Pedágio de 2 lentes

- **Lente 1 (PSR):** 0.6325  — P(Sharpe estratégia > Sharpe benchmark), corrige não-normalidade
- **Lente 2 (IC 95% da diferença de Sharpe, block bootstrap pareado, bloco 21):** [-0.2149, 0.4724]
  - H7 comprovada só se o IC não cruzar zero → CRUZA zero / negativo
- **Critério (ii) — DSR (Deflated Sharpe Ratio):** 0.5795 contra E[max SR | N=7] = 0.0144 por-período (mínimo pré-registrado: 0.95)

## Estratégia vs. benchmark (equiponderado do universo)

| métrica | estratégia | benchmark |
|---|---|---|
| Sharpe (anual.) | 0.3032 | 0.1766 |
| Sortino (anual.) | 0.4230 | 0.2391 |
| retorno total | 36.35% | 9.45% |
| max drawdown | 44.16% | 48.26% |

## Ressalvas registradas (não-negociáveis)

- Retorno **só-preço** (rota (b)): dividendos/JCP omitidos; SEM direção declarada a priori — ao contrário de H1/H2/H4/H5/H6/H8 (fatores de preço/vol, onde a relação com yield é conhecida da literatura), a relação entre ROE alto e política de dividendos de empresas B3 não foi estabelecida nesta rodada (poderia ir em qualquer direção: empresa lucrativa paga mais OU reinveste mais). Viés não quantificado, registrado como limitação honesta (declarado no pré-registro da H7, 2026-09-03) — não inferir sinal. Adicionalmente: o dado de ROE tem embargo de divulgação de 90 dias sobre `ref_date` (`h7_factor.disclosure_embargo_days`), mas não cobre a data REAL de entrega da DFP à CVM (ver `ingest_cvm.py`) — um embargo curto demais vazaria informação contábil antes da publicação real.
- Custo proporcional ao turnover real; execução na abertura de D+1.
- Veredito real da H7 exige COTAHIST **real** da B3 — sintético só valida a máquina.
