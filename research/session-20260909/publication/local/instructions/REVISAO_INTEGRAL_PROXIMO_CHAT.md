# Stocks — revisão integral, correção e prontidão

## Pedido atual do usuário

Faça uma revisão completa do projeto Stocks: lógica, arquitetura, implementação,
dados, fontes, metodologia, resultados, documentação e tudo que ele pressupõe ou
afirma ser verdadeiro. Comece pelo que já existe para conferir se está correto e
se o caminho adotado continua fazendo sentido. Identifique o que existe, o que
falta e, principalmente, execute as correções e complete o que for necessário.
O objetivo é chegar a um projeto utilizável, com limites de uso demonstrados.

Este é o escopo autorizado para a próxima tarefa. Não se limite à antiga fila de
completar eventos/custos H21. A prioridade agora é a revisão integral solicitada;
regras antigas de ordem de trabalho não restringem esse escopo. Preserve o
significado de protocolos congelados e todas as evidências históricas.

Não trate uma afirmação como validada só porque está num Markdown, catálogo,
comentário de código, relatório anterior, nome de arquivo ou resposta do assistente.
Confira a evidência, o código efetivamente executado e o alcance real da conclusão.
Também não presuma que toda afirmação esteja errada: separe fatos confirmados,
inferências, hipóteses, conflitos, desconhecidos e conclusões refutadas.

## Localização, continuidade e ponto de partida

Todo o conteúdo local autoral e os dados do projeto ficam em `C:\STOCKS`.
Checkout único: `C:\STOCKS\stocks-predictor`. Trabalhos, fontes novas, logs e
temporários em `C:\STOCKS\work`; entregas em `C:\STOCKS\outputs`.
Não gravar conteúdo do projeto na pasta gerada da tarefa em Documents/Codex.

Primeiro confira Git, HEAD, remoto, worktrees e alterações. A última integração
verificada ao preparar esta passagem foi `7de0ea9ad5e9c34e695c49a2c720561cad283685`,
PR72, main local/remota limpa. Essa referência não autoriza reset nem substitui
a conferência do estado atual. Não criar outro checkout sem necessidade.

Leia, nesta ordem, ampliando a leitura conforme as dependências reais:

1. Este pedido e `C:\STOCKS\AGENTS.md`.
2. No checkout: `AGENTS.md`, `README.md`, início de `HANDOFF.md`,
   `STOCKS_CURRENT_STATE.md` e `docs/DOCUMENTATION_INDEX.md`.
3. `docs/continuation/MANDATO_20260909.md` integralmente. A nova prioridade de
   revisão ampla prevalece sobre a antiga orientação de começar por um experimento
   econômico mínimo; autonomia, integridade e limites do mandato permanecem.
4. `C:\STOCKS\LOCALIZACAO_PROJETO.json`,
   `docs/continuation/LOCAL_PATHS_20260909.json`, `C:\STOCKS\data\README.md`
   e `C:\STOCKS\data\CATALOG.json`.
5. `docs/research/2026-09-09-data-completion-r2.md` e seus JSON de prontidão,
   eventos, entradas operacionais e inventário de fontes; recibo
   `C:\STOCKS\outputs\ENTREGA_DADOS_FONTES_R2_20260909.json`.
6. Antes de alterar o domínio, leia `docs/DESIGN.md` integralmente e os designs,
   protocolos, decisões e congelamentos pertinentes. Confira sua vigência contra
   o código. `docs/continuation/PROMPT_NOVO_CHAT.md` registra a continuidade
   anterior; sua fila H21 é contexto, não limite para este novo pedido.

Os números seguintes são referências para reconferir, não certificados globais:

- 37 caminhos arquivados correspondem a 12 bancos únicos recuperados em
  `C:\STOCKS\data\recovery-r2`, com catálogo de aliases, hashes e integridade.
  Banco original, versões reparadas, versões de pesquisa e fixtures estão separados.
  Nenhum foi ativado automaticamente como banco operacional.
- Fontes 13 e 14 estão disponíveis separadamente. A auditoria 13 foi reproduzida
  exatamente; a 14 registra 52 líquidos, 24 datas e 28 entradas societárias
  pendentes, com 0/1.248 intervalos integralmente certificados. As contagens se
  sobrepõem. Confira os manifestos utilizados e o significado de cada bloqueio.
- BOVA11 tem 2.159 cotações até 08/09/2026, separadas dos dados do experimento
  original H21, que termina em 01/04/2026. A base ampla tem cotações até 27/08.
  Tabelas `fundamentals_pit` existentes nos bancos recuperados estão vazias.
- Demonstrações e comparativos BOVA11 cobrem exercícios de 2018 a março de 2026;
  isso não certifica todo evento/direito nem ausência contínua de pagamentos.
  Persistem lacunas documentais, de tarifas históricas e de despesas efetivas.
- CI191 no commit citado: 791 testes regulares, cobertura 78%, Python 3.13.15,
  Core 3.2.0, Ruff, Pyright, build, gitleaks e wheel fora do checkout.
  Nove testes auxiliares também passaram localmente. Dezessete testes arquivados
  ficaram fora da suíte. Testes aprovados não comprovam lucro ou dados completos.
- H21 é exploratória e inconclusiva para lucro líquido executável; H20 estava
  estacionada para reconstrução ampla. Reveja as razões dessas escolhas, sem
  alterar retroativamente resultados ou pressupor que alguma delas deva vencer.
- XP é a preferência do usuário, com abertura a alternativa justificada.
  Canal/assessor, capital, horizonte e perda aceitável não foram informados.
  R$5 mil e R$10 mil são cenários. Não existe monitor ou operação real ativo.

## Como executar a revisão

Faça primeiro um mapa do sistema real: objetivo econômico, fluxo de dados,
componentes, pontos de entrada, dependências, comandos, estados persistidos e
saídas. Confronte o sistema descrito com o implementado e o efetivamente exercitado.
Inclua componentes legados, arquivados, incompletos ou desconectados do fluxo ativo.
Esse mapa deve orientar correções; não transformar a tarefa em inventário interminável.

Mantenha uma matriz rastreável das afirmações materiais. Para cada uma, registre
o que se afirma, onde, em qual versão/escopo, a evidência ou teste que a sustenta,
o resultado da conferência, o impacto e a ação tomada. Dê atenção especial às
afirmações de prontidão, cobertura, causalidade, execução, retorno e validade futura.
Inclua incompatibilidades entre documentos, implementação e dados.

Cubra pelo menos estas frentes, sem presumir que a lista contém todos os problemas:

1. **Objetivo e caminho escolhido.** Confira a pergunta econômica atendida,
   o benefício do sistema frente a uma alternativa simples, sua necessidade e
   custo de manutenção. Reavalie H21, H20, fatores e demais escolhas relevantes.
   Compare alternativas com critérios explícitos. Simplifique, substitua ou retire
   do fluxo ativo componentes quando houver justificativa, preservando a história.
   Não reescreva por estética nem preserve uma decisão apenas por investimento passado.
2. **Lógica e metodologia.** Confira fórmulas, unidades, datas, informação
   disponível na decisão, revisões contábeis, preços brutos/ajustados, causalidade,
   seleção do universo, sobrevivência, vazamento de informação, múltiplas tentativas,
   hipóteses estatísticas, critérios de seleção e interpretação dos resultados.
   Separe exploração, validação fora da amostra, projeção e observação prospectiva.
3. **Arquitetura e implementação.** Confira contratos, acoplamentos, estados,
   caminhos efetivamente usados, banco padrão, transações, migrações, idempotência,
   falhas, logs, segurança, configurações, CLI, pacote, dependências/Core, imports
   reais e isolamento de testes. Localize caminhos que criam dados vazios, ignoram
   falhas ou prometem executar algo que não executam.
4. **Dados e fontes.** Confira disponibilidade física, integridade, identidade,
   proveniência, licença/condições aplicáveis, atualidade, cobertura por instrumento
   e período, conhecimento temporal, duplicações, conflitos, versões, quarentenas,
   ausências e procedimentos de atualização. Audite preços, fundamentos, eventos,
   direitos, pagamentos, sucessores, calendário e custos quando necessários ao uso.
   Distinga dado existente, utilizável, suficiente e certificado para uma conclusão.
5. **Contabilidade e execução.** Reconcilie posições, caixa, recebíveis, obrigações,
   aportes, base fiscal, capital comprometido, liquidação, lotes, custos, impostos,
   spread, deslizamento e eventos após vendas. Confira dupla contagem de proventos,
   custos embutidos no fundo e diferenças entre anúncio, direito e pagamento.
   Preço diário e ordem simulada não demonstram preenchimento real.
6. **Testes, resultados e documentação.** Confira o que a suíte realmente detecta,
   seus pontos cegos, fixtures e exclusões. Para erros materiais, crie regressões
   que detectem o problema; use dados reais e conferência contábil por outro caminho
   quando pertinentes. Corrija afirmações, instruções e exemplos incompatíveis com
   o estado demonstrado. Não use teste que apenas repete a implementação como prova.

Priorize dependências que podem invalidar uma conclusão ou impedir o uso pretendido.
Corrija problemas conforme forem suficientemente compreendidos, sem aguardar o fim
de toda a leitura para começar a agir. Valide a correção e seus efeitos relacionados.
Não encerre entregando somente uma lista de problemas, sugestões ou interfaces vazias.

Para dados ausentes, examine primeiro os pacotes, versões e fontes já recuperados;
depois tente fontes públicas pertinentes e rotas oficiais alternativas. Falha de
acesso não comprova ausência. Registre tentativas e obtenha evidência adequada ao
período e ao instrumento. Não repetir downloads sem motivo nem reconstruir todo o
arquivo de 60.023 caminhos por padrão.

As rodadas R1/R2 anteriores estão encerradas. Isso não proíbe novas correções ou
aquisições nesta tarefa: registre orçamento prospectivo próprio e condições de
conclusão antes de novas rodadas. Não invente custos zero, eventos inexistentes,
pagamentos confirmados ou dados pessoais para remover bloqueios. Não descarte
ativos/períodos problemáticos para melhorar o resultado ou aparentar completude.

Rever decisões não autoriza consultar desempenho e depois escolher silenciosamente
parâmetros. Antes de nova hipótese, reabertura ou variante econômica, registre
mecanismo, protocolo, dados já observados, orçamento, critérios e comparação.
Resultados corrigidos recebem versões próprias; originais e tentativas negativas
permanecem preservados. Não é possível recriar um holdout intacto com dados já vistos.

## Autonomia e limites

Trabalhe sozinho, sem agentes auxiliares, conforme preferência vigente do usuário.
O mandato autoriza investigação, fontes públicas, correções, artefatos derivados,
testes, commits, push e integração após revisão do diff, base exata e checks.
Não peça novamente autorização para etapas já cobertas. Se precisar de informação
pessoal indispensável, peça somente o necessário e continue o trabalho independente.

Não envie ordens, autentique corretoras, movimente dinheiro, crie contas financeiras,
contrate serviços ou ative automações recorrentes. Candidata promissora não autoriza
capital. Preservar fontes, bancos originais, ledgers, quarentenas e trabalho do usuário.
Não editar bytes históricos para corrigir caminhos, executar scripts legados sem
examinar os efeitos, contornar controles ou reduzir checks para obter aprovação.

No Windows atual, não criar venv, instalar Core/dependências nem alterar Python
global/EDR. O Python 3.12.14 fornecido pelo Codex atende auxiliares compatíveis.
Validação de produção usa a CI Linux permitida, com runtime/imports conferidos;
verifique se o ambiente mudou antes de afirmar disponibilidade. Ferramentas e
caches internos do ambiente não precisam ser movidos para `C:\STOCKS`.

## Critério de conclusão e entrega

Defina e justifique os usos para os quais o projeto deve ficar pronto. Separe
prontidão para desenvolvimento, pesquisa histórica, observação futura e operação
real. Não confundir código íntegro, CI verde e resultado passado com lucro futuro.
Mudar o escopo exige justificativa visível; não estreitá-lo apenas para declarar êxito.

Conclua as correções e aquisições acessíveis e pertinentes ao escopo revisado.
Se algo material não puder ser resolvido, demonstre as tentativas, a dependência
externa ou a observação futura necessária, a conclusão impedida e a condição exata
de retomada. Não declarar o projeto inteiro pronto enquanto houver bloqueios
materiais para o uso declarado. Também não exigir dados irrelevantes apenas para
alcançar uma completude abstrata de todo o mercado.

Entregue em português: mapa do sistema real; matriz de afirmações conferidas;
problemas e premissas corrigidos; decisões arquiteturais/metodológicas com razões;
inventário verificável dos dados disponíveis e ausentes; correções executadas;
testes e reconciliações com ambiente/SHA; limites dos resultados; prontidão por uso
e pendências concretas. Atualize os pontos de entrada e a continuidade para que a
próxima pessoa não tenha de reconstruir o estado pela conversa.

Mantenha parâmetros, fontes, hashes, comandos e recibos suficientes para reproduzir.
Preserve a preferência por main consolidada, sem force-push ou remoção de trabalho
concorrente. Verifique o conteúdo e os checks do commit integrado. Avance da
conferência inicial até as correções e a validação do projeto, dentro dos limites
autorizados, sem fabricar certeza ou prometer rentabilidade.
