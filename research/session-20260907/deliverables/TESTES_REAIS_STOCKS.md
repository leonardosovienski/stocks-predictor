# Testes reais Stocks — 07/09/2026

**Funcionamento: aprovado nos controles executados. Rentabilidade de H17–H19: ainda não avaliada.**
O trabalho foi executado na cópia isolada. O usuário não precisa rodar comandos para concluir estes testes.
A reconstrução integral necessária ao backtest das estratégias continua incompleta; esta entrega não a declara concluída.

## O que foi corrigido e testado

1. Capital histórico: leitura da escala no documento original da CVM, separada da escala monetária das demonstrações. Para 31/12/2023, BBAS informa 2.865.417.020 ações e Energisa 2.039.086.540 em unidades. Ambev informa 15.753.833 **milhares** de ações, equivalentes a 15.753.833.000 com precisão arredondada. Ações em tesouraria ficam separadas. Três documentos não completam todo o histórico nem resolvem preços distintos de ON/PN/units.
2. Vínculos contábeis: o painel só associa DFP e ticker quando o demonstrativo e o cadastro correspondente já estavam públicos. Uma versão nova sem código de negociação não permite reaproveitar silenciosamente um cadastro antigo. Uma revisão sem valor também não ressuscita o valor anterior.
3. Bonificação Energisa: direito em 28/11/2025, entrega das novas ações em 02/12/2025. O motor reconhece o recebível sem permitir vender essas ações antes do crédito. Os dividendos anteriores mantêm a quantidade original de ações. Três eventos foram acrescentados à cópia, para ENGI3/4/11, com fonte identificada.
4. Erro encontrado pelo teste real: no cenário de preço adverso, o saldo de uma compra podia provocar uma venda posterior sem novo sinal. A compra agora usa o preço efetivo para dimensionar o orçamento. O caso possui teste de regressão.
5. Ordens arredondadas: no controle Ambev, compras e vendas usam múltiplos de 100 ações e preservam o dinheiro que sobra. Ordens de lote padrão que tentassem vender frações produzidas por evento corporativo passam a falhar explicitamente, pois exigiriam cotação de outro mercado.

## Resultado dos testes

- **463 testes automatizados aprovados**, em 140,05 segundos; cobertura de 86%.
- **36 cenários reais aprovados**: três eventos × dois capitais (R$5 mil/R$10 mil) × três preços (abertura seguinte, fechamento seguinte e adverso) × dois custos por lado (0,18%/0,36%). São hipóteses de custo para o teste, não tarifas cotadas da corretora.
- Casos fixados antes da execução: BBAS, 12–19/04/2024 (desdobramento); Energisa, 25/11–22/12/2025 (bonificação e dividendo); Ambev, 17/12/2025–22/06/2026 (pagamentos parcelados).
- A primeira execução identificou quatro falhas do caso Energisa/adverso. Após a correção comum de execução, a matriz inteira foi repetida. Os registros da falha e da repetição foram preservados.
- Conferência independente de quantidades, preços de execução, custos, caixa liquidado e valores ainda a receber. Maior diferença de reconciliação: aproximadamente R$0,000000000002.
- Ruff e Pyright configurado passaram. A wheel foi construída e verificada fora do checkout.
- Banco operacional, preços brutos, tabelas históricas, configurações congeladas e ledgers protegidos permaneceram intactos, conferidos por hashes.

Os controles BBAS/Energisa usam quantidades matemáticas fracionárias para verificar a contabilidade; o de Ambev usa lotes de 100. Não foram simulados impostos, execução específica de corretora ou o leilão das frações de bonificação. BBAS verifica apenas preço e desdobramento, sem caixa. As janelas foram escolhidas pelos eventos, não representam uma estratégia escolhida por fatores e não estimam lucro futuro. Os valores de patrimônio dos 36 casos constam do JSON apenas para reconciliar a contabilidade.

## O que ainda impede o backtest das estratégias

O painel foi conferido em 104 datas de 2018 a agosto de 2026 (última data disponível: 27/08). A mediana foi de 168,5 emissores com accruals calculável e cotação nessa data; isso mede disponibilidade, não qualidade final do universo nem poder independente. Não houve ranking seguido de cálculo de retornos de H17/H18/H19.

A cobertura de caixa certificada permanece em quatro tickers, representando apenas dois emissores. Faltam eventos completos de outros emissores, mudanças de capital e preços por classe, versões antigas ausentes dos arquivos correntes e o histórico completo de entradas, saídas e mudanças de código. As consultas B3 anteriores retornaram cadastro vazio para 13 emissores. Os links de download dos três documentos CVM testados retornaram erros do servidor; a consulta HTML permitiu recuperar o capital desses documentos, mas não completou todas as versões históricas.

**Decisão: INCONCLUSIVE_DATA_QUALITY para rentabilidade. H17–H19 continuam bloqueadas.** Não há ordem de investimento, compra de dados, alteração na conta de corretora ou indicação de que o capital de R$5–10 mil deva ser aplicado.

## Reprodução

O pacote inclui código completo, patch desde o complemento anterior, wheel, protocolo, banco de entrada e banco testado, fontes necessárias aos controles, resultados e manifesto de hashes. `tools/test_real_integration.py` exige destino novo e abre a origem somente para leitura. O comando exato desta execução foi:

```powershell
py -3.13 work/stocks-predictor/tools/test_real_integration.py --source-db work/stocks-history-2016-2026.db --output-db work/stocks-tested-real-v2-20260907.db --sources work/source-acquisition --report outputs/real-integration-results.json
```

Para repetir a partir do pacote, primeiro clonar o bundle local: `git clone outputs/stocks-testes-reais.bundle work/stocks-replay`. Executar então o script em `work/stocks-replay/tools/test_real_integration.py`, mantendo os argumentos de entrada e escolhendo saídas novas. Isso preserva a identidade Git sem acesso à rede; os arquivos exportados diretamente no ZIP não contêm `.git`.

Ambiente: Python 3.13, Core 3.2 disponibilizado no PYTHONPATH isolado. Não foi criada venv nem instalada dependência nova de runtime. Para repetir, usar nomes novos nos dois arquivos de saída. O banco de entrada é fixado por SHA-256 no protocolo. A reprodução dos 36 controles usa o comando acima; a suíte completa usa `py -3.13 -m pytest tests/ -q` a partir do checkout limpo, com as dependências de desenvolvimento já descritas no projeto.

## Fontes primárias

- [CVM — DFP e composição do capital](https://dados.cvm.gov.br/dataset/cia_aberta-doc-dfp).
- [CVM — documento Ambev 134335](https://www.rad.cvm.gov.br/ENET/frmGerenciaPaginaFRE.aspx?CodigoTipoInstituicao=1&NumeroSequencialDocumento=134335).
- [Energisa — ata de 19/11/2025, datas e termos da bonificação](https://api.mziq.com/mzfilemanager/v2/d/60f49a2d-bd8c-4fd9-95ab-bdf833097a83/c27daac3-4dc2-ff18-d469-6cd61cd1418f?origin=1).
- [Ambev — pagamentos de dividendos e JCP](https://ri.ambev.com.br/informacoes-aos-acionistas/dividendos-e-jcp/).
