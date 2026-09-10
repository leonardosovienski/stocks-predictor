# R5 — pesquisa de lucro e resultado da H22

**A H22 foi rejeitada nos cenários registrados. Comprar e manter BOVA11 continuou
com lucro histórico condicional em parte dos cenários. Lucro integralmente
executável ou futuro ainda não foi validado.** Não houve operação financeira.

O pedido de 10/09/2026 reabriu a pesquisa econômica, autorizando novas hipóteses e
mudanças de arquitetura. Esta rodada executou uma hipótese nova e examinou duas
lacunas documentais concretas. O ganho positivo da alternativa simples não depende
de superar um benchmark: lucro absoluto e vantagem da regra foram julgados separadamente.

## Resultado completo

Todos os valores são ganhos/perdas **nominais em reais**, depois dos custos,
despesas e imposto definidos no protocolo. Não são dinheiro recebido em conta,
retorno real descontada a inflação, reconstrução de notas de corretagem nem previsão.

| Janela | Cenário | Capital | Regra mensal H22 | Comprar e manter | Diferença H22 |
|---|---|---:|---:|---:|---:|
| 2018–08/09/2026 | Referência | 5.000 | −730,04 | +3.627,73 | −4.357,77 |
| 2018–08/09/2026 | Referência | 10.000 | −4,40 | +10.188,46 | −10.192,86 |
| 2018–08/09/2026 | Adverso | 5.000 | Inviável | Inviável | — |
| 2018–08/09/2026 | Adverso | 10.000 | −5.540,43 | +259,43 | −5.799,86 |
| 2018–2021 | Referência | 5.000 | −254,53 | +862,76 | −1.117,29 |
| 2018–2021 | Referência | 10.000 | +55,81 | +2.214,03 | −2.158,22 |
| 2018–2021 | Adverso | 5.000 | −2.522,56 | −1.794,80 | −727,76 |
| 2018–2021 | Adverso | 10.000 | −2.420,82 | −303,33 | −2.117,49 |
| 2022–08/09/2026 | Referência | 5.000 | −417,20 | +2.234,14 | −2.651,34 |
| 2022–08/09/2026 | Referência | 10.000 | −96,01 | +5.749,95 | −5.845,96 |
| 2022–08/09/2026 | Adverso | 5.000 | −2.907,33 | −1.486,44 | −1.420,89 |
| 2022–08/09/2026 | Adverso | 10.000 | −3.420,16 | +2.007,47 | −5.427,63 |

São **24 avaliações previstas, 22 calculadas e reconciliadas, duas inviáveis pelo
orçamento, zero erros econômicos/contábeis na execução**. As janelas se sobrepõem;
não são 24 evidências independentes. O resultado positivo de R$55,81 em um recorte
não resgata a hipótese: o critério registrado exigia lucro na janela integral,
nos dois cenários e capitais. Todos os 11 pares calculáveis tiveram incremento negativo.
O orçamento de construção sustentado por esse incremento histórico é zero.

Os R$5 mil adversos são inviáveis porque 105 despesas mensais de R$50 exigem
R$5.250 de reserva inicial. Essa consequência foi registrada antes de observar
retornos. Não se adicionou capital para forçar uma avaliação possível.

## O que os resultados mostram

Na janela integral, capital de R$10 mil e referência, H22 realizou 20 ordens e
permaneceu com posição em 69,89% das observações. Comprar e manter fez duas ordens.
A queda máxima do patrimônio marcado foi **45,46% na H22 e 44,35% na alternativa**.
O patrimônio mínimo foi R$7.002,73 e R$8.165,82, respectivamente. Não houve melhoria
de lucro ou de queda máxima na janela inteira.

O filtro reduziu a queda máxima em 2018–2021: 24,64% contra 44,35%, no cenário de
R$10 mil/referência, mas deixou lucro de apenas R$55,81 contra R$2.214,03. Em
2022–2026 a queda da H22 foi 30,05%, contra 19,81%, com resultado negativo.
Essa instabilidade aparece nos recortes escolhidos antes da medição; não motivou
trocar o período da média ou escolher outro início/fim.

Na H22 integral/referência de R$10 mil, a atribuição anual soma R$5.707,51 nos anos
positivos e −R$5.711,91 nos negativos. O maior ano positivo é 2019, R$2.543,00,
44,56% da contribuição positiva; 2022 perdeu R$2.161,49. O denominador do ganho
líquido é negativo, portanto uma porcentagem de concentração sobre o lucro líquido
não teria interpretação útil. Os livros registram vendas com perda em 2020, duas
em 2022, 2023 e dezembro de 2024. Isso é compatível com saídas e reentradas em
mercados que alternam direção, não prova causal de que toda regra de tendência falhe.

Comprar e manter, R$10 mil/referência: reserva inicial de R$1.050, compra de 120
cotas a R$74 e venda a R$184,73. Custos das ordens R$65,88, imposto R$1.983,26,
despesas R$1.050; patrimônio final R$20.188,46. No adverso, a reserva R$5.250 reduz
a compra a 60 cotas, os custos somam R$96,12 e o imposto R$972,25, deixando apenas
R$259,43 de ganho nominal após mais de oito anos. Despesa adicional de mesmo valor,
sem mudar a alocação, já consumiria esse ganho. Isso não é margem robusta para
despesas desconhecidas ou promessa de preservação do poder de compra.

Esses números diferem da H21 congelada porque a R5 tem outro término, reserva
prévia de despesas e custos fixos adicionais. Nenhum livro H21 foi reescrito.

## Protocolo, fontes e limites

A [regra e critérios](../2026-09-10-profit-validation-r5-protocol.json) foram
publicados no commit `1d2b62594f7b7b61848092e32217ddee47753477`, antes da implementação
e da primeira medição. Código inicial `8ff6700`; fontes fixadas em `b248a53`.
A execução começou em **10/09/2026 às 14:06:06 UTC**, com esse último commit limpo.
Os [detalhes contábeis](../../../research/session-20260910/profit_validation/METHODOLOGY.md)
foram publicados antes dos resultados. Não houve grade de parâmetros.

A origem externa da regra de dez meses é o [artigo de Meb Faber, páginas 21–22](https://mebfaber.com/wp-content/uploads/2016/05/SSRN-id962461.pdf).
Seu experimento usa fechamento do sinal, caixa remunerado e séries de retorno
total, excluindo tributos e atritos. H22 foi registrada com execução no pregão
seguinte, caixa sem rendimento e custos brasileiros hipotéticos. O artigo não
valida os resultados brasileiros desta adaptação.

Foram confrontadas **2.405 cotações com dez ZIPs originais COTAHIST**: 246 observações
de 2017 para os sinais e 2.159 para 2018–2026. Todas as 2.159 coincidem com a
normalização R1 preservada. Os oito hashes de 2018–2025 coincidem com os recibos
originais. O calendário histórico exige cotação do ETF em todo dia à vista observado;
2026 também foi confrontado com o [calendário oficial B3](https://www.b3.com.br/pt_br/noticias/calendario-de-negociacao-da-b3-confira-o-funcionamento-da-bolsa-em-2026.htm).
Ausência de todos os ativos em um dia anterior a 2026 não é verificável por esse
controle. As fontes foram adquiridas depois dos períodos estudados; isso é uma
reconstrução retrospectiva, sem certificação point-in-time da publicação antiga.

Recuperadas as [demonstrações originais de 2024](https://fnet.bmfbovespa.com.br/fnet/publico/downloadDocumento?id=672335)
e o [aviso de AGO de 2025](https://fnet.bmfbovespa.com.br/fnet/publico/downloadDocumento?id=941503).
A tabela de evolução e a política de resultados de 2024 corroboram a incorporação
dos dividendos da carteira ao patrimônio. Não mostram uma linha separada de
amortização. A AGO de 27/06/2025 não foi instalada; as demonstrações foram consideradas
aprovadas automaticamente. O aviso não anuncia distribuição, split ou incorporação
executada. Com essa recuperação, os 39 itens do catálogo anterior têm corpo original
ou equivalente oficial; a completude do próprio catálogo continua sem certificação.

**O gate de eventos continua parcial.** Ainda falta a reconciliação contínua de
eventos/direitos até o encerramento e liquidação, além do período de inicialização
de 2017. Não ter encontrado evento não significa provar que não houve evento.
Os números são condicionais à inexistência de distribuição/split não refletido.

A [Receita Federal](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1/bolsa-de-valores)
descreve alíquota de 15% para operações comuns, dedução de despesas de negociação
e compensação de perdas. A [isenção mensal de ações não inclui ETFs de ações](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1/isencoes).
O simulador agrega realizações no mês e reserva imposto, sem devolver tributo de
meses anteriores quando surgem perdas posteriores. Fluxos reais de DARF e créditos
de IRRF em meses de prejuízo não foram reconstruídos.

**O gate de custos continua parcial.** Referência: abertura, 0,18% por lado mais
R$5 por ordem e R$10/mês. Adverso: pior entre abertura/fechamento, 0,36% mais
R$20 por ordem e R$50/mês. São cenários, não limites superiores certificados.
A [Rico publica corretagem zero de ETF para execução digital pelo próprio cliente](https://www.rico.com.vc/custos/),
mas isso não demonstra elegibilidade ou faturas históricas. A preferência XP
permanece sem dados de conta/canal/assessor. Os HTTP403 nas capturas Rico/XP foram
preservados; observação web não foi apresentada como captura bruta bem-sucedida.

Todos os detalhes de recuperação, hashes e lacunas estão no
[registro de fontes](source-review.json) e [recibo dos preços](inputs-receipt.json).

## Validação e continuidade

O replay separado em centavos conferiu **30.226 observações de patrimônio**, sinais,
preços, quantidades máximas, fluxo de despesas, reservas tributárias e datas de
liquidação. Ele não importa o simulador, mas foi escrito pelo mesmo assistente;
não é revisão independente por outra pessoa. Os 12 testes sintéticos abrangem
arredondamento, mudança temporal, ausência de cotação, impostos, lotes e adulteração
de valores. Sucesso de software não certifica lucro econômico.

A [CI206 do commit da medição](https://github.com/leonardosovienski/stocks-predictor/actions/runs/34486825764)
passou **859 testes e 29 subtestes em cada Python 3.13/3.14**, cobertura de 79%,
Ruff, Pyright, lock, metadados, build/wheel fora do checkout e segredos.
[Recibo por job](ci-experiment.json). A CI205 foi cancelada por substituição do
commit; não é contada como nova evidência nem falha econômica. O PR registra os
checks adicionais da entrega final.

A [segunda execução](reproduction.json), após endurecer as recusas do runner,
reproduziu exatamente os 24 casos, ordens, impostos e 30.226 observações. Apenas
metadados de horário/commit diferem. Não foi contada como nova evidência econômica.

Decisões: rejeitar H22 neste registro; preservar o ganho nominal condicional da
exposição simples; não promover uma variante escolhida depois dos resultados.
Nenhuma das janelas é holdout intacto. Os 24 casos, incluindo negativos e inviáveis,
estão em [results.json](results.json); ordens e impostos em [ledgers.json](ledgers.json).
[Reprodução e arquivos locais](../../../research/session-20260910/profit_validation/README.md).
Integração e checks por SHA: [PR76](https://github.com/leonardosovienski/stocks-predictor/pull/76).

O objetivo de lucro validado permanece **não atingido**. Mais busca dentro da mesma
história não cria dados futuros nem resolve custos desconhecidos. Uma continuação
útil precisa de uma hipótese economicamente distinta registrada antes de medir,
fontes completas e validação posterior ao registro. O plano prospectivo H21 já
existente foi preservado e não foi ativado; H22 não foi promovida para operação.
