# predictor-stocks — Relatório do veredito da H8

- **run_id:** `n/d`
- **pregões pareados:** 2131
- **veredito H8:** **não comprovada (IC cruza 0 / negativo; DSR 0.6050 < 0.95)**

## Pedágio de 2 lentes

- **Lente 1 (PSR):** 0.6366  — P(Sharpe estratégia > Sharpe benchmark), corrige não-normalidade
- **Lente 2 (IC 95% da diferença de Sharpe, block bootstrap pareado, bloco 21):** [-0.1508, 0.4138]
  - H8 comprovada só se o IC não cruzar zero → CRUZA zero / negativo
- **Critério (ii) — DSR (Deflated Sharpe Ratio):** 0.6050 contra E[max SR | N=6] = 0.0137 por-período (mínimo pré-registrado: 0.95)

## Estratégia vs. benchmark (equiponderado do universo)

| métrica | estratégia | benchmark |
|---|---|---|
| Sharpe (anual.) | 0.3110 | 0.1891 |
| Sortino (anual.) | 0.4188 | 0.2570 |
| retorno total | 44.42% | 14.51% |
| max drawdown | 44.18% | 48.26% |

## Ressalvas registradas (não-negociáveis)

- Retorno **só-preço** (rota (b)): direção MISTA — a perna momentum tende a FAVORECER a estratégia (menor yield, como H1/H6) e a perna baixa-vol tende a PENALIZAR (maior yield, como H2/H4); como a H8 é a INTERSEÇÃO das duas, o viés líquido não tem sinal a priori (não fixado explicitamente no pré-registro original da H8; nota técnica adicionada na revisão de código de 2026-08-28).
- Custo proporcional ao turnover real; execução na abertura de D+1.
- Veredito real da H8 exige COTAHIST **real** da B3 — sintético só valida a máquina.
