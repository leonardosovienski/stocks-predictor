# HANDOFF — predictor-stocks

**O HANDOFF nunca pode mentir sobre o estado da suíte.**
Atualizar ao fim de cada marco. Toda decisão registrada aqui é permanente.

---

## Estado atual: M1–M6 núcleo (dados sintéticos) + Onda 0 de governança ✓ (veredito real da H1 aguarda COTAHIST real)

**Data:** 2026-07-02
**Suíte:** 111/111 verde (`python -m pytest tests/ -q`; 2 são `slow` — cobertura Monte
Carlo do bootstrap, ~70s — deselecionáveis com `-m "not slow"`)
**Python:** o global da máquina hoje é **3.14.6** (o design diz 3.13; o HANDOFF antigo
dizia `py -3.12` — registrado para não mentir: a suíte roda no global, seja qual for)
**Implementador:** Claude Code

### Onda 0 — Governança e fundação (2026-07-02, pré-dado)

Auditoria da mesma data encontrou deriva entre design e código; correções por ondas.
Onda 0 (esta): governança. Onda 1: pipeline de julgamento. Onda 2: replay/obs.

1. **`scripts/sync_core.py` RECRIADO** (tinha sumido do repo — a verificação de
   integridade era ferramenta morta). Modos: `--check` (hashes vs manifesto),
   `--stamp` (re-carimbo após evolução por demanda; RECUSA sem bump de VERSION),
   `--sync SOURCE` (importa do upstream; recusa com diff local não commitado).
2. **Integridade do vendor virou TESTE** (`tests/test_core_manifest.py`): 1 byte
   alterado no vendor sem `--stamp` = suíte vermelha. Inclui simulação de corrupção.
3. **Aceite (a)–(e) do bootstrap (design §10/M5) implementado**
   (`tests/test_bootstrap_coverage.py`, marcado `slow`, seeds fixas). O aceite formal
   do M5 estava incompleto (só existia o teste fraco "block mais largo que iid").
4. **ACHADO ESTATÍSTICO (medido, 500–1000 séries AR(1) por ponto, n≈1755):** o IC
   percentile do block bootstrap cobre **~92%** quando o nominal é 95% — em qualquer
   combinação de método (moving/stationary), bloco (10–84), n_boot (200–1000) e
   construção (percentile/basic/simétrica). Anticonservador na direção que INFLA
   falso "COMPROVADA". Correção: **intervalo `studentized`** (bootstrap-t simétrico,
   se por batch means) no vendor — cobertura medida 93,5–93,8%, dentro do aceite.
   O percentile permanece como default retrocompatível e diagnóstico de geometria.

**Trilha do vendor (recompondo o buraco 0.3→0.7 e registrando hoje):**

| Versão | O quê |
|--------|-------|
| 0.3.x–0.7.0 | Sincronizadas do upstream em 2026-06-17 SEM changelog neste domínio (falha de governança, daqui em diante sync exige entrada aqui). Diferença observável vs 0.2.0: chegaram `replay.py` (anti-lookahead estrutural), `settings.py` (não usado por este domínio), `spearman`/`spearman_block_ci`, manifesto `CORE_MANIFEST.json`. |
| 0.7.1-vendored-20260702 | `_quantile` com interpolação linear no `block_bootstrap_ci`/`ci_mean` (indexação truncada enviesava os extremos do IC). Pendente upstream. |
| 0.7.2-vendored-20260702 | `interval="studentized"` no `block_bootstrap_ci` (ver achado acima) + `_batch_se`. Pendente upstream. |

### Onda 1 — Pipeline de julgamento (2026-07-02, TODAS as mudanças PRÉ-DADO)

Nenhuma rodada com COTAHIST real aconteceu; portanto estas emendas são legítimas sob a
disciplina de pré-registro — e depois da primeira rodada real nada disto pode mais mudar.

1. **PSR virou Lente 1 OBRIGATÓRIA** (`bootstrap.psr_min: 0.95` [H1-FROZEN]). Antes o
   `judge()` calculava o PSR e o ignorava no veredito — "pedágio de 2 lentes" com uma
   lente decorativa. Agora `COMPROVADA` exige `IC>0` E `PSR ≥ 0.95`.
2. **`bootstrap.method: stationary`** — a H1 pré-registra stationary (Politis & Romano);
   o `moving` era andaime do M0 e o `judge()` nem passava `method` (rodava moving por
   default contra o pré-registro). Aposentado pré-dado.
3. **`bootstrap.interval: studentized`** [H1-FROZEN] — consequência do achado da Onda 0
   (percentile cobre ~92% p/ nominal 95%). O IC da Lente 2 continua sendo "IC 95% do
   stationary bootstrap da diferença de Sharpe" como pré-registrado; muda a construção
   do intervalo para a calibrada.
4. **Execução na ABERTURA de D+1 no walk-forward** (era o defeito mais grave: o motor
   media fechamento-a-fechamento a partir do pregão do sinal = executar no próprio
   fechamento usado pelo sinal, preço inatingível, violando `execution.price: next_open`
   [H1-FROZEN]). Dia de transição compõe (1+gap overnight da carteira antiga) ×
   (1+intraday da nova). `adjust.adjusted_series_oc` fornece aberturas ajustadas.
5. **Custo = roundtrip × TURNOVER REAL** (`execution.turnover`), debitado
   incondicionalmente no primeiro dia utilizável do período (o bug do `j==0` que
   engolia o custo do mês se o 1º dia não tivesse dado foi eliminado junto).
6. **Benchmark FORMALIZADO:** o "buy-and-hold equiponderado do mesmo universo" da H1 é
   implementado como carteira equiponderada do universo point-in-time, re-selecionada
   a cada rebalance, com as MESMAS regras de execução (D+1 open) e MESMO modelo de
   custo × turnover — tratamento simétrico (antes era gross com rebalanceamento
   implícito de graça). Direção: benchmark ficou marginalmente mais fácil; simetria >
   conservadorismo assimétrico não documentado.
7. **Carteiras aleatórias (design §2b) implementadas:** mesmo nº de posições, turnover
   CASADO com o do modelo (mantém fração (1−turnover)·k da própria carteira anterior),
   mesmas regras de execução/custo. Percentil do modelo na distribuição delas sai no
   veredito como CONSULTIVO (`benchmark.n_random: 200`) — a H1 é julgada pelas 2 lentes.
8. **Embargo aplicado:** `purge_embargo_months: 1` [H1-FROZEN] agora é lido (o config
   congelava um parâmetro que nenhum código usava): pulam-se os primeiros N rebalances
   após `test_start`.

**Nota de calibração para o veredito:** mesmo com o studentized, a cobertura medida é
~93,5–94% para nominal 95% — o IC da Lente 2 é levemente anticonservador. Como a
direção favorece falso "COMPROVADA", um resultado que passar RASPANDO nas duas lentes
merece a desconfiança que o design já institui ("positivo marginal é suspeito").

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
| M1 — Ingestão crua | PARCIAL | 2026-06-16 | Parser posicional (layout B3 oficial VERIFICADO via doc) + gerador sintético determinístico (`cotahist.py`) + carga idempotente em prices_raw + caminho ZIP. Golden contra posições oficiais. **Falta:** carregar um ANO real da B3 e golden sobre registros reais (o sintético destrava M2-M6 hoje; troca-se a fonte quando o arquivo chegar). |
| M2 — Ajustes (PORTÃO CRÍTICO) | PARCIAL | 2026-06-16 | `adjust.py`: detector de saltos, inferência de split (proporção redonda), série ajustada por `adjustments`, quarentena de salto inexplicado. Rota de dividendos = (b) só-preço (decidida, abaixo). **Falta:** validar 5+ splits REAIS quando o COTAHIST real chegar. |
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
