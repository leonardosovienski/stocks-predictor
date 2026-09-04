# predictor-stocks — Relatório do veredito da H13

- **run_id:** `n/d`
- **pregões pareados:** 1597
- **veredito H13:** **não comprovada (IC cruza 0 / negativo; DSR 0.2598 < 0.95)**

## Pedágio de 2 lentes

- **Lente 1 (PSR):** 0.3579  — P(Sharpe estratégia > Sharpe benchmark), corrige não-normalidade
- **Lente 2 (IC 95% da diferença de Sharpe, block bootstrap pareado, bloco 21):** [-0.4562, 0.1611]
  - H13 comprovada só se o IC não cruzar zero → CRUZA zero / negativo
- **Critério (ii) — DSR (Deflated Sharpe Ratio):** 0.2598 contra E[max SR | N=12] = 0.0268 por-período (mínimo pré-registrado: 0.95)

## Estratégia vs. benchmark (equiponderado do universo)

| métrica | estratégia | benchmark |
|---|---|---|
| Sharpe (anual.) | 0.1690 | 0.3136 |
| Sortino (anual.) | 0.2430 | 0.4515 |
| retorno total | 7.40% | 32.11% |
| max drawdown | 48.57% | 36.64% |

## Ressalvas registradas (não-negociáveis)

- Retorno **só-preço** (rota (b)): dividendos/JCP omitidos; SEM direção declarada a priori — a relação entre crescimento de receita e política de dividendos de empresas B3 não foi estabelecida nesta rodada. Viés não quantificado, registrado como limitação honesta (declarado no pré-registro da H13, 2026-09-04) — não inferir sinal. Mesmo embargo de divulgação de 90 dias de H7/H9/H10/H12 (`h13_factor.disclosure_embargo_days`, mesma fonte DFP/CVM). Adicionalmente: granularidade ANUAL da DFP (não ITR trimestral) — as duas linhas mais recentes elegíveis usadas no cálculo de crescimento nem sempre estão exatamente 12 meses de distância se houver ano com dado faltante (ver `factor.revenue_growth_signals`).
- Custo proporcional ao turnover real; execução na abertura de D+1.
- Veredito real da H13 exige COTAHIST **real** da B3 — sintético só valida a máquina.
