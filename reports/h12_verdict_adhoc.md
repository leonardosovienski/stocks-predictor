# predictor-stocks — Relatório do veredito da H12

- **run_id:** `n/d`
- **pregões pareados:** 1826
- **veredito H12:** **não comprovada (IC cruza 0 / negativo; DSR 0.1952 < 0.95)**

## Pedágio de 2 lentes

- **Lente 1 (PSR):** 0.4328  — P(Sharpe estratégia > Sharpe benchmark), corrige não-normalidade
- **Lente 2 (IC 95% da diferença de Sharpe, block bootstrap pareado, bloco 21):** [-0.3356, 0.1848]
  - H12 comprovada só se o IC não cruzar zero → CRUZA zero / negativo
- **Critério (ii) — DSR (Deflated Sharpe Ratio):** 0.1952 contra E[max SR | N=11] = 0.0273 por-período (mínimo pré-registrado: 0.95)

## Estratégia vs. benchmark (equiponderado do universo)

| métrica | estratégia | benchmark |
|---|---|---|
| Sharpe (anual.) | 0.1135 | 0.1766 |
| Sortino (anual.) | 0.1561 | 0.2391 |
| retorno total | -2.28% | 9.45% |
| max drawdown | 44.86% | 48.26% |

## Ressalvas registradas (não-negociáveis)

- Retorno **só-preço** (rota (b)): dividendos/JCP omitidos; SEM direção declarada a priori — a relação entre margem líquida e política de dividendos de empresas B3 não foi estabelecida nesta rodada. Viés não quantificado, registrado como limitação honesta (declarado no pré-registro da H12, 2026-09-04) — não inferir sinal. Mesmo embargo de divulgação de 90 dias sobre `ref_date` de H7/H9/H10 (`h12_factor.disclosure_embargo_days`, mesma fonte DFP/CVM).
- Custo proporcional ao turnover real; execução na abertura de D+1.
- Veredito real da H12 exige COTAHIST **real** da B3 — sintético só valida a máquina.
