# Prompt de continuidade — Stocks Predictor

> Atualização vigente de 08/09/2026: continuar na **main**, integrada localmente
> e enviada ao GitHub após esclarecimento do operador; as outras branches foram
> excluídas nos dois lugares. Ler antes MIGRACAO_MAIN.md e
> MIGRACAO_VERIFICADA.json. Código e histórico estão em CODIGO_MAIN.bundle;
> dados em DADOS_STOCKS.zip, restaurados pelo tools/data_transfer.py do Git.
> Os caminhos da branch fix nas seções abaixo descrevem a preservação anterior.
> Usar o código do clone main atual e o mapeamento dos dados do guia de migração.
> Validação: 777 testes; auditoria 14 reproduzida, com lucro ainda desconhecido.

Você vai continuar o stocks-predictor para aumentar a probabilidade de gerar lucro
real, líquido, futuro e reproduzível no mercado acionário. Quero revisão crítica,
implementação e execução, com autonomia para mudar o caminho quando houver
justificativa econômica. Não preserve hipóteses ou arquitetura por apego, nem
otimize o histórico até aparecer um resultado positivo.

## Comece pela cópia independente do chat anterior

Raiz preservada de pesquisa:
`C:\Users\Superleo13\stocks-predictor-work\.local-research\stocks-session-20260907`

Código atualizado, em checkout próprio:
`C:\Users\Superleo13\stocks-predictor-work\.local-research\stocks-session-20260907\work\stocks-predictor`

Branch: `fix/stocks-cvm-execution-20260907`.
O checkout principal `C:\Users\Superleo13\stocks-predictor-work` permanece em
outra branch; não confunda seu código antigo com esta pesquisa nem sobrescreva
arquivos locais do usuário. A branch de pesquisa também está preservada no Git
desse repositório principal. Não dependa do histórico da conversa anterior.

Leia primeiro, dentro do código atualizado:
- `docs/continuation/SESSION_CONTEXT.md` e `docs/continuation/PATHS.json`;
- `docs/continuation/INITIAL_REQUEST.md` (pedido original, preservado);
- `AGENTS.md`, início de `HANDOFF.md`, `STOCKS_CURRENT_STATE.md` e as instruções
  aplicáveis de `docs/DESIGN.md`;
- `docs/research/2026-09-07-final-review.md`;
- `research/session-20260907/deliverables/ESTADO_FINAL_STOCKS.md` e os JSONs
  `STOCKS_REVISAO_FINAL_DECISAO`, `VALIDACAO`, `FONTES`, `EXECUCAO` e `REPRODUCAO`.

Os dados extensos e as dependências locais ficam em `work/` da raiz preservada;
os pacotes anteriores e relatórios ficam em `outputs/`. Os artefatos históricos
mantêm hashes e caminhos originais; use o mapeamento em PATHS.json, sem reescrever
as fontes apenas para mudar caminhos. Verifique o recibo de preservação disponível
nessa raiz e no diretório `docs/continuation/`.

## Capital, autonomia e limites

- Capital informado: R$5.000 a R$10.000, para avaliação econômica.
- Lucro anual mínimo e horas aceitáveis de manutenção não foram informados.
  Use cenários identificados como hipóteses, sem inventar preferências do usuário.
- Pesquisa em ações, alterações locais reversíveis e simulações estão autorizadas.
  Core/Ops só entram como infraestrutura realmente necessária a Stocks.
- Não investir dinheiro real, enviar ordens, comprar dados ou contratar serviços.
- Não coordenar outros agentes nem desenvolver outros mercados para fugir da linha.
- Não pedir confirmação para decisões rotineiras cobertas por esta autonomia.
- Preservar bancos existentes, dados brutos, ledgers e quarentenas. Não executar
  automaticamente scripts históricos de ingestão/reconstrução: alguns escrevem
  bancos. Consultas usam somente leitura; testes usam bases temporárias próprias.
- Windows, Python 3.13 global; não criar venv nem instalar Core via pip.
  Preferir stdlib e dependências já disponíveis. Mudança de runtime exige
  justificativa e respeito às autorizações existentes.

## Estado real da pesquisa

- Código de runtime validado: `741d237388405970127492a4eff81ab1e5c755a1`.
  Revisão documental correspondente: `858ba52315be3508bfe3d442388f1f9ed793f371`.
  Commits posteriores de preservação não constituem novos experimentos.
- 592 testes passaram, cobertura geral 79%; Ruff, Pyright no escopo RJ+H19,
  wheel/importação externa e 48 testes do recorte passaram.
- Foram conferidos 365.198 registros de cotação contra extratos brutos e 367
  cópias de fontes. Isso não certifica cobertura integral ou fills.
- As quatro coortes, 9.732 células e 12 cenários antigos foram reproduzidos.
  Seus resultados continuam sendo diagnósticos de preços, não lucro líquido.
- A execução econômica completa ainda não foi concluída. O replay atual termina
  em `BLOCKED_MISSING_EVIDENCE`, código 2, com lucro nulo no sentido de campo
  desconhecido (`null`), não lucro igual a zero.
- Faltam 356 datas no cadastro de pagamentos; nenhum dos 1.237 intervalos tem
  inventário integral de caixa certificado; 36 registros societários exigidos
  ainda não foram integrados/aprovados no arquivo de execução.
- Há lacunas de código e integração, especialmente tributação societária que
  depende da posição e do custo fiscal de cada carteira, além das lacunas de fonte.
- H1–H16 têm limitações históricas de dados/método; H3 não foi executada. H17 ficou
  inconclusiva. H18 é controle enfraquecido; H19 trimestral é candidata exploratória.
- Pelo menos 32 configurações e 37 avaliações históricas já foram expostas.
  Não existe holdout intacto demonstrado. Nenhum edge líquido foi confirmado.
- Decisão atual: `INCONCLUSIVE_NET_PROFIT / OPERATIONAL_NO_GO`.

## Trabalho solicitado

1. Revise criticamente o diagnóstico atual. Confirme defeitos e pendências com
   evidência; não aceite conclusões anteriores apenas porque estão documentadas.
2. Escolha o próximo trabalho pelo valor econômico e informacional. Compare
   continuar H19, simplificar a implementação ou investigar outra hipótese em
   ações. Considere custo de reconstrução, manutenção, capital e tempo até uma
   resposta confiável. Não persista na H19 por apego, nem a abandone apenas para
   encontrar um backtest positivo em outro lugar.
3. Execute o caminho escolhido: corrija, implemente, reutilize fontes já adquiridas
   e rode testes/experimentos pertinentes. Não encerre somente com plano ou lista
   de tarefas. Se houver bloqueio concreto, esgote caminhos viáveis e continue o
   trabalho independente; não preencha lacunas com suposições ocultas.
4. Meça economia executável: quantidades inteiras, fracionário, giro efetivo,
   caixa disponível, liquidação, proventos, eventos societários, impostos,
   custos de negociação, custos fixos e manutenção. Compare alternativas coerentes
   quanto a período, risco, tributação e capital. Separe valorização, lucro líquido,
   retorno excedente e evidência de vantagem futura.
5. Antes de observar uma nova configuração, registre mecanismo, hipótese,
   parâmetros, custos, avaliação e regra de parada. Contabilize a busca adaptativa,
   preserve observações anteriores e não ajuste janela, direção, universo ou
   limiares depois de ver resultados para resgatar uma hipótese. Nova direção de
   pesquisa exige registro próprio, não reescrita dos protocolos congelados.
6. Não trate dados ausentes como zero nem exclua casos difíceis pelo desempenho
   futuro. Só acrescente ML, fatores ou infraestrutura quando resolverem uma
   necessidade demonstrada. Quantidade de código e testes não é a função objetivo.
7. Valide proporcionalmente às mudanças e reproduza resultados importantes.
   Dê atualizações curtas e mantenha HANDOFF, protocolos, resultados e Git atualizados.

## Critério de sucesso

Melhorar concretamente a capacidade de decidir se existe lucro executável, ou
demonstrar com evidência que uma linha deve ser descartada por inviabilidade.
Se surgir algo promissor, prepare validação independente/prospectiva antes de
qualquer operação real. Discovery não é Proof.

Se permanecer inconclusivo, explique exatamente o impedimento, o que foi tentado,
o que depende de código e de fonte externa, e se o esforço adicional ainda faz
sentido para R$5–10 mil. Não prometa lucro nem force um resultado positivo.
