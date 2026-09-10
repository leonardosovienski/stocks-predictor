# Auditoria integral Stocks — reconhecimento intermediário

Base observada: `3f9b891bfc48f38a36fa7f5405547b85ca76b317`, main local/remota,
um checkout em C:\STOCKS\stocks-predictor, sem alterações ou arquivos não rastreados.
Referência antiga 7de0ea9 está superada pelo PR73. CI194 dessa base: sucesso no
GitHub; conteúdo dos logs ainda em conferência. Este documento não encerra a auditoria.

## Usos e critérios de aceite

1. Desenvolvimento/manutenção: dependências declaradas, imports de pacote,
   testes/lint/tipagem/build e wheel fora do checkout no SHA exato, comandos seguros.
2. Pesquisa histórica e experimentação controlada: identidade de protocolo/fontes,
   integridade, disponibilidade temporal adequada ao método, histórico de seleção
   explícito, contas reproduzíveis, ausência de promoção automática para lucro real.
3. Simulação: capital finito, posições/caixa/recebíveis/obrigações conciliados,
   eventos e custos explicitados, execução posterior à decisão, baseline comparável
   quando a conclusão pretender superioridade.
4. Observação prospectiva: plano e entradas verificáveis antes do resultado,
   mecanismo sem retroatividade, sem ativação de monitor nesta auditoria.
5. Apoio à decisão: evidência econômica, limites de perdas e despesas relevantes.
6. Operação real: avaliar os impedimentos; ordens/corretora/capital não autorizados.

Lucro absoluto, vantagem, robustez, complexidade, plausibilidade de execução e
risco terão respostas separadas. Capital pessoal, horizonte, tolerância a perdas e
conta XP são desconhecidos; não bloqueiam a auditoria sob cenários já registrados.

## Sistema encontrado e dados pressupostos

1356 caminhos Git. `stocks_predictor` contém pesquisa de fatores/RJ, ingestão,
SQLite/migrações, eventos, contabilidade e simulações. `main.py` é CLI histórica.
`tests` é a suíte ativa; `research/session-*` preserva medidores/artefatos e auxiliares.
`vendor/predictor_core` é arquivo histórico, enquanto pyproject/lock apontam Core 3.2.
Não há necessidade demonstrada de serviço/API/frontend/ML para exposição simples.

Fluxo H21 encontrado: nove COTAHIST locais + recibo -> `extract_quotes.py` ->
quotes.json/calendário/linhas originais -> protocolo -> `run_round.py` ->
`etf_hold.simulate`/Selic -> oito livros -> `verify_result.py` em centavos e
`reproduce_check.py`. Não depende de banco operacional nem de previsão.
É uma compra e venda BOVA11 entre 2018-01-02 e 2026-04-01, custos 18/36bp,
dois preços e capitais hipotéticos R$5/10mil. Dados R1 até setembro ficam separados.

Fluxo de ações: COTAHIST/CVM/eventos -> dados e painéis -> sinais H17-H20 ->
execução/contabilidade -> diagnósticos/revisão de fontes. O CLI H20 verifica
prontidão e não demonstra uma execução econômica integral. RJ/fatores estão
arquivados/congelados, mas seus resultados/decisões continuam objeto da revisão.

Fora do Git: arquivo de migração e partes, 12 objetos SQLite recuperados de 37 aliases,
fontes13/14 separadas, nove ZIPs de cotações, originais R1/R2, livros H21 e logs.
Catálogos alegam integridade, com referência original, sete versões de pesquisa,
um reparo de exemplo e três fixtures. Verificação independente em curso.
Não confundir calendário, prices_raw ou fundamentals com histórico PIT suficiente.

## Claims iniciais e prioridade

| ID | Proposição | Natureza | Evidência inicial | Próximo exame |
|---|---|---|---|---|
| C01 | Main limpa no SHA antigo | FATO | DESATUALIZADO: SHA atual 3f9b891 | Preservar baseline |
| C02 | 12 DBs íntegros, sem ativação | FATO | NÃO VERIFICADO fisicamente nesta auditoria | Hash, SQLite somente leitura, tabelas, default |
| C03 | Todas fundamentals_pit vazias | FATO | CONFLITANTE: catálogo lista 3 linhas no reparo | Consulta de todos os bancos |
| C04 | H21 reproduz oito resultados | FATO | NÃO VERIFICADO por execução atual | Fontes -> medição -> conta independente |
| C05 | Ganho H21 é lucro executável integral | HIPÓTESE | Documentação corretamente não o afirma | Eventos, execução, custos, tributos |
| C06 | Fonte13 reproduzida/fonte14 com lacunas | FATO | NÃO VERIFICADO por execução atual | Reexecutar audit_recovered |
| C07 | H20 justifica menor prioridade | INFERÊNCIA | Razão de custo/dados, não inferioridade comprovada | Protocolos e diagnóstico comparável |
| C08 | Ausência de ML/UI/API é defeito | HIPÓTESE | Sem necessidade demonstrada | Decisão por uso e custo |
| C09 | 791 testes/78% suportam HEAD atual | FATO | CI194 success; contagem por confirmar | Logs de execução, exclusões e escopo |
| C10 | Status CLI representa linha atual | FATO | REFUTADO na leitura: imprime H19 e comando Windows antigo | Corrigir após baseline e testar |

Riscos prioritários: dados com identidade/tempo incorretos; certificação de
eventos por ausência de registros; mistura de fixtures/reparos com mercado;
tributo/custo contado duas vezes; resultado patrimonial chamado caixa disponível;
comandos de prontidão ou status apresentados como fluxo econômico executado;
holdout considerado intacto apesar da exposição prévia; publicação sem reprodução.

Prioridade: (P0) preservar linha inicial e reproduzir evidência; (P1) provar/corrigir
falhas de contratos temporais e contábeis; (P2) conferir suficiência documental e
resultados H20/H21/legado; (P3) verificar ponta a ponta e checks; (P4) consolidar
registros, documentação, PR e main com CI do SHA efetivo.

## Orçamento prospectivo de investigação adicional

Rodada AUDIT-R3, distinta das coletas R1/R2 encerradas. Objetivo: resolver questões
materiais de calendário/eventos/custos/tributos e suficiência para H21, com revisão
crítica de H20 e alternativas existentes. Primeiro examinar fontes locais.
Limite inicial: 20 consultas/aberturas web direcionadas, até 12 novas aquisições
de fontes primárias, 2 tentativas por recurso/rota, 100MB de novos dados, até 90min
de coleta. Fontes: B3, CVM/FNET, BlackRock/administrador, Receita/Planalto, BCB/XP.
Parar a coleta quando a evidência decidir a proposição ou o limite for atingido;
registrar pendência como externa ou encerrada por orçamento, sem declarar resolvida.

Reprodução econômica: mesma hipótese H21, oito resultados originais; nenhum tuning,
novo ativo, janela ou parâmetro. H20: reprodução do diagnóstico existente sem
reativar sua estratégia, se os arquivos permitirem. Nenhuma nova hipótese econômica
é aberta nesta etapa. Se correção alterar medida, criar versão derivada e comparar
com original, sem editar protocolos/livros antigos ou alegar evidência independente.

Baseline técnico: `baseline.json` (hashes de arquivos Git e inventário externo),
`module-map.json`, `database-verification.json`; resultados novos e comandos serão
registrados nesta pasta. Matriz final será visão de registros canônicos vinculados.
