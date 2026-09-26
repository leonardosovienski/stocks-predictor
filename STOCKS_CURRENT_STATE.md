# Estado atual do Stocks Predictor

## Protocolo de avaliação v2 e série de prompts — 24 e 25/09/2026

Toda avaliação nova usa o pacote aditivo `stocks_predictor/v2`
([contratos, uso e dívida técnica](docs/engineering/2026-09-24-protocol-v2/README.md)). Motores legados,
circuito `research_*` e vereditos congelados não mudaram. Série executada, um prompt por vez: Prompt 1, portão de
segredos liberado (PR #98); 2, auditoria (#99); 3a, protocolo v2 (#100); 3b, validação estatística (#101); 3c,
previsão e execução real (#102 e #103); 4, reavaliação e integridade experimental (#104). A
[revisão de coerência de 25/09](docs/evidence/2026-09-25-revisao-completa.md) corrigiu a governança e registrou a
[auditoria dos prompts](docs/continuation/2026-09-25-serie-stocks-revisada.md).

- **3c, COTAHIST 2026 (172 pregões; janela 2026-04-07 a 2026-09-09; CDI SGS 12):** o `chronos-bolt-small`
  zero-shot teve CRPS 0,0722, contra 0,0602 do passeio aleatório gaussiano (19,9% pior, 747 tarefas). A amostra é
  insuficiente para o poder desenhado (n necessário 1552), então o status é `INSUFFICIENT_SAMPLE`, não uma
  conclusão. A carteira pelo ranking do modelo teve Sharpe líquido em excesso do CDI de −1,68, contra −1,69 da EW
  e −0,74 do fundo de índice. Nenhuma decisão: amostra abaixo de 504 pregões, DSR e PBO não estimáveis.
- **4:** 15 vereditos históricos reavaliados sem reexecução, com N conhecido = 102 (grade 102/150/204/510). Todos
  seguem `NOT_SUPPORTED`; a régua nova é mais conservadora. Nenhuma hipótese foi aprovada.
- **Política de decisão** [v1](policy/stocks-evaluation-policy-v1.json): `PROPOSED_PENDING_OWNER_APPROVAL`.
  Desde 25/09, política não aprovada nunca decide: toda decisão é `NO_DECISION` e `decision_if_approved` registra o
  que os limiares decidiriam. Os 8 registros `DECISION` anteriores já eram `NO_DECISION`.
- **Holdout prospectivo selado** de 2026-09-10 a 2027-09-10 (selo `d2fc50e7…`). Abre só com aprovação humana
  registrada. Até lá, toda avaliação cujo dataset ou janela alcance 2026-09-10 é recusada.
- **Ledger de domínio:** fica no PC 2, fora do Git, com 56 registros. O
  [índice verificável](docs/engineering/2026-09-24-protocol-v2/evidence/ledger/stocks-domain-ledger-index.json)
  tem os hashes da cadeia e nenhum dado de processo.
- **Leitura pela CAIN (26/09):** o estado da pesquisa está em
  [`research/scientific_state.json`](research/scientific_state.json), gerado das fontes e conferido por teste.
  A CAIN lê esse arquivo, o `trials_v2.json` e o índice do ledger num commit fixado, sem preços
  ([contrato](docs/engineering/2026-09-26-cain-findings/README.md)).
- **Qualificação:** o runtime qualificado continua `61fc017` / wheel 0.3.0rc2. O pacote v2 é código posterior e
  **não está qualificado**; requalificar (C14) é decisão do dono. Os achados ST-F007 e ST-F008 passam a
  `ACCEPTED_BY_OWNER` (D-21) na
  [PR #48 do predictor-qualification](https://github.com/leonardosovienski/predictor-qualification/pull/48).
- **Decisões pendentes do dono:** aprovar ou alterar os limiares da política v1; requalificar o v2; reabrir família
  encerrada, só pela `reopen_policy` do [congelamento](RESEARCH_FREEZE.md).

## Candidato EXTERNAL_INTELLIGENCE_V1 — 20/09/2026

Foi implementada uma fundação aditiva de staging B3/CVM com raw por SHA-256, versionamento imutável,
PIT/identidade/lineage, CLI, receipts, verify/status e compatibilidade Ops não ativada. Consulte
[docs/external_intelligence/REPORT.md](docs/external_intelligence/REPORT.md). Ela não altera
BIG_WINNER_V2, fatores, ranking, portfólio ou publicação CAIN. Estados científico e econômico:
`NOT_EVALUATED`.

> **Continuidade vigente:** [auditoria de integração e consolidação](docs/INTEGRATION_AUDIT_20260912.md). Notas datadas abaixo são históricas; publicação e aceite devem ser conferidos pelo SHA e pelos recibos atuais.


## Entrega arquitetural publicada — 11/09/2026

Versão **0.2.0** publicada: [release e artefatos](https://github.com/leonardosovienski/stocks-predictor/releases/tag/v0.2.0). [CI de engenharia aprovada](https://github.com/leonardosovienski/stocks-predictor/actions/runs/34629227472) para a fonte `56c1a7b8db33f15404342fc61cceaa64452517d5`. Consulte [ARCHITECTURE_IMPLEMENTATION.md](ARCHITECTURE_IMPLEMENTATION.md) para comportamento, migração e limites. Este registro atualiza a entrega de software; estados científicos e registros datados abaixo conservam sua autoridade e contexto histórico.

Estado atualizado em 11/09/2026. A infraestrutura está validada para pesquisa
em lote em um host/disco local. **O pedido econômico integral permanece aberto;
lucro líquido pessoal executável ou futuro não foi demonstrado.**

[Mandato integral](docs/continuation/PROMPT_AUDITORIA_INTEGRAL_20260909.md),
[encerramento R8](docs/continuation/2026-09-10-closure/README.md),
[revisão de arquivos](docs/maintenance/2026-09-10-files/README.md) e
[índice completo](docs/DOCUMENTATION_INDEX.md).

## Prontidão por uso

A iniciativa [OSS-20260911-01](docs/open_source_research/OSS-20260911-01/closure/REPORT.md)
terminou com cinco protótipos stdlib executados: fit temporal, ranking por data,
neutralização por grupo, participação ordem/volume e alocação com limite de giro.
Quatro são candidatos de engenharia; o último permanece experimental após
contraexemplo de reversão. Os recibos registram 33 checks e 40 comparações de
custos; nenhum benchmark econômico B3 novo. Código e evidências foram salvos
no commit `860996d`, sem integração no runtime. X05 continua bloqueado pelo
painel comum de inputs PIT e labels econômicos completos. UNC02 e TOTS3 mantêm
seus resultados e UNKNOWNs originais. Ver a [retomada](HANDOFF.md).

| Uso | Estado e limite |
|---|---|
| Diagnóstico e pesquisa histórica | Funcionais no runtime suportado, com gates de dados e evidência |
| Banco gerido e fontes versionadas | Ingestão por hash, replay, inspeção, backup e restauração testados; não mistura versões nem substitui bancos legados |
| Capacidade e recuperação | 250 mil linhas sintéticas e 55.986 preços reais; concorrência, WAL, morte de processo e falhas testados; sem certificação de falha física do host |
| Reprodução H21/H20 | Histórica, com escopo e entradas preservados; não é nova evidência independente |
| Retorno líquido pessoal e operação real | Não aptos: custos, eventos, cenário pessoal e observações insuficientes |
| Backup externo e produção distribuída | Não implantados; RPO limitado ao último snapshot local concluído |

## Dados e hipóteses

- Capital confirmado: R$5.000. Demais premissas pessoais continuam desconhecidas.
- R6 recuperou os cinco objetos antes ausentes; 1.448 arquivos do pacote original
  conferidos. O erro estrito de float de 2,22e-16 permanece documentado.
- 12 bancos originais preservados, com funções e hashes distintos. Integridade
  física não certifica cobertura econômica. Fonte15 é separada das revisões 13/14.
- Persistem 50 valores líquidos, 22 datas de pagamento e 28 registros societários
  incompletos. As contagens se sobrepõem; não significam ausência de todos os preços.
- H22: 24 avaliações, 22 calculadas e duas inviáveis; rejeição nos 11 pares calculáveis.
- H21: lucro histórico condicional, não lucro pessoal executável/futuro certificado.
  [Plano prospectivo](docs/research/2026-09-09-h21-forward-plan.json) fixado até
  primeira sessão em/após 10/09/2027, sem observações concluídas nem ordens.
- [R7](docs/audit/2026-09-10-r7/CONSOLIDADO.md) preserva 75 itens e 1.590 ocorrências
  sobrepostas. I15/arquivos e omissão PR75 resolvidos; I10–I14/I16 permanecem limitados.
- Licenças de 792 documentos individuais e disponibilidade histórica ampla não
  foram certificadas. A licença de uma base não se transfere automaticamente a seus PDFs.

## Evidência técnica

Runtime Linux/Python 3.13/3.14, Core 3.2.0 travado; tipagem/lint, piso de cobertura
77%, build reproduzível e teste do wheel fora do checkout. CI232 do merge
`bf7b3bc` aprovou 891 testes ativos + 17 históricos + 63 subtests por runtime;
cobertura exibida 80%/79%, sem somar versões ou tratar subtests como provas independentes.
Para qualquer commit posterior, consultar a CI correspondente.

O scanner verifica a árvore completa, inclusive merges, e um controle sintético.
A entrada operacional é `python -m stocks_predictor`; ver [runbook](docs/engineering/2026-09-10-r8/RUNBOOK.md).
Neste Windows, não instalar o runtime de produção nem criar venv.

O [estado anterior completo](https://github.com/leonardosovienski/stocks-predictor/blob/bf7b3bc9f888dc94fd186646424159f31682b747/STOCKS_CURRENT_STATE.md)
permanece no Git com suas datas. A [continuidade](HANDOFF.md) define a retomada.
