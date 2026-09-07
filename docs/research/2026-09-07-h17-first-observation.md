# H17: primeira observação e correção de medição

Código da primeira execução: `00a4a13b649e23a2af1200d4ea8ab69f5ed1094b`.
Suíte: 479 testes aprovados em 138,63 s. O diagnóstico real foi executado sob o
protocolo lacrado `H17-DISCOVERY-PRICE-DIAGNOSTIC-1`. A família H17 já foi observada.
As fontes, janela, direção e parâmetros permanecem os do registro anterior.

Primeiro resultado: `INCONCLUSIVE_DATA_QUALITY`; 94 meses elegíveis dentre 96,
56 com todos os retornos medidos; 5.348 de 5.399 células medidas. Das 51 não
medidas, 15 eram do quintil selecionado. IC médio disponível -0,013189 e spread
médio mensal apenas nos meses completos -0,252221 ponto percentual. Esses
valores são condicionais à disponibilidade futura dos dados, não P&L executável
nem prova negativa definitiva da tese em retorno total.

A inspeção das 51 células revelou quatro falsas divergências mecânicas:
MULT3 em 23/07/2018, TOTS3 em 04/05/2020 e CSMG3 em 26/11/2020 tinham fator
legado 0,333333 versus B3 1/3. A tolerância implementada era mais rígida que o
limite de diferença relativa de 0,01% já escrito no protocolo. VIVT3 em
15/04/2025 tinha fator legado líquido 0,5, correspondente aos componentes B3
1/80 × 40 = 0,5. Comparar o líquido com apenas o desdobramento era incorreto.

Correção: reconhecer a precisão registrada e a equivalência do fator líquido
com o produto dos componentes. O fator B3 não é alterado nem aplicado em dobro;
divergências materiais continuam bloqueadas. Quatro regressões reais foram
acrescentadas. A primeira saída é preservada integralmente; a correção gera uma
segunda observação identificada, nunca substitui a primeira.

Contagem: pelo menos 16 candidatos nominais expostos, incluindo H17, após 15
candidatos históricos. Após a reexecução corrigida haverá pelo menos 17
avaliações históricas de retorno (15 anteriores + duas saídas H17); isso não
representa 17 famílias independentes. O denominador adaptativo real continua
desconhecido. H18/H19 permanecem não observadas e seus bloqueios são mantidos.
