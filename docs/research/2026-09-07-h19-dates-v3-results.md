# H19: 16 datas resolvidas; lucro ainda não demonstrado

Atualização de 07/09/2026. Foram conciliadas com documentos primários as 16
linhas da carteira selecionada que ainda não tinham data candidata de pagamento.
A reprodução offline confirmou as correções e preservou as seleções e os
valores brutos anteriores. **Não foi executada uma carteira histórica completa
nem calculado um novo lucro líquido.**

| Fila original | Antes, V2 | Agora, V3 |
|---|---:|---:|
| Linhas com pagamento individual revisado | 144 | 160 |
| Dessas, linhas selecionadas | 107 | 123 |
| Selecionadas sem data candidata | 16 | 0 |
| Total sem data candidata, incluindo comparação | 545 | 529 |

A fila contém 778 linhas, sendo 133 selecionadas. Entre as selecionadas, além
das 123 revisões individuais, duas linhas têm calendário explícito de parcelas
da Aliansce. Outras oito têm apenas datas candidatas, ainda sujeitas a revisão.
Essas contagens não certificam que todo o histórico de proventos esteja presente.
A fila original exclui os 11 eventos posteriores da JBS já encontrados e o
caixa ordinário dos sucessores.

As 16 correções abrangem Valid, Copasa, BR Malls, Tupy, Banco do Brasil,
Neoenergia, Natura, Allos, Cogna e Eztec. As três atualizações do Banco do Brasil
foram conciliadas por diferença decimal entre o total atualizado e o valor
nominal; os componentes continuam separados para evitar crédito em duplicidade.
As datas de Cogna e Eztec foram confirmadas nas tabelas de crédito da B3:
[Cogna, página 4](https://arquivos.b3.com.br/bdi/download/bdi/2025-05-30/BDI_05_20250530.pdf)
e [Eztec, página 4](https://arquivos.b3.com.br/bdi/download/bdi/2025-08-29/BDI_05_20250829.pdf).

As ressalvas das fontes foram preservadas: tradução inglesa da Tupy com data
incompatível com o original português; erro de exercício na ata da Copasa;
precisão arredondada em avisos; e valor líquido inconsistente num aviso anterior
da Natura. Uma data conciliada não aprova automaticamente o valor líquido.

O pacote V3 foi extraído numa pasta nova. Os 71 arquivos do manifesto foram
verificados; o cadastro reconstruído a partir da V2 e das fontes ficou idêntico
ao entregue. A auditoria executou os quatro testes da compra inicial e retornou
o bloqueio esperado `BLOCKED_MISSING_EVIDENCE`, código 2. O bloqueio representa
evidência e integração pendentes, não uma falha inesperada do programa.
O runtime permaneceu inalterado: os 558 testes pertencem à validação anterior
do commit `5e71bc8642cc2b0759e8a1885cab446e315121fd` e não foram repetidos nesta rodada.

Ainda são necessários:

1. Revisar as oito datas candidatas selecionadas e certificar a completude de
   proventos nas janelas de ambas as carteiras, incluindo JBS e sucessores.
2. Conferir valores líquidos, entregas de ações, frações e bases fiscais.
3. Integrar a carteira contínua com liquidações, giro efetivo e calendário fiscal.
4. Executar os casos completos para R$5 mil e R$10 mil, mantendo seleções,
   premissas registradas e contagem de avaliações.

A auditoria ainda exige cobertura de 1.237 intervalos potenciais, dos quais 236
selecionados. As pendências do conjunto incluem 12 reorganizações e 24 eventos
ordinários de ações. Contagens de campos ou intervalos pendentes não representam
o mesmo número de erros de software.

Para dimensionar o esforço de pesquisa: cada 1 ponto percentual de ganho anual
adicional equivale a R$50 sobre R$5 mil ou R$100 sobre R$10 mil, antes de qualquer
custo ainda não incluído. Isso é apenas uma relação aritmética, não previsão de
retorno. O usuário ainda não definiu lucro anual mínimo ou horas aceitáveis;
não há base para afirmar que a reconstrução completa compensará economicamente.

**Decisão preservada:** H19 continua inconclusiva em Discovery. Não houve nova
observação de retorno, promoção para Proof ou alteração do fator para buscar
um resultado melhor. Contagem acumulada: pelo menos 32 configurações e 37
avaliações históricas. Os dados ainda não demonstram lucro nem ausência de lucro.

Arquivos entregues nesta atualização:

- `STOCKS_H19_DATAS_E_AUDITORIA_V3.zip`: fontes necessárias, scripts, runtime e
  manifesto; reprodução sem rede e sem dependências adicionais.
- `H19_CAIXA_PAGAMENTOS_REVISADOS_V3.json`: cadastro com as correções e ressalvas.
- `H19_CAIXA_EXECUCAO_V3.json`: resultado da auditoria.
- `H19_DATAS_V3_REPRODUCAO.json`: recibo de reprodução e hashes.

SHA256 do ZIP:
`5ba1884ab9b414583f22f2d225e03539398d57b006f04b345b8dfb1e2574b1dd`.
Versões anteriores preservadas. O pacote é de conciliação e auditoria; ainda
não contém um simulador histórico contínuo concluído.
