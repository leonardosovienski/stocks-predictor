# Revisão completa da sessão de 24 e 25/09/2026

Revisão de coerência de tudo o que a sessão fez no stocks. O histórico do chat foi a fonte principal. Classificação
das conclusões: **[execução]** = validado por execução ou teste; **[inspeção]** = validado por análise;
**[não validado]** = não foi possível validar, com o motivo.

## 1. O que foi revisto

- A missão noturna D-16 (`COMUM.md` + `stocks.md`) e o relatório `~/predictors/logs/noite/stocks.md`, que termina
  em `ESTADO FINAL: CONCLUIDO`. No `predictor-qualification`, as PRs #20, #21, #31, #36 e #37.
- A série 1 → 4 inteira e as entregas em `docs/evidence/2026-09-24-prompt*.md` e
  `2026-09-25-prompt4-reavaliacao.md`. No stocks-predictor, as PRs #98 a #104.
- As autorizações de download dadas pelo dono: `chronos-bolt-small` em venv isolado, CDI SGS 12 e COTAHIST
  2019–2025.
- O código de `stocks_predictor/v2` e seus testes, a política v1, o ledger de domínio (56 registros), as
  evidências versionadas e o estado de qualificação.

## 2. Requisitos recuperados

| Requisito | Origem | Estado |
|---|---|---|
| Só dados locais com hash; baixar só com autorização | série, regra comum | cumprido [inspeção]: os três downloads têm recibo sha256 |
| Nenhuma decisão com limiar não aprovado | 3b ("versão da política") + status `PROPOSED` | **faltava**: corrigido nesta revisão [execução] |
| Nenhum backtest de hipótese nova antes do pré-registro; limite de variantes | Prompt 4, item 5 | **só gravado, não aplicado**: corrigido [execução] |
| Holdout selado só com aprovação humana; nunca consulta iterativa | Prompt 4, item 6 | **só gravado, não aplicado**: corrigido [execução] |
| Nenhum segredo nem dado da máquina em artefato | série, `COMUM.md` | hostname no `STARTED` do ledger (fora do Git): corrigido [execução] |
| Decisão só com comparação a baseline | 3b, item 6 | a decisão também se aplicava ao próprio baseline: corrigido [execução] |
| Achados aceitos pelo dono atualizados na qualificação | D-21 | ST-F007/F008 seguiam `OPEN`: corrigido na PR #48 do `predictor-qualification`, já mergeada com CI verde [execução] |
| Nunca apagar branches | `COMUM.md` | **violado nesta revisão**: apaguei a branch local `review-tmp`, sem commits próprios, apontando para `origin/main` [inspeção] |

## 3. Inconsistências encontradas

1. A política v1 estava `PROPOSED_PENDING_OWNER_APPROVAL`, mas `decide()` devolvia `PASS`/`REJECT` como se valesse.
   Nenhuma decisão histórica mudaria: os 8 `DECISION` do ledger são todos `NO_DECISION` por falta de amostra, de
   baseline ou de DSR [execução: leitura do ledger].
2. `PREREGISTERED`, `HOLDOUT_SEALED` e `HOLDOUT_OPENED` eram só registros: `run_evaluation` não os consultava.
3. `forecast_eval` pedia decisão da política sobre `ew_universe` e `index_buy_and_hold`, que são as próprias
   referências (seqs 23/24 e 38/39 do ledger).
4. O `STARTED` gravava `process.host` com o nome da máquina. O ledger de domínio fica fora do Git. Nenhuma evidência
   versionada contém o hostname [execução: `git grep`].
5. `load_config` vivia em `__main__` e era importado por `validation` e `forecast_eval`: módulos de biblioteca
   dependiam da CLI.
6. As CLIs `validation` e `forecast_eval` não aceitavam `hypothesis_id`, então a exigência de pré-registro só valia
   para quem chama a biblioteca.
7. O README do protocolo dizia "não existe construtor de dataset PIT real", "nada foi baixado" e "não há série de
   rf real", o que era verdade antes do 3c. Não documentava o uso de `forecast_eval`, `reassessment`, selo de
   holdout nem índice do ledger. `STOCKS_CURRENT_STATE.md` e `AGENTS.md` não mencionavam o v2.
8. ST-F007/F008 continuavam `OPEN` no `FINDINGS.json` apesar da D-21.
9. O `.gitignore` não cobria `.env`. Não havia `.env` no repositório [execução: `git check-ignore` e scan].
10. A mensagem do motivo tratava `RETIRED` como "ainda não aprovada". Encontrado no segundo ciclo.
11. `forecast_eval` não calcula DSR nem PBO, então a decisão da carteira é sempre `NO_DECISION`. Isso não estava
    dito. Agora está documentado: decidir uma carteira exige a `validation` (3b). Encontrado no segundo ciclo.

## 4. Prompts melhorados

Ver [auditoria dos prompts](../continuation/2026-09-25-serie-stocks-revisada.md): o bloco comum revisado, os deltas
de 3b, 3c e 4 e as lacunas da missão noturna. Os arquivos originais fora do repositório não foram editados.

## 5. Decisões revistas

- **Série executada uma vez, sem reexecução.** O dono colou a série de novo durante esta revisão. Ela foi usada como
  texto canônico da auditoria, não como pedido de reexecução: rodar de novo duplicaria trials no ledger e inflaria o
  N do DSR.
- **Registros históricos intactos.** O ledger é uma cadeia de hashes, e as evidências dos PRs anteriores estão
  congeladas (AGENTS.md: "Não corrigir caminhos dentro de evidências congeladas"). As correções valem daqui para a
  frente; os `STARTED` antigos com `host` continuam reconhecidos.
- **"aprovadp" não virou aprovação.** A mensagem não nomeia o objeto, e a política continua `PROPOSED`.
- **COTAHIST 2019–2025 sem uso.** Reexecutar hipótese encerrada exige a `reopen_policy`, e reproduzir os vereditos
  exige o banco do PC 1. Os arquivos ficam no PC 2 com recibo.
- **Caminhos com o usuário local nas evidências.** Aparecem em 193 arquivos versionados desde 02/09, inclusive no
  `RESEARCH_FREEZE.md`. É prática do repositório. Mudar isso é decisão do dono, não correção desta revisão.

## 6. Correções

| Arquivo | Correção | Prova |
|---|---|---|
| `v2/policy.py` | `STATUSES` validados; só `APPROVED` decide; `decision_if_approved` registra o hipotético; motivo distinto para `RETIRED` | `test_unapproved_policy_never_decides_but_records_what_it_would_decide`, `test_retired_policy_never_decides` |
| `v2/manifest.py` | `host_id` (hash) no lugar do hostname; `ledger.refresh()`; pré-registro, `max_variants` e holdout aplicados antes do `STARTED`; `ledger_index` + CLI `index` | `test_ledger_never_writes_the_host_name`, `test_legacy_records_with_host_name_are_still_recognized`, `test_ledger_index_is_verifiable_and_free_of_process_data`, `test_evaluation_of_a_hypothesis_requires_preregistration_and_respects_max_variants`, `test_sealed_holdout_blocks_evaluation_until_opened_and_then_allows_one_query` |
| `v2/preregistration.py` | Consulta delegada ao ledger, sem cópia da lógica | mesmos testes do Prompt 4 |
| `v2/config.py` (novo), `__main__.py`, `validation.py`, `forecast_eval.py` | `load_config` fora da CLI | suíte v2 inteira |
| `v2/forecast_eval.py` | Só a carteira candidata recebe decisão; `--hypothesis-id` | `test_forecast_run_is_ledgered_with_contamination_and_rank_portfolio`, `test_forecast_candidate_portfolio_is_a_variant_of_the_preregistered_hypothesis` |
| `v2/validation.py` | `--hypothesis-id`: a família é o conjunto de variantes | `test_validation_cli_ties_the_family_to_a_preregistered_hypothesis` |
| `v2/forecast_metrics.py` | Docstring com versão, licença e dependências do `fev` conferidas | inspeção |
| `.gitignore` | `.env`, `.env.*`, `*.env` | `git check-ignore` |
| README do protocolo, `STOCKS_CURRENT_STATE.md`, `AGENTS.md` | Estado real depois do 3c/4, uso das CLIs, governança | `check_project_files` |
| `evidence/ledger/stocks-domain-ledger-index.json` | Índice verificável do ledger de domínio (56 registros, cabeça `f9dc9367…`), sem dados de processo; `DECISION` com `decision_if_approved` (nulo nos registros anteriores a 25/09) | sha256 do ledger igual antes e depois; zero ocorrências de hostname, `process`, `pid` e usuário |
| `evidence/review-20260925/` e `review-20260925-ciclo2/` | Recibos R8 novos, um por mudança do pacote: real, 55986 linhas; capacidade, 250000; ambos PASS | `verify_operational_evidence`: PASS, 257 arquivos de código [execução] |
| `predictor-qualification` PR #48 | ST-F007/F008 `ACCEPTED_BY_OWNER` (D-21); GATES com nota; attestation reemitida (P2 abertos 5 → 3); a anterior foi preservada como `_superseded_` | CI `check` SUCCESS; mergeada. No `main` pós-merge `a15b6b1`: `attest.py check` OK e `verify_attestation` com as 11 regras e `all_ok: true` [execução] |

## 7. O que foi preservado

- Motores legados, circuito `research_*`, vereditos, `RESEARCH_FREEZE.md` e trials históricos.
- O ledger de domínio: só leitura.
- As evidências dos PRs #98 a #104.
- Os resultados de 3c e 4.
- O status da política.
- O runtime qualificado `61fc017` / 0.3.0rc2.
- Os prompts originais.

## 8. Testes realmente executados

Execuções locais no PC 2 (WSL, Python 3.13 do venv da suíte):

- `pytest tests/test_v2_*.py`: **126 passed** no estado final [execução].
- `ruff check stocks_predictor tests tools/chronos_forecast.py`: sem achados [execução].
- `pyright --pythonversion 3.13` e `3.14`: 0 erros [execução].
- Índice do ledger: gerado pela CLI nova sobre o ledger real [execução].
- `predictor-qualification`: `attest.py check` OK e `verify_attestation` com `all_ok: true` no commit da PR #48 e no
  `main` pós-merge `a15b6b1` [execução].
- Holdout real, numa cópia do ledger de domínio [execução]. O snapshot COTAHIST A2026 (corte 2026-09-09) passa. A
  janela até 2026-09-30 e um dataset com corte em 2026-09-15 são recusados ("holdout selado
  stocks-prospective-2026-09-10 … ainda não aberto"). O sha256 da cópia ficou igual.

- R8 nos dois estados do pacote: real e capacidade PASS; `verify_operational_evidence` PASS [execução].
- `check_project_files`: PASS, zero links não resolvidos [execução].
- gitleaks `protect --staged`, com a configuração do repositório e com a padrão: sem vazamentos. O diff não contém
  o hostname [execução].

## 9. O que não pôde ser verificado

- **Qualificação do v2** [não validado]: o pacote é posterior ao runtime qualificado; requalificar (C14) é decisão do
  dono.
- **Resultado econômico** [não validado]: nenhuma hipótese tem amostra para decidir, e o holdout só abre depois de
  2027-09-10.

## 10. Suíte isolada e CI

A suíte completa, com o mesmo comando do step "Tests" do CI, rodou no commit `83a0251` com a árvore limpa:

- `env -i` (só PATH, HOME, LANG);
- `unshare --net`, e a sonda de rede deu `Network is unreachable`;
- resultado: **1174 passed, 71 subtests passed**, em 339 s, exit 0 [execução].

São 8 testes a mais que no Prompt 4 (1166). O segundo ciclo mudou 3 linhas de código e acrescentou 1 teste, e a
suíte roda de novo no commit final. O resultado dela e o do CI ficam no PR, porque este arquivo já estaria
commitado.

## 11. Pendências e riscos

- **Decisões do dono:**
  - aprovar ou alterar os limiares da política v1, nomeando versão e sha256;
  - requalificar o v2 (C14);
  - fazer o merge da PR desta revisão (a #48 do `predictor-qualification` já foi mergeada);
  - decidir sobre caminhos com o usuário local em evidências futuras.
- **Risco:** os `STARTED` antigos do ledger de domínio guardam o hostname. O ledger não deve ser publicado inteiro;
  publique o índice.
- **Risco:** o holdout é aplicado na avaliação, não na leitura do arquivo. Quem abrir o ZIP vê os dados; a garantia
  é que nenhuma execução registrada usa esses dados antes da abertura.
