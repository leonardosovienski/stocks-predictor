# Revisão dirigida de fontes e limites — R7

Autor: mesmo assistente que conduziu as rodadas anteriores. Revisão individual,
sem revisor independente. Escopo: documentos materiais já presentes, rotas
dirigidas para pagamentos faltantes e termos dos conjuntos efetivamente usados.
O conjunto de 794 documentos não foi lido integralmente de ponta a ponta nesta
rodada. Hash, extração e pesquisa de texto têm alcances diferentes de leitura.

**Resultado de dados econômicos: nenhuma alteração admitida na Fonte15.**
Permanecem 50 líquidos ausentes, dos quais 22 também têm data de pagamento ausente;
28 registros societários e 1.590 ocorrências sobrepostas de 15 classes. Essas
contagens não representam 1.590 defeitos independentes. O consolidado mantém os
registros individuais e todos os intervalos, inclusive resultados negativos.

## Decisões materiais

As referências SHA abaixo correspondem aos arquivos `primary/` da Fonte15,
cujo manifesto completo é
`1c6410bebc9627d6dea8ae6ac4a9034823786fa47c48c26a8632c529c8560c46`.

| Documento / localizador | Leitura e resultado | Consequência |
|---|---|---|
| SLCE, aviso de 30/04/2019, SHA eee7eb502367f6e67348cf91775b23a790681fc367d265beb346d501c41acbdf, p.1 | Texto e página renderizada conferidos. R$0,947055 considera o desdobramento; pagamento em 09/05/2019; documento declara ausência de IR. | O nominal B3 preservado é R$1,894109. Dobrar o valor arredondado do aviso dá diferença de R$0,000001; falta conciliar quantidade/unidade do livro. Não preencher líquido na unidade antiga com o valor novo. |
| RD, AGO2021 e manuais de AGO2024/2025 já adquiridos em R6 | Trechos materiais de proventos e tabelas históricas revistos. Datas-limite e valores históricos não demonstram por si o pagamento dos JCP de 2020/2022. | Não converter “até 31/05” em pagamento comprovado em 31/05. |
| RD, ata publicada em 06/05/2023 | A agenda menciona dia 31/05/2023, mas a deliberação descreve prazo “até” essa data para JCP/dividendos. | A redação mais forte da agenda não substitui a deliberação nem comprova recebimento. [Documento primário da companhia](https://estadaori.estadao.com.br/wp-content/uploads/2023/05/raia-drogasil-sa-ata-2023-05-06_01-29-49.pdf). |
| B3, BDI de 31/05/2023 e 05/05/2023 | Capítulo 05 de um dia tem só uma página de clearing. BDI00 de 31/05 tem 82 páginas e BDI04 tem 63; pesquisa do texto extraído não encontrou RADL. | O número de capítulo muda entre períodos. Corpos sem a tabela alvo não provam ausência de evento. |
| CXSE, aviso 2024, prefixo SHA 5236dfa, p.1 | Nominal 0,550580432 e atualizado 0,566339055 distinguem dividendo e rendimento. | O rendimento de 0,015758623 exige tratamento próprio; bruto não é líquido. |
| CXSE, aviso 2026, prefixo SHA fa491, p.1 | Nominal 0,35 e atualizado 0,352128404, com IRRF sobre atualização. | A Fonte15 já contém o rendimento separado de 0,002128404; não era nova omissão de evento. |
| VBBR, SHA 5762ff (aviso 1368), p.1 | Valor estimado 0,31403898619, pagamento em 27/02/2026 e retenção segundo legislação aplicável. | Valor estimado e cláusula genérica não certificam líquido final. |
| VBBR, avisos 1524/1525, prefixos SHA 6988/6f44 | Cadeia de correção distingue 15/09/2026 de 15/09/2027. | A Fonte15 já preserva a data corrigida de 2027. Pagamento futuro não vira caixa recebido. |
| PSSA, documento final com prefixo SHA 5741c3, p.1; créditos B3 d081, p.2 | Declaração final e quatro parcelas de JCP identificam brutos e data, sem líquido individual. | A existência de um bruto final não fecha imposto/arredondamento pessoal. |
| ALOS, avisos com prefixos SHA 88dd/77fd, p.1 | Valores finais e datas das parcelas foram conferidos. | Valor final do dividendo não certifica automaticamente o líquido fiscal da pessoa em 2026. |
| MOVI, aviso 1514, prefixo SHA 3c970, 24 páginas | Trechos materiais indicam opção de integralização de capital com crédito de JCP; não houve certificação de leitura integral das 24 páginas. | Escolha do titular pode mudar entrega/caixa. Não presumir todo o JCP como dinheiro recebido. |
| SMFT, RENT e VALE, prefixos SHA 74e29/0b7/c8a, páginas materiais | Cláusulas de retenção/legislação vigente, valores e datas revistos. | Cláusula genérica não prova alíquota aplicável ao fato gerador específico. |

Os localizadores abreviados da tabela são índices de leitura, não identidades
criptográficas autossuficientes. O catálogo preservado e os registros de caixa da
[base V2](baseline-v2.json) contêm as identidades completas e URLs por evento.

## Tributo e unidade não são preenchimento automático

A [LC224/2025, arts.8 e 14](https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp224.htm)
altera a alíquota de JCP para 17,5% com efeitos em 01/01/2026, vinculada ao pagamento
ou crédito ao beneficiário. A consulta do texto primário foi possível no navegador
de pesquisa; a captura direta falhou e essa falha permanece no recibo. Isso
reforça a necessidade de identificar o fato gerador antes de aplicar uma taxa.
Esta revisão não arbitrou o enquadramento individual de cada crédito anterior a
2026 pago posteriormente, nem a fiscalidade pessoal dos dividendos de 2026.

Ambev tem parcelas e arredondamentos próprios; restituições de capital dependem
da base fiscal; frações e sucessores dependem da quantidade/carteira. A data da
consulta atual não comprova quando cada informação ficou publicamente disponível.
Não foi criada uma Fonte16 apenas para reduzir contadores sem novas provas.

## Aquisições e reprodução

[Recibos de aquisição](evidence/acquisitions.json) preservam sucessos, HTTP500,
conexão fechada e página de erro retornada como HTTP200. As respostas completas
ficam no pacote local R7; pesquisa sem resultado não é atestado de inexistência.

O [materializador](../../../tools/materialize_source_revision.py) conferiu os
manifestos da Fonte14 e Fonte15 e reconstruiu os 830 arquivos da Fonte15 em destino
novo a partir de seis arquivos alterados mais manifesto. O
[recibo](evidence/source15-materialized.receipt.json) prova identidade de bytes,
sem elevar isso a completude econômica ou publicação histórica certificada.
