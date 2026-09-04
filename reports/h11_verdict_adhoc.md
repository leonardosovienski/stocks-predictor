# predictor-stocks — Relatório do veredito da H11

- **run_id:** `n/d`
- **pregões pareados:** 1218
- **veredito H11:** **não comprovada (IC cruza 0 / negativo; DSR 0.8430 < 0.95)**

## Pedágio de 2 lentes

- **Lente 1 (PSR):** 0.7704  — P(Sharpe estratégia > Sharpe benchmark), corrige não-normalidade
- **Lente 2 (IC 95% da diferença de Sharpe, block bootstrap pareado, bloco 21):** [-0.0378, 0.7914]
  - H11 comprovada só se o IC não cruzar zero → CRUZA zero / negativo
- **Critério (ii) — DSR (Deflated Sharpe Ratio):** 0.8430 contra E[max SR | N=10] = 0.0277 por-período (mínimo pré-registrado: 0.95)

## Estratégia vs. benchmark (equiponderado do universo)

| métrica | estratégia | benchmark |
|---|---|---|
| Sharpe (anual.) | 0.9167 | 0.5660 |
| Sortino (anual.) | 1.2852 | 0.7674 |
| retorno total | 205.51% | 77.28% |
| max drawdown | 48.62% | 46.50% |

## Ressalvas registradas (não-negociáveis)

- Retorno **TOTAL** (rota (a), 2026-09-04): proventos REINVESTIDOS via `adjust.total_return_series`, ao contrário de H1-H10 (só-preço). **Cobertura de proventos parcial**: a fonte (CVM/FRE, `dividends`) só é confiável 2018-2022 (achado registrado no HANDOFF 2026-09-04 — 2023-2026 têm quase zero cobertura) — por isso a janela da H11 é restrita a 2018-2022 (`h11_backtest.test_start/test_end`), não os anos completos de H1-H10. Duas aproximações do dado de provento em si (não escondidas): valor por ação médio ON+PN (não por classe específica) e data de PAGAMENTO como proxy de data-ex (a CVM não expõe a data-ex real neste dataset).
- Custo proporcional ao turnover real; execução na abertura de D+1.
- Veredito real da H11 exige COTAHIST **real** da B3 — sintético só valida a máquina.
