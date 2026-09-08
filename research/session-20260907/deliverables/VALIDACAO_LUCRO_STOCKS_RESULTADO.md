**Stocks: validação técnica e econômica — 7 de setembro de 2026**

**Ainda não há lucro líquido validado para operar.** Há valorização histórica nas simulações, mas a incerteza sobre vantagem futura, os proventos incompletos e a execução impedem chamar isso de estratégia lucrativa comprovada. H19 trimestral continua apenas como hipótese em Discovery.

Os 539 testes passaram em 153,65 segundos. Cobertura: 79%; Ruff no escopo CI, Pyright configurado, construção do wheel e importação fora do repositório passaram. O segundo cálculo confirmou 9.732 células, com diferença máxima de 2,22×10⁻¹⁶ por arredondamento numérico. Fatores, papéis selecionados e períodos ficaram fixos.

A tabela mostra **vantagem média sobre o universo comparável**, em pontos percentuais por mês, após um desconto fixo de 72 pontos-base por período de manutenção. Esse desconto é cenário de custo, não giro efetivamente medido. O cenário adverso compra pelo maior e marca a saída pelo menor entre abertura e fechamento; aplica a mesma regra ao benchmark. Ele não é um limite inferior matemático do excesso de retorno.

| Hipótese | Abertura | Fechamento | Preço adverso | Intervalo descritivo de 95%, abertura |
|---|---:|---:|---:|---:|
| H18 mensal | -0.161 | -0.210 | -0.076 | -0.789 a +0.486 |
| H18 trimestral | +0.169 | +0.202 | +0.204 | -0.542 a +0.901 |
| H19 mensal | -0.094 | -0.026 | -0.114 | -0.825 a +0.590 |
| H19 trimestral | +0.359 | +0.482 | +0.380 | -0.658 a +1.435 |

**Os 12 intervalos de incerteza incluem zero.** O bootstrap preserva blocos de tempo de tamanho médio de um ano e usa 10 mil reamostragens pareadas. São intervalos descritivos após observar a pesquisa, sem correção pela busca adaptativa: não são evidência confirmatória. A medição continua omitindo dividendos/JCP ordinários, impostos e disponibilidade efetiva dos direitos.

**Ganho no passado e risco.** Abaixo está o crescimento geométrico hipotético das marcas na abertura, subtraindo 72 pb a cada período e supondo reinvestimento de todos os valores marcados. Valores ainda não recebidos podem estar incluídos nessas marcas; portanto isto não é saldo executável de uma conta. As quedas são medidas entre finais de período e podem subestimar as perdas dentro de cada mês ou trimestre.

| Hipótese | Janela de compra/saída | Crescimento hipotético anual | Maior queda entre marcas |
|---|---|---:|---:|
| H18 mensal | 2018-05-02 a 2026-02-02 | 2.64% | -49.81% |
| H18 trimestral | 2018-07-02 a 2026-04-01 | 9.25% | -41.96% |
| H19 mensal | 2018-05-02 a 2026-02-02 | 2.43% | -48.03% |
| H19 trimestral | 2018-07-02 a 2026-04-01 | 9.35% | -44.55% |

Na H19 trimestral, o cenário adverso reduz o crescimento hipotético e mantém perdas elevadas. Não foi escolhido o fechamento só porque ele apresentou resultado melhor. A régua exploratória original de 0,42 p.p./mês continua sendo uma premissa de pesquisa; você informou capital de R$5–10 mil, sem definir um lucro mínimo anual.

**Custo de oportunidade.** Na mesma janela trimestral, a Selic diária oficial acumulou o equivalente a 9.02% ao ano, antes de impostos e custos de produto. A proximidade dos números pede cuidado com o valor econômico da pesquisa. A comparação ainda não determina um vencedor líquido: a carteira de ações omite dividendos e a referência Selic é bruta. [Fonte e unidade da série 11, Banco Central](https://dadosabertos.bcb.gov.br/dataset/11-taxa-de-juros---selic).

**Proventos: avancei na fonte, sem inventar retorno.** Os históricos foram localizados para os 126 instrumentos da coorte, incluindo nomes antigos de empresas que deixaram de negociar. Foram examinadas 872 linhas nas janelas necessárias; os preços anteriores informados coincidem com o COTAHIST. Só 92 linhas encontraram ao menos uma data de pagamento no suplemento B3 consultado, o que não certifica a completude ou unicidade desses pagamentos. Algumas mudanças de emissor ainda exigem reconciliação.

Há 10 grupos com valor, data e aprovação repetidos. Repetição não equivale a erro: na WEGE3, três registros iguais correspondem no suplemento a pagamentos em 2026, 2027 e 2028. Somar tudo como dinheiro imediatamente disponível ou apagar parcelas duplicadas distorceria a carteira. A primeira auditoria de correspondência por texto foi corrigida para comparar decimais sem zeros insignificantes; ambas versões ficaram preservadas e nenhuma gerou retorno de estratégia.

**Capital de R$5–10 mil.** Na H19 trimestral, 182/233 tickets com R$5 mil e 115/233 com R$10 mil ficariam abaixo de 100 ações, usando alocação equiponderada inicial e custo por lado de 36 pb. Localizei 4.225 cotações fracionárias em 4.226 endpoints procurados e todos os endpoints dos ativos selecionados. A única ausência é JBSS32 em 01/07/2025, BDR cujo suplemento informa lote de uma unidade; não se deve exigir um mercado fracionário separado para esse caso. [Regra B3 de lote unitário de BDR](https://www.b3.com.br/pt_br/noticias/alteracao-no-lote-padrao-de-bdrs-e-etfs.htm).

Isso fecha a busca de preços necessários, mas não mede ainda uma carteira contínua de R$5 mil ou R$10 mil: faltam giro efetivo, lotes/frações gerados por eventos, recebimentos, custos sobre as ordens reais e impostos. Cotações diárias também não garantem execução ao preço mostrado.

**H1–H19 e decisão.** A revisão anterior de H1–H16 permanece preservada, com 15 estudos negativos e H3 não executada. Eles não foram rodados novamente nesta etapa. H17 continua inconclusiva e sem ganho demonstrado; as quatro configurações H18/H19 receberam esta validação. Não há promoção a Proof, operação real ou evidência de que o lucro futuro esteja garantido. H18 perde prioridade por instabilidade; H19 trimestral merece no máximo pesquisa limitada à reconciliação de caixa e execução das mesmas seleções.

Contagem conservadora atual: pelo menos 32 configurações e 37 avaliações históricas, com histórico adaptativo antigo desconhecido. As oito novas sensibilidades de preço foram contabilizadas. Reproduções idênticas, auditorias de fonte e a comparação de oportunidade não são novas hipóteses independentes. Nenhum parâmetro, janela ou limiar foi ajustado para produzir lucro.

**Reprodução.** O pacote `STOCKS_VALIDACAO_LUCRO_TESTADA.zip` e o lançador `RODAR_VALIDACAO_LUCRO_STOCKS.py` reproduzem offline a observação anterior, o segundo cálculo e os 12 cenários com bootstrap. Incluem fontes, hashes, código e logs. O lançador exige Python 3.13 e não instala dependências, não envia ordens e não faz downloads. A confirmação da execução do pacote fica em `VALIDACAO_LUCRO_REPRODUCAO.json`.

O próximo teste econômico depende da conclusão do caixa: recebimentos nas datas efetivas, reinvestimento somente do disponível, giro entre carteiras, quantidades inteiras e benchmark sob a mesma execução. Se essa reconciliação exigir pesquisa extensa diante da vantagem e da incerteza atuais, encerrar o aprofundamento será uma decisão econômica válida. Não faz sentido multiplicar variantes até aparecer um positivo.

Reproducao offline executada: PASS. Os 1.448 arquivos foram verificados; as quatro coortes originais, as 9.732 celulas, os 12 cenarios e seus intervalos de bootstrap foram reproduzidos sem diferencas.
