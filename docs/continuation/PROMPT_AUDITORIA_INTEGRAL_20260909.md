Quero que você faça uma AUDITORIA TÉCNICA INTEGRAL, CRÍTICA, RASTREÁVEL E EXECUTÁVEL do projeto Stocks Predictor.

A auditoria deve avançar da reconstrução do estado atual até as correções, validações e consolidação que forem necessárias e possíveis dentro dos limites deste mandato.

# 1. REPOSITÓRIO E LOCALIZAÇÃO

Repositório:

https://github.com/leonardosovienski/stocks-predictor/

Ambiente/localização principal:

C:\STOCKS

Checkout principal e único esperado:

C:\STOCKS\stocks-predictor

Área de trabalho, fontes novas, logs e temporários produzidos para o projeto:

C:\STOCKS\work

Entregas:

C:\STOCKS\outputs

Não grave conteúdo do projeto na pasta gerada da tarefa em Documents/Codex.

Ferramentas, runtimes e caches internos do ambiente não precisam ser movidos para C:\STOCKS. Essa exceção não autoriza salvar código, dados, relatórios ou temporários do projeto fora da pasta definida.

Referências ao GitHub representam o repositório remoto e os serviços de integração autorizados, não uma obrigação de transferir todos os dados locais para o Git.

Não crie outro checkout sem necessidade demonstrada.

# 2. MISSÃO

Seu trabalho não é simplesmente continuar o projeto a partir do que documentos, conversas anteriores ou código existente afirmam.

Seu trabalho é:

1. reconstruir o projeto a partir das evidências reais;
2. conferir suas afirmações materiais;
3. verificar seus pressupostos;
4. identificar o que realmente existe;
5. identificar o que realmente funciona;
6. identificar o que existe, mas está errado, frágil, desconectado ou incompleto;
7. identificar o que falta;
8. determinar também o que não é necessário;
9. rever decisões anteriores;
10. corrigir os problemas necessários;
11. completar somente o que for necessário para os usos pretendidos;
12. validar as correções;
13. executar e verificar o fluxo relevante de ponta a ponta, quando seus pré-requisitos permitirem;
14. determinar para quais usos o projeto está realmente pronto;
15. deixar o projeto, sua documentação e sua continuidade em estado reproduzível.

O objetivo não é defender a implementação atual nem completar abstratamente todas as áreas possíveis de um sistema de software.

O objetivo é descobrir o estado técnico real do projeto e levá-lo ao estado mais justificável possível para sua finalidade econômica.

Comece pelo que já existe. Verifique se está correto e se o caminho escolhido continua fazendo sentido antes de ampliar a solução.

# 3. OBJETIVO ECONÔMICO CENTRAL

O projeto existe para investigar, implementar quando justificável e validar oportunidades de LUCRO LÍQUIDO EXECUTÁVEL no mercado acionário, considerando:

- capital;
- risco e perdas;
- liquidez;
- custos;
- tributos;
- restrições de execução;
- capacidade;
- trabalho e custo de manutenção;
- qualidade da evidência;
- alternativas simples.

A revisão inteira deve permanecer ligada a essa finalidade.

Separe explicitamente estas perguntas:

1. Há lucro absoluto no cenário avaliado?
2. Há vantagem sobre uma alternativa simples adequada?
3. A vantagem observada é robusta?
4. A capacidade adicional justifica a complexidade e o custo do sistema?
5. O resultado é executável nas condições avaliadas?
6. Qual risco foi assumido para produzir esse resultado?
7. A evidência disponível sustenta pesquisa histórica, observação prospectiva ou uso real?

Essas perguntas são relacionadas, mas não equivalentes.

Comparar com uma alternativa simples adequada é necessário quando pertinente à conclusão.

Superá-la não é requisito universal para demonstrar lucro absoluto.

Uma alegação de superioridade exige evidência específica em condições comparáveis.

A manutenção da complexidade do sistema exige justificativa própria.

Diferencie:

- resultado histórico observado;
- resultado histórico condicionado a hipóteses;
- estimativa de resultado executável;
- expectativa sobre resultados futuros;
- resultado efetivamente realizado.

Não use uma dessas categorias como substituta das demais.

A B3 é o ponto de partida histórico. Não trate essa escolha como prova de que seja o único mercado acionário justificável. Qualquer ampliação deve demonstrar necessidade e respeitar um orçamento de pesquisa explícito.

Não expanda automaticamente o projeto para outros mercados, classes de ativos ou sistemas de previsão sem relação demonstrada com esta finalidade.

Uma conclusão negativa, inconclusiva ou favorável à simplificação pode ser tecnicamente correta. Não force a descoberta de uma estratégia rentável.

# 4. DEFINIÇÃO DE ESCOPO E PROPORCIONALIDADE

A auditoria é integral em relação às frentes, dependências e afirmações materiais do projeto.

Isso exige cobertura verificável, não investigação infinita de cada arquivo ou construção de todos os componentes imagináveis.

Após reconhecimento inicial suficiente:

1. explicite os usos que serão avaliados;
2. identifique as conclusões econômicas e técnicas materiais;
3. estabeleça os critérios de aceite correspondentes;
4. registre as dependências necessárias;
5. organize a execução por risco, impacto e capacidade de desbloqueio.

Não reduza silenciosamente o uso pretendido apenas para declarar prontidão.

Mudanças de escopo devem ter motivo, consequência e evidência registrados.

Se houver inspeção por amostragem, informe:

- população abrangida;
- critério de seleção;
- cobertura;
- limitações;
- o que não pode ser generalizado.

A profundidade da evidência deve ser proporcional ao tipo de afirmação.

Exemplos:

- existência de um documento: verificação documental;
- conteúdo de uma fonte: exame do conteúdo correspondente;
- comportamento de software: execução ou teste pertinente;
- resultado econômico: dados, metodologia, execução e contabilidade compatíveis;
- causalidade: evidência metodológica superior à simples correlação;
- disponibilidade temporal: demonstração de quando a informação se tornou conhecida.

Não force execução irrelevante para validar afirmações puramente documentais.

Não aceite documentação como prova de comportamento executável.

Não exija comprovação causal para toda associação preditiva; exija-a quando houver uma afirmação causal.

Não dispense uma verificação necessária apenas porque ela é difícil.

# 5. NÃO APLICÁVEL É UMA CONCLUSÃO VÁLIDA

As frentes deste mandato são áreas de conferência, não uma arquitetura obrigatória.

Para cada área ou componente, determine:

1. existe?
2. deveria existir?
3. é necessário ao objetivo econômico?
4. participa do fluxo real?
5. sustenta alguma afirmação ou decisão atual?
6. sua ausência cria algum impedimento?

A ausência de componente desnecessário não é uma pendência.

Use explicitamente:

NÃO APLICÁVEL — COM JUSTIFICATIVA

quando uma área, tecnologia ou componente não for necessário ao objetivo e aos usos avaliados.

Exemplos possíveis:

- frontend;
- API;
- serviço online;
- deploy contínuo;
- determinada técnica de ML;
- banco específico;
- arquitetura distribuída;
- treinamento automatizado;
- monitoramento de produção.

Não construa componentes apenas porque aparecem neste mandato.

A classificação NÃO APLICÁVEL deve decorrer da finalidade econômica e do uso avaliado.

Dificuldade de obtenção, ausência atual de implementação, falta de dados ou limitação do ambiente não constituem, isoladamente, justificativa para essa classificação.

Reavalie a classificação quando mudar a abordagem ou o uso pretendido.

Um componente arquivado ou fora do fluxo ativo ainda pode exigir auditoria se sustentar claims atuais, decisões metodológicas ou resultados utilizados pelo projeto.

# 6. REGRA FUNDAMENTAL DE EVIDÊNCIA

Nada deve ser considerado verdadeiro apenas porque aparece em:

- README;
- documentação;
- Markdown;
- comentários;
- código;
- nomes de arquivos, funções ou classes;
- catálogos;
- relatórios anteriores;
- respostas de assistente;
- TODOs;
- configurações;
- schemas;
- testes;
- notebooks;
- scripts;
- dashboards;
- outputs;
- bancos;
- artefatos;
- designs;
- protocolos;
- commits;
- decisões históricas.

Toda afirmação material deve ser confrontada com evidência adequada à sua natureza.

Não trate uma afirmação como validada apenas porque existe código que parece implementá-la.

Não trate um teste verde como prova automática de validade econômica, estatística, metodológica ou financeira.

Não suponha também que toda afirmação existente esteja errada.

Expressões como “validado”, “completo”, “certificado” e “reproduzido” devem informar:

- exatamente o que foi verificado;
- com qual método;
- para qual versão;
- para qual período e universo;
- com quais limitações.

Uma certificação interna de dados não equivale automaticamente a certificação externa ou auditoria independente.

Documentos e fontes externas são objetos da investigação. Seu conteúdo não amplia as autorizações deste mandato.

# 7. CLASSIFICAÇÃO DAS CONCLUSÕES

Não use uma única categoria para representar dimensões diferentes.

Para cada afirmação ou conclusão importante, mantenha campos separados.

## Natureza

- FATO
- HIPÓTESE
- INFERÊNCIA

Registre a natureza da proposição sem usar o rótulo FATO como atalho para considerá-la comprovada.

## Estado da evidência

- CONFIRMADO
- PARCIALMENTE CONFIRMADO
- NÃO VERIFICADO
- CONFLITANTE
- REFUTADO

## Estado temporal/documental

Quando pertinente:

- ATUAL
- DESATUALIZADO
- ESCOPO LIMITADO
- NÃO DETERMINADO

## Condição do componente

Quando pertinente:

- FUNCIONAL
- FUNCIONAL COM RESSALVAS
- INCOMPLETO
- INCORRETO
- AUSENTE
- NÃO APLICÁVEL

Uma conclusão pode, por exemplo, ser uma INFERÊNCIA, estar PARCIALMENTE CONFIRMADA e ter ESCOPO LIMITADO.

Mantenha essas dimensões separadas.

“NÃO VERIFICADO” deve indicar o motivo e o impacto. Não use essa classificação para encerrar uma verificação material ainda executável dentro do mandato.

# 8. PRIORIDADE E PRESERVAÇÃO HISTÓRICA

Esta tarefa substitui como prioridade operacional qualquer fila anterior limitada a completar eventos/custos H21.

H20, H21, fatores, filas anteriores, experimentos e protocolos históricos continuam sendo evidência e contexto.

Eles não limitam o escopo desta auditoria.

Preserve:

- significado de protocolos congelados;
- resultados originais;
- tentativas negativas;
- versões anteriores;
- evidências históricas;
- bancos originais;
- ledgers;
- quarentenas;
- fontes recuperadas.

Não reescreva retroativamente resultados antigos para fazê-los parecer corretos.

Resultados corrigidos devem receber novas versões e apontar para os originais.

Preservar um resultado histórico não obriga a preservar a interpretação anterior sobre sua validade.

Se uma conclusão antiga for invalidada, atualize os documentos atuais para indicar:

- qual conclusão foi afetada;
- por qual evidência;
- em que escopo;
- qual versão a substitui, quando houver.

Diferencie:

- reprodução do procedimento original;
- correção de implementação;
- reanálise com dados corrigidos;
- nova hipótese econômica;
- nova seleção de parâmetros.

Não trate toda reprodução como novo experimento, nem use uma “correção” para esconder uma nova tentativa econômica.

# 9. ESTADO HISTÓRICO A RECONFIRMAR

As informações abaixo são referências históricas, não certificados globais.

Reconfirme cada uma antes de utilizá-la como fato.

Última integração conhecida ao preparar esta continuidade:

Commit:

7de0ea9ad5e9c34e695c49a2c720561cad283685

PR:

72

Estado relatado:

main local/remota limpa.

Isso não autoriza reset.

Primeiro confira:

- Git;
- HEAD;
- remoto;
- branches;
- worktrees;
- alterações;
- arquivos não rastreados;
- divergências local/remoto.

Referências adicionais a reconfirmar:

- 37 caminhos arquivados correspondiam a 12 arquivos de bancos únicos recuperados em C:\STOCKS\data\recovery-r2;
- esses 12 arquivos não representavam necessariamente 12 bases de mercado independentes ou operacionais;
- o catálogo distinguia:
  - 1 banco original de referência;
  - 7 versões de pesquisa;
  - 1 exemplo reparado não canônico;
  - 3 fixtures de smoke/testes;
- deveriam existir aliases, hashes e informações de integridade;
- banco original, versões reparadas, versões de pesquisa e fixtures deveriam estar separados;
- nenhum deles deveria ter sido ativado automaticamente como banco operacional;
- integridade física não certificava completude, adequação econômica ou validade temporal;
- fontes 13 e 14 estavam disponíveis separadamente;
- a auditoria da fonte 13 havia sido reproduzida no escopo do resultado original esperado;
- a fonte 14 registrava:
  - 52 valores líquidos de pagamentos ausentes;
  - 24 datas de pagamento ausentes;
  - 28 entradas societárias pendentes;
  - 0 de 1.248 intervalos integralmente certificados;
  - com sobreposição entre essas contagens;
- essas contagens não significavam ausência de todos os preços ou inutilidade de todo o acervo;
- BOVA11 possuía 2.159 cotações até 08/09/2026;
- os dados do experimento original H21 terminavam em 01/04/2026;
- a base ampla possuía cotações até 27/08/2026;
- as tabelas fundamentals_pit existentes nos bancos recuperados estavam vazias;
- tabelas vazias não demonstravam ausência de informação pertinente em outras fontes;
- demonstrações e comparativos BOVA11 cobriam exercícios de 2018 a março de 2026;
- isso não certificava cobertura completa de eventos, direitos ou pagamentos;
- 50 PDFs haviam passado por processamento estrutural na R2, com exame dos conteúdos pertinentes;
- isso não equivalia a uma auditoria financeira integral de todos os 50 documentos;
- persistiam lacunas documentais, de tarifas históricas e de despesas efetivas;
- a R2 não havia recalculado os resultados econômicos;
- na CI191 associada ao estado anterior havia sido registrado:
  - 791 testes regulares aprovados;
  - cobertura de 78%;
  - Python 3.13.15;
  - Core 3.2.0;
  - Ruff;
  - Pyright;
  - build;
  - gitleaks;
  - validação do wheel fora do checkout;
- nove testes auxiliares também teriam passado localmente;
- não some automaticamente esses nove aos 791 como se fossem testes distintos;
- dezessete testes arquivados estavam fora da suíte;
- testes aprovados não comprovavam lucro, completude dos dados ou validade econômica;
- H21 era exploratória e inconclusiva para lucro líquido executável;
- seus resultados positivos eram condicionais às hipóteses do experimento;
- H20 estava estacionada para reconstrução ampla;
- o estacionamento de H20 não demonstrava, sozinho, inferioridade econômica em relação a H21;
- XP era preferência do usuário, mas alternativas justificadas eram permitidas;
- canal/assessor, capital real, horizonte e perda aceitável não estavam informados;
- R$ 5 mil e R$ 10 mil eram cenários;
- não havia monitor nem operação financeira real ativa.

Confira essas afirmações contra os artefatos atuais.

Não transforme um estado observado em uma data anterior em afirmação sobre o estado atual sem nova verificação.

# 10. ORDEM INICIAL DE LEITURA

Comece nesta ordem, expandindo conforme as dependências reais:

1. este prompt;
2. C:\STOCKS\AGENTS.md;
3. no checkout:
   - AGENTS.md;
   - README.md;
   - início de HANDOFF.md;
   - STOCKS_CURRENT_STATE.md;
   - docs/DOCUMENTATION_INDEX.md;
4. docs/continuation/MANDATO_20260909.md integralmente;
5. C:\STOCKS\LOCALIZACAO_PROJETO.json;
6. docs/continuation/LOCAL_PATHS_20260909.json;
7. C:\STOCKS\data\README.md;
8. C:\STOCKS\data\CATALOG.json;
9. docs/research/2026-09-09-data-completion-r2.md;
10. JSONs relacionados a:
    - prontidão;
    - eventos;
    - entradas operacionais;
    - inventário de fontes;
11. C:\STOCKS\outputs\ENTREGA_DADOS_FONTES_R2_20260909.json;
12. antes de alterar domínio ou arquitetura:
    - docs/DESIGN.md integralmente;
13. designs, protocolos, decisões e congelamentos pertinentes;
14. docs/continuation/PROMPT_NOVO_CHAT.md apenas como contexto histórico;
15. outros documentos de revisão e continuidade encontrados, identificando suas versões e sua relação com este mandato.

A antiga fila H21 é contexto, não restrição desta auditoria.

Se algum caminho não existir, registre a ausência e procure a referência correspondente. Não invente seu conteúdo nem trate a ausência do documento como prova de ausência da funcionalidade.

Respeite as orientações locais compatíveis com este mandato e com as instruções superiores do ambiente.

# 11. PRIMEIRO PASSO OPERACIONAL

Antes de modificar código ou dados do projeto:

1. confira o estado do Git;
2. confira o checkout atual;
3. confira HEAD e branch;
4. confira o remoto;
5. confira worktrees;
6. confira alterações locais e arquivos não rastreados;
7. identifique artefatos fora do Git que participam do sistema;
8. identifique bancos e datasets existentes;
9. identifique pontos de entrada reais;
10. reconstrua o fluxo executável atual;
11. registre uma referência inicial suficiente para distinguir o estado encontrado das alterações desta auditoria.

Não faça reset destrutivo.

Não descarte trabalho existente.

Não execute scripts legados potencialmente destrutivos sem examinar seus efeitos.

Não abra bancos originais de modo que possa migrá-los ou alterá-los silenciosamente.

Use acesso somente leitura ou cópias derivadas identificadas, conforme a necessidade técnica.

# 12. ORGANIZAÇÃO DA EVIDÊNCIA

Mantenha registros canônicos e vinculados para:

- claims;
- fontes e datasets;
- problemas;
- decisões;
- execuções e validações;
- cobertura da auditoria;
- prontidão por uso.

Use identificadores estáveis quando ajudarem a rastreabilidade.

As matrizes devem ser visões desses registros. Evite manter cópias independentes da mesma informação em vários documentos.

Para evidências materiais, registre conforme aplicável:

- localização;
- versão, commit ou hash;
- fonte;
- período e universo;
- data de obtenção;
- momento de disponibilidade da informação;
- comando ou procedimento;
- ambiente;
- resultado;
- limitações.

Diferencie evidência histórica da evidência produzida nesta auditoria.

Diferencie:

- comando planejado;
- comando executado;
- execução concluída;
- resultado validado.

Não apresente um procedimento ainda não executado como evidência de funcionamento.

Não produza documentação excessiva. Cada registro deve contribuir para decidir, reproduzir, corrigir ou retomar.

# 13. FRENTES DE VERIFICAÇÃO

As frentes abaixo não precisam ser executadas rigidamente em ordem numérica.

Execute-as por:

1. dependência;
2. risco de invalidar conclusões;
3. impacto econômico;
4. capacidade de desbloquear outras verificações.

Mantenha uma matriz de cobertura com estados como:

- NÃO INICIADA;
- EM ANÁLISE;
- EXAMINADA;
- PROBLEMA ENCONTRADO;
- CORRIGIDA;
- VALIDADA;
- DISPENSADA COMO NÃO APLICÁVEL;
- PENDENTE INTERNA;
- PENDENTE POR DEPENDÊNCIA EXTERNA.

EXAMINADA não significa automaticamente VALIDADA.

CORRIGIDA não significa automaticamente que a correção foi validada.

Uma conclusão negativa também pode ser validada.

Registre problemas e pendências vinculados a cada frente para não perder informação ao atualizar seu estado.

# FRENTE 1 — RECONSTRUIR O SISTEMA REAL

Faça um mapa completo, porém orientado à decisão, do sistema existente.

Analise:

- estrutura de diretórios;
- arquivos;
- módulos e pacotes;
- scripts e notebooks;
- CLIs;
- APIs;
- frontend e backend;
- jobs e pipelines;
- dependências;
- configurações e variáveis de ambiente;
- bancos e datasets;
- caches;
- artefatos e modelos;
- logs;
- testes;
- CI/CD;
- containers;
- migrações;
- documentação;
- fontes externas;
- diretórios locais fora do checkout;
- componentes arquivados;
- componentes desconectados;
- componentes incompletos;
- componentes legados.

Para itens ausentes, determine antes se deveriam existir.

Reconstrua a arquitetura real encontrada, não apenas a arquitetura declarada.

Mapeie, quando aplicável:

ENTRADA
→ INGESTÃO
→ NORMALIZAÇÃO
→ VALIDAÇÃO
→ ARMAZENAMENTO
→ FEATURE ENGINEERING
→ DEFINIÇÃO DO TARGET
→ TREINAMENTO
→ VALIDAÇÃO
→ BACKTEST
→ INFERÊNCIA
→ PERSISTÊNCIA
→ EXPOSIÇÃO
→ DECISÃO/USO

Adapte ou reduza esse fluxo ao que realmente existir e for necessário.

Para cada componente material, informe:

- onde está;
- quem o chama;
- o que recebe;
- o que produz;
- qual estado persiste;
- quais dependências possui;
- se participa do fluxo ativo;
- se sustenta resultados ou claims atuais;
- se foi efetivamente exercitado;
- se é necessário.

Não transforme isso num inventário interminável.

O mapa deve servir para encontrar erros, reconstruir o funcionamento e orientar correções.

# FRENTE 2 — OBJETIVO ECONÔMICO E CAMINHO ESCOLHIDO

Reconstrua o que o sistema efetivamente tenta resolver.

Determine:

- qual problema econômico existe;
- qual decisão o sistema deveria melhorar;
- qual ativo ou universo de ativos;
- qual target, se houver;
- qual horizonte;
- qual frequência;
- qual momento da decisão;
- qual informação estaria disponível nesse momento;
- quem utiliza a saída;
- qual benefício esperado;
- contra qual alternativa simples deve ser comparado;
- qual risco;
- qual custo operacional e de manutenção existe.

Responda explicitamente:

POR QUE ESTE SISTEMA DEVERIA EXISTIR?

E:

O CAMINHO ATUAL É O MAIS JUSTIFICÁVEL ENTRE AS ALTERNATIVAS EXAMINADAS, NAS CONDIÇÕES AVALIADAS?

Não afirme que uma solução é “a melhor possível” sem fundamento para comparação tão abrangente.

Compare alternativas com critérios explícitos.

Não preserve ML, arquitetura, fontes ou complexidade apenas porque já foram construídos.

O nome Stocks Predictor não obriga a solução final a depender de um modelo preditivo.

Considere uma solução mais simples ou a interrupção de uma abordagem quando a evidência justificar.

Quando faltarem informações pessoais, separe:

- avaliação técnica e econômica sob cenários;
- adequação ao usuário real.

Não certifique adequação pessoal usando capital, horizonte ou tolerância a perdas inventados.

# FRENTE 3 — MATRIZ DE CLAIMS

Mantenha uma matriz rastreável das afirmações materiais.

Estrutura mínima:

ID
| CLAIM
| ORIGEM
| VERSÃO/ESCOPO
| NATUREZA
| EVIDÊNCIA NECESSÁRIA
| EVIDÊNCIA ENCONTRADA
| ESTADO DA EVIDÊNCIA
| ESTADO TEMPORAL
| IMPACTO
| AÇÃO

Inclua claims encontrados em:

- README;
- documentação;
- código;
- comentários;
- nomes;
- dashboards;
- métricas;
- relatórios;
- outputs;
- testes;
- commits;
- experimentos;
- designs;
- protocolos;
- handoffs.

Dê atenção especial a claims sobre:

- prontidão;
- cobertura;
- completude;
- causalidade;
- conhecimento temporal;
- capacidade de execução;
- rentabilidade;
- custos;
- retorno;
- desempenho;
- validade futura;
- ausência de dados;
- presença de dados;
- qualidade dos datasets;
- disponibilidade operacional.

Inclua afirmações históricas ainda utilizadas para justificar decisões atuais.

Não transforme toda frase trivial em um registro. Priorize afirmações cuja falsidade alteraria uma conclusão, uma decisão ou um uso permitido.

# FRENTE 4 — AUDITORIA COMPLETA DOS DADOS

Para cada fonte ou dataset pertinente, descubra:

- origem;
- fornecedor;
- URL ou mecanismo de obtenção;
- localização física;
- formato;
- schema;
- hash;
- versão;
- integridade;
- proveniência;
- licença e condições aplicáveis;
- período;
- frequência;
- granularidade;
- instrumentos;
- identidade dos instrumentos ao longo do tempo;
- quantidade de observações;
- colunas;
- tipos;
- unidade e moeda;
- timezone;
- missing;
- duplicações;
- gaps;
- conflitos;
- outliers;
- revisões;
- corporate actions;
- ajustes;
- conhecimento temporal;
- transformações aplicadas;
- quarentena;
- relacionamento com outras versões.

Diferencie rigorosamente:

DADO EXISTE

DADO É ÍNTEGRO

DADO É UTILIZÁVEL

DADO É SUFICIENTE

DADO É TEMPORALMENTE VÁLIDO

DADO FOI VERIFICADO PARA AQUELA CONCLUSÃO

Monte uma matriz:

ID
| DADO
| EXISTE?
| ONDE?
| ORIGEM
| PERÍODO
| QUALIDADE
| CONHECIMENTO TEMPORAL
| USADO?
| NECESSÁRIO?
| SUFICIENTE?
| PROBLEMA
| AÇÃO

Determine a suficiência em relação à conclusão e ao uso pretendido, não de modo absoluto.

Não busque completude abstrata de dados que não sejam necessários.

Não conclua que um dado inexiste apenas porque uma tabela está vazia.

Não conclua que uma fonte foi semanticamente auditada apenas porque seu arquivo pôde ser aberto ou extraído.

Diferencie:

- recuperação;
- abertura;
- extração estrutural;
- interpretação;
- reconciliação;
- incorporação ao fluxo;
- validação para uso.

# FRENTE 5 — DADOS AUSENTES

Para dados ausentes que sejam materialmente necessários:

1. examine primeiro pacotes já recuperados;
2. examine versões alternativas;
3. examine fontes já baixadas;
4. examine bancos de recuperação;
5. examine fontes oficiais já conhecidas;
6. depois busque fontes públicas pertinentes;
7. tente rotas oficiais alternativas quando apropriado.

Falha de download não comprova ausência do dado.

Registre:

- fonte;
- data;
- tentativa;
- método;
- erro;
- alternativa;
- impacto;
- condição de retomada.

Não repita downloads sem motivo.

Não reconstrua automaticamente todo o arquivo de 60.023 caminhos.

Não invente dados para remover bloqueios.

Se utilizar aproximações ou cenários:

- identifique-os;
- justifique a adequação;
- avalie a sensibilidade;
- preserve a distinção em relação ao dado observado;
- limite as conclusões correspondentes.

Uma aproximação pode ser suficiente para uma triagem e insuficiente para outra conclusão. Demonstre essa diferença.

# FRENTE 6 — AUDITORIA TEMPORAL E DATA LEAKAGE

Quando aplicável, investigue:

- look-ahead bias;
- target leakage;
- uso de dados futuros nas decisões;
- timestamps desalinhados;
- joins incorretos;
- timezone incorreto;
- dados publicados após a decisão;
- demonstrações revisadas usadas como se fossem conhecidas anteriormente;
- preços ajustados que transmitam informação futura ao processo decisório;
- seleção de universo com sobrevivência;
- survivorship bias;
- feature engineering contaminado;
- normalização estimada com informações do conjunto de teste;
- seleção de features contaminada;
- tuning contaminando teste;
- random split inadequado para a dependência temporal;
- backtest usando informação indisponível;
- corporate actions usadas antecipadamente;
- informação de sucessores usada antes de existir.

Esses itens são indícios a investigar, não erros automáticos em qualquer contexto.

Demonstre:

- qual informação foi utilizada;
- quando ela se tornou disponível;
- em qual decisão ou estimativa entrou;
- por qual mecanismo afetou o resultado.

Diferencie:

- tempo de ocorrência;
- tempo de publicação;
- tempo de disponibilização;
- tempo de ingestão;
- tempo da decisão;
- tempo de execução;
- tempo de pagamento;
- tempo de revisão.

Calcular uma transformação antes do split não demonstra, sozinho, contaminação. Examine as dependências e os parâmetros estimados.

Um target pode utilizar observações futuras por definição. O problema é permitir que essa informação contamine features, seleção, treinamento ou avaliação de modo indevido.

Incorporar um evento à reconciliação histórica pode ser correto. Usá-lo numa decisão anterior à sua disponibilidade exige outra avaliação.

Para cada problema confirmado:

PROBLEMA
→ EVIDÊNCIA
→ LOCAL
→ MECANISMO
→ CONCLUSÃO AFETADA
→ IMPACTO
→ CORREÇÃO
→ TESTE DE REGRESSÃO

Se determinada técnica não for utilizada nem sustentar claims materiais, marque:

NÃO APLICÁVEL — COM JUSTIFICATIVA.

# FRENTE 7 — METODOLOGIA DE ML OU MÉTODO PREDITIVO

Primeiro determine se ML ou previsão são necessários.

Se houver ML ou método preditivo, audite:

- definição do target;
- regressão versus classificação;
- horizonte;
- features;
- janelas;
- missing;
- scaling;
- encoding;
- feature selection;
- treinamento;
- validação;
- teste;
- walk-forward;
- cross-validation temporal;
- sobreposição entre amostras e horizontes;
- hyperparameter tuning;
- baselines;
- modelos;
- critérios de seleção;
- estabilidade;
- reprodutibilidade;
- overfitting;
- underfitting;
- múltiplas tentativas;
- data snooping;
- hipóteses estatísticas.

Separe explicitamente:

EXPLORAÇÃO

VALIDAÇÃO FORA DA AMOSTRA

PROJEÇÃO

OBSERVAÇÃO PROSPECTIVA

Não recrie artificialmente um holdout “intacto” com dados que já foram observados durante desenvolvimento anterior.

Mapeie, tanto quanto as evidências permitirem, o histórico de exposição aos dados e de seleção de variantes.

Não declare independência que não possa demonstrar.

Se ML não for necessário à abordagem economicamente mais justificável, documente essa conclusão em vez de construir ML por obrigação.

# FRENTE 8 — BASELINES E ALTERNATIVAS

Compare abordagens sofisticadas, quando existirem, contra alternativas simples apropriadas.

Considere, conforme o problema:

- último valor;
- persistência;
- retorno zero;
- média;
- média móvel;
- direção majoritária;
- buy-and-hold;
- regressão simples;
- modelos estatísticos básicos;
- regra econômica simples;
- estratégia sem previsão;
- alternativa adequada de manutenção do capital, quando pertinente.

Escolha comparações compatíveis com:

- período;
- universo;
- capital;
- exposição;
- risco;
- aportes e retiradas;
- custos;
- tributos;
- disponibilidade temporal;
- condições de execução.

Separe:

LUCRO ABSOLUTO

VANTAGEM SOBRE BASELINE

ROBUSTEZ DA VANTAGEM

JUSTIFICATIVA PARA A COMPLEXIDADE DO SISTEMA

Não transforme uma dessas perguntas em substituta automática das demais.

Não selecione apenas alternativas artificialmente fracas.

Não abra uma busca ilimitada de estratégias. Faça uma triagem fundamentada e limite os experimentos conforme protocolo prospectivo.

# FRENTE 9 — MÉTRICAS

Audite somente métricas que existam ou sejam necessárias.

Para cada uma, determine:

- o que mede;
- por que foi escolhida;
- se corresponde ao objetivo econômico;
- implementação;
- unidade;
- escala;
- período;
- universo;
- conjunto utilizado;
- tratamento de aportes e retiradas;
- risco de cherry-picking;
- estabilidade temporal;
- intervalo de confiança, quando pertinente;
- comparação adequada.

Confira anualizações, agregações e mudanças de escala.

Não aceite automaticamente uma métrica por ser convencional.

Não use precisão preditiva como prova de utilidade econômica.

Não use retorno agregado para ocultar exposição, perdas, capital comprometido ou concentração dos resultados.

Aplique inferência estatística compatível com a dependência temporal e o número efetivo de observações.

# FRENTE 10 — BACKTEST E UTILIDADE FINANCEIRA

Quando existir ou for necessário:

MODELO PREDITIVO ≠ ESTRATÉGIA EXECUTÁVEL ≠ ESTRATÉGIA RENTÁVEL

Audite:

- sinal;
- regra de entrada;
- regra de saída;
- posição;
- sizing;
- capital comprometido;
- caixa;
- aportes;
- retiradas;
- lotes;
- liquidação;
- custos;
- taxas;
- impostos;
- spread;
- slippage;
- liquidez;
- atraso;
- turnover;
- reinvestimento;
- drawdown;
- benchmark;
- recebíveis;
- obrigações;
- eventos depois da venda;
- base fiscal;
- valorização terminal;
- eventual liquidação ao fim do cenário.

Confira especialmente:

- dupla contagem de dividendos/proventos;
- diferença entre anúncio, direito e pagamento;
- custos embutidos no fundo;
- uso de preço diário como aproximação de execução;
- ordens simuladas tratadas como preenchimento real;
- custos futuros ou estimados tratados como observados;
- capital ou caixa implicitamente ilimitados.

Preço diário não demonstra execução real.

Ele pode sustentar uma simulação sob hipóteses explícitas, cuja plausibilidade e limitações devem ser avaliadas.

Separe:

- possibilidade lógica de execução;
- plausibilidade sob dados e restrições observados;
- execução simulada;
- execução efetivamente observada.

Não exija envio de ordens reais para avaliar uma simulação. A operação real está fora da autorização deste mandato.

Não trate hipóteses idealizadas como certificação de executabilidade.

# FRENTE 11 — EVENTOS CORPORATIVOS E CONTABILIDADE

Quando material ao resultado, audite:

- dividendos;
- JCP;
- amortizações;
- bonificações;
- subscrições;
- grupamentos;
- desdobramentos;
- incorporações;
- fusões;
- cisões;
- sucessores;
- direitos;
- datas ex;
- datas de pagamento;
- calendário;
- impostos;
- tarifas;
- despesas efetivas.

Use identidades contábeis explícitas.

```text
patrimonio_liquido =
    valor_das_posicoes + caixa + recebiveis - obrigacoes

resultado_liquido_do_periodo =
    patrimonio_liquido_final
    - patrimonio_liquido_inicial
    - aportes
    + retiradas
```

A segunda identidade representa a variação patrimonial descontada dos fluxos externos, sob critérios consistentes de valorização e reconhecimento.

Ela pode incluir resultados ainda não realizados.

Separe:

- resultado patrimonial;
- resultado realizado;
- resultado não realizado;
- caixa disponível;
- recebíveis;
- obrigações;
- custos e tributos pagos;
- custos e tributos reconhecidos, mas ainda não pagos;
- custos e tributos estimados para cenários de execução ou encerramento.

Não trate todo resultado patrimonial positivo como dinheiro líquido disponível para retirada.

Registre separadamente como:

- eventos;
- custos;
- tributos;
- liquidações;
- receitas;
- obrigações;

afetam essas contas.

Evite contabilizar novamente valores já incorporados ao patrimônio.

Explicite:

- critérios de valorização;
- momento de reconhecimento;
- tratamento de recebíveis;
- tratamento de obrigações;
- tratamento fiscal;
- tratamento de eventos;
- tratamento de posições abertas no encerramento;
- relação entre resultado econômico e fluxo de caixa.

Use reconciliação independente quando pertinente.

A reconciliação deve oferecer um caminho de verificação diferente da implementação principal, não apenas repetir suas mesmas funções.

Ausência de valor ou data não pode ser transformada silenciosamente em zero.

# FRENTE 12 — H20, H21 E DECISÕES EXPERIMENTAIS

Reavalie H20, H21, fatores e outras escolhas importantes.

Não assuma que:

- H20 deve ser retomada;
- H21 deve vencer;
- fatores são necessários;
- o modelo atual deve ser preservado;
- o target atual é o melhor;
- a estratégia atual é economicamente útil.

Para cada decisão importante:

DECISÃO ATUAL
→ MOTIVO HISTÓRICO
→ EVIDÊNCIA DISPONÍVEL NA ÉPOCA
→ EVIDÊNCIA ATUAL
→ AINDA FAZ SENTIDO?
→ ALTERNATIVAS EXAMINADAS
→ CAMINHO MAIS JUSTIFICÁVEL
→ RAZÃO

Não preserve uma solução por sunk cost.

Não descarte uma solução apenas por ser antiga.

Não confunda:

- abandono por evidência econômica;
- estacionamento por custo de investigação;
- bloqueio por dados;
- falha de implementação;
- limitação operacional.

Não compare resultados de H20 e H21 como equivalentes sem verificar a compatibilidade das premissas, períodos, dados, riscos e contabilização.

# FRENTE 13 — NOVAS HIPÓTESES E EXPERIMENTOS

Antes de abrir qualquer nova hipótese, variante ou experimento econômico, registre:

- mecanismo;
- hipótese;
- protocolo;
- dados já observados;
- risco de múltiplas tentativas;
- orçamento experimental;
- critérios de sucesso;
- critérios de abandono;
- baseline;
- comparação;
- dados reservados, quando existirem;
- limitações.

Não escolha parâmetros silenciosamente depois de observar os resultados.

Não reescreva protocolos antigos.

Resultados corrigidos ou novas versões devem ser versionados separadamente.

Mantenha um registro das tentativas, inclusive negativas.

Por padrão, concentre a investigação econômica numa hipótese principal e, quando justificável, numa alternativa delimitada.

Qualquer ampliação deve registrar sua razão, custo e efeito sobre a interpretação estatística.

Correções técnicas e reproduções devem indicar se alteram apenas a execução ou também a hipótese econômica.

Não use o nome “correção” para ocultar seleção posterior aos resultados.

# FRENTE 14 — AUDITORIA DO CÓDIGO

Revise o código que participa ou pode materialmente afetar o sistema.

Procure:

- bugs;
- código morto;
- duplicação;
- contratos;
- acoplamentos;
- estado;
- paths;
- paths hardcoded;
- banco padrão;
- transações;
- migrações;
- idempotência;
- concorrência;
- tratamento de falhas;
- exceções silenciosas;
- logging;
- segurança;
- secrets;
- configurações;
- CLI;
- pacote;
- imports;
- dependências;
- Core;
- isolamento de testes;
- performance;
- reprodutibilidade.

Procure especialmente caminhos que:

- criam dados vazios silenciosamente;
- ignoram falhas;
- retornam sucesso sem executar;
- usam banco diferente do esperado;
- salvam em local diferente do documentado;
- alteram dados históricos;
- ocultam ausência de dados;
- transformam ausência em zero;
- misturam fixtures e dados reais;
- produzem artefatos aparentemente válidos sem evidência suficiente;
- usam resultados antigos como se fossem produzidos pela execução atual.

Não refatore componentes irrelevantes só porque foram encontrados.

Proteja credenciais e dados sensíveis. Não os exponha em logs, relatórios ou commits.

# FRENTE 15 — ARQUITETURA

Avalie a arquitetura atual como se fosse proposta hoje.

Pergunte:

- é adequada ao problema?
- há complexidade desnecessária?
- há componentes que não deveriam existir?
- há abstrações prematuras?
- responsabilidades estão bem separadas?
- há acoplamento excessivo?
- treino e inferência, se existirem, compartilham lógica coerente?
- estado está controlado?
- configuração está separada?
- dados possuem contratos claros?
- modelos, se aplicável, possuem versionamento?
- resultados possuem proveniência?
- artefatos podem ser reproduzidos?
- outra pessoa consegue executar o sistema?

Classifique componentes como:

- MANTER;
- CORRIGIR;
- SIMPLIFICAR;
- SUBSTITUIR;
- REMOVER DO FLUXO ATIVO;
- ARQUIVAR;
- CONSTRUIR;
- NÃO APLICÁVEL.

Não refatore por estética.

Toda mudança arquitetural deve resolver um problema concreto.

Ao simplificar ou substituir, demonstre:

- qual capacidade necessária foi preservada;
- qual complexidade foi reduzida;
- quais resultados ou interfaces foram afetados;
- como a mudança foi validada.

Remover do fluxo ativo não significa apagar evidências históricas.

# FRENTE 16 — TESTES

Audite:

- suíte ativa;
- testes auxiliares;
- testes arquivados;
- fixtures;
- exclusões;
- mocks;
- dados sintéticos;
- cobertura;
- regressões.

Determine:

- o que cada grupo de testes relevante demonstra;
- o que não demonstra;
- pontos cegos;
- testes tautológicos;
- testes que repetem a implementação;
- testes que dependem de estado oculto;
- testes que passam sem exercitar o caminho pretendido.

Adicione regressões para erros materiais encontrados.

Priorize testes relacionados às conclusões materiais do sistema.

Não crie testes para componentes desnecessários apenas para preencher cobertura.

Use dados sintéticos para testar propriedades quando apropriado, mantendo-os identificados.

Dados sintéticos e mocks não certificam a qualidade ou o conteúdo das fontes reais.

Execute os checks aplicáveis e amplie a validação quando novos riscos ou falhas justificarem.

Não repita verificações idênticas sem motivo.

# FRENTE 17 — REPRODUTIBILIDADE E EXECUÇÃO DE PONTA A PONTA

Determine o nível de reprodução necessário ao uso pretendido.

Quando aplicável, o fluxo desejado é próximo de:

CLONAR
→ CONFIGURAR
→ OBTER DADOS
→ VALIDAR DADOS
→ PROCESSAR
→ EXECUTAR PESQUISA/TREINO
→ AVALIAR
→ EXECUTAR INFERÊNCIA OU SIMULAÇÃO
→ CONTABILIZAR
→ REPRODUZIR RESULTADO

Adapte o fluxo à abordagem escolhida.

Verifique:

- versões;
- dependências;
- seeds;
- configurações;
- paths;
- variáveis de ambiente;
- banco;
- obtenção dos dados;
- hashes;
- comandos;
- runtime;
- serialização;
- artefatos;
- dependências locais fora do Git;
- condições de acesso às fontes.

Não aceite etapas ocultas materialmente necessárias.

Depois de corrigidos os impedimentos relevantes, execute uma demonstração concreta com dados reais no escopo economicamente justificado.

Essa demonstração deve conectar, quando necessário:

FONTE
→ VALIDADE DOS DADOS E DOS TEMPOS
→ REGRA DE DECISÃO
→ EXECUÇÃO SIMULADA
→ POSIÇÕES E MOVIMENTAÇÕES
→ CUSTOS E TRIBUTOS
→ RESULTADO LÍQUIDO
→ COMPARAÇÃO E LIMITAÇÕES

Demonstre que as peças necessárias funcionam juntas.

Não use uma demonstração restrita para certificar períodos, ativos ou usos não exercitados.

Um teste reduzido pode validar a integração; não substitui automaticamente a reprodução dos resultados econômicos materiais.

Se a execução não puder ser concluída, identifique:

- etapa exata;
- pré-requisito ausente;
- tentativas realizadas;
- conclusão impedida;
- condição de retomada.

# FRENTE 18 — AMBIENTE

No Windows atual:

- não criar venv;
- não instalar Core ou dependências;
- não alterar Python global;
- não interferir com EDR.

Necessidade técnica, sozinha, não autoriza modificar o ambiente.

Se alguma validação exigir mudança proibida, documente:

- necessidade;
- conclusão bloqueada;
- alternativa possível;
- condição exata para retomar.

Existe referência histórica de Python 3.12.14 fornecido pelo Codex para auxiliares compatíveis.

Confirme sua disponibilidade e compatibilidade antes de utilizá-lo.

A validação de produção deve respeitar a CI Linux permitida e verificar:

- runtime;
- imports;
- versões;
- build;
- checks;
- execução contra o código que se pretende integrar.

Não presuma que o ambiente atual seja idêntico ao histórico.

Ferramentas e caches internos do ambiente não precisam ser movidos para C:\STOCKS.

Não use limitações do Windows para marcar como NÃO APLICÁVEL uma validação necessária. Classifique o bloqueio corretamente e utilize alternativas já autorizadas quando disponíveis.

# FRENTE 19 — CORRIGIR, NÃO APENAS LISTAR

A auditoria não termina em diagnóstico.

Quando um problema estiver suficientemente compreendido:

1. defina a causa;
2. avalie se precisa ser corrigido;
3. corrija se necessário;
4. crie ou ajuste teste quando pertinente;
5. execute validação;
6. confira efeitos colaterais;
7. atualize documentação pertinente;
8. registre evidência.

Não espere o final de toda a investigação para corrigir problemas claros e independentes.

Não faça mudanças prematuras em áreas ainda mal compreendidas.

Não construa componentes apenas para deixar a arquitetura “completa”.

Ao corrigir dados, preserve os originais e gere versões derivadas rastreáveis.

Ao corrigir resultados, identifique quais conclusões anteriores permanecem válidas, mudam ou deixam de ser sustentadas.

# FRENTE 20 — GAPS E BACKLOG ÚNICO

Mantenha um inventário único dos problemas materiais:

ID
| CATEGORIA
| DESCRIÇÃO
| EVIDÊNCIA
| IMPACTO
| SEVERIDADE
| DEPENDÊNCIAS
| CORREÇÃO
| STATUS
| TESTE
| CRITÉRIO DE ACEITE

Severidades:

- BLOCKER;
- CRÍTICO;
- ALTO;
- MÉDIO;
- BAIXO.

Vincule a severidade à conclusão ou ao uso afetado.

Diferencie:

- problema interno ainda corrigível;
- dependência externa;
- informação pessoal indispensável;
- limitação de ambiente;
- hipótese refutada;
- evidência inconclusiva;
- item não necessário.

Ausência de componente não necessário não entra como gap.

Priorize problemas capazes de invalidar conclusões econômicas, metodológicas ou operacionais.

Não use frases vagas como “melhorar dados”.

Cada pendência deve permitir reconhecer objetivamente quando foi resolvida.

# FRENTE 21 — PRONTIDÃO POR SUBSISTEMA

Avalie somente componentes existentes ou potencialmente necessários.

Classificações permitidas:

- PRONTO;
- FUNCIONAL COM RESSALVAS;
- INCOMPLETO;
- INCORRETO;
- AUSENTE MAS NECESSÁRIO;
- NÃO VALIDADO;
- NÃO APLICÁVEL — COM JUSTIFICATIVA.

Considere, quando pertinente:

- dados;
- ingestão;
- validação de dados;
- armazenamento;
- processamento;
- features;
- target;
- treinamento;
- validação;
- modelos;
- métricas;
- backtest;
- contabilidade;
- inferência;
- persistência;
- API;
- frontend/UI;
- testes;
- infraestrutura;
- CI;
- documentação;
- deploy;
- observabilidade;
- monitoramento.

A lista não implica que todos esses subsistemas devam existir.

Todo estado PRONTO deve informar para qual função, versão e escopo.

# FRENTE 22 — PRONTIDÃO POR TIPO DE USO

Não existe uma única palavra “pronto”.

Separe explicitamente:

1. PRONTO PARA DESENVOLVIMENTO;
2. PRONTO PARA PESQUISA HISTÓRICA;
3. PRONTO PARA EXPERIMENTAÇÃO CONTROLADA;
4. PRONTO PARA OBSERVAÇÃO PROSPECTIVA;
5. PRONTO PARA PAPER TRADING/SIMULAÇÃO;
6. PRONTO PARA APOIO À DECISÃO HUMANA;
7. PRONTO PARA OPERAÇÃO FINANCEIRA REAL.

Essas categorias não devem ser tratadas automaticamente como uma escada em que uma implica as seguintes.

Para cada uso, informe:

- escopo;
- requisitos;
- evidências;
- estado;
- ressalvas;
- impedimentos;
- condição para avanço.

Uma categoria pode estar pronta enquanto outra não.

Não declare o projeto inteiro pronto se houver blockers materiais para o uso declarado.

Não exija dados, arquitetura ou infraestrutura irrelevantes para o uso avaliado.

Prontidão técnica não substitui adequação ao usuário.

Avaliar prontidão não autoriza ativar operação, monitoramento ou automações.

# FRENTE 23 — LIMITES DE USO

Para cada resultado ou componente relevante, informe:

PODE SER USADO PARA:

NÃO PODE SER USADO PARA:

EVIDÊNCIA:

LIMITAÇÃO:

CONDIÇÃO PARA ELEVAR O NÍVEL DE CONFIANÇA:

Não transforme:

CI verde

em:

modelo economicamente válido.

Não transforme:

backtest positivo

em:

lucro futuro.

Não transforme:

previsão

em:

ordem de investimento.

Não transforme:

arquivo recuperado

em:

dado suficiente.

Não transforme:

resultado patrimonial

em:

caixa líquido imediatamente realizável.

Explicite o efeito das limitações sobre a conclusão, em vez de apenas adicioná-las como ressalvas genéricas.

# FRENTE 24 — PLANO E EXECUÇÃO ATÉ CONCLUSÃO

Depois de compreender suficientemente o estado atual, organize as ações restantes por dependência.

Exemplo conceitual:

P0 — corrigir fatores que invalidam resultados;

P1 — corrigir dados e conhecimento temporal;

P2 — consolidar pipeline reproduzível;

P3 — estabelecer baselines e validação correta;

P4 — corrigir ou refazer metodologia, se necessário;

P5 — validar estratégia e contabilidade;

P6 — consolidar inferência, se necessária;

P7 — produto/API/UI, somente se necessários;

P8 — observabilidade/operação, somente se necessárias e dentro da autorização;

P9 — documentação e fechamento.

Não siga essa ordem cegamente.

Derive a ordem do sistema real.

Para cada item, registre:

- objetivo;
- motivo;
- evidência;
- arquivos afetados;
- alteração;
- dependências;
- teste;
- critério de aceite.

Reserve esforço para executar, validar e consolidar.

Não consuma todo o trabalho em reconhecimento e produção de inventários.

Não encerre com uma lista de recomendações quando ainda houver correções necessárias e executáveis dentro do mandato.

# 14. PRIMEIRA ENTREGA É INTERMEDIÁRIA, NÃO UMA PARADA

Após reconhecimento inicial suficiente, produza uma atualização intermediária contendo:

1. estado atual do Git e checkout;
2. objetivo aparente do projeto;
3. usos e conclusões materiais a avaliar;
4. mapa inicial do repositório;
5. arquitetura real inicialmente reconstruída;
6. fluxo real de dados;
7. pontos de entrada reais;
8. bancos, datasets e artefatos encontrados;
9. componentes ativos, legados, arquivados e desconectados;
10. matriz inicial de claims;
11. dados existentes versus dados pressupostos;
12. inconsistências iniciais;
13. riscos capazes de invalidar resultados;
14. itens ainda não verificados;
15. prioridade da auditoria e correção;
16. critérios iniciais de aceite.

Essa entrega não encerra nem pausa a tarefa.

Após o reconhecimento inicial suficiente:

CONTINUE AUTOMATICAMENTE

pelas investigações, correções e validações autorizadas.

Não aguarde confirmação do usuário para continuar.

O mapa inicial pode e deve ser aprofundado durante a execução.

Não gaste tempo excessivo tentando tornar a primeira entrega perfeita antes de avançar para problemas materiais.

# 15. GIT E INTEGRAÇÃO

O mandato permite:

- investigação;
- aquisição de fontes públicas;
- correções;
- novos artefatos derivados;
- testes;
- commits;
- push;
- integração.

Antes de integrar:

1. confira diff;
2. confira base;
3. confira HEAD;
4. confira alterações concorrentes;
5. confira arquivos inesperados;
6. execute checks aplicáveis;
7. confira artefatos gerados;
8. confira se o código validado corresponde ao que será integrado;
9. preserve trabalho concorrente.

Preferência:

main consolidada.

Utilize branch e PR quando apropriado ao fluxo existente, preservando o checkout principal e evitando duplicação desnecessária.

Não publique automaticamente bancos, arquivos sensíveis ou grandes volumes de dados apenas porque foram utilizados na auditoria.

Respeite o papel do repositório, os contratos de dados e as condições das fontes.

Proibido:

- force-push;
- destruir histórico;
- apagar trabalho concorrente;
- editar bytes históricos para “corrigir” resultados;
- reduzir checks apenas para conseguir aprovação.

Registre os commits e validações que sustentam a entrega final.

Não atribua a um commit resultados obtidos apenas sobre outra versão.

# 16. AUTONOMIA

Trabalhe sozinho, sem agentes auxiliares.

Não peça autorização novamente para passos já abrangidos por este mandato.

Não substitua execução por ofertas de continuar.

Se informação pessoal indispensável for necessária:

- peça apenas o mínimo necessário;
- explique qual conclusão depende dela;
- continue tudo que puder ser feito independentemente.

Não repita perguntas já respondidas no contexto disponível.

XP é a preferência já informada.

Ausência de capital real, horizonte ou tolerância a perdas não impede toda auditoria técnica ou histórica. Ela limita as conclusões que dependem desses parâmetros.

Não invente respostas para remover essas limitações.

# 17. LIMITES OPERACIONAIS E FINANCEIROS

Não:

- envie ordens;
- autentique corretoras;
- movimente dinheiro;
- crie contas financeiras;
- contrate serviços;
- faça compras;
- ative automações recorrentes;
- trate candidata promissora como autorização de capital.

A proibição de automações recorrentes não se limita a automações financeiras.

XP é preferência histórica do usuário, não obrigação técnica.

Alternativas podem ser propostas se houver justificativa.

Não invente:

- capital;
- tolerância a perda;
- horizonte;
- assessor;
- canal;
- custos zero;
- eventos inexistentes;
- pagamentos confirmados;
- dados pessoais.

Custos dependentes de canal, período ou condição comercial devem ser verificados para o escopo relevante.

Uma tarifa atual não certifica uma tarifa histórica.

Não transforme impossibilidade de autenticar uma corretora em impossibilidade de auditar código, fontes públicas ou simulações.

# 18. RODADAS DE DADOS E ORÇAMENTO DE INVESTIGAÇÃO

R1 e R2 anteriores estão encerradas como rodadas históricas.

Isso não impede novas correções ou aquisições.

Antes de abrir uma nova rodada, registre:

- objetivo;
- escopo;
- orçamento prospectivo;
- fontes;
- critérios de conclusão;
- condição de parada;
- resultado ou decisão que a rodada pretende desbloquear.

Explicite o orçamento em unidades úteis, como:

- tempo;
- número de fontes;
- tentativas;
- volume;
- experimentos;
- outro limite pertinente.

Defina limites proporcionais com base no contexto disponível. Não transforme a ausência de um número previamente fornecido pelo usuário em bloqueio automático.

Não descarte ativos ou períodos difíceis apenas para melhorar resultados.

Não prolongue indefinidamente uma busca sem novas evidências ou sem relação com uma conclusão material.

O esgotamento de orçamento pode encerrar uma rodada, mas não equivale a resolver a pendência.

Registre separadamente:

- resolvido;
- refutado;
- dispensado com justificativa;
- bloqueado externamente;
- pendente internamente;
- encerrado por orçamento.

# 19. PADRÃO DE RACIOCÍNIO

Para toda descoberta material:

EVIDÊNCIA
→ INTERPRETAÇÃO
→ CONSEQUÊNCIA
→ AÇÃO
→ VALIDAÇÃO

Para componentes:

DECLARADO
→ ENCONTRADO
→ NECESSÁRIO?
→ EXECUTADO?
→ VALIDADO?
→ PROBLEMA?
→ AÇÃO

Para decisões:

DECISÃO
→ HIPÓTESE
→ EVIDÊNCIA
→ ALTERNATIVAS EXAMINADAS
→ CAMINHO MAIS JUSTIFICÁVEL
→ JUSTIFICATIVA

Para limites:

CONCLUSÃO PRETENDIDA
→ EVIDÊNCIA EXIGIDA
→ EVIDÊNCIA DISPONÍVEL
→ DIFERENÇA MATERIAL
→ EFEITO
→ CONDIÇÃO DE RESOLUÇÃO

Separe observação de interpretação.

Quando fizer uma inferência, identifique-a e explicite suas premissas.

# 20. MATRIZ DE COBERTURA DA AUDITORIA

Mantenha uma visão consolidada para impedir lacunas e trabalho desnecessário.

Para cada frente relevante:

FRENTE
| NECESSÁRIA?
| JUSTIFICATIVA
| ESTADO
| PRINCIPAL EVIDÊNCIA
| PROBLEMAS
| CORREÇÕES
| VALIDAÇÃO
| PENDÊNCIAS

O objetivo é responder:

- o que foi examinado;
- o que ainda não foi;
- o que foi corrigido;
- o que foi validado;
- o que foi dispensado como não aplicável;
- o que permanece bloqueado;
- o que ainda pode ser resolvido internamente.

Vincule essa matriz aos registros existentes.

Não replique todo o conteúdo dos claims, datasets e gaps em cada célula.

# 21. CRITÉRIO DE ENCERRAMENTO

Diferencie explicitamente:

1. conclusão da auditoria;
2. encerramento de uma rodada de trabalho;
3. prontidão do sistema;
4. sucesso ou fracasso da hipótese econômica.

Uma auditoria pode concluir que uma hipótese não se sustenta.

Uma rodada pode terminar com dependências externas documentadas.

Nenhuma dessas situações autoriza declarar o sistema pronto para um uso cujos requisitos não foram atendidos.

Para encerrar a auditoria, conecte as verificações a uma demonstração concreta do funcionamento do sistema no escopo economicamente justificado.

Quando os pré-requisitos permitirem:

1. execute o fluxo necessário com dados reais;
2. verifique a validade temporal;
3. execute a decisão e a simulação pertinentes;
4. apure posições, caixa, recebíveis e obrigações;
5. contabilize custos e tributos;
6. reproduza os resultados materiais;
7. compare com alternativas adequadas;
8. reconcilie a contabilidade por um caminho de verificação independente da implementação principal;
9. registre versões, comandos, hipóteses e limitações.

Se a evidência indicar que a abordagem não justifica continuidade, registre a conclusão e sua fundamentação.

Não construa uma abordagem substituta ilimitadamente apenas para evitar uma conclusão negativa.

Se houver impedimento material, identifique:

- etapa bloqueada;
- natureza da dependência;
- tentativas realizadas;
- conclusão afetada;
- condição objetiva de retomada.

O orçamento esgotado não autoriza declarar resolvido o que permanece pendente.

A classificação NÃO APLICÁVEL não pode substituir uma dependência difícil.

Não declare a auditoria integralmente executada se frentes materiais permanecerem sem exame ou se ainda houver trabalho interno necessário e executável não realizado.

Se um encerramento parcial for inevitável, nomeie-o como parcial e preserve uma continuidade executável.

Não use esse mecanismo como alternativa a corrigir problemas ainda solucionáveis dentro do mandato.

# 22. ENTREGA FINAL

A entrega final deve ser em português.

Organize um conjunto enxuto de artefatos canônicos em C:\STOCKS, com um ponto de entrada claro.

O resumo final deve permitir entender o resultado sem depender desta conversa.

As seções abaixo representam conteúdo obrigatório, não a exigência de criar um arquivo separado para cada uma.

## A — O QUE EXISTE E ESTÁ CORRETO

Com evidências, versão e escopo.

## B — O QUE EXISTE MAS ESTAVA ERRADO, FRÁGIL OU INCOMPLETO

Com causa, impacto e correção realizada.

## C — O QUE NÃO EXISTIA E REALMENTE PRECISAVA SER CONSTRUÍDO

Com justificativa e validação.

## D — O QUE NÃO EXISTE E NÃO É NECESSÁRIO

Classificado como:

NÃO APLICÁVEL — COM JUSTIFICATIVA.

## E — O QUE CONTINUA AUSENTE MAS É NECESSÁRIO

Com motivo, tentativas, impacto e condição de retomada.

## F — MAPA FINAL DO SISTEMA

Arquitetura, fluxo, pontos de entrada e dependências locais ou externas.

## G — MATRIZ FINAL DE CLAIMS

Com natureza, estado da evidência, temporalidade, escopo e referências.

## H — MATRIZ FINAL DE COBERTURA

Mostrando o que foi:

- examinado;
- corrigido;
- validado;
- dispensado;
- bloqueado;
- deixado pendente internamente, se houver.

## I — INVENTÁRIO FINAL DOS DADOS

Distinguindo:

- disponíveis;
- íntegros;
- utilizáveis;
- temporalmente válidos;
- suficientes para usos específicos;
- insuficientes;
- não necessários;
- ausentes.

## J — DECISÕES ARQUITETURAIS E METODOLÓGICAS

Incluindo decisões:

- mantidas;
- alteradas;
- abandonadas;
- simplificadas;
- consideradas não aplicáveis.

Com razões e alternativas examinadas.

## K — CORREÇÕES EXECUTADAS

Código, dados, testes, documentação e infraestrutura, quando pertinente.

Diferencie mudanças realizadas de propostas ainda não executadas.

## L — VALIDAÇÃO

Incluindo, conforme aplicável:

- comandos;
- ambiente;
- SHA;
- testes;
- cobertura;
- checks;
- reconciliações;
- hashes;
- resultados;
- falhas;
- verificações não executadas e seus motivos.

## M — LIMITES DOS RESULTADOS

O que é e não é possível concluir.

Diferencie resultado histórico, plausibilidade de execução, evidência prospectiva e execução efetivamente observada.

## N — PRONTIDÃO POR USO

Separando:

- desenvolvimento;
- pesquisa histórica;
- experimentação controlada;
- observação prospectiva;
- simulação;
- apoio à decisão;
- operação financeira real.

## O — PENDÊNCIAS CONCRETAS

Cada pendência deve possuir:

- necessidade;
- impacto;
- dependência;
- ação;
- condição objetiva de resolução.

Sem frases vagas como “melhorar dados”.

## P — CONTINUIDADE

Atualize os pontos de entrada e documentos de continuidade para que a próxima pessoa consiga retomar a partir dos artefatos.

Inclua:

- estado do Git;
- localização dos dados;
- comandos de reprodução;
- ambiente necessário;
- decisões vigentes;
- resultados válidos e invalidados;
- prioridades restantes;
- dependências externas;
- limites de autorização.

## Q — DEMONSTRAÇÃO DO FLUXO E CONCLUSÃO ECONÔMICA

Informe:

- qual abordagem foi efetivamente avaliada;
- por que foi escolhida;
- qual fluxo foi executado;
- quais dados reais foram utilizados;
- quais resultados materiais foram reproduzidos;
- se houve lucro absoluto;
- se houve vantagem sobre alternativas;
- qual risco foi assumido;
- quais condições de execução foram modeladas;
- se a complexidade se justifica;
- o que permanece inconclusivo.

Se a demonstração não tiver sido possível, identifique o ponto exato de interrupção e a evidência correspondente.

## R — ESTADO DE ENCERRAMENTO

Declare separadamente:

- estado da auditoria;
- estado da rodada;
- estado do projeto por uso;
- estado da hipótese econômica.

Não utilize uma única expressão “concluído” para representar esses quatro resultados.

# 23. CRITÉRIO DE SUCESSO

A tarefa deve permitir responder, com evidência e escopo explícito:

1. O que o projeto realmente faz?
2. Qual problema econômico ele realmente tenta resolver?
3. O caminho atual continua sendo justificável?
4. Entre as alternativas efetivamente examinadas, qual caminho é mais justificável nas condições avaliadas?
5. Quais partes estavam corretas?
6. Quais estavam incorretas?
7. O que foi corrigido?
8. O que foi removido, simplificado ou substituído?
9. O que inicialmente parecia faltar, mas foi considerado não aplicável?
10. Quais dados realmente existem?
11. Quais são íntegros?
12. Quais são utilizáveis?
13. Quais são temporalmente válidos?
14. Quais são suficientes para as conclusões pretendidas?
15. Quais faltam e são realmente necessários?
16. Há leakage ou problemas temporais?
17. A metodologia é válida para o escopo alegado?
18. Os resultados históricos materiais são reproduzíveis?
19. Quais claims foram confirmados, limitados ou refutados?
20. Há lucro absoluto no cenário avaliado?
21. Há vantagem sobre alternativas simples?
22. Essa vantagem, se houver, justifica a complexidade do sistema?
23. O backtest representa alguma execução plausível?
24. Quais hipóteses sustentam essa plausibilidade?
25. A contabilidade fecha sem dupla contagem?
26. Resultado patrimonial, resultado realizado e caixa disponível estão corretamente separados?
27. Outra pessoa consegue reproduzir os resultados materiais?
28. O fluxo necessário foi efetivamente executado de ponta a ponta?
29. Para quais usos o sistema está realmente pronto?
30. O que exatamente ainda impede os demais usos?
31. Quais componentes não precisam existir?
32. O projeto pode ser simplificado sem perder capacidade econômica relevante?
33. A evidência justifica continuar, reformular, estacionar ou abandonar a abordagem avaliada?
34. O que foi resolvido e o que continua dependendo de fatores externos?

Uma resposta inconclusiva pode ser correta quando fundamentada.

Ela deve identificar a evidência disponível, a lacuna material e o que permitiria resolver a questão.

Não fabrique certeza.

Não prometa rentabilidade.

Não confunda implementação com validação.

Não confunda ausência de evidência com evidência de ausência.

Não confunda resultado passado com resultado futuro.

Não confunda resultado patrimonial com caixa realizável.

Não confunda complexidade com qualidade.

Não confunda componente ausente com defeito antes de demonstrar sua necessidade.

Não confunda recuperação de arquivos com completude dos dados.

Não confunda documentação atualizada com afirmações comprovadas.

Não confunda encerramento de uma rodada com conclusão da auditoria ou prontidão do sistema.

Não encerre com apenas uma lista de recomendações.

Avance da auditoria inicial até as correções, testes, execução pertinente, validação e consolidação final dentro dos limites autorizados.
