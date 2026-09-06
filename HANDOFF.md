# HANDOFF — predictor-stocks

> ## VEREDITO: os 5 critérios da H18 fecharam — VALE RODAR (2026-09-06)
>
> Medição final, com as duas pernas point-in-time corretas. Encerra a
> auditoria independente de 2026-09-04 (`docs/auditoria_2026-09-04.md`).
>
> ### Cobertura de `known_at` — 100%
>
>     total 1579 | com known_at 1579 (100.0%)
>       DFP: 733 linhas, 733 com known_at (100.0%)
>       FRE: 846 linhas, 846 com known_at (100.0%)
>
> **Nenhuma linha cai no embargo estimado.** Todo `known_at` é data
> observada de recebimento pela CVM (`DT_RECEB`). O
> `disclosure_embargo_days: 90` permanece no config como fallback, mas hoje
> não é exercido por nenhuma linha das fontes ingeridas.
>
> ### Os cinco critérios
>
> | # | critério | medido | veredito |
> |---|---|---|---|
> | 1 | coluna de ações existe e vem preenchida | derivada; BBAS3/ABEV3/ASAI3 conferem | APROVADO |
> | 2 | `shares_outstanding` em fração relevante | 846 linhas, 126 de 132 tickers | APROVADO |
> | 3 | duas pernas juntas por rebalance | mediana 49,5 papéis com E/P | APROVADO |
> | 4 | comparável a H7/H9/H12/H13 | 49,5 vs. 53 / 53 / 54 (~93%) | APROVADO |
> | 5 | nada entra antes de ser público | 100% `known_at` observado | APROVADO |
>
> **VALE RODAR A H18.** Foi a primeira vez, em toda a auditoria, que a
> resposta deixou de ser "não".
>
> ### Cobertura por rebalance (104 datas, 2026-09-06, pós-correção)
>
> | sinal | mediana | zeros | antes (embargo) |
> |---|---|---|---|
> | universo | 60,0 | 0 | 60,0 · 0 |
> | lucro | 56,0 | 12 | 56,0 · 15 |
> | ações | 57,0 | 12 | 58,0 · 3 |
> | E/P (H18) | 49,5 | 13 | 50,0 · 15 |
> | B/M (H19) | 53,0 | 13 | 53,0 · 15 |
> | roe (H7) | 53,0 | **15** | 53,0 · 15 |
> | lev (H9) | 53,0 | **15** | 53,0 · 15 |
> | marg (H12) | 54,0 | **15** | 54,0 · 15 |
> | accruals (H17) | 56,0 | 12 | 56,0 · 15 |
>
> **`roe`, `lev` e `marg` saíram IDÊNTICOS** enquanto `lucro` e `accruals`
> mudaram, sobre as MESMAS linhas de `fundamentals`. É a prova no dado real
> de que a política explícita por hipótese funciona: as julgadas continuam
> presas ao embargo estimado, H17/H18/H19 usam a data observada.
>
> ### Uma previsão minha que ERROU, e o mecanismo que ela revelou
>
> Antes de ver o resultado ficou registrado que o E/P deveria SUBIR. Ele
> CAIU de 50,0 para 49,5. A previsão estava incompleta, não a implementação:
>
> - quem entrega CEDO (BBAS3, fevereiro) fica elegível ANTES -> zeros do E/P
>   caem de 15 para 13;
> - quem entrega TARDE tem `DT_RECEB` POSTERIOR aos 90 dias e agora sai
>   corretamente do sinal em datas onde antes entrava -> a contagem cai em
>   algumas datas.
>
> Os dois efeitos brigam; o saldo foi -0,5 na mediana. **A queda é lookahead
> real sendo removido de quem entrega atrasado** — exatamente o que o embargo
> fixo escondia, e o motivo pelo qual a correção valeu a pena mesmo sem
> melhorar a cobertura agregada.
>
> ### DECISÃO PENDENTE — a ordem das rodadas, e ela precisa ser fixada ANTES da primeira
>
> O N do DSR cresce a cada tentativa registrada. Hoje são **15**. Quem rodar
> primeiro enfrenta N=16; a segunda, N=17; a terceira, N=18. **A terceira tem
> a barra mais alta só por ter sido rodada por último.**
>
> O pré-registro de 2026-09-04 NÃO fixou essa ordem. Escolher depois de ver
> qualquer resultado é p-hacking. Critério defensável sugerido: rodar na
> ordem de pré-registro (H17 -> H18 -> H19), arbitrária mas independente de
> qualquer expectativa sobre qual funciona.
>
> ### O que fica declarado e NÃO corrigido
>
> `execution.price: next_open` e `backtest.purge_embargo_months` continuam
> `[FROZEN]` e inertes — a liquidação real é close-to-close no dia do sinal.
> Vale igual para as 16 julgadas, então não torna a H18 especial, mas quem
> auditar o `config_hash` precisa saber. Ver a lista completa de dívidas na
> entrada "ESTADO ATUAL E PRÓXIMOS PASSOS".
>
> ### Estado
>
> `trials.json` em 15 tentativas, md5 `98BFC543DE1E80E2EAEC981E876E5A0C` —
> inalterado desde o início da auditoria. **H17/H18/H19 continuam NÃO
> EXECUTADAS.** Nenhuma métrica de desempenho delas foi observada por
> ninguém, que é o que mantém legítimos os re-pré-registros de 2026-09-06.
>
> Suíte: **374 verdes**.

---

> ## BUG: known_at da DFP nunca era gravado (2026-09-06, corrigido)
>
> A primeira rodada real da ingestão da DFP com `known_at` reportou
> **`TOTAL: 0 linhas gravadas`** e a cobertura saiu idêntica à anterior.
>
> Causa: `parse_dfp_received_dates` devolve chaves `(cnpj, ref_date)` —
> TUPLA — e a consulta usava só o CNPJ, uma string. Nunca casava.
> `known_at` ficava NULL em 100% das linhas, o `WHERE` do upsert não
> disparava, e a ingestão terminava com zero mudanças **sem erro nenhum**.
>
> O padrão veio copiado da versão do FRE, que é chaveada por `doc_id`
> (string), sem ajustar para a chave composta da DFP — os demonstrativos da
> DFP não trazem `ID_DOC`, por isso a chave é outra.
>
> **A suíte estava verde com a junção quebrada (372 testes).** O teste de
> então cobria `parse_dfp_received_dates` ISOLADO; a junção, que era onde
> estava o bug, não tinha cobertura. É o mesmo modo de falha que a auditoria
> de 2026-09-04 apontou no parser do FRE — teste que exercita a peça e não o
> encaixe — cometido por quem tinha acabado de apontá-lo.
>
> Correção: `_known_at_dfp()`, função nomeada com as duas indireções
> explícitas. Dois testes PONTA A PONTA novos, um deles verificado por
> reversão (com o bug de volta: `None != '2024-02-08'`; com a correção:
> verde), mais o de idempotência.
>
> ### O que a rodada de 2026-09-06 mostrou, antes da correção
>
> Cobertura idêntica à de antes em TODAS as linhas — consistente com zero
> linhas gravadas. Nenhuma contaminação ocorreu; as julgadas continuam
> intactas por não ter havido mudança alguma.
>
> ### A medição da DFP CONTINUA PENDENTE
>
> ```powershell
> git pull origin main
> py -3.13 tools\ingest_h7_real.py      # agora grava known_at de verdade
> py -3.13 tools\cobertura_h18.py
> ```
>
> Previsões registradas ANTES de ver o resultado:
> - `lucro`: 15 datas zeradas devem CAIR (DT_RECEB ~fevereiro vs. embargo 30/mar)
> - `E/P (H18)`: deve SUBIR — a perna do lucro era o gargalo
> - `roe`, `lev`, `marg`: devem ficar IDÊNTICOS (julgadas, presas ao embargo).
>   Se mudarem, a proteção falhou.
>
> Suíte: **374 verdes**. `trials.json` intacto em 15 tentativas.
> H17/H18/H19 continuam NÃO EXECUTADAS.

---

> ## DFP também tem DT_RECEB — H17 re-pré-registrada, julgadas protegidas (2026-09-06)
>
> `tools/explore_fre_ref_date.py --dataset dfp --anos 2023`, rodado pelo
> operador: `dfp_cia_aberta_2023.csv` traz `DT_RECEB`, igual ao FRE.
>
>     BBAS3 DFP 2023: DT_REFER 2023-12-31, DT_RECEB 2024-02-08
>     embargo de 90 dias liberaria só em 2024-03-30 -> 51 dias de atraso
>
> Ao contrário do FRE, o `DT_REFER` da DFP é fim de exercício DE VERDADE, e
> o embargo de 90 dias bate com o prazo regulamentar de 3 meses — era muito
> mais defensável. Ainda assim erra dos dois lados: atrasa quem entrega
> cedo (a maioria das grandes, em fevereiro) e ANTECIPA quem entrega
> depois de 90 dias, que aí entra no sinal antes de ser público.
>
> ### A armadilha que isso criava, e como foi resolvida
>
> `_fundamental_signals` preferia `known_at` sempre que existisse. Enquanto
> só o FRE gravava, isso afetava apenas H18/H19, que declararam a política.
> Com a DFP passando a gravar, **H7/H9/H10/H12/H13 mudariam de comportamento
> por efeito colateral da ingestão** — e o veredito delas é registro
> histórico, selado com o embargo estimado. Um re-run daria número diferente
> em silêncio, com o `config_hash` selado sem refletir isso.
>
> Correção: a preferência virou EXPLÍCITA por hipótese
> (`use_known_at`). As julgadas passam `False`, documentado como preservação
> do que foi efetivamente rodado. Nenhuma hipótese herda a política de outra.
>
> | hipótese | estado | política de `known_at` |
> |---|---|---|
> | H7, H9, H10, H12, H13 | JULGADAS | embargo estimado, explícito |
> | H17 | pré-registrada, nunca rodou | **observado** (re-pré-registro) |
> | H18, H19 | pré-registradas, nunca rodaram | observado (2026-09-06) |
>
> **Lacre da H17 re-emitido:** `aece696b814c0fd9` -> `e6cf9bd7454750c3`
> (entrou `known_at_policy: observed`). Legítimo pelo mesmo motivo de
> H18/H19: a H17 nunca rodou, nenhum resultado foi observado.
>
> ### Junção por (CNPJ, DT_REFER), não por documento
>
> Os CSVs de demonstrativo da DFP não trazem `ID_DOC` — diferente do
> `distribuicao_capital` do FRE. A junção é por `(CNPJ_CIA, DT_REFER)`,
> ficando com o `DT_RECEB` MAIS ANTIGO entre versões: é quando o exercício
> ficou público pela primeira vez. `parse_dfp_received_dates`.
>
> ### Remedição do FRE (2026-09-06) — o que ela mostrou
>
> Depois de re-ingerir o FRE com `known_at`, só a linha `acoes` mudou:
> mediana 58 -> 57, datas com zero 3 -> 12. É o lookahead de ~2 meses do
> FRE pré-2023 sendo removido, e é a PROVA de que o mecanismo funciona.
>
> **O E/P não se moveu** (mediana 50, 15 datas zeradas, idêntico) porque a
> perna do LUCRO (DFP) é o gargalo: 15 datas zeradas contra 12 das ações. O
> múltiplo é limitado pela perna mais escassa. H7/H9/H12/H13/H17 saíram byte
> a byte iguais no dado real — a promessa de não mudar nada retroativo se
> sustentou fora dos testes.
>
> ### O que falta agora
>
> ```powershell
> git pull origin main
> py -3.13 tools\ingest_h7_real.py              # backfill do known_at na DFP
> py -3.13 tools\cobertura_h18.py               # remedir com AS DUAS pernas corretas
> ```
>
> Só depois disso o critério 5 fecha: até aqui a perna das ações está
> point-in-time correta e a do lucro ainda não. Esta é a última medição.
>
> Suíte: **372 verdes**. `trials.json` intacto em 15 tentativas.
> H17/H18/H19 continuam NÃO EXECUTADAS.

---

> ## ESTADO ATUAL E PRÓXIMOS PASSOS (2026-09-06) — leia isto primeiro
>
> Consolidação escrita para não depender de nenhuma conversa: o chat da
> sessão de auditoria foi apagado, e tudo que importa está aqui, no
> `docs/auditoria_2026-09-04.md` e no `docs/RUNBOOK_H18.md`.
>
> ### Onde H17/H18/H19 estão
>
> **Pré-registradas, NUNCA executadas.** `trials.json` em 15 tentativas
> (md5 `98BFC543DE1E80E2EAEC981E876E5A0C`). Nenhuma métrica de desempenho
> delas foi observada por ninguém — nem Sharpe, nem PSR, nem DSR, nem
> retorno. Essa condição é o que tornou legítimo o re-pré-registro de
> 2026-09-06; se ela for quebrada, qualquer ajuste posterior de parâmetro
> vira p-hacking.
>
> ### Critérios de aceite da H18 (auditoria 2026-09-04)
>
> | # | critério | estado |
> |---|---|---|
> | 1 | coluna de ações existe e vem preenchida | APROVADO (derivada; ver 2026-09-05) |
> | 2 | `shares_outstanding` em fração relevante | APROVADO com o embargo ANTIGO — **remedir** |
> | 3 | duas pernas juntas por rebalance | APROVADO com o embargo ANTIGO — **remedir** |
> | 4 | comparável a H7/H9/H12/H13 | APROVADO com o embargo ANTIGO — **remedir** |
> | 5 | nada entra antes de ser público | **PENDENTE de remedição** |
>
> Os números de 2, 3 e 4 (E/P mediana 50, etc.) foram medidos ANTES da
> correção do `known_at`. **Não valem mais.** A correção muda QUANDO cada
> linha fica elegível: mais dado de 2023 em diante, menos antes de 2023.
>
> ### Os três passos que faltam, em ordem
>
> ```powershell
> git pull origin main
> py -3.13 tools\ingest_fre_shares_real.py     # backfill do known_at
> py -3.13 tools\cobertura_h18.py              # remedir 2, 3 e 4
> ```
>
> Sinal de sanidade esperado na remedição: mediana de E/P SOBE de 2023 em
> diante e CAI antes de 2023. Padrão diferente disso indica erro na
> implementação do `known_at` — investigar antes de seguir.
>
> Só depois disso o critério 5 pode ser declarado APROVADO e a pergunta
> "vale rodar a H18?" tem resposta. **Hoje a resposta ainda é NÃO**, e não
> por falta de código: por falta da medição pós-correção.
>
> ### A última incógnita: a DFP
>
> `tools/explore_fre_ref_date.py --dataset dfp --anos 2023` responde se o
> `dfp_cia_aberta_{ano}.csv` também traz `DT_RECEB`. Se trouxer, o embargo
> de 90 dias de H7/H9/H12/H13/H17 pode virar data OBSERVADA nas próximas
> rodadas, como já foi feito no FRE.
>
> **Isso NÃO reabre veredito nenhum.** As quatro julgadas deram
> NOT_SUPPORTED, e um embargo conservador demais não fabrica resultado
> positivo — no máximo esconde um. Reabertura exigiria o dossiê de 6 campos
> do `RESEARCH_FREEZE` §11, e nada aqui pede isso.
>
> ### Dívidas conhecidas e NÃO corrigidas
>
> 1. **`execution.price: next_open` e `backtest.purge_embargo_months` são
>    `[FROZEN]` mas o `walk_forward` NUNCA os lê.** A liquidação real é
>    close-to-close no dia do sinal. Está declarado no docstring de
>    `backtest.py`, mas o selo criptográfico afirma o que a máquina não faz.
>    Vale para as 16 hipóteses julgadas. Não muda veredito (o viés é o mesmo
>    para estratégia e benchmark), mas quem auditar o `config_hash` no
>    futuro vai concluir errado.
> 2. **`_pick_account` chaveia por nome de companhia normalizado**, com o
>    CNPJ disponível e não usado. Colisão vira `None` (fail-closed, não
>    fabrica número), mas derruba linhas boas em silêncio.
> 3. **`CLAUDE.md` diz que a fonte da verdade é `vendor/predictor_core/`**;
>    `tests/conftest.py:18` asserta o contrário. A suíte só roda contra as
>    wheels dos repos irmãos.
> 4. **Janela efetiva das hipóteses de fundamento é 2019-04 em diante**, não
>    2018-01 — 15 das 104 datas de rebalance não têm sinal contábil. Vale
>    RETROATIVAMENTE para H7/H9/H12/H13. Não invalida veredito; a janela
>    declarada é que estava errada.
>
> ### A MÁQUINA DO OPERADOR (verificado 2026-09-06)
>
> Fatos que não estavam em lugar nenhum e sem os quais uma sessão nova
> perde tempo — ou pior, roda no lugar errado:
>
> - **Repo canônico:** `C:\Users\Superleo13\stocks-predictor-work`
>   (o `docs/RUNBOOK_H18.md` chegou a mandar `C:\Claude-projetos\Claude\
>   stocks-predictor`, que NÃO EXISTE — palpite meu, corrigido).
> - **Existem QUATRO checkouts do projeto na máquina**; três com `stocks.db`
>   vazio (~110-140 KB) em `.kimi-work\predictors-audit\`,
>   `Documents\Codex\2026-08-27\...` e `Documents\Codex\2026-09-02\...`.
>   Rodar no errado grava no banco errado sem aviso. Confirme com
>   `python main.py`: `prices_raw` tem de dar ~1.149.872.
> - **`python` NÃO é o 3.13** nessa máquina: resolve para
>   `pythoncore-3.14-64` (3.14.6). Use `py -3.13` (3.13.14) em TUDO,
>   inclusive no `pip`.
> - **Artefatos locais não versionados na raiz do repo**, dos quais a
>   ingestão depende: `universo_2018_2026.txt` (obrigatório para
>   `ingest_h7_real.py`), `ticker_of_2019.json`, `ticker_of_proposto.json`,
>   `dfp_2023_companies.txt`, `dividend_exploration.txt`,
>   `universo_snapshots.txt`. Não apagar.
> - **Rede:** as máquinas de agente (Claude Code na web) NÃO alcançam
>   `dados.cvm.gov.br` — 403 na política de rede. Toda ingestão real roda na
>   máquina do operador. Isso valeu para a auditoria inteira.
>
> ### Onde está cada coisa
>
> - `docs/auditoria_2026-09-04.md` — o parecer independente, íntegro, com
>   nota de errata no topo. Estava em `reports/` (gitignored, efêmero);
>   movido para cá em 2026-09-06 para não se perder.
> - `docs/RUNBOOK_H18.md` — do zero até a medição, com tabela de erros comuns.
> - `tools/ingest_fre_shares_real.py`, `tools/cobertura_h18.py`,
>   `tools/explore_fre_ref_date.py` — ingestão, medição e investigação.
> - Entradas de 2026-09-05 e 2026-09-06 abaixo — os achados e as correções.
>
> Suíte: **370 verdes**.

---

> ## H18/H19 RE-PRÉ-REGISTRADAS (2026-09-06, ANTES de qualquer rodada)
>
> Ordem explícita do operador ("faz todas") sobre as duas correções que a
> entrada de 2026-09-05 deixou pendentes. **Isto é revisão de pré-registro,
> não mover a trave:** H18 e H19 NUNCA rodaram, nenhum resultado de
> desempenho foi observado por ninguém, e a trava do `cobertura_h18.py`
> existiu justamente para manter isso verdadeiro enquanto a cobertura era
> medida. Mudar parâmetro ANTES de qualquer observação é legítimo; depois
> seria p-hacking.
>
> **Lacres RE-EMITIDOS** (`config.py`): H18 `dded266f1bb712f1` ->
> `cbea4d3c98ac3422`; H19 `dabaa53adc9b9349` -> `d96753f2af7b39a6`.
> Entraram dois parâmetros novos em `h18_factor`/`h19_factor`:
> `known_at_policy: observed` e `split_base: adjusted`.
> `disclosure_embargo_days: 90` permanece como FALLBACK, aplicável só a
> linha sem `known_at`.
>
> **N do DSR inalterado:** 15 tentativas registradas; H18 seria a 16ª. O
> re-pré-registro não cria tentativa nova — nada foi rodado.
>
> ### Correção 1 — `known_at` OBSERVADO substitui o embargo estimado
>
> Migração `0012_fundamentals_known_at` (append-only): coluna `known_at` em
> `fundamentals`. A ingestão do FRE passa a ler o `DT_RECEB` do arquivo
> principal (`fre_cia_aberta_{ano}.csv`), casado por `ID_Documento` ->
> `ID_DOC` — logo por companhia E por versão do documento. Entre versões da
> mesma `(company, ref_date)` fica a data MAIS ANTIGA: é quando aquela
> informação ficou pública pela primeira vez.
>
> `factor._fundamental_signals` passa a preferir `known_at` quando existe, e
> só cai no embargo quando é NULL. **Todas as linhas da DFP têm `known_at`
> NULL hoje**, então H7/H9/H12/H13/H17 mantêm comportamento byte a byte —
> nenhum veredito emitido muda, e a H17 pré-registrada não é afetada.
>
> Corrige o erro que trocava de SINAL no meio da amostra (60 dias de
> lookahead até 2022; 305 dias conservador demais depois de 2023).
>
> ### Correção 2 — base de desdobramento
>
> `factor._shares_on_price_base`: as ações da `ref_date` do FRE são
> convertidas para a base de preço vigente em `asof`, dividindo pelos
> `adjustments.factor` de `type IN ('split','grupamento')` com
> `ex_date` em `(ref_date, asof]`. Só ajustes APROVADOS por humano contam
> (mesma disciplina de `adjust._load`); provento não entra, porque não muda
> quantidade de ações; `ex_date` estritamente maior que `ref_date`, porque
> evento na própria data de referência já está refletido na contagem
> publicada.
>
> Sem isso, BBAS3 (2.865.417.024 ações no FRE 2022 -> 5.730.799.931 no FRE
> 2023) teria o market cap subestimado em 50% na janela entre os dois
> formulários, dobrando o E/P e jogando o papel para o quintil "barato" por
> artefato mecânico — no papel mais líquido da bolsa.
>
> ### Bug encontrado ao implementar
>
> A primeira versão do upsert de `shares_outstanding` disparava UPDATE
> sempre que `known_at` fosse NULL nos dois lados, contando mudança em todo
> re-run e quebrando a idempotência já testada. Pego pelo teste de
> re-execução que já existia. O `WHERE` passou a exigir buraco A PREENCHER
> **e** valor novo PARA preencher.
>
> ### O que falta antes de rodar
>
> 1. **Re-ingerir o FRE** (`py -3.13 tools\ingest_fre_shares_real.py`) para
>    popular `known_at` — as 846 linhas gravadas em 2026-09-05 estão com
>    `known_at` NULL e cairiam no embargo antigo. O upsert faz backfill.
> 2. **Re-medir a cobertura** (`tools/cobertura_h18.py`): a mudança de
>    `known_at` altera QUANDO cada linha fica elegível, então os números de
>    critério 3 e 4 mudam — para melhor de 2023 em diante (o dado passa a
>    entrar ~10 meses antes) e para pior antes de 2023 (some o lookahead).
>    O critério 5 só pode ser declarado APROVADO depois disso.
> 3. **Verificar se a DFP também traz `DT_RECEB`** — se trouxer, o mesmo
>    tratamento vale para H7/H9/H12/H13/H17 nas próximas rodadas. Não
>    verificado; nada foi mudado na ingestão da DFP.
>
> Suíte: **370 verdes**. `trials.json` intacto em 15 tentativas.
> H17/H18/H19 continuam NÃO EXECUTADAS.

---

## Ingestão real de FRE/DFP e medição dos critérios de H18/H19 (2026-09-05)

Primeira vez que a ingestão do FRE roda contra dado REAL. Origem: auditoria
independente de 2026-09-04 (`reports/auditoria_2026-09-04.md`), que marcou
os critérios de aceite 2, 3 e 4 da H18 como **nunca medidos** — nem pela
sessão que pré-registrou H17/H18/H19, nem pela própria auditoria (ambas sem
banco e sem rede à CVM).

**Nenhuma hipótese foi executada.** H17/H18/H19 continuam não rodadas,
`trials.json` intacto em 15 tentativas, nenhum parâmetro `[FROZEN]` tocado.

### 1. BUG BLOQUEANTE corrigido: o FRE gravava FREE FLOAT como ações totais

`_find_col` casa por SUBSTRING, e as duas chaves de quantidade do FRE
colidiam no cabeçalho real: `Quantidade_Total_Acoes_Circulacao` contém tanto
`quantidade_total_acoes` (procurada por `shares_outstanding`) quanto
`circulacao` (procurada por `free_float`). O free float ia para o banco como
capital total, **sem erro e sem aviso**.

Consequência se tivesse rodado: `market_cap = preço × free float` infla E/P e
B/M por `1 ÷ (fração de circulação)` — fator que varia ~6x entre papéis na
B3. H18/H19 teriam ranqueado por **concentração acionária**, não por valor, e
o veredito consumiria tentativa irreversível do denominador do DSR.

O teste que devia pegar isso usava cabeçalho SINTÉTICO com duas colunas
separadas (`Quantidade_Total_Acoes` + `Quantidade_Acoes_Circulacao`) que a
CVM não publica — passava POR CONSTRUÇÃO, violando a regra "golden tests com
dados reais no parse" do `CLAUDE.md`. Corrigido com golden sobre as 15
colunas e 3 primeiras linhas do arquivo real de 2023 (PRs #52, #53).

Achado colateral, pré-existente: `free_float` casava
`Quantidade_Acoes_Ordinarias_Circulacao` (só ON) pelo keyword genérico
`"circulacao"`. Não afeta veredito — `load_free_float` não está ligada ao
`rj_pipeline`, que recebe free float por CSV.

### 2. O FRE NÃO publica ações totais — elas são DERIVADAS

`fre_cia_aberta_distribuicao_capital` publica, por classe e no total, apenas
a quantidade EM CIRCULAÇÃO e o PERCENTUAL que ela representa. Não existe
coluna de capital total emitido.

    ações totais = quantidade em circulação ÷ (percentual ÷ 100)

Verificação cruzada interna do próprio arquivo: o total derivado da linha
TOTAL bate com a soma dos totais derivados das pernas ON e PN a menos de
1e-4 relativo (arredondamento dos 6 decimais do percentual). Validado contra
companhias conhecidas: BBAS3 2023 = 5.730.799.931; ABEV3 = 15.726.802.114;
ASAI3 = 1.347.213.155.

O percentual vem em formato EN (`"49.596000"`), diferente das quantidades no
MESMO arquivo (inteiros sem separador). Parseado com a convenção BR viraria
49596000 e o total ficaria ~10^6x menor, em silêncio.

### 3. Critérios de aceite 1-4: MEDIDOS e APROVADOS

Ingestão real (`tools/ingest_h7_real.py` + `tools/ingest_fre_shares_real.py`)
sobre banco com `prices_raw` = 1.149.872: **718 linhas** de DFP e **846
linhas** de `shares_outstanding` gravadas. `fundamentals` passa a ter 1.579
linhas em 127 tickers.

| # | critério | medido | veredito |
|---|---|---|---|
| 1 | coluna existe e vem preenchida | derivada e validada (§2) | APROVADO |
| 2 | `shares_outstanding` em fração relevante | 846 linhas, 126 de 132 tickers (53,6%) | APROVADO |
| 3 | duas pernas juntas por rebalance | mediana 50 papéis com E/P | APROVADO |
| 4 | comparável a H7/H9/H12/H13 | H18 50 vs. H7 53, H9 53, H12 54 | APROVADO |
| 5 | nada entra antes de ser público | ver §4 | **REPROVADO** |

Cobertura por rebalance (104 datas desde 2018-01-01, `tools/cobertura_h18.py`,
somente leitura, mede COBERTURA e nunca desempenho):

| sinal | mediana | mín | máx | datas com 0 |
|---|---|---|---|---|
| universo | 60 | 60 | 60 | 0 |
| lucro | 56 | 0 | 57 | 15 |
| ações | 58 | 0 | 58 | 3 |
| E/P (H18) | 50 | 0 | 53 | 15 |
| B/M (H19) | 53 | 0 | 54 | 15 |
| roe (H7) | 53 | 0 | 54 | 15 |
| accruals (H17) | 56 | 0 | 57 | 15 |

`accruals` com 716 linhas em 123 tickers: a H17 ganhou insumo. Isso exigiu
RE-RODAR a ingestão da DFP num banco já ingerido — o upsert de `fundamentals`
(`ingest_cvm.py`) faz backfill via `COALESCE` das colunas acrescentadas
depois (receita/margem na migração 0010; fluxo de caixa/accruals na 0011).
Sem esse re-run, um banco anterior à 0011 não tem accruals e a H17 ficaria
sem insumo em silêncio.

### 4. Critério 5 REPROVADO: o embargo de 90 dias erra em DIREÇÕES OPOSTAS

A `ref_date` gravada muda de convenção no meio da amostra:

    BBAS3  2019-01-01 .. 2022-01-01     primeiro dia do ano
    BBAS3  2023-12-31 .. 2026-12-31     último dia do ano

`tools/explore_fre_ref_date.py` (rodado pelo operador contra 2019/2022/2023/
2024) mostrou por quê: o arquivo principal `fre_cia_aberta_{ano}.csv` traz
`DT_RECEB`, a data de recebimento do documento pela CVM.

| ano | `DT_REFER` | `DT_RECEB` (real) | `known_at` usado (ref+90d) | erro |
|---|---|---|---|---|
| 2019 | 2019-01-01 | 2019-05-21 | 2019-04-01 | 50 dias de LOOKAHEAD |
| 2022 | 2022-01-01 | 2022-05-31 | 2022-04-01 | 60 dias de LOOKAHEAD |
| 2023 | 2023-12-31 | 2023-05-30 | 2024-03-30 | 305 dias CONSERVADOR DEMAIS |
| 2024 | 2024-12-31 | 2024-05-29 | 2025-03-31 | 306 dias CONSERVADOR DEMAIS |

No FRE 2023 a data de referência é POSTERIOR à entrega: recebido em maio de
2023, rotulado `2023-12-31`. **`DT_REFER` é rótulo de exercício, não data do
dado** — somar dias a esse campo não produz nada interpretável, e o viés não
é constante: troca de sinal em 2023.

A auditoria de 2026-09-04 estimou "lookahead de ~2 meses". Estava certa para
2019-2022 e ERRADA para 2023+, onde o erro inverte e fica dez vezes maior.

**Caminho de correção disponível, NÃO implementado:** join
`distribuicao_capital.ID_Documento` -> `fre_cia_aberta_{ano}.csv.ID_DOC` ->
`DT_RECEB` dá o `known_at` OBSERVADO, por empresa e por versão do documento
— eliminando o embargo em vez de recalibrá-lo. É o que `ingest_ipe_year` já
faz com `Data_Entrega` para fatos relevantes, e o que o protocolo §8 pede.
Implementar isso muda `disclosure_embargo_days`, que é `[H18-FROZEN]` e
`[H19-FROZEN]` — **exige decisão do operador e re-pré-registro**.

Pergunta aberta relacionada: se `dfp_cia_aberta_{ano}.csv` também traz
`DT_RECEB`, o mesmo vale para H7/H9/H12/H13/H17 nas próximas rodadas. Não
verificado.

### 5. Desdobramento deixou de ser risco teórico

    BBAS3  2022-01-01   2.865.417.024
    BBAS3  2023-12-31   5.730.799.931     exatamente 2x

`factor._value_signals` compõe `preço_cru(asof) × ações(ref_date do FRE)`. Com
um desdobramento no intervalo, as duas pernas ficam em bases diferentes e o
market cap erra pelo fator do split — no papel mais líquido da bolsa. A
tabela `adjustments` permite corrigir (`type IN ('split','grupamento')`,
`ex_date`, `factor`), mas `_value_signals` não faz isso hoje e nenhum teste
cobre o caso. Também exige decisão: corrigir muda o sinal de hipótese
pré-registrada.

### 6. Janela efetiva das hipóteses de fundamento: 2019-04 em diante

15 das 104 datas de rebalance têm ZERO papéis com sinal contábil. Não é bug:
a DFP ingerida começa no exercício 2018 (`ref_date` 2018-12-31), elegível só
a partir de 2019-03-31 com o embargo de 90 dias. De 2018-01 a 2019-03 são
exatamente 15 meses.

**Isto vale RETROATIVAMENTE para H7/H9/H12/H13**, que foram julgadas com a
mesma limitação. Não invalida veredito nenhum (`walk_forward` pula rebalance
sem carteira), mas a janela efetiva dessas hipóteses é 2019-04 a 2026, não
2018-01 a 2026 como o `backtest.test_start` sugere. Nunca foi registrado.

### 7. Higiene de log

O `WARNING` da colisão de coluna anunciava `shares_outstanding=None` e calava
que o total é derivado logo em seguida: 3-4 avisos alarmantes por ano de
ingestão, nenhum acionável, num caminho correto. Aviso que assusta sem
informar treina o operador a ignorar avisos. Agora o nível distingue: com
coluna de percentual nada se perde (INFO); sem ela a derivação é impossível e
o dado se perde (WARNING). Dois testes travam o comportamento.

### PRs desta sessão

#52 (colisão detectada, fail-loud), #53 (derivação + golden real), #54
(scripts de ingestão e cobertura), #55 (`docs/RUNBOOK_H18.md`), #56 (higiene
de log + probe da ref_date), #57 (falso negativo do probe: as pistas exigiam
`"recebimento"` inteiro e a coluna real é `DT_RECEB` — mesmo erro de
palavra-chave que a auditoria pegou no parser, com sinal trocado).

Suíte: **363 verdes**.

### PENDENTE DE DECISÃO DO OPERADOR

H18/H19 têm fonte de dado, cobertura adequada e quatro dos cinco critérios
aprovados. **Não devem rodar** enquanto o critério 5 estiver reprovado.
Opções, todas mexendo em `[FROZEN]`:

1. Re-pré-registrar H18/H19 com `known_at` observado (`DT_RECEB`) —
   elimina o embargo em vez de recalibrá-lo, e corrige os dois lados do erro.
2. Manter o embargo de 90 dias declarando a limitação no pré-registro —
   agora sabendo que ela inverte de sinal em 2023.
3. Investigar antes se a DFP traz `DT_RECEB`, para decidir uma vez só
   incluindo H7/H9/H12/H13/H17.

Decisão do desdobramento (§5) é separada e igualmente do operador.

---

> ## H11 ABERTA — PRÉ-REGISTRO (2026-09-04, ANTES de qualquer rodada real)
>
> Decisão explícita do operador ("todos vamos fazer tudo"), primeira
> hipótese a usar a infraestrutura de retorno total (entrada abaixo). **H11
> — momentum 12-1 em RETORNO TOTAL** (`config.yaml` `h11_*`,
> `config.h11_frozen_config_hash` = `1a75b7f12695cc97`): mesmo sinal
> exato da H1 (momentum 12-1, quintil superior, equiponderado), mas sobre
> `adjust.total_return_series` (proventos reinvestidos) em vez de
> `adjust.adjusted_series` (só-preço). Racional: o pré-registro da H1
> declarou que omitir proventos FAVORECE momentum contra o benchmark
> (papéis de momentum tendem a menor yield) — a H11 testa se corrigir esse
> viés muda o veredito.
>
> **Janela restrita 2018-01-01 a 2022-12-31** (`h11_backtest.test_start/
> test_end`, NÃO os mesmos de `backtest.test_start` global) — a cobertura
> real de `dividends` (CVM/FRE) só é confiável nesse período (achado
> registrado nesta mesma sessão, entrada "Retorno TOTAL implementado"
> abaixo); 2023-2026 ficam de fora até uma fonte melhor aparecer. Isso é
> MENOS dado que H1 (2018-2026 completo) — declarado, não escondido.
>
> **Critério:** IC95% diff-Sharpe > 0 E DSR >= 0,95 (N=10 tentativas no
> registro, contando H1/H2/H4/H5/H6/H7/H8/H9/H10).
>
> **Implementação:** `backtest.walk_forward` ganhou dois parâmetros novos,
> ambos com default que preserva H1-H10 byte a byte: `series_fn` (troca a
> fonte de preço — default `adjust.adjusted_series`) e
> `cfg["backtest"]["test_end"]` (corta a janela — default `None` = sem
> corte). `_run_hypothesis` repassa `series_fn`. `run_h11` monta uma CÓPIA
> de `cfg["backtest"]` só pra própria rodada (testado explicitamente —
> `test_run_h11_does_not_mutate_shared_config` — que o `cfg` compartilhado
> não é alterado, H1-H10 continuam vendo `test_start`/ausência de
> `test_end` originais). `config.py` (`H11_FROZEN_KEYS`/
> `h11_frozen_config_hash`), `report._BIAS_NOTE["H11"]` (declara a
> cobertura parcial de proventos + as duas aproximações da fonte).
> Testes em `tests/test_h11_total_return.py` (smoke com proventos
> sintéticos, golden hash, hash ignora parâmetro operacional, não-mutação
> do cfg compartilhado) — validados manualmente nesta sessão (sandbox sem
> `pytest`). Regressão de H1 (`backtest.run`) e H6 confirmada funcionando
> sem alteração após a mudança em `walk_forward`.
>
> **Próximo passo:** dado real já está na sua máquina (a mesma ingestão de
> `dividends` já rodada) — só falta `python -m pytest tests/ -v` e
> `python -c "import backtest; backtest.run_h11(write_report=True)"`.

> ## Retorno TOTAL implementado (2026-09-04) — infraestrutura opt-in, NÃO uma hipótese
>
> Decisão do operador ("A e B" + confirmação de prosseguir com a aproximação
> declarada): construir a ROTA (a) do design §4 (preço + proventos
> reinvestidos), corrigindo o viés só-preço declarado em TODAS as 9
> hipóteses julgadas (H1-H10, exceto H3 que nunca existiu). **Isto é
> infraestrutura, não uma hipótese nova** — mesma classificação do
> `economic_gate.py` (2026-09-01): fica disponível para quem pré-registrar
> a próxima hipótese, não altera nenhum veredito já emitido.
>
> **Fonte confirmada** (via `tools/explore_dividend_sources.py`, rodado pelo
> operador): `fre_cia_aberta_distribuicao_dividendos_classe_acao_{ano}.csv`
> (Montante + Data_Pagamento_Dividendo por categoria de distribuição) +
> `fre_cia_aberta_distribuicao_capital_{ano}.csv` (Quantidade_Total_Acoes_Circulacao,
> arquivo PRINCIPAL — não o `_classe_acao`, que só cobre PN).
>
> **Duas aproximações declaradas** (aprovadas pelo operador para prosseguir,
> não escondidas):
> 1. Valor por ação = Montante (somado por categoria/pagamento) ÷ total de
>    ações em circulação (ON+PN) — não por classe específica. Companhias
>    com política de proventos muito diferente entre ON/PN ficam com um
>    valor médio, não exato por classe.
> 2. `Data_Pagamento_Dividendo` usada como proxy de `ex_date` — a data-ex
>    real (que de fato move o preço) tipicamente vem semanas/meses antes;
>    este dataset da CVM não expõe a data-ex diretamente.
>
> **Implementação:**
> - `stocks_predictor/db.py`: migração `0009_dividends` — tabela nova
>   (`ticker, ex_date, value_per_share, source`), append-only,
>   `UNIQUE(ticker, ex_date, source)`. Domínio independente de
>   `prices_raw`/`adjustments` (não referencia, não é referenciado).
> - `stocks_predictor/ingest_cvm.py`: `parse_fre_dividend_rows`,
>   `parse_fre_capital_total_rows` (fail-loud sem coluna esperada, nunca
>   fabrica número), `ingest_fre_dividends_year` (mesmo contrato de
>   `ingest_dfp_year`: `companies`/`ticker_of`, `INSERT OR IGNORE`). Achado
>   ao implementar: `_open_zip_csv(zbytes, "distribuicao_capital")` é
>   AMBÍGUO no zip do FRE (bate tanto no arquivo principal quanto no
>   `_classe_acao`) — resolvido com filtro manual de nome excluindo
>   `classe_acao`, documentado no código (não é bug do `_open_zip_csv`
>   genérico, é a especificidade deste caso). `_to_float` tolera os dois
>   formatos numéricos que a CVM mistura entre datasets (ponto decimal nos
>   exports novos vs. vírgula decimal BR em datasets mais antigos já usados
>   no projeto) — tenta ponto primeiro, cai para vírgula só se falhar.
> - `stocks_predictor/adjust.py`: `dividend_factor` (mesma direção
>   matemática de `adjusted_closes` — multiplica preços ANTES da ex_date),
>   `total_return_series` (combina `adjusted_series`, já split-ajustada, com
>   `dividends`; proventos fora do range de preços são ignorados com aviso,
>   mesma disciplina de `adjustments` fora de range).
> - `tools/ingest_dividends_real.py`: script de ingestão real 2018-2026, por
>   ano (mesmo padrão de `tools/ingest_h7_real.py`) — roda na máquina do
>   operador (rede à CVM necessária).
> - Testes: `tests/test_adjust.py` (4 novos —
>   `test_dividend_factor_known_value`,
>   `test_total_return_series_lowers_prices_before_ex_date`,
>   `test_total_return_series_no_dividends_matches_adjusted_series`,
>   `test_total_return_series_dividend_outside_range_ignored`). Validados
>   manualmente nesta sessão (sandbox sem `pytest`) contra dado sintético
>   E contra uma amostra real (linhas literais de
>   `fre_cia_aberta_distribuicao_dividendos_classe_acao_2023.csv` coladas
>   pelo operador via `explore_dividend_sources.py`).
>
> **NÃO FEITO nesta sessão:** ingestão real de proventos 2018-2026 (precisa
> rodar `tools/ingest_dividends_real.py` na máquina do operador — mesmo
> bloqueio de rede de sempre neste sandbox) e nenhuma hipótese usa
> `total_return_series` ainda — é infraestrutura pronta, esperando a
> próxima hipótese pré-registrada que decida usá-la (H11 em diante).
>
> **Atualização (2026-09-04, mesmo dia) — ingestão real rodada, achado
> IMPORTANTE de cobertura temporal:** `tools/ingest_dividends_real.py`
> executado pelo operador: **2.384 linhas gravadas em `dividends`**, mas com
> cobertura MUITO desigual entre anos:
>
> | ano | linhas | situação |
> |---|---|---|
> | 2018 | 366 | ok |
> | 2019 | 509 | ok |
> | 2020 | 530 | ok |
> | 2021 | 486 | ok |
> | 2022 | 485 | ok |
> | 2023 | **8** | suspeito — muito abaixo do padrão, não investigado ainda |
> | 2024 | 0 (falhou) | `fre_cia_aberta_distribuicao_dividendos_classe_acao_2024.csv` **não existe** no zip FRE 2024 (nem a versão sem `_classe_acao`) — zip de 2024 tem 35 arquivos contra 56 do de 2023, a CVM aparentemente parou de publicar esse CSV específico a partir de 2024 |
> | 2025 | 0 (falhou) | mesmo motivo do 2024 |
> | 2026 | 0 (falhou) | mesmo motivo do 2024 |
>
> **Implicação real:** a série de retorno total cobre bem 2018-2022, mas fica
> capenga de 2023 em diante — justo a parte mais recente da janela 2018-2026
> usada em H1-H10. Isso NÃO invalida a infraestrutura (ela é honesta sobre o
> que tem: `total_return_series` só aplica os proventos que existem em
> `dividends`, sem inventar nada para os anos sem cobertura — o resultado
> pra 2023-2026 fica equivalente à rota (b) só-preço, não errado, só
> incompleto) — mas qualquer hipótese futura que use `total_return_series`
> precisa declarar essa limitação de cobertura explicitamente, e o
> `_BIAS_NOTE` dela não pode alegar "retorno total corrigido" sem qualificar
> o período.
>
> **Investigação do 2023 concluída (2026-09-04, mesmo dia): NÃO é bug do
> parser.** Diagnóstico rodado pelo operador: `parse_fre_dividend_rows` sobre
> o zip FRE 2023 devolve só **58 linhas brutas / 9 empresas distintas**,
> ANTES de qualquer filtro por universo/ticker — a fonte da CVM já vem rala
> nesse ano, não é perda no match de ticker. Consistente com o achado de
> 2024-2026 (arquivo sumiu de vez): a CVM parece ter mudado/descontinuado a
> forma de reportar distribuição de dividendos no FRE bem na transição
> 2023→2024 — não é algo que dá pra corrigir ajustando o parser deste lado.
>
> **Cobertura real confirmada da fonte FRE para retorno total: sólida
> 2018-2022, praticamente inexistente 2023-2026.** Decisão de prioridade
> (não tomada nesta sessão): (1) aceitar a cobertura parcial e usar
> `total_return_series` só para períodos/hipóteses dentro de 2018-2022; (2)
> buscar fonte alternativa pra 2023-2026 (dataset próprio da B3, não
> investigado por falta de acesso de rede neste ambiente); (3) não usar
> retorno total até resolver a lacuna. Fica registrado como limitação
> conhecida da infraestrutura, não como bug.

> ## H10 ABERTA — PRÉ-REGISTRO (2026-09-04, ANTES de qualquer rodada real)
>
> Decisão explícita do operador ("A e B", após o veredito NÃO COMPROVADA da
> H9): opção (a) — filtro duplo ROE ∩ alavancagem, mesmo racional da H8
> (momentum∩baixa-vol) aplicado às duas variáveis contábeis já testadas
> isoladamente (H7 ROE, H9 alavancagem, ambas NÃO COMPROVADAS). **H10 —
> filtro duplo ROE ∩ baixa alavancagem** (`config.yaml` `h10_*`,
> `config.h10_frozen_config_hash` = `150023ca75fd4324`): top 40% do universo
> por ROE, depois metade de menor alavancagem DENTRO desse subconjunto —
> interseção explícita de tickers com AMBOS os sinais antes de rankear
> (mesma disciplina de `portfolio.momentum_lowvol_double_filter`). Mesmo
> dado já ingerido pela H7 (`fundamentals.roe`/`leverage`), não exige nova
> ingestão.
>
> **Critério:** IC95% diff-Sharpe > 0 E DSR >= 0,95 (N=9 tentativas no
> registro, contando H1/H2/H4/H5/H6/H7/H8/H9).
>
> **Implementação:** `portfolio.double_filter` (motor genérico extraído de
> `momentum_lowvol_double_filter` — refactor comportamento-preservado,
> regressão confirmada byte a byte contra os testes existentes da H8,
> incluindo o golden hash `h8_frozen_config_hash`), `portfolio.
> roe_lowlev_double_filter` (H10, reaproveita o motor), `backtest.run_h10`
> (mesmo runner genérico, `portfolio_fn` fecha sobre `conn`),
> `config.py` (`H10_FROZEN_KEYS`/`h10_frozen_config_hash`),
> `report._BIAS_NOTE["H10"]`. Testes em `tests/test_h10_double_filter.py`
> (smoke, golden hash, teste de interseção com valores conhecidos) —
> validados manualmente nesta sessão (mesma limitação de ambiente sem
> `pytest`). Dado real já disponível — só falta rodar:
> `python -c "import backtest; backtest.run_h10(write_report=True)"`.

> ## VEREDITO H10 — ENCERRADA: NÃO COMPROVADA (2026-09-04, rodada única, dado real)
>
> Suíte confirmada (265 passed + 1 falha pré-existente/não relacionada,
> versão do Core instalado). Rodada única via `backtest.run_h10(write_report=True)`,
> dado já ingerido pela H7 (sem ingestão nova).
>
> - 1.826 pregões pareados
> - **IC 95% diff-Sharpe (stationary, bloco 21): (−0,3820, +0,2029)** — cruza zero
> - **DSR: 0,3661 < 0,95** (N=9)
> - PSR 0,4139.
> - **Não comprovada. Sem repescagem.**
> - Relatório: `reports/h10_verdict_adhoc.md` (a versionar via `git add -f`).
>
> **Leitura acumulada (9 tentativas, 0 comprovadas):** nem os fatores contábeis
> isolados (H7 ROE, H9 alavancagem) nem sua interseção (H10) sobrevivem ao
> pedágio — mesmo padrão da H8 (interseção momentum∩baixa-vol também
> reprovou). As duas variáveis contábeis da DFP e sua combinação estão
> esgotadas. `RESEARCH_FREEZE.md`/`STOCKS_CURRENT_STATE.md` atualizados de
> volta a `FROZEN`/`CLOSED`.
>
> **Próxima frente aberta pelo operador (decisão "A e B" + confirmação
> posterior): construir uma série de RETORNO TOTAL (preço + proventos
> reinvestidos)** para corrigir o viés só-preço declarado em TODAS as 9
> hipóteses. Fonte confirmada via `tools/explore_dividend_sources.py`
> (rodado pelo operador, saída no HANDOFF abaixo):
> `fre_cia_aberta_distribuicao_dividendos_classe_acao_{ano}.csv` (CVM/FRE) —
> `Montante` (total distribuído no ano por classe de ação) e
> `Data_Pagamento_Dividendo`. **Limitação declarada, aprovada pelo
> operador para prosseguir mesmo assim:** (1) `Montante` é AGREGADO
> anual por classe, não valor por ação — precisa dividir pela quantidade de
> ações da classe (`fre_cia_aberta_distribuicao_capital_classe_acao`) para
> aproximar o valor por ação; (2) `Data_Pagamento_Dividendo` é a data de
> PAGAMENTO, não a data-ex real (que costuma vir semanas/meses antes) — usada
> como proxy conservador. Ver próxima entrada de HANDOFF para a
> implementação.

> ## H9 ABERTA — PRÉ-REGISTRO (2026-09-04, ANTES de qualquer rodada real)
>
> Decisão explícita do operador ("vamos fazer", após o veredito NÃO COMPROVADA
> da H7). Mesma disciplina de pré-registro: formalizar ANTES de qualquer
> rodada. **H9 — fator de qualidade, alavancagem isolada**
> (`config.yaml` `h9_*`, `config.h9_frozen_config_hash` = `af797c56c2ab36b7`):
> quintil INFERIOR de alavancagem (`fundamentals.leverage`, empresas MENOS
> endividadas), mesma fonte DFP/CVM e mesmo embargo de divulgação de 90 dias
> da H7 — **dado já ingerido** (a mesma ingestão real 2018-2026 da H7 gravou
> `leverage` junto com `roe`, mesma linha da tabela `fundamentals`), não exige
> nova ingestão nem `tools/ingest_h7_real.py` de novo. Racional: mesmo tilt de
> qualidade/baixo risco de H2 (baixa vol)/H4 (inverse-vol sizing), aplicado a
> dado contábil em vez de preço.
>
> **Critério:** IC95% diff-Sharpe > 0 E DSR >= 0,95 (N=8 tentativas no
> registro, contando H1/H2/H4/H5/H6/H7/H8). Fixado antes de qualquer rodada.
>
> **Implementação:** `factor._fundamental_signals` (motor comum extraído de
> `roe_signals`, reaproveitado por `leverage_signals` — mesmo mecanismo de
> embargo, sem duplicar lógica), `backtest.run_h9` (mesmo runner genérico,
> `take="bottom"`), `config.py` (`H9_FROZEN_KEYS`/`h9_frozen_config_hash`),
> `report._BIAS_NOTE["H9"]` (mesma limitação declarada da H7: direção do viés
> só-preço não estabelecida). Testes em `tests/test_h9_quality_leverage.py`
> (smoke com dado sintético, golden hash, hash ignora parâmetro operacional,
> embargo bloqueia leitura antecipada) — validados manualmente nesta sessão
> (mesma limitação de ambiente da H7: sandbox sem `pytest`/rede à CVM/
> `stocks.db` real). Regressão de `factor.roe_signals` confirmada após o
> refactor para `_fundamental_signals` (mesmo resultado de antes).
>
> **Como o dado já está na sua máquina, o próximo passo é só rodar** (sem
> ingestão nova): `python -m pytest tests/ -v` (confirmar suíte verde) e
> `python -c "import backtest; backtest.run_h9(write_report=True)"` (rodada
> única, sem repescagem).

> ## VEREDITO H9 — ENCERRADA: NÃO COMPROVADA (2026-09-04, rodada única, dado real)
>
> Suíte pytest confirmada na máquina do operador (260 passed + 2 falhas
> pré-existentes/não relacionadas: `test_predictor_core_version_is_at_least_3`,
> Core instalado 2.2.0 vs 3.0.0 esperado — achado antigo, nada a ver com H9; e
> `test_unknown_hypothesis_does_not_inherit_h1_bias_note`, que usava "H9" como
> placeholder genérico — corrigido pra "H99" no mesmo commit). Rodada única via
> `backtest.run_h9(write_report=True)`, dado já ingerido pela H7
> (`fundamentals.leverage`, sem ingestão nova).
>
> - 1.826 pregões pareados
> - **IC 95% diff-Sharpe (stationary, bloco 21): (−0,3724, +0,1602)** — cruza zero
> - **DSR: 0,3479 < 0,95** (N=8)
> - PSR 0,3987.
> - **Não comprovada. Sem repescagem.**
> - Relatório: `reports/h9_verdict_adhoc.md` (a versionar via `git add -f`,
>   mesmo padrão de H6/H7/H8).
>
> **Leitura acumulada (8 tentativas, 0 comprovadas):** as duas variáveis
> contábeis disponíveis na DFP da CVM (ROE e alavancagem, isoladas) também não
> sobrevivem ao pedágio nesta janela/universo — mesmo desfecho do baralho
> só-preço. `RESEARCH_FREEZE.md`/`STOCKS_CURRENT_STATE.md` atualizados de
> volta a `FROZEN`/`CLOSED` — a `reopen_policy` agora cobre também
> "qualidade/alavancagem".

> ## Errata de schema em `trials.json` (2026-09-03) — campo órfão removido, NENHUM veredito alterado
>
> Ao tentar registrar a H7 na máquina do operador (Core `predictor-core==3.0.0` real,
> não o vendor/shim), `trials_gate.apply_dsr` falhou com
> `ValueError: registro violaria o schema de trials` — não na trial nova, mas em
> `trial[4]` (`h6-momentum-6-1`) e `trial[5]` (`h8-mom-lowvol-double`), que tinham um
> campo `"pipeline_fingerprint": null` gravado **dentro do objeto da trial**. Inspeção
> do código-fonte real do wheel 3.0.0 (`predictor_core/measurement/trials.py`,
> `_TRIAL_FIELDS`) confirma que esse campo **não faz parte do schema** — é só um
> parâmetro de validação passado na hora de `register()` (comparado contra o
> atestado), nunca deveria ter sido persistido no registro. Alguma chamada/versão
> anterior gravou esse campo a mais quando H6/H8 foram registradas (H1/H2/H4/H5 não
> têm); o Core 3.0.0 real, mais estrito, passou a rejeitar a lista inteira por causa
> dessas duas entradas — bloqueando qualquer registro novo, não só a H7.
>
> **Correção**: removida só a chave `"pipeline_fingerprint": null` (valor sempre nulo,
> nunca teve dado real) de `trial[4]`/`trial[5]` — `name`, `registered_at`, `params`,
> `sharpe`, `notes`, `metric`, `test_period` de H6/H8 preservados byte a byte. Nenhum
> veredito, Sharpe ou parâmetro `[H6-FROZEN]`/`[H8-FROZEN]` foi tocado — é limpeza de
> schema, mesma disciplina do `tools/migrate_trials_schema.py` já existente no
> projeto. Validado: `json.load` + checagem de chaves nas 6 trials, todas agora com o
> mesmo conjunto de campos.

> ## H7 ABERTA — PRÉ-REGISTRO (2026-09-03, ANTES de qualquer rodada real) — implementada, NÃO julgada
>
> Decisão explícita do operador ("faz tudo" / "o que precisar pro lucro"), após o
> `RESEARCH_FREEZE.md` (2026-09-02) fechar formalmente a pesquisa em 6 hipóteses
> só-preço (H1/H2/H4/H5/H6/H8, todas não comprovadas). H7 é a única fronteira
> honesta que restava: dado NOVO (fundamentos DFP da CVM, `ingest_cvm.py`, já
> ingerido só em formato sintético desde 2026-08-27), nunca usada em sinal. Isso
> **não** é reabertura de família encerrada (não toca H1-H6/H8, não exige os 6
> campos de `reopen_policy` do `RESEARCH_FREEZE.md` — essa política cobre as
> famílias já fechadas, não uma hipótese nova) — é a mesma disciplina de
> pré-registro usada em H4/H5/H6/H8: formalizar ANTES de qualquer rodada real.
>
> **HIPÓTESE #7 (pré-registrada — critérios fixados ANTES de ver o dado real):**
>
> **H7 — fator de qualidade, ROE isolado** (`config.yaml` `h7_*`,
> `config.h7_frozen_config_hash` = `61fd7d1c73999c73`): carteira long-only do
> **quintil SUPERIOR de ROE** (lucro líquido / patrimônio líquido,
> `fundamentals.roe`), universo B3 point-in-time (top 60 por liquidez, mesma
> régua de H1/H2/H4/H5/H6/H8), equiponderada, mesmo custo/execução/pedágio.
> Racional: fator "quality" clássico da literatura (empresas mais rentáveis
> tendem a superar em janelas longas) — nunca testado neste projeto porque
> nenhuma hipótese anterior usa dado contábil, só preço.
>
> **Sinal e embargo (`factor.roe_signals`, novo):** `fundamentals.ref_date`
> (fim do exercício contábil) **não** é a data de publicação real — a DFP é
> divulgada meses depois (já registrado em `ingest_cvm.py` desde 2026-08-27,
> nunca implementado). `disclosure_embargo_days: 90` (`[H7-FROZEN]`) soma um
> embargo fixo sobre `ref_date`: em cada `asof`, só entra a linha mais recente
> com `ref_date + 90d <= asof`. Prazo escolhido por ser o prazo regulamentar
> típico de entrega da DFP anual à CVM — não é a data de entrega REAL por
> companhia (que existiria em outro campo da fonte, não capturado por
> `ingest_dfp_year` nesta versão); é um embargo CONSERVADOR mas aproximado,
> limitação declarada, não escondida.
>
> **Critério:** IC95% diff-Sharpe > 0 E DSR >= 0,95 (N=7 tentativas no
> registro, contando H1/H2/H4/H5/H6/H8). Fixado antes de qualquer rodada real.
>
> **Implementação (código, testado com dado sintético):**
> `factor.roe_signals` (sinal com embargo, testado por
> `test_roe_signals_embargo_blocks_early_asof`/
> `test_roe_signals_picks_most_recent_eligible_ref_date` — prova que o embargo
> bloqueia leitura antecipada e que a linha mais recente elegível é escolhida,
> não a mais antiga nem uma futura), `backtest.run_h7` (mesmo runner genérico
> `_run_hypothesis` das anteriores, `signal_fn` fecha sobre `conn` porque o
> sinal vem do banco, não da série de preço como as demais), `config.py`
> (`H7_FROZEN_KEYS`/`h7_frozen_config_hash`), `report._BIAS_NOTE["H7"]` (viés
> de retorno só-preço declarado como NÃO quantificado — ao contrário de
> H1/H2/H4/H5/H6/H8, a relação ROE↔yield de dividendo na B3 não foi
> estabelecida nesta rodada, então nenhuma direção é inferida). Testes em
> `tests/test_h7_quality_roe.py` (smoke com dado sintético inserido direto em
> `fundamentals`, golden hash do lacre, hash ignora parâmetro operacional,
> embargo bloqueia leitura antecipada, seleção da linha mais recente elegível)
> — validados manualmente nesta sessão via script ad-hoc reproduzindo os
> asserts (ambiente sandbox sem `pytest` instalado e sem permissão de rede
> para instalar; ver limitações abaixo). Suíte completa **NÃO** executada
> nesta sessão — `python -m pytest tests/ -v` precisa rodar antes de confiar
> nesta mudança em produção.
>
> **NÃO FEITO nesta sessão — bloqueadores reais do ambiente sandbox, não do
> design:**
> 1. **`ingest_dfp_year` NÃO rodou com anos reais.** Este container não tem
>    acesso de rede a `dados.cvm.gov.br`/`bvmf.bmfbovespa.com.br` (egress
>    bloqueado pela política do proxy, confirmado por teste direto) — só o
>    GitHub Releases (wheel do Core) é alcançável daqui. A ingestão real de
>    DFP 2018-2026 exige rodar `ingest_dfp_year` na máquina do operador (mesma
>    onde `stocks.db` canônico vive, `C:\Users\Superleo13\stocks-predictor-work\`),
>    com rede liberada para a CVM.
> 2. **`data/stocks.db` não existe neste checkout** (é gitignored por
>    design, ~256MB, vive só na máquina do operador) — a rodada única real da
>    H7 (`python -c "import backtest; backtest.run_h7(write_report=True)"`,
>    exatamente como H6/H8 foram rodadas) precisa acontecer lá, não aqui.
> 3. **Suíte oficial (`pytest`) não roda neste sandbox** (módulo ausente,
>    instalação via pip bloqueada pela política do ambiente) — validação
>    desta sessão foi manual (script ad-hoc reproduzindo os asserts dos testes
>    novos, ver acima), não a suíte oficial. Precisa reconfirmar com
>    `python -m pytest tests/ -v` na máquina do operador antes do H7 ser
>    considerado pronto para rodar.
>
> **Resumo honesto para o operador:** o código da H7 está pronto e a lógica
> validada manualmente, mas **nenhuma rodada real aconteceu** — sem
> `stocks.db` real e sem rede para a CVM neste ambiente, não há como produzir
> o veredito de fato. Os próximos passos mecânicos, na sua máquina, são:
> (1) `python -m pytest tests/ -v` (confirmar suíte verde com os testes
> novos); (2) `ingest_dfp_year` para 2018-2026 contra o `stocks.db` real
> (rede liberada); (3)
> `python -c "import backtest; backtest.run_h7(write_report=True)"` (rodada
> única, sem repescagem — mesma disciplina de H4/H5/H6/H8). Isso entra como
> N=7 no `trials.json` automaticamente via `trials_gate.apply_dsr` — o
> hurdle de DSR fica mais alto do que qualquer tentativa anterior.

> ## VEREDITO H7 — ENCERRADA: NÃO COMPROVADA (2026-09-04, rodada única, dado real)
>
> Pendências do bloco acima resolvidas na máquina do operador, na ordem: suíte
> pytest confirmada (252 passed pré-existentes + os novos da H7), ingestão real
> da DFP 2018-2026 via `tools/ingest_h7_real.py` (695 linhas gravadas em
> `fundamentals`, `ticker_of` por ano cruzado por CNPJ entre DFP e FCA — ver
> `tools/build_h7_ticker_of.py`), errata de schema em `trials.json` (campo
> órfão `pipeline_fingerprint` em H6/H8 removido, bloqueava qualquer registro
> novo no Core 3.0.0 real — ver entrada de errata acima), reatestado o controle
> positivo do pedágio (`trials_gate.attest`), rodada única via
> `backtest.run_h7(write_report=True)`.
>
> - 1.826 pregões pareados
> - **IC 95% diff-Sharpe (stationary, bloco 21): (−0,2149, +0,4724)** — cruza zero
> - **DSR: 0,5795 < 0,95** (N=7 — primeira hipótese julgada com o denominador
>   completo das 6 anteriores + ela mesma)
> - PSR 0,6325.
> - **Não comprovada. Sem repescagem.**
> - Relatório: `reports/h7_verdict_adhoc.md` (a versionar via `git add -f`,
>   mesmo padrão de H6/H8 — `run_id: n/d` porque a chamada foi ad hoc, sem
>   `db.new_run`).
>
> **Leitura acumulada (7 tentativas, 0 comprovadas):** a única fronteira de
> dado novo desde o congelamento de 2026-09-02 — fator de qualidade (ROE) via
> DFP da CVM — também não sobrevive ao pedágio nesta janela/universo. Com
> H1-H8 esgotadas (preço + agora fundamentos), não resta hipótese pré-registrada
> pendente de execução. `RESEARCH_FREEZE.md`/`STOCKS_CURRENT_STATE.md`
> atualizados de volta a `FROZEN`/`CLOSED` — a mesma `reopen_policy` (6 campos
> preenchidos por humano) agora cobre também a H7.

> **Estado técnico corrente — 2026-09-01:** pacote `stocks_predictor`, Core
> 3.0.x por wheel e nenhuma dependência declarada de Ops. A migração moderna
> prevalece sobre a antiga pendência Core 2.3/Ops 3.1 e sobre caminhos históricos
> `src/*` citados abaixo. Esses blocos permanecem como evidência datada, não como
> instrução operacional atual.

> ## Infra econômica opt-in para hipótese FUTURA (2026-09-01)
>
> Adicionado `stocks_predictor/economic_gate.py`: uma trava prequential que só
> recomenda `REBALANCE` quando o limite conservador da vantagem bruta observada
> em períodos já maturados paga o custo de turnover e um hurdle explícito. Com
> amostra insuficiente ou edge líquido conservador não positivo, recomenda
> `HOLD`. Toda decisão carrega `capital_enabled=False`: é infraestrutura de
> shadow/research, não autorização para operar dinheiro real.
>
> A trava não foi conectada retroativamente ao `walk_forward` congelado e não
> altera H1/H2/H4/H5/H6/H8, seus parâmetros, relatórios ou vereditos. Usá-la em
> uma estratégia requer hipótese nova, pré-registro e janela forward nova. Testes
> cobrem amostra insuficiente, custo+hurdle, causalidade (resultado corrente só
> entra depois da decisão) e entradas inválidas.

> ## Migração de namespace do pacote (2026-08-31)
>
> Autorização explícita do operador para corrigir a colisão cross-repo confirmada
> pela auditoria. O pacote Python genérico `src` foi renomeado para
> `stocks_predictor`; entry point, Hatch, cobertura, Pyright, CI, testes, comandos
> e documentação operacional foram atualizados. Nenhum sinal, parâmetro congelado,
> banco, ledger ou resultado científico foi alterado. Validação pós-migração:
> **242/242 testes verdes** e wheel sem pacote top-level `src`.

> ## Auditoria full-tree de `src/` (2026-08-30) — 3 achados corrigidos, 1 escalado ao humano
>
> Pedido do operador ("roda a auditoria de verdade" / "roda a varredura completa em
> src/"), após um relatório externo genérico (não deste repo, cheio de nomes de
> função inexistentes) ser descartado por não bater com o código real. `/code-review
> high` rodado full-tree (sem diff — árvore de trabalho limpa no commit `00b2a5e`).
>
> **Corrigidos:**
> 1. `paper.py`: `settle_executions` só preenchia `exec_date`/`exec_price` — nenhum
>    código do repositório jamais escrevia `exit_date`/`exit_price`/`cost_paid`/
>    `realized_return_net`/`holding_days`, apesar de `db.py` documentar esse bloco
>    como "preenchida na liquidação" e o M6 existir justamente para produzir esse
>    veredito real. Adicionado `settle_exits`: liquida no PRÓXIMO fim-de-mês do
>    calendário à vista (mesma cadência "segura até o próximo mês" já pré-registrada
>    em `backtest.walk_forward` — reaproveitada, não inventada), abertura D+1,
>    `execution.net_return`/`roundtrip_cost` para custo/retorno líquido, WRITE-ONCE
>    via COALESCE. Ligado em `main.py cmd_paper`. Testes novos em `test_paper.py`
>    (liquidação, write-once, posição ainda aberta fica pendente). **Nota para
>    revisão humana**: a cadência "próximo fim-de-mês" é uma escolha de engenharia
>    (reaproveita a única convenção de holding já pré-registrada no design), não uma
>    decisão de pesquisa nova — mas o cron do paper forward nunca rodou em produção
>    (ver marco M6 abaixo), então vale confirmar antes de religar o cron real.
> 2. `backtest.py` (`walk_forward`, ramo `portfolio_fn`/H4): docstring prometia
>    "retorno diário = média ponderada (re-normalizada pelos presentes no dia)", mas
>    o código nunca fez essa renormalização (o denominador é sempre Σw≈1, fixo).
>    Corrigida a DOCSTRING para bater com o código, não o código para bater com a
>    docstring: renormalizar só pelos "presentes no dia" daria peso extra grátis aos
>    sobreviventes, reintroduzindo o mesmo viés de sobrevivência que o ramo
>    equiponderado (H1/H2) explicitamente evita com a convenção "retorno 0 no dia sem
>    cotação, denominador cheio" (comentário ao lado de `srets`). Mudar o código para
>    bater com a doc teria piorado o H4, não corrigido um bug.
> 3. `rj_pipeline.py` (`build_episodes`): variável local `universe` sombreava o
>    `import universe` usado por `_load_price_series`/outras funções do mesmo
>    arquivo — um `AttributeError` esperando um edit futuro que reusasse
>    `universe.SPOT_MARKET` dentro de `build_episodes`. Renomeada para
>    `approved_universe` (é exatamente o que a variável é: a fila já aprovada,
>    `approved_by IS NOT NULL`).
>
> **Escalado, NÃO corrigido — decisão do humano**: `pyproject.toml` declara
> `predictor-core`/`predictor-ops` como dependências pip/uv (wheels do GitHub
> Releases, `[tool.uv.sources]`), e `tests/conftest.py` ativamente barra o uso do
> `vendor/predictor_core` (exceto via `STOCKS_ALLOW_VENDOR_SHIM=1`). Isso contradiz o
> texto atual de `CLAUDE.md`/`docs/DESIGN.md` ("PROIBIDO instalar o core via pip",
> sem condicional). MAS não é drift acidental: é uma migração deliberada em ~8
> commits (`build: add modern Python project metadata`, `test: stop injecting
> vendored core into test runtime`, `tooling: permitir shim vendor via
> STOCKS_ALLOW_VENDOR_SHIM`, `ci: phase in quality gates...`). Reverter destruiria
> esse trabalho; manter deixa a regra escrita do projeto tecnicamente violada. Regra
> do próprio CLAUDE.md ("dúvida de design não coberta: PARAR e perguntar") — decisão
> real é do operador: (a) atualizar CLAUDE.md/DESIGN.md para refletir a migração para
> wheels pip/uv (com o vendor como fallback/dev), ou (b) reverter a migração e voltar
> o import a vir de `vendor/predictor_core`. **Efeito colateral observado**: neste
> sandbox, sem acesso às wheels reais, `vendor/predictor_core` está desatualizado
> frente à API que os testes já esperam da v2.3 (`PastView.__init__` mudou de
> assinatura; `trials_gate.attest` não devolve mais `pipeline_fingerprint` na versão
> vendorizada) — 4 testes falham só por isso (`test_h2_gate.py`,
> `test_replay.py`×3), pré-existente, não introduzido por esta sessão.

> ## Revisão de código pós-reconstrução do banco (2026-08-28) — 10 achados, todos corrigidos
>
> Pedido do operador ("testa a qualidade dele, acertos e erros") logo após a
> reconstrução do `stocks.db` e o julgamento de H6/H8 (ver entrada abaixo).
> Duas frentes: (1) `/code-review high src/` — revisão multi-agente com
> verificação adversarial; (2) taxa de acerto (hit rate) das 6 hipóteses já
> julgadas sobre o dado real, puramente descritivo (papel de analista §9b,
> não altera nenhum veredito). Achados da frente (1), todos corrigidos nesta
> sessão, suíte revalidada **240/240 verde** (230 + 10 testes de regressão
> novos):
>
> 1. `rj_pipeline.py` (`persist_run`): `UPDATE ... WHERE value IS NOT ?` com
>    parâmetro `None` virava `IS NOT NULL` no SQLite — uma rodada que
>    recomputasse uma família como indisponível apagava com NULL um score
>    válido de rodada anterior, sem trilha em `adjustments`/`quarantine`.
>    Corrigido: score `None` nunca escreve (rodada sem dado não apaga rodada
>    anterior com dado).
> 2. `rj_families.py` (`ownership`): só dispara com
>    `rj_events.event_type == "investidor_5pct"`, mas NENHUM ingestor deste
>    repo produz esse tipo (`ingest_cvm.ingest_ipe_year` só grava
>    `fato_relevante`/`ipe_outro`) — a família sempre voltava 0, uma falsa
>    certeza de "não houve entrada de investidor". Corrigida a fiação em
>    `compute_family_scores`: `ownership` fica `None` (dado indisponível,
>    mesma disciplina de `liquidity`/free_float) até existir um ingestor real.
> 3. `report.py` (`_BIAS_NOTE`): faltavam entradas H6/H8 — o relatório caía
>    silenciosamente na ressalva de viés da H1, errada para a H8 (perna
>    baixa-vol tem viés oposto). Corrigido + notas próprias para H6/H8 +
>    fallback genérico (nunca mais herda nota de outra hipótese) — ver
>    entrada de veredito H6/H8 abaixo para o impacto no DSR da H6.
> 4. `rj_episodes.py`/`rj_families.py`/`rj_families_next.py`: guards
>    estruturais (anti-lookahead; consistência de registry) eram `assert` nu
>    — removível com `-O`/`PYTHONOPTIMIZE`. Trocado por `raise` explícito
>    (mesmo tipo de exceção onde havia teste dependente).
> 5. `adjust.py` (`adjusted_series`, `scan_and_quarantine`): faltava
>    `approved_by IS NOT NULL` nas leituras de `adjustments` — defesa em
>    profundidade (hoje latente, já que o único writer exige aprovação antes
>    de inserir); um ajuste PENDENTE agora nem "explica" o salto na
>    quarentena nem entra na série ajustada.
> 6. `execution.py`/`backtest.py`: a versão NORMALIZADA e correta do custo de
>    turnover (`equal_weight_turnover_cost`) vivia duplicada como função
>    privada em `backtest.py`, enquanto `execution.py` exportava só a versão
>    BRUTA (`calculate_turnover_cost`) sem avisar que não é normalizada —
>    risco de reintroduzir o bug histórico de custo já diagnosticado. Movida
>    para `execution.py` como canônica; `backtest.py` importa (não duplica).
> 7. `universe.py`/`backtest.py`: nada impedia rodar `backtest` sem nunca ter
>    rodado `adjust` — um split real ficaria sem excluir/ajustar, corrompendo
>    o Sharpe em silêncio. Novo guard `adjust.require_scanned` (fail loud se
>    `prices_raw` tem escala de produção e `quarantine`+`adjustments` estão
>    os DOIS vazios), chamado no início de `walk_forward`.
> 8. `report.py`: o limiar de DSR exibido caía para `h2_criteria` quando a
>    seção própria da hipótese faltava no config — divergindo do fallback
>    REAL usado por `trials_gate.apply_dsr` (vazio -> default 0.95). Corrigido
>    para bater exatamente com o que decidiu o veredito.
> 9. `backtest.py`: `run_h2/h4/h5/h6/h8` eram 5 funções quase idênticas
>    copiadas à mão — a mesma duplicação que já causou o bug real do clobber
>    de sharpe da H2 (2026-07-18). Extraído `_run_hypothesis` genérico; cada
>    `run_hN` fica só com o que É específico dela (parâmetros do config,
>    `signal_fn`/`portfolio_fn`).
> 10. `rj_judge.py`/`rj_judge_robust.py`: a convenção de p-valor de permutação
>     `(n_ge+1)/(n_perm+1)` estava implementada 3x independentemente
>     (`permutation_pvalue`, `categorical_family_verdict`,
>     `romano_wolf_stepdown`). Extraído `permutation_pvalue_from_count`
>     (+ `_permutation_test` genérico para os dois testes de família única);
>     `romano_wolf_stepdown` importa a mesma função.
>
> **Frente (2), hit rate** (descritivo, sobre o dado real 2018-2026, não
> altera veredito): taxa de acerto essencialmente de moeda honesta em quase
> tudo (H1 50,8%, H2 50,2%, H4 49,8%, H6 50,2%, H8 51,0%) — consistente com
> "mercado eficiente, nenhuma comprovada". **H5 destoa negativamente** (47,1%
> de acerto, só 39,8% dos meses batendo o benchmark), confirmando o achado de
> anti-sinal já registrado. **H8 tem a melhor taxa (51,0%/55,3%)**, batendo
> com "melhor descritivo do domínio" — mas DSR/IC já reprovaram, então
> continua não comprovada.

> ## Ingestão DFP da CVM (2026-08-27) — dado novo para viabilizar a H7 (fator de qualidade)
>
> Terceira frente do pedido do operador (H6/H8 já pré-registradas acima). A
> H7 (ROE/alavancagem, quintil superior) não pôde ser pré-registrada antes
> porque o dado contábil não existia no banco — `ingest_cvm.py` só cobria
> IPE (fatos relevantes) e FRE (free float). Resolvido: `ingest_cvm.py`
> ganhou `parse_dfp_statement_rows`/`compute_fundamentals`/`ingest_dfp_year`
> (Demonstrações Financeiras Padronizadas, BPA/BPP/DRE consolidados) e
> `db.py` ganhou a migração `0007_fundamentals` (tabela nova, append-only —
> nenhuma migração existente tocada).
>
> **Armadilha de dado registrada** (por isso a implementação, não só o
> anúncio): no plano de contas padronizado da CVM, `CD_CONTA "2" - Passivo
> Total` do BPP **já inclui** o Patrimônio Líquido (é o espelho contábil do
> Ativo Total por identidade — sempre bate 1:1). Um `leverage =
> passivo_total / ativo_total` ingênuo daria sempre ~1.0, um índice inútil.
> `leverage` gravado é `(passivo_total - patrimonio_liquido) / ativo_total`
> — dívida excluindo o PL. Documentado no docstring de `compute_fundamentals`
> pra não repetir o erro.
>
> **Limitação conhecida, não escondida**: contas de ROE/alavancagem são
> casadas por `CD_CONTA` (BPA/BPP) e por palavra-chave na descrição (DRE,
> onde o código do lucro líquido varia mais). Companhias financeiras
> (bancos/seguradoras) usam um plano de contas diferente do não-financeiro e
> podem não casar — ficam de fora silenciosamente nesta 1ª versão (não é
> erro, é escopo: `ingest_dfp_year` só grava o que resolveu sem
> ambiguidade). `ref_date` (fim do exercício) é usado como `known_at`
> conservador — na prática o dado é PUBLICADO bem depois do fechamento; a
> H7, quando pré-registrada, decide se soma um embargo de divulgação.
>
> **PENDENTE — H7 ainda NÃO pré-registrada.** Isso é só o dado. Próximo
> passo (não feito aqui, decisão de protocolo separada): definir o sinal
> exato (ROE isolado? ROE E alavancagem baixa, filtro duplo como H8?
> quintil de quê sobre qual universo?) e travar em `config.yaml`/
> `config.py`/HANDOFF ANTES de rodar — mesma disciplina de H6/H8. Também
> falta rodar `ingest_dfp_year` com anos reais (2018-2026) contra o
> `stocks.db` real e o `ticker_of` de verdade — testado aqui só com dado
> sintético, sem rede (este ambiente não baixa da CVM).
>
> Testes: `tests/test_rj_ingest.py` (parsing DFP + `compute_fundamentals` +
> `ingest_dfp_year` end-to-end, dado sintético). Validado manualmente nesta
> sessão com um stub de `predictor_core.infra` (sem depender do vendor) —
> ver `python -m pytest tests/ -v` para a suíte oficial.

> ## H6 e H8 ABERTAS — PRÉ-REGISTRO (2026-08-27, ANTES de qualquer rodada)
>
> Decisão humana explícita (pedido do operador de tentar achar uma estratégia
> com sucesso real, após H1/H2/H4/H5 fecharem "ruído"). Duas hipóteses NOVAS,
> formalizadas e travadas em `config.yaml`/`config.py` ANTES de qualquer
> código de sinal ter rodado — mesma disciplina de H4/H5. Uma terceira
> candidata (fator de qualidade — ROE/alavancagem) foi DESCARTADA desta
> rodada: exige ingestão nova de demonstrações financeiras da CVM (DFP/ITR),
> que não existe hoje (`ingest_cvm.py` só cobre IPE/FRE) — escopo de
> engenharia de dados separado, não uma hipótese pronta para travar agora.
>
> **H6 — momentum 6-1** (`config.yaml` `h6_*`, `config.h6_frozen_config_hash`
> = `7ff75a9ade2ee9fb`): mesma maquinaria da H1 (universo/custos/pareamento/
> pedágio, quintil superior, equiponderado), sinal com janela mais curta —
> 126 pregões (~6 meses), skip 21. Racional: H1 (12-1) fracassou, mas
> mercados menos líquidos/eficientes que os desenvolvidos às vezes mostram
> momentum mais forte em janelas mais curtas (incorporação de informação mais
> lenta) — hipótese distinta, não o mesmo teste com outro número. Critério:
> IC95% diff-Sharpe > 0 E DSR >= 0.95 (N=6 tentativas no registro).
>
> **H8 — filtro duplo momentum ∩ baixa vol** (`config.yaml` `h8_*`,
> `config.h8_frozen_config_hash` = `8bad7034233189c0`): top 40% do universo
> por momentum 12-1 (mesma régua da H1), depois a metade de menor vol
> realizada 252d (mesma régua da H2) DENTRO desse subconjunto — não do
> universo inteiro. Equiponderado, long-only. Racional: H1 (momentum
> isolado) e H2 (baixa vol isolada) fracassaram isoladas, mas a literatura
> mostra que a interseção às vezes filtra o lado mais arriscado do momentum
> e sobrevive onde nenhuma das duas isoladas sobrevive — hipótese distinta
> de ambas, não combinação escolhida depois de ver resultado. Critério:
> IC95% diff-Sharpe > 0 E DSR >= 0.95 (N=6 tentativas no registro).
>
> **Implementação:** `backtest.run_h6`, `backtest.run_h8`,
> `portfolio.momentum_lowvol_double_filter` (nova função — filtro em duas
> etapas, interseção explícita de tickers com AMBOS os sinais antes de
> rankear). Testes de smoke (dado sintético) + golden hash em
> `tests/test_h6_momentum6.py`/`tests/test_h8_double_filter.py`.
>
> **RESOLVIDO (2026-08-27/28) — banco real reconstruído, rodada única executada.**
> O `data/stocks.db` anterior (250MB, 2016-2026) não existia mais nesta máquina;
> reconstruído do zero nesta sessão a partir dos COTAHIST anuais oficiais da B3
> (`bvmf.bmfbovespa.com.br/InstDados/SerHist/COTAHIST_A{ano}.ZIP`, 2016-2026,
> download automatizado via `ingest_cotahist.download_cotahist` — rede não
> bloqueou desta vez) + `main.py ingest` por ano: **1.149.872 linhas em
> `prices_raw`** (mesma ordem de grandeza do banco anterior). Detector de saltos
> (`main.py adjust`) achou 2.227 saltos sem ajuste registrado; `splits-review`
> exportou 440 candidatos com proporção redonda plausível, dos quais **39
> tickers (46 eventos)** de fato entraram no universo top-60 de liquidez em
> algum momento 2018-2026 (mesmo filtro de relevância usado na adjudicação da
> H1) — os ~394 restantes ficam em quarentena conservadora (sem liquidez
> relevante, decisão formalizada, não silenciosa).
>
> **Adjudicação humana dos 46 candidatos relevantes** (§9b/§11: IA pesquisou via
> WebSearch contra fonte financeira nomeada e propôs `source` por linha; humano
> aprovou explicitamente, `approved_by=Superleo13`): **43 confirmados** (39
> desdobramentos/grupamentos formais + NATU3/PSSA3, bonificações com efeito de
> preço idêntico a split, mesmo tratamento do precedente da H1) gravados em
> `adjustments` via `splits-import`. **3 excluídos por não serem splits reais**
> (permanecem em quarentena): **GOLL4** 2025-06-09 (não foi split — troca de
> ticker GOLL4→GOLL54 + diluição massiva pós-recuperação judicial, ação subiu
> >1800% no debut, direção oposta a um split); **PCAR3** 2023-08-23 (não foi
> split — spin-off do Grupo Éxito via BDR, queda ~20% incompatível com a queda
> ~67% que um split 1:3 exigiria); **RAIZ4** 2026-07-31 (nenhuma operação
> corporativa encontrada — provável ruído de dado, queda orgânica por crise de
> dívida/RJ extrajudicial). Suíte revalidada pós-adjudicação: **230/230 verde**.
>
> **Comandos executados exatamente como travado no pré-registro** (nenhum
> parâmetro `[H6-FROZEN]`/`[H8-FROZEN]` tocado):
> ```powershell
> python -c "import backtest; backtest.run_h6(write_report=True)"
> python -c "import backtest; backtest.run_h8(write_report=True)"
> ```
> Nota de gap, registrada por transparência (não corrigida retroativamente —
> mesma disciplina do item 2 da errata de 2026-07-28): a chamada ad hoc não
> passou `run_id` (não houve `db.new_run`), então os relatórios saem como
> `reports/h6_verdict_adhoc.md`/`h8_verdict_adhoc.md` com `run_id: n/d` em vez
> do padrão `h#_verdict_<run_id>.md` das hipóteses anteriores. O bootstrap é
> determinístico (seed=42 fixa em `config.yaml`), então a rodada é
> reproduzível bit-a-bit.
>
> **Errata (2026-08-28, mesmo dia — revisão de código pós-veredito, achados
> aplicados):** revisão de código encontrou e corrigiu, entre outros, dois bugs
> que tocam diretamente estes dois relatórios (nenhum mexe em `[H6-FROZEN]`/
> `[H8-FROZEN]` nem inverte veredito nenhum):
> 1. `report.py`: `_BIAS_NOTE` só tinha entradas H1/H2/H4/H5 — o relatório da
>    H6/H8 imprimia silenciosamente a ressalva de viés da H1 (momentum puro),
>    errada para a H8 (perna baixa-vol tem viés na direção OPOSTA). Também o
>    texto herdado do template ("veredito real exige COTAHIST real — sintético
>    só valida a máquina") tinha ficado obsoleto (já rodou com dado real).
>    Corrigido; relatórios REGERADOS (mesmo `seed=42`, números idênticos) para
>    carregar o texto certo.
> 2. **A H6 tinha sido julgada a primeira vez com N=5 no DSR**, não N=6 como o
>    próprio pré-registro da H6 fixa ("N=6 tentativas no registro", igual à
>    H8) — a chamada ad hoc rodou H6 ANTES de H8 existir no `trials.json`,
>    então o denominador do DSR (todas as tentativas do registro NO MOMENTO do
>    cálculo) ficou incompleto. Ao regerar o relatório (depois de H8 já
>    registrada), a H6 saiu corretamente com N=6. **PSR, IC e sharpe realizado
>    da H6 são idênticos** (o sinal/carteira/custo não mudaram) — só o DSR e o
>    E[max SR] mudam porque o denominador agora tem a tentativa que faltava.
>    Não é reabertura de hipótese nem ajuste de parâmetro: é a correção de um
>    artefato de ORDEM de execução no registro de tentativas. **Não inverte
>    veredito**: DSR ficou ainda MENOR (0,4565 < 0,4828), mais longe do
>    limiar, não mais perto.
>
> ### VEREDITO H6 — ENCERRADA: NÃO COMPROVADA (2026-08-28, rodada única)
>
> - 2.131 pregões pareados
> - **IC 95% diff-Sharpe (stationary, bloco 21): (−0,3526, +0,3256)** — cruza zero
> - **DSR: 0,4565 < 0,95** (N=6; E[max SR|N=6] = 0,0137 por-período — ver
>   errata de correção do N acima)
> - PSR 0,4898. Descritivo: Sharpe anual. 0,1802 vs 0,1891 (benchmark
>   levemente superior); Sortino 0,2414 vs 0,2570; retorno total 11,03% vs
>   14,51%; max drawdown 49,65% vs 48,26%. Momentum 6-1 não supera o
>   buy-and-hold nem no descritivo nesta janela.
> - **Não comprovada. Sem repescagem.**
> - Relatório: [`reports/h6_verdict_adhoc.md`](reports/h6_verdict_adhoc.md)
>   (versionado via `git add -f`); `trials.json` com sharpe realizado 0,011356
>   por-período.
>
> ### VEREDITO H8 — ENCERRADA: NÃO COMPROVADA (2026-08-28, rodada única)
>
> - 2.131 pregões pareados
> - **IC 95% diff-Sharpe (stationary, bloco 21): (−0,1508, +0,4138)** — cruza zero
> - **DSR: 0,6050 < 0,95** (N=6; E[max SR|N=6] = 0,0137 por-período)
> - PSR 0,6366. Descritivo: o melhor do domínio até aqui — Sharpe anual. 0,3110
>   vs 0,1891; Sortino 0,4188 vs 0,2570; retorno total 44,42% vs 14,51%; max
>   drawdown 44,18% vs 48,26% (melhor que o benchmark nas quatro métricas). Mesmo
>   assim, a régua estatística (IC + DSR) não deixa promover a um edge — a
>   amostra (2018-2026, mesma janela reutilizada 6x) não tem poder para
>   distinguir isso de sorte.
> - **Não comprovada. Sem repescagem.**
> - Relatório: [`reports/h8_verdict_adhoc.md`](reports/h8_verdict_adhoc.md)
>   (versionado via `git add -f`); `trials.json` com sharpe realizado 0,019597
>   por-período.
>
> **Leitura acumulada (6 tentativas, 0 comprovadas):** H1/H6 (momentum, duas
> janelas) e H2/H4/H5/H8 (vol/sizing/reversão/filtro-duplo) — nenhuma sobreviveu
> à régua nesta janela de 8,5 anos de dado diário da B3. H8 é o resultado
> descritivo mais forte do domínio (bate o benchmark nas 4 métricas) e AINDA
> ASSIM falha DSR por margem grande — o registro honesto de tentativas (N=6)
> está fazendo exatamente o trabalho para o qual foi criado: impedir que um
> resultado bonito, mas indistinguível de sorte com 8 tentativas no denominador,
> vire "comprovado". Com dados só-preço e a maquinaria momentum/vol/sizing
> esgotada nesta B3, a próxima fronteira honesta do domínio é FONTE NOVA — a
> H7 (fundamentos ROE/alavancagem, dado DFP da CVM já ingerido, ver entrada
> acima) segue como candidata não pré-registrada, decisão do operador.

> ## Errata de auditoria (2026-08-27) — bugs corrigidos no código, vereditos antigos INTOCADOS
>
> Auditoria de bugs/lógica/matemática (via IA, revisão cruzada e verificação
> manual linha a linha antes de qualquer correção). **Nenhum `trials.json`,
> `reports/*` ou número congelado de H1/H2/H4/H5 foi alterado** — são
> encerramento formal (2026-07-26) e ficam como registro histórico. As
> correções abaixo valem para rodadas FUTURAS; reabrir H1-H5 continua
> exigindo decisão humana explícita + pré-registro (regra inalterada).
>
> Domínio de ações (motor compartilhado por H1/H2/H4/H5):
> 1. `backtest.py` (`walk_forward`): custo de turnover só era cobrado quando
>    `j==0` dentro do loop de pregões do período — se o 1º pregão não tivesse
>    retorno válido (`continue`), o custo do rebalanceamento inteiro sumia
>    silenciosamente (inflava o retorno líquido). Corrigido com flag
>    `cost_pending`, cobrado no 1º par de retornos efetivamente registrado.
> 2. `backtest.py` (`walk_forward`): ativo sem retorno no dia (suspensão/
>    iliquidez) era descartado da média da carteira, redistribuindo peso
>    grátis para os sobreviventes (viés de sobrevivência silencioso).
>    Corrigido: retorno tratado como 0 no dia sem cotação, denominador fixo
>    em `len(port)`/pesos declarados.
> 3. `adjust.py` (`scan_and_quarantine`, `adjusted_series`,
>    `list_split_candidates`): leituras de `prices_raw` não filtravam
>    `market_type` — defesa que `universe.py`/`paper.py` já tinham e
>    documentavam, mas não estava replicada aqui. Corrigido: mesmo filtro
>    `market_type=SPOT_MARKET` nas três queries.
>
> Domínio RJ (M0 — nenhum dado real ainda, nada julgado, correções livres):
> 4. `rj_coda.py` (`clr_matrix`): colunas em `dropped_cols` (sem nenhum valor
>    positivo em toda a matriz) não eram excluídas antes do `clr` — uma
>    única coluna morta colapsava a matriz inteira para `None`
>    (`rows_failed` = 100%). Corrigido: colunas dropped excluídas antes do CLR.
> 5. `rj_judge_robust.py` (`romano_wolf_stepdown`): `same_units` comparava
>    `(ticker, valor)` entre famílias — como o valor difere por construção,
>    a permutação CONJUNTA (o ponto central do método) quase nunca era
>    exercitada, mesmo com as mesmas empresas em todas as famílias. Corrigido
>    para comparar só identidade/ordem dos tickers.
> 6. `rj_pipeline.py` (`_load_volumes`): mesma falta de filtro `market_type`
>    do item 3, agora também aqui.
> 7. `rj_families.py` (`drawdown`): sem checar `pre_rj_high_date < trough_date`
>    — erro de dado do chamador (máxima "pré-RJ" no/após o fundo) produzia
>    drawdown 0% em vez de `None`. Corrigido com a guarda `i_h >= i_t`.
> 8. `config_rj.yaml` (`info_trigger.metric`): rótulo dizia "10p" (pregões),
>    mas a implementação (`rj_families.info_trigger`) sempre usou dias
>    CORRIDOS (já documentado no docstring do código — só o rótulo do YAML
>    divergia). Rótulo corrigido para bater com o código.
> 9. `rj_outcomes.py` (`market_adjusted_rally`): excesso de retorno sobre o
>    índice calculado por subtração aritmética (`stock_ret - idx_ret`) em vez
>    de geométrica — distorce magnitude em rallies grandes (regime deste
>    projeto). Corrigido para `(1+stock_ret)/(1+idx_ret)-1`. Outcome é
>    AUXILIAR (nunca alimentou veredito primário/secundário).
> 10. `factor.py` (`momentum_12_1`): guarda `i_start<0` não cobria `i_end<0`
>     (só ocorre se `skip>lookback`, config que nenhuma hipótese registrada
>     usa hoje) — indexação negativa do Python leria preço fora da janela.
>     Guarda defensiva adicionada.
>
> **Errata (2026-08-27, revisão): `censoring_horizon_trading_days` NÃO é
> parâmetro morto — é regra de protocolo real, ainda não implementada.**
> Correção da entrada anterior desta mesma errata, que classificou o
> parâmetro como "config morto"/lookahead: `docs/RJ_DESIGN.md` §5 (o
> documento canônico — manda em caso de conflito, `CLAUDE.md`) DECLARA a
> censura por EMPRESA (`censoring_horizon_trading_days`, a partir do
> pedido de RJ) como regra de protocolo pré-registrada. O que existe hoje
> em `rj_episodes.classify_episode` é uma censura por EPISÓDIO (a partir
> do FUNDO, `rally.primary/secondary_window_trading_days`) — implementada
> corretamente, mas é uma camada DIFERENTE, não um substituto. Lacuna real:
> empresa sem nenhum candidato a fundo ainda vira `excluded` em
> `rj_pipeline.build_episodes` (fora do denominador do estudo) em vez de
> `censored`/controle definitivo — viés de denominador já registrado
> independentemente em `docs/audit/kimi_2026-08-24/RELATORIO_AUDITORIA_RJ.md`.
> Não implementei: definir o grupo controle de um estudo ainda não julgado
> é decisão de protocolo, não bug de código — cabe a quem decide o
> pré-registro do RJ (regra `CLAUDE.md`: "em dúvida de design não coberta,
> parar e perguntar"), não a esta sessão inferir sozinha a partir de um
> comentário. `censoring_horizon_trading_days` foi mantido no
> `config_rj.yaml` com nota explicando o gap; nada foi codificado.

> **Atualização de implementação (2026-08-31): lacuna fechada.**
> `rj_pipeline.build_episodes` agora registra empresas sem candidato em
> `rj_company_observations`: `censored` antes do horizonte e
> `no_candidate_control` ao atingi-lo. A migração `0008_rj_company_censoring`,
> persistência, relatório e teste de regressão foram adicionados; nenhum fundo
> ou trough é inferido para completar o denominador.
>
> Suíte de testes não pôde ser executada nesta sessão (ambiente sem
> `predictor_core`/`predictor_ops` vendorizados) — correções verificadas
> por scripts isolados ad-hoc reproduzindo o comportamento antes/depois
> (ver histórico da sessão), não pela suíte oficial. **Rodar
> `python -m pytest tests/ -v` antes de confiar nestas mudanças em produção.**

> ## NOVO DOMÍNIO ADICIONADO (2026-08-23): predictor-rj (event study, RJ na B3)
>
> Módulo novo, INDEPENDENTE do domínio de momentum/fatores abaixo — reaproveita
> `prices_raw`/`adjustments`/`quarantine` (mesmo COTAHIST já ingerido, mesmo
> `quote_factor`) e o `vendor/predictor_core` (bootstrap, infra), mas não toca
> em nenhuma tabela, sinal ou veredito do domínio de ações. Estuda rallies
> ≥50% em ações de empresas em recuperação judicial — estrutura evento-driven
> (fundo→outcome por empresa), não ranking cross-sectional recorrente.
>
> **Arquivos:** `src/rj_episodes.py` (detecção de fundo, ex-post vs.
> point-in-time), `src/rj_families.py` (8 famílias preditivas + 1 descritiva,
> condensando 114 hipóteses de um relatório de Fase 1), `src/rj_judge.py`
> (permutação + bootstrap cluster + FDR de Benjamini-Hochberg — não DSR, que é
> Sharpe-específico). Config em `config_rj.yaml` (namespace separado de
> `config.yaml` — não compartilha chaves). Documento canônico:
> [docs/RJ_DESIGN.md](docs/RJ_DESIGN.md). Schema novo via migração
> `0004_rj_domain_schema` (append-only, nenhuma tabela existente alterada).
>
> **Estado:** M0 — núcleo validado em dados SINTÉTICOS
> (`tests/test_rj_smoke_synthetic.py` + `tests/test_rj_power_gate.py`, 12/12
> verde). Suíte completa do repo: **156/156 verde** (144 do domínio de ações,
> intocado + 12 novos). Nenhum dado real de RJ foi coletado — `rj_universe`
> está vazia. Pendências: universo completo de RJ da B3 (decisão de fonte),
> port do parser COTAHIST/`adjust.py` para popular `rj_episodes` a partir de
> preço real, e atestado formal de power gate antes de qualquer H1 real. Ver
> `docs/RJ_DESIGN.md` §10 para a lista completa do que NÃO fazer.
>
> Passou por 3 rodadas de revisão externa antes de integrar aqui (lookahead na
> escolha do fundo corrigido, features contemporâneas separadas de
> antecedentes, `rj_stage` tratado como categórico não ordinal, seleção de
> episódio primário fixada a priori — nunca por outcome).

> ## STATUS: FECHADO (2026-07-26) — 4 hipóteses, 4 ruído, nenhuma pendente
>
> Fechamento formal. O bloco de reabertura abaixo continua válido como
> histórico, mas **a reabertura de 2026-07-18 cumpriu seu propósito e
> terminou**: H4 e H5 foram pré-registradas antes de qualquer código, rodadas
> em rodada única e ambas voltaram **não comprovadas**. Não resta hipótese
> pendente de execução.
>
> | Hipótese | Veredito | Sharpe por-período |
> |---|---|---|
> | `h1-momentum-12-1` | **RUÍDO** | +0,010029 |
> | `h2-lowvol-252` | **RUÍDO** | +0,013363 |
> | `h4-invvol-sizing-252` | **RUÍDO** | +0,011372 |
> | `h5-strev-21` | **RUÍDO / anti-sinal** | **−0,011367** |
>
> Quatro fatores clássicos de equities — momentum 12-1, baixa volatilidade,
> sizing por 1/vol e reversão de 21 dias — todos com efeito na terceira casa
> decimal, e o mais promissor da literatura (reversão de curto prazo) saindo
> **negativo** no universo B3 testado. Quatro tentativas, quatro nadas.
>
> **Condição para reabrir, inalterada:** decisão humana explícita + hipótese
> formalizada ANTES de qualquer código. O vendor segue congelado em
> `1.3.0-ga-20260711` por regra deste projeto, e o projeto segue no set
> `PARKED` do `sync_core.py` — onde, para ele, `PARKED` significa "vendor
> congelado por decisão do projeto", não "projeto inativo".
>
> Armadilha registrada para quem inventariar este projeto: **`trials.json`
> fica na RAIZ**, não em `data/`. O inventário de 2026-07-26 que olhava só
> `data/` perdeu estas 4 hipóteses e reportou 38 em vez de 42.
>
> Suíte revalidada em 2026-07-26: **144 verdes**, vendor intocado.

---

> ## Histórico: REABERTO PARA H4 (2026-07-18) — vendor segue congelado
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
> Suíte completa revalidada em 2026-07-20: **144 verdes**. O vendor
> permanece congelado; nenhum arquivo do vendor foi tocado.

---

## Errata de auditoria (2026-07-28) — encerramento factual, somente-leitura

Auditoria de encerramento sobre o estado congelado, posterior ao fechamento
formal de 2026-07-26. **Nenhum número, veredito, parâmetro congelado ou
artefato de rodada foi alterado.** Achados registrados:

1. **Relatório da H1 não estava versionado** (corrigido nesta sessão). O link
   para `reports/h1_verdict_20260712T091903477689-41cc24.md` era um link
   QUEBRADO no repositório: `.gitignore` ignora `reports/*`, e apenas H2/H4/H5
   haviam sido versionados via `git add -f`. O arquivo existia só como untracked
   no checkout principal e **não é regenerável** (o `stocks.db` de 250 MB e os
   ZIPs COTAHIST de origem não estão no git). Versionado agora: cópia fiel do
   artefato gerado pela rodada, conteúdo inalterado (EOL normalizado para LF pelo
   `.gitattributes`, como nos relatórios de H2/H4/H5). A ciência nunca esteve em
   risco — os números completos já viviam neste HANDOFF e no `trials.json`, ambos
   versionados e mutuamente coerentes — mas o artefato agora tem paridade de
   auditoria com as outras três hipóteses.

2. **`backtest.purge_embargo_months: 1` está registrado mas NÃO implementado.**
   O parâmetro consta como `[H1-FROZEN]` no `config.yaml` e nos `params` das 4
   trials do `trials.json`; `src/backtest.py` (docstring, "Simplificações desta
   passada") declara que o purge/embargo formal ficou para a evolução do M5. O
   registry portanto descreve um controle que o código não aplicou. **Não inverte
   veredito nenhum**: a ausência de purge/embargo só pode vazar informação A FAVOR
   da estratégia, e as quatro reprovaram assim mesmo. Corrigir isso = novo
   pré-registro, nova rodada, N+1 — não é errata de texto.

3. **Ressalva obsoleta dentro do relatório da H1.** O `.md` diz "Custo roundtrip
   aplicado no rebalance"; a rodada `20260712T091903477689-41cc24` (code_version
   `e6f1334`) **já usava custo por turnover real** — `execution.calculate_turnover_cost`
   está presente naquele commit (verificado por `git show`). A frase era template
   antigo do `report.py`, corrigido só depois em `3b5e8b1`. **O artefato da rodada
   NÃO foi editado** (é registro histórico); esta errata é o apontamento.

4. **Tabela de Marcos: linhas M1/M2 são histórico, não pendência.** "Falta p/ H1:
   anos 2016-2023" e "Falta p/ H1: operador adjudicar os ~57 splits" foram
   ATENDIDAS e o próprio arquivo registra isso acima: banco cobre 2016-01-04 →
   2026-07-03 (1.137.456 linhas, 1.783 tickers) e 15 splits de maior liquidez
   foram adjudicados com aprovação humana nominal. Não reabrir.

5. **Não são critérios do pré-registro** — e portanto NÃO bloqueiam o
   encerramento: robustez de execução a 3 preços e purge/embargo formal constam
   como "evolução do M5". O pré-registro §9 da H1 fixa **um único** critério: IC
   95% da diferença de Sharpe excluindo zero. Ele foi aplicado e reprovou.

6. **`ECOSYSTEM_HANDOFF.md`, referenciado acima, nunca existiu neste
   repositório** (`git log --all -- ECOSYSTEM_HANDOFF.md` → vazio). Vive fora
   deste workspace; não verificável aqui.

**Provenance da H1 confirmada contra o banco** (leitura read-only da tabela
`runs`): `run_id 20260712T091903477689-41cc24`, `config_hash 41cc2495292cdfd3`,
`code_version e6f1334`, `started_at 2026-07-12 09:19:03`, com os `params_json`
congelados batendo com o `config.yaml`. Registry, relatório e HANDOFF são
numericamente idênticos. Classificação de encerramento: **H1 = NO-GO confirmado
(IC cruza zero — falha em rejeitar a nula, não refutação); H2/H4/H5 registradas
no `trials.json` e encerradas.** Suíte 144/144 verde, working tree limpa.

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

### VEREDITO H5 — ENCERRADA: NÃO COMPROVADA, com IC INTEIRAMENTE NEGATIVO (2026-07-18, rodada única)

Trilha na ordem pré-registrada: pré-registro commitado (`384ffda`) → controle
positivo re-atestado (2026-07-18T20:26:27Z) → trial `h5-strev-21` (N=4) → UMA
rodada.

- **run_id:** `20260718T202628182793-427444` — 2.092 pregões pareados
- **(i) IC 95% diff-Sharpe (stationary, bloco 21): (−0,6406, −0,1009)** — não
  contém zero, mas do lado ERRADO: a estratégia é significativamente PIOR que
  o benchmark. Primeiro resultado do domínio em que a régua fecha uma direção
  — e é contra.
- **(ii) DSR: 0,1274 < 0,95** (N=4; E[max SR|N=4] = 0,0134 por-período).
- PSR 0,1607. Descritivo brutal: Sharpe anual. **−0,18** vs 0,16; retorno
  total **−59,03%** vs +8,03%; maxDD 68,20% vs 48,03%. Comprar os perdedores
  do mês no top-60 da B3, líquido de custo por turnover real, DESTRÓI capital
  — o turnover intrínseco (declarado como adversário no pré-registro) e a
  continuação de momentum no curto prazo enterram a reversão implementável.
- **Não comprovada (e na prática refutada na direção oposta). Sem repescagem.**
- Relatório: [`reports/h5_verdict_20260718T202628182793-427444.md`](reports/h5_verdict_20260718T202628182793-427444.md)
  (versionado); `trials.json` com sharpe realizado −0,011367 por-período.

**Suíte pós-marco: 140/140 verde** (135 + 5 da H5).

### Correção pós-revisão (2026-07-18, mesma noite) — bug de clobber no registry

Revisão de código da sessão achou um bug REAL de governança:
`register_baseline_trials` re-registrava a H2 com `sharpe=None`, e o update
sobrescrevia o sharpe REALIZADO da rodada única — os comandos `backtest-h4` e
`backtest-h5` zeraram o valor da H2 no `trials.json`. Consequências, medidas e
registradas:

1. **DSRs de H4/H5 foram computados com a variância entre tentativas SEM o
   sharpe da H2** — sr0 da H4 saiu ~0,0009 (correto ~0,0014) e o da H5 0,0134
   (correto ~0,0122). **Nenhum veredito muda**: ambos reprovaram o DSR por
   margem enorme (0,68 e 0,13 vs 0,95) e o critério (i) do IC já reprovava os
   dois independentemente. Os números impressos nos relatórios de H4/H5 ficam
   como estão (artefatos da rodada, com esta errata apontando o desvio).
2. **Fix**: guarda anti-clobber em `trials_gate.register_hypothesis`
   (re-registro com sharpe=None preserva sharpe/notes realizados) + teste de
   regressão. `trials.json` reparado via API: sharpe da H2 restaurado a
   0,013363 com nota de correção na própria trial.
3. **Errata deste HANDOFF**: os sharpes registrados de H4/H5 haviam sido
   anotados de memória (0,011478 / −0,011225); os valores REAIS do arquivo são
   **0,011372 / −0,011367** — corrigidos acima.

### Revisão profunda do src/ (2026-07-18, 2ª passada — módulos M1–M6 inteiros)

Leitura linha a linha de adjust/universe/paper/db/cotahist/analyst/ingest:

1. **`paper.settle_executions` blindado** (era a ÚNICA query de leitura sem as
   defesas do Red Team): agora filtra mercado à vista (`universe.SPOT_MARKET`)
   e dedupa re-ingest (`GROUP BY date`) — um banco com `avista_only=False` não
   pode mais liquidar paper a preço de opção; + cache de série por ticker (era
   uma query por decisão pendente). Teste de regressão determinístico
   (`test_settle_ignores_non_spot_rows`). Seguro: paper nunca rodou em produção
   (`decisions`=0) e não alimenta veredito nenhum.
2. **`quote_factor` nunca aplicado ao preço** — registrado acima na lista de
   "Conhecidos, NÃO corrigidos" com análise de impacto (zero nos vereditos;
   decisão de correção é do operador).
3. Sem outros defeitos materiais: adjust/universe já carregam as defesas das
   revisões anteriores (GROUP BY, resolved_at, janela por calendário); analyst
   segue §9b (só SELECT); cotahist falha alto em linha corrompida (estilo do
   projeto).

**Leitura acumulada (4 tentativas, 0 comprovadas, 1 anti-sinal):** H1 momentum
~empate; H2/H4 (tilts de baixa vol) melhores no descritivo sem significância;
H5 reversão significativamente PIOR. O anti-sinal da H5 é informação real: se
perdedores de 21d underperformam com significância, isso é evidência de
CONTINUAÇÃO de curto prazo neste universo — nota consultiva para ideação
futura (qualquer uso disso = nova hipótese, novo pré-registro, N+1; o lado
comprado dela já foi ~testado na H1 e não passou; o lado vendável esbarra no
custo de aluguel do mapa §10-H5). Com dados só-preço, o baralho local está
jogado; a próxima fronteira honesta é FONTE NOVA (fundamentos/proventos) —
decisão de dependência do operador.

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
  (versionado via `git add -f`); `trials.json` com sharpe realizado 0,011372
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
  explícito e o banco atual foi carregado filtrado);
- ~~`quote_factor` parseado mas nunca aplicado ao preço~~ — **RESOLVIDO
  2026-07-18 por decisão do operador ("corrige o quote_factor na leitura")**:
  divisão por FATCOT aplicada na CAMADA DE LEITURA (`db.price_expr`; consumido
  por `adjust.scan_and_quarantine`/`adjusted_series`/`list_split_candidates` e
  `paper.settle_executions`); `prices_raw` permanece o espelho intocável do
  arquivo. Impacto quantificado no banco real ANTES da correção: 626 linhas / 9
  tickers com fator ≠1 (de 1,14M/1783), 4 tickers com MUDANÇA de fator na
  série, **zero deles em qualquer universe_snapshot** → vereditos H1–H5
  inalterados (produzidos pré-correção, code_version por run; a invariância de
  razão intra-ticker já os protegia). Efeito prático daqui em diante: troca de
  lote de cotação deixa de virar salto falso na quarentena, e o paper liquida
  por AÇÃO. Testes: `test_quote_factor.py`.

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
| `pyyaml` | APROVADO (portão, 2026-08-24) | `config_rj.yaml` usa 3 níveis de aninhamento (`families: → <familia>: → metric/direction_expected`), fora do subconjunto plano do mini-parser de `src/config.py`. As alternativas foram achatar o config do RJ ou estender o mini-parser — esta última exigiria alterar `tests/test_config.py`, que asserta a rejeição de 3 níveis como fronteira de design. Operador escolheu a dependência. Declarada em `requirements.txt`; o CI já a instala. O domínio de ações continua no mini-parser stdlib — `src/config.py` NÃO passa a usar pyyaml. |

---

## Restrições invioláveis (resumo operacional)

- Python 3.13 global. Sem venv.
- Separar download (rede limpa, cron) de processamento (offline).
- `prices_raw` é append-only e imutável.
- Ledger `decisions`: parte EVAL imutável; parte RISK write-once via COALESCE.
- IA (analista) NUNCA escreve no banco, NUNCA resolve quarentena.
- Nenhum lookahead: exec_ts > signal_ts em toda linha do ledger (teste automatizado obrigatório no M4).
- Parâmetros H1-FROZEN não se tocam após qualquer rodada de resultado.

---

## Congelamento científico (2026-09-02)

Pesquisa ativa de fatores **encerrada**. `stocks-predictor` passa a ser
`FROZEN_RESEARCH_ASSET + REUSABLE_QUANT_COMPONENTS + SCIENTIFIC_CASE_STUDY`.
Decisões completas, evidence registry, component inventory e case studies em
[RESEARCH_FREEZE.md](RESEARCH_FREEZE.md). Resumo:

- Nenhuma família de fatores (momentum 12-1/6-1, low-vol, vol-target, reversão 21d,
  interseção) pode ser reaberta sem os 6 campos exigidos em `reopen_policy` do manifesto.
- `purge_embargo_months` [H1-FROZEN] permanece declarado no config mas **nunca foi
  consumido pelo backtest** — decisão: `DOCUMENTED_HISTORICAL_LIMITATION` (não implementar
  retroativamente, não remover parâmetro frozen). Vereditos H1-H8 não têm proteção formal
  de purge/embargo.
- `vendor/predictor_core/` (congelado em 1.3.0-ga) resolvido como `ARCHIVE_FOR_REPRODUCTION`
  — nenhum caminho de runtime o usa (guard já ativo em `tests/conftest.py`); único
  consumidor é `poc_leak.py`, classificado `HISTORICAL_POC / NOT_REPRODUCIBLE_AGAINST_CORE_3_0`.
- Linha RJ: `ST_RJ_STATE = ARCHIVED` — zero dados reais coletados, protocolo preservado,
  sem trabalho ativo/ingestão nova autorizada.
- `trials.json` migrado de forma não-destrutiva/idempotente para o schema prospectivo
  canônico em `trials_v2.json` (`tools/migrate_trials_schema.py`); campos sem informação
  registrada usam `"UNKNOWN"` (seed, dataset_hash, selection_path nunca inventados).
- **Blocker operacional pendente:** `data/stocks.db` não está neste checkout (excluído por
  `.gitignore`) e não tem backup offsite verificado — ação humana necessária antes de
  qualquer desligamento da máquina de pesquisa.

---

## Varredura de qualidade — ingestão FRE (2026-09-04)

Pedido do operador: revisão completa do projeto em busca de bugs/melhorias
(`code-review` skill, `--full-tree stocks_predictor/ tools/ tests/`). Achados
reais, todos em `stocks_predictor/ingest_cvm.py` (código de dividendos/H11
escrito nesta mesma sessão, ainda sem cobertura de teste) — os três corrigidos:

1. **`load_free_float()` usava `_open_zip_csv(zbytes, "distribuicao_capital")`**
   — nome ambíguo (bate tanto no CSV principal quanto no `_classe_acao`), o
   mesmo bug já contornado dentro de `ingest_fre_dividends_year` mas nunca
   aplicado aqui; contra um zip FRE real teria levantado `ValueError`
   ("2 CSVs contendo...") em toda chamada. Corrigido extraindo a lógica de
   filtro manual (já existente, duplicada só em `ingest_fre_dividends_year`)
   para uma função nova, `_open_fre_distribuicao_capital_main(zbytes)`,
   reutilizada pelas duas chamadoras — ponto único de verdade pra essa
   seleção de arquivo.
2. **`_to_float()` tentava `float(raw)` puro primeiro, caindo pro parse BR
   (`,`-decimal/`.`-milhar) só se isso falhasse.** Risco de corrupção
   silenciosa ~1000x: `"450.000"` em notação BR de milhar (450 mil) seria
   lido como `450.0` decimal inglês sem erro nenhum — violação direta da
   regra "nunca consertar/adivinhar dado em silêncio". A ambiguidade é
   inerente à string sozinha (não dá pra adivinhar com segurança); a
   correção foi tornar `fmt` **obrigatório** (`"en"` ponto-decimal-puro pra
   `Montante` de dividendos, formato observado nesse dataset; `"br"`
   milhar-ponto/decimal-vírgula pra `Quantidade_Total_Acoes_Circulacao`,
   mesma convenção do resto do FRE/DFP) — decisão de formato passa a ser do
   chamador, nunca de tentativa-e-erro.
3. **Zero cobertura de teste** pros parsers novos (`parse_fre_dividend_rows`,
   `parse_fre_capital_total_rows`, `_to_float`, `_open_fre_distribuicao_capital_main`,
   `ingest_fre_dividends_year`) — violava a regra de golden tests no parse.
   Adicionados 12 testes em `tests/test_rj_ingest.py` seguindo o padrão
   já estabelecido (zips sintéticos com cabeçalhos/nomes de coluna reais da
   CVM, fixture `_zip_of`/`conn`), cobrindo: os dois formatos de `_to_float`
   e o `fmt` inválido fail-loud; soma de `Montante` por `(cnpj, pay_date)`;
   linha sem data de pagamento descartada; fail-loud sem coluna de valor;
   seleção do CSV principal vs. `_classe_acao`; retenção da maior
   `Data_Referencia` por CNPJ; ingestão fim-a-fim gravando `value_per_share`
   correto e idempotente; companhia sem total de ações confiável não gera
   dado inventado; companhia sem ticker mapeado é pulada.

Suite completa (`STOCKS_ALLOW_VENDOR_SHIM=1` neste sandbox, sem rede real):
278 passed, 1 skipped, 6 failed — os 6 falhos são pré-existentes, do shim de
vendor deste sandbox (`predictor_core` vendorizado numa versão mais antiga
que a canônica 3.0.0: `PastView.__init__` mudou de assinatura,
`pipeline_fingerprint` não existe na versão vendorizada), não relacionados a
esta mudança. Rodar `python -m pytest tests/ -v` na máquina real (Core 3.0.0
canônico) pra confirmar verde total antes de considerar a varredura fechada.

Não coberto ainda por este ciclo de varredura: os itens já pendentes de
antes (lacuna de proventos 2023-2026 na fonte CVM/FRE — sem alternativa
confirmada; fonte B3 candidata em `tools/explore_b3_dividends_api.py` segue
não verificada, endpoint precisa ser confirmado via devtools do navegador
numa máquina com rede real) e a rodada real da H11 (só smoke test sintético
rodou até agora).

---

## Varredura de qualidade — 2ª leva (2026-09-04)

Continuação do pedido do operador ("faz tudo já"): rodada nova do
`code-review` (`--full-tree stocks_predictor/ tools/`) sobre o resto do
projeto (o núcleo financeiro/estatístico — anti-lookahead, point-in-time,
custo/turnover, DSR/FDR, ledger write-once — não teve achado defensável).
3 achados reais, todos em caminhos secundários (metadado de ledger, tooling
ad-hoc), os três corrigidos:

1. **`paper.settle_exits()` calculava `holding_days` a partir de `asof`
   (data do SINAL), não de `exec_date` (data da EXECUÇÃO real).**
   `settle_executions()` preenche `exec_date` em D+1 (ou mais, com
   feriado/fim de semana no meio) — usar `asof` inflava sistematicamente o
   campo de auditoria pelo atraso sinal→execução em toda linha do ledger
   RISK. Corrigido buscando `exec_date` na mesma query e usando-o no cálculo.
   `tests/test_paper.py::test_settle_exits_writes_risk_part_write_once`
   ganhou um assert que confere `holding_days == (exit_date - exec_date).days`
   exatamente (antes só checava `> 0`, o que não pegava a inflação).
2. **`tools/migrate_trials_schema.py`: `_FAMILY_BY_PREFIX` nunca foi
   atualizado para H7/H9 (já registradas em `trials.json`) nem H10/H11**,
   então `hypothesis_family` saía `"UNKNOWN"` pras trials novas e
   `n_trials_domain` ficava travado em `len(_FAMILY_BY_PREFIX)` (6) mesmo
   com 8 trials reais já no ledger — o tipo exato de subestimação
   silenciosa de multiplicidade que a disciplina DSR/FDR do projeto existe
   pra evitar. Corrigido: mapa completado com os 4 prefixos que faltavam
   (h7/h9/h10/h11) e `n_trials_domain` passou a ser `len(legacy_trials)`
   (contagem real do ledger), não mais o tamanho do mapa. `trials_v2.json`
   regerado (arquivo derivado/regenerável, não é o ledger — `trials.json`
   não foi tocado); `--check` confirma idempotência.
3. **`tools/ingest_h7_real.py` rebaixava e reparseava o zip do DFP inteiro
   do ano a cada ticker extra (ON+PN da mesma empresa)** — pra um ano com 5
   empresas ambíguas, 6 downloads completos em vez de 1, todos do mesmo
   balanço já em mãos. Corrigido: `ingest_cvm.ingest_dfp_year` ganhou
   parâmetro opcional `zbytes` (bytes já baixados; `None` = comportamento
   antigo, baixa como sempre) e o script agora baixa o zip do ano UMA vez,
   reusado pela passada primária e por todas as chamadas de 2ª classe. Teste
   novo (`test_ingest_dfp_year_accepts_prefetched_zbytes_without_downloading`)
   confirma que `download_zip` não é chamado quando `zbytes` é passado.

Suite completa (sandbox, `STOCKS_ALLOW_VENDOR_SHIM=1`): 279 passed, 1
skipped, 6 failed — os mesmos 6 pré-existentes do shim de vendor (Core
vendorizado mais antigo que o canônico 3.0.0), documentados na entrada
anterior, não relacionados a esta mudança. Confirmar verde total na
máquina real com Core 3.0.0.

---

## Varredura de qualidade — 3ª leva, linha RJ (2026-09-04)

Continuação do pedido do operador ("continua a varredura no resto do
projeto"). `code-review` (`--full-tree`) sobre `tests/`, `config.py`,
`config.yaml` e o resto do pipeline RJ (`rj_judge*`, `rj_pipeline`,
`rj_episodes`, `rj_families*`, `rj_power`, `rj_coda`) — matemática de
BH-FDR, Romano-Wolf, censura/candidatos point-in-time e o mini-parser de
config conferidos corretos. 2 achados reais, ambos corrigidos (linha RJ é
`ARCHIVED`/sem trabalho científico novo autorizado, mas
`STOCKS_CURRENT_STATE.md` permite explicitamente "bug real" como alteração
válida):

1. **`rj_judge.apply_fdr()` marcava família ELEGÍVEL pro FDR mas SEM
   p_value (ex.: `"ownership"`, sem ingestor real ainda — `rj_pipeline`
   grava `p_value=None` pra ela em todo episódio) como
   `significant_after_fdr=False`**, quando deveria ser `None` — a mesma
   distinção "nunca testada" vs. "testada e não significativa" que o
   próprio docstring da função já declarava para famílias descritivas
   (fora do FDR), mas não implementava para famílias elegíveis sem dado.
   Isso contaminaria o veredito real da linha RJ (`rj_judge_robust`
   já tinha até um teste — `test_robustness_report_none_bh_gives_none_concordant`
   — que assumia `None` corretamente, mas `apply_fdr` nunca entregava
   `None` nesse caso). Corrigido: `significant_after_fdr=None` tanto pra
   família fora do conjunto de FDR quanto pra elegível sem p_value.
   Teste novo `test_apply_fdr_family_without_data_is_none_not_false`.
2. **`rj_coda.clr_matrix()` descarta colunas sem nenhum valor positivo de
   `data`, mas devolvia `mask` ainda indexada na numeração ORIGINAL das
   colunas** (a de `impute_zeros`, antes do descarte) — qualquer auditoria
   downstream usando `mask` pra localizar a célula imputada em `data` lia a
   célula errada (ou estourava índice) sempre que `dropped_cols` não
   fosse vazio, quebrando a garantia que o próprio docstring promete
   ("qualquer análise downstream deve poder auditar quanto do dado é
   imputado"). Corrigido: `mask` remapeada pra numeração nova (pós-descarte)
   antes de retornar. Teste novo
   `test_clr_matrix_mask_remapped_after_dropping_column`.

Suite completa (sandbox): 281 passed, 1 skipped, 6 failed — mesmos 6
pré-existentes do shim de vendor, não relacionados. Confirmar verde total
na máquina real com Core 3.0.0.

---

## Varredura de qualidade — 4ª leva, módulos restantes (2026-09-04)

Continuação do pedido do operador ("continua a varredura nos módulos
restantes"). `code-review` (`--full-tree`) sobre `analyst.py`,
`ecosystem_plugin.py`, `economic_gate.py`, `universe.py`, `returns.py`,
`execution.py`, `cotahist.py`, `ingest_cotahist.py` — com isso, praticamente
todo `stocks_predictor/`, `tools/` e `tests/` já passou por pelo menos uma
leva. `universe.py`/`execution.py`/`returns.py` já estavam muito
endurecidos por revisões anteriores (comentários citando achados prévios) e
não tiveram achado novo. 4 achados, todos corrigidos:

1. **`cotahist.parse_line()` construía o campo `date` por interpolação de
   string CRUA, sem validação de dígito/formato** — ao contrário de TODOS
   os outros campos (protegidos por `int()`, que já falha em lixo). Um
   registro tipo 01 com os bytes de DATA corrompidos (posições 3-10)
   virava `"2024- X-  "` sem levantar exceção nenhuma, e como não é
   detectado por `int()`, não contava em `n_bad` — o EXATO tipo de
   corrupção silenciosa que o resto do parser evita. Toda query
   anti-lookahead (`date < ?`, `ORDER BY date DESC`) em `universe.py`/
   `returns.py`/`execution.py` depende de ordenação lexicográfica dessa
   string. Corrigido: `date` agora valida 8 dígitos antes de montar a
   string ISO, levanta `ValueError` (capturado e contado como `n_bad` por
   `parse_lines`, mesmo tratamento dos outros campos). Teste novo
   `test_cotahist_corrupted_date_is_malformed_not_silently_accepted`.
2. **`cotahist.parse_lines()` não tinha guard pra ZERO linhas tipo 01 na
   fonte inteira** (`n_quote == 0`) — o guard existente só cobria "achou
   linhas de cotação mas todas malformadas"; uma fonte com zero linhas tipo
   01 (arquivo errado, vazio, layout mudou) retornava silenciosamente
   `([], 0)`, sem log e sem exceção. Corrigido: `n_quote == 0` agora
   também é fail-loud.
3. **`ingest_cotahist.parse_cotahist()` escolhia o `.TXT` de dentro do zip
   via `next(... .endswith(".TXT"))`** — pegava o primeiro que batesse por
   sorte, sem checar se era de fato o arquivo de cotação (um
   README/layout `.TXT` companheiro, se algum dia existir no zip, seria
   escolhido no lugar). Combinado com o achado 2 acima (zero linhas tipo
   01 → 0 silencioso), um zip assim "carregava com sucesso" sem carregar
   nada. Corrigido: `_pick_cotahist_txt()` novo, prefere nome contendo
   "COTAHIST", falha alto se ambíguo. Testes novos cobrindo o companheiro
   e a ambiguidade.
4. **`analyst.build_brief()` formatava `median_vol` com separador de
   milhar padrão Python (`{:,.0f}`, convenção US — vírgula)** — o
   briefing é em português pra operador brasileiro, onde vírgula é o
   separador DECIMAL; "R$ 1,234,567" lido em convenção PT-BR sugeriria
   ~1,23, não ~1,23 milhão, arriscando má leitura da magnitude no relatório
   consultivo que existe pra transmitir exatamente isso. Corrigido:
   `_fmt_ptbr()` novo (formata em US, troca separadores — não usa
   `locale.setlocale`, que é estado global de processo). Primeiro arquivo
   de teste pra `analyst.py` (`tests/test_analyst.py`, não existia
   nenhum antes).
5. **`economic_gate.estimate_edge()` chamava `float(x)` duas vezes por
   observação** (uma no filtro, outra na expressão) — não era bug de
   correção, só trabalho redundante; trocado por `fx := float(x)` numa
   única conversão via walrus.

Suite completa (sandbox): 287 passed, 1 skipped, 6 failed — mesmos 6
pré-existentes do shim de vendor, não relacionados. Confirmar verde total
na máquina real com Core 3.0.0.

---

## Varredura de qualidade — 5ª leva, módulos finais (2026-09-04)

Continuação do pedido do operador ("continua a varredura nos módulos
restantes"). `code-review` (`--full-tree`) sobre os arquivos que ainda
não tinham passado por nenhuma leva: `rj_outcomes.py`, `main.py` e os
scripts ad-hoc na raiz `audit_db.py`/`diagnose_universe.py`. Com isso,
TODO o código do projeto (pacote, tools/, scripts de raiz, tests/) já
passou por pelo menos uma leva de revisão. 6 achados, todos corrigidos:

1. **`main.py::cmd_paper` gravava `runs.config_hash` do hash de um dict
   EMBRULHADO (`{"command", "asof", "config": cfg}`), não de `cfg`
   diretamente** — ao contrário de TODO outro comando (`cmd_backtest`,
   `cmd_backtest_h2/h4/h5`). Violava a garantia do próprio design
   (§11, "reproduzível por run_id+config_hash"): nenhuma rodada de paper
   jamais teve `config_hash` igual ao `cfg_mod.config_hash(cfg)` real,
   fazendo qualquer auditoria de "essa rodada usou o config atual?" falhar
   sempre. Corrigido: `db.new_run(conn, cfg, ...)` direto, `asof` movido
   pro `notes`.
2. **`rj_outcomes.market_adjusted_rally()` só validava o fechamento do
   índice no dia do FUNDO, nunca em dias posteriores da janela** — um
   tick ruim do benchmark em qualquer outro dia (fechamento <=0) zerava
   `(1+idx_ret)` e estourava `ZeroDivisionError` na razão geométrica, em
   vez de degradar como o resto da função já fazia. Corrigido: dia com
   fechamento de índice inválido é pulado (mesmo espírito "sem dado
   confiável, sem inventar" do resto do outcome).
3. **`rj_outcomes.walk_forward_splits()` sem validação de `step`** —
   `step<=0` nunca avança o cursor (`start = min(start+step, n_obs)`
   trava, ou até regride pra `step<0`), loop infinito silencioso.
   Corrigido: `ValueError` fail-loud pra `step<=0`.
4. **`diagnose_universe.py` simulava a query do universo SEM o filtro
   `market_type = SPOT_MARKET`** que `universe.rank_universe()` sempre
   aplica — o diagnóstico contava linhas de mercados que a query real
   nunca vê (ex.: leilão), escondendo o motivo real de um ticker sumir
   do universo, exatamente o tipo de coisa que este script existe pra
   investigar. Corrigido: filtro adicionado.
5. **`diagnose_universe.py` conectava em `data/stocks.db` sem checar
   `Path.exists()`** — rodar antes de qualquer ingest criava um
   `stocks.db` vazio espúrio e falhava com `OperationalError` cru em vez
   de mensagem clara. Corrigido: mesma checagem que `audit_db.py` já
   tinha.
6. **`audit_db.py` nunca reconfigurava `stdout` pra UTF-8** — o próprio
   `CLAUDE.md` documenta esse pitfall explicitamente ("default do Windows
   é cp1252 — já mordeu"); o emoji `❌` no print de erro quebraria com
   `UnicodeEncodeError` ANTES de mostrar a mensagem de erro pretendida.
   Corrigido: mesmo `sys.stdout.reconfigure(encoding="utf-8")` que
   `main.py` já usa.

Testes novos em `tests/test_rj_next_gen.py`
(`test_walk_forward_splits_rejects_nonpositive_step`,
`test_market_adjusted_rally_skips_bad_index_tick_mid_window`). Os scripts
de raiz (`audit_db.py`/`diagnose_universe.py`) são ad-hoc, sem suíte —
validados manualmente rodando contra o `stocks.db` do sandbox (sem
crash, comportamento preservado no caminho feliz).

Suite completa (sandbox): 289 passed, 1 skipped, 6 failed — mesmos 6
pré-existentes do shim de vendor, não relacionados. Confirmar verde total
na máquina real com Core 3.0.0.

---

## Confirmação real da varredura + Core 3.1.0 (2026-09-04)

Operador rodou a suíte completa na máquina real (Windows, Core recém
atualizado): **296 passed, 0 failed** — confirma as 5 levas da varredura
(PRs #38-#42, 22 achados corrigidos) de ponta a ponta, sem shim de vendor.

Achado no caminho: `predictor-core` instalado na máquina estava em 2.2.0
(pyproject.toml exige `>=3.0,<4`). O pacote NÃO está no PyPI público —
distribuição é só por wheel de GitHub Release do repo irmão
`leonardosovienski/core-predictor` (`README.md` de lá: "Distribution
occurs through wheels"). Resolvido instalando direto do asset da release:

```powershell
python -m pip install --upgrade "https://github.com/leonardosovienski/core-predictor/releases/download/v3.1.0/predictor_core-3.1.0-py3-none-any.whl"
```

`core-predictor` (repo irmão) não tinha nada quebrado — release 3.1.0 já
publicada e íntegra (`v3.0.0`→`v3.1.0`, wheel+sdist com attestation). O
problema era só a versão instalada localmente estar desatualizada.

## Retrospectiva da sessão (2026-09-04, pedido do operador)

Pedido: reler a sessão inteira, avaliar se o caminho seguido foi correto,
se eu manteria as decisões. Registro aqui pra não viver só no chat:

**Mantido sem ressalva:** disciplina de pré-registro (parâmetros
`[Hn-FROZEN]` travados por golden hash antes de qualquer código tocar
dado real, em toda hipótese H7-H11); parar e perguntar via
`AskUserQuestion` nos pontos de decisão de design não cobertos (edição do
`trials.json`, fonte de dado de dividendos, desenho do sinal H9/H10) em
vez de decidir em silêncio; declarar aproximações e limitações
explicitamente (agregação ON+PN, data de pagamento como proxy de ex-date,
lacuna de cobertura 2023-2026) em vez de escondê-las; vereditos honestos
— 9/9 hipóteses `NOT_SUPPORTED` reportadas como são, sem dourar.

**Faria diferente (tático, não estrutural):**
1. A varredura de qualidade virou 5 PRs separados (#38-#42) — granularidade
   fina demais pro tipo de achado (bugs de código, não decisão científica);
   agrupar por módulo/tema em 2-3 PRs teria reduzido o overhead de
   coordenação (5 ciclos de draft→watch→merge→check-in cancelado) sem
   perder atomicidade de revisão.
2. Chutei o caminho do repo (`C:\Claude-projetos\Claude\stocks-predictor`)
   quando o operador reabriu o PowerShell, sem esse dado — devia ter
   pedido pra localizar o repo primeiro.
3. Girei tentando `pip install predictor-core` contra o PyPI público antes
   de ir direto ao repo `core-predictor` no GitHub — o pacote nunca esteve
   no PyPI, então essas tentativas eram fadadas a falhar; devia ter
   perguntado "o Core tem repo remoto?" mais cedo.

**Não é erro, é o processo funcionando:** 0/9 hipóteses comprovadas é o
pedágio estatístico (IC95% + DSR) fazendo o trabalho dele, não falha de
condução. H11 (única pendente) segue como a única ponta solta real — dado
o histórico, a expectativa honesta é que também não passe, mas valia
testar por corrigir um viés metodológico real (só-preço) declarado desde a
H1.

**Achado na varredura de documentação** (pedido do operador, "confere
todos os md do projeto"): `AGENTS.md` e `CLAUDE.md` são idênticos exceto
por uma linha — `AGENTS.md` apontava o repo irmão do Core em
`C:\Codex-projetos\Codex\predictor_core\`, `CLAUDE.md` em
`C:\Claude-projetos\Claude\predictor_core\` (a fonte de verdade real,
confirmada nesta sessão). Drift de cópia, não decisão intencional
(nenhuma data/nota diferenciando os dois). Corrigido: `AGENTS.md`
alinhado ao caminho real. Demais menções a `predictor-core==3.0.0`/
"252 testes" em `RESEARCH_FREEZE.md`/`README.md` são entradas DATADAS de
sessões anteriores (registram o que era verdade naquele momento, não
claim de estado atual) — preservadas intactas, mesma disciplina
append-only do resto do projeto.

---

## Errata de schema — test_period (2026-09-04)

Tentando registrar a H11 de verdade (Core 3.1.0 já instalado, atestado
regerado com sucesso), `register_hypothesis` rejeitou o registro com um
erro que não era da H11 em si: o Core 3.1.0 passou a validar TODAS as
entradas de `trials.json` ao registrar qualquer trial nova (não só a
nova), e ficou mais estrito sobre `test_period` — exige ISO-8601 UTC
completo com `Z` em limites fechados. As 6 entradas mais antigas
(H1/H2/H4/H5/H6/H8, registradas sob uma versão de Core mais antiga/frouxa)
usavam só data (`"2018-01-01"`); H7/H9 (registradas depois, 2026-09-04)
já usavam o formato completo — por isso só as 6 antigas quebravam.

Mesmo padrão de errata do achado de 2026-09-03 (`pipeline_fingerprint`
órfão): schema drift entre versões do Core, não erro de conteúdo.
Corrigido com autorização explícita do operador antes de tocar o ledger:
`"2018-01-01"` → `"2018-01-01T00:00:00Z"`, `"2026-07-03"` →
`"2026-07-03T23:59:59Z"` nas 6 entradas — mesma data, só formatação;
`sharpe`/`params`/`notes`/`registered_at` preservados byte a byte.
Validado (`json.load` + contagem de entradas) antes de commitar.

**Próximo passo:** operador roda de novo
`python -c "import backtest; backtest.run_h11(write_report=True)"` — a
H11 deve registrar sem erro agora (schema do ledger inteiro válido).

---

## VEREDITO H11 — ENCERRADA: NÃO COMPROVADA (2026-09-04, rodada real, COTAHIST real)

Rodada real na máquina do operador, Core 3.1.0, `backtest.run_h11(write_report=True)`,
após a errata de `test_period` acima:

```
1.218 pregões pareados
IC 95% diff-Sharpe (stationary, bloco 21): (-0,0378, +0,7914) — cruza zero
DSR: 0,8430 < 0,95 (N=10)
PSR: 0,7704
NÃO COMPROVADA. Sem repescagem.
```

Estratégia vs. benchmark: Sharpe anualizado 0,9167 (estratégia) vs. 0,5660
(benchmark); retorno total 205,51% vs. 77,28%; max drawdown 48,62% vs.
46,50%. Relatório: `reports/h11_verdict_adhoc.md` (versionado via
`git add -f`, mesmo padrão de H6-H10).

**Achado no caminho — ledger `trials.json` sincronizado com atraso:** ao
tentar registrar a H11, apareceu um `diff` local não commitado — o
veredito real da H10 (sharpe 0,006019, registrado 2026-09-04T03:22:11Z)
nunca tinha sido enviado ao repositório, mesmo já documentado no HANDOFF
(entrada "VEREDITO H10" acima) e no `RESEARCH_FREEZE.md`. Commitado antes
de prosseguir (`chore: registra H10 no ledger`), sem alterar nenhum valor
— só levando ao GitHub o que já existia local.

**Leitura acumulada (10 tentativas, 0 comprovadas, pesquisa de fatores
ESGOTADA):** H11 teve o MAIOR DSR de todas as 10 hipóteses (0,8430 —
contra 0,0277 a 0,6843 das anteriores) e o IC mais próximo de excluir
zero, mas ainda reprova o limiar pré-registrado de 0,95. Mesmo corrigindo
o viés metodológico mais sério declarado desde a H1 (retorno só-preço
favorecendo momentum artificialmente), o sinal não sobrevive ao pedágio
estatístico nesta janela/universo da B3. Não há mais nenhuma hipótese
pré-registrada pendente nem fronteira de dado nova identificada.
`RESEARCH_FREEZE.md` (H11 movida pra `stopped_hypotheses`) e
`STOCKS_CURRENT_STATE.md` (`research_state=FROZEN`,
`scientific_state=CLOSED_FOR_H1_THROUGH_H11`, `new_scientific_trials=0`)
atualizados.

---

## H12 e H13 ABERTAS — PRÉ-REGISTRO (2026-09-04, ANTES de qualquer rodada real)

Decisão explícita do operador (com a ressalva de que cada hipótese é
testada UMA vez, julgada UMA vez — não é "tentar até passar", que é
justamente o que o pedágio IC95%+DSR existe pra impedir). Duas hipóteses
novas, ambas reusando dado JÁ ingerido (DRE da DFP/CVM, baixada desde a
H7) — zero rede/ingestão nova, só extração de contas que já estavam nos
arquivos e nunca tinham sido lidas.

**H12 — margem líquida isolada** (`config.yaml` `h12_*`,
`config.h12_frozen_config_hash` = `73444111b8bd969f`): quintil SUPERIOR de
`net_margin = lucro_liquido/receita_liquida`, mesmo universo/custos/embargo
(90 dias) de H7/H9/H10. Racional: 3ª variável contábil independente da
DFP — ROE (H7) mistura alavancagem financeira no numerador por identidade
contábil, alavancagem isolada (H9) também reprovou; margem é qualidade
puramente OPERACIONAL, mecanismo distinto dos dois.

**H13 — crescimento de receita YoY** (`config.yaml` `h13_*`,
`config.h13_frozen_config_hash` = `473ca87ab5b1f8a0`): quintil SUPERIOR de
`(receita_t − receita_t-1)/receita_t-1`, mesma fonte/embargo. **Primeira
hipótese de CRESCIMENTO testada neste domínio** — H1-H12 são todas
nível/valor (momentum mede preço, não fundamento). Precisa de DUAS linhas
elegíveis de receita por ticker (a mais recente sobre a anterior); como a
DFP é anual (não ITR trimestral), as duas linhas mais recentes elegíveis
tipicamente distam ~12 meses, mas isso não é verificado — um gap maior por
ano com dado faltante entra do mesmo jeito (limitação da granularidade da
fonte, declarada em `report._BIAS_NOTE["H13"]`, não escondida).

**Critério (ambas):** IC95% diff-Sharpe > 0 E DSR >= 0,95 — H12 com N=11
tentativas no registro, H13 com N=12 (10 já julgadas + a outra nova).

**Implementação:**
- `db.py` migração `0010_fundamentals_revenue` (append-only: 2 colunas
  novas em `fundamentals`, `0007` intocada) — `receita_liquida`,
  `net_margin`.
- `ingest_cvm.compute_fundamentals`: conta de receita (código `3.01`,
  keyword "receita") extraída da MESMA DRE já parseada pela H7/H9; grupo
  de contas de margem (`lucro` + `receita`) é INDEPENDENTE do grupo de
  roe/leverage (`ativo`+`passivo`+`pl`+`lucro`) — uma empresa pode ter
  `net_margin` sem `roe`/`leverage` resolvidos, e vice-versa. `ingest_dfp_year`
  grava as 2 colunas novas no INSERT.
- `factor.net_margin_signals` (H12): reusa o motor comum
  `_fundamental_signals` (mesmo de roe/leverage), só adiciona `"net_margin"`
  às colunas aceitas.
- `factor.revenue_growth_signals` (H13): motor NOVO (não cabe no comum —
  precisa de 2 linhas, não 1): pega as duas linhas mais recentes ELEGÍVEIS
  (embargo já vencido) de `receita_liquida`, `growth = (mais_recente −
  anterior)/anterior`; ticker com <2 linhas elegíveis ou receita anterior
  <=0 fica fora (sem crescimento fabricado).
- `backtest.run_h12`/`run_h13`: mesmo runner genérico `_run_hypothesis`,
  `take="top"` nas duas.
- `report._BIAS_NOTE["H12"]`/`["H13"]`: mesma limitação declarada de
  H7/H9/H10 (direção do viés só-preço não estabelecida a priori); H13
  soma a limitação de granularidade anual.
- `tests/test_h12_quality_margin.py`, `tests/test_h13_revenue_growth.py`:
  smoke com dado sintético, golden hash do lacre, hash ignora parâmetro
  operacional, testes de embargo/2-linhas/denominador inválido.
- `tests/test_rj_ingest.py`: 2 testes novos confirmando que os dois grupos
  de contas (roe/leverage vs. margem) são independentes em
  `compute_fundamentals`.

Suite completa (sandbox): 302 passed, 1 skipped, 6 failed — mesmos 6
pré-existentes do shim de vendor, não relacionados.

**Achado no caminho — backfill é OBRIGATÓRIO, não opcional:** as linhas de
`fundamentals` já gravadas pela H7 (antes desta migração) têm
`receita_liquida`/`net_margin` NULL — a coluna não existia quando foram
inseridas. `ingest_dfp_year` usava `INSERT OR IGNORE`, que NUNCA
preencheria colunas novas em linha já existente (ignorada pra sempre).
Corrigido para `INSERT ... ON CONFLICT DO UPDATE`, mas o UPDATE só dispara
quando a linha existente tem `receita_liquida IS NULL` E o novo parse tem
valor pra gravar — nunca sobrescreve um valor já preenchido, e não conta
como "mudança" (nem quebra a idempotência já testada) quando rodado de
novo sobre dado já backfillado. Teste novo:
`test_ingest_dfp_year_backfills_revenue_on_preexisting_row`.

**Próximo passo (máquina do operador):** `python -m pytest tests/ -v`
pra confirmar verde total, depois RE-RODAR a ingestão real da H7 pra
backfillar receita/margem nas linhas já existentes (mesmos zips já
baixados, sem rede nova necessária se ainda estiverem em cache/repetir o
download é barato):
```
python tools/ingest_h7_real.py
python -c "import backtest; backtest.run_h12(write_report=True)"
python -c "import backtest; backtest.run_h13(write_report=True)"
```

---

## VEREDITO H12 e H13 — ENCERRADAS: NÃO COMPROVADAS (2026-09-04, rodada real, COTAHIST real)

Backfill (`tools/ingest_h7_real.py`) confirmou o achado documentado acima: 733
linhas gravadas/atualizadas em `fundamentals` (69-96 por ano, 2018-2026) — o
`INSERT OR IGNORE` puro realmente travava o backfill; o UPSERT condicional
corrigiu. Rodadas reais na máquina do operador, Core 3.1.0:

```
H12 (margem líquida, quintil superior):
  1.826 pregões pareados
  IC 95% diff-Sharpe: (-0,3356, +0,1848) — cruza zero
  DSR: 0,1952 < 0,95 (N=11)
  PSR: 0,4328
  NÃO COMPROVADA.

H13 (crescimento de receita YoY, quintil superior):
  1.597 pregões pareados
  IC 95% diff-Sharpe: (-0,4562, +0,1611) — cruza zero
  DSR: 0,2598 < 0,95 (N=12)
  PSR: 0,3579
  NÃO COMPROVADA.
```

Ambas ficaram entre as DSR mais BAIXAS de toda a série (H12: 0,1952 — 2ª mais
baixa depois da H5/0,1274; H13: 0,2598) — nem perto do limiar, ao contrário
da H11 (0,8430). Relatórios: `reports/h12_verdict_adhoc.md`,
`reports/h13_verdict_adhoc.md` (versionados via `git add -f`).

**Achado adicional no caminho — H11 também tinha lacuna de ledger:** o
mesmo padrão do H10 (achado 2026-09-04, entrada "VEREDITO H11" acima) se
repetiu — o registro real da H11 em `trials.json` (sharpe 0,057773,
2026-09-04T15:24:10Z) nunca tinha sido commitado, só o relatório `.md`.
Commitado junto com H12/H13 nesta rodada, sem alterar nenhum valor
(`chore: registra H11/H12/H13 no ledger`).

**Leitura acumulada (12 tentativas, 0 comprovadas):** a 3ª e 4ª variáveis
contábeis independentes da DFP (margem líquida, crescimento de receita)
também reprovam, com folga — bem mais fracas que ROE/alavancagem/H10/H11.
Isso esgota o baralho de fatores extraíveis da DFP consolidada sem uma
fonte de dado genuinamente nova (fluxo de caixa, múltiplos de mercado,
dado intraday/institucional) ou universo diferente. `RESEARCH_FREEZE.md`/
`STOCKS_CURRENT_STATE.md` atualizados: `scientific_state=CLOSED_FOR_H1_THROUGH_H13`,
`new_scientific_trials=0`.

---

## H14, H15 e H16 ABERTAS — PRÉ-REGISTRO (2026-09-04, ANTES de qualquer rodada real)

Decisão explícita do operador ("as 3 ao msm tempo"), sempre com a ressalva
de que cada hipótese é testada UMA vez, julgada UMA vez. Três candidatos
levantados após o esgotamento da DFP (H7-H13): dois fatores de preço nunca
testados (zero dado novo) e a primeira hipótese de TIMING do domínio.

**H14 — proximidade da máxima de 52 semanas** (`config.yaml` `h14_*`,
`config.h14_frozen_config_hash` = `21b9c2ca735a8684`): quintil SUPERIOR de
`close(asof)/max(close, 252 pregões)` (`factor.near_52w_high_signals`).
Fator de preço distinto de momentum (George & Hwang 2004) — proximidade da
máxima tem poder preditivo próprio na literatura, não redutível ao retorno
acumulado que momentum mede. Mesma maquinaria de H1 (`walk_forward`), zero
dado novo.

**H15 — volume anormal** (`config.yaml` `h15_*`,
`config.h15_frozen_config_hash` = `a4d7e124231d6a5b`): quintil SUPERIOR de
`volume_médio_21d/volume_médio_252d − 1` (`factor.volume_surge_signals`).
`volume_fin` já vive em `prices_raw` desde o M1 (usado só pra ranquear
liquidez do universo), NUNCA como sinal de seleção — zero dado novo. Mesma
maquinaria de H1.

**H16 — efeito virada-de-mês** (`config.yaml` `h16_*`,
`config.h16_frozen_config_hash` = `584350278798ef6a`): últimos
`last_days_of_month=1` pregões do mês + primeiros `first_days_of_month=3`
do mês seguinte (Lakonishok & Smidt 1988, "turn-of-the-month effect").
**PRIMEIRA hipótese de TIMING testada neste domínio** — H1-H15 são todas
seleção transversal (QUAIS papéis escolher, rebalance mensal, hold até o
próximo); H16 testa QUANDO estar posicionado, no MESMO universo, sem
seleção por fator nenhum.

**Critério (as 3):** IC95% diff-Sharpe > 0 E DSR >= 0,95 — H14 N=13, H15
N=14, H16 N=15 (12 já julgadas + as outras duas novas cada vez).

**Implementação:**
- `factor.near_52w_high`/`near_52w_high_signals` (H14): mesma disciplina
  point-in-time de `momentum_12_1` (`_idx_le`), `None` se histórico
  insuficiente ou preço <=0.
- `factor.volume_surge_signals` (H15): consulta `prices_raw` direto (não
  `series_by_ticker`, que só carrega preço) — mesmo padrão de
  `_fundamental_signals`. Só pregões ESTRITAMENTE anteriores a `asof`
  (`date < asof`, não `<=`) — o volume do próprio dia não é conhecido
  antes do fechamento, mesma disciplina anti-lookahead do resto do
  domínio.
- `backtest.run_h14`/`run_h15`: mesmo runner genérico `_run_hypothesis`
  (`walk_forward`), `take="top"` nas duas.
- `backtest.run_h16`: mecânica NOVA, não usa `walk_forward` — universo
  rebalanceado mensalmente (mesma disciplina PIT de
  `universe.select_universe`), carteira equiponderada FIXA entre
  rebalances (mesma de H1); a estratégia só "conta" o retorno do dia nos
  pregões de virada-de-mês (`backtest._turn_of_month_days`), o BENCHMARK
  é a MESMA carteira posicionada TODO dia (isola timing de seleção de
  universo). Custo: 1 `one_way` em cada transição cash/posicionado
  (aproximação declarada: ignora turnover de composição do universo entre
  rebalances — ver docstring de `run_h16`).
- `backtest._run_hypothesis`/`_finalize_hypothesis`: refactor não-invasivo
  — extraído o fecho comum (pedágio+registro+relatório) de
  `_run_hypothesis` pra uma função própria, reusada por `run_h16` (que não
  passa por `walk_forward`). H1-H15 continuam idênticas (mesma suíte
  completa confirmando, sem quebra).
- `config.yaml`/`config.py`: `h14_*`/`h15_*`/`h16_*` `[H14-FROZEN]`/
  `[H15-FROZEN]`/`[H16-FROZEN]`.
- `report._BIAS_NOTE["H14"]`/`["H15"]`/`["H16"]`: declaram a limitação de
  cada uma (H14: mesma direção de viés da H1/momentum; H15: sem direção
  estabelecida; H16: viés irrelevante ao mecanismo — timing, não seleção
  — mas custo simplificado declarado).
- Testes novos: `tests/test_h14_near_52w_high.py`,
  `tests/test_h15_volume_surge.py`, `tests/test_h16_turn_of_month.py`
  (smoke, golden hash, hash ignora parâmetro operacional, casos de borda
  point-in-time, calendário de virada-de-mês com meses conhecidos).

Suite completa (sandbox): 321 passed, 1 skipped, 6 failed — mesmos 6
pré-existentes do shim de vendor, não relacionados.

**Próximo passo (máquina do operador):** `python -m pytest tests/ -v` pra
confirmar verde total, depois:
```
python -c "import backtest; backtest.run_h14(write_report=True)"
python -c "import backtest; backtest.run_h15(write_report=True)"
python -c "import backtest; backtest.run_h16(write_report=True)"
```
Nenhum backfill/ingestão nova necessária — as 3 usam dado que já está em
`prices_raw` desde o M1 (H14/H15) ou o mesmo universo/preço de H1 (H16).

---

## VEREDITO H14, H15 e H16 (2026-09-04, rodada real na máquina do operador)

Rodadas reais via `python main.py backtest-h 14/15/16` (dispatcher novo
da revisão de infraestrutura abaixo). Suite completa antes das rodadas:
328 passed (sandbox). Todas as 3 **NOT_SUPPORTED** — com H14-H16, a
pesquisa de fatores fecha em **16/16 NOT_SUPPORTED**.

- **H14 (proximidade da máxima 52 semanas)** — 2.131 pregões. PSR
  0.5800, IC95% diff-Sharpe (-0.2424, 0.3864) cruza zero, DSR 0.3249
  (N=13) < 0.95. Sharpe por-período realizado positivo (0.016328) mas
  insuficiente para passar o pedágio. Relatório:
  `reports/h14_verdict_adhoc.md`.
- **H15 (surto de volume)** — 2.131 pregões. PSR 0.5228, IC95%
  diff-Sharpe (-0.2527, 0.3129) cruza zero, DSR 0.2826 (N=14) < 0.95.
  Sharpe por-período realizado positivo (0.013167), mesma conclusão da
  H14. Relatório: `reports/h15_verdict_adhoc.md`.
- **H16 (efeito virada-de-mês)** — 2.132 pregões, motor de backtest
  dedicado (não `walk_forward`). PSR 0.0427, IC95% diff-Sharpe
  (-1.4044, 0.2011) cruza zero, DSR 0.0052 (N=15) — **o mais baixo de
  toda a série de 16 hipóteses**. Sharpe por-período realizado
  NEGATIVO (-0.02483): o sinal apontou na direção errada (virada de mês
  não superou o resto do mês nesta janela/universo). Relatório:
  `reports/h16_verdict_adhoc.md`.

Ledger real (`trials.json` + `trials.harness_attestation.json`)
atualizado e commitado (`f468e66`). `RESEARCH_FREEZE.md` e
`STOCKS_CURRENT_STATE.md` atualizados: `scientific_state =
CLOSED_FOR_H1_THROUGH_H16`.

Com H14-H16, também se esgota — junto com o esgotamento fundamentalista
de H12/H13 — a linha de padrões técnicos/calendário testável com os
dados de preço já ingeridos (COTAHIST): momentum, reversão, vol,
proximidade de máxima, volume e sazonalidade de calendário todos
reprovaram. Qualquer hipótese nova exigiria fonte de dado genuinamente
diferente (fluxo de caixa, múltiplos de mercado, dado intraday/
institucional, opções) ou universo/mercado diferente — não mais uma
recombinação do que já foi observado (isso seria p-hacking, recusado
explicitamente nesta sessão).

---

## Revisão de infraestrutura (2026-09-04, pedido do operador)

Pedido do operador: com a pesquisa de fatores esgotada (16/16), revisar o
que existe mas nunca foi completado/conectado, sem reabrir nenhuma
hipótese julgada nem "combinar até funcionar" (recusado explicitamente —
ver conversa; combinar fatores já observados como fracos é exatamente o
p-hacking que o pedágio IC95%+DSR existe pra impedir).

**Achado 1 — CLI travado em H5, 11 hipóteses inalcançáveis pelo ponto de
entrada documentado.** `main.py` só tinha comandos nomeados até
`backtest-h5`; H6-H16 só eram alcançáveis via
`python -c "import backtest; backtest.run_hN(...)"` (o workaround que
usamos a sessão inteira, com o atrito real de `PYTHONPATH` manual toda
vez). Corrigido: `main.py backtest-h <N>` — dispatcher genérico que chama
`backtest.run_hN(write_report=True)` via `getattr`. Não adiciona hipótese
nenhuma, só conecta o que já existia.

**Achado 2 (sério) — `trials_gate.trials_path_from` sem variável de
ambiente de override, ao contrário de `db.py`/`report.py`.** Descoberto
testando o achado 1: meu próprio teste do dispatcher, rodado via
subprocess, ESCREVEU no `trials.json` REAL do repo (adicionou de volta o
campo `pipeline_fingerprint` que a errata de 2026-09-03 tinha removido) —
porque não havia como isolar o path por variável de ambiente, só passando
`trials_path=` explícito em código Python direto (impossível via
subprocess/CLI). Revertido (`git checkout -- trials.json`, confirmado
limpo) antes de qualquer commit. Corrigido: `trials_gate.TRIALS_PATH_ENV`
("PREDICTOR_TRIALS_PATH"), mesma precedência de `db.DB_PATH_ENV`
(override explícito > env var > config > default). Teste novo:
`test_trials_path_from_honors_env_var`; o teste do dispatcher (achado 1)
agora isola via essa env var.

**Achado 3 — `economic_gate.py` órfão, nunca importado por nenhum outro
módulo.** Gate econômico REBALANCE/HOLD completo e testado
(`tests/test_economic_gate.py`), mas `paper.py` (M6) nunca o chama — a
liquidação de execuções grava `realized_return_net`, mas nada decide se
esse edge "paga" turnover+hurdle pra habilitar capital. **Não conectado
nesta rodada**: com 16/16 hipóteses NOT_SUPPORTED, não há edge real pra
gatear — conectar o gate agora seria infraestrutura para uma capacidade
sem sinal nenhum pra usar (documentado, não implementado; decisão
consciente de não fazer trabalho sem propósito no momento presente).

**Achado 4 — `purge_embargo_months` declarado mas nunca consumido.** Já
documentado e decidido em `RESEARCH_FREEZE.md` §4 como
`DOCUMENTED_HISTORICAL_LIMITATION` (2026-09-02) — implementar
retroativamente contaria como ajustar metodologia depois de já ter
vereditos, proibido pelo próprio design. Confirmado ainda válido,
nenhuma ação (a decisão já está tomada e registrada).

Suite completa (sandbox): 324 passed, 1 skipped, 6 failed — mesmos 6
pré-existentes do shim de vendor, não relacionados. `trials.json` real
confirmado intocado (`md5sum` antes/depois idêntico) após a correção do
achado 2.

---

## H17, H18 e H19 ABERTAS — PRÉ-REGISTRO (2026-09-04, ANTES de qualquer rodada real)

Decisão explícita do operador ("abre as duas, A e B") após a varredura que
confirmou o esgotamento das duas linhas anteriores (16/16 NOT_SUPPORTED).
Como sempre: cada hipótese é testada UMA vez, julgada UMA vez.

**Por que estas três NÃO são recombinação do que já foi observado.** As 16
anteriores esgotaram (a) a DFP consolidada em regime de COMPETÊNCIA
(BPA/BPP/DRE — ROE, alavancagem, margem, crescimento e interseções) e (b) o
COTAHIST (momentum, reversão, vol, proximidade de máxima, volume,
calendário). As três abaixo entram por FONTE DE DADO NOVA, não por novo
arranjo dos mesmos números — que seria o p-hacking recusado explicitamente
na sessão anterior e que o pedágio IC95%+DSR existe para barrar.

### H17 — accruals / qualidade do lucro (Sloan 1996)

`config.yaml` `h17_*`, `config.h17_frozen_config_hash` = `aece696b814c0fd9`.

Quintil **INFERIOR** de `(lucro_liquido − fluxo_caixa_operacional)/ativo_total`
(`factor.accruals_signals`). Direção fixada ANTES da rodada: accrual baixo =
lucro lastreado em caixa. A literatura prevê que accrual ALTO antecede
retorno futuro BAIXO; testar as duas pontas e ficar com a que der seria
exatamente o que o pedágio impede.

**Dado novo:** `dfp_cia_aberta_DFC_MI_con_YYYY.csv` — a Demonstração de Fluxo
de Caixa (método indireto, consolidada). Ela já vinha DENTRO do zip DFP que o
`ingest_cvm.py` baixa desde a H7, mas o parser nunca abriu esse arquivo. É a
primeira demonstração nova ingerida desde o M2. BPA, BPP e DRE são todas de
COMPETÊNCIA — o mesmo regime contábil, com os mesmos graus de liberdade de
reconhecimento; a DFC é de CAIXA, e nenhuma combinação das outras três a
reconstrói. `RESEARCH_FREEZE.md` §11 nomeia "fluxo de caixa" como fonte
materialmente nova admissível.

### H18 — valor por earnings yield (Basu 1977; Fama & French 1992)

`config.yaml` `h18_*`, `config.h18_frozen_config_hash` = `dded266f1bb712f1`.

Quintil **SUPERIOR** de `E/P = lucro_liquido/(preço_cru × ações)`
(`factor.earnings_yield_signals`) — E/P alto = mais barato.

**PRIMEIRO fator de VALOR do domínio.** Dezesseis hipóteses julgadas e
nenhuma mediu o PREÇO PAGO pelo fundamento: H7/H9/H12/H13 medem a qualidade
do negócio, momentum/H14/H15 medem o comportamento do preço, mas ninguém
mediu a RAZÃO entre os dois. É a lacuna mais visível do domínio contra a
literatura.

**Dado novo:** `fundamentals.shares_outstanding` (migração 0011). O parser do
FRE (`parse_fre_float_rows`) já lia a quantidade de ações desde a família
`liquidity`, mas o valor era transitório e era jogado fora. Sem ele não há
capitalização de mercado, logo não há múltiplo nenhum — é a peça que faltava.

Usa-se E/P e não P/L de propósito: P/L explode quando o lucro tende a zero e
é indefinido com prejuízo, o que faria o RANKING depender de um polo
instável. E/P é monotônico e finito no domínio admitido (lucro > 0).

### H19 — valor por book-to-market (Fama & French 1992)

`config.yaml` `h19_*`, `config.h19_frozen_config_hash` = `dabaa53adc9b9349`.

Quintil **SUPERIOR** de `B/M = patrimonio_liquido/(preço_cru × ações)`
(`factor.book_to_market_signals`).

**Por que é hipótese SEPARADA da H18, e não a mesma coisa medida duas
vezes** (decisão explícita, registrada para não ser lida como inflação de
tentativas): E/P ancora no FLUXO de um único exercício — lucro é volátil e
sensível a itens não recorrentes; B/M ancora no ESTOQUE acumulado —
patrimônio líquido é estável. É precisamente por isso que Fama & French
construíram o HML sobre B/M e não sobre E/P. Rodar as duas e reportar a que
passar seria p-hacking; por isso cada uma tem seu próprio lacre, seu próprio
registro e seu próprio N no DSR (H19 entra com N=19, não 18).

**Nota ao operador:** o pedido original tratava "valor" como uma coisa só.
Ele se divide necessariamente em duas tentativas sob a disciplina do
projeto — o N do DSR sobe para 19 e o limiar fica mais duro. Rodar só a H18
e deixar a H19 pré-registrada mas não executada é uma opção legítima; o que
NÃO é legítimo é rodar as duas e reportar uma.

### Critério (as três)

IC95% diff-Sharpe > 0 **E** DSR >= 0,95 — H17 N=17, H18 N=18, H19 N=19.

### Implementação

- `db.py` migração **0011_fundamentals_cashflow_shares** (append-only):
  `fluxo_caixa_operacional`, `accruals`, `shares_outstanding` em
  `fundamentals`. Migrações 0007/0010 intocadas.
- `ingest_cvm.py`: constantes `_CASHFLOW_OPS_CODE` (6.01) /
  `_CASHFLOW_OPS_KEYWORDS_ALL`, cruzando código E descrição como todas as
  outras contas. `compute_fundamentals` ganha o parâmetro OPCIONAL
  `dfc_rows` (default `None` — chamador antigo recebe exatamente as linhas
  de antes, com os campos novos em `None`; H7-H16 não mudam de
  comportamento). Grupo de elegibilidade próprio para accruals, como já
  valia para receita/margem.
- `ingest_cvm.ingest_dfp_year`: abre a DFC-MI. **Ausência do arquivo é
  tolerada com aviso, não fail-loud** — a companhia pode publicar pelo
  método DIRETO (DFC-MD) e anos antigos podem não trazê-lo; nesse caso
  `accruals` fica NULL e os papéis ficam fora do sinal, com o resto da
  ingestão intacto.
- `ingest_cvm.ingest_fre_shares_year` (novo): persiste `shares_outstanding`
  com `source = "CVM FRE {year}"` e a `ref_date` DO PRÓPRIO FRE. **Decisão
  deliberada: as datas de DFP e FRE NÃO são casadas à força.** São
  formulários distintos, com datas de referência e de entrega distintas;
  alinhá-los por ano-calendário produziria uma capitalização de mercado com
  data errada — lookahead sutil e silencioso. Cada fonte é resolvida pelo
  seu próprio embargo, e a junção acontece só no momento do sinal.
- `factor.accruals_signals` (H17): motor comum `_fundamental_signals`,
  mesmo embargo de H7/H9/H12/H13.
- `factor._price_at` + `_value_signals` + `earnings_yield_signals` /
  `book_to_market_signals` (H18/H19). **O preço do múltiplo é CRU**
  (corrigido só pelo fator de cotação da B3), não a série ajustada:
  multiplicar a série retro-ajustada pela contagem de ações vigente daria
  uma capitalização de mercado que nunca existiu, e o erro cresce quanto
  mais para trás se olha. Para RETORNO a série ajustada continua sendo a
  correta em todas as hipóteses; para NÍVEL DE PREÇO num múltiplo, é a crua.
  Fundamento <= 0 (prejuízo, PL negativo) fica FORA — o múltiplo inverte de
  sinal e a empresa apareceria como "baratíssima" no ranking; mesma
  disciplina do ROE sobre PL negativo.
- `backtest.run_h17`/`run_h18`/`run_h19`: mesmo runner genérico
  `_run_hypothesis` (`walk_forward`). `take="bottom"` na H17, `"top"` nas
  outras duas. Nenhuma mudança na maquinaria compartilhada.
- `config.yaml`/`config.py`: `h17_*`/`h18_*`/`h19_*` com
  `[H17-FROZEN]`/`[H18-FROZEN]`/`[H19-FROZEN]`.
- `report._BIAS_NOTE["H17"]/["H18"]/["H19"]`. Ponto importante em H18/H19:
  a direção do viés É conhecida e **PENALIZA** a estratégia — ações de valor
  têm sistematicamente maior dividend yield e a rota (b) descarta justamente
  esse componente. O teste é CONSERVADOR: um NOT_SUPPORTED ali não separa
  "o fator não funciona" de "o retorno do fator está no provento que esta
  rota não mede". Declarado agora, não descoberto depois.
- `main.py`: nenhuma mudança necessária — o dispatcher `backtest-h <N>`
  (revisão de infraestrutura 2026-09-04) já é genérico.
- Testes novos: `tests/test_h17_accruals.py` (8 casos),
  `tests/test_h18_h19_value.py` (15 casos) — smoke, golden hash, hash ignora
  parâmetro operacional, direção pré-registrada, embargo bloqueando `asof`
  cedo, fator de cotação, point-in-time do preço, exclusão por fundamento
  não-positivo e por ações ausentes, idempotência da ingestão do FRE.

Suíte completa: **354 passed** (331 antes desta rodada, +23 novos), zero
falhas, nenhuma regressão em H1-H16.

### Dependências

Nenhuma nova. Continua stdlib + `pyyaml`.

### Próximo passo (máquina do operador)

Ao contrário de H14-H16, **estas exigem ingestão nova** — o dado não está no
banco atual.

```
python -m pytest tests/ -v                      # confirmar verde total
python main.py backtest-h 17
python main.py backtest-h 18
python main.py backtest-h 19                    # opcional; ver "Nota ao operador"
```

Antes das rodadas é preciso re-executar a ingestão da DFP (para popular
`fluxo_caixa_operacional`/`accruals` via DFC-MI) e a nova
`ingest_fre_shares_year` (para popular `shares_outstanding`) nos anos da
janela. A migração 0011 roda sozinha na primeira conexão; as colunas ficam
NULL até a ingestão rodar, e um `run_hN` com as colunas vazias produz
universo vazio — **checar a contagem de papéis por rebalance antes de
interpretar qualquer veredito**, especialmente na H17, cujo universo efetivo
pode ser menor que o de H7/H9/H12/H13 por causa da cobertura parcial da
DFC-MI.
