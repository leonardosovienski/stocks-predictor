## Operação R8 — 10/09/2026 UTC

[Relatório operacional](engineering/2026-09-10-r8/README.md) e
[runbook](engineering/2026-09-10-r8/RUNBOOK.md).
Entrada instalada: `python -m stocks_predictor`; no checkout: `python main.py ops`.
Banco gerido separado, ingestão por hash, inspeção por versão, backup e restauração.
O escopo é pesquisa local em lote; fontes/custos/observação futura ainda pendentes.
R7 mantém o inventário econômico e os recibos históricos. Os blocos abaixo são datados.

## Índice vigente R7 — 10/09/2026 UTC

[Relatório](audit/2026-09-10-r7/README.md), [consolidado](audit/2026-09-10-r7/CONSOLIDADO.md),
[registro atual](audit/2026-09-10-r7/current.json), [reprodução](audit/2026-09-10-r7/REPRODUCTION.md),
[revisão das fontes](audit/2026-09-10-r7/SOURCE_REVIEW.md),
[condições de uso](audit/2026-09-10-r7/SOURCE_RIGHTS.md).
Os registros históricos abaixo são preservados com suas datas.

## Dados R6 — 10/09/2026 UTC

[Relatório vigente](research/2026-09-10-r6/README.md),
[recibos](research/2026-09-10-r6/manifest.json) e
[reprodução](../research/session-20260910/gap_resolution/README.md).
Cinco objetos recuperados; 1.448 arquivos verificados; fonte de preços até 09/09;
fonte 15 com duas datas e dois líquidos corrigidos. Demais lacunas permanecem explícitas.

## Pesquisa econômica R5 — 10/09/2026 UTC

O usuário reabriu a pesquisa em busca de lucro validado, com liberdade sobre hipóteses
e arquitetura. [R5/H22](research/2026-09-10-r5/README.md) executou uma regra mensal
de dez meses, registrada antes de medir, e uma alternativa de comprar e manter.
24 avaliações: 22 calculadas/reconciliadas e duas inviáveis; H22 rejeitada, sem
incremento positivo nos 11 pares calculáveis. Ganho nominal da alternativa simples
permanece condicional a eventos/custos. Lucro integral ou futuro não demonstrado.
Demonstrações2024 e AGO2025 recuperadas; fontes/livros anteriores preservados.
[PR76](https://github.com/leonardosovienski/stocks-predictor/pull/76) contém a integração
com testes e checks por SHA. O objetivo econômico permanece não atingido; as
restrições antigas de fila/coleta não substituem a nova autorização do usuário.
Não transformar busca repetida na mesma história em validação futura.

---

# Índice documental — engenharia R4 de 10/09/2026 UTC

Leitura de engenharia atual: [relatório, mudanças e reprodução](engineering/2026-09-10-r4/README.md),
[manifesto dos recibos](engineering/2026-09-10-r4/manifest.json) e
[PR75](https://github.com/leonardosovienski/stocks-predictor/pull/75).
A auditoria R3 abaixo permanece a referência econômica e documental, com a data
da sua execução. R4 não reabre hipóteses nem coleta de mercado.

---

# Índice documental — auditoria integral de10/09/2026 UTC

Leitura corrente: [relatório A–R](audit/2026-09-10-integral/README.md), [registro canônico](audit/2026-09-10-integral/registry.json), [reprodução](../research/session-20260910/integral/README.md). O registro vincula claims,16achados/lacunas,24frentes, dados, decisões, execuções e sete usos. I01–I09 corrigidos; I10–I16 delimitam as dependências. H21 condicional e H20 amplo estacionado. PR74 registra integração e CI final.

Os índices abaixo preservam a história anterior à execução da auditoria.

---

# Índice documental — revisão de 09/09/2026

Continuidade mais recente: [prompt completo da auditoria integral](continuation/PROMPT_AUDITORIA_INTEGRAL_20260909.md)
e [pacote de publicação da sessão](../research/session-20260909/publication/README.md).
A auditoria foi preparada, mas não executada. O pacote publica artefatos autorais
que antes estavam apenas na raiz local e registra separadamente os dados brutos
não publicados. As contagens e descrições abaixo preservam suas datas e escopos.

Complemento mais recente no mesmo dia, R2:
[dados/fontes](research/2026-09-09-data-completion-r2.md),
[catálogo de prontidão](research/2026-09-09-data-readiness.json),
[eventos](research/2026-09-09-bova-event-review-r2.json),
[entradas operacionais](research/2026-09-09-operational-inputs-r2.json) e
[inventário das aquisições](research/2026-09-09-source-inventory-r2.json), além da
[recuperação/auditoria](../research/session-20260909/data_completion/README.md).
Os 12 bancos únicos e as fontes 13/14 já foram recuperados, sem ativação operacional.
Na raiz local, `data/README.md` explica `data/CATALOG.json`; os Markdown originais
dos pacotes recuperados preservam seu contexto histórico. As contagens abaixo são
do inventário inicial, não do acervo ampliado. Recibo R2:
`C:\STOCKS\outputs\ENTREGA_DADOS_FONTES_R2_20260909.json`.

Complemento anterior no mesmo dia, R1:
[fontes/custos H21](research/2026-09-09-h21-source-closure.md) e
[reprodução da atualização](../research/session-20260909/source_closure/README.md).
São dois Markdown novos, além do inventário inicial e deste índice.
README, AGENTS, estado atual, HANDOFF e prompt de continuidade receberam o
estado dessa rodada; históricos e documentos congelados continuam preservados.
O recibo final fica em `C:\STOCKS\outputs\ENTREGA_FONTES_H21_20260909.json`.

A revisão inventariou e varreu os **94 Markdown existentes em C:\STOCKS**:
caminhos, referências locais, estado da pesquisa, runtime, contagens de testes
e instruções conflitantes. Este índice é um arquivo novo, além dos 94 iniciais.
Não é nova auditoria científica ou recertificação de afirmações históricas.

## Leitura vigente

1. [AGENTS](../AGENTS.md) e [README](../README.md).
2. Início de [STOCKS_CURRENT_STATE](../STOCKS_CURRENT_STATE.md) e [HANDOFF](../HANDOFF.md).
3. [Mandato integral da próxima auditoria](continuation/PROMPT_AUDITORIA_INTEGRAL_20260909.md),
   [mandato econômico original](continuation/MANDATO_20260909.md) e
   [prompt anterior como contexto histórico](continuation/PROMPT_NOVO_CHAT.md).
4. [Relatório H21 com complemento final](research/2026-09-09-h21-results.md) e
   [reprodução H21](../research/session-20260909/h21/README.md).
5. [Relatório e pendências R2](research/2026-09-09-data-completion-r2.md),
   [catálogo](research/2026-09-09-data-readiness.json) e
   [mapa local](continuation/LOCAL_PATHS_20260909.json).

A raiz local única é `C:\STOCKS`; código em `stocks-predictor`, pesquisa/logs em
`work`, entregas em `outputs`. Não usar antigos destinos em Superleo13 ou no chat.
Runtime instalado do Codex e GitHub são recursos externos do ambiente/remoto.

A referência integrada H21 é `4a85d43`, com CI184: 782 testes regulares,
Python 3.13.15/Core 3.2.0 no Linux, cobertura 78%; 17 testes arquivados excluídos.
O SHA e a CI de uma revisão posterior devem ser conferidos separadamente.
A H21 continua inconclusiva para lucro executável, e seu plano futuro está
registrado, sem observações. H20 fica estacionada para reconstrução ampla.

## Como interpretar o acervo

- **ATUAL:** instruções corrigidas ou conferidas para este computador.
- **ATUAL_COM_HISTORICO:** o primeiro bloco é vigente; depois do separador,
  a narrativa e os comandos pertencem às respectivas versões.
- **MANDATO_ORIGINAL_VIGENTE:** prompt do usuário mantido byte a byte;
  seus dados de partida não substituem o estado verificado após a execução.
- **PROTOCOLO_HISTORICO_CONGELADO:** regras/lacres preservados. Descrições antigas
  de ambiente ou prontidão não significam estado operacional atual.
- **ORIGINAL_PRESERVADO / PEDIDO_ORIGINAL_HISTORICO / REGISTRO_HISTORICO:**
  evidência datada e proveniência, sem instrução automática de retomada.

O charter antigo e o runbook H18 receberam aviso de contexto. Os três guias
em `FONTES_WEB_ORIGINAIS` e o relatório lacrado em `outputs` mantêm os bytes
originais; os nomes “continuar”, “iniciar” ou “resultado” não os tornam vigentes.
O `COMECE_AQUI.md` da raiz agora aponta para os documentos atuais.

Não substituir em massa caminhos, contagens ou vereditos nos documentos datados:
isso apagaria o que foi feito em cada versão. Links históricos a pastas de outra
máquina ou artefatos não restaurados são registrados no recibo local, não promovidos
a links operacionais. O teste de links ativos exclui o corpo histórico após o aviso.

A documentação corrigiu caminhos, Python/Core, comandos de instalação Windows,
escopo de tipagem, contagens de CI por SHA, capital como cenário, estado H21/H20,
plano futuro já registrado e atraso da finalização. Nenhum resultado, parâmetro,
fonte bruta, banco, trial ou protocolo congelado foi alterado.

Inventário inicial, hashes antes/depois, cópias anteriores dos arquivos editados
e verificações estão em `C:\STOCKS\work\markdown-review-20260909`.
Arquivos locais da raiz/entrega não fazem parte do repositório Git.

## Inventário completo dos 94 arquivos iniciais

O caminho é relativo a `C:\STOCKS`. Cada arquivo aparece uma vez.

| Arquivo | Classificação | Ação |
|---|---|---|
| `AGENTS.md` | ATUAL | Preservado/conferido |
| `COMECE_AQUI.md` | ATUAL | Atualizado |
| `FONTES_WEB_ORIGINAIS/INICIAR_NO_NOTEBOOK.md` | ORIGINAL_PRESERVADO | Preservado/conferido |
| `FONTES_WEB_ORIGINAIS/LEIA_PRIMEIRO.md` | ORIGINAL_PRESERVADO | Preservado/conferido |
| `FONTES_WEB_ORIGINAIS/PROMPT_CONTINUAR.md` | ORIGINAL_PRESERVADO | Preservado/conferido |
| `instructions/STOCKS_PREDICTOR_PROMPT_FINAL_20260909.md` | MANDATO_ORIGINAL_VIGENTE | Preservado/conferido |
| `outputs/RELATORIO_STOCKS_H21.md` | ORIGINAL_PRESERVADO | Preservado/conferido |
| `stocks-predictor/AGENTS.md` | ATUAL | Atualizado |
| `stocks-predictor/CLAUDE.md` | ATUAL | Atualizado |
| `stocks-predictor/docs/AGENT_CHARTER.md` | ATUAL_COM_HISTORICO | Atualizado |
| `stocks-predictor/docs/audit/kimi_2026-08-24/plan.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/docs/audit/kimi_2026-08-24/RELATORIO_AUDITORIA_RJ.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/docs/auditoria_2026-09-04.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/docs/continuation/INITIAL_REQUEST.md` | PEDIDO_ORIGINAL_HISTORICO | Preservado/conferido |
| `stocks-predictor/docs/continuation/MANDATO_20260909.md` | MANDATO_ORIGINAL_VIGENTE | Preservado/conferido |
| `stocks-predictor/docs/continuation/MIGRACAO_MAIN.md` | ATUAL_COM_HISTORICO | Atualizado |
| `stocks-predictor/docs/continuation/PRESERVATION_VERIFIED.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/docs/continuation/PROMPT_NOVO_CHAT.md` | ATUAL | Atualizado |
| `stocks-predictor/docs/continuation/SESSION_CONTEXT.md` | ATUAL_COM_HISTORICO | Atualizado |
| `stocks-predictor/docs/continuation/UPDATE_20260908.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/docs/DESIGN.md` | PROTOCOLO_HISTORICO_CONGELADO | Preservado/conferido |
| `stocks-predictor/docs/research/2026-09-06-readiness.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/docs/research/2026-09-07-final-review.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/docs/research/2026-09-07-h17-first-observation.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/docs/research/2026-09-07-h17-registration.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/docs/research/2026-09-07-h19-cash-pilot.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/docs/research/2026-09-07-h19-continuous-results.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/docs/research/2026-09-07-h19-dates-v3-results.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/docs/research/2026-09-07-h19-retail-results.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/docs/research/2026-09-07-profit-validation-results.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/docs/research/2026-09-07-real-integration-results.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/docs/research/2026-09-07-reorganization-results.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/docs/research/2026-09-07-repairs.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/docs/research/2026-09-07-source-completion.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/docs/research/2026-09-07-value-results.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/docs/research/2026-09-08-auction-accounting.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/docs/research/2026-09-08-chat-review.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/docs/research/2026-09-08-continuation-state.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/docs/research/2026-09-08-entry-unit-source-addendum.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/docs/research/2026-09-08-feasibility-results.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/docs/research/2026-09-08-h20-profit-test-results.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/docs/research/2026-09-08-h20-remediation-results.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/docs/research/2026-09-08-h20-results.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/docs/research/2026-09-08-similar-models.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/docs/research/2026-09-08-source-closure-results.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/docs/research/2026-09-09-h21-results.md` | ATUAL_COM_HISTORICO | Atualizado |
| `stocks-predictor/docs/RJ_DESIGN.md` | PROTOCOLO_HISTORICO_CONGELADO | Preservado/conferido |
| `stocks-predictor/docs/RUNBOOK_H18.md` | ATUAL_COM_HISTORICO | Atualizado |
| `stocks-predictor/HANDOFF.md` | ATUAL_COM_HISTORICO | Atualizado |
| `stocks-predictor/README.md` | ATUAL | Atualizado |
| `stocks-predictor/reports/h10_verdict_adhoc.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/reports/h11_verdict_adhoc.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/reports/h12_verdict_adhoc.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/reports/h13_verdict_adhoc.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/reports/h14_verdict_adhoc.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/reports/h15_verdict_adhoc.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/reports/h16_verdict_adhoc.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/reports/h1_verdict_20260712T091903477689-41cc24.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/reports/h2_verdict_20260716T221541856778-ac106e.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/reports/h4_verdict_20260718T201214322046-5e3833.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/reports/h5_verdict_20260718T202628182793-427444.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/reports/h6_verdict_adhoc.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/reports/h7_verdict_adhoc.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/reports/h8_verdict_adhoc.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/reports/h9_verdict_adhoc.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/research/session-20260907/deliverables/COMPLEMENTO_STOCKS.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/research/session-20260907/deliverables/CORRECOES_STOCKS.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/research/session-20260907/deliverables/ESTADO_FINAL_STOCKS.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/research/session-20260907/deliverables/H17_RESULTADO.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/research/session-20260907/deliverables/H18_H19_REORGANIZACOES_RESULTADO.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/research/session-20260907/deliverables/H18_H19_RESULTADO_TESTADO.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/research/session-20260907/deliverables/H19_CAIXA_PROXIMO_TESTE.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/research/session-20260907/deliverables/H19_CAIXA_RESULTADO.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/research/session-20260907/deliverables/H19_DATAS_V3_RESULTADO.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/research/session-20260907/deliverables/H19_EXECUCAO_CONTINUA_RESULTADO.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/research/session-20260907/deliverables/PRIMEIRA_ENTREGA_STOCKS.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/research/session-20260907/deliverables/PROMPT_NOVO_CHAT_STOCKS.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/research/session-20260907/deliverables/TESTES_REAIS_STOCKS.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/research/session-20260907/deliverables/VALIDACAO_LUCRO_STOCKS_RESULTADO.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/research/session-20260907/README.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/research/session-20260907/scripts/h17-manual.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/research/session-20260908/chat-review/REVISAO_CRITICA_CHAT_STOCKS.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/research/session-20260908/deliverables/RELATORIO_STOCKS_CONTINUIDADE.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/research/session-20260908/h20-implementation/H20_IMPLEMENTACAO.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/research/session-20260908/h20-profit-test/H20_TESTE_LUCRO.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/research/session-20260908/h20-remediation/COMO_REPRODUZIR.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/research/session-20260908/h20-remediation/CORRECOES_STOCKS.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/research/session-20260908/historical-code-preserved/README.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/research/session-20260908/local-scripts-preserved/README.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/research/session-20260908/source-closure/RESULTADO_FONTES_12.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/research/session-20260908/source-closure/RESULTADO_FONTES_13.md` | REGISTRO_HISTORICO | Preservado/conferido |
| `stocks-predictor/research/session-20260909/h21/README.md` | ATUAL | Atualizado |
| `stocks-predictor/RESEARCH_FREEZE.md` | PROTOCOLO_HISTORICO_CONGELADO | Preservado/conferido |
| `stocks-predictor/STOCKS_CURRENT_STATE.md` | ATUAL_COM_HISTORICO | Atualizado |
