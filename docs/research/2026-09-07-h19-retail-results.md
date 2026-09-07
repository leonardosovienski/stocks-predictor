# H19: cálculo de caixa testado; lucro líquido ainda não demonstrado

Implementei e testei a contabilidade de ações inteiras e caixa. Executei quatro
testes da primeira compra da H19, com R$5 mil e R$10 mil. **A carteira histórica
completa ainda não foi executada. Esta rodada não produziu um resultado de
lucro líquido.**

O código passou **558 testes em 154,91 segundos**, com cobertura geral de 79%
e 85% no módulo novo. Ruff, Pyright no escopo configurado do projeto, build e
importação da wheel fora do repositório passaram. O commit do runtime testado é
`5e71bc8642cc2b0759e8a1885cab446e315121fd`.

Foram verificados dimensionamento pelo fechamento anterior, execução posterior,
preços distintos de lote padrão e fracionário, custos apenas nas quantidades
negociadas, liquidações em datas diferentes, proventos recebidos depois da venda,
caixa indisponível antes do pagamento, retenção de posições sem custo fictício
e rollback de rebalanceamento se faltar uma cotação. A apuração mensal ordinária
tem testes; calendário fiscal, retenções e reorganizações ainda exigem integração.

## Teste da entrada com fontes reais

Mesmas sete ações da primeira seleção elegível, sinal em 29/06/2018, compra em
02/07/2018 e liquidação em 05/07/2018. O pacote preserva os registros brutos do
COTAHIST. A data de liquidação usa o regime anterior à mudança da B3 para D+2,
efetiva em 27/05/2019. [Fonte B3](https://www.b3.com.br/pt_br/noticias/liquidacao.htm).

| Capital | Custo hipotético por lado | Compras | Custos calculados | Caixa após liquidação |
|---|---:|---:|---:|---:|
| R$5.000 | 0,18% | R$4.985,78 | R$8,97 | R$5,25 |
| R$5.000 | 0,36% | R$4.969,29 | R$17,89 | R$12,82 |
| R$10.000 | 0,18% | R$9.966,17 | R$17,94 | R$15,89 |
| R$10.000 | 0,36% | R$9.949,68 | R$35,82 | R$14,50 |

Valores exibidos arredondados; cálculos preservam decimais. Os custos são
premissas de pesquisa. Esses quatro testes validam a compra inicial e o caixa;
não são quatro backtests. Cotações de abertura não garantem preenchimento real.

## Proventos e pendências

Na fila original de 778 registros, 144 têm pagamento individual conciliado com
fontes, dos quais 107 pertencem às posições selecionadas. Outros dois registros
da Aliansce foram substituídos por um calendário de duas parcelas, conferido no
aviso: pagamentos em maio e julho de 2023. Valores iguais não foram descartados
como duplicatas nem creditados simultaneamente.

A fila selecionada passou de 89 registros sem data candidata, após o piloto
anterior, para **16**. No conjunto das duas carteiras, restam **545 registros
sem data candidata**. Datas candidatas não significam cobertura completa ou
valor líquido aprovado. A fila também exclui os 11 eventos posteriores da JBS
localizados no piloto e os proventos ordinários dos sucessores.

A auditoria identificou 1.237 intervalos potenciais de posições das duas carteiras,
incluindo sucessores; 236 são da seleção. Não foi fornecido um cadastro completo
e verificado de proventos para esses intervalos. Há pendências de entrega,
frações e custo fiscal em 12 reorganizações e 24 eventos ordinários de ações
relevantes ao conjunto. Isso não significa que todos ocorram na carteira
selecionada.

Também foi preservado um controle contra antecipação de caixa: um dividendo da
Cogna declarado em dezembro de 2025 tem pagamento previsto para dezembro de
2028. O aviso o descreve como valor estimado. Esse valor não pode financiar
compras no período histórico em análise.

As referências fiscais do código são as páginas da Receita sobre
[isenções](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1/isencoes),
[compensações](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1/compensacoes)
e [tributação de bolsa](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1/bolsa-de-valores),
além da [LC224/2025](https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp224.htm).
Valor líquido e tratamento de cada evento continuam explícitos; o código não
escolhe automaticamente a alíquota apenas pela data em que o dinheiro é pago.
O cenário assume ausência de operações externas para pesquisa; isso não é uma
informação confirmada sobre a situação fiscal do usuário.

## Resultado reproduzível e decisão

O pacote V2 foi extraído numa pasta nova e executado sem rede duas vezes, com
saída idêntica e 1.056 arquivos verificados por SHA256. A saída esperada é
`BLOCKED_MISSING_EVIDENCE`, código 2: a auditoria rodou corretamente e impediu
um resultado econômico baseado em dados incompletos. O pacote é um auditor e
teste de entrada; preencher datas, sozinho, não o transforma num simulador
contínuo completo.

SHA256 do ZIP V2:
`8f9e8375c77c9575c12447e69a85d2888e1a827a9943c15b75cac276f5f79b7e`.
A primeira versão foi preservada; V2 incorpora o calendário das parcelas da
Aliansce no replay. Os dois bancos anteriores e a observação congelada mantêm
seus hashes. Nenhuma nova avaliação de retorno foi acrescentada: o orçamento
permanece em pelo menos 32 configurações e 37 avaliações históricas.

**Decisão: H19 continua em Discovery, inconclusiva para lucro líquido por
qualidade/completude de dados e integração de execução.** A evidência anterior
não foi promovida. Falta de dados também não demonstra que o lucro seja zero.
O capital de R$5–10 mil foi considerado; lucro anual mínimo e horas aceitáveis
continuam sem definição pelo usuário. O obstáculo econômico anterior era uma
premissa de pesquisa, não uma preferência confirmada.

As pendências concretas são: completar e certificar o inventário de caixa das
duas carteiras; integrar proventos da JBS e dos sucessores; conferir entregas,
frações e custos fiscais; implementar a execução contínua com calendário fiscal;
e só então observar os quatro casos completos, preservando seleções e orçamento
de evidência. Antes de ampliar essa reconstrução, seu custo precisa continuar
justificado pelo possível ganho econômico. Não foi aberta outra família nem
alterado o fator para tentar melhorar o resultado.
