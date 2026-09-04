# predictor-stocks — Relatório do veredito da H10

- **run_id:** `n/d`
- **pregões pareados:** 1826
- **veredito H10:** **não comprovada (IC cruza 0 / negativo; DSR 0.3661 < 0.95)**

## Pedágio de 2 lentes

- **Lente 1 (PSR):** 0.4139  — P(Sharpe estratégia > Sharpe benchmark), corrige não-normalidade
- **Lente 2 (IC 95% da diferença de Sharpe, block bootstrap pareado, bloco 21):** [-0.3820, 0.2029]
  - H10 comprovada só se o IC não cruzar zero → CRUZA zero / negativo
- **Critério (ii) — DSR (Deflated Sharpe Ratio):** 0.3661 contra E[max SR | N=9] = 0.0141 por-período (mínimo pré-registrado: 0.95)

## Estratégia vs. benchmark (equiponderado do universo)

| métrica | estratégia | benchmark |
|---|---|---|
| Sharpe (anual.) | 0.0955 | 0.1766 |
| Sortino (anual.) | 0.1297 | 0.2391 |
| retorno total | -3.56% | 9.45% |
| max drawdown | 43.64% | 48.26% |

## Ressalvas registradas (não-negociáveis)

- Retorno **só-preço** (rota (b)): dividendos/JCP omitidos; SEM direção declarada a priori — mesma limitação de H7/H9 (a interseção de ROE alto e baixa alavancagem não tem relação estabelecida com política de dividendos nesta rodada). Viés não quantificado, registrado como limitação honesta (declarado no pré-registro da H10, 2026-09-04) — não inferir sinal. Mesmo embargo de divulgação de 90 dias por variável (`h10_factor.roe_disclosure_embargo_days`/`leverage_disclosure_embargo_days`), mesma fonte DFP/CVM de H7/H9.
- Custo proporcional ao turnover real; execução na abertura de D+1.
- Veredito real da H10 exige COTAHIST **real** da B3 — sintético só valida a máquina.
