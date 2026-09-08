# Teste do Stocks Predictor: houve melhora no lucro?

**Houve melhora no resultado composto do diagnóstico histórico. Ainda não é possível concluir que a projeção de lucro líquido melhorou.** O histórico mais recente e a incerteza estatística impedem tratar essa diferença como uma vantagem futura demonstrada.

Foram comparados os três conjuntos de ações já congelados na H20, sem ajustar pesos de fatores, cortes de ranking, ativos ou datas depois de observar retornos. O teste cobriu **31 trimestres**, de **02/07/2018 a 01/04/2026**. A data de sinal 29/03/2018 permaneceu registrada e bloqueada por cobertura insuficiente; nenhuma data elegível foi retirada pelo resultado.

## O que os números medem

A tabela mostra **variação geométrica anualizada de uma carteira sintética**, com custos assumidos de negociação. Inclui cotações, fatores e direitos societários do painel anteriormente auditado, mas **omite dividendos/JCP ordinários, impostos, atrasos de pagamento/entrega, arredondamentos e manutenção**. Portanto não é retorno total, lucro líquido executável nem previsão para o próximo ano.

Cada trimestre atribui pesos iguais aos nomes selecionados e supõe liquidação/reinvestimento completo. O custo hipotético é igual para todas as alternativas: `(1 + variação do trimestre) × (1 − custo)/(1 + custo) − 1`. As taxas de 0,18% e 0,36% por lado são as premissas anteriores do projeto. Não representam uma tarifa atual recém-verificada.

| Preço de compra/saída | Custo por lado | Valor — controle comum | Valor + rentabilidade | Com retenção de nomes |
|---|---:|---:|---:|---:|
| Abertura | 0,18% | 11,00% | 14,02% | 14,58% |
| Abertura | 0,36% | 9,41% | 12,39% | 12,94% |
| Fechamento | 0,18% | 12,77% | 14,96% | 15,17% |
| Fechamento | 0,36% | 11,16% | 13,31% | 13,52% |
| Adverso | 0,18% | 3,53% | 6,26% | 6,78% |
| Adverso | 0,36% | 2,05% | 4,74% | 5,25% |

O cenário adverso compra pelo maior preço entre abertura e fechamento e vende pelo menor. As seis combinações foram reportadas. Na abertura e custo base, a diferença anualizada entre retenção e controle é **3,58 pontos percentuais**, de 11,00% para 14,58%. No cenário adverso com custo dobrado, é **3,20 pontos**, de 2,05% para 5,25%. A forte queda de nível no cenário adverso mostra a sensibilidade à execução.

O controle usa **exatamente o mesmo universo válido** das duas alternativas H20, isolando melhor o efeito da seleção. A H19 original, com seu universo diferente, teve 10,91% no mesmo cenário de abertura/custo base, contra 11,00% do controle comum; no adverso com custo dobrado, 1,95% contra 2,05%. Esses números H19 são referências de diagnóstico, também sem lucro líquido. O universo comum equiponderado teve 5,60% e −3,21%, respectivamente; não é índice de retorno total ou carteira passiva executada.

## Por que a melhora ainda é incerta

- Na abertura/custo base, a retenção superou o controle na média por apenas **0,197 ponto percentual por trimestre**, vencendo em **16 dos 31**. O intervalo descritivo de 95% vai de **−3,61 a +3,92 pontos por trimestre**; inclui piora expressiva.
- A comparação do valor com rentabilidade, sem retenção, também não excluiu zero. Todos os intervalos das três comparações principais, nos três preços e dois custos, incluem zero. Não são intervalos ajustados pelas tentativas anteriores.
- Na divisão fixada antes da medição, a retenção teve vantagem média bruta de **+0,77 ponto por trimestre nos primeiros 15**, mas **−0,34 ponto nos últimos 16**. Estes últimos correspondem aos sinais de 2022–2025 e encerram em abril de 2026. O sinal dessa vantagem recente também foi negativo no fechamento e no cenário adverso.
- Uma trajetória composta melhor pode coexistir com uma diferença média pequena ou negativa. No fechamento, por exemplo, a retenção teve composição anualizada maior, mas diferença média de **−0,085 ponto por trimestre** contra o controle, com custo base. Nenhuma das duas métricas deve ser ocultada.
- A queda máxima medida somente entre finais de trimestre foi **−40,42%** com retenção na abertura/custo base. No adverso com custo dobrado chegou a **−48,24%**, contra **−45,13%** do controle. Perdas dentro do trimestre podem ter sido maiores.

## O que foi e o que ainda não foi executado

O teste utilizou a **sequência de nomes pretendidos** já arquivada na H20. A tolerância de peso de 2,5% e a retenção baseada no livro real não foram executadas numa carteira contínua. Não foi atribuído nenhum ganho financeiro às 26 substituições de nomes evitadas no diagnóstico anterior. Todas as alternativas receberam o mesmo cenário de rotação integral e custos; a economia real pode ser diferente.

Os capitais de R$5 mil e R$10 mil aparecem no JSON como equivalentes sintéticos de patrimônio, sob reinvestimento integral das marcações. Esses valores **não são lucro e não servem como projeção anual em reais**. Os campos `profit` e `future_profit_projection` permaneceram `null`.

A execução econômica H19 foi repetida e retornou `BLOCKED_MISSING_EVIDENCE`, byte a byte igual à anterior. Continuam 1.237 intervalos H19 sem inventário integral de caixa e 36 registros societários sem integração/aprovação, entre outras lacunas. Para H20, cada seleção requer 231 intervalos de posição trimestral; há **zero certificados integrais de caixa disponíveis**. Estes intervalos não certificam posições mantidas por vários trimestres, sucessores ou seu tratamento fiscal. Fontes da H19 não habilitam automaticamente a H20.

Assim, o impedimento atual é a evidência econômica e a execução contínua da H20. Não é uma falha detectada nos testes nem lucro igual a zero. Uma projeção líquida válida exige aplicar os eventos, caixa e base fiscal ao livro efetivo de cada alternativa, com compras/vendas inteiras e fracionárias e custos de manutenção coerentes.

## Verificação e reprodução

- **639 testes do projeto passaram** em 71,85 segundos; **11 testes novos da medição passaram**. Estes testam médias calculáveis à mão, custo simétrico, identidades, causalidade, falha de entrada, fontes ausentes, períodos faltantes e integridade do protocolo.
- **1.448 arquivos do pacote histórico foram verificados**. A reprodução a partir dos extratos de cotações em SQLite somente leitura reconstruiu **9.732 células, quatro coortes e os 12 cenários antigos**, incluindo seus intervalos, sem diferenças.
- Um segundo cálculo conferiu **465 médias de carteiras**, **30 composições/annualizações/drawdowns** e **54 comparações pareadas com suas metades fixas**. Não reutilizou as funções da nova medição para essas contas.
- A nova observação H20 foi reproduzida **byte a byte**: SHA256 `aa184580bf5ba69b515a20cc40115453396bdefa470ac0f5408c0d3ced15e1a3`.
- Protocolo registrado no commit `9286129`, antes de cruzar seleções com retornos; medidor testado em `2488171`. O runtime de produção não foi alterado. Bancos principais, dados brutos, ledgers e quarentenas foram preservados. Nenhuma instalação, ordem, gasto ou push remoto.

O pacote contém o medidor, testes, protocolo, resultado completo, verificação e logs. O comando está em `REPRODUZIR_TESTE.ps1`; exige o Python 3.13 global e reutiliza as fontes preservadas na raiz de pesquisa. As saídas são novas e o resultado financeiro permanece explicitamente desconhecido.

## Decisão registrada

**Melhora histórica aparente, vantagem incremental inconclusiva e lucro líquido não calculável.** Não promover a H20 com base nesses números nem ajustar o histórico para fortalecer a melhora. O desempenho recente não justifica, por si só, uma reconstrução manual extensa para capital de R$5–10 mil. O trabalho seguinte só se justifica com uma rota barata para completar caixa/eventos e validar prospectivamente a execução da regra congelada.

Foram observados 18 cenários novos, contando conservadoramente três seleções × três preços × dois custos: mínimos **53 configurações e 55 avaliações históricas**. São diagnósticos no mesmo histórico já exposto, não 18 provas independentes ou um holdout novo. Estado mantido: `INCONCLUSIVE_NET_PROFIT / OPERATIONAL_NO_GO`.
