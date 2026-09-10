# H22 — implementação anterior à primeira medição

O protocolo foi publicado no commit `1d2b62594f7b7b61848092e32217ddee47753477`.
Uma única regra mensal de dez meses, 24 avaliações previstas. Não há busca de
parâmetros. Todas as janelas são retrospectivas e já expostas; nenhuma é holdout.

O artigo de Faber, páginas 21–22, especifica a média mensal, mas usa fechamento
do próprio sinal, retorno total e juros de Treasury bills, excluindo tributos,
comissões e slippage. H22 é uma adaptação explicitamente registrada para BOVA11:
próximo pregão, caixa zero, custos e impostos brasileiros hipotéticos. Igualdade
fica em caixa. Não se atribuem ao Brasil os resultados estrangeiros do artigo.

Valores em centavos, arredondamento comercial half-up por ordem e por mês fiscal.
A tarifa variável é um cenário agregado de despesas/atrito, não fatura de corretora.
O preço adverso usa o pior entre abertura e fechamento: stress de preço, não
promessa de execução nem limite superior certificado para slippage. O lote máximo
considera a tarifa arredondada. Taxas e despesas internas do fundo já estão na cota.

Imposto calculado sobre resultado realizado mensal, com prejuízos anteriores;
despesas mensais não são deduzidas da base tributável. A reserva tributária permanece
comprometida e fora do caixa reinvestível. Não há pagamento real de DARF. Como o
caixa não rende, segregar indefinidamente o tributo tem o mesmo efeito patrimonial
que pagá-lo. Não se reconstrói o fluxo histórico de créditos de IRRF em meses de
prejuízo; eventual diferença no caixa disponível é pendência operacional, não zero
certificado. Não há histórico tributário externo nem taxa de aluguel de cotas.

Liquidação de venda D+3 antes de 27/05/2019, D+2 depois; a compra compromete caixa
imediatamente. O patrimônio inclui recebíveis e reserva de despesas, deduzindo o
imposto realizado comprometido/provisório. Drawdown usa marcação diária ao fechamento,
sem imposto hipotético sobre posição ainda não vendida. A instrução terminal tem
prioridade: não se abre compra para vender no mesmo dia. Rejeição por lote insuficiente
não provoca tentativas diárias; exige nova mudança do estado desejado.

Reserva integral das despesas mensais é feita antes da compra. O cenário adverso
de R$5 mil na janela inteira exige R$5.250 e é inviável antes de qualquer retorno.
Esta consequência aritmética foi identificada antes da primeira medição e será
preservada. Não será substituída por financiamento externo ou despesas menores.

Preparação inicial falhou antes das medições: filtro BDI14 descartava 92 registros
de 2019. O COTAHIST original e a normalização preservada mostram BDI02 com o mesmo
ticker, ISIN, moeda, mercado à vista e fator. O filtro novo mantém BDI02/14 e exige
essas identidades; nenhum byte antigo é modificado. Todos os preços 2018–2026 devem
ser idênticos à normalização R1. A primeira preparação não produziu inputs nem retorno.

Calendário 2017–2025: dias com registros à vista nos ZIPs anuais, exigindo BOVA11
em todos eles. Isso detecta buracos relativos à publicação, não certifica dias
ausentes de todos os ativos. Calendário 2026: confrontado com fechamentos oficiais
B3 e estendido apenas para liquidar recebíveis e reconhecer meses incompletos.
Os 246 preços de 2017 servem somente à inicialização dos sinais.

Eventos: a hipótese econômica é condicional à ausência de distribuições/splits
não incorporados aos preços. Demonstrações e avisos são revisados como evidência;
ausência de linha de amortização não é certificação integral de inexistência.
Não se calcula sinal sobre uma série chamada ajustada sem ajustes documentados.

A verificação separada reconstitui centavos inteiros, sinais, cronologia, lotes,
preços, despesas, impostos, liquidação e patrimônio sem importar o simulador.
Foi escrita pelo mesmo assistente, não é auditoria de terceiro. Testes sintéticos
e CI validam mecanismos de software; não convertem lucro condicional em futuro.
