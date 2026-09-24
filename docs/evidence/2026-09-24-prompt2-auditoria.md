# Prompt 2 — Auditoria técnica antes de alterações (stocks-predictor) — 2026-09-24

Base: `main` `36081a6` (mesma árvore do alvo qualificado `61fc017`). Modo somente leitura: nenhum código foi alterado
e nenhum backtest ou experimento foi rodado; a única execução foi a suíte de testes, isolada (seção 9).
Pré-condição: o relatório do Prompt 1 (`docs/evidence/2026-09-24-prompt1-segredos.md`) tem gate **CLEARED**.

Convenções: **PROVEN** = constatado nesta sessão (arquivo:linha, comando); **DECLARED** = afirmado em doc, não
comprovado aqui; **UNKNOWN**; **RISK** = risco sem evidência concreta de dano.

## Resumo executivo factual

- **Mercado e dados.** B3 à vista, barras diárias do COTAHIST, fundamentos da CVM (DFP/FRE) e proventos. Os bancos
  reais (12) ficam em `C:\STOCKS\data`, no PC 1 (DECLARED, `README.md`); aqui só há código e fixtures.
- **Modelos.** Não há treino: nenhuma biblioteca de ML (sem sklearn, numpy, pandas, scipy). Os "modelos" são rankings
  por regra (momentum, volatilidade, fundamentos) com carteira por quantil equiponderada ou 1/vol. Risco de split
  aleatório, normalização ou ajuste com dados futuros: não aplicável.
- **Três motores de backtest coexistem:**
  1. `backtest.legacy_walk_forward` (`backtest.py:52-182`) — julgou H1, H2, H4–H16. Entra **no fechamento do dia do
     sinal**, apesar de o `config.yaml` declarar `execution.price: next_open [H1-FROZEN]`;
  2. `simulation.walk_forward` (`simulation.py:309-405`), reparo de 2026-09-07 — `next_open` por padrão, desdobramentos
     PIT, proventos e caixa; nenhuma hipótese julgada o usa;
  3. circuito de pesquisa `research_worker` sobre `research_pit` (qualificação Etapa A) — decisão antes da abertura,
     entrada no fechamento da sessão, identidade por `security_id` e CNPJ.
- **Sharpe sem taxa livre de risco em todo lugar.** `predictor_core.measurement.stats.sharpe` "assume risk-free=0"
  (Core 3.2.1, `measurement/stats.py:76-77`), e `economics.screen` também (`economics.py:140`). Pelo critério do
  prompt, todo Sharpe reportado é inválido como Sharpe em excesso.
- **Multiplicidade.** O DSR usa N = registro legado (`trials.json`, 15 tentativas). H17–H22, BIG_WINNER, RJ e as
  sondas de qualificação ficam fora desse N.
- **Suíte isolada** (rede cortada, só `PATH`/`HOME`/`LANG`): 1049 passed + 71 subtests, 0 failed/erro/skipped,
  278,8 s, cobertura 78% (piso 77%).

## 1. Mapa do pipeline

| Etapa | Onde | O que faz | Status |
|---|---|---|---|
| Fontes | `ingest_cotahist.py` (usa `predictor_core.kernel.net.download_file`), `cotahist.py:40-70`, `ingest_cvm.py`, `cvm_pit.py`, `cash_events.py`, `stock_events.py`, `external_intelligence.py` | COTAHIST B3 (TPMERC 010, CODBDI 02), DFP/FRE/IPE da CVM, proventos, eventos acionários; staging externo só COLLECTION_ONLY | PROVEN (código); dados reais só no PC 1 (DECLARED) |
| Persistência | `db.py` (SQLite, migrações), `reports/` (gitignored, opt-in) | `prices_raw`, `adjustments`, `quarantine`, `fundamentals`, `universe_snapshots`, `decisions`, `cash_events` | PROVEN |
| Universo | `universe.py:24-104`; circuito: `research_pit.py` `Panel.universe` | top-N por mediana do volume financeiro em 126 pregões, dia sem negócio = 0, histórico mínimo 252, `date < asof`; dedup por prefixo de 4 letras (legado) ou por CNPJ (circuito) | PROVEN |
| Período | `config.yaml` `backtest.test_start 2018-01-01` (H1), `h11_backtest.test_end 2022-12-31` | fim mensal (`returns.month_end_dates`) | PROVEN |
| Features | `factor.py` — `momentum_12_1` (`:33-46`), `vol_signals`, `roe_signals`, `leverage_signals`, `net_margin_signals`, `revenue_growth_signals`, `near_52w_high`, volume surge | séries ≤ `asof` (`_idx_le`, `:22`) | PROVEN |
| Target/label | retorno do período entre rebalances (legado: diário composto; circuito: `label_close` início→fim, `research_worker.py:184`) | — | PROVEN |
| Modelo/sinal | ranking por regra, quantil 0,2 (`portfolio.select_portfolio`) | sem ajuste de parâmetros | PROVEN |
| Portfólio | `portfolio.py` (equiponderado, `inverse_vol_weights`), long-only | — | PROVEN |
| Execução | legado: close→close desde o fechamento do sinal (`backtest.py:152-169`); `simulation.py:102,191,223` next_open/next_close/worst; `execution.next_open_after` (`execution.py:8-15`) usado em `paper.py:92` | — | PROVEN |
| Custos | `execution.one_way_cost` = emolumentos 0,03% + spread/slippage 0,15% por lado; turnover real (`execution.equal_weight_turnover_cost`) | seção 4 | PROVEN |
| P&L | legado: retorno diário médio − custo no 1º dia do período (`backtest.py:153-179`); `simulation.simulate_portfolio` com quantidades, caixa e eventos | — | PROVEN |
| Avaliação | `backtest.judge`: PSR vs Sharpe do benchmark + IC por bootstrap pareado (`:185-216`); DSR `trials_gate.apply_dsr` (`:162-220`); `economics.screen` | Sharpe sem rf | PROVEN |
| Registro de hipóteses | `trials.json` (15), `trials_v2.json` (15, migrado), `trials.harness_attestation.json`, `RESEARCH_FREEZE.md`, lacres `[Hn-FROZEN]` em `config.py` | — | PROVEN |

Lacunas: nenhum `RunManifest` por execução no pipeline legado, só relatório e registro de trial (PROVEN, grep).
`reports/` fica fora do Git por padrão; H14–H16 sem relatório versionado (DECLARED, `RESEARCH_FREEZE.md`).

## 2. Riscos específicos de ações

| Risco | Tratado? | Evidência |
|---|---|---|
| Viés de sobrevivência | **Parcial.** O universo inclui deslistadas enquanto negociavam (vêm do COTAHIST histórico) e as exclui por inatividade; composição de índice não é usada (universo por liquidez, recalculado em cada data). Completude do banco real: DECLARED | `universe.py:47-70`; `tests/test_universe.py::test_excludes_delisted_ticker_stale_before_window`, `test_newly_listed_ticker_does_not_appear_before_its_ipo_date` |
| Identidade | **Fraca no legado:** ticker e prefixo de 4 letras; troca de ticker quebra a série, reuso de ticker funde empresas. Circuito novo: `security_id` e CNPJ com eventos datados | `universe.py:74-80`; `research_pit.py` |
| Eventos corporativos | **Legado:** desdobramentos e grupamentos detectados por salto, com fator aprovado por humano, aplicados **retroativamente** a toda a série (`adjust.py:89,152-170`); saltos sem aprovação → quarentena. O ajuste retroativo não altera razões de preço (o momentum não muda), mas não é PIT literal. **Motor novo:** só eventos com data ex ≤ asof (`simulation.py:53-66`). Proventos: rota (b) só-preço nas julgadas; rota (a) retorno total em `adjust.total_return_series` (H11) | PROVEN |
| Quarentena no legado | usa o estado **atual** de resolução, não o da data (`universe.py:40-43`; docstring "Frozen reconstruction… NOT a strict temporal claim") | PROVEN (RISK de resolução futura) |
| Fundamentos PIT | **Não nas julgadas.** H7, H9, H10, H12 e H13 usam `use_known_at=False`, embargo **estimado** `ref_date + 90 dias` (`factor.py:118-145`). A ingestão legada grava `DT_RECEB` mais antigo por (CNPJ, ref), sem separar versões (`ingest_cvm.py:364`), então reapresentações não têm tratamento PIT. `cvm_pit.py` guarda toda versão com o próprio `DT_RECEB` + 1 dia (`:3,101-110,163-223`), mas só as H17–H19 o usariam, e estão bloqueadas | PROVEN |
| Calendário | **Observado:** datas com barra em `prices_raw`; sem calendário oficial de feriados, meio-pregão ou leilão (dados diários); timestamps só de data; CVM com data de recebimento + 1 dia | `backtest.py:116-119`; `returns.py:4-9`; `cvm_pit.py:3` |
| Execução | **Legado (vereditos H1–H16): fechamento do próprio dia do sinal** (look-ahead pelo critério do prompt). Motor novo, paper e circuito: abertura de D+1, ou decisão antes da abertura e fechamento de D+1 | `backtest.py:134,152-169`; `factor.py:36`; `simulation.py:85`; `execution.py:1-15`; `research_pit.py:48,89` |
| Liquidez | filtro por mediana do volume (top 60) na decisão; **sem** ADV mínimo explícito e **sem** limite de participação no volume; custo fixo, sem impacto de mercado. O protótipo OSS de participação ordem/volume não foi integrado (DECLARED, `STOCKS_CURRENT_STATE.md`) | PROVEN |

## 3. Vazamento geral

| Severidade | Problema | Evidência | Impacto provável |
|---|---|---|---|
| **HIGH** | Execução no fechamento do dia do sinal no motor que julgou H1, H2, H4–H16 | `backtest.py:126-181` (sinal com `_idx_le(dates, asof)`, `factor.py:36`; 1º retorno `close[t+1]/close[t]`); `config.yaml` `execution.price: next_open` declarado e não consumido | resultados de H1–H16 não refletem execução factível; direção do viés depende do fator (reversão de curto prazo) |
| **MEDIUM** | Fundamentos com embargo estimado, sem data real de divulgação, e sem versões | `factor.py:118-145`; `ingest_cvm.py:364` | entregas com mais de 90 dias e reapresentações podem entrar antes de públicas (H7, H9, H10, H12, H13) |
| **MEDIUM** | Identidade por ticker | `universe.py:74-80` | histórico quebrado ou fundido em troca e reuso de código |
| RISK | Quarentena legada com resolução atual | `universe.py:40-43` | inclusão ou exclusão baseada em resolução posterior à data |
| RISK | Ajuste de desdobramento retroativo (legado) | `adjust.py:89` | invariante para razões; não é PIT literal |
| INFO | purge/embargo declarados e inertes | `RESEARCH_FREEZE.md` §4; `tests/test_purge_embargo_limitation.py`; `simulation.py:326-339` recusa embargo sem `train_end` | sem estimador ajustado e com labels mensais não sobrepostos, o impacto prático é baixo |
| N/A | split aleatório, overlap treino/teste, normalização e seleção de features com futuro | nenhum estimador | — |
| OK | Ranking cross-section com futuro | universo `date < asof`; sinal ≤ asof | PROVEN sem uso de futuro no ranking |

## 4. Custos

| Componente | Estado | Evidência |
|---|---|---|
| Corretagem | 0 (assumido) | `config.yaml` `brokerage_pct: 0.0000` |
| Emolumentos/liquidação | 0,03% por lado, constante | `config.yaml` `b3_fee_pct` |
| Spread/slippage | 0,15% por lado, constante, sem impacto por volume/ADV | `execution.py`; `simulation.py:84` (0,0018 por lado) |
| Impacto de mercado | não modelado | `RESEARCH_FREEZE.md` §7 |
| Aluguel (vendidos) | não se aplica (long-only) | `docs/DESIGN.md` §6 (DECLARED) |
| Impostos | só nas linhas H20–H22 (`continuous_cash.py`, `monthly_etf.py`); ausentes nos fatores | PROVEN |
| Aplicado antes da métrica | sim, retorno líquido de turnover real (legado `backtest.py:141,169`; motor novo `simulation.py:207,251`) | PROVEN; sem decomposição bruto × líquido nos relatórios antigos (DECLARED) |

## 5. Inventário de tentativas

| Fonte | Registros | Evidência |
|---|---|---|
| Ledger legado de fatores | 15 (H1, H2, H4–H16; H3 nunca executada) | `trials.json`, `trials_v2.json` |
| H17, H18, H19 | pré-registradas (fonte nova). **H17 observada** (discovery de 2026-09-07) → `PAUSED_INCONCLUSIVE_DATA_QUALITY`; H18/H19 `PAUSED`, não executadas: 1 registro avaliado | `RESEARCH_FREEZE.md:1,102-117`; `research_admission.py:139-141` |
| H20, H21 | 2 linhas históricas executadas (`CLOSED_HISTORICAL`, `CLOSED_HISTORICAL_CONDITIONAL`) | `research_admission.py:140-141` |
| H22 | 24 avaliações (22 calculadas, 2 inviáveis) | `docs/research/2026-09-10-r5/ledgers.json` (24 entradas) |
| BIG_WINNER detecção V1 | 16 detectores | `experiments/BIG_WINNER_DETECTION_V1/audit/detector_registry.md` |
| BIG_WINNER preço V1 | 7 detectores | `experiments/BIG_WINNER_PRICE_DETECTION_V1/audit/detector_registry.md` |
| BIG_WINNER V2 | 5 candidatos (1 selecionado, 2 rejeitados, 2 adiados) + 8 endpoints secundários | `experiments/BIG_WINNER_IMPROVEMENT_PROGRAM_V1/V2_SELECTION_FREEZE.yaml` |
| RJ | 8 famílias, só com dados sintéticos | `RESEARCH_FREEZE.md` §8–9 |
| Sonda de qualificação (Etapa A) | 1 configuração (`stocks:QUAL-PIT-MOM-001`) + 80 controles negativos, que não são variantes de busca | predictor-qualification `RAW_LOGS/d16` |

**N_trials_observed = 71** registros avaliados com evidência: 15 (ledger) + 24 (H22) + 16 + 7 + 5 (BIG_WINNER) +
3 (H17 observada, H20, H21) + 1 (sonda). Detectores do BIG_WINNER
reaproveitam H1 e H11, então há sobreposição; o RJ fica fora por ser só sintético.

**N_trials_total_known = LOWER_BOUND(71).** Variantes exploratórias não registradas (scripts `discovery_*.py`, sessões
de pesquisa) não estão contadas. **N_upper ≈ 150** (estimativa: cerca de 2× o observado, pelas sessões de descoberta
e pelos programas BIG_WINNER com escolhas de desenho anteriores ao congelamento). É um teto de sensibilidade, não uma
contagem.

O DSR histórico usou N ≤ 15 (`trials_gate.py:188-193`), ou seja, **N subestimado**.

## 6. Baselines

| Baseline | Estado | Evidência |
|---|---|---|
| Carteira equiponderada do universo, mesmo protocolo e custos | **avaliado** | legado `backtest.py:159,181` (sem custo de turnover no benchmark); motor novo `simulation.py:397-404` (mesmos custos e execução); circuito `research_worker.py` (EW_UNIVERSE) |
| Buy-and-hold do índice (Ibovespa/BOVA11) | **não** no protocolo dos fatores; BOVA11 aparece como a própria estratégia em H21/H22 | `etf_hold.py`, `monthly_etf.py` |
| Random walk/naive de forecast | N/A (não há modelo de forecast) | — |
| Momentum simples (12-1) | é a própria H1; baseline declarado do BIG_WINNER V2 (`BIG_WINNER_V2_MOMENTUM_12_1_BASELINE`) | `config.yaml`; decision artifact BIG_WINNER |

Assimetria: no legado, o benchmark EW **não** paga custo de turnover e a estratégia paga (`backtest.py:169` × `:181`).

## 7. Taxa livre de risco

Nenhuma no Sharpe:
- `predictor_core.measurement.stats.sharpe` assume rf = 0 (`stats.py:76-77`);
- `economics.screen` usa `mean/sd·√252` (`economics.py:140`);
- o PSR é contra o Sharpe do benchmark (`backtest.py:204`).

A Selic só aparece como "referência bruta de oportunidade" em `etf_hold.selic_reference` (`etf_hold.py:195-218`),
fora de qualquer Sharpe. Para a B3 o correto é CDI ou Selic. **Todo Sharpe reportado é inválido como Sharpe em
excesso**; comparações Sharpe × Sharpe contra o benchmark EW são menos afetadas, mas não isentas.

## 8. Integração com o predictor_core (3.2.1, wheel instalada)

| Contrato pedido | No Core 3.2.1? | Uso no stocks |
|---|---|---|
| RunManifest | **não** | — |
| TrialLedger | não com esse nome; `TrialRegistryV2` (`contracts/trial_v2.py:277`) e `TrialRegistry` legado (`measurement/trials.py:748`) | circuito novo usa `TrialRegistryV2`; legado usa `TrialRegistry` + `trials.json` |
| Evaluator | `PrequentialEvaluator` abstrato (`testing/prequential.py:23`), para previsão probabilística | não usado |
| DecisionPolicy + arquivo de política | **não** | limiares em `config.yaml` (`dsr_min` por hipótese) |
| DSR / PSR | sim (`measurement/trials.py:692`, `stats.py:154`) | sim |
| PBO/CSCV, IC/Rank IC | **não** | — |
| Replay anti-lookahead, `bootstrap_ci`, `dataset_fingerprint` | sim | circuito novo |

Custo e risco: o Core está congelado na Etapa A da qualificação. Criar RunManifest, política ou PBO no Core exige
decisão do dono e C14 nas missões. Implementar localmente no stocks é possível e fica registrado como dívida técnica.

## 9. Testes isolados de rede e segredos

- Como o CI roda: `uv sync --locked --all-extras`; `uv run --no-sync coverage run -m pytest -q --durations=15
  --junitxml=test-results.xml` (`.github/workflows/ci.yml`, job `quality`).
- Local: venv do lock em `~/predictors/runtime/stocks/venv-suite` (Python 3.13.15), commit `28f17d2`, árvore de
  `36081a6` + este diretório `docs/evidence`.
- Isolamento:
  `env -i PATH=<venv>/bin:/usr/bin:/bin HOME=$HOME LANG=C.UTF-8 unshare --net --map-current-user sh -c 'python -m coverage run -m pytest -q --durations=15 --junitxml=…'`.
  Conferido dentro do namespace: uid 1000 (não root), `socket.create_connection` falha com `[Errno 101] Network is
  unreachable`, variáveis de ambiente só `HOME`, `LANG`, `OLDPWD`, `PATH`, `PWD`. Nenhum `.env` no checkout.
- Resultado: **1120 casos (1049 testes + 71 subtests) coletados; 1049 passed, 71 subtests passed; 0 failed, 0 errors,
  0 skipped; 278,76 s; exit 0**. Cobertura 78% (`TOTAL 10292 stmts, 1895 miss`; piso 77%).
- Nenhum teste falhou por rede ou `.env`. Testes mais lentos: `test_h11_total_return::test_run_h11_does_not_mutate_shared_config`
  (34,1 s) e `conformance/test_failure_extra::test_db_lock_longer_than_busy_timeout…` (32,7 s).

## 10. Plano para 3a, 3b e 3c

**Restrições que valem para os três (evidência acima):**
- (R1) **AGENTS.md (R8):** mudança em código ou CI exige atualizar a evidência operacional R8 (recibos de carga real
  e capacidade, `tools/operational_validation.py` + `tools/materialize_current_operational_evidence.py`, conferidos
  por `tools/verify_operational_evidence.py` no CI). O `COTAHIST_A2026.ZIP` de referência existe no PC 2
  (`~/predictors/data/d16/stocks`, sha256 `34b77468…`, o mesmo do PC 1).
- (R2) **Qualificação:** o `final_commit` qualificado é `61fc017`. Mudar o pacote `stocks_predictor` depois dele não
  invalida a attestation desse commit, mas o runtime qualificado deixa de ser o `main` (C14 se o dono quiser o novo
  código qualificado).
- (R3) Os dados reais do repositório (12 bancos) estão só no PC 1; dado novo ou download → parar e perguntar.

**3a — dados PIT, execução, baselines, custos, walk-forward, manifesto.**

Obrigatórias:
- (i) Execução configurável com proibição de fechamento de D: tornar `simulation.walk_forward` (next_open) o caminho de
  avaliação e recusar modo de execução no fechamento do sinal. O legado fica congelado e rotulado.
- (ii) Identidade e universo PIT por ISIN/CNPJ. Reusar `research_pit.Panel` ou adaptar `universe.py`.
- (iii) Fundamentos por `DT_RECEB` com versões (`cvm_pit`), proibindo embargo estimado no caminho novo.
- (iv) Custos com impacto proporcional a volume/ADV e limite de participação; aluguel parametrizável (0 no long-only).
- (v) Baselines EW (com os **mesmos** custos) e BOVA11 buy-and-hold no mesmo protocolo; momentum 12-1.
- (vi) RunManifest mínimo compatível com `TrialRegistryV2` (dívida: não existe no Core), gravado em toda execução
  avaliativa, inclusive as que falham.
- (vii) Testes obrigatórios do prompt: PIT de fundamento, execução, sobrevivência, monotonicidade de custo e
  reprodutibilidade.

Arquivos: `simulation.py`, `universe.py`/`research_pit.py`, `cvm_pit.py`, `execution.py`, novo módulo de manifesto,
`tests/`, recibos R8.

Riscos: quebrar os vereditos congelados (proibido); mitigação: caminho novo e aditivo, o legado intocado.

**3b — CPCV, métricas de fator, PSR/DSR/PBO, política.**
- CPCV com purge/embargo derivados do horizonte (1 rebalance ≈ 21 pregões) e da autocorrelação.
- IC/Rank IC/ICIR, decaimento e quantis.
- Sharpe **em excesso de CDI/Selic** (dado local versionado necessário → pode exigir parar e perguntar).
- PBO via CSCV implementado localmente (pypbo é AGPL; mlfinlab é proprietário).
- DSR com N em {71, 142, 355, 150} (N, 2N, 5N, N_upper; o histórico usou 15) e decisão no pior caso.
- t > 3 (Harvey, Liu & Zhu).
- Política versionada em arquivo com hash (não existe no Core → local + dívida); sem baseline → NO_DECISION.

**3c — Chronos zero-shot e execução real.**
- Licença e checkpoint conferidos no model card no dia.
- Download → parar e perguntar.
- Corte pós-publicação do checkpoint e poder estatístico.
- CRPS/WQL.
- Avaliação real só com dado local versionado (R3).

## Próximo passo

- **O 3a pode assumir como PROVEN:**
  - não há estimador ajustado;
  - `simulation.walk_forward` já executa em `next_open` com desdobramentos PIT e caixa;
  - `cvm_pit` guarda versões com `DT_RECEB`;
  - `research_pit.Panel` tem identidade PIT por `security_id`/CNPJ e universo sem sobrevivência (usado na D-16);
  - o Core 3.2.1 tem `TrialRegistryV2`, DSR, PSR, `bootstrap_ci`, `replay` e `dataset_fingerprint`, e não tem
    RunManifest, DecisionPolicy nem PBO;
  - a suíte roda isolada e verde.
- **DECLARED:** completude dos bancos reais do PC 1; decomposição bruto × líquido dos relatórios antigos; relatórios
  H14–H16 fora do Git.
- **UNKNOWN:** N real de tentativas (LOWER_BOUND 71).
- **Premissas do 3a que o código contradiz:**
  - "execução no mínimo em D+1" — o legado executa em D;
  - "universo inclui deslistadas" — inclui, mas com identidade por ticker;
  - "fundamentos pela data de divulgação" — os julgados usam embargo estimado;
  - "baseline com mesmos custos" — o benchmark EW do legado não paga turnover.
