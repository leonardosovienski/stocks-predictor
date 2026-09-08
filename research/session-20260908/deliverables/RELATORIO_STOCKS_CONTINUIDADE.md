# Continuidade Stocks — resultado da execução

**A pesquisa ganhou contabilidade mais correta e uma medida concreta de viabilidade.
O lucro líquido da H19 continua desconhecido. A decisão operacional permanece não operar.**
Recomendo pausar a reconstrução manual extensa da H19 e só retomá-la com uma rota
barata de fechamento das fontes e manutenção compatível com R$5–10 mil.
Isso é uma decisão de alocação de esforço, não prova de que a H19 perde dinheiro.

## Trabalho executado

- Reproduzi o bloqueio original e conferi a preservação das entradas e dos bancos.
- Implementei ganho de leilão calculado com o custo fiscal da fração de cada posição,
  integrado à apuração mensal, compensação de perdas, retenção e datas de caixa.
- Corrigi três falhas reproduzidas na versão anterior: valores já líquidos e impostos
  fixos aceitos em outra carteira, e imposto futuro antecipado antes de ser conhecido.
- Executei compras inteiras nas 31 datas congeladas, em ambas as carteiras, com
  R$5 mil/R$10 mil e custos de 0,18%/0,36% por lado: **248 casos concluídos**.
- Calculei os 432 cenários registrados de manutenção, custos fixos, reconstrução
  futura e lucro desejado; arquivei as duas versões do diagnóstico e sua reprodução.

A primeira versão concluiu 244 compras e bloqueou quatro na entrada da Cyrela.
A fonte existente de 31/12/2025 confirmou uma bonificação em outra classe, sem
mudar o número de ON. A revisão de unidades, registrada separadamente, permitiu
concluir essas quatro compras sem dar direitos de bonificação ao livro vazio.
Um ajuste de compatibilidade também vinculou o ISIN ao plano congelado, pois o
cadastro de requisitos societários ordinários não repete esse campo.
Isso não aprova pagamentos, frações ou fiscalidade da Cyrela no replay contínuo.

## Compras iniciais: resultado medido

Medianas nas mesmas 31 datas, custo de **0,18% por lado**. Cada data começa com
caixa integral e nenhuma posição; não é uma simulação de riqueza acumulada.

| Capital | Carteira | Ações distintas compradas | Custo modelado da compra | Caixa após liquidação |
|---|---|---:|---:|---:|
| R$5.000 | H19 | 8 | R$8,92 | R$33,22 |
| R$5.000 | Comparação congelada | 40 | R$8,12 | R$481,29 |
| R$10.000 | H19 | 8 | R$17,92 | R$25,88 |
| R$10.000 | Comparação congelada | 40 | R$17,15 | R$452,58 |

As ordens usam quantidades inteiras definidas pelos fechamentos do sinal e preços
de abertura distintos para lote padrão e fracionário. O calendário fornecido
liquida 216 casos em dois pregões e 32 em três pregões; as obrigações foram
liquidadas sem empréstimo ou caixa negativo. O cenário de custo dobrado também
foi executado e está no JSON completo, sem selecionar uma variante vencedora.

Com R$5 mil, a comparação deixa cerca de 9,63% do capital em caixa na mediana,
contra 0,66% da H19. Logo, uma comparação futura precisa considerar a diferença
de exposição. A H19 concentra seis a nove nomes; a comparação tem de 33 a 46.
Nenhum desses números demonstra equivalência de risco ou vantagem de seleção.

As aberturas observadas não comprovam preenchimento, spread, prioridade da ordem
ou arredondamento por nota. **Giro efetivo contínuo, dividendos totais, imposto
histórico total, lucro líquido e retorno excedente ajustado ao risco seguem
desconhecidos.** Não extrapole estes custos iniciais para um retorno anual.

## Quanto esforço esse capital pode sustentar

Os valores abaixo são hipóteses de custo, não preferências suas nem previsões
de alpha. O retorno adicional necessário é depois de negociação e impostos,
antes dos custos desta tabela, em relação a uma alternativa comparável.
Adota-se custo administrativo zero para a alternativa; se não for zero,
é a diferença entre os custos das duas alternativas que deve ser usada.

| Cenário, sem reconstrução futura | Custo anual | Retorno adicional necessário sobre R$5 mil | Sobre R$10 mil |
|---|---:|---:|---:|
| 1 h/mês a R$25/h | R$300 | 6% | 3% |
| 2 h/mês a R$25/h | R$600 | 12% | 6% |
| 2 h/mês a R$25/h + R$120 fixos/ano | R$720 | 14,4% | 7,2% |

Por exemplo, uma vantagem hipotética de 5% ao ano produziria R$250/R$500 antes
da manutenção. Com duas horas mensais a R$25/h, sobrariam **−R$350/−R$100**.
São cenários de custo de oportunidade, não perdas da estratégia observadas.
Sem custos fixos, essa vantagem hipotética pagaria no máximo 50 minutos/mês
de trabalho a R$25/h sobre R$5 mil, ou 100 minutos sobre R$10 mil.

Se houver ainda 20 horas futuras de reconstrução a R$25/h, amortizadas em três
anos, acrescente R$166,67 por ano. Para desejar R$500 anuais adicionais, com
duas horas mensais e R$120 fixos, seria necessário retorno excedente líquido
de aproximadamente 27,73% sobre R$5 mil ou 13,87% sobre R$10 mil.
O esforço já gasto foi excluído: é custo passado, não justificativa para continuar.
Piso de lucro e horas aceitáveis continuam desconhecidos; cenários de custo zero
também estão registrados, sem supor que seu tempo seja gratuito.

## O que a revisão fiscal resolveu e o que ainda falta

A implementação distingue bruto de leilão, despesas, retenção e custo da posição.
Nos controles sintéticos, o mesmo recebimento gera imposto com um custo de
aquisição menor e perda fiscal com um custo maior. Não são retornos da H19.
O tratamento ordinário segue as regras gerais de ganho, deduções e compensações
da [Receita Federal](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1/bolsa-de-valores),
com a [isenção mensal de ações](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1/isencoes)
aplicada ao total elegível de vendas, não inferida do capital inicial.
Cada evento ainda exige enquadramento legal e fonte próprios.

Revi os três documentos VIVT preservados. O comunicado de 19/05/2025 informa
resultado descontadas despesas, não certifica o imposto pessoal nem o crédito
exato de cada investidor. Por isso, o exemplo de 39 ON, convertido em 78 unidades
de leilão, tem recebimento antes do imposto pessoal de R$2.078,07311434242,
mas imposto desconhecido. A quantidade e os custos usados no exemplo são
hipotéticos, não uma posição histórica calculada da H19.
[Comunicado da Telefônica/CVM](https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx?Tela=ext&descTipo=IPE&CodigoInstituicao=1&numProtocolo=1380678&numSequencia=905390&numVersao=1).

O cadastro real permanece com **356 datas de pagamento ausentes, 389 líquidos
não revisados, zero certificados para 1.237 intervalos e zero dos 36 registros
societários integrados/aprovados**. O problema adicional de cronologia é o
pagamento estimado da Cogna em 2028, ainda sem disponibilidade validada.
O motor não inventa essa data. Em planejamento, os 1.237 intervalos podem ser
agrupados em 312 períodos para 123 identidades ticker/ISIN; isso reduz repetição
na busca de documentos, mas não certifica nenhum intervalo.

Dependem de fonte: inventários completos de proventos e sucessores, datas e
valores líquidos revisados, bruto/despesas/retenções de leilões e termos de
entrega. Dependem também de código/integração: outras modalidades de reorganização,
revisões de razão de entrega, alterações de custo por restituição, fiscalidade
fora da bolsa/estrangeira e conciliação de centavos. Fills precisam de evidência
de execução futura. Nenhuma lacuna foi preenchida como zero.

## Decisão de pesquisa

| Caminho | Decisão e motivo |
|---|---|
| Completar todo o histórico H19 manualmente | Pausar a reconstrução extensa: há custo alto de fonte e integração para chegar apenas a um resultado exploratório. |
| Simplificar a medição e a manutenção | Caminho executado nesta etapa: compras quantificadas, código fiscal corrigido e custo de esforço explícito. Uma retomada depende de uma rota concreta de fontes com baixo custo recorrente. |
| Nova hipótese em ações | Backlog: reação a resultados pode ter mecanismo informacional, mas ainda não há vantagem PIT demonstrada; trocar de hipótese não elimina as obrigações de execução e não justifica nova varredura. |

H19 permanece Discovery/inconclusiva; não foi descartada como sem edge.
As famílias antigas não foram reabertas para procurar um backtest positivo.
Há pelo menos **32 configurações e 37 avaliações históricas expostas**, sem
holdout intacto demonstrado. Esta etapa acrescentou **zero avaliações de retorno**.
As duas versões do diagnóstico de compras e o complemento de fonte foram preservados.
Nenhuma coorte prospectiva ou automação foi iniciada. Se surgir mérito econômico
e a cadeia de dados for fechada, será necessário registrar validação futura
independente antes de qualquer operação real.

## Validação e reprodução

Suíte completa: **613 testes passaram** no snapshot `0ac04cb`. O ajuste final
de compatibilidade `bebe1f7` foi validado pelos três testes do diagnóstico e
pelos **69 testes do pacote fora do checkout**; a suíte inteira não foi repetida
para essa alteração localizada. Os módulos contábeis não mudaram depois da suíte.
Ruff e Pyright no escopo configurado passaram; cobertura geral de 79%.

As três regressões falharam na versão anterior de forma reproduzível e agora
rejeitam as entradas sem alterar a carteira. O replay real conferiu 31 arquivos
e 365.198 cotações e permaneceu **exit 2 / BLOCKED_MISSING_EVIDENCE**, idêntico
byte a byte ao anterior. O diagnóstico final e a auditoria das fontes também
foram reproduzidos byte a byte. Os bancos conservaram seus hashes.

O ZIP contém código, testes, protocolo, fontes específicas, resultados e
`reproduce.py`. Reutiliza as cotações da pasta independente já preservada;
não duplica o conjunto extenso de dados. Execute com Python 3.13 global,
sem venv ou instalação de dependências. O relatório de validação registra
commits, hashes, escopos e comandos. Nenhuma ordem, compra de serviço ou push
ao GitHub foi realizado.
