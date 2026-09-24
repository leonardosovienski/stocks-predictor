# Prompt 3a — Dados PIT, execução, custos, baselines, walk-forward e manifesto (stocks-predictor) — 2026-09-24

Base: `main` `fe53b19` (PRs #98 e #99 mergeadas). Código no commit `85524d6` da branch
`feature/prompt3a-pit-protocol-20260924`. Execução local no PC 2 (WSL Ubuntu 24.04, Python 3.13.15). Nenhuma
credencial, nenhuma ordem, nenhum download. Dados: o `COTAHIST_A2026.ZIP` versionado (sha256 `34b77468…`, só para
os recibos R8) e o dataset **sintético** determinístico dos testes.

Convenções: **PROVEN** = constatado nesta sessão (comando, arquivo, commit); **DECLARED** = descrito, não comprovado
aqui; **UNKNOWN** = indeterminado.

## A. Resumo

- **Pacote novo e aditivo `stocks_predictor/v2`** (10 módulos, 1.831 linhas; testes com 638 linhas): dados PIT, convenção de execução,
  custos e liquidez, motor, baselines, walk-forward, RunManifest/TrialLedger, dataset sintético e CLI.
  - Nenhum `.py` existente mudou. `git diff --stat origin/main` antes do commit mostrava um único arquivo
    versionado alterado, o registro R8. PROVEN.
  - Os vereditos congelados e o circuito qualificado seguem byte a byte.
  - Contrato em [docs/engineering/2026-09-24-protocol-v2](../engineering/2026-09-24-protocol-v2/README.md).
- **Testes:** 71 novos em `tests/test_v2_dataset.py`, `tests/test_v2_engine.py` e `tests/test_v2_manifest.py`,
  incluindo os 5 obrigatórios. A mensagem do commit `85524d6` diz "74"; a contagem certa é 71 (1.120 testes
  contra 1.049 no Prompt 2).
- **Mutação:** 6 defeitos injetados de propósito, todos detectados (seção D). PROVEN.
- **Suíte integral isolada** (sem rede; ambiente só com `HOME`, `LANG` e `PATH`) no commit limpo `85524d6`:
  **1.120 passed + 71 subtests, 0 falhas, 0 erros, 0 skips**, 260,10 s. Cobertura de 80% (piso 77; eram 78% no
  Prompt 2); os módulos do `v2` ficam entre 86% e 100%. PROVEN.
- **R8:** recibos novos no código deste commit. Carga real de 55.986 linhas, fonte `34b77468…`, `rows_sha256`
  `6d47c43e…` igual à população R7 preservada. Capacidade de 250.000 linhas. Registro re-selado com 239 arquivos
  de código; `tools/verify_operational_evidence.py` = PASS. PROVEN.
- **Qualidade:** ruff limpo; pyright com 0 erros em 3.13 e 3.14; `tools/quality_exception_control.py` PASS;
  `tools/check_project_files.py` PASS. PROVEN.
- **Nenhuma biblioteca adicionada.** Só biblioteca padrão e o contrato `trial-registry/2.0.0` do `predictor-core`
  3.2.1, que já é dependência travada no `uv.lock`.
- **Não houve avaliação com dados reais.** Não existe dataset `stocks-pit-dataset/2` real; montá-lo exige os
  bancos do PC 1 e eventos societários com data de anúncio (seção G). Nada foi baixado.

## B. Requisitos do prompt → implementação → teste

| Requisito | Implementação | Teste(s) | Estado |
|---|---|---|---|
| Universo por data com deslistados | `PITView.listed`/`listed_ids`: entra depois do 1º pregão com a listagem já conhecida; sai só quando a deslistagem é conhecida **e** efetiva. `engine.decision_universe` aplica a liquidez | `test_delisted_securities_are_in_the_universe_while_they_traded`, `test_delisted_holdings_leave_at_delisting_value_and_bankruptcy_hurts` | PROVEN (sintético) |
| Preço ajustado só com o que se sabia | Barras guardam o preço negociado. `PITView.history` ajusta só por eventos com anúncio já conhecido e data ex anterior à decisão. Revisões de barra só depois de publicadas | `test_reverse_split_adjusts_history_only_after_it_is_known`, `test_future_split_never_adjusts_a_past_view`, `test_bar_revision_is_invisible_until_published` | PROVEN (sintético) |
| Fundamentos pela data de divulgação | `fundamentals` com `available_at` = divulgação e `version`. Uma reapresentação só vale depois da sua própria divulgação | `test_fundamental_disclosed_at_d_never_appears_before_d`, `test_restatement_replaces_value_only_from_its_disclosure` | PROVEN (sintético) |
| Calendário de pregões correto | Calendário explícito no dataset. Rejeita fim de semana, pregão sem negócio, barra fora do calendário e barra disponível antes das 20:00 UTC. Rebalanceamento no último pregão do período | `test_dataset_validation_fails_closed` (11 casos), `test_rebalance_schedule_uses_period_ends` | PROVEN |
| Sinal até o fechamento de D, execução ≥ abertura de D+1 | `ExecutionConvention(lag_sessions >= 1, price)`; `lag_sessions=0` levanta `ExecutionError` | `test_no_trade_uses_the_close_that_generated_the_signal` (3 convenções), `test_signal_only_sees_bars_up_to_the_signal_close`, `test_same_close_execution_is_not_representable` | PROVEN |
| Baselines no mesmo universo, período, custos e protocolo | `EqualWeightUniverse`, `IndexBuyAndHold`, `Momentum12_1`, `RandomPortfolio` (DESIGN §8) rodam no mesmo motor e com a mesma `ProtocolConfig`. `RandomWalkForecaster` e `NaiveLastReturn` são avaliados contra o preço de execução | `test_equal_weight_baseline_pays_the_same_costs_as_any_strategy`, `test_index_buy_and_hold_buys_once_and_holds`, `test_momentum_uses_the_top_quintile_of_12_1_scores`, `test_random_portfolio_is_seeded_and_keeps_position_count`, `test_naive_and_random_walk_forecasts_score_against_execution_prices` | PROVEN (sintético) |
| Custos explícitos; métricas líquidas | `CostModel` sem padrões: corretagem (bps + fixo), emolumentos, spread, slippage, impacto vs ADV, aluguel. `performance` é líquida; o bruto é só decomposição | `test_net_result_is_monotonically_non_increasing_in_costs`, `test_every_cost_component_reduces_the_net_result`, `test_short_positions_pay_borrow`, `test_metrics_are_net_and_gross_is_only_a_decomposition` | PROVEN |
| Liquidez na decisão + participação | `LiquidityRule(min_adv, adv_lookback, max_participation, statistic)`; o excedente fica sem execução e é registrado | `test_liquidity_filter_and_participation_cap`, `test_adv_counts_sessions_without_trades_as_zero` | PROVEN |
| Walk-forward estrito | `walk_forward_splits` e `assert_separation` (`train_end + h + embargo < test_start`, sem sobreposição). `run_walk_forward` ajusta só com a visão do treino | `test_walk_forward_splits_are_strictly_separated`, `test_walk_forward_fits_only_on_training_data` | PROVEN |
| RunManifest em toda execução avaliativa; TrialLedger com falhas e crashes, sem sobrescrita | `build_manifest`, `TrialLedger` (append-only, cadeia de hashes, STARTED/COMPLETED/FAILED/ABANDONED), `run_evaluation` | `test_every_evaluative_run_writes_a_complete_manifest`, `test_failed_runs_are_recorded_counted_and_reraised`, `test_crash_leaves_a_started_record_that_becomes_abandoned`, `test_nothing_is_overwritten`, `test_ledger_is_tamper_evident` (4 danos) | PROVEN |

Campos do manifesto (PROVEN no ledger da demonstração): `run_id`, `git.commit` + `git.dirty`, `package_version`,
`config` + `config_hash`, `dataset.hash`/`version`/`data_cutoff`, `universe` (regra, liquidez e corte), `interval`,
`seed`, `model`, `costs`, `execution`, `validation`, `engine_version`, `policy_version`
(`stocks-evaluation-protocol-v2/3a.1`). O ledger acrescenta `trial_number` (todo `STARTED` conta, inclusive falhas),
as métricas e o digest do resultado. Cada desfecho leva uma linha `trial-registry/2.0.0` validada pelo core, com
`n_trials_domain = known_trials >= 71 + trials do ledger` (limite inferior do Prompt 2).

## C. Testes obrigatórios

| Teste | O que prova | Resultado |
|---|---|---|
| PIT — `test_fundamental_disclosed_at_d_never_appears_before_d` | Varre todos os 630 pregões e as 3 versões de fundamento: nada aparece antes da sua divulgação, nem como valor mais recente nem pelo período | PASS |
| Execução — `test_no_trade_uses_the_close_that_generated_the_signal` | EW e momentum em `open` D+1, `close` D+1 e `worst` D+2: todo negócio é exatamente `lag` pregões depois do sinal, com decisão antes da abertura, no preço do pregão de execução | PASS |
| Sobrevivência — `test_delisted_securities_are_in_the_universe_while_they_traded` | DEL1 (deslistagem anunciada), BUST (falência só conhecida 10 dias depois) e IPO1 entram e saem exatamente quando deviam | PASS |
| Custos — `test_net_result_is_monotonically_non_increasing_in_costs` | Custos ×{0; 0,5; 1; 2; 4; 8} nas 4 carteiras de baseline: NAV final líquido não cresce e cai de ×0 a ×8 | PASS |
| Reprodutibilidade — `test_same_config_dataset_hash_and_seed_reproduce_the_same_result` | Dataset reconstruído do zero: mesmo hash; `evaluate` idêntico nas 4 carteiras. Outra semente muda o digest da aleatória | PASS |

## D. Verificação

- **Mutação** (patch em memória, no commit `85524d6`, sobre os 71 testes `test_v2_*`, que passam todos sem
  mutação; nenhum arquivo alterado):

  | Defeito injetado | Testes que falharam |
  |---|---|
  | Visão PIT enxerga tudo | 5 |
  | Visão um pregão atrasada (futuro) | 8 |
  | Universo ignora deslistagem | 2 |
  | Spread grátis | 1 |
  | Ledger sem verificação de cadeia | 4 |
  | Execução no pregão do sinal | 5 |

  Todos os seis defeitos foram detectados.
- **Suíte integral** (`prompt3a_suite.sh`: `env -i`, `unshare --net`, uid 1000, rede inalcançável; mesmo comando do
  step "Tests" do CI).
  - Primeira execução, com a árvore **suja** (código ainda sem commit): 1.097 passed e 23 failed. As 23 falhas têm
    a mesma causa, `DirtyWorkingTreeError` do `predictor_core.testing.harness`, que recusa atestado com árvore
    suja. O AGENTS.md proíbe contornar essa recusa, e ela não foi contornada.
  - Segunda execução, já no commit `85524d6`, também com 23 × `DirtyWorkingTreeError`. Erro meu: gravei o
    relatório e o resumo da demonstração no worktree durante a execução. Tirei os dois de lá.
  - Terceira execução, no commit `85524d6` com o worktree intocado (`git status --porcelain
    --untracked-files=all` vazio): **1.120 passed + 71 subtests, 0 falhas**, 260,10 s, cobertura de 80%. Log em
    `~/predictors/runtime/stocks/prompt3a/` (fora do repositório).
- **Pyright:** o node do pyright-python pede `libatomic.so.1`, que não está no WSL. Rodei com `LD_LIBRARY_PATH`
  apontando para uma cópia que já existia em outro runtime local, sem instalar nada.
- **R8:**
  - A primeira tentativa da carga real falhou por erro meu de invocação. A ferramenta usa `--rows 250000` por
    padrão e recusou a contagem, como devia. Log preservado fora do repositório.
  - Repeti com `--rows 55986`: PASS.
  - Recibos em [evidence/operational-real.json](../engineering/2026-09-24-protocol-v2/evidence/operational-real.json)
    (sha256 `7f81858f…`) e
    [evidence/operational-capacity.json](../engineering/2026-09-24-protocol-v2/evidence/operational-capacity.json)
    (`57f05b58…`).
  - Registro: `code_population_sha256` `66293c9f…`. Os recibos da etapa A foram mantidos.
- **Segredos:** `gitleaks protect --staged` (config do repo) e `gitleaks dir` (config do repo e regras padrão) nos
  arquivos novos: sem achados. Busca por `ghp_`, `gho_`, `github_pat_`, `-----BEGIN`, `api_key` e `secret` no diff:
  nada.

## E. Demonstração no dataset sintético (não é evidência empírica)

Comando: `python -m stocks_predictor.v2 --config docs/engineering/2026-09-24-protocol-v2/synthetic-demo-config.json
--dataset synthetic --ledger ledger.jsonl --output summary.json`, no commit `85524d6` (`dirty: false`).
- Dataset `f1edbb03…`, config `e4c30869…`, janela de 2020-01-02 a 2021-06-30, rebalanceamento mensal.
- Custo congelado da H1: 3 + 15 bps por lado.
- Resumo em [synthetic-demo-summary.json](../engineering/2026-09-24-protocol-v2/evidence/synthetic-demo-summary.json)
  (sha256 `842a4019…`); ledger com 10 registros, cabeça `102be3d0…`.

| Baseline (trial) | Retorno líquido | Retorno bruto | Sharpe rf=0 | Max DD | Turnover a.a. | Custos (R$) |
|---|---|---|---|---|---|---|
| EW do universo (1) | 16,62% | 17,12% | 1,03 | −9,14% | 1,53 | 4.379 |
| Buy-and-hold do índice (2) | 25,95% | 26,17% | 1,98 | −4,30% | 0,61 | 1.797 |
| Momentum 12-1 (3) | 33,52% | 35,94% | 1,18 | −12,60% | 6,39 | 18.493 |
| Aleatória, 5 papéis (4) | 9,12% | 14,07% | 0,46 | −10,61% | 16,71 | 48.707 |

- Previsão, h = 21 pregões (trial 5), 299 pares, 2 excluídos por falta de barra:
  - passeio aleatório: MSE 0,01064, MAE 0,07812;
  - ingênuo: MSE 0,01964, MAE 0,10956, acerto de direção 47,2%.
- Reexecução num ledger novo: os 5 digests saíram idênticos, com `run_id`s diferentes. PROVEN.
- Os números mostram o motor funcionando, com custos, falência a R$ 0 e deslistagem. Não dizem nada sobre o mercado.

## F. Premissas que o Prompt 2 mostrou contraditas pelo código

| Premissa | Legado | Protocolo v2 |
|---|---|---|
| Execução no mínimo em D+1 | `legacy_walk_forward` executa no fechamento de D | D+lag com lag ≥ 1; lag 0 é irrepresentável |
| Universo inclui deslistadas | inclui, mas com identidade pelo prefixo do ticker | `security_id` + ticker/emissor por vigência |
| Fundamentos pela divulgação | embargo estimado de 90 dias | só por `available_at` da divulgação, com versões |
| Baseline com os mesmos custos | benchmark EW sem custo | todos os baselines no mesmo motor e com os mesmos custos |

O legado continua intocado. Os vereditos julgados por ele (H1, H2, H4–H16) não mudam aqui. A reavaliação é do Prompt 4.

## G. Dívida técnica e limites

1. O core 3.2.1 não tem RunManifest nem ledger com ciclo de vida. Este pacote tem a versão mínima local, com
   ponte validada para `trial-registry/2.0.0`.
2. Não há dataset PIT real.
   - `adjustments` não guarda instante de anúncio.
   - O `stocks-pit-panel/1` do circuito qualificado tem as mesmas regras de instante, mas não tem abertura, eventos
     societários nem fundamentos.
   - Montá-lo exige os bancos do PC 1 e eventos com data de anúncio. Não foi feito e nada foi baixado.
3. A carteira aleatória iguala posições e frequência, mas não o turnover.
4. Não são modelados: lote, tributação, margem e participação contra o volume do próprio pregão.
5. A saída por deslistagem sem `delisting_value` usa o último fechamento, o que é otimista em falências.
6. O Sharpe usa rf = 0. O excesso sobre CDI/Selic é do 3b.
7. O pacote mudou depois do `final_commit` qualificado `61fc017`. O runtime qualificado deixa de ser o `main`; C14
   é decisão do dono.
8. O build reprodutível e o wheel instalado não rodaram localmente: faltava `hatchling` e não baixei. Ficam para o
   CI desta PR.

## Próximo passo

- **O 3b pode assumir como PROVEN:**
  - `stocks_predictor/v2` com dados PIT, execução D+1, custos líquidos, liquidez, baselines, walk-forward estrito e
    ledger de trials;
  - os 5 testes obrigatórios, a mutação 6/6 e a suíte integral isolada e verde no commit limpo;
  - R8 re-selado com recibos novos.
- **DECLARED:** completude dos bancos do PC 1.
- **UNKNOWN:** o desempenho de qualquer estratégia em dado real sob o v2, porque não há dataset real; e o N real
  de tentativas (limite inferior 71).
- **O 3b deve acrescentar sobre este motor:**
  - CPCV com purge/embargo derivados do horizonte;
  - IC, Rank IC e ICIR;
  - Sharpe em excesso de CDI/Selic (sem dado local versionado de rf: parar e perguntar);
  - PSR e DSR com N em {71, 142, 355, 150} e decisão no pior caso;
  - PBO por CSCV implementado localmente;
  - t > 3;
  - política versionada com hash; NO_DECISION sem baseline.
