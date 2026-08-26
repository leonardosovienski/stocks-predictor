# Relatório de Auditoria — stocks-predictor (predictor-rj)

**Data:** 2026-08-24 · **Branch:** `audit/2026-08-24-fixes` (13 commits sobre `main`)
**Ambiente:** wheels predictor-core/ops indisponíveis → shim `vendor/predictor_core` + shim local `predictor_ops` via `STOCKS_ALLOW_VENDOR_SHIM=1 PYTHONPATH=/mnt/agents/shims:vendor` (precedente do PR #5).
**Estado final da suíte:** 211 passed / 4 failed — as 4 falhas são exatamente as conhecidas de shim (`test_h2_gate` + 3× `test_replay`), inalteradas, não-regressão. `ruff check src tests`: limpo.

---

## 1. Bugs encontrados (severidade · arquivo/linha · reprodução)

### CRÍTICOS

| # | Bug | Local | Reprodução |
|---|-----|-------|-----------|
| C1 | **Lookahead informacional:** fallback `known_at or event_date` — evento publicado após o fundo mas datado antes dele vira "conhecível" (viola Regra 2 e §8/§10 do protocolo) | `rj_families.py:122,172` (ownership, info_trigger — famílias PRÉ-REGISTRADAS); `rj_families_next.py:69` (equity_issuance) | `info_trigger([{"event_date":"2024-05-10","known_at":None,...}], "2024-05-12")` → 1 |
| C2 | **Fila de revisão humana bypassada:** pipeline lia `rj_events` e `rj_universe` sem filtrar `approved_by`; ingest CVM gravava direto na tabela final (viola Regra 5) | `rj_pipeline.py:69,94`; `ingest_cvm.py:175` | Ingerir IPE e rodar pipeline → eventos não aprovados pontuam famílias |
| C3 | **Parse vazio CVM aceito silenciosamente** (viola Regra 4) — layout novo da CVM retornaria 0 eventos indistinguível de "nada publicado" | `ingest_cvm.py:88-127,160-182` | `parse_ipe_rows(iter([header]))` → `[]`, sem exceção |

### ALTOS

| # | Bug | Local |
|---|-----|-------|
| A1 | Fail-open em parsing de eventos: `except ...: continue` descartava evento malformado; `trough_date` inválida retornava 0 ("não houve evento") em vez de indisponível | `rj_families.py:115-126,165-176`; `rj_families_next.py:61-64` |
| A2 | **Preço de fundo ≤ 0 virava `no_rally_observed` definitivo** — dado inválido contaminava o grupo controle | `rj_episodes.py:121,159-163` |
| A3 | **chs_nimta com MTA < 0 invertia o sinal** (empresa mais distressed classificada como menos) | `rj_families_next.py:135-136` |
| A4 | Re-execução de `ingest_ipe_year` duplicava eventos (sem idempotência) | `ingest_cvm.py:175` |
| A5 | `persist_run` com `INSERT OR IGNORE` congelava outcome obsoleto (censurado em T1 permanecia após rally em T2) — trilha do banco contradizia o relatório | `rj_pipeline.py:162-183` |
| A6 | Free float sem noção temporal: FRE de um ano aplicado a troughs de qualquer data (2015–2026) | `rj_pipeline.py:146-147` |
| A7 | Datas do IPE aceitas sem validação (`[:10]` cego); data corrompida era descartada silenciosamente nas famílias | `ingest_cvm.py:112-116` |

### MÉDIOS

| # | Bug | Local |
|---|-----|-------|
| M1 | P-valor de permutação sem correção (+1): `n_ge/n_perm` pode ser 0 (impossível) e anti-conservador sob BH | `rj_judge.py:50,132`; `rj_judge_robust.py:85` |
| M2 | Empates no mínimo geram candidatos espúrios (platô de R$0,01 → enxurrada de "fundos"; desempate arbitrário não pré-registrado) | `rj_episodes.py:79,48` |
| M3 | Divergência config↔código: `fato_relevante_ate_10p_antes_do_fundo` ("p" = pregões no config) implementado como 10 dias **corridos** | `config_rj.yaml:73` × `rj_families.py:160,177` |
| M4 | `rj_stage` usa `event_date` de colunas do universo sem disciplina `known_at` | `rj_pipeline.py:95,152` |
| M5 | Custo de turnover normalizado pelo denominador errado quando a carteira muda de tamanho (viés a favor da estratégia) | `backtest.py:105` |
| M6 | `momentum_12_1` não validava `closes[i_end] ≤ 0` → sinal −1.0 espúrio entrava no ranking | `factor.py:31-34` |
| M7 | `robustness_report` tratava `bh_sig=None` como `False` | `rj_judge_robust.py:100-102` |
| M8 | `walk_forward_evaluate` fail-open quanto à ordenação temporal dos units | `rj_outcomes.py:64-70` |
| M9 | Parser COTAHIST abortava o arquivo inteiro numa linha malformada | `cotahist.py:44-50` |
| M10 | `load_free_float`: múltiplos FREs por companhia → "último vence" sem ordenação | `ingest_cvm.py:209-216` |
| M11 | Parser numérico pt-BR corrompe formato US ("1.5" → 15.0) silenciosamente | `ingest_cvm.py:150` |
| M12 | RJ herda ajustes com `ex_date > asof` aplicados à série (violação formal do invariante anti-lookahead de nível absoluto de preço) | `rj_pipeline.py:44-53` via `adjust.adjusted_series` |
| M13 | Adjudicação humana futura (`resolved_at`) vaza para backtests passados — viés não declarado no DESIGN | `adjust.py:219-223` |

### BAIXOS (seleção)

- `classify_episode`: parâmetro `asof_today` morto, sem assert (rj_episodes.py:131)
- `rj_judge.py:207,216`: defaults fail-open (direção "ambiguous"; fallback que incluiria família descritiva no FDR)
- `simulate_power` com `reps=0` → divisão por zero (rj_power.py:66)
- `_open_zip_csv`: empate de múltiplos CSVs → escolha arbitrária (ingest_cvm.py:82)
- `scan_and_quarantine` contava inserções ignoradas (adjust.py:99-105)
- Ranking/dedup ON/PN com empates arbitrários e `GROUP BY` sem `ORDER BY` (portfolio.py:28; universe.py:70)
- `retail_migration`: empate silencioso em `max(ref_date)`; `rj_coda`: matriz irregular → IndexError cru
- Docstring `wayback_snapshots` inexistente (ingest_rj_universe.py:22); `select_secondary_episodes` retorna o primário (contrato-armadilha)

### Pontos auditados e ABSOLVIDOS
Janelas de rally sem off-by-one; BH correto sobre exatamente as 8 famílias com α=0,10 e descritiva fora do denominador; seeds reproduzíveis (42; `Random(seed+rep)` no power); bootstrap por cluster; análise primária filtra `censored==0`; censurados nunca viram controle; assert de disjunção next-gen × pré-registro correto e fail-fast; ingest B3 rejeita retrato vazio; proposição de universo não escreve na tabela final; direção dos fatores de ajuste de split correta; walk-forward histórico sem lookahead; determinismo bit a bit de power e pipeline confirmados por execução.

---

## 2. Correções aplicadas (teste reproduz o bug ANTES da correção)

13 commits na branch `audit/2026-08-24-fixes`; 29 testes novos em `tests/test_rj_audit_2026_08_24.py` (+ ajustes pontuais). Diff: 17 arquivos, +775/−63.

| Commit | Correção |
|--------|----------|
| `9e10cb2` | tooling: shim vendor via `STOCKS_ALLOW_VENDOR_SHIM` no conftest |
| `b27f25f` | **C1:** fallback `known_at or event_date` eliminado; evento sem `known_at` inelegível; trough inválida → `None` (missing) |
| `c499d99` | **C2:** `approved_by IS NOT NULL` em `rj_events` e `rj_universe`; ingest CVM grava pendente (`NULL`) |
| `a4fe871` | **C3/A7:** parse vazio, ZIP ambíguo e lote com data malformada → exceção (fail-loud) |
| `9aaa735` | **A2:** fundo ≤ 0 → outcome `invalid_data`, excluído (nunca controle); assert `dates[-1] <= asof_today` |
| `f821782` | **A3:** `chs_nimta` com MTA ≤ 0 → `None` |
| `4bf45d8`+`480f0bb` | **M1:** p de permutação `(n_ge+1)/(n_perm+1)` no judge e Romano-Wolf |
| `9263475` | **A5:** `persist_run` atualiza linha divergente em asof posterior; idempotente bit a bit |
| `40d347f` | **A4:** ingest IPE idempotente (SELECT-before-INSERT, migrações intactas) |
| `62b8586` | **M5/M6/M9 + baixos:** momentum valida `i_end`; turnover com denominadores corretos; COTAHIST por linha (malformada contada/logada, 100% ruim → exceção); quarentena via `rowcount`; `ORDER BY` determinístico |
| `6681f15` | **J:** power rejeita reps<1; `robustness_report` None→None; walk-forward valida monotonicidade; FRE toma maior `ref_date`; docstring altman_z; coda exige matriz retangular |
| `1b4d638` | tooling: assert anti-vendor sob guarda do shim (ruff F401) |

**Validação pós-correção:** suíte 211/4 (só shim), ruff limpo, `rj_power.py --fast` funcional e determinístico, pipeline sintético ponta a ponta reproduzível.

## 3. Riscos metodológicos remanescentes (NÃO corrigidos — exigem decisão)

1. **`censoring_horizon_trading_days = 756` [RJ-FROZEN] é parâmetro morto** — nenhuma linha de código o lê; a censura empresa-nível do §5 não está implementada (empresas sem candidato viram `excluded`, não `censored`/`control`). Enviesa o denominador do estudo. **Exige proposta de módulo separado / novo pré-registro.**
2. **Janela `info_trigger`: "10p" (pregões) no config vs. 10 dias corridos no código** — desvio de parâmetro congelado; precisa decisão explícita documentada (não silenciosa).
3. **`rj_stage` sem disciplina `known_at`** — datas de plano/homologação comparadas diretamente ao fundo.
4. **Free float ponto-no-tempo** — corrigido o determinismo (maior `ref_date`), mas a seleção do FRE anterior ao trough é mudança metodológica → backlog.
5. **IC bootstrap e LOCO ausentes para a família categórica** (`rj_stage` reporta V de Cramér sem intervalo nem análise de influência; §9 parcial).
6. **Outcome da janela secundária não persistido** no banco (só no JSON) — schema precisa de coluna/tabela.
7. **Viés de adjudicação retroativa** no domínio histórico (`resolved_at` não é point-in-time) — decisão de design a declarar.
8. **Empates em min()/max()** — regra de desempate não pré-registrada (platôs de preço em ações ilíquidas).

## 4. Melhorias de engenharia implementadas
Tooling de shim reproduzível (conftest + env var); ingestão CVM fail-loud e idempotente; persistência do pipeline consistente com re-runs; robustez numérica (p de permutação, denominadores); I/O defensivo no COTAHIST; 29 testes novos cobrindo os bugs; validação funcional ponta a ponta com SQLite sintético (5 empresas: rally/controle/censurada/excluídas) documentada.

## 5. Backlog priorizado
1. **[metodologia]** Implementar censura empresa-nível de 756 pregões (módulo separado + proposta de pré-registro) — risco #1.
2. **[decisão]** Resolver "10p" vs. 10 dias corridos em `info_trigger` e registrar no documento correspondente.
3. **[metodologia]** Free float point-in-time (FRE mais recente anterior ao trough; indisponível se ausente) + ponte ticker↔companhia com `source`/`approved_by`.
4. **[metodologia]** `rj_stage` derivado de `rj_events.known_at` (colunas `*_known_at` no universo).
5. **[estatística]** IC bootstrap por cluster e LOCO para família categórica; correção de empates no Romano-Wolf.
6. **[schema]** Persistir outcome/rally_pct da janela secundária; versionar episódios por `asof` (append-only).
7. **[dados]** Constraint UNIQUE em `rj_events`; validador de magnitude para parser numérico pt-BR/US.
8. **[docs]** Declarar viés de adjudicação retroativa no DESIGN; regra de desempate de fundos (platôs); remover promessa `wayback_snapshots` ou implementá-la.
9. **[higiene]** Contrato de `select_secondary_episodes` (renomear ou excluir primário); defaults fail-closed no judge (rj_judge.py:207,216).

## Entrega
- Branch `audit/2026-08-24-fixes` (13 commits limpos, prontos para PR).
- Patches: `/mnt/agents/output/patches/0001..0013` (`git am` sobre `main`).
