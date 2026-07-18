# HANDOFF — predictor-stocks

> ## STATUS: REABERTO PARA H4 (2026-07-18) — vendor segue congelado
>
> O bloco PARKED de 2026-07-18 fixava a condição formal de reabertura:
> "decisão humana explícita + hipótese formalizada antes de qualquer
> código". **Ambas satisfeitas em 2026-07-18**: ordem explícita do operador
> ("abre a H4 com volatility targeting") + pré-registro formal da H4 abaixo,
> escrito ANTES de qualquer código/rodada. Nota: o texto do bloco dizia "H2
> sem hipótese formalizada" — estava desatualizado em relação a ESTE arquivo
> (a H2 foi pré-registrada, rodada e encerrada em 2026-07-16, ver seções
> abaixo); a inconsistência veio de um carimbo de ecossistema, não de
> decisão nova.
>
> **Permanece PROIBIDO** (inalterado): sync/atualização do vendor
> `predictor_core` (fica em 1.3.0-ga-20260711, agregado `3445e37f43c458cc`,
> drift esperado e correto — o sync indevido de 2026-07-17 foi revertido em
> `e8adae1`). A H4 usa somente APIs já vendorizadas. Ver `ECOSYSTEM_HANDOFF.md`.

---

## H5 ABERTA — PRÉ-REGISTRO (2026-07-18, ANTES de qualquer rodada)

**Decisão do operador (2026-07-18):** "abre a próxima com reversão de curto
prazo" — o fator que o mapa M7+ do design §10 sempre nomeou como o segundo da
fila. Nota de numeração: o slot "H2" do mapa foi ocupado pela baixa-vol
(decisão de 2026-07-16) e "H3" segue reservada para combinação (condicionada a
sobreviventes individuais, que não existem); esta hipótese entra como **H5**.
O "H5-short" do mapa permanece hipótese futura própria (gated na perna comprada
validada). A identidade real de cada tentativa é o `trials.json`, não o número.
Entra como **tentativa N=4** no Experiment Registry.

### HIPÓTESE #5 (pré-registrada — critérios fixados ANTES de ver o dado)

> **H5:** Carteira long-only do **quintil INFERIOR de retorno recente**
> (retorno acumulado dos últimos 21 pregões ≤ asof — os "perdedores" do mês,
> aposta clássica de reversão de curto prazo, Jegadeesh 1990), universo B3
> point-in-time (top 60 por liquidez, janela 126 pregões — idêntico a
> H1/H2/H4), equiponderada, rebalanceamento mensal com execução na abertura de
> D+1 e custo proporcional ao turnover real (0,18% por lado), obtém **Sharpe
> líquido superior ao buy-and-hold equiponderado do mesmo universo**, com:
> (i) IC 95% (stationary bootstrap, bloco 21) da diferença de Sharpe excluindo
> zero, E (ii) **DSR ≥ 0,95** (descontado por TODAS as tentativas do
> `trials.json`, N=4).
>
> **Sinal:** `momentum_12_1(lookback=21, skip=0)` — retorno de [asof−21, asof]
> na série ajustada; point-in-time como sempre. Sem skip de microestrutura
> (variante clássica, fixada a priori).
>
> **Janela:** a MESMA de H1/H2/H4 (teste 2018-01 → último dado COTAHIST) —
> DSR com N=4 é o pedágio dessa reutilização.
>
> **Critérios fixados antes de qualquer rodada.** IC contendo zero OU
> DSR < 0,95 = "não comprovada nesta janela" — encerra a H5 sem repescagem.
> Lookback (21), quintil, pesos e custos são [H5-FROZEN]; lacre por máquina em
> `config.h5_frozen_config_hash`.

**Adversário natural declarado:** reversão de curto prazo gira a carteira
quase inteira todo mês — o turnover alto é intrínseco à hipótese e o custo por
turnover real vai cobrá-lo integralmente. Se a H5 morrer no custo, isso é
REFUTAÇÃO honesta da versão implementável, não defeito da régua.

**Viés declarado (rota (b), só-preço):** queda ex-dividendo entra como retorno
negativo sem perda econômica → papéis de maior yield caem no quintil
"perdedor" com mais frequência, e o provento omitido então SUBESTIMA o retorno
realizado da carteira → o viés tende a PENALIZAR a H5 (conservador; direção
declarada).

**Veredito H5:** _pendente — nenhuma rodada executada até este pré-registro._

---

## H4 ABERTA — PRÉ-REGISTRO (2026-07-18, ANTES de qualquer código/rodada)

**Decisão do operador (2026-07-18):** "abre a H4 com volatility targeting" —
a H4 do mapa M7+ do design §10 ("sizing: volatility targeting (peso inverso à
vol realizada) vs. equiponderado; julgado por Sharpe líquido E drawdown").
É SIZING, não seleção: a carteira segura o universo INTEIRO e muda só os
pesos — estruturalmente distinta da H2 (que selecionava o quintil de menor
vol com pesos iguais). O design condiciona só a H3 (combinação) à
sobrevivência de H1/H2; a H4 não tem essa trava. Entra como tentativa N=3 no
Experiment Registry e paga o DSR correspondente.

### HIPÓTESE #4 (pré-registrada — critérios fixados ANTES de ver o dado)

> **H4:** Carteira long-only de **TODO o universo point-in-time** (top 60 por
> liquidez, janela 126 pregões — idêntico a H1/H2), **ponderada inversamente à
> volatilidade realizada** (w_i ∝ 1/vol_i, vol = desvio-padrão dos retornos
> diários dos últimos 252 pregões ≤ asof, normalizado para Σw=1),
> rebalanceamento mensal com execução na abertura de D+1 e custo proporcional
> ao turnover real de PESOS (0,18% por lado × Σ|Δw_i|), obtém **Sharpe líquido
> superior ao buy-and-hold equiponderado do mesmo universo**, com TODOS os
> critérios: (i) IC 95% (stationary bootstrap, bloco 21) da diferença de
> Sharpe excluindo zero; (ii) **DSR ≥ 0,95** (descontado por TODAS as
> tentativas do `trials.json`, N=3); (iii) **max drawdown da estratégia ≤ max
> drawdown do benchmark** (o "E drawdown" do design §10, fixado a priori).
>
> Papel do universo sem vol definida no asof (janela de 252 retornos
> incompleta) fica com peso 0 NAQUELE mês — declarado; o benchmark
> equiponderado o mantém (assimetria pequena e conservadora).
>
> **Janela:** a MESMA de H1/H2 (teste 2018-01 → último dado COTAHIST); é por
> isso que o DSR com N=3 é critério, não enfeite.
>
> **Critérios fixados antes de qualquer rodada.** Falha em QUALQUER um dos
> três = "não comprovada nesta janela" — resultado válido, encerra a H4 sem
> repescagem. Lookback de vol (252 — mesma régua da H2, reuso declarado, não
> ajuste), custos e janela são [H4-FROZEN]; lacre por máquina em
> `config.h4_frozen_config_hash`.

**Viés declarado (rota (b), só-preço):** a ponderação 1/vol sobrepesa papéis
de baixa volatilidade, que tendem a MAIOR dividend yield → omitir proventos
**PENALIZA a H4 contra o benchmark** (conservador, mesma direção da H2).

**Simplificação declarada (herdada da maquinaria M5):** pesos re-normalizados
diariamente dentro do mês (sem drift intramês), igual ao tratamento do
benchmark equiponderado — simétrico, não favorece a estratégia.

### VEREDITO H4 — ENCERRADA: NÃO COMPROVADA (2026-07-18, rodada única)

Trilha na ordem pré-registrada: pré-registro commitado (`85aeee9`) → controle
positivo RE-ATESTADO sobre o código atual (2026-07-18T20:12:07Z) → trial
`h4-invvol-sizing-252` registrada (N=3) → UMA rodada.

- **run_id:** `20260718T201214322046-5e3833` — 2.092 pregões pareados (mesma
  janela de H1/H2)
- **(i) IC 95% diff-Sharpe (stationary, bloco 21):** **(−0,0297, +0,0742) —
  cruza zero** → reprovado. IC muito mais ESTREITO que o da H2: sizing sobre o
  universo inteiro é altamente correlacionado com o benchmark, então a régua
  mede a diferença com precisão — e a diferença é pequena.
- **(ii) DSR:** **0,6843 < 0,95** (N=3; E[max SR|N=3] = 0,0008 por-período)
  → reprovado.
- **(iii) drawdown:** maxDD 46,02% vs 48,03% → **OK (não pior)** — único
  critério aprovado.
- PSR 0,5209. Descritivo: Sharpe anual. 0,1805 vs 0,1621; retorno total 13,00%
  vs 8,03%. De novo melhor que o benchmark no descritivo, de novo
  indistinguível de sorte. **Não comprovada. Sem repescagem.**
- Relatório: [`reports/h4_verdict_20260718T201214322046-5e3833.md`](reports/h4_verdict_20260718T201214322046-5e3833.md)
  (versionado via `git add -f`); `trials.json` com sharpe realizado 0,011478
  por-período.

**Suíte pós-marco: 135/135 verde** (126 + 9 da H4: pesos 1/vol, custo por
turnover de pesos, walk-forward ponderado, smoke 3 critérios, lacre golden).

**Leitura acumulada do domínio (3 tentativas, 0 comprovadas):** H1 (momentum,
seleção), H2 (baixa-vol, seleção) e H4 (baixa-vol, sizing) — todas venceram ou
empataram no descritivo e NENHUMA sobreviveu à régua. O padrão consistente:
tilts de baixa volatilidade melhoram drawdown e Sharpe descritivo no top-60 da
B3, mas 8,5 anos de dado diário não dão poder para promovê-los a edge. Próximas
candidatas (cada uma = novo pré-registro, N+1 no DSR): reversão de curto prazo
(mapa §10), fundamentos (exige fonte nova — decisão do operador). O vendor
segue congelado (1.3.0); condição do bloco de status permanece válida para
qualquer H futura.

**O HANDOFF nunca pode mentir sobre o estado da suíte.**
Atualizar ao fim de cada marco. Toda decisão registrada aqui é permanente.

---

## H2 ABERTA — PRÉ-REGISTRO (2026-07-16, ANTES de qualquer rodada)

**Decisão do operador (2026-07-16):** a pausa estratégica de 2026-07-12 está
levantada por ordem explícita ("abre a H2 com baixa volatilidade"). A escolha da
baixa volatilidade segue a diretriz pós-H1 deste HANDOFF ("Mudança Estrutural de
Sinal — ex: fundamentos, anomalias de momentum, **volatilidade**"). Nota de
divergência registrada: o mapa M7+ do design §10 nomeava "H2" como reversão de
curto prazo; a diretriz mais recente (encerramento da H1, aprovada pelo operador)
substitui aquele ordenamento — reversão de curto prazo permanece no mapa como
hipótese futura própria.

### HIPÓTESE #2 (pré-registrada — critérios fixados ANTES de ver o dado)

> **H2:** Carteira long-only do **quintil INFERIOR de volatilidade realizada**
> (desvio-padrão dos retornos diários da série ajustada nos últimos 252 pregões
> ≤ asof), universo B3 point-in-time (top 60 por liquidez, janela 126 pregões —
> idêntico à H1), equiponderada, rebalanceamento mensal com execução na abertura
> de D+1 e custo proporcional ao turnover real (0,18% por lado), obtém **Sharpe
> líquido superior ao buy-and-hold equiponderado do mesmo universo**, com:
> (i) IC 95% (stationary bootstrap, bloco 21) da diferença de Sharpe excluindo
> zero, E (ii) **DSR ≥ 0,95** (Deflated Sharpe Ratio descontado por TODAS as
> tentativas do `trials.json` — obrigatório a partir da 2ª hipótese).
>
> **Janela:** a MESMA da H1 (teste 2018-01 → último dado COTAHIST). A
> reutilização deliberada da janela é exatamente o motivo de o DSR ser critério:
> a 2ª hipótese sobre o mesmo dado paga o pedágio de múltiplas tentativas.
>
> **Critérios fixados antes de qualquer rodada.** IC contendo zero OU DSR < 0,95
> = "não comprovada nesta janela" — resultado válido, encerra a H2 sem
> repescagem de parâmetros. Lookback de vol (252), quintil, pesos e custos são
> [H2-FROZEN] no config; lacre por máquina em `config.h2_frozen_config_hash`.

**Viés declarado (rota (b), só-preço):** papéis de baixa volatilidade tendem a
MAIOR dividend yield que a média do universo; omitir proventos portanto
**PENALIZA a H2 contra o benchmark** (viés conservador — o oposto da H1, onde o
viés favorecia). Um veredito positivo é robusto a esse viés; um negativo carrega
a ressalva.

**Trava de poder (obrigatória antes de registrar trials):**
`testing.harness.attest_pipeline_power` sobre o `backtest.judge` real — detectar
edge plantado (sensibilidade) E rejeitar ruído (especificidade) em séries
sintéticas pareadas; atestado gravado como irmão do `trials.json`
(`main.py attest-power`). Registro de tentativas: `h1-momentum-12-1`
(retroativa, Sharpe por-período do veredito final) + `h2-lowvol-252`.
`trials.json` é VERSIONADO (o denominador do DSR não pode sofrer esquecimento
seletivo).

### VEREDITO H2 — ENCERRADA: NÃO COMPROVADA (2026-07-16, rodada única)

Trilha na ordem pré-registrada: pré-registro commitado (`3b5e8b1`) → controle
positivo PASSOU (atestado 2026-07-16T22:15:30Z, metric `sharpe_diff_ci95`) →
trials registradas → UMA rodada.

- **run_id:** `20260716T221541856778-ac106e` — 2.092 pregões pareados (mesma
  janela da H1)
- **Lente 2 — IC 95% diff-Sharpe (stationary, bloco 21):** **(−0,2850, +0,3958)
  — cruza zero** → critério (i) reprovado
- **Critério (ii) — DSR:** **0,7092 < 0,95** (N=2 tentativas; E[max SR|N=2] =
  0,0012 por-período) → reprovado também
- PSR 0,5568. Descritivamente a estratégia venceu o benchmark (Sharpe anual.
  0,2121 vs 0,1621; retorno total 20,04% vs 8,03%; max DD 35,64% vs 48,03%) —
  e o viés só-preço ainda a penaliza —, mas a diferença NÃO é estatisticamente
  distinguível de sorte nesta janela. O melhor resultado descritivo do domínio
  até aqui, e mesmo assim: **não comprovada. Sem repescagem de parâmetros.**
- Relatório: [`reports/h2_verdict_20260716T221541856778-ac106e.md`](reports/h2_verdict_20260716T221541856778-ac106e.md)
  (versionado via `git add -f`); `trials.json` atualizado com o sharpe realizado
  (0,013363 por-período).

**Suíte pós-marco: 126/126 verde** (113 + 13 da H2: fator point-in-time,
bottom-quintile, trava de poder, registry N+1, smoke end-to-end, lacre golden).

**Diretriz para H3+ (se/quando o operador abrir):** o registro de tentativas
está LIGADO e é obrigatório — cada nova hipótese entra no `trials.json` (N+1) e
paga o DSR. Candidatas já nomeadas: reversão de curto prazo (mapa do design
§10), fundamentos/qualidade (exige fonte nova de dados — decisão de dependência
do operador). O sinal descritivo da baixa-vol (Sharpe maior com drawdown MUITO
menor) sugere que **H4-sizing (volatility targeting)** do mapa também é caminho
digno. Nada disso está autorizado sem novo pré-registro.

---

## VEREDITO FINAL DA H1 — ENCERRADA: NÃO COMPROVADA (2026-07-12)

Adjudicados os 15 candidatos a split de maior liquidez da quarentena (via WebSearch
contra fonte financeira nomeada, aprovação humana explícita `approved_by=Superleo13`
por linha, §9b/§11): B3SA3, PRIO3, SBSP3, BPAC11, BIDI11, CSAN3, IRBR3, CASH3, TOTS3,
BIDI4, ASAI3, UGPA3, VIVT3, LWSA3, NATU3 (este último tecnicamente uma bonificação de
ações 1:1, não desdobramento formal — efeito econômico idêntico, registrado com nota).
`main.py splits-import` gravou os 15 ajustes em `adjustments`; quarentena
correspondente resolvida. Os ~410 candidatos restantes (sem liquidez relevante para o
universo top-60) permanecem em quarentena conservadora — decisão formalizada do
operador, não silenciosa.

**Backtest final rodado sobre a base atualizada (COTAHIST real, 11 anos, 2018→2026):**

- **run_id:** `20260712T091903477689-41cc24`
- **2.092 pregões pareados**
- **PSR:** 0,4966
- **IC 95% da diferença de Sharpe (stationary bootstrap, bloco 21):** (−0,3192, 0,2933)
  — **cruza zero**
- Sharpe anualizado: estratégia 0,1592 vs. benchmark 0,1621 (benchmark levemente
  superior); Sortino 0,2128 vs. 0,2201; retorno total 5,72% vs. 8,03%; max drawdown
  49,77% vs. 48,03%.
- Relatório completo: [`reports/h1_verdict_20260712T091903477689-41cc24.md`](reports/h1_verdict_20260712T091903477689-41cc24.md)

**CONCLUSÃO FORMAL:** conforme os critérios fixados no pré-registro (§9), o IC 95% da
diferença de Sharpe contém zero → **H1 é "não comprovada nesta janela"**. A carteira de
momentum 12-1 não superou o buy-and-hold equiponderado do mesmo universo com
significância estatística. **Resultado válido e definitivo — sem repescagem de
parâmetros.** A H1 está oficialmente ENCERRADA.

**TrialRegistry (`measurement.trials`, DSR):** avaliado e decidido NÃO ligar para este
veredito — obrigatório apenas a partir de H2 em diante (desconta múltiplas tentativas
via Deflated Sharpe Ratio); para uma única hipótese pré-registrada isolada, o veredito
acima é válido sem ele. Fica disponível no core para quando H2/H3... forem abertas.

**Próximos passos / diretriz para H2:** A H1 foi encerrada sem comprovação de edge. O
próximo ciclo (H2) deve focar exclusivamente em uma Mudança Estrutural de Sinal
(Caminho 2 — ex: fundamentos, anomalias de momentum, volatilidade) para evitar
overfitting. O refinamento de parâmetros da H1 está estritamente vetado. Antes de
qualquer H2, ligar o `measurement.trials` (Experiment Registry + DSR + trava de poder)
é obrigatório (desconta múltiplas tentativas a partir da 2ª hipótese).

**Pausa estratégica (2026-07-12):** a ideação da H2 está PAUSADA por tempo
indeterminado. A prioridade atual do ecossistema é alocar recursos onde já existe
sinal comprovado e em validação operacional — Cripto/H5 e Brasileirão/Modo Sombra.
O laboratório de ações (predictor-stocks) entra em modo de ideação passiva: sem
próxima sessão de trabalho agendada até decisão em contrário do operador.

---

## Estado atual: M1–M6 — núcleo implementado sobre dados sintéticos ✓ (veredito real da H1 aguarda COTAHIST real)

**Data:** 2026-07-12
**Suíte:** 113/113 verde (`py -3.13 -m pytest tests/ -q`) — M0..M6 + plataforma (pedágio/telemetria/net/lacre frozen/guard de segredos); +4 testes vindos do sync do core v1.3.0-ga-20260711
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

### Porte do trabalho Red Team (main, não commitado) + custo por TURNOVER (2026-07-10)

Health-check dos 3 projetos irmãos (todos verdes: core 145, cripto 256, wc 234; vendors
em sincronia via `sync_core.py --check`) revelou **trabalho paralelo NÃO COMMITADO no
checkout principal deste repo** (auditoria "Red Team", jun/2026): 306 linhas em src/,
com uma correção material que esta linha não tinha. Portado para cá (a working tree da
main permanece intacta — reconciliação de branches é decisão do operador):

1. **Custo proporcional ao TURNOVER REAL** (`execution.calculate_turnover_cost` +
   `one_way_cost`; walk_forward rastreia prev_port): o modelo anterior cobrava o
   roundtrip de 0,36% sobre a carteira INTEIRA todo rebalance — assumia turnover de
   100%/mês e superestimava o arrasto ~3-5× para carteiras persistentes, viés CONTRA a
   estratégia. Agora só entra/sai paga (1 lado cada). É a leitura honesta do
   pré-registro ("custo 0,36% ida-e-volta" por operação, não por carteira-mês).
   Blindado por `test_turnover_cost_accuracy`.
2. **Veredito "SEM DADOS" ≠ "amostra curta"** no judge (pipeline vazio não se disfarça
   de veredito estatístico).
3. **Filtro à-vista na LEITURA** (`universe.SPOT_MARKET='010'` nas queries de
   universo/calendário) — defesa em camada p/ banco carregado com `avista_only=False`;
   fecha a pendência declarada na revisão. Migração append-only `0003` cria índice
   `(market_type, date)` (sem ele o predicado forçava full scan — backtest 46s→3m16s;
   com ele, 1m21s).
4. **Sanidade nos ajustes**: fator <= 0 => ValueError; fora de [0.05, 20] => warning;
   ex_date fora do range de preços => ignorado com warning.
5. **Snapshots imutáveis**: `materialize_snapshot` INSERT OR REPLACE → OR IGNORE.
6. + testes de regressão deles: quarentena futura não exclui (anti-lookahead),
   quarentena resolvida não exclui, turnover cost. **Suíte 109/109 verde.**

NÃO portado (avaliado): `next_open_after` retornando gap (muda shape da API por
logging marginal); asserts de pré-condição no factor; logs de debug.

**VEREDITO H1 re-rodado com custo justo (stationary, 2092 pregões):**
PSR 0,43→**0,57**; IC95% ΔSharpe (−0,400, 0,257)→**(−0,263, 0,387)** — o custo
superestimado estava de fato penalizando a estratégia; ainda assim o IC cruza zero:
**H1 segue "não comprovada"** nesta janela. Ressalva de sempre: ~426 candidatos a
split não adjudicados seguem fora (quarentena conservadora).

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

**Veredito H1:** **ENCERRADA — NÃO COMPROVADA** (2026-07-12, run_id
`20260712T091903477689-41cc24`). IC 95% diff-Sharpe (−0,3192, 0,2933) cruza zero. Ver
seção "VEREDITO FINAL DA H1" no topo deste arquivo para números completos e trilha de
adjudicação dos splits.

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
| M6 — Julgamento H1 + paper forward | ✓ **H1 ENCERRADA** | 2026-07-12 | `paper.py`: `record_forward` (EVAL antes do futuro, anti-tautologia) + `settle_executions` (RISK write-once via COALESCE); `backtest.run()` é o mecanismo do veredito. **Veredito H1 rodado sobre COTAHIST REAL (11 anos, 15 splits de maior liquidez adjudicados): não comprovada.** Ver seção "VEREDITO FINAL DA H1". **Falta:** ligar o cron diário do paper (não bloqueia H1; é infra p/ forward contínuo). |

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
