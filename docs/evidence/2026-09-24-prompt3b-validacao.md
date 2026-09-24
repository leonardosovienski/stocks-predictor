# Prompt 3b — CPCV, métricas de fator, PSR/DSR/PBO e política (stocks-predictor) — 2026-09-24

Base: o Prompt 3a (branch `feature/prompt3a-pit-protocol-20260924`, PR #100). Código no commit `ba24f56` da branch
cumulativa `feature/prompt3b-validation-20260924`. Execução local no PC 2 (WSL Ubuntu 24.04, Python 3.13.15).
Nenhuma credencial, nenhuma ordem, nenhum download de dados. Dados: só o dataset e a taxa livre de risco
**sintéticos** dos testes, mais o `COTAHIST_A2026.ZIP` versionado (`34b77468…`) para os recibos R8.

Convenções: **PROVEN** = constatado nesta sessão; **DECLARED** = descrito, não comprovado aqui; **UNKNOWN** =
indeterminado.

## A. Resumo

- **7 módulos novos em `stocks_predictor/v2`** (1.357 linhas contando os testes): `riskfree`, `metrics`,
  `factor_metrics`, `cpcv`, `pbo`, `policy` e `validation`. Também houve ajustes pequenos em `manifest` (registro
  `DECISION` e identidade da política no manifesto), `baselines` (nome distinto por variante de momentum) e
  `synthetic` (série livre de risco sintética). Nenhum `.py` fora do `v2` mudou. PROVEN.
- **Política de decisão** em [policy/stocks-evaluation-policy-v1.json](../../policy/stocks-evaluation-policy-v1.json)
  (sha256 `4898b7c7…`).
  - Os limiares só existem no arquivo.
  - Status `PROPOSED_PENDING_OWNER_APPROVAL`: limiares propostos antes de qualquer resultado em dado real.
  - O core 3.2.1 não tem arquivo de política, então a política é local e fica registrada como dívida.
- **Testes:** 24 novos em `tests/test_v2_validation.py`, incluindo os 5 obrigatórios.
- **Mutação:** 6 defeitos injetados, 6 detectados (seção E). PROVEN.
- **Suíte integral isolada** no commit limpo `ba24f56`: **1.144 passed + 71 subtests, 0 falhas, 0 erros,
  0 skips**, 313,32 s. Cobertura de 80% (piso 77); os módulos do 3b ficam entre 78% (`metrics`) e 93%
  (`factor_metrics`). PROVEN.
- **R8:** recibos novos (real de 55.986 linhas, sha256 `6bb54f22…`; capacidade de 250.000 linhas, `8b9f714d…`).
  Registro re-selado com 247 arquivos de código (`code_population_sha256` `4d7701c8…`); `verify_operational_evidence`
  = PASS. PROVEN.
- **Qualidade:** ruff limpo; pyright com 0 erros em 3.13 e 3.14; `check_project_files` PASS; gitleaks sem achados.
  PROVEN.
- **Bibliotecas:** nenhuma adicionada. PSR e E[max SR] vêm do core, que já é dependência travada no `uv.lock`.
  - skfolio (BSD-3, 1.3.1, conferido na documentação e no PyPI em 2026-09-24): não adotado. O
    `CombinatorialPurgedCV` purga um número fixo de observações (`purged_size`), não o intervalo real do rótulo, e
    traria numpy, scipy, pandas, cvxpy, clarabel, scikit-learn e plotly. DECLARED (documentação).
  - pypbo (AGPL) e mlfinlab (proprietário): não usados.
- **Taxa livre de risco real: indisponível no PC 2.** A Selic SGS 11 usada na H21 só tem o manifesto de fonte no
  Git (`research/session-20260909/.../selic-11.json.source.json`, sha256 `82d23198…`, 84.912 bytes). Procurei
  pelo hash em `~/predictors` e não há cópia. O 3b não precisa dela; a avaliação real precisa. UNKNOWN se o PC 1
  tem a cópia.

## B. Métricas: fórmula, referência e teste

| Métrica | Fórmula / referência | Teste que prova |
|---|---|---|
| Retorno em excesso | `r_s − rf_s`; rf das unidades SGS (`% a.d.` ou `% a.a.` base 252); pregão sem taxa → erro | `test_sharpe_uses_the_configured_risk_free_rate`, `test_risk_free_series_fails_closed` |
| Sharpe líquido em excesso | média/desvio amostral do excesso diário × √252 (Sharpe 1994) | `test_sharpe_uses_the_configured_risk_free_rate` (valor à mão; cai mais de 0,5 com rf de 12%) |
| PSR | Φ[(SR − SR*)·√(n − 1)/√(1 − γ3·SR + (γ4 − 1)/4·SR²)] (Bailey & López de Prado 2012); série pelo core | `test_psr_from_moments_agrees_with_the_core_on_a_series` (diferença ≤ 1e−12) |
| DSR | PSR com SR* = E[max SR] = √V[SR]·((1 − γ)Φ⁻¹(1 − 1/N) + γΦ⁻¹(1 − 1/(Ne))) (Bailey & López de Prado 2014) | `test_dsr_matches_the_published_numerical_example`: E[max SR] = 0,113172 (publicado 0,1132) e DSR = 0,900397 (publicado 0,9004); `test_dsr_is_more_conservative_with_more_trials` |
| Grade de N | {N, 2N, 5N, N_upper} com N = 71 + execuções do ledger; decisão no pior caso | `test_trial_grid_matches_the_audit` ([71, 142, 150, 355]); `test_dsr_is_more_conservative_with_more_trials` |
| t e limiar HLZ | t = média/(desvio/√n); t > 3 como diagnóstico (Harvey, Liu & Zhu 2016); vira gate só se a política mandar | `test_policy_decisions_carry_version_and_hash_and_use_file_thresholds` (diagnóstico não bloqueia; `role: gate` bloqueia) |
| beta/alpha | MQO do excesso da estratégia sobre o excesso do índice; α anual = α × 252 | `test_beta_alpha_hand_computed` (β = 2, α = 0,001, R² = 1) |
| Max drawdown, turnover, custos | do motor do 3a, líquidos | testes do 3a |
| IC / Rank IC | Pearson; Spearman = Pearson dos postos médios (Grinold & Kahn 2000) | `test_ic_and_rank_ic_hand_computed` (0,8 sem empates; 0,5; 4,5/√22,5 com empates) |
| ICIR, decaimento, quantis | média/desvio do IC (× √períodos/ano); Rank IC por h; média por quantil; long-short = topo − base | `test_cross_section_ic_is_one_for_an_oracle_scorer` (IC = Rank IC = 1 com escore oráculo; quantis crescentes; rótulo dentro da janela) |
| PBO | CSCV (Bailey, Borwein, López de Prado & Zhu 2017): λ = ln(ω̄/(1 − ω̄)), PBO = P(λ ≤ 0) | `test_pbo_hand_computed_example` (6 combinações à mão, PBO = 4/6); `test_pbo_properties` (dominante → 0; ruído → média ≈ 0,5) |
| CPCV | purge pelo intervalo do rótulo, embargo após cada bloco, φ = C(N − 1, k − 1) caminhos (López de Prado 2018, cap. 7 e 12) | `test_overlapping_labels_leak_without_purge_and_never_with_it`, `test_leakage_guard_rejects_a_leaking_split`, `test_cpcv_paths_cover_every_group_once`, `test_run_cpcv_fits_only_on_train_and_assembles_full_paths` |
| Decisão | NO_DECISION / REJECT / PASS pela política versionada | `test_no_baseline_means_no_decision`, `test_policy_decisions_carry_version_and_hash_and_use_file_thresholds`, `test_policy_file_is_validated` |

## C. purge_size e embargo_size

- **purge_size = lag + h = 1 + 21 = 22 pregões.**
  - A amostra decidida em `t0` executa em `t0 + 1` e o rótulo usa preços até `t0 + 1 + 21`.
  - O purge remove do treino toda amostra cujo intervalo `[t0, t1]` cruza um bloco de teste. É o intervalo real
    de cada rótulo, não um número fixo.
  - Com rebalanceamento mensal (passo mediano de 21 pregões), os rótulos de meses vizinhos se sobrepõem em 1
    pregão. Por isso toda divisão purga ao menos a amostra adjacente ao bloco de teste. Na demonstração, a divisão
    0 purgou 1 amostra.
- **embargo_size = (L − 1) × passo.**
  - L é a primeira defasagem, em períodos de rebalanceamento, em que |ρ(L)| do Rank IC do candidato fica abaixo
    da banda de Bartlett z/√n.
  - Na demonstração sintética: ρ(1) = 0,124 < 0,462 (z = 1,96, n = 18), então L = 1 e o embargo é **0**.
  - Com dependência persistente (AR(1) com φ = 0,9 no teste) o embargo sai positivo e múltiplo do passo
    (`test_purge_and_embargo_sizes_are_derived_not_chosen`).
  - Se nenhuma defasagem até `max_lag` for insignificante, o embargo é o máximo, e isso fica sinalizado.
- **Limite:** com n = 18 a banda é larga, e o ρ do sintético não diz nada do mercado. No dado real a regra é a
  mesma, e os tamanhos saem da série real.

## D. Testes obrigatórios

| Teste | O que prova | Resultado |
|---|---|---|
| Purge/embargo — `test_overlapping_labels_leak_without_purge_and_never_with_it` | 200 amostras com rótulos de 22 pregões. Sem purge há vazamento (constatado); com o CPCV, nas 15 divisões, nenhum treino cruza teste, nenhum treino cai no embargo, a partição é exata e houve purge | PASS |
| DSR × N — `test_dsr_is_more_conservative_with_more_trials` | Mesmas métricas: o DSR cai estritamente em 71 → 142 → 150 → 355 e o pior caso é N = 355 | PASS |
| Valores publicados e à mão | DSR do exemplo de Bailey & López de Prado (2014); PSR contra o core; IC/Rank IC, PBO e beta/alpha à mão | PASS |
| Sharpe com rf — `test_sharpe_uses_the_configured_risk_free_rate` | O Sharpe em excesso bate com o cálculo à mão com rf de 12% a.a. e difere do rf = 0 | PASS |
| Sem baseline — `test_no_baseline_means_no_decision` | Sem nenhum baseline, ou com só um dos dois exigidos: NO_DECISION com o motivo | PASS |

## E. Verificação

- **Mutação** (patch em memória, sobre os 24 testes de `test_v2_validation.py`, que passam todos sem mutação):

  | Defeito injetado | Testes que falharam |
  |---|---|
  | CPCV sem purge e sem guarda | 3 |
  | DSR ignora N | 1 |
  | Taxa livre de risco ignorada | 2 |
  | Baseline opcional na decisão | 1 |
  | Posto do PBO sobre N em vez de N + 1 | 4 |
  | Postos sem média de empates | 1 |

  Todos os seis defeitos foram detectados.
- **Suíte integral** (`prompt3b_suite.sh`: `env -i`, `unshare --net`, uid 1000; mesmo comando do CI), no commit
  limpo `ba24f56` com o worktree intocado durante a execução: **1.144 passed + 71 subtests, 0 falhas**, 313,32 s,
  rede inalcançável, ambiente só com `HOME`, `LANG` e `PATH`, cobertura de 80%. São 24 testes a mais que no 3a
  (1.120).
- **Uma correção durante o trabalho:**
  - A propriedade estatística do PBO em ruído puro, que eu mesmo tinha escrito com limites não calibrados
    (0,25–0,8 para uma matriz), falhou com 0,83.
  - Medi a distribuição: em 200 matrizes 80×10, média 0,491 e desvio 0,224, compatível com E[PBO] = 0,5.
  - O teste passou a verificar a média de 30 matrizes independentes em 0,5 ± 0,15, com a justificativa no
    comentário. Não é afrouxamento de validação existente: é a calibração de um teste novo contra a propriedade
    teórica.
- **Cross-section:** a primeira versão cortava todos os horizontes pelo maior (126). Corrigi para que cada horizonte
  use todos os sinais cujo rótulo termina dentro da janela.

## F. Demonstração no dado sintético (não é evidência empírica)

Comando `python -m stocks_predictor.v2.validation` (seção de uso do
[README](../engineering/2026-09-24-protocol-v2/README.md)), no commit `ba24f56` (`dirty: false`), com a política
real.
- Duas execuções em ledgers separados: mesmos digests nas 8 execuções, relatório idêntico sem ids e horários, mesma
  decisão. PROVEN.
- Saída em [synthetic-validation.json](../engineering/2026-09-24-protocol-v2/evidence/prompt3b/synthetic-validation.json)
  (sha256 `1899ec5a…`).

- **Decisão: NO_DECISION.** Motivos: `SYNTHETIC-RF` não admitida; dataset sintético; 376 pregões < 504. A decisão
  foi registrada no ledger (`DECISION`), com a política `1.0.0` e sha256 `4898b7c7…`.
- Sharpe líquido em excesso anualizado:

  | Execução | Sharpe |
  |---|---|
  | EW do universo | 0,753 |
  | Buy-and-hold do índice | 1,609 |
  | Candidato momentum 12-1 (pré-declarado) | 1,017 |

  - O candidato tem PSR 0,892, t 1,24, β = 1,11 e α anual = 3,7% contra o índice.
  - As outras 5 variantes da família ficaram entre 0,305 e 1,607.
- **Cross-section** do candidato (18 períodos mensais):

  | h | IC médio | Rank IC médio |
  |---|---|---|
  | 21 | 0,088 | 0,028 |
  | 63 | 0,096 | −0,027 |
  | 126 | 0,037 | −0,070 |

  Long-short: média 2,79% por mês, t = 1,48, abaixo do limiar de 3.
- **CPCV:** 15 divisões, 5 caminhos; Sharpe por caminho do procedimento "melhor variante no treino" entre 0,397 e
  0,499.
- **DSR** (V[SR] da família = 0,000933):

  | N | DSR |
  |---|---|
  | 79 | 0,419 |
  | 150 | 0,369 |
  | 158 | 0,365 |
  | 395 | 0,302 (pior caso) |
- **PBO** = 0,418 (12.870 combinações, S = 16, 6 configurações, 8 linhas finais descartadas).
- Estes números mostram a maquinaria funcionando. Não dizem nada sobre o mercado.

## G. Limites, dívidas e DECLARED/UNKNOWN

1. **Taxa livre de risco real:** não há série versionada no PC 2 (UNKNOWN no PC 1). A avaliação real exige parar e
   perguntar antes de baixar a SGS 11/12 do BCB.
2. **Política** local e proposta. Os limiares da v1 são: PSR ≥ 0,95; DSR no pior N ≥ 0,95; PBO ≤ 0,2; vencer EW e
   índice no Sharpe em excesso; ≥ 504 pregões; t > 3 como diagnóstico. Valem depois da aprovação do dono. Subir o
   arquivo de política para o core é dívida.
3. **N de tentativas:** limite inferior de 71 (Prompt 2) mais as execuções do ledger. O N_upper de 150 é
   DECLARED do Prompt 2. A decisão usa o pior caso da grade.
4. **V[SR] do DSR:** vem da família avaliada no ledger. Os 15 Sharpes históricos de `trials.json` foram medidos com
   rf = 0 no motor legado e não se misturam sem conversão.
5. **t e ICIR** supõem independência entre períodos; com h > passo são otimistas.
6. Tudo o que o 3a registrou continua valendo: sem dataset PIT real, dívidas do motor, e o pacote muda depois do
   `final_commit` qualificado `61fc017` (C14 é decisão do dono).

## Próximo passo

- **O 3c pode assumir como PROVEN:**
  - O `v2` tem métricas líquidas em excesso de uma taxa livre de risco versionada (sem zero silencioso).
  - Tem cross-section IC/Rank IC/ICIR com rótulo desde o preço de execução.
  - Tem CPCV com purge pelo intervalo real do rótulo e embargo derivado.
  - Tem DSR com grade de N e pior caso, conferido contra o exemplo publicado, e PBO por CSCV.
  - Tem política de decisão versionada com hash, e NO_DECISION sem baseline, com rf não admitida ou com dado
    sintético.
  - Toda execução e toda decisão ficam no ledger.
  - A suíte integral isolada está verde no commit limpo, e o R8 foi re-selado.
- **DECLARED:** os parâmetros do skfolio (documentação); N_upper = 150.
- **UNKNOWN:** a série real de CDI/Selic e se o PC 1 a tem; o desempenho de qualquer estratégia ou modelo em dado
  real sob o v2.
- **Para o 3c:**
  - Chronos só com a licença conferida no model card no dia.
  - Download do checkpoint e dos dados reais (COTAHIST de vários anos, eventos com anúncio, CDI): parar e
    perguntar.
  - As previsões zero-shot devem passar pelo mesmo `validation` (rótulo desde a execução, excesso de rf, DSR com
    N atualizado, PBO, política).
