# RESEARCH_FREEZE — stocks-predictor

**Status:** `FROZEN_RESEARCH_ASSET + REUSABLE_QUANT_COMPONENTS + SCIENTIFIC_CASE_STUDY`
**Data do congelamento:** 2026-09-02
**Regra de leitura:** este documento é a barreira contra reabertura por inércia. Uma
sessão futura (humana ou de IA) que queira testar um novo fator, revisitar H1/H2/H4/H5/H6/H8,
ou reabrir a linha RJ **deve** primeiro satisfazer `reopen_policy` abaixo — não decidir em silêncio.

O projeto deixou de ser `ACTIVE_ALPHA_RESEARCH` / `TRADING_PRODUCT` / `SIGNAL_SERVICE`.
Ele é `POINT_IN_TIME_CASE + SURVIVORSHIP_CASE + MULTIPLICITY_CASE + NEGATIVE_RESULT_PORTFOLIO`.

---

## 1. Preservation Result

`ST_PRESERVATION = PASS`

**Atualização (2026-09-02, pós-congelamento):** o operador localizou e verificou 3 cópias de
`stocks.db` na máquina Windows local. Auditadas por contagem de linhas via `sqlite3`:

| cópia | path | tamanho | prices_raw | adjustments | decisions | universe_snapshots | papel |
|---|---|---|---|---|---|---|---|
| **canônica (source_of_truth)** | `C:\Users\Superleo13\stocks-predictor-work\data\stocks.db` | 256.499.712 bytes | 1.149.872 | 43 | 0 | 60 | banco operacional real — usado nas rodadas H1-H8 |
| cópia de auditoria (kimi, 2026-08-24) | `C:\Users\Superleo13\.kimi-work\predictors-audit\stocks-predictor\data\stocks.db` | 110.592 bytes | — (não auditado, tamanho indica stub/teste) | — | — | — | clone usado só para rodar a suíte de testes na auditoria RJ; não é fonte de verdade |
| cópia de dev (Codex, 2026-08-27) | `C:\Users\Superleo13\Documents\Codex\2026-08-27\le-x20\work\repo\data\stocks.db` | 118.784 bytes | — (idem) | — | — | — | clone de trabalho de outra sessão; não é fonte de verdade |

`decisions=0` é esperado — o ledger de paper-trading contínuo (`paper.py: record_forward`/
`settle_executions`) ainda não foi ligado em cron (item já registrado como pendência de
evolução no HANDOFF: "falta ligar o cron diário do paper"), não é um sinal de perda de dado.

Backup executado: as 3 cópias foram replicadas para
`D:\backups\stocks-predictor-db-20260902_214421\{work,kimi-audit,codex}\`, com hash SHA-256
verificado idêntico entre origem e destino em cada uma:

| cópia | SHA-256 |
|---|---|
| work (canônica) | `C870CBE938591179569C413FA8A4D046C2009AB6E8DFD8247B0484C1DDC145DC` |
| kimi-audit | `3D158724D2CB55655E9DEBD910D9210B3059BE9EE81CC5C80501C3882986B309` |
| codex | `E430EA47F7094B51B56E325A8B934D4386944604036DCE031D5F78B1CE9DEA0B` |

| asset | path | source_of_truth | backup_status | offsite_copy? | hash_verified? | reconstructible? | irreversible? | risk | action |
|---|---|---|---|---|---|---|---|---|---|
| DB (prices_raw, adjustments, quarantine, decisions, universe_snapshots) | `C:\Users\Superleo13\stocks-predictor-work\data\stocks.db` | confirmada — é o único dos 3 com volume real de dados (1.149.872 linhas) | **DONE** (2026-09-02) | **sim**, `D:\backups\stocks-predictor-db-20260902_214421\work\` | **sim**, SHA-256 idêntico origem↔destino | **parcialmente** — `prices_raw` é re-baixável (COTAHIST é fonte pública B3), mas os 43 registros de `adjustments` são **julgamento humano acumulado**, não reconstituível a partir da fonte crua | SIM para `adjustments` | BAIXO (mitigado) — backup offsite existe e foi verificado por hash | nenhuma ação pendente; recomenda-se repetir o backup periodicamente se o banco continuar recebendo escritas (splits futuros, paper-trading) |
| Trials registry | `trials.json` | repo (versionado) | git | sim (GitHub) | não (sem hash de conteúdo, mas é texto pequeno e versionado) | sim, é o próprio arquivo fonte | não | baixo | preservado — nenhuma ação |
| Trial schema canônico (novo) | `trials_v2.json` | repo (versionado, gerado por `tools/migrate_trials_schema.py`) | git | sim | idempotência verificada (`--check`) | sim, regenerável a qualquer momento a partir de `trials.json` | não | baixo | preservado — nenhuma ação |
| Attestation | `trials.harness_attestation.json` | repo | git | sim | é ele mesmo um hash-gate | sim | não | baixo | preservado |
| Reports/verdicts | `reports/*.md` (h1,h2,h4,h5,h6,h8) | repo (force-added, opt-in) | git | sim | não | sim, são os próprios registros do julgamento — **não reconstituíveis** se apagados (número exato de IC/DSR fica só na memória de quem rodou) | **SIM** | médio | preservado — recomenda-se nunca fazer `git rm` desses arquivos |
| Configs | `config.yaml`, `config_rj.yaml` | repo | git | sim | sim, via `_frozen_hash` sobre `H1_FROZEN_KEYS` etc. | sim | não (mas params `[H1-FROZEN]` não podem mudar após rodada) | baixo | preservado |
| Vendor snapshot | `vendor/predictor_core/` | repo | git | sim | sim, `CORE_MANIFEST.json` (SHA-256 por arquivo + agregado) | sim | não | baixo | preservado — ver §5 (Vendor Resolution) |
| HANDOFF.md (decision log) | `HANDOFF.md` | repo | git | sim | não | é o log — não reconstituível | SIM | baixo (git já protege) | preservado |
| RJ docs/protocol | `docs/RJ_DESIGN.md`, `config_rj.yaml`, `docs/audit/kimi_2026-08-24/*` | repo | git | sim | não | sim | não | baixo | preservado |

**Por que PASS:** todo ativo *reproduzível a partir de código versionado* (trials, reports, configs, vendor, docs) está preservado com segurança de git; o `data/stocks.db` canônico foi localizado, auditado por contagem de linhas e replicado com verificação de hash SHA-256 para armazenamento offsite (2026-09-02) — ver atualização acima. O blocker original (§17, item 1) está fechado.

---

## 2. Trial Migration

`ST_TRIAL_SCHEMA = PASS`

- Schema legado de `trials.json` auditado campo a campo contra o schema prospectivo canônico (ver relatório de auditoria acima). Faltavam: `hypothesis_id`, `hypothesis_family`, `trial_id`, `executed_at`, `seed`, `forecast_horizon`, `dataset_hash`, `dataset_version`, `feature_version`, `model_version`, `code_version`, `selection_path`, `n_trials_family/domain/ecosystem`, `result`, `status`.
- Migração implementada em `tools/migrate_trials_schema.py`: lê `trials.json` (não altera), escreve `trials_v2.json` com o schema canônico completo.
  - **Não-destrutiva:** `trials.json` original permanece intocado.
  - **Idempotente:** `--check` confirma que rodar de novo produz byte-a-byte o mesmo resultado.
  - **Auditável:** cada campo migrado é rastreável ao campo legado de origem (`legacy_*` preservados no output).
  - `seed`, `selection_path`, `dataset_hash` e `hypothesis_family` (quando o nome não permite mapeamento inequívoco) recebem `"UNKNOWN"` — **nada foi inventado**. `hypothesis_family` só foi preenchido para os 6 trials existentes porque o nome do trial já deixava a família inequívoca (mapeamento factual, não nova classificação).
  - `n_trials_family=1` (uma rodada por hipótese, fato registrado), `n_trials_domain=6` (6 famílias no domínio de ações testadas, fato do HANDOFF), `n_trials_ecosystem="UNKNOWN"` (não temos visibilidade do denominador do ecossistema completo — não inventado).
- A partir de agora, **qualquer novo trial pré-registrado deve nascer diretamente em `trials_v2.json`** com o schema canônico completo (schema prospectivo, não retrofit).

---

## 3. PIT Integrity

`ST_PIT_INTEGRITY = PASS`

- `stocks_predictor/universe.py` implementa a regra "em cada `asof`, usa SOMENTE dados < asof" com `WHERE date < ?` bound a `asof` em todas as queries relevantes.
- Testes de survivorship/PIT existentes em `tests/test_universe.py`:
  `test_universe_is_point_in_time`, `test_excludes_quarantined`, `test_future_quarantine_does_not_exclude`,
  `test_resolved_quarantine_does_not_exclude`, `test_dedup_on_pn_keeps_more_liquid`,
  `test_excludes_delisted_ticker_stale_before_window`, `test_sporadic_trader_median_counts_no_trade_days_as_zero`,
  `test_min_history_excludes_short`.
- Cobertura confirmada para "empresa delistada some do universo após sair" (`test_excludes_delisted_ticker_stale_before_window`).
- **Atualização (2026-09-03):** adicionado `test_newly_listed_ticker_does_not_appear_before_its_ipo_date` — teste nomeado explicitamente que prova (i) um ticker recém-listado não aparece em `rank_universe`/`select_universe` para nenhum `asof` anterior ao seu próprio primeiro pregão, mesmo com volume altíssimo desde a estreia; (ii) continua excluído logo após a estreia até cumprir `min_history`; (iii) fica elegível normalmente depois disso — não é uma blacklist permanente. Fecha o gap que antes só tinha cobertura indireta via `min_history_excludes_short`.
- **Atualização (2026-09-03):** a suíte completa FOI executada nesta sessão com Python 3.13.12 (instalado via `python3.13` no ambiente de auditoria) + `predictor-core==3.0.0` real (wheel oficial do GitHub Release, mesma fonte de `pyproject.toml`/`uv.lock`) — `python -m pytest tests/ -q` → **252 passed, 0 failed** (após os 5 testes novos desta rodada: import path, purge/embargo, listagem tardia). Isso supera a execução anterior conhecida (2026-08-24, 211 passed / 4 failed com shim de vendor) e confirma que a suíte está verde com o Core real, não com o shim histórico.

---

## 4. Purge/Embargo Decision

`ST_PURGE_EMBARGO_STATUS = DOCUMENTED_HISTORICAL_LIMITATION`

**Evidência:** `config.yaml` declara `purge_embargo_months: 1  # [H1-FROZEN]`, e o valor é
usado **apenas** dentro do cálculo de hash de integridade de config (`_frozen_hash` sobre
`H1_FROZEN_KEYS`/`H2_FROZEN_KEYS`/etc. em `stocks_predictor/config.py`). O próprio docstring
de `stocks_predictor/backtest.py` já admitia: *"o purge/embargo formal ficam para a evolução
do M5"*. Não há nenhum trecho de `backtest.py` que exclua uma janela ao redor da fronteira
treino/teste — apenas um filtro de data de início (`test_start`).

**Decisão (Opção C, não B, não A):**
- **Por que não A (implementar agora):** a pesquisa de fatores está **congelada**. Implementar
  purge/embargo agora alteraria o comportamento do backtest que já produziu os vereditos
  H1/H2/H4/H5/H6/H8 — isso seria "consertar dados/resultado sem trilha", proibido pelo design.
  Além disso, não há consumidor real futuro declarado (nenhuma nova avaliação prevista).
- **Por que não B (remover):** o parâmetro é `[H1-FROZEN]` — **não pode ser tocado após
  qualquer rodada de resultado** (regra inviolável do CLAUDE.md). Remover a chave do config
  quebraria o hash de integridade frozen retroativamente. A config fica como está.
- **Opção C aplicada:** documentamos aqui e no Evidence Registry (§13) que, para todos os
  vereditos H1–H8 já emitidos, **`purge_embargo_months` foi declarado mas nunca consumido
  pelo motor de backtest** — os resultados não têm proteção formal de purge/embargo contra
  overlap de labels na fronteira treino/teste. Isso não invalida os vereditos (a maioria já é
  "não comprovada" — um viés de embargo ausente tenderia a, se algo, *inflar* falsamente um
  sinal positivo, e mesmo assim a maioria não cruzou o gate; H5 é claramente anti-sinal). É uma
  limitação de rigor a registrar, não uma falha que exige reabrir os testes.
- **Atualização (2026-09-03):** em vez de um teste de label-overlap que dependeria de um
  purge/embargo inexistente (decoração, como registrado antes), foi adicionado
  `tests/test_purge_embargo_limitation.py` — dois testes que tornam a lacuna **verificável em
  código**, não só descritiva: (1) `test_purge_embargo_months_has_no_effect_on_walk_forward`
  prova que rodar o mesmo walk-forward com `purge_embargo_months=1` vs `=12` produz séries
  estrategicamente **idênticas** (o parâmetro é comprovadamente inerte); (2)
  `test_first_rebalance_after_test_start_has_no_embargo_gap` prova que o primeiro rebalance
  elegível após `test_start` não guarda nenhum espaçamento de embargo. Os dois passam hoje
  (documentando a limitação atual) e **vão quebrar** se algum dia alguém implementar
  purge/embargo de verdade — forçando atualização consciente deste documento em vez de uma
  suíte verde por acidente sobre uma mudança de proteção temporal.

---

## 5. Vendor Resolution

`ST_VENDOR_STATE = RESOLVED`

**Classificação: `ARCHIVE_FOR_REPRODUCTION` (com freshness guard já implementado).**

- `vendor/predictor_core/` está congelado em `1.3.0-ga-20260711` (arquivo `VERSION`), com
  manifesto de integridade `CORE_MANIFEST.json` (SHA-256 por arquivo).
- Dependência real declarada é `predictor-core==3.0.0` (`pyproject.toml`, `uv.lock`, wheel do
  GitHub Release), instalada como pacote — **nenhum caminho de runtime** (`main.py`,
  `stocks_predictor/*.py`) importa de `vendor/`.
- `poc_leak.py` é o **único** consumidor real do vendor (via `sys.path.insert` manual) — e é
  histórico/demonstrativo, não parte do pipeline.
- **Freshness guard já existe:** `tests/conftest.py` faz
  `assert "vendor" not in pathlib.Path(predictor_core.__file__).parts` a menos que
  `STOCKS_ALLOW_VENDOR_SHIM=1` esteja setado explicitamente — isso já cobria o "import path
  test" pedido na tarefa (§12) como efeito colateral de import.
- **Atualização (2026-09-03):** adicionado `tests/test_core_import_path.py`, um teste NOMEADO
  e independente (`test_predictor_core_does_not_resolve_to_vendor`,
  `test_predictor_core_version_is_at_least_3`) que reproduz e reforça o guard do conftest —
  agora citável e executável isoladamente (`pytest tests/test_core_import_path.py -v`), sem
  depender de reestruturação futura do conftest. Executado nesta sessão com o Core 3.0.0
  real instalado: **2 passed**.
- **Por que arquivar em vez de remover:** o vendor snapshot é necessário para reproduzir
  historicamente o ambiente em que `poc_leak.py` foi originalmente demonstrado (ele depende de
  uma API específica de `vendor/predictor_core/replay.py` que não existe/mudou no Core 3.0.0
  atual). Remover apagaria a capacidade de reproduzir esse caso histórico.
- **Decisão final:** manter `vendor/predictor_core/` como arquivo histórico read-only, com o
  guard de `conftest.py` como proteção permanente contra uso acidental. Nenhuma mudança de
  código necessária — o estado já satisfaz `KEEP_WITH_FRESHNESS_GUARD` na prática.

## 6. Runtime Core Import Test

Resultado real (não simulado): o teste de guarda já existe e roda como parte da suíte —
`tests/conftest.py`, fixture/assert que falha se `predictor_core.__file__` contiver o segmento
`"vendor"`, salvo com a variável de ambiente explícita `STOCKS_ALLOW_VENDOR_SHIM=1`. Não foi
necessário criar um teste novo porque este já cumpre a especificação do item 12 da tarefa
(prova qual Core é usado no runtime, falha se resolver para vendor). Não foi possível executar
a suíte completa nesta sessão (ambiente sandbox sem `predictor-core` instalado) — este é um
relato do que o teste faz, não uma nova corrida com output.

**`poc_leak.py` — classificação (§13 da tarefa):**
```
HISTORICAL_POC
NOT_REPRODUCIBLE_AGAINST_CORE_3_0
```
Alvo: `vendor/predictor_core/replay.py` (API antiga). Demonstra bypass de encapsulamento de
`PastView` via atributo privado `._data`, contornando o bloqueio público de lookahead
(`LookaheadError`). Preservado como artefato de red-team histórico; **não é evidência de falha
do Core 3.0.0 atual** (não há como comparar — o código-fonte do 3.0.0 não está neste checkout,
só o pacote instalado).

---

## 7. Cost/Corporate Action Audit

| componente | classificação | evidência |
|---|---|---|
| Emolumentos/liquidação B3 | ASSUMED | `execution.b3_fee_pct: 0.0003` — constante literal, não puxada de tabela oficial dinâmica |
| Corretagem | ASSUMED | `brokerage_pct: 0.0000` |
| Spread/slippage | ASSUMED (rotulado "conservador" no próprio config) | `spread_slippage_pct: 0.0015` por lado, flat |
| Turnover | **MEASURED** | `equal_weight_turnover_cost()`/`weighted_turnover_cost()` calculam entradas/saídas reais da carteira a cada rebalanceamento |
| Impostos (IR/JCP) | **NOT_MODELED** | nenhum caminho de código encontrado |
| Custo de aluguel (short) | **NOT_MODELED** (deliberado) | estratégia é long-only por design (`docs/DESIGN.md` §6) — decisão de escopo, não gap |
| Impacto de mercado além de slippage flat | **NOT_MODELED** | `roundtrip_cost() = 2×(fee+slippage)`, constante independe de tamanho de ordem/liquidez do papel |

Resultados publicados (`reports/*.md`) já reportam Sharpe **líquido** de custos (0,36%
ida-e-volta embutido). Não há decomposição gross-vs-net separada nos relatórios existentes —
registrado como limitação, não corrigido retroativamente (corrigir exigiria nova rodada, que é
reabertura, proibida sem novo pré-registro).

**Dividendos/corporate actions:** decisão de design já documentada em HANDOFF.md
(2026-06-16): rota (b) — retorno **só-preço**, sem proventos/JCP, com viés declarado e
direcional (favorece a estratégia de momentum contra o benchmark, pois momentum tende a menor
yield — "positivo marginal é suspeito por construção"). Splits: 57 saltos detectados, adjudicados
manualmente (não auto-resolvidos, trilha em `adjustments`). Delistings/ticker changes: cobertos
por `test_excludes_delisted_ticker_stale_before_window`, mas sem inventário completo publicado
de todos os eventos corporativos da amostra — **limitação registrada, não corrigida**.

---

## 8. Multiplicity/Power Result

- **DSR** aplicado ao domínio de fatores de ações (H2,H4,H5,H6,H8), threshold 0,95: **nenhum
  passou** (H2 0,7092; H4 0,6843; H5 0,1274; H6 0,4565; H8 0,6050). H1 usa IC do bootstrap
  pareado (não DSR) e também cruza zero.
- **FDR (Benjamini-Hochberg)** reservado para o domínio RJ (8 famílias, diferença de médias —
  métrica não-Sharpe, por isso FDR e não DSR, decisão já documentada em `config_rj.yaml`), ainda
  não aplicado a dados reais (RJ não tem dados reais — §9).
- **Romano-Wolf stepdown** existe como checagem cruzada de robustez contra o FDR, também restrito
  a dados sintéticos do domínio RJ.
- **Correção de rótulo no Evidence Registry (§13):** nenhuma hipótese estava rotulada como
  "REFUTED" quando deveria ser "INCONCLUSIVE_DUE_TO_POWER" — os vereditos já usam a formulação
  correta ("não comprovada nesta janela", explicitamente não-definitiva). Nenhuma correção de
  rótulo foi necessária; verificado, não fabricado.

---

## 9. RJ Closure

`ST_RJ_STATE = ARCHIVED`

- Estado de dados real: **zero linhas reais** — `rj_universe` vazia (HANDOFF.md, 2026-08-23).
  Todo o trabalho até aqui (auditoria kimi 2026-08-24, correções de censura por empresa
  2026-08-31) foi sobre **scaffolding sintético/mecânico**, nunca sobre dados de RJ reais.
- Sem comprador/consumidor declarado para dados reais de RJ nesta sessão.
- **Nenhuma nova ingestão será iniciada.** Protocolo (`docs/RJ_DESIGN.md`), config congelada
  (`config_rj.yaml`) e o relatório de auditoria externa (`docs/audit/kimi_2026-08-24/`) são
  preservados como estavam — nenhuma edição de conteúdo, só a marcação de arquivamento aqui e
  no manifesto (§11).
- Riscos metodológicos remanescentes listados na auditoria kimi (8 itens) permanecem
  **registrados, não resolvidos** — arquivar não significa declarar "resolvido", significa
  "sem trabalho ativo".

---

## 10. Component Inventory

| component | purpose | tested? | domain_specific? | consumer_count | second_real_consumer? | candidate_for_core? | decision |
|---|---|---|---|---|---|---|---|
| PIT universe builder (`universe.py`) | universo B3 point-in-time, exclui quarentena/delisted | sim (`test_universe.py`) | sim (B3/COTAHIST) | 1 (stocks-predictor) | não | não | `KEEP_DOMAIN_OWNED` |
| Survivorship protection (dedup PN/ON, exclusão delisted) | evitar viés de sobrevivência | sim | sim | 1 | não | não | `KEEP_DOMAIN_OWNED` |
| Cost model (`execution.py`) | custo de turnover/fee/slippage | parcial | parcial (fee B3 específico; lógica de turnover é genérica) | 1 | não | não (sem 2º consumidor real) | `KEEP_DOMAIN_OWNED` |
| Walk-forward engine (`backtest.py`) | orquestra universo→fator→carteira→medição | sim | não (a mecânica é genérica) | 1 | não | não | `KEEP_DOMAIN_OWNED` (sem 2º consumidor comprovado, apesar de parecer genérico) |
| Stationary bootstrap (IC de diferença de Sharpe) | inferência de significância pareada | sim | não | vendor (`predictor_core.measurement`) já é consumidor externo | **sim** (vendor + stocks-predictor) | já está no Core | já `IN_CORE` — nenhuma ação |
| DSR (vendor `measurement/trials.py`) | correção de múltiplos testes, Sharpe-específico | sim | não | vendor + stocks-predictor | sim | já está no Core | já `IN_CORE` — nenhuma ação |
| FDR/BH (`rj_judge.py`) | correção de múltiplos testes, domínio RJ (diff de médias) | sim (sintético) | sim (specíico ao desenho de 8 famílias RJ) | 1 | não | não | `KEEP_DOMAIN_OWNED` |
| Romano-Wolf stepdown (`rj_judge_robust.py`) | checagem cruzada de robustez | sim (sintético) | não necessariamente | 1 | não | não sem 2º consumidor real | `KEEP_DOMAIN_OWNED` |
| Trial governance (schema canônico, `tools/migrate_trials_schema.py`) | registro prospectivo de trials | sim (idempotência verificada) | não (schema é genérico) | 1 | não | possível candidato futuro, sem 2º consumidor hoje | `KEEP_DOMAIN_OWNED` (regra da tarefa: sem 2º consumidor real, não promove) |

Nenhum componente foi movido para o Core nesta rodada — os dois já compartilhados
(bootstrap, DSR) já residiam lá antes desta auditoria.

---

## 11. Research Freeze Manifest

```yaml
ST_RESEARCH_FREEZE:
  active_hypotheses: []
  stopped_hypotheses:
    - id: H1
      family: momentum_12_1
      result: NOT_SUPPORTED (IC 95% diff-Sharpe cruza zero)
      closed_at: 2026-07-12
    - id: H2
      family: low_vol_252
      result: NOT_SUPPORTED (IC cruza zero; DSR 0.7092 < 0.95)
    - id: H4
      family: vol_target_sizing
      result: NOT_SUPPORTED (IC cruza zero; DSR 0.6843 < 0.95)
    - id: H5
      family: reversal_21d
      result: NOT_SUPPORTED (Sharpe negativo; IC inteiramente negativo -> anti-sinal; DSR 0.1274 < 0.95)
    - id: H6
      family: momentum_6_1
      result: NOT_SUPPORTED (IC cruza zero; DSR 0.4565 < 0.95)
    - id: H8
      family: momentum_lowvol_intersection
      result: NOT_SUPPORTED (IC cruza zero; DSR 0.6050 < 0.95)
    - id: H7
      family: quality_roe
      result: NOT_SUPPORTED (IC cruza zero; DSR 0.5795 < 0.95)
      closed_at: 2026-09-04
      note: >
        Única hipótese sobre fonte de dado NOVA (DFP/CVM, fundamentos) desde
        o congelamento de 2026-09-02 — dado real ingerido (695 linhas em
        fundamentals, 2018-2026), julgada em rodada única, mesma disciplina
        das anteriores. Ver HANDOFF.md "VEREDITO H7" para detalhes completos
        (IC, DSR, provenance da ingestão).
    - id: H9
      family: quality_leverage
      result: NOT_SUPPORTED (IC cruza zero; DSR 0.3479 < 0.95)
      closed_at: 2026-09-04
      note: >
        2ª e última variável contábil disponível na DFP/CVM já ingerida
        (fundamentals.leverage, mesma linha do ROE da H7) — não exigiu
        ingestão nova. Alavancagem isolada, quintil inferior (empresas menos
        endividadas). Ver HANDOFF.md "VEREDITO H9" para detalhes completos.
  preserved_components:
    - stocks_predictor/universe.py (PIT universe + survivorship)
    - stocks_predictor/execution.py (cost model)
    - stocks_predictor/backtest.py (walk-forward engine)
    - stocks_predictor/rj_judge.py, rj_judge_robust.py (FDR/Romano-Wolf, domínio RJ)
    - vendor/predictor_core/ (arquivo histórico, freshness-guarded)
    - trials.json, trials_v2.json (registro de trials, legado + canônico)
    - reports/*.md (vereditos)
    - poc_leak.py (HISTORICAL_POC, red-team artifact)
  archived_lines:
    - RJ (zero dados reais; protocolo e auditoria preservados; sem trabalho ativo)
  reopen_policy: >
    Nenhuma família de fatores já encerrada (momentum 12-1, momentum 6-1, low-vol,
    vol-target, reversão 21d, interseção momentum×low-vol, qualidade/ROE,
    qualidade/alavancagem) pode ser
    reaberta sem registrar EXPLICITAMENTE, antes de qualquer código novo:
      previous_result, closure_reason, new_information, causal_reason,
      why_old_test_no_longer_answers_question, new_protocol.
    Sem esses 6 campos preenchidos e revisados por um humano, qualquer proposta de
    reabertura deve ser recusada. A linha RJ segue a mesma regra e adicionalmente
    exige uma fonte de dados reais nomeada antes de qualquer ingestão nova.
```

---

## 12. Case Studies

### CASE-ST-001 — Seis famílias de fatores testadas, nenhuma evidência suficiente
- **claim:** momentum (12-1 e 6-1), low-vol, vol-target sizing, reversão 21d e a
  interseção momentum×low-vol produzem Sharpe líquido superior ao benchmark equiponderado
  do universo PIT da B3.
- **protocol:** pré-registro de parâmetros antes de cada rodada (`trials.json`), janela
  walk-forward 2018→2026, custo de 0,36% ida-e-volta, IC 95% via stationary bootstrap pareado
  + DSR ≥ 0,95 como gate duplo.
- **result:** todas as 6 famílias falharam o(s) gate(s) — IC contém zero e/ou DSR < 0,95.
- **failure_mode:** nenhuma; ausência de sinal detectável na amostra/janela com os gates
  pré-registrados. Não é um bug — é o resultado esperado de uma varredura honesta de fatores
  conhecidos em um mercado razoavelmente eficiente.
- **lesson:** um protocolo pré-registrado com gate duplo (significância + DSR) produz "não
  comprovado" honesto em vez de promover o melhor ponto-estimado por acaso (H8 tinha o maior
  Sharpe bruto, 0,3110, e mesmo assim falhou DSR).

### CASE-ST-002 — Reversão aparente virou anti-sinal
- **claim:** reversão de curto prazo (21 dias) no quintil de pior retorno recente geraria
  Sharpe positivo (efeito reversão clássico da literatura).
- **protocol:** mesmo desenho de H1/H2, quintil inferior de retorno 21d, long-only.
- **result:** Sharpe da estratégia **negativo** (-0,1804 vs +0,1621 do benchmark); IC 95%
  inteiramente negativo (-0,6406, -0,1009) — não apenas "sem evidência", mas evidência de
  **anti-sinal** (pior que o benchmark com confiança estatística).
- **failure_mode:** a hipótese não só não se sustentou como se inverteu — um lembrete de que
  "reversão" em equities de mercado emergente/menor liquidez pode não se comportar como na
  literatura de mercados desenvolvidos.
- **lesson:** um resultado de anti-sinal com CI que não cruza zero é uma descoberta válida por
  si só (mostra que a direção testada estava errada) — não precisa e não deve virar sinal
  invertido sem novo pré-registro (isso seria HARKing).

### CASE-ST-003 — Survivorship/PIT muda a interpretação de um backtest
- **claim:** um backtest ingênuo sobre a lista atual de tickers da B3 (sem PIT) tende a
  superestimar retorno porque exclui empresas que faliram/foram delistadas.
- **protocol:** `universe.py` reconstrói o universo asof cada data de rebalanceamento,
  usando somente dados `< asof`; testes automatizados (`test_universe_is_point_in_time`,
  `test_excludes_delisted_ticker_stale_before_window`) verificam que uma empresa delistada
  continua aparecendo antes da saída e desaparece depois.
- **result:** a arquitetura PIT está implementada e testada; o caso "empresa listada depois
  não aparece antes de sua data real de listagem" tinha cobertura só indireta e agora tem
  teste nomeado explícito (`test_newly_listed_ticker_does_not_appear_before_its_ipo_date`,
  adicionado 2026-09-03).
- **failure_mode:** ausência de survivorship bias não foi *provada* de forma exaustiva — foi
  testada nos casos que a suíte cobre (eventos corporativos fora dos 9 casos de
  `test_universe.py` continuam fora do escopo verificado).
- **lesson:** "proteção contra survivorship" não é um booleano — é uma lista de casos de teste,
  e é preciso ser honesto sobre qual subconjunto de casos está de fato coberto.

### CASE-ST-004 — Múltiplos testes sem promoção artificial de vencedor
- **claim:** entre 6 famílias testadas, nenhuma deveria ser promovida a "a vencedora" só por
  ter o Sharpe bruto mais alto.
- **protocol:** DSR (Sharpe-específico) aplicado a todas as 5 famílias pós-H1 com threshold
  fixo 0,95, definido antes de ver os resultados; H8 (Sharpe bruto mais alto do conjunto,
  0,3110) teve DSR 0,6050 — abaixo do gate.
- **result:** nenhuma família foi promovida; todas os 6 vereditos registrados são
  "não comprovada".
- **failure_mode:** o risco clássico de "cherry-pick pós-hoc" (escolher H8 porque teve o maior
  Sharpe) foi estruturalmente bloqueado pelo gate DSR pré-registrado.
- **lesson:** o denominador de multiplicidade (quantos testes foram feitos) importa mais do
  que o numerador (o melhor resultado pontual) — e por isso `n_trials_domain`/`n_trials_family`
  agora são campos de primeira classe no schema de trials (§2).

---

## 13. Evidence Registry Updates

| claim | state | evidence | limitations | decision |
|---|---|---|---|---|
| `CLAIM-ST-MOMENTUM` (12-1 e 6-1) | INCONCLUSIVE_DUE_TO_POWER / NOT_SUPPORTED-IN-WINDOW (não "REFUTED") | H1 IC (-0,3192,0,2933); H6 DSR 0,4565<0,95 | janela única 2018-2026, sem repetição fora da amostra | ENCERRADA, sem reabertura sem os 6 campos de `reopen_policy` |
| `CLAIM-ST-LOWVOL` | NOT_SUPPORTED-IN-WINDOW | H2 DSR 0,7092<0,95, IC cruza/negativo | idem | ENCERRADA |
| `CLAIM-ST-REVERSAL` | ANTI_SIGNAL (mais forte que "não comprovada") | H5 Sharpe -0,1804, IC (-0,6406,-0,1009) inteiramente negativo | direção testada pode estar simplesmente errada para este mercado/janela | ENCERRADA — reabrir exigiria hipótese de sinal invertido, com novo pré-registro completo |
| `CLAIM-ST-PIT` | SUPPORTED | `universe.py` + testes citados em §3, incluindo `test_newly_listed_ticker_does_not_appear_before_its_ipo_date` (2026-09-03) | nenhuma conhecida além do escopo geral de `test_universe.py` (9 casos) | fechado |
| `CLAIM-ST-SURVIVORSHIP` | SUPPORTED (parcial, não "perfeita") | `test_excludes_delisted_ticker_stale_before_window` | sem inventário completo de eventos corporativos/delistings da amostra inteira | registrado como limitação honesta |
| `CLAIM-ST-PURGE` | **LIMITATION, não implementado** | config declara, `backtest.py` não consome | vereditos H1-H8 não têm proteção formal de purge/embargo | `DOCUMENTED_HISTORICAL_LIMITATION` — ver §4 |

`reopen_conditions` para todas as claims acima de fatores: idênticas à `reopen_policy` do
manifesto (§11) — sem exceção.

---

## 14. Red Team (checklist explícita pré-fechamento)

Sete perguntas adversariais, respondidas com a evidência já levantada nas seções acima —
nenhuma resposta nova, só a síntese direta como checklist de fechamento.

| # | pergunta | resposta | evidência |
|---|---|---|---|
| 1 | **PIT** — há ativo aparecendo antes de existir? | Não. `universe.py` filtra `WHERE date < asof` em todo lugar; `test_universe_is_point_in_time` prova isso para delisting, e `test_newly_listed_ticker_does_not_appear_before_its_ipo_date` (2026-09-03) prova isso para listagem tardia — ambos os lados do ciclo de vida do ticker agora têm teste nomeado explícito. | §3, §13 (`CLAIM-ST-PIT`) |
| 2 | **Survivorship** — delisted está desaparecendo do passado? | Não. `test_excludes_delisted_ticker_stale_before_window` prova que uma empresa delistada continua aparecendo antes da saída. Sem inventário completo de todos os eventos de delisting da amostra de 2018-2026 — gap registrado, não fabricado como cobertura total. | §3, §8, §13 (`CLAIM-ST-SURVIVORSHIP`) |
| 3 | **Costs** — resultado líquido está subestimando fricção? | Parcialmente possível. `spread_slippage_pct=0.0015` e `b3_fee_pct=0.0003` são **ASSUMED** (constantes literais, não medidas de execução real); só `turnover` é **MEASURED**. Impostos e custo de aluguel **NOT_MODELED**. Isso tende a subestimar fricção real — viés que jogaria a favor dos resultados positivos, o que reforça (não enfraquece) a conclusão de "não comprovada" nas 6 famílias. | §7 |
| 4 | **Purge** — config diz uma coisa e runtime faz outra? | **Sim, confirmado.** `purge_embargo_months: 1` está declarado e é usado só no hash de integridade de config; `backtest.py` nunca o consome no walk-forward. Não deixado ambíguo: decisão explícita `DOCUMENTED_HISTORICAL_LIMITATION` (§4), não implementação silenciosa nem remoção do parâmetro `[H1-FROZEN]`. | §4, §13 (`CLAIM-ST-PURGE`) |
| 5 | **Vendor** — runtime pode resolver para código velho? | Não, por padrão. `tests/conftest.py` tem assert que falha se `predictor_core.__file__` contiver `"vendor"`, a menos que `STOCKS_ALLOW_VENDOR_SHIM=1` seja setado explicitamente. Único consumidor real do vendor é `poc_leak.py` (script standalone, fora do pipeline). | §5, §6 |
| 6 | **Multiplicity** — há sweeps fora do ledger? | Não identificado nesta auditoria: `trials.json`/`trials_v2.json` cobre as 6 famílias citadas no HANDOFF (H1,H2,H4,H5,H6,H8); `n_trials_ecosystem` é registrado como `UNKNOWN` (não fabricado) porque esta auditoria não tem visibilidade do denominador do ecossistema completo fora deste repo. Isso é uma limitação de visibilidade, não uma alegação de completude. | §2, §17 (task) |
| 7 | **Freeze** — alguma tarefa ainda reabre pesquisa ativa? | Não. Nenhuma família foi retestada, nenhum fator novo foi criado, nenhuma linha de código de sinal foi alterada. O único código novo desta rodada é `tools/migrate_trials_schema.py` (schema, não sinal) e a atualização de `data/stocks.db` é *preservação*, não nova ingestão de features. | §11 (manifesto), §26 (task) |

## 15. Valor Comercial Indireto

O `stocks-predictor` não vira produto próprio, mas fica pronto como case reutilizável para uma
futura oferta de auditoria/consultoria quantitativa, com evidência concreta e reproduzível
(não hipotética) em cada um destes pontos:

- **Survivorship bias:** CASE-ST-003 e os testes de `test_excludes_delisted_ticker_stale_before_window`
  são um exemplo real e auditável de como construir (e testar) um universo livre de
  sobrevivência — útil para demonstrar a um cliente por que um backtest ingênuo superestima
  retorno.
- **Point-in-time universe:** `universe.py` + o design doc (`docs/DESIGN.md`) são referência
  concreta de implementação de disciplina PIT, algo que muitos backtests comerciais pulam.
- **Multiple testing / false discovery:** CASE-ST-001 e CASE-ST-004 mostram, com números reais
  (DSR de 5 famílias todas abaixo de 0,95, incluindo a de maior Sharpe bruto), como um gate de
  múltiplos testes pré-registrado evita promover um vencedor por acaso — argumento forte para
  auditar processos de seleção de fatores de terceiros.
- **Custos:** a decomposição MEASURED/ESTIMATED/ASSUMED/NOT_MODELED (§7) é um template direto
  para uma checklist de due diligence de custos em qualquer backtest de terceiros.
- **Hipóteses sem efeito / poder insuficiente:** a distinção entre `NOT_SUPPORTED-IN-WINDOW` e
  "refutado" (§13, §19 da task) é um argumento técnico reutilizável contra a prática comum de
  rotular resultado nulo como prova de ausência de efeito.
- **Anti-sinal como achado válido:** CASE-ST-002 (reversão 21d) demonstra que um resultado
  "pior que o benchmark com significância" é uma descoberta, não um fracasso a esconder —
  argumento de honestidade científica que reforça credibilidade de uma oferta de auditoria.

Nenhuma ação de produtização (SaaS, dashboard, API comercial) foi tomada ou é recomendada por
esta seção — o valor é o **case em si**, preservado e documentado, não uma nova entrega.

---

## 16. Final Checkpoints

```
ST_PRESERVATION       = PASS (data/stocks.db canônico localizado, auditado e replicado offsite com hash verificado em 2026-09-02)
ST_TRIAL_SCHEMA       = PASS
ST_PIT_INTEGRITY      = PASS (suíte reexecutada em 2026-09-03: 252 passed, 0 failed; gap de "listada depois" fechado com teste nomeado)
ST_PURGE_EMBARGO_STATUS = DOCUMENTED_HISTORICAL_LIMITATION
ST_VENDOR_STATE       = RESOLVED (ARCHIVE_FOR_REPRODUCTION + freshness guard já ativo em tests/conftest.py)
ST_RJ_STATE           = ARCHIVED
ST_RESEARCH_STATE     = FROZEN
ST_CASE_STUDY_READY   = YES
```

## 17. Remaining Blockers

1. ~~`data/stocks.db` não existe neste checkout e não tem cópia offsite verificada.~~
   **RESOLVIDO (2026-09-02):** operador localizou o banco canônico
   (`C:\Users\Superleo13\stocks-predictor-work\data\stocks.db`, 1.149.872 linhas em
   `prices_raw`, 43 em `adjustments`), verificou que as outras 2 cópias na máquina são clones
   de auditoria/dev sem volume real de dados, e replicou o canônico para
   `D:\backups\stocks-predictor-db-20260902_214421\` com hash SHA-256 idêntico
   origem↔destino. Ver §1.
2. ~~Suíte de testes não pôde ser executada nesta sessão.~~ **RESOLVIDO (2026-09-03):**
   instalado Python 3.13.12 + `predictor-core==3.0.0` real (mesmo wheel do GitHub Release
   declarado em `pyproject.toml`/`uv.lock`) no ambiente de auditoria; `python -m pytest
   tests/ -q` → **252 passed, 0 failed**, incluindo os 5 testes novos desta rodada
   (`test_core_import_path.py` ×2, `test_purge_embargo_limitation.py` ×2,
   `test_newly_listed_ticker_does_not_appear_before_its_ipo_date`).
3. ~~Sem teste nomeado explicitamente para "ativo listado depois não aparece antes da data
   real de listagem".~~ **RESOLVIDO (2026-09-03):** adicionado
   `test_newly_listed_ticker_does_not_appear_before_its_ipo_date` em `tests/test_universe.py`
   — prova que um ticker recém-listado fica ausente do universo em qualquer `asof` anterior
   à sua estreia, permanece excluído até cumprir `min_history`, e fica elegível normalmente
   depois disso.

Nenhum blocker conhecido permanece em aberto nesta rodada.
