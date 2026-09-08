A nova rodada H18/H19 foi executada em código versionado. Os 35 intervalos
antes sem medição agora têm um resultado no diagnóstico de preços mais direitos societários.
São 70 células recuperadas nas duas famílias, sem alterar nenhum retorno anteriormente medido,
nenhum fator, seleção ou data. As quatro configurações permanecem **NO_PRIORITY_UPGRADE**.

| Configuração | Períodos medidos/elegíveis | IC médio | Diferença bruta por mês | Após desconto de 72 pb por período |
|---|---:|---:|---:|---:|
| H18 mensal | 93/93 | -0.00016 | +0.5587 p.p. | -0.1613 p.p. |
| H18 trimestral | 31/31 | +0.02544 | +0.4094 p.p. | +0.1694 p.p. |
| H19 mensal | 93/93 | +0.02462 | +0.6259 p.p. | -0.0941 p.p. |
| H19 trimestral | 31/31 | +0.04870 | +0.5988 p.p. | +0.3588 p.p. |

A H19 trimestral mantém IC e diferença após custos positivos nas duas metades fixadas,
2018–2021 e 2022–2025. Seu resultado após o desconto de estresse equivale a 0,3588 p.p.
por mês, abaixo da régua de pesquisa de 0,42 p.p. A H19 mensal fica negativa nesse
estresse; a H18 tem IC negativo na primeira metade. Não houve ajuste de parâmetros.

A régua de 0,42 p.p. é uma hipótese de alocação de pesquisa, aproximadamente compatível
com R$500 anuais adicionais sobre R$10 mil. O usuário informou capital de R$5–10 mil,
mas não confirmou um lucro mínimo ou horas de manutenção. Este diagnóstico não permite
concluir REAL_EDGE_BUT_ECONOMICALLY_TOO_SMALL: o próprio edge líquido ainda não foi provado.

O resultado trimestral bruto condicionado aos antigos períodos completos era 1,0458 p.p.
por mês. Com todos os períodos medidos nesta nova definição, ficou em 0,5988 p.p.
A versão antiga superestimava a leitura favorável ao deixar períodos problemáticos de fora.
A diferença também inclui a mudança explícita de estimando para direitos societários;
não é uma comparação entre duas medições do mesmo retorno total.

As conversões usam termos finais de emissores, CVM e B3. A GNDI entrega 5,24364185943
ações HAPV e dois pagamentos, ambos com data de 29/03/2022. A LCAM entrega 0,43884446
RENT e o dividendo de fechamento. Fibria, BR Malls, Iguatemi, Aliansce, TIM, Soma,
Motiva, JBS e Natura preservam as respectivas quantidades e/ou caixa. A cisão da
Vamos mantém VAMO3 e adiciona 1,15136366 AMOB3; 28,290555% era migração do histórico
de negociação, não a proporção de entrega de ações. No Carrefour foi usada a opção
padrão de R$8,50 em dinheiro, sem escolher uma alternativa pelo resultado posterior.

Na saída de SOMA3 em 01/08/2024, AZZA3 é um direito marcado a mercado, com crédito
previsto em 05/08. Na tentativa de entrada em SOMA3 em 01/08, não há compra nem
conversão retroativa: a alocação fica em caixa. Os documentos originais e seus hashes
estão no pacote, junto às cotações B3 e aos registros de cada conversão.

Limites: quantidades fracionárias teóricas; valores brutos; direitos de subscrição
marcados a zero, sem exercício ou venda; dividendos e JCP ordinários omitidos.
Datas de pagamento refletem comunicados, não extratos de conta; algumas datas de
crédito físico continuam desconhecidas. Recebíveis não são reinvestidos. O desconto
de 36/72 pb é um cenário fixo por período, não uma apuração de giro, impostos ou custos
efetivos. As médias trimestrais foram divididas por três para comparação, não compostas.
Não é retorno total, backtest executável, estimativa de lucro líquido ou autorização de capital.

O próximo teste barato se concentra na execução da carteira trimestral congelada da H19.
A análise das seleções encontrou 40,16% de peso-alvo médio em nomes novos por rebalanceamento.
Isso não mede o giro financeiro efetivo: faltam a deriva de preços, quantidades inteiras,
eventos e liquidação. Para alcançar a mesma régua com o resultado bruto observado, o
orçamento de custos seria 0,5365% por trimestre; não se alterou a régua nem se declarou
que esse custo é alcançável. A fonte atual possui 9.812 registros de caixa não validados,
mas nenhuma das 233 posições trimestrais selecionadas tem seu intervalo integralmente
coberto pelo cadastro de proventos verificados. A prioridade é verificar se essa lacuna
pode ser resolvida a baixo custo antes de financiar nova simulação de lucro.

H18 perde prioridade; H19 permanece exploratória e sem promoção. H11 não foi reaberta:
reconstruir momentum de retorno total exige histórico limpo também na janela do sinal.
Modelos novos não resolvem essa lacuna. Regra de parada: uma comparação fixa de execução,
sem otimizar frequência, filtros, thresholds ou períodos; abandonar o aprofundamento se
a cobertura de caixa não puder ser obtida a baixo custo ou se o estresse de execução
eliminar a margem econômica. Nenhuma Proof ou amostra histórica intacta foi criada.

Próximas ações registradas: auditar cobertura primária de caixa dos membros originais;
reconciliar datas e quantidades por ISIN; resolver crédito físico e frações; medir giro
e caixa efetivos para R$5 mil e R$10 mil; aplicar a mesma régua com execução na abertura,
fechamento e pior preço. São tarefas futuras, ainda não executadas neste resultado.

Validação técnica: 533 testes passaram em 153,45 s, cobertura de 80%; Ruff no escopo do
CI, Pyright configurado, build e importação do wheel fora do checkout passaram.
Código testado: 54fd8643ef43c3b8182deb0d82a8e186498f1f91. Nenhuma dependência nova de runtime.
Banco operacional e base anterior preservados por SHA-256. Orçamento conservador:
ao menos 24 configurações e 29 avaliações históricas, com busca adaptativa antiga
desconhecida. A reprodução idêntica é verificação técnica, não evidência independente.

Reprodução offline concluída: PASS. O comando entregue extraiu o ZIP, verificou 162 arquivos e reproduziu exatamente todos os membros e resumos das quatro configurações. O usuário não precisa instalar dependências para repetir essa verificação.
