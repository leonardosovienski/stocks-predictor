# HANDOFF — predictor-stocks

**O HANDOFF nunca pode mentir sobre o estado da suíte.**
Atualizar ao fim de cada marco. Toda decisão registrada aqui é permanente.

---

## Estado atual: M1–M6 — núcleo implementado sobre dados sintéticos ✓ (veredito real da H1 aguarda COTAHIST real)

**Data:** 2026-07-04
**Suíte:** 106/106 verde (`py -3.13 -m pytest tests/ -q`) — M0..M6 + plataforma (pedágio/telemetria/net/lacre frozen/guard de segredos)
**Implementador:** Claude Code

### Revisão de código da sessão (2026-07-04) — 8 ângulos, fixes aplicados

Code review multi-ângulo sobre o diff completo da sessão. Correções aplicadas:

1. **`import_approved_adjustments` resolvia quarentena com INSERT ignorado** — se já
   existia ajuste com fator DIVERGENTE do CSV (write-once), a correção era descartada
   em silêncio mas a quarentena fechava mesmo assim → papel voltava ao universo com a
   série ainda descontínua. Agora: fator divergente = AVISO + linha ignorada +
   quarentena mantida; fator idêntico = re-import idempotente. Teste de regressão.
2. **`runs.config_hash` constante** — `cmd_backtest` registrava `{'backtest': True}`
   em vez do config real, quebrando "reproduzível por run_id+config_hash" (§11).
   Agora `new_run` recebe o cfg completo (backtest) / cfg embutido (paper).
3. **`PREDICTOR_DB_PATH` na altitude errada** — o override vivia só em `main._db_path`;
   `cmd_ingest`, `backtest.run()` default, `paper.main` e `analyst.main` iam direto ao
   banco de produção mesmo com a env setada. Movido para `db.get_connection` (mesmo
   padrão do `obs.EVENTS_ENV`); `main._db_path` mantido p/ honrar cfg.
4. **Suíte poluía `reports/` real** — o smoke test do backtest gravava um
   `h1_verdict_*.md` de verdade a cada rodada do pytest. Novo override
   `PREDICTOR_REPORTS_DIR` em `report.write_report` (padrão obs), setado no teste.
5. **NaN na telemetria** — `isinstance(nan, float)` passa e `json.dumps` emite `NaN`
   (JSON inválido); PSR degenerado corromperia o events.jsonl append-only. Filtro de
   metrics agora exige finito (`math.isfinite`). Teste de regressão.
6. **Mediana de liquidez com amostra única** — papel que negociou 1x na janela ganhava
   "mediana" daquele print (um bloco de R$80M ranquearia um papel intragável). Sessão
   do calendário sem negócio agora conta volume 0. Teste de regressão.
7. **Datas duplicadas por re-ingest** — UNIQUE inclui source_file; re-download com
   outro nome duplicaria (date,ticker) e quebraria `dates.index`/retornos. `GROUP BY
   date` em `adjusted_series`, `scan_and_quarantine` e `list_split_candidates`.
8. **Paths relativos ao cwd** — `splits-review`/`splits-import` agora ancoram no ROOT.
9. **Eficiência** — `rank_universe`: janela via SQL + agregados de uma passada (era
   N+1 de história completa por ticker por rebalance); `list_split_candidates`: uma
   query por ticker (era uma por linha de quarentena); `walk_forward`: carga preguiçosa
   só dos tickers que entram em universo. Backtest 11 anos: **4min23s → 1min03s**
   (medido). Veredito re-rodado pós-fixes: 2092 pregões, PSR 0,429, IC95% ΔSharpe
   (−0,391, 0,270) — segue "não comprovada"; o deslocamento pequeno vs a rodada
   anterior vem da mediana zero-fill (papéis esporádicos saem do universo). O run_id
   agora carrega o prefixo do config_hash REAL (-f92897), não mais o hash constante.
10. **Limpeza** — try/except redundante em report.py (get_code_version já tem fallback
    interno); `_num`/`import math` no topo do módulo; dupla negação no relatório;
    helper SQL f-string inline no analyst; monkeypatch no test_report; conexões dos
    comandos fechadas via `contextlib.closing` (não vazam em exceção).

**Marcado para upstream (predictor-core):** `testing/secrets.py` +
`testing/__init__.py` (novo subpacote, v0.8.0) — sync manual, `scripts/sync_core.py`
não existe mais neste repo; NÃO sincronizar por cima sem levar o subpacote junto.

### Sync ao core canônico v1.1.0 + stationary pré-registrado (2026-07-09)

O upstream `predictor_core/` (repo irmão) estava na **v1.1.0-ga-20260709** — o commit
quebrado `2c188e0` referia-se ao v1.0.1 dele (o humano sincronizou o teste do guard de
segredos mas não o vendor; a reconstrução manual desta sessão foi SUBSTITUÍDA pela
canônica no sync). Sincronizado via a lógica do `sync_core.py` canônico (que voltou a
existir — vive no upstream, não mais em `scripts/` deste repo): 33 arquivos, agregado
`026f1f7b761440d9`.

- **Reorganização**: `stats`/`replay`/`net`/`obs` da raiz agora são compat shims;
  consumidores migrados para `measurement.stats` / `measurement.bootstrap` (bye
  DeprecationWarning). Teste de versão migrado do carimbo 'vendored' para semver
  (integridade agora é o CORE_MANIFEST, como nos outros 2 domínios).
- **`bootstrap_ci(scheme=...)` suporta STATIONARY** (Politis-Romano) — que é o que a
  H1 PRÉ-REGISTRA ("stationary bootstrap, bloco 21"). `config.yaml bootstrap.method:
  moving→stationary` (linha NÃO é H1-FROZEN; o moving era placeholder declarado
  "stationary como refinamento M5" — isto é alinhar À pré-especificação, não
  repescagem). Veredito re-rodado sob o esquema pré-registrado: 2092 pregões, PSR
  0,429, IC95% ΔSharpe **(−0,400, 0,257)** → **não comprovada** (consistente com o
  moving; backtest agora em ~46s).
- **Disponível no core p/ a PRÓXIMA hipótese** (não ligado ainda — por demanda):
  `measurement.trials` (Experiment Registry + **Deflated Sharpe Ratio** — desconta
  E[max SR | N tentativas]; obrigatório se iterarmos H2, H3...) com **trava de poder**
  (criar trial exige atestado do `testing.harness` — controle positivo: o pipeline
  prova que detectaria edge plantado antes de qualquer NO-GO ser interpretável) e
  `testing.synth`/`coverage` (séries com verdade conhecida p/ validar a régua).
- **Aprendizado do previsao-cripto AVALIADO e n/a aqui**: o C2 deles (PSR inflado por
  janelas de trade SOBREPOSTAS) não se aplica — nossos retornos são diários
  não-sobrepostos; a autocorrelação residual é papel da Lente 2 (blocos), como o
  design já previa.

**Conhecidos, NÃO corrigidos (decisão de design pendente, não silenciosa):**
- `factor.momentum_12_1` não checa recência do último preço ≤ asof (guardado hoje pelo
  filtro de deslistagem do universo — defesa em camada única; guard próprio exigiria
  calendário no factor e mexe em semântica de sinal com H1 em andamento);
- filtro à-vista só no ingest: um banco carregado com `avista_only=False` fluiria
  derivativos p/ o universo sem re-checagem na leitura (aceito; escape hatch é
  explícito e o banco atual foi carregado filtrado).

### Correção + acabamento (2026-07-04)

Auditoria "roda tudo e mostra onde investir" encontrou a suíte VERMELHA no HEAD e a
fechou, além de completar dois stubs:

1. **BUG CRÍTICO — commit `2c188e0` quebrou a suíte:** adicionou `tests/test_secrets_telemetry.py`
   importando `predictor_core.testing.secrets`, módulo que **nunca foi criado** (pytest
   abortava na coleção → suíte inteira vermelha, contradizendo o "92/92" que o HANDOFF
   afirmava). Criado o subpacote `vendor/predictor_core/testing/` com `secrets.py`
   (`find_secrets` + `assert_no_secrets_in_events`, stdlib-regex, conservador). VERSION do
   core → `0.8.0-vendored-20260704`; `CORE_MANIFEST.json` recomputado. Guard verificado:
   passa telemetria limpa, pega chave AWS/OpenAI plantada.
2. **`src/report.py`** (era stub) — relatório do veredito da H1 em `reports/` (Sharpe/
   Sortino/MaxDD/retorno da estratégia vs. benchmark + o IC do pedágio) + evento
   estruturado na telemetria (`obs.emit_event`, metrics só-numérico). Ligado ao
   `main.py backtest` (grava relatório) via `backtest.run(write_report=True)`.
3. **`src/analyst.py`** (era stub) — analista SOMENTE-LEITURA do §9b: descreve estado
   (cobertura, universo, quarentena pendente, última carteira) em `reports/ai/`. NÃO
   escreve no banco, NÃO resolve quarentena, NÃO gera sinal. Comando `main.py analyst`.
   Determinístico e sem dependência — deletá-lo não quebra teste algum (invariante §9b).
4. **Robustez:** `backtest.run()` imprimia `Δ` (U+0394, fora do cp1252) — crashava em
   chamador sem stdout utf-8. Trocado por `diff-Sharpe`. `.gitignore` passou a cobrir
   `reports/*` e `events.jsonl` (artefatos gerados; versionar é opt-in via `git add -f`).

**Nota de ambiente:** o `py -3.12` do HANDOFF/README antigo não existe nesta máquina
(3.13 é o global, conforme CLAUDE.md §Ambiente); a suíte roda em `py -3.13`. Nenhum
parâmetro H1-FROZEN tocado; nada do pipeline de sinal alterado.

### Validação sobre COTAHIST REAL da B3 (2026-07-04)

Chegaram os arquivos reais `COTAHIST_A2024/2025/2026.ZIP` (Downloads). Fecha as
pendências de dado real de M1 e M2:

- **M1 — parser validado em dado real ✓** PETR4 (30,96/30,71), VALE3 (72,33), ITUB4,
  BBAS3, MGLU3 — preços 2026 corretos. `quote_factor` ∈ {1,100,1000,10000,1000000}
  (o caso ≠1 existe de fato). Encoding latin-1 OK.
- **Filtro à-vista no ingest (decisão do operador):** COTAHIST é ~98% opção/derivativo
  (mkt 070/080). `cotahist.load_prices` agora filtra `market_type=010 + bdi=02`
  (à-vista lote-padrão) por padrão — 1,95M registros/2026 → 41k; 407 papéis reais.
  `avista_only=False` é escape hatch explícito. Coberto por teste. prices_raw segue
  append-only (só carregamos subconjunto; derivativos podem ser acrescentados depois).
  3 anos carregados: 210.472 registros à-vista.
- **M2 — inferidor de split validado em split REAL ✓** dos 263 saltos |r|>30%
  quarentenados, 57 têm proporção redonda. Confirmados reais: **BBAS3 2024-04-16
  desdobramento 2:1** (56,46→27,91, fator 0,5), **FESA3+FESA4 2024-01-24** (ON+PN
  consistentes, 0,25), DIRR3 (3:1), EMAE3, ADMF3... Muito além dos "5+ splits reais"
  exigidos. `scan_and_quarantine` corretamente NÃO auto-resolve (design: sem fix
  silencioso; `adjustments` exige source+approved_by humano). Os 206 restantes são
  ruído de ilíquida/glitch (AZEV4 +1918%, AVLL3 +2309%) — retidos p/ revisão humana.
- **Dry-run de máquina em real (NÃO é o veredito H1):** universo 2026-06-01 =
  PETR4, VALE3, ITUB4, PRIO3, BBDC4, B3SA3, BPAC11, ITSA4, ABEV3, RENT3 (liquidez real
  correta). backtest: 353 pregões, PSR 0,14, IC ΔSharpe (−2,06, 0,16) cruza zero.

**PENDENTE para o veredito H1 pré-registrado (2 itens, ambos do operador humano):**
1. **Baixar COTAHIST 2016–2023** — só temos 2024-2026; a janela H1 exige aquecimento
   até 2017-12 e teste 2018-01→último ano completo. Sem isso o veredito não é o
   pré-registrado.
2. **Adjudicar os ~57 candidatos a split** — registrar em `adjustments` (com source)
   os splits reais (BBAS3 etc.) para que esses papéis sejam AJUSTADOS em vez de
   excluídos por quarentena (hoje BBAS3 sai do universo após 2024-04-16). Decisão
   humana, fora do alcance da IA (§9b/§11).

### 11 anos completos (2016-2026) + ferramenta de adjudicação + BUG CRÍTICO corrigido (2026-07-04)

O operador conseguiu **todos os anos** (`COTAHIST_A2016..2026.ZIP`). Ingestão completa:
**1.137.456 registros à-vista** em 4,6s de scan; walk-forward completo (2018→2026,
2.092 pregões) roda em **~4 minutos** sem numpy — dry-run ainda não é o veredito oficial
(ver pendência 2 abaixo). Quarentena sobe para 2.209 saltos em 11 anos; **440** têm
proporção redonda (candidatos a split real).

**Ferramenta de adjudicação humana (`adjust.py` + `main.py`):**
- `export_candidates_csv` / `main.py splits-review [csv]` — lista os candidatos a
  split/grupamento (proporção redonda) da quarentena aberta em CSV, colunas
  `source`/`approved_by` em branco para o operador preencher.
- `import_approved_adjustments` / `main.py splits-import <csv>` — grava em
  `adjustments` SÓ as linhas com `source` E `approved_by` preenchidos (write-once via
  UNIQUE); a IA nunca resolve quarentena sozinha (§9b/§11) — só o CSV aprovado
  explicitamente pelo humano fecha o ciclo.
- Fechei um gap: a quarentena resolvida agora é marcada (`resolved_at`) e
  `universe.rank_universe` passou a IGNORAR quarentena resolvida — antes, mesmo
  aprovando o split, o papel ficava excluído do universo PARA SEMPRE (a coluna
  `resolved_at` existia no schema desde o M0 mas nada a usava).
- CSV gerado: [`reports/splits_candidates.csv`](reports/splits_candidates.csv) (440
  linhas, gitignored — dado derivado, não versionado).

**BUG CRÍTICO encontrado e corrigido — papel deslistado tratado como ativo:**
Pedido do operador ("o que eu investiria hoje com base no projeto?") expôs o bug: o
ranking de momentum em `asof=2026-06-30` incluía `FIBR3` (Fibria, último pregão
2019-01-03, incorporada pela Suzano), `BVMF3` (virou B3SA3 em 2018-03-23) e `TIMP3`
(último pregão 2020-10-09) — todos com sinais de momentum calculados a partir de
preços de **anos atrás**, como se fossem cotações de hoje.

Causa raiz em `universe.rank_universe`: `vols[-lookback:]` pegava os últimos N
elementos da **própria lista de histórico do ticker**, não os últimos N pregões do
**calendário real** antes do asof. Para um papel deslistado, "os últimos N da própria
história" são de anos atrás — mas o código tratava como se fosse a janela de liquidez
recente, e `len(vols) >= min_history` só checava contagem total, nunca recência.
`factor.momentum_12_1` tem a mesma lacuna estrutural (`_idx_le` acha "o último pregão
≤ asof" sem checar se é recente) mas nunca é chamado fora dos tickers que o universo
já filtrou — corrigir na fronteira do universo bastou.

**Correção:** `rank_universe` agora calcula a janela de liquidez a partir do
calendário real de pregões (`all_dates[-lookback:]`, não por ticker) e exige que o
ÚLTIMO pregão do ticker antes do asof esteja DENTRO dessa janela — senão está
deslistado e é excluído. Teste de regressão:
`test_excludes_delisted_ticker_stale_before_window`. Suíte 103/103 verde.

**Impacto:** este bug afetava TODO o histórico do walk-forward (qualquer rebalance
mensal em qualquer asof), não só "hoje" — um papel deslistado permanecia elegível para
sempre depois de sair de negociação. O veredito H1 rodado antes desta correção
(dry-run) estava contaminado por isso; precisa ser re-rodado.

### 14 splits adjudicados via fonte pública verificada (2026-07-04, mesma sessão)

Operador autorizou a IA a fazer o trabalho de VERIFICAÇÃO (WebSearch contra fato
relevante/imprensa financeira) dos candidatos de maior liquidez do CSV — mas a decisão
de aprovar e o registro do aprovador (`approved_by=leonardo`) são do operador, nunca
da IA sozinha (§9b/§11: a IA nunca resolve quarentena por iniciativa própria; aqui ela
só reuniu evidência para uma aprovação humana explícita já concedida).

**14 ajustes gravados em `adjustments`** (source=`fato_relevante_confirmado_websearch`),
todos com data E proporção conferidas contra fonte citável:
BBAS3 (2024-04-16, 1:2), WEGE3 (2021-04-28, 1:2), RADL3 (2020-09-21, 1:5), HAPV3
(2020-11-25, 1:5), EQTL3 (2019-11-28, 1:5), ENEV3 (2021-03-12, 1:4), FESA3+FESA4
(2024-01-24, 1:4), DIRR3 (2025-08-11, 1:3), MGLU3 ×4 (2017-09-05 1:8, 2019-08-06 1:8,
2020-10-14 1:4, 2024-05-27 grupamento 10:1), RENT3 (2017-11-23, 1:3 — ratio/ano
confirmados, dia exato via COTAHIST). Verificado: série ajustada de BBAS3 fica contínua
(28,50→28,23→27,91, sem o salto falso de −50%). Quarentena aberta: 2209→2195 (14
resolvidas); esses papéis voltam a ser elegíveis no universo (fix do resolved_at desta
sessão). `EMAE3` (3 eventos) ficou de fora — papel de baixo free-float, sem fonte
rápida confiável; permanece em quarentena para revisão do operador. Restam ~426
candidatos plausíveis (proporção redonda) não adjudicados no CSV. Suíte 103/103 verde.

### O que foi feito no M0

- Estrutura de repositório criada conforme §3 do design doc
- `vendor/predictor_core/` vendorizado com carimbo `0.1.0-vendored-20260612`
  - Módulos presentes: `net`, `obs`, `infra`, `stats`
  - `stats.py` já inclui `block_bootstrap_ci` (moving + stationary), `sharpe`, `sortino`, `max_drawdown`
    — implementado por demanda: este domínio exige no M5; entra no vendor agora para evitar retrabalho
- `config.yaml` com todos os parâmetros H1-FROZEN registrados a priori
- `src/db.py` com schema completo (migração idempotente `0001_initial_schema`)
  - Tabelas: `prices_raw`, `adjustments`, `quarantine`, `universe_snapshots`, `decisions`, `runs`
  - Princípio write-once via COALESCE na parte RISK do ledger documentado nos testes
- Esqueletos `src/` para M1–M6 (todos com `NotImplementedError` explícito + marco)
- `tests/test_m0_genesis.py` — 16 testes cobrindo vendor, infra, schema, stats, config, HANDOFF

### Decisões de M0

| Decisão | Justificativa |
|---------|--------------|
| `block_bootstrap_ci` no vendor já no M0 | Evitar retrabalho no M5; a especificação Politis & Romano (1994) já está no design |
| `method='moving'` como default | Mais simples de implementar corretamente; stationary é refinamento aprovado no portão M5 |
| `quote_factor` em `prices_raw` | Obrigatório para divisão de preços (÷100 × fator) no parser COTAHIST |
| Esqueletos com `NotImplementedError` | Cada arquivo deixa claro o marco responsável; importar antes da hora quebra explicitamente |

### Revisão pós-M0 (2026-06-12, mesma sessão)

Auditoria do M0 contra o design doc encontrou e corrigiu 4 itens:

1. **`runs.params_frozen_until` ausente** (nomeada no design §4) — adicionada via migração
   `0002` (de quebra, validou o caminho de upgrade append-only com teste próprio);
2. **`net.download_file` declarava `timeout` sem usá-lo** (`urlretrieve` ignora) — trocado
   por `urlopen` com timeout real + User-Agent (B3 rejeita requests sem UA);
3. **Leituras de texto sem `encoding="utf-8"`** — no Windows o default é cp1252; explicitado
   em todos os `read_text`. Convenção daqui em diante: TODO I/O de texto declara encoding;
4. **`.gitignore` engolia `data/` e `reports/ai/`** — estrutura não sobreviveria a clone;
   corrigido com `.gitkeep` + negação.

**Pendência do parser YAML — FECHADA (rota a, mesma sessão):** `src/config.py` implementa
mini-parser stdlib do subconjunto plano (seções de 1 nível + chave: valor). Não é decisão
de portão porque NÃO adiciona dependência — é o caminho default da política stdlib-first.
O parser falha alto (ValueError) em qualquer construção fora do subconjunto (listas,
aninhamento profundo); se o config um dia precisar disso, a decisão de pyyaml volta ao portão.

### Complementos pós-revisão (2026-06-12, mesma sessão)

- **`docs/DESIGN.md`** — o documento de design agora vive NO repositório (o HANDOFF
  referencia §§ dele; antes só existia em Downloads — risco de perder a constituição);
- **`CLAUDE.md`** — guardrails e convenções para sessões futuras do implementador;
- **`README.md`** — visão geral + fronteira (§12);
- **`src/config.py`** — carregador do config + `config_hash` (ver pendência fechada acima);
- **`db.new_run()` / `db.get_code_version()`** — registro de execuções com run_id único
  ordenável (timestamp UTC + prefixo do config_hash), params_json canônico e code_version
  do git (exigência de reprodutibilidade do §11);
- **`scripts/sync_core.py`** — sync do vendor com carimbo de VERSION; aborta se o vendor
  tiver diff não commitado (proteção contra perder evolução por demanda não levada a upstream);
- **`tests/conftest.py`** — paths centralizados; **`tests/test_config.py`** — testes de
  config, runs e smoke do main.py;
- **`.gitattributes`** — normalização de EOL (LF nos fontes);
- **`main.py`** — ponto de entrada: `python main.py` mostra status read-only (versões,
  config_hash, contagem das tabelas, marcos). Comandos de pipeline (`ingest`, `adjust`,
  `backtest`, `paper`) estão reservados e respondem qual marco os libera — viram
  implementação real conforme cada marco fechar.

### Evolução por demanda do vendor (2026-06-16)

`predictor_core/stats.py` ganhou a **Lente 1 do pedágio**: `probabilistic_sharpe_ratio`
(PSR, Bailey & López de Prado 2012) — fórmula fechada que pune não-normalidade
(skew/curtose); barreira barata ANTES do block bootstrap pesado. E a **Lente 2** foi
generalizada: `block_bootstrap_ci` agora aceita unidades PAREADAS (tuplas) para
reamostragem conjunta — preserva a cross-correlação exigida pela diferença de Sharpe
da H1 (M5). Invariante "reamostre linhas, não colunas" coberta por teste novo
(`test_paired_resampling_preserves_cross_correlation`). PSR verificado contra a
implementação do QuantConnect/LEAN. VERSION → `0.2.0-vendored-20260616`; marcar para
upstream no próximo `sync_core`. **Suíte 39/39 verde. Nenhum parâmetro H1-FROZEN
tocado; nada do pipeline de sinal alterado** — é só ferramenta de medição (M5) entrando
cedo no vendor, como o block bootstrap já entrou no M0.

---

## HIPÓTESE #1 (pré-registrada — cópia do design §9)

> **H1:** Carteira long-only do quintil superior de momentum 12-1, universo B3
> point-in-time (top 60 por liquidez, janela 126 pregões), equiponderada,
> rebalanceamento mensal com execução na abertura de D+1 e custo total de 0,36%
> ida-e-volta, obtém **Sharpe líquido superior ao buy-and-hold equiponderado do mesmo
> universo**, com IC 95% (stationary bootstrap, bloco 21) da diferença de Sharpe
> excluindo zero, na janela de teste walk-forward.
>
> **Janela:** calibração/aquecimento até 2017-12; teste 2018-01 → último COTAHIST
> anual completo.
>
> **Critérios fixados antes de qualquer rodada.** Resultado inconclusivo (IC contém
> zero) é válido e encerra a hipótese como "não comprovada nesta janela" —
> sem repescagem de parâmetros.

**Veredito H1:** PENDENTE — aguardando M6

Ajustes de parâmetros após ver resultados = nova hipótese, novo pré-registro, nova janela. Sem exceções.

---

## Marcos

| Marco | Status | Data | Notas |
|-------|--------|------|-------|
| M0 — Gênese | ✓ COMPLETO | 2026-06-12 | Estrutura, vendor, schema, suíte verde |
| M1 — Ingestão crua | ✓ VALIDADO (real) | 2026-07-04 | Parser posicional (layout B3 VERIFICADO) + gerador sintético + carga idempotente + ZIP. **Validado em COTAHIST REAL 2024-2026** (PETR4/VALE3/ITUB4 corretos; quote_factor≠1 presente). Filtro à-vista lote-padrão (mkt010+bdi02) no ingest — 98% do arquivo é derivativo. **Falta p/ H1:** anos 2016-2023 (janela pré-registrada). |
| M2 — Ajustes (PORTÃO CRÍTICO) | ✓ VALIDADO (real) | 2026-07-04 | `adjust.py`: detector + inferência de split + série ajustada + quarentena. **Inferidor validado em split REAL:** BBAS3 2:1 (2024-04-16), FESA3/4, DIRR3... (57 de 263 saltos = proporção redonda). NÃO auto-resolve (design). Dividendos = rota (b). **Falta p/ H1:** operador adjudicar os ~57 splits em `adjustments` (com source) p/ ajustar em vez de excluir. |
| M3 — Universo + retornos | PARCIAL | 2026-06-16 | `universe.py` (top-N por mediana de volume, POINT-IN-TIME só dados < asof, dedup ON/PN, exclui quarentena/histórico curto; snapshot materializado) + `returns.py` (retornos mensais). Teste-âncora prova anti-lookahead. **Falta:** benchmark equiponderado + gerador de carteiras aleatórias (construo no M5, onde são consumidos como nulo). |
| M4 — Fator + carteira + execução | FEITO (componentes) | 2026-06-16 | `factor.py` momentum 12-1 (point-in-time) + `portfolio.py` quintil superior equiponderado long-only + `execution.py` D+1/custos. Teste anti-lookahead `exec_ts > signal_ts`. O walk-forward que os ENCADEIA é o M5. |
| M5 — Medição | FEITO (núcleo) | 2026-06-16 | `backtest.py`: walk-forward mensal (universo→momentum→quintil→hold), curva DIÁRIA estratégia vs benchmark pareada, e o PEDÁGIO de 2 lentes (PSR + block bootstrap PAREADO da diferença de Sharpe). End-to-end testado em dados sintéticos. **Falta (evolução):** robustez de execução a 3 preços (abertura/fechamento D+1/pior) + 2× custo; purge/embargo formal. |
| M6 — Julgamento H1 + paper forward | FEITO (núcleo) | 2026-06-16 | `paper.py`: `record_forward` (EVAL antes do futuro, anti-tautologia) + `settle_executions` (RISK write-once via COALESCE); `backtest.run()` é o mecanismo do veredito. **Falta:** rodar o veredito da H1 UMA vez sobre o COTAHIST REAL (dado físico da B3) e ligar o cron diário do paper. |

---

## Próximos passos (M1)

1. Obter layout oficial COTAHIST da B3 (documento PDF da B3, não de memória)
2. Implementar `ingest_cotahist.py`: `download_cotahist` (separado, rede limpa) e `parse_cotahist` (offline)
3. Testes golden com registros reais (incluindo: fator cotação ≠1, papéis fracionários, encoding CP1252)
4. Carregar um ano completo; verificar contagens batem com o arquivo; reprocessar é idempotente

### Pendência de design a decidir antes do M4 (portão M2)

Rota de dividendos/JCP (§4, armadilha 2):
- **(a) [recomendada]** ingerir proventos de fonte nomeada (fundamentus/statusinvest; yfinance como cross-check)
- **(b)** rodar H1 em retorno só-preço com limitação e direção do viés escritas no pré-registro

**DECISÃO (2026-06-16): rota (b) — retorno SÓ-PREÇO.** Não há fonte de proventos
disponível nesta passada. Viés DECLARADO e direcional: omitir dividendos/JCP subestima o
retorno total; como papéis de momentum tendem a yield menor, a omissão FAVORECE a
estratégia contra o benchmark (viés a nosso favor — "positivo marginal é suspeito por
construção"). Quando uma fonte nomeada de proventos existir, migrar para rota (a) =
nova hipótese / novo pré-registro. Aplica-se igualmente à estratégia E ao benchmark.

---

## Dependências de runtime aprovadas

| Pacote | Status | Justificativa |
|--------|--------|---------------|
| `numpy` | PRÉ-APROVADO (M0) | Matriz de retornos cruzada + stationary bootstrap |
| `pandas` | NÃO aprovado | Parse COTAHIST é trivial em stdlib; revisar na dor do M1 |
| `pytest` | dev — precedente domínio 1 | |

---

## Restrições invioláveis (resumo operacional)

- Python 3.13 global. Sem venv.
- Separar download (rede limpa, cron) de processamento (offline).
- `prices_raw` é append-only e imutável.
- Ledger `decisions`: parte EVAL imutável; parte RISK write-once via COALESCE.
- IA (analista) NUNCA escreve no banco, NUNCA resolve quarentena.
- Nenhum lookahead: exec_ts > signal_ts em toda linha do ledger (teste automatizado obrigatório no M4).
- Parâmetros H1-FROZEN não se tocam após qualquer rodada de resultado.
