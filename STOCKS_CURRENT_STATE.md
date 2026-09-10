## Pausa e encerramento revisado — 10/09/2026 UTC

[Estado final, evidências e retomada](docs/continuation/2026-09-10-closure/README.md).
Infraestrutura de pesquisa em lote validada; CI230 e recibos finais preservados.
O objetivo econômico permanece aberto. Lucro não validado; nenhuma operação financeira ativa.
As seções anteriores abaixo conservam seu contexto e suas datas.

## Operação R8 — 10/09/2026 UTC

[Relatório operacional](docs/engineering/2026-09-10-r8/README.md) e
[runbook](docs/engineering/2026-09-10-r8/RUNBOOK.md).
Entrada instalada: `python -m stocks_predictor`; no checkout: `python main.py ops`.
Banco gerido separado, ingestão por hash, inspeção por versão, backup e restauração.
O escopo é pesquisa local em lote; fontes/custos/observação futura ainda pendentes.
R7 mantém o inventário econômico e os recibos históricos. Os blocos abaixo são datados.

## Estado vigente R7 — 10/09/2026 UTC

[Relatório](docs/audit/2026-09-10-r7/README.md) e
[consolidado verificável](docs/audit/2026-09-10-r7/CONSOLIDADO.md).
Capital confirmado: R$5.000. Origem por conteúdo, contratos datados, análise
estática de todo o pacote, build por hashes e materializador de fonte implementados.
Fontes econômicas ainda parciais: 50 líquidos, 22 datas, 28 registros societários.
Zero observações prospectivas concluídas; lucro pessoal/futuro não demonstrado.
I15 documental e fechamento do PR75 resolvidos. O registro R7 prevalece para leitura.

## Estado R6 — 10/09/2026 UTC

[Relatório vigente de dados](docs/research/2026-09-10-r6/README.md): I15 resolvido
quanto aos cinco arquivos; todos os 1.448 arquivos passaram no verificador original.
Fonte BOVA até 09/09/2026, 171 registros anteriores iguais. Fonte 15: 22 datas/50
líquidos pendentes, após incorporar dois pagamentos documentados. Inventário de
eventos/PIT/custos ainda parcial; sem lucro executável/futuro demonstrado ou ordens.
Os estados abaixo são registros históricos, não substituem esta atualização.

## Pesquisa econômica R5 — 10/09/2026 UTC

O usuário reabriu a pesquisa em busca de lucro validado, com liberdade sobre hipóteses
e arquitetura. [R5/H22](docs/research/2026-09-10-r5/README.md) executou uma regra mensal
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

## Engenharia R4 posterior à auditoria — 10/09/2026 UTC

[Relatório vigente de engenharia](docs/engineering/2026-09-10-r4/README.md) e
[integração/checks do PR75](https://github.com/leonardosovienski/stocks-predictor/pull/75).
Carga COTAHIST por lotes, contagem efetiva, conflitos de identidade rejeitados,
rollback de falhas e respeito à transação do chamador. Validação canônica de datas
e contagens, conexão fechada em falha de migração e diagnóstico sem dependências.
CI: Python 3.13/3.14, lock obrigatório, tipos de argumentos verificados,
cobertura mínima de 77%, timeouts e evidência retida por 14 dias.
Memória e regressões são medidas no relatório; não constituem nova evidência de lucro.
Os estados anteriores abaixo preservam suas respectivas datas.

---

## Estado após auditoria integral — 10/09/2026 UTC

A auditoria solicitada foi executada. Ponto de entrada: [relatório A–R](docs/audit/2026-09-10-integral/README.md), [registro canônico](docs/audit/2026-09-10-integral/registry.json) e [reprodução](research/session-20260910/integral/README.md). Integração e último check: [PR74](https://github.com/leonardosovienski/stocks-predictor/pull/74).

24 frentes examinadas; defeitos de parser, tempo, snapshot, origem documental, paper e inferência corrigidos. CI197:815 testes, seis subtestes,78% de cobertura reportada, build/wheel e segredos aprovados. Oito livros H21 e16.400 pontos reproduzidos; H20 consumido reconciliado, pacote integral bloqueado por cinco objetos. Os12 bancos e lacres verificados permanecem intactos; banco operacional não ativado.

H21 permanece lucro histórico condicional e prioridade de validação por simplicidade/custo de evidência; superioridade, lucro integral/futuro e adequação pessoal não demonstrados. H20 amplo estacionado. O reparo de exemplo tem três linhas fundamentals_pit, corrigindo a generalização anterior de que todas eram vazias; não constitui painel amplo. Pendências únicas:I10–I16, todas com condição objetiva. Nenhuma automação, ordem ou instalação Windows foi realizada.

Os blocos abaixo são históricos, com suas datas e escopos originais.

---

## Estado da continuidade — auditoria integral preparada em 09/09/2026

O usuário solicitou uma revisão ampla do projeto e consolidou o
[prompt integral de auditoria](docs/continuation/PROMPT_AUDITORIA_INTEGRAL_20260909.md).
Essa auditoria ainda não foi executada. A publicação desta continuidade preserva
os resultados anteriores e reúne os registros autorais da sessão no
[pacote de publicação](research/session-20260909/publication/README.md).

Qualificações para a próxima revisão: os 12 bancos recuperados incluem referência,
versões de pesquisa, reparo e fixtures; integridade não significa suficiência.
Os 50 PDFs passaram por processamento estrutural e exame dos conteúdos pertinentes,
sem certificação de auditoria financeira integral dos 50 documentos. R2 não
recalculou resultados econômicos. Testes aprovados não demonstram lucro executável.

Os estados e números abaixo pertencem às rodadas indicadas e devem ser reconfirmados.
A antiga fila H21 foi substituída como prioridade pelo mandato integral.

---

## Estado após recuperação de dados R2 — 09/09/2026

Os 37 caminhos de banco da migração correspondem a 12 bancos únicos, agora
recuperados em `C:\STOCKS\data\recovery-r2`, com hashes e integridade conferidos.
O catálogo `C:\STOCKS\data\CATALOG.json` separa referência original, reparos,
versões históricas e fixtures. Não houve ativação de banco ou ingestão.
Fontes 13 e 14 estão disponíveis separadamente; auditoria 13 reproduzida exatamente.
A 14 conserva 52 valores líquidos e 24 datas ausentes, 28 entradas societárias
pendentes e 0/1.248 intervalos integrais certificados; contagens sobrepostas.

[Relatório R2](docs/research/2026-09-09-data-completion-r2.md),
[prontidão](docs/research/2026-09-09-data-readiness.json),
[eventos](docs/research/2026-09-09-bova-event-review-r2.json) e
[custos/entradas](docs/research/2026-09-09-operational-inputs-r2.json).
Demonstrações e comparativos agora cobrem os exercícios de 2018 a março de 2026.
Avisos cancelados e identidade incorreta foram segregados; proposta de incorporação
não foi convertida em evento executado. Tarifa B3 de 2021 foi recuperada.

Prontidão integral continua parcial: eventos/direitos contínuos, tarifa de entrada
de 2018, despesas efetivas e execução permanecem sem certificação completa.
XP é preferida, com canal/assessor, capital, horizonte e perda aceitável desconhecidos.
H21 original e 2.159 cotações R1 até 08/09 estão intactas; zero retornos recalculados.
H20 estacionada; nenhum monitor, autenticação de corretora ou ordem.

R2: 121 aquisições finalizadas, 50 PDFs analisados, uma normalização de eventos/custos.
Nove testes locais do recuperador passaram no Python auxiliar 3.12.14. Atestados
de produção dependem da CI Linux no SHA exato; integração e resultado final em
`C:\STOCKS\outputs\ENTREGA_DADOS_FONTES_R2_20260909.json`.
Coleta encerrada; retomada exige orçamento próprio e consulta ao catálogo.

Os blocos seguintes são históricos; referências a bancos ainda não recuperados
descrevem o estado anterior à R2.

---

## Estado após a revisão de fontes R1 — 09/09/2026

Raiz local única: `C:\STOCKS`. O
[complemento documental](docs/research/2026-09-09-h21-source-closure.md) conferiu
171 pregões de 2026 até 08/09, acrescentando 109 à fonte preservada:
2.159 registros, 62 sobrepostos idênticos. Nenhum retorno novo ou alteração H21.

XP é a preferência informada; Rico é alternativa condicional de corretagem.
Custos B3 por fase, adicionais das corretoras e custódia estão documentados.
Conta/canal, capital real, horizonte e tolerância de perda permanecem desconhecidos.
Eventos do ETF têm inventário parcial com regulamentos e demonstrações recuperados;
a proposta de incorporação examinada não teve assembleia instalada.
Cobertura histórica contínua e custo integral ainda impedem certificação líquida.

Fontes, falhas, duas normalizações e validações:
`C:\STOCKS\work\h21-source-closure-20260909`.
[Entradas operacionais](docs/research/2026-09-09-h21-operational-inputs.json) e
[inventário](docs/research/2026-09-09-h21-source-inventory.json) separam fatos,
condições e desconhecidos. Recibo da integração/CI desta revisão:
`C:\STOCKS\outputs\ENTREGA_FONTES_H21_20260909.json`.
Não há monitor ativo, operação ou observação futura.

Os blocos seguintes descrevem estados anteriores pela data. A revisão de fontes
acrescentou aquisições públicas; não ampliou a restauração dos bancos de migração.

---

## Estado após a centralização — 09/09/2026

Raiz única: `C:\STOCKS`; checkout: `C:\STOCKS\stocks-predictor`, main.
Entregas: `C:\STOCKS\outputs`; pesquisa/logs: `C:\STOCKS\work`; prompt original:
`C:\STOCKS\instructions\STOCKS_PREDICTOR_PROMPT_FINAL_20260909.md`.
Seis entregas e o prompt foram movidos com SHA-256 conferido; a pasta anterior
da tarefa ficou sem arquivos do projeto. Mapas: `C:\STOCKS\LOCALIZACAO_PROJETO.json`
e [LOCAL_PATHS_20260909.json](docs/continuation/LOCAL_PATHS_20260909.json).

A rodada H21 foi integrada pelo [PR69](https://github.com/leonardosovienski/stocks-predictor/pull/69),
commit `4a85d4317657ac5ddaffcacf889b6341cf9c4b0a`.
A [CI184 desse SHA](https://github.com/leonardosovienski/stocks-predictor/actions/runs/34386092297)
passou 782 testes regulares, Ruff, Pyright, build, gitleaks e wheel fora do checkout;
Linux, Python 3.13.15/Core 3.2.0, cobertura 78%. Os 17 testes arquivados não foram
executados. Revisões documentais posteriores não são nova medição econômica.

Somente nove COTAHIST foram recuperados da migração; bancos não foram abertos
ou integralmente restaurados. Python auxiliar local: 3.12.14; produção
3.13/Core/pytest indisponível localmente. Nenhuma instalação Windows foi feita.

H21: uma história exploratória BOVA11 de 2018-01-02 a 2026-04-01,
quatro especificações e oito valorizações de capital, com 2.050 cotações.
Ganho condicional R$5.515,48–5.618,39 no cenário R$5 mil e
R$11.950,19–12.173,17 no cenário R$10 mil; drawdown máximo 43,46–46,31%.
Custos/imposto modelados não resolvem despesas reais e inventário de eventos
do ETF. Lucro executável integral e previsão permanecem desconhecidos (`null`).
H21 é candidata a validação adicional; reconstrução ampla H20 estacionada.
Não há comparação líquida H21–H20 nem holdout intacto demonstrados.
57/59 são mínimos administrativos, não provas independentes.

O [plano prospectivo](docs/research/2026-09-09-h21-forward-plan.json) já está
registrado, para o primeiro pregão a partir de 10/09/2026 até o primeiro a partir
de 10/09/2027. Zero observações futuras e nenhum processo ativo.
Próximo trabalho: inventariar eventos do ETF e direitos após a venda, apurar
despesas/execução, reconciliar sem tuning e seguir o plano quando houver dados.
O pré-registro do plano não está pendente.

O experimento terminou às 16:50:16 UTC. A finalização excedeu o prazo registrado
de 17:38 UTC e foi conferida após 18:02 UTC; atraso declarado, sem novas variantes.
Recibo: `C:\STOCKS\outputs\ENTREGA_STOCKS_H21.json`.

Os blocos abaixo são registros datados. “Atual”, “nunca rodou”, contagens e
caminhos externos neles se referem à respectiva versão.
[Índice documental](docs/DOCUMENTATION_INDEX.md): orientação vigente e acervo.

---

## Estado vigente — rodada H21 de 09/09/2026

Código agora em `C:\STOCKS\stocks-predictor`. Mapa local:
`docs/continuation/LOCAL_PATHS_20260909.json`. O mandato atual autoriza nova pesquisa
e está preservado em `docs/continuation/MANDATO_20260909.md`; os estados abaixo
continuam históricos, interpretados pela data.

**H21 BOVA11:** uma rodada exploratória executada, quatro cenários de preço/custo,
oito valorizações em R$5/10 mil, 2.050 cotações reais. Ganhos históricos condicionais
positivos; quedas máximas de 43–46%. Lucro executável integral e previsão continuam
`null`: faltam inventário completo dos eventos do ETF e despesas adicionais.
H21 é candidata à validação adicional, não aprovada para operar.
H20 permanece inconclusiva e fica estacionada para reconstrução ampla nesta rodada.
H1–H20/lacres preservados. Nenhum capital real, monitor ou paper ativado.

Relatório: [H21 e decisão econômica](docs/research/2026-09-09-h21-results.md).
Reprodução: `research/session-20260909/h21/README.md`. `economics.py` agora distingue
equivalente histórico anualizado de previsão; CI wheel verifica isolamento real.
Python auxiliar local 3.12.14 não é validação do contrato de produção 3.13;
ver recibo de CI/PR69 para checks do estado integrado.

## Complemento de fontes — revisão 13 (08/09/2026 UTC)

Entrada atual: work/source-closure-20260908/execution-inputs-13, manifesto
7c24e093f7a148c3f375fff9fbd23db62f049ba8012e49e6ba7b4413e27a372b.
12 datas preenchidas; uma duplicata Hypera conciliada com documentos da
companhia. As 778 linhas brutas permanecem preservadas: representam 777
direitos distintos, materializados em 800 pagamentos com 9 cronogramas.
Datas ausentes 37→24; líquidos ausentes 66→54 linhas derivadas.
14 datas de formulários continuam apenas como candidatas: prazo máximo ou
cronograma agregado superado não é confirmação de recebimento.

O seletor de documentos inclui Relatório Proventos e avisos sem assunto,
começa na aprovação e limita também a data de envio: uma retificação tardia
não existia na data original do evento. 174 candidatos mantidos, todas as
versões preservadas. Deduplicação exige registros B3 idênticos e revisão
explícita de uma única distribuição na companhia; parcelas Iguatemi não
são eliminadas automaticamente. Não houve ajuste de parâmetros ou retornos.

827 arquivos de entrada, 791 fontes primárias e 1 reconstrução derivada;
365.198 cotações. Correção do relatório anterior: a cobertura de cotações
termina em 01/04/2026, mas a lista de pregões vai até 27/08/2026.
O PDF parcial Hapvida ITR não serve como prova; o prospecto integral contém
a confirmação do pagamento GNDI. Alguns relatórios CVM têm preenchimento
NUL após EOF: os bytes originais foram preservados, sem truncar ou editar.

Continuam 28 entradas societárias e 1.248 intervalos sem inventário completo
certificado. Lucro e projeção continuam null/BLOCKED_MISSING_EVIDENCE.
Protocolo de fontes e H1–H20 preservados; 53/55; zero novos retornos.
Nenhuma ordem, instalação, serviço pago, agente adicional ou escrita em
banco, ledger ou quarentena. Nenhuma nova dependência de runtime.

Validação 13: auditoria 12 idêntica com código novo, auditoria 13 reproduzida;
11 adulterações rejeitadas. Código d2edbea: 735 testes completos
e 166 testes na wheel extraída, sem instalação; Ruff/Pyright verdes. Pacote
de 1485 arquivos reproduz a auditoria byte a byte. Resultados em
docs/research/2026-09-08-source-closure-results.md. Não confundir fontes com lucro.

## Revisão de fontes e pendências (08/09/2026 UTC)

Pedido do operador: resolver também as fontes pendentes. Protocolo 0700f82,
SHA da8b91a7a263d9870822c58af85b4a47f2c051e932ecb3099fea986ba4456c49,
anterior à reconstrução. Nenhuma nova avaliação de retorno; 53/55 preservados.
As versões 01–12 permanecem preservadas fora de bancos e ledgers.

Entrada atual: work/source-closure-20260908/execution-inputs-12.
Manifesto b9dfab5fb2dc67f7fcdd71f52b325a3a1d442917c116f514fd09f11926876f7e.
788 arquivos verificados; 754 arquivos de fonte, dos quais 753 publicações/fontes
primárias e 1 reconstrução local derivada. 365.198 cotações. Os 778 direitos
originais são preservados em 801 linhas de pagamento, com 9 cronogramas e 32
parcelas. Datas ausentes: 356→37; valores líquidos ausentes: 389 registros
originais→66 linhas derivadas. 8 desdobramentos inteiros integrados; 28 eventos
societários ainda exigem termos, entrega ou base fiscal. 1.248 intervalos de
inventário permanecem sem certificação integral. Estas contagens se sobrepõem.

Falhas corrigidas nesta revisão: associações entre JCP/dividendos retiradas;
reconciliação de parcelas sem pagar o total original duas vezes; retificações
ligadas ao aviso original; datas TIM corrigidas; tabelas em imagem revisadas;
fonte derivada não contada como primária. Créditos B3 com aprovação ausente
agora aparecem em incomplete_rows e exigem fonte adicional para associação;
não são descartados silenciosamente nem promovidos a dados completos.
Líquidos de atualização Selic usam prazo documentado e regra específica para pessoa física.
Os líquidos 2026 tratados aqui são retenção no pagamento, não imposto mínimo
anual pessoal. Capital devolvido, base fiscal e frações continuam dependentes
do livro e das fontes aplicáveis. SLC 2019: data provada, unidades antes/depois
do desdobramento ainda não reconciliadas. BRDT 2020: aviso contém duas
atualizações monetárias ausentes no inventário original; lacuna explicitada.

Validação do código 6e54e5d: 714 testes completos, sem avisos; 145 testes
na wheel fora do checkout. Ruff e Pyright verdes. Cinco adulterações rejeitadas.
Pacote de 856 arquivos reproduz a auditoria byte a byte com Python 3.13
isolado, sem instalação ou rede. Resultados em docs/research/
2026-09-08-source-closure-results.md e na pasta de pesquisa source-closure.
Usar py -3.13 explícito, sem venv ou instalação. Extrações 01–03 usaram 3.14;
as materializações 04–12 e os testes finais usam o Python global 3.13.

Resultado econômico: BLOCKED_MISSING_EVIDENCE; lucro e projeção permanecem
null. Não houve ordens, custos, agentes, escrita nos bancos ou ajuste H1–H20.
O protocolo de fontes não libera retornos: ainda é necessária pré-inscrição
específica vinculada ao hash final das fontes, após completar a evidência.
Evidências e fila completa: research/session-20260908/source-closure.

## Correções concluídas da revisão (08/09/2026 UTC)

Protocolo 38cf95f antes da implementação; código 62444c0. H20Policy integrada ao
run_continuous: posições realmente executadas, bandas no sinal, proventos,
entregas, leilões e impostos antes das compras. H19 padrão preservada. O auxiliar
execute_rebalance continua limitado à mecânica de ordens e explicita essa limitação.
Reprodução oficial: python -m stocks_predictor.h20_checked; proteção na wheel e
nos testes regulares, sem alterar o medidor/observações arquivados.

687 testes passaram sem avisos (670 regulares +17 arquivados); 31 novos regulares.
104 testes adicionais na wheel extraída fora do checkout; Ruff/Pyright verdes.
Primeira suíte parou por árvore sem commit; a repetição limpa passou sem bypass.
H19 e H20 anterior reproduzidas byte a byte; quatro livros H19 iguais a c1bfa15.
Conferência pelo mesmo agente, sem independência científica ou novas observações.

Diagnóstico H20 específico: 31 arquivos/365.198 cotações; 1.217 intervalos comuns,
união conservadora de 1.248, zero inventários completos certificados; 36 eventos
societários não integrados. Fontes de caixa/datas/valores ainda faltam. Exigir
revisão H20 vinculada às fontes e intervalos, além do controle de cada evento.
O motor contábil de baixo nível não certifica fontes. O CLI h20_continuous apenas
audita prontidão e retorna 2 enquanto bloqueado; não emite retorno histórico.

Não transformar marcações ou nomes planejados em lucro ou economia real de custo.
Lucro/projeção futura desconhecidos, sem holdout intacto; contagem administrativa
53/55 preservada. Nenhum novo fator, janela, retorno histórico, instalação ou ordem.
Não expandir hipóteses para contornar fontes ausentes. A próxima etapa econômica
depende de inventário documentado e revisão de eventos, não de novos parâmetros.

Relatório: docs/research/2026-09-08-h20-remediation-results.md.
Reprodução e evidências: research/session-20260908/h20-remediation.
Saídas duráveis: work/h20-remediation-20260908; entrega no outputs do chat.

## Revisão crítica de todo o chat (08/09/2026 UTC)

Releitura dos quatro turnos e revisão técnica/metodológica concluída. Contas
anteriores reproduzidas; lucro líquido continua desconhecido. H20 histórica
mediu nomes pretendidos com rotação integral hipotética, sem banda de peso,
livro contínuo ou impostos incrementais integrados ao executor H20.
“Melhorou” deve ser entendido somente como composição de marcações; vantagem
recente e incerteza não sustentam projeção líquida. Sequência de implementação
foi excessiva frente ao gargalo econômico. Não repetir a mesma priorização.

Falha reproduzida: compare_h20 arquivado aceitava --gate sem hash e não conferia
todos os payloads do manifesto de execução. Arquivo fictício contaminava apenas
metadados contextuais; lucro principal continuava null. Arquivos legítimos foram
usados anteriormente, portanto números publicados não mudaram. Nova entrada
research/session-20260908/chat-review/reproduce_h20_checked.py verifica fontes,
gate e código antes de medir, novamente ao terminar e exige resultado idêntico.
Usar REPRODUZIR_VERIFICADO.ps1; executor/pacotes anteriores ficam históricos.

656 testes passaram (639 +11 +6 novos). Resultado H20 aa184580bf5b... byte idêntico;
gate fictício rejeitado sem saída. Nenhuma nova estratégia/avaliação de retorno,
ordem, gasto, instalação, agente, banco protegido escrito ou push. 53/55 é a
contagem administrativa conservadora anterior, não provas independentes.
Relatório: docs/research/2026-09-08-chat-review.md. Artefatos desta revisão em
research/session-20260908/chat-review e outputs/chat-review-20260908 da raiz.

## Teste de desempenho H20 (08/09/2026 UTC)

Pedido: testar se melhorou a projeção de lucro. Protocolo 9286129 anterior ao
cruzamento com retornos; medidor 2488171. 31 trimestres de 2018-07-02 a 2026-04-01,
três seleções congeladas, três preços e dois custos, sem tuning. 29/03/2018 retida
como bloqueada por cobertura; nenhuma data elegível removida pelo desempenho.

Diagnóstico de marcações com rotação integral hipotética, sem caixa ordinário,
impostos ou manutenção: anualização na abertura/custo base 11,00% controle comum,
14,02% valor/rentabilidade, 14,58% retenção. Adverso/custo dobrado 2,05%, 4,74%, 5,25%.
Retenção é a sequência pretendida, sem execução contínua da banda de peso de 2,5%.
Economia real de turnover não foi inferida. Lucro/projeção futura permanecem null.

Diferença média retenção-controle na abertura +0,197 pp/trimestre; IC descritivo
95% [-3,61; +3,92] pp, sem ajuste por seleção. Segunda metade -0,34 pp/trimestre
brutos; vantagem recente também negativa nos outros preços. Drawdown adverso
com custo dobrado -48,24%. Melhora composta aparente, incremento inconclusivo.

639 testes completos +11 testes da medição. Reprodução de 1.448 arquivos,
9.732 células e 12 cenários anteriores, conferência independente de 465 médias,
30 trajetórias e 54 pares. Nova observação byte idêntica aa184580bf5b...;
replay financeiro antigo idêntico e bloqueado. Zero inventários integrais de
caixa disponíveis para os 231 intervalos trimestrais de cada seleção H20.
Runtime de produção inalterado, extratos históricos lidos com mode=ro e hashes
verificados; bancos principais, ledgers, quarentenas e fontes preservados.

18 cenários adicionais registrados/observados, contagem conservadora mínima
53 configurações/55 avaliações históricas; sem holdout ou Proof. Não promover
H20 ou ajustar parâmetros. INCONCLUSIVE_NET_PROFIT / OPERATIONAL_NO_GO mantido.
Relatório: docs/research/2026-09-08-h20-profit-test-results.md. Arquivo reproduzível
em research/session-20260908/h20-profit-test; saídas também na raiz durável,
outputs/h20-profit-test-20260908. Nenhuma ordem, gasto, agente, instalação ou push.

# Estado vigente — implementação H20 de 08/09/2026 UTC

H20 implementada: valor com rentabilidade dos acionistas, retenção até 30% do
ranking e tolerância de 2,5% do capital para ajustes de posições mantidas.
Três alternativas no mesmo universo; protocolo def8e96 anterior à medição.
31/32 datas elegíveis, 372/384 entradas simuladas; 12 casos da data de cobertura
insuficiente permanecem bloqueados. Substituições planejadas 96→70 com tolerância;
não são giro financeiro ou economia real de uma carteira contínua.

639 testes no runtime 9ecf5eb, 92 na wheel fora do checkout, Ruff e Pyright no
escopo novo. H20 reproduzida byte a byte; replay H19 e diagnóstico anterior
preservados. Agora mínimos 35 configurações registradas / 37 avaliações históricas
de retorno; zero retorno novo. H19 permanece congelada e NO_GO, lucro desconhecido.
Relatório e uso: [H20](docs/research/2026-09-08-h20-results.md).

# Estado anterior — continuidade de 08/09/2026 UTC

Revisão adicional de 17 fontes sobre modelos semelhantes concluída:
[mecanismos, resultados externos e prioridades](docs/research/2026-09-08-similar-models.md).
Revisão documental, sem novo sinal, backtest ou mudança de veredito. Priorizar
custo de manutenção e execução, depois viabilidade de valor com rentabilidade;
PEAD condicionado a fontes e ML adiado. Histórico externo não valida a H19.

**H19 permanece Discovery/inconclusiva; NO_GO operacional. Pausar a reconstrução
manual extensa até existir uma rota barata de fontes e manutenção.**

Foi implementada a tributação de leilões ordinários a partir da base fiscal
individual e corrigida a reutilização de líquidos/impostos entre carteiras.
248 compras iniciais nas seleções congeladas foram simuladas; não são giro nem
lucro da carteira contínua. Permanecem 356 datas, 389 líquidos, zero certificados
para 1.237 intervalos e zero dos 36 registros societários aprovados/integrados.

613 testes na suíte completa (0ac04cb); ajuste final bebe1f7 validado por 3 testes
do diagnóstico e 69 testes no pacote externo. Replay real idêntico, exit 2,
lucro null. Nenhum retorno histórico novo; mínimos 32 configurações/37 avaliações.
Fontes, bancos, ledgers e vereditos anteriores preservados.

[Resultado, cenários econômicos e limites](docs/research/2026-09-08-feasibility-results.md).
O começo de HANDOFF.md contém a execução atual; os textos abaixo são históricos.

# Estado vigente — revisão final de 07/09/2026

**H19 trimestral está em Discovery; H18 é controle; H17 já foi observada e ficou
inconclusiva. Nenhum lucro líquido executável foi demonstrado. NO_GO para operar.**

A revisão final passou 592 testes e os controles técnicos declarados. Faltam
356 datas no cadastro de pagamentos, cobertura de caixa de 1.237 intervalos e
integração fiscal/física de 36 registros societários. Isso impede um replay
econômico completo; saída de auditoria bloqueada não é lucro zero.
O código, as cotações e os testes não substituem essas evidências.

O estado mais recente está no início de [HANDOFF.md](HANDOFF.md) e em
[revisão final](docs/research/2026-09-07-final-review.md). Os textos abaixo são
históricos: referências a H18/H19 não observadas e a RJ como linha ativa foram
superadas. As estatísticas antigas continuam associadas às suas versões.

# Atualização anterior 2026-09-07 — H17 Discovery observada

H17 agora tem duas saídas históricas de um único protocolo exploratório: primeira
medição e correção documentada de quatro falsas divergências de fatores. A última
execução completou 94 meses elegíveis, mediu 5.352/5.399 células e classificou a
rodada como INCONCLUSIVE_DATA_QUALITY. IC disponível médio -0,013201; diferença
mensal apenas nos 59 meses completos -0,161341 p.p. Sem rentabilidade executável,
holdout intacto identificado, GO ou confirmação. H18/H19 seguem não observadas.

Código testado `4f487098e702004a88f02fe65d62a008c6df618b`, 483 testes aprovados.
Ver os registros append-only em `docs/research/2026-09-07-h17-observations.jsonl`
e `docs/research/2026-09-07-h17-budget-update.json`. Os estados abaixo são históricos
e suas referências a H17 nunca vista foram superadas por esta atualização.

## Integração real concluída em 2026-09-07

Motor v3 corrigido: bonificação com direito/entrega separados e dimensionamento correto no
preço adverso. A primeira matriz encontrou quatro falhas; após correção, os 36 controles reais
passaram (R$5/10 mil, três preços, dois custos). Suíte completa: 463 testes, cobertura 86%;
lint, Pyright configurado e wheel instalada fora do checkout aprovados. Código testado:
`5c09c7b8ffebefef00467cbab12481f3535a7837`. Fontes e bancos originais preservados por hash.

Capital original CVM validado em três documentos com escala própria e base em 31/12/2023;
isso não resolve toda a base histórica de capitalização. Nenhum retorno H17–H19 observado,
nenhum trial científico novo. O painel DFP/FCA foi verificado em 104 datas sem performance.
Rentabilidade continua INCONCLUSIVE_DATA_QUALITY e os runners H17–H19 permanecem pausados.
[Resultado completo e limites](docs/research/2026-09-07-real-integration-results.md).

## Complemento executado em 2026-09-07

Reconstruídos 2016–2026 em cópia isolada: 4.177 DFP, 4.824 observações de
circulação, 7.450 registros de capital emitido e 4.336 vínculos FCA. Coletados
9.812 registros B3 de 100 emissores. Reconciliados 184 recebíveis B3/RI;
95 recebíveis com quatro intervalos de cobertura importados apenas na cópia.
FRE inválido é rejeitado por documento, com motivo persistente. Migração 0014
isola observações de fontes das entradas de fatores. Nenhum desempenho protegido.

Ainda faltam bases efetivas de ações, versões históricas completas, cobertura
dos demais emissores e eventos sem dinheiro. H17–H19 permanecem pausadas.
Detalhes: [relatório de fontes](docs/research/2026-09-07-source-completion.md).
Validação completa e hashes são registrados no manifesto da entrega.

# Stocks Predictor — estado corrente

> ## Correções implementadas em cópia isolada — 2026-09-07
>
> As APIs públicas de ingestão agora gravam versões separadas, em reais,
> nas tabelas PIT da migração 0013. Base de ações desconhecida não gera
> múltiplo; retorno total exige eventos por papel e cobertura documentada.
> O novo `backtest.walk_forward` mantém quantidades, negocia após o sinal
> e contabiliza caixa/custos igualmente para estratégia e benchmark.
> Os runners julgados usam explicitamente o instrumento `legacy_*`.
> H17/H18/H19 estão bloqueadas no CLI antes de banco/ledger/desempenho:
> validar o dataset reconstruído e registrar a metodologia corrigida primeiro.
>
> [Implementação, evidências e limites](docs/research/2026-09-07-repairs.md).
> Suíte completa: **422 testes aprovados**, com cobertura; lint e Pyright verdes.
> Parser validado no ZIP integral 2023: 475 documentos DFP e 455 FRE.
> Nenhum resultado protegido observado; nenhuma dependência de runtime nova.


**Vigência:** 2026-09-06 (auditoria de prontidão; nenhuma nova rodada)

**H17-H19: PAUSE antes de desempenho.** A auditoria em
[docs/research/2026-09-06-readiness.md](docs/research/2026-09-06-readiness.md)
encontrou no DFP real associação de valores revisados à primeira entrega e
escala monetária incorreta. Os 100% de `known_at` preenchidos não demonstram
PIT por versão. `tools/audit_dfp_readiness.py` reproduz os bloqueios sem
avaliar retornos e sem abrir o banco. Não está ligado automaticamente ao
dispatcher de backtests; é uma checagem de auditoria com exit code 2 em falha.

Este é o ponto de entrada técnico corrente. O código, Git/CI e
`RESEARCH_FREEZE.md` prevalecem sobre documentação histórica.

## Estado canônico

```text
role = ACTIVE_RESEARCH_ASSET + REUSABLE_COMPONENT_LIBRARY + NEGATIVE_RESULT_CASE
research_state = REOPENED_BY_NEW_DATA_SOURCE          # ver HANDOFF.md, 2026-09-04
scientific_state = CLOSED_FOR_H1_THROUGH_H16          # as 16 primeiras seguem julgadas
                                                      # e FECHADAS; H17-H19 pré-registradas,
                                                      # NÃO rodadas
commercial_state = NOT_A_PRODUCT
new_scientific_trials = 3                             # H17 accruals, H18 E/P, H19 B/M
```

As famílias de fatores JÁ JULGADAS (H1/H2/H4/H5/H6/H7/H8/H9/H10/H11/H12/H13/
H14/H15/H16 — 15 no total, todas NOT_SUPPORTED; H3 não executada) e a linha RJ estão
encerradas/congeladas. **H11** (momentum 12-1 em RETORNO TOTAL, proventos
reinvestidos — corrige o viés só-preço das 9 anteriores) julgada
2026-09-04: NOT_SUPPORTED (DSR 0,8430 < 0,95 — o maior de toda a série).
**H12** (margem líquida isolada) e **H13** (crescimento de receita YoY,
primeira hipótese de CRESCIMENTO testada) julgadas na mesma sessão: ambas
NOT_SUPPORTED com DSR bem abaixo do limiar (0,1952 e 0,2598) — junto com
H7/H9 (ROE/alavancagem isoladas), esgotam o baralho de fatores extraíveis
da DFP consolidada da CVM sem uma fonte de dado genuinamente nova (fluxo
de caixa, múltiplos de mercado, dado intraday/institucional) ou universo
diferente. **H14** (proximidade da máxima 52 semanas), **H15** (surto de
volume) e **H16** (efeito virada-de-mês, primeira hipótese de TIMING
puro do domínio, motor de backtest dedicado) julgadas 2026-09-04: também
NOT_SUPPORTED (DSR 0,3249 / 0,2826 / 0,0052 — H16 a mais baixa de toda a
série). Com H14-H16, esgota-se também a linha de padrões técnicos/
calendário testável com os dados de preço já ingeridos (COTAHIST). Ver
HANDOFF.md "VEREDITO H11"/"VEREDITO H12 e H13"/"VEREDITO H14, H15 e H16"
para detalhes completos. Reabertura de qualquer uma das 16 exige o
dossiê completo definido em `RESEARCH_FREEZE.md` e informação
materialmente nova.

## H17-H19 — re-pré-registradas, aguardando integridade de dados (2026-09-06)

Decisão do operador de reabrir a pesquisa por **fonte de dado nova**, não por
recombinação do que já foi observado (o que seria p-hacking e segue recusado):

| # | fator | direção | dado novo | lacre |
|---|---|---|---|---|
| H17 | accruals `(lucro − FCO)/ativo` (Sloan 1996) | quintil INFERIOR | DFC-MI consolidada da CVM — 1ª demonstração nova desde o M2 | `e6cf9bd7454750c3` |
| H18 | earnings yield `E/P` (Basu; Fama-French) | quintil SUPERIOR | `shares_outstanding` (FRE, migração 0011) | `cbea4d3c98ac3422` |
| H19 | book-to-market `B/M` (Fama-French) | quintil SUPERIOR | idem H18 | `d96753f2af7b39a6` |

H18/H19 são os **primeiros fatores de VALOR** do domínio — as 15 julgadas
mediram qualidade do negócio ou comportamento do preço, nunca a razão entre
os dois. São hipóteses separadas de propósito (fluxo vs. estoque), cada uma
com registro próprio. Há 15 tentativas executadas; a ordem das três ainda
precisa ser congelada. O N nominal seria 16/17/18 na ordem de execução,
sem representar uma contabilidade completa de escolhas adaptativas.

**Estado: NENHUMA rodada real executada; dados ingeridos, prontidão refutada.**
Cobertura remensurada em conexão somente-leitura: medianas H17=56,
H18=49,5 e H19=53 em 104 datas. A ingestão precisa resolver versão/unidade
e base de ações em derivação isolada antes de qualquer veredito.

As 15 hipóteses já julgadas permanecem FECHADAS: nada aqui as reabre, e a
`reopen_policy` de `RESEARCH_FREEZE.md` §11 (6 campos + revisão humana)
continua valendo integralmente para elas.

## Dependência e vendor

- contrato: `predictor-core>=3.0,<4`;
- resolução canônica do CI/lock: wheel oficial `predictor-core==3.2.0`;
- `vendor/predictor_core/`: arquivo histórico íntegro, não runtime normal e não
  incluído no pacote `stocks-predictor`;
- `poc_leak.py`: PoC histórico contra o vendor legado, ativado apenas por execução
  explícita; importá-lo é inerte;
- `tests/conftest.py` e `tests/test_core_import_path.py`: impedem resolução silenciosa
  para o vendor;
- `tests/test_replay.py`: protege a fronteira temporal do Core instalado.

Estado:

```text
STOCKS_RUNTIME_CORE_SOURCE = CANONICAL_PACKAGE_ONLY
STOCKS_VENDOR_RUNTIME = UNREACHABLE_BY_DEFAULT
STOCKS_VENDOR_MIGRATION = CLOSED
LEGACY_VENDOR_LOOKAHEAD_CASE = PRESERVED
CANONICAL_TEMPORAL_GUARD = PASS
VENDOR_REINTRODUCTION_GUARD = PASS
```

## Alterações permitidas

Bug real, segurança, preservação, integridade de dependência — e o trabalho das
hipóteses H17-H19 pré-registradas acima. Mudanças de manutenção não promovem claim
científica ou comercial, e pré-registro NÃO é resultado: nenhuma claim pode ser feita
sobre H17-H19 antes da rodada real e do pedágio.

## Fontes

1. `RESEARCH_FREEZE.md` — estado científico, decisões e política de reabertura;
2. `pyproject.toml` e `uv.lock` — contrato de dependências;
3. `.github/workflows/ci.yml` — ambiente canônico de validação;
4. `poc_leak.py` e testes de import/replay — preservação e regressão anti-drift;
5. Git/CI — evidência mecânica atual.
