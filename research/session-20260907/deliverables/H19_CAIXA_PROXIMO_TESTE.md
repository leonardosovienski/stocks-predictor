# H19 trimestral: próximo teste e correções de caixa

**Decisão: continuar apenas a correção das fontes para o teste de execução. Não há lucro líquido demonstrado nem promoção para Proof.**

O próximo resultado útil é uma carteira contínua das mesmas seleções H19, com R$ 5 mil e R$ 10 mil, ações inteiras, pagamentos nas datas corretas, custos sobre o giro efetivo e impostos aplicáveis. Esse cálculo ainda não foi executado: os dados de caixa não estão completos.

**O que esta rodada resolveu**

| Achado | Resultado verificado | Limite |
|---|---|---|
| Banco do Brasil | 13 registros de caixa reconciliados, 11 em posições selecionadas | Três registros de atualização monetária ainda não reconciliados; não certifica cobertura integral |
| JBS | 11 dividendos posteriores a 2019 ausentes na consulta B3 por nome histórico | A tabela do RI usa quatro casas decimais; valores arredondados exigem aviso específico |
| JBS, junho de 2023 | Ata e tabela histórica concordam em R$ 1 por ação, ex em 23/06 e pagamento em 29/06 | A ata chama o valor de estimado; a tabela posterior relata o pagamento. Não é comprovante de custódia |

Os 11 dividendos ausentes da JBS afetam 11 células trimestrais: **uma selecionada e dez apenas no universo de comparação**. Não representam 11 ganhos adicionais da estratégia.

No Banco do Brasil, a B3 confirma o crédito de R$ 0,09044686629 por ação em **12/06/2025**; o PDF do RI traz 2024 nessa linha. Outro ajuste distingue a data civil declarada de 24/02/2020 do primeiro pregão ex, 26/02/2020. Rendimentos de atualização foram conciliados separadamente do provento original para evitar dupla contagem.

**O que continua faltando**

A fila inicial tinha 778 células de caixa nos instrumentos originais, 133 em posições selecionadas. Depois das conciliações do BBAS, ainda restam **644 células sem data candidata na fila original, 89 selecionadas**. Essas contagens não incluem os novos eventos da JBS nem proventos dos sucessores. Ter uma data candidata também não prova completude, identidade ou unicidade.

Antes de medir lucro, é necessário:

1. Completar datas e valores das mesmas posições e do universo de comparação, incluindo sucessores; verificar também lacunas sem registros.
2. Distinguir parcelas, atualizações monetárias e pagamentos extraordinários já considerados nas reorganizações.
3. Executar a carteira contínua com crédito efetivo de dinheiro e ações, frações, posições mantidas e lotes negociáveis.
4. Aplicar custos ao giro real, tributação por instrumento e período e comparar com uma alternativa de caixa em bases equivalentes.
5. Encerrar a linha se o ganho plausível não justificar risco e manutenção; nenhum ajuste de fator ou janela para resgatar o resultado histórico.

O custo da reconstrução continua sendo critério de parada. Cobertura insuficiente implica resultado inconclusivo ou pausa; não autoriza substituir proventos desconhecidos por zero e chamar a simulação de lucro líquido. Os R$ 5–10 mil são cenários informados pelo usuário. O lucro mínimo e as horas aceitáveis de manutenção ainda não foram definidos.

**Verificação e rastreabilidade**

Não houve novo cálculo de retorno, mudança de seleção ou alteração dos bancos. Permanecem os mínimos de 32 configurações e 37 avaliações históricas; esta rodada é auditoria de fontes. O código de estratégia permanece no estado anteriormente testado, com 539 testes aprovados; a suíte não foi repetida nesta rodada de dados/documentação. Scripts do piloto concluíram e os hashes das fontes foram conferidos.

O pacote de evidência contém as fontes primárias deste piloto, o histórico BBAS usado, as filas, resultados e scripts. É um arquivo de auditoria; não contém a base completa nem um simulador de lucro pronto. O pacote de validação anterior continua preservado.

Fontes: [histórico oficial JBS](https://ir.jbsglobal.com/shareholder-information/dividends/), [ata JBS de 19/06/2023](https://api.mziq.com/mzfilemanager/v2/d/043a77e1-0127-4502-bc5b-21427b991b22/11a431b2-5282-5345-0234-53fdf7524bfb?origin=1), [B3: crédito de 12/06/2025, página 4](https://arquivos.b3.com.br/bdi/download/bdi/2025-06-12/BDI_05_20250612.pdf), [histórico de pagamentos BBAS](https://api.mziq.com/mzfilemanager/v2/d/5760dff3-15e1-4962-9e81-322a0b3d0bbd/14581997-4233-3b2e-1d82-0d9c766cb7ec?origin=2).

O BDI_05 de 29/06/2023 baixado neste piloto contém somente um quadro de negociação. Foi preservado como tentativa sem evidência de crédito e não comprova pagamento da JBS.
