# Auditoria dos prompts do stocks — 25/09/2026

Revisão, depois da execução, dos prompts usados nas sessões de 24 e 25/09/2026. São dois conjuntos: a série
1 → 2 → 3a → 3b → 3c → 4 (PRs #98 a #104) e a missão noturna D-16 (`~/predictors/noite/prompts/stocks.md` +
`COMUM.md`, fora deste repositório). Cada item diz o que o texto pedia, o que a execução mostrou e a correção. Os
prompts originais não foram editados. Os arquivos da noite pertencem ao workspace do dono, e o `prompts-cain.md` é
de outra sessão. As versões corrigidas estão aqui para a próxima rodada.

## 1. Série 1 → 4

### Objetivo recuperado

Levar o stocks ao mesmo padrão do cripto sem reabrir a busca:

- segredos conferidos antes de tudo;
- auditoria somente leitura;
- protocolo novo, com PIT, custos, baselines, CPCV, DSR/PBO e política versionada;
- modelo fundacional só com licença e contaminação controladas;
- reavaliação das hipóteses sem variantes novas.

A ordem é obrigatória e cada prompt é colado sozinho.

### Lacunas que a execução expôs

| # | Prompt | Texto original | O que aconteceu | Correção |
|---|---|---|---|---|
| 1 | 2, 3a–3c | "suíte isolada de rede e segredos" | A suíte recusa checkout sujo: arquivo não rastreado conta. Uma rodada deu 23 × `DirtyWorkingTreeError`. | Rodar a suíte só depois do commit, com a árvore limpa, sem escrever no checkout durante a rodada. |
| 2 | 3a–4 | Não cita as regras locais do repositório | O `AGENTS.md` exige novos recibos R8 a cada mudança no pacote, e isso só foi descoberto no CI. | Ler o `AGENTS.md` antes de alterar código; R8 e índice documental fazem parte da entrega. |
| 3 | todos | "salve em docs/evidence/…" sem regra de PR | O merge da PR #102 aconteceu enquanto commits do 3c ainda subiam; foi preciso abrir a #103. | Um PR por prompt, base `main`. Antes de cada push, conferir se o PR ainda está aberto. Não declarar a etapa entregue antes do CI verde. |
| 4 | 3b | Limiares no arquivo de política, versão e hash em toda decisão | Ninguém definia quem aprova os limiares nem o que vale enquanto não aprovados. Decisões foram emitidas com a política `PROPOSED`. Todas deram `NO_DECISION` por outros motivos, mas nada impedia um `PASS`. | Política criada pelo agente nasce `PROPOSED_PENDING_OWNER_APPROVAL`. Enquanto não aprovada, toda decisão é `NO_DECISION`, com o hipotético registrado à parte. A aprovação nomeia versão e sha256. |
| 5 | 4 | Pré-registro e holdout "gravados no TrialLedger" | A primeira implementação só gravava: nada impedia um backtest sem pré-registro nem uma consulta ao holdout selado. | Exigir aplicação no caminho da avaliação, com teste que prove a recusa. |
| 6 | 3c | Tabela com coluna `decision` para todo candidato | Os próprios baselines receberam decisão (seqs 23/24 e 38/39 do ledger: "sem comparação com baseline" sobre o próprio baseline). | `decision` só para candidatos; previsores e referências ficam `N/A`. |
| 7 | 3c | "Reporte tamanho de amostra pós-corte e estimativa de poder" | Faltava o efeito que o poder mede. Ele foi fixado na especificação antes da execução (α 0,05, poder 0,8, melhoria relativa mínima de 5%). | Declarar α, poder e efeito mínimo na especificação versionada, antes. |
| 8 | 4 | "Se precisar baixar dados, PARE e pergunte" | O COTAHIST 2019–2025 foi autorizado e baixado, mas o próprio Prompt 4 proíbe reexecutar hipótese encerrada: não havia uso permitido. | Antes de pedir download, mostrar que o uso é permitido pelo princípio da etapa. |
| 9 | 3a | Campos do manifesto | O `STARTED` gravava o hostname. O ledger fica fora do Git, mas o risco estava no formato. | Nenhum dado da máquina ou pessoal em artefato: `host_id` com hash. Caminhos absolutos seguem a prática do repositório (193 arquivos desde 02/09); mudar isso é decisão do dono. |
| 10 | 4 | "abrir exige aprovação humana registrada" | Uma resposta de uma palavra ("aprovadp") não diz o que foi aprovado. O status da política não foi mudado. | Aprovação precisa nomear o objeto: "aprovo a política 1.0.0, sha256 `4898b7c7…`". |

Os pontos 1, 2, 3 e 8 são de processo e entram no bloco comum. Os pontos 4, 5, 6 e 9 viraram código nesta revisão
([relatório](../evidence/2026-09-25-revisao-completa.md)). Os pontos 7 e 10 são texto de prompt.

### Bloco comum revisado

Substitui "CONVENÇÕES E REGRAS: as mesmas do 3a". Como cada prompt é colado sozinho, o bloco vai inteiro em cada
um. Os prompts 1 e 2 continuam somente leitura e só levam as convenções e a regra de segredos.

```text
CONVENÇÕES E REGRAS
- PROVEN / DECLARED / UNKNOWN; cite arquivo:linha, commit, teste, comando, run_id; nunca promova por inferência.
- Nunca exponha credenciais, tokens, chaves, cookies, URLs assinadas, valores de variáveis secretas, hostname,
  usuário ou outro dado da máquina em artefato versionado.
- Leia o AGENTS.md do repositório antes de alterar código e siga as regras locais (ex.: recibos R8 para toda
  mudança no pacote; índice documental ao adicionar Markdown).
- Mudanças pequenas e testadas; sem refatoração fora do escopo; não desative testes nem afrouxe validações.
- Execução local. Nenhuma credencial. Nenhuma ordem, nem em conta simulada do broker.
- DADOS: só locais, versionados e com hash. Se precisar baixar, PARE e pergunte, dizendo o que, de onde, o tamanho
  e por que o uso é permitido pelas regras desta etapa.
- Não altere resultados históricos. Não escolha período, limiar ou efeito mínimo depois de ver resultado:
  declare-os numa especificação versionada antes.
- Política de decisão criada aqui nasce PROPOSED_PENDING_OWNER_APPROVAL; enquanto não aprovada, nenhuma execução
  decide (NO_DECISION, com o hipotético registrado). Aprovação do dono nomeia versão e sha256.
- Antes de adicionar biblioteca: já é dependência? licença efetiva? versão fixada? fonte registrada?
- Suíte: rode só com a árvore limpa (faça o commit antes; arquivo não rastreado também suja), isolada de rede
  e segredos, e não escreva no checkout durante a rodada.
- Git: um PR por prompt, base main. Antes de cada push, confira se o PR ainda está aberto. A etapa só termina com
  CI verde.
```

### Deltas por prompt

- **3b, item 6**, acrescentar: "A política nunca decide sobre o próprio baseline. Teste que prove que política não
  aprovada devolve `NO_DECISION`."
- **3c, item 2**, trocar "Reporte tamanho de amostra pós-corte e estimativa de poder" por: "Declare antes, na
  especificação versionada, α, poder e efeito mínimo detectável; reporte o n pós-corte e o n necessário."
- **3c, ENTREGA**, acrescentar: "`decision` só para carteiras candidatas; previsores e baselines: N/A."
- **4, itens 5 e 6**, acrescentar: "A avaliação recusa hipótese nova sem pré-registro, variante além do máximo e
  qualquer dado do holdout selado antes da abertura; depois dela, uma consulta por hipótese pré-registrada antes da
  abertura. Testes provam cada recusa."
- **4, item 3**, acrescentar: "Não peça download para hipótese encerrada: a régua nova se aplica ao artefato
  versionado."

## 2. Missão noturna D-16 (`stocks.md` + `COMUM.md`)

### Objetivo recuperado

Fechar os 4 gates bloqueados pela D-16 com dados públicos, sem tocar critérios congelados. A missão terminou
`CONCLUIDO`, com as PRs #20, #21, #31, #36 e #37 do `predictor-qualification`.

### Lacunas

| # | Texto original | O que aconteceu | Correção |
|---|---|---|---|
| 1 | "Critérios, perfil, seeds e vetores continuam intocados (C15)" | O parâmetro congelado pede rebalance no "fim de mês", mas o código só aceita "a cada N pregões". Foram usados 21 pregões, declarados antes da execução. Virou o achado ST-F007, aceito na D-21. | Pré-voo: antes de executar, conferir se cada parâmetro congelado é representável no código. Se não for, registrar o substituto antes da execução e marcar como decisão do dono. |
| 2 | "o do ano corrente (`COTAHIST_A2026.ZIP`) muda todo dia útil" | Outras respostas da B3 também mudam. A de proventos de `ALOS` mudou depois do pin, e o workflow disparado por push ficou vermelho sem significado. A PR #21 deixou o disparo só manual. | "Toda fonte sem versão imutável é snapshot: fixe sha256 e data. O workflow que baixa só roda por `workflow_dispatch`, nunca em push." |
| 3 | "Nunca apague branches" (`COMUM.md`) | Nesta revisão de 25/09, apaguei a branch local temporária `review-tmp`, sem commits próprios e apontando para `origin/main`. Não houve perda de trabalho, mas a regra foi violada. | A regra continua valendo. Branch temporária não deve ser criada; use worktree com branch de trabalho definitiva. |
| 4 | "Python: só o gerenciado… venvs só a partir de `uv.lock`" | O venv do Chronos (3c) foi criado fora do `uv.lock`, isolado em `~/predictors/runtime/stocks/chronos-venv`, com `freeze` versionado. | Não há conflito real: a regra é das sessões da noite, e a série posterior autorizou o venv isolado. Na próxima série, explicitar a exceção. |
| 5 | ST-F007 e ST-F008 tratados só no relatório da noite | A D-21 aceitou os dois, mas o `FINDINGS.json` ficou `OPEN`, e isso só foi percebido nesta revisão. | "Toda decisão do dono que resolve um achado atualiza `FINDINGS.json`, `GATES.json` e a attestation no mesmo PR." Feito agora na PR #48 do `predictor-qualification`. |
