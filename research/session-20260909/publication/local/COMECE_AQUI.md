> Continuidade consolidada: leia o [prompt integral final](stocks-predictor/docs/continuation/PROMPT_AUDITORIA_INTEGRAL_20260909.md) e o [pacote publicado](stocks-predictor/research/session-20260909/publication/README.md). A auditoria ainda não foi executada. O documento anterior de revisão abaixo é contexto; o novo prompt contém as 24 frentes e os critérios finais.

# Stocks — localização e continuidade atuais

Atualizado em 09/09/2026. A raiz local única é **C:\STOCKS**.

**Próxima tarefa solicitada:** revisão integral da lógica, arquitetura, dados,
fontes, metodologia, resultados e premissas, começando pelo que já existe e
executando as correções necessárias. Instrução completa:
[REVISAO_INTEGRAL_PROXIMO_CHAT.md](instructions/REVISAO_INTEGRAL_PROXIMO_CHAT.md).
Esse pedido amplia a prioridade anterior de fechar fontes H21; as referências
abaixo descrevem o ponto de partida, não um caminho que deva ser mantido.

| Conteúdo | Local |
|---|---|
| Código, main e histórico Git | `C:\STOCKS\stocks-predictor` |
| Pesquisa, fontes novas, logs e temporários | `C:\STOCKS\work` |
| Bancos/fontes recuperados e catálogo atual | `C:\STOCKS\data` |
| Relatórios e recibos | `C:\STOCKS\outputs` |
| Prompt original | `C:\STOCKS\instructions\STOCKS_PREDICTOR_PROMPT_FINAL_20260909.md` |
| Mapa local e movimentações verificadas | `C:\STOCKS\LOCALIZACAO_PROJETO.json` |
| Arquivos originais e bundle offline | Esta raiz e `FONTES_WEB_ORIGINAIS` |

Comece por [AGENTS](AGENTS.md), [README](stocks-predictor/README.md),
[estado atual](stocks-predictor/STOCKS_CURRENT_STATE.md) e
[índice documental](stocks-predictor/docs/DOCUMENTATION_INDEX.md).

O ZIP de dados já foi reunido e verificado. Nove COTAHIST e os 12 bancos únicos
foram recuperados seletivamente, com fontes 13/14 em diretórios separados.
Comece por [data/README.md](data/README.md) e [CATALOG.json](data/CATALOG.json).
Não juntar novamente, clonar outro checkout ou restaurar tudo por padrão.

A referência integrada da H21 é `4a85d4317657ac5ddaffcacf889b6341cf9c4b0a`,
PR69. Revisões documentais posteriores podem avançar o SHA; conferir HEAD.
O [relatório entregue](outputs/RELATORIO_STOCKS_H21.md) e seus hashes permanecem
intactos. Complementos posteriores estão no estado atual do repositório.
Lucro executável integral e lucro futuro não foram validados.

O [complemento de fontes/custos](stocks-predictor/docs/research/2026-09-09-h21-source-closure.md)
atualizou a fonte para 2.159 cotações até 08/09/2026, sem recalcular H21.
XP é a preferência registrada, com alternativa Rico condicional. Eventos históricos
e custos integrais permanecem parcialmente documentados; campos desconhecidos
estão explícitos. Fontes e conferências: `work\h21-source-closure-20260909`.
Recibo da nova integração e CI: `outputs\ENTREGA_FONTES_H21_20260909.json`.

O [complemento mais recente, R2](stocks-predictor/docs/research/2026-09-09-data-completion-r2.md),
ampliou as demonstrações/comparativos BOVA11 até março de 2026 e as tarifas históricas.
Recuperação física foi validada; eventos, despesas e execução ainda têm pendências
explícitas no catálogo. O recibo R2 de integração/CI fica em
`outputs\ENTREGA_DADOS_FONTES_R2_20260909.json`.

Guias em `FONTES_WEB_ORIGINAIS` descrevem a exportação do outro computador.
Seus caminhos em Superleo13, E: e `C:\Stocks\codigo` são proveniência histórica.
As sete movimentações verificadas por SHA-256 estão em
`work\centralizacao-20260909\movimentacoes.json`.

Este Windows não recebeu instalações Python/Core. Usar os auxiliares stdlib
disponíveis e a CI Linux conforme [AGENTS do código](stocks-predictor/AGENTS.md).
Nenhum monitor, paper recorrente ou operação real está ativo.
