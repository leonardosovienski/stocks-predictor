# HANDOFF — predictor-stocks

**O HANDOFF nunca pode mentir sobre o estado da suíte.**
Atualizar ao fim de cada marco. Toda decisão registrada aqui é permanente.

---

## Estado atual: M1–M6 — núcleo implementado sobre dados sintéticos ✓ (veredito real da H1 aguarda COTAHIST real)

**Data:** 2026-06-25 (auditoria hostil de encerramento); 2026-06-29 (fix de teste estagnado)
**Suíte:** 96/96 verde (`python -m pytest tests/ -q`) — M0..M6 + plataforma + 3 testes de regressão novos

> **NOTA (jun/2026 — Red Team):** dois ajustes de comportamento nesta sessão:
> (1) **universo filtra mercado à vista** (`market_type='010'`) em `universe.py`/`backtest.py`
> — antes `prices_raw` puxava ~130k opções/termo junto; agora só ações+BDR+ETF (à vista
> completo, decisão do Leo). (2) `judge` distingue **"SEM DADOS (pipeline vazio)"** de
> "amostra curta" quando `walk_forward` não produz pares (DB sem histórico suficiente).
> Core consumido = `predictor_core 0.8.0-redteam`.
**Implementador:** Claude Code

---

### REGISTRO DE AUDITORIA — 2026-06-29 (teste estagnado: HANDOFF declarava verde, estava vermelho)

1. **Chegada VERMELHA de novo:** `test_m0_genesis.py::test_vendor_version_readable` falhava.
   O HANDOFF afirmava "95/95 verde" — factualmente falso nesta máquina.
2. **Causa raiz:** o teste exigia a substring fixa `"vendored"` em `predictor_core.__version__`,
   mas o `vendor/.../VERSION` foi recarimbado para `0.8.0-redteam-20260625` na sessão de Red
   Team (mudança DELIBERADA, registrada acima). O VERSION evoluiu; o teste do M0 ficou para trás.
3. **Correção (opção A):** a asserção passou a validar o FORMATO da procedência
   (`<semver>-<tag>-<YYYYMMDD>` via regex), não uma palavra fixa — robusto a futuros recarimbos.
   Nenhum parâmetro [H1-FROZEN] tocado; só ferramenta de teste. Suíte: **96/96 verde**.
4. **Registrado, não corrigido (ambiente):** sob **Python 3.14** (a máquina não tem o 3.12 dos
   docs; pytest só no 3.14) aparece 1 *warning* não-fatal — `UnicodeDecodeError` numa thread de
   leitura de `subprocess` (atrito de encoding cp1252×utf-8). Não derruba teste. Some no 3.12.

### REGISTRO DE AUDITORIA — 2026-06-25 (auditoria hostil + Ato de Honestidade)

1. **Auditoria hostil realizada:** 6 arquivos core + infra revisados sob framework de 7 pontos
   (`universe.py`, `adjust.py`, `execution.py`, `factor.py`, `portfolio.py`, `backtest.py`).
2. **Regressão encontrada na CHEGADA:** o repositório foi recebido **VERMELHO**, não verde.
   `config.yaml` + hardcodes em `main.py` e `universe.py` haviam sido sabotados para rodar
   dados sintéticos curtos — `min_history: 126` (vs 252), `factor: momentum_6_1` /
   `lookback_days: 126` (vs momentum_12_1 / 252), e quarentena point-in-time removida de
   `universe.py`. `test_config.py::test_load_real_config_h1_frozen_params` (assere 252 um a
   um) estava FALHANDO. Arquivos não rastreados (`diagnose_universe.py`, `poc_leak.py`,
   `audit_db.py`) testemunham a sessão de depuração que afrouxou os parâmetros.
3. **A mentira do HANDOFF:** este arquivo afirmava "92/92 verde" — factualmente falso e em
   violação da diretriz suprema do projeto. Corrigido aqui.
4. **Correção:** todos os parâmetros [H1-FROZEN] restaurados ao design §5–§9; telemetria
   `print()` removida; quarentena point-in-time restaurada SEM lookahead
   (`WHERE date < asof AND resolved_at IS NULL`); custo de transação corrigido para
   proporcional ao turnover real (era cobrado sobre o portfólio inteiro — superestimava
   ~3-5× para estratégias com persistência normal); fórmula de custo EXTRAÍDA para o helper
   testável `execution.calculate_turnover_cost`.
5. **Blindagem (3 testes de regressão novos):**
   - `test_universe.py::test_future_quarantine_does_not_exclude` (anti-lookahead);
   - `test_universe.py::test_resolved_quarantine_does_not_exclude`;
   - `test_factor_portfolio.py::test_turnover_cost_accuracy` (custo proporcional);
   - (+ assertion de `gap` de liquidez no anti-lookahead de execução existente).
6. **Estado atual:** 95/95 verde (vs "92/92" declarado, que era falso e vermelho de fato).

**Pendências fora do escopo de correção de código (exigem COTAHIST real ou são análise da
Fase -1):** validar 5+ splits reais (M2), golden sobre registros reais (M1), veredito da H1
(M6); robustez de execução a 3 preços + 2× custo, sensibilidade paramétrica ±10%,
decomposição por regime, remoção dos 5 melhores pregões (design §8/M5). Decisão humana
pendente: a exclusão de quarentena é por ticker inteiro (um salto exclui o papel para sempre
após aquela data) — bate com a "quarentena agressiva deliberada" do §11, mas merece registro.

---

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
