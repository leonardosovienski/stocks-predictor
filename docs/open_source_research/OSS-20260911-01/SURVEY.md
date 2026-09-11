# Discovery e fichas técnicas

Duas ondas: (1) sementes quantitativas e fontes oficiais, (2) código focado, correção de identidades, validação/risco e referências negativas. Limite declarado: 65 candidatos, 20 aprofundamentos e 30 MB de fontes. Encerramento pelo orçamento desta rodada e carteira de decisões definida; **não foi demonstrada saturação**. Metadados GitHub começaram a retornar erros/indisponibilidade; UNKNOWN foi preservado, sem tentativa de contornar quotas. Algumas URLs tentadas estavam incorretas, e as correções estão em second_wave.json.

60 entradas de discovery, incluindo tentativas não confirmadas. As contagens verificáveis estão no registro; 15 fichas abaixo têm implementação relevante lida. Leitura de testes e issues foi seletiva, não uma auditoria integral de 15 repositórios. Nenhum código externo executado. README obtido é evidência C0, não C1. Tags de release e saúde de manutenção não foram verificadas em todos os candidatos.

## Triagem rastreável

| ID | Referência | Capacidade | Verificação | Licença observada | Decisão |
|---|---|---|---|---|---|
| R01 | [microsoft/qlib](https://github.com/microsoft/qlib) | ranking e pipeline | C1 | MIT | CANDIDATE |
| R02 | [QuantConnect/Lean](https://github.com/QuantConnect/Lean) | eventos e execução | C1 | Apache-2.0 | CANDIDATE |
| R03 | [polakowo/vectorbt](https://github.com/polakowo/vectorbt) | teste diferencial vetorizado | C1 | Apache-2.0 + Commons Clause; arquivo LICENSE.md examinado | CANDIDATE |
| R04 | [mementum/backtrader](https://github.com/mementum/backtrader) | simulação por eventos | C0 | GPL-3.0 | DEFER |
| R05 | [stefan-jansen/zipline-reloaded](https://github.com/stefan-jansen/zipline-reloaded) | ajustes e calendário | C1 | Apache-2.0 | CANDIDATE |
| R06 | [nautechsystems/nautilus_trader](https://github.com/nautechsystems/nautilus_trader) | execução e precisão | C0 | LGPL-3.0 | DEFER |
| R07 | [robertmartin8/PyPortfolioOpt](https://github.com/robertmartin8/PyPortfolioOpt) | covariância e HRP | C2 | MIT | CANDIDATE |
| R08 | [dcajasn/Riskfolio-Lib](https://github.com/dcajasn/Riskfolio-Lib) | CVaR e carteira | C1 | BSD-3-Clause | CANDIDATE |
| R09 | [bashtage/arch](https://github.com/bashtage/arch) | bootstrap e SPA | C2 | NOASSERTION | CANDIDATE |
| R10 | [statsmodels/statsmodels](https://github.com/statsmodels/statsmodels) | ARIMA VAR Kalman | C1 | BSD-3-Clause | CANDIDATE |
| R11 | [scikit-learn/scikit-learn](https://github.com/scikit-learn/scikit-learn) | linear RF ExtraTrees PCA | C1 | BSD-3-Clause | CANDIDATE |
| R12 | [microsoft/LightGBM](https://github.com/microsoft/LightGBM) | LambdaRank e boosting | C2 | UNKNOWN | CANDIDATE |
| R13 | [dmlc/xgboost](https://github.com/dmlc/xgboost) | ranking e boosting | C0 | Apache-2.0 | DEFER |
| R14 | [catboost/catboost](https://github.com/catboost/catboost) | categorias e boosting | C0 | Apache-2.0 | DEFER |
| R15 | [quantopian/alphalens](https://github.com/quantopian/alphalens) | rank IC quantis e turnover | IDENTIDADE NÃO CONFIRMADA | UNKNOWN | REJECT |
| R16 | [stefan-jansen/alphalens-reloaded](https://github.com/stefan-jansen/alphalens-reloaded) | sucessor Alphalens | C1 | UNKNOWN | CANDIDATE |
| R17 | [skfolio/skfolio](https://github.com/skfolio/skfolio) | CV carteira e risco | C0 | UNKNOWN | DEFER |
| R18 | [gerrymanoim/exchange_calendars](https://github.com/gerrymanoim/exchange_calendars) | calendário B3 | C0 | UNKNOWN | DEFER |
| R19 | [rsheftel/pandas_market_calendars](https://github.com/rsheftel/pandas_market_calendars) | calendários | C0 | UNKNOWN | DEFER |
| R20 | [wilsonfreitas/python-bcb](https://github.com/wilsonfreitas/python-bcb) | BCB SGS | C1 | UNKNOWN | CANDIDATE |
| R21 | [wilsonfreitas/brasa](https://github.com/wilsonfreitas/brasa) | B3 e renda fixa | C0 | UNKNOWN | DEFER |
| R22 | [msperlin/GetDFPData2](https://github.com/msperlin/GetDFPData2) | CVM DFP | C0 | UNKNOWN | DEFER |
| R23 | [msperlin/GetFREData](https://github.com/msperlin/GetFREData) | CVM FRE | C0 | UNKNOWN | DEFER |
| R24 | [gustavomoers/FinancialData](https://github.com/gustavomoers/FinancialData) | COTAHIST | IDENTIDADE NÃO CONFIRMADA | UNKNOWN | REJECT |
| R25 | [alvarobartt/tribuo](https://github.com/alvarobartt/tribuo) | CVM | IDENTIDADE NÃO CONFIRMADA | UNKNOWN | REJECT |
| R26 | [jmaranhao/pycvm](https://github.com/jmaranhao/pycvm) | CVM | IDENTIDADE NÃO CONFIRMADA | UNKNOWN | REJECT |
| R27 | [Nixtla/statsforecast](https://github.com/Nixtla/statsforecast) | ARIMA e baselines | C0 | UNKNOWN | DEFER |
| R28 | [Nixtla/neuralforecast](https://github.com/Nixtla/neuralforecast) | NBEATS NHITS TFT PatchTST | C0 | UNKNOWN | DEFER |
| R29 | [unit8co/darts](https://github.com/unit8co/darts) | TCN RNN e previsão probabilística | C0 | UNKNOWN | DEFER |
| R30 | [sktime/sktime](https://github.com/sktime/sktime) | validação de séries | C0 | UNKNOWN | DEFER |
| R31 | [timeseriesAI/tsai](https://github.com/timeseriesAI/tsai) | redes temporais | C0 | UNKNOWN | DEFER |
| R32 | [hmmlearn/hmmlearn](https://github.com/hmmlearn/hmmlearn) | HMM | C1 | UNKNOWN | CANDIDATE |
| R33 | [deepcharles/ruptures](https://github.com/deepcharles/ruptures) | change points | C1 | UNKNOWN | CANDIDATE |
| R34 | [scikit-learn-contrib/hdbscan](https://github.com/scikit-learn-contrib/hdbscan) | clustering | C0 | UNKNOWN | DEFER |
| R35 | [scikit-learn-contrib/MAPIE](https://github.com/scikit-learn-contrib/MAPIE) | conformal | C1 | UNKNOWN | CANDIDATE |
| R36 | [SeldonIO/alibi-detect](https://github.com/SeldonIO/alibi-detect) | drift | C0 | UNKNOWN | DEFER |
| R37 | [shap/shap](https://github.com/shap/shap) | explicabilidade | C0 | UNKNOWN | DEFER |
| R38 | [optuna/optuna](https://github.com/optuna/optuna) | tuning rastreável | C0 | UNKNOWN | DEFER |
| R39 | [mlflow/mlflow](https://github.com/mlflow/mlflow) | tracking | C0 | UNKNOWN | DEFER |
| R40 | [iterative/dvc](https://github.com/iterative/dvc) | versionamento de dados | C0 | UNKNOWN | DEFER |
| R41 | [unionai-oss/pandera](https://github.com/unionai-oss/pandera) | contratos | C0 | UNKNOWN | DEFER |
| R42 | [great-expectations/great_expectations](https://github.com/great-expectations/great_expectations) | validação | C0 | UNKNOWN | DEFER |
| R43 | [Hudson-and-Thames/mlfinlab](https://github.com/Hudson-and-Thames/mlfinlab) | purga e multiplicidade | C0 | UNKNOWN | DEFER |
| R44 | [AI4Finance-Foundation/FinRL](https://github.com/AI4Finance-Foundation/FinRL) | reinforcement learning | C0 | UNKNOWN | DEFER |
| R45 | [AI4Finance-Foundation/FinRL-Meta](https://github.com/AI4Finance-Foundation/FinRL-Meta) | ambientes RL | C0 | UNKNOWN | DEFER |
| R46 | [AI4Finance-Foundation/FinGPT](https://github.com/AI4Finance-Foundation/FinGPT) | LLM financeiro | C0 | UNKNOWN | DEFER |
| R47 | [stefan-jansen/empyrical-reloaded](https://github.com/stefan-jansen/empyrical-reloaded) | métricas | C0 | UNKNOWN | DEFER |
| R48 | [quantopian/pyfolio](https://github.com/quantopian/pyfolio) | atribuição | C0 | UNKNOWN | DEFER |
| R49 | [pmorissette/bt](https://github.com/pmorissette/bt) | alocação | C0 | UNKNOWN | DEFER |
| R50 | [kernc/backtesting.py](https://github.com/kernc/backtesting.py) | referência simples | C0 | UNKNOWN | DEFER |
| R51 | [CVM DFP](https://dados.cvm.gov.br/dataset/cia_aberta-doc-dfp) | DFP versionadas e recebimento; atualizações semanais por reapresentação. | C0 | ODbL declarada no catálogo | CANDIDATE |
| R52 | [CVM FRE](https://dados.cvm.gov.br/dataset/cia_aberta-doc-fre) | Capital e informações corporativas; validade da base de ações precisa de documento. | C0 | Ver catálogo e direitos do documento específico | CANDIDATE |
| R53 | [CVM FCA](https://dados.cvm.gov.br/dataset/cia_aberta-doc-fca) | Vínculos históricos de emissor e papel; preservar versão cadastral. | C0 | Ver catálogo e documento específico | CANDIDATE |
| R54 | [B3 COTAHIST](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/series-historicas/) | Fonte oficial para preços; ajustes econômicos requerem evidência separada. | C0 | Termos de dados/redistribuição não certificados | CANDIDATE |
| R55 | [BCB SGS](https://www.bcb.gov.br/gestao_site/webservices.asp?frame=1) | Acesso a séries macro; API histórica não prova vintage observado. | C0 | Termos por série não certificados | CANDIDATE |
| R56 | [NEFIN fatores](https://nefin.com.br/data/risk-factors/) | Controle de exposição a fatores brasileiros; metodologia e página examinadas. | C0 | Acesso público; redistribuição não certificada | CANDIDATE |
| R57 | [Deflated Sharpe Ratio](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf) | Ajuste por seleção e não normalidade exige denominador de tentativas e suas dependências. | C0 | Artigo; não é licença de software | CANDIDATE |
| R58 | [Probability of Backtest Overfitting](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf) | CSCV diagnostica seleção entre alternativas; não produz holdout prospectivo. | C0 | Artigo; não é licença de software | CANDIDATE |
| R59 | [AQR Fact Fiction Factor Investing](https://www.aqr.com/insights/research/journal-article/fact-fiction-and-factor-investing) | Referência econômica contextual; carteiras ilustrativas não certificam custos pessoais B3. | C0 | Termos do editor, sem redistribuição do artigo | CANDIDATE |
| R60 | [CVM ITR](https://dados.cvm.gov.br/dataset/cia_aberta-doc-itr) | Fundamentos trimestrais com reapresentações; separar acumulado e trimestre isolado. | C0 | ODbL declarada no catálogo | CANDIDATE |

## Aprofundamento por alegação

### R01 — microsoft/qlib

Commit `79633dd9506ea689e5400dea0197717b5b3d74b7`. [Trecho qlib/data/dataset/processor.py:228–259](https://github.com/microsoft/qlib/blob/79633dd9506ea689e5400dea0197717b5b3d74b7/qlib/data/dataset/processor.py#L228). **C1 / E1 / EXTERNAL / ENGINEERING / NOT_EVALUATED**.

ZScoreNorm calcula média/desvio no intervalo explícito de fit e aplica fora dele. O caller pode fornecer fim de treino inválido; adaptar por fold e por data. Não importa dados B3 automaticamente.

Testes: Não examinados, salvo ficha explícita. Reuso sugerido: referência parcial ou adapter isolado, após gate da capacidade. Dados próprios B3 e equivalência econômica não verificados.

### R02 — QuantConnect/Lean

Commit `8ee075a39918f2df6fe9e0a5944e366fb60d10dc`. [Trecho Common/Orders/Fills/EquityFillModel.cs:124–175](https://github.com/QuantConnect/Lean/blob/8ee075a39918f2df6fe9e0a5944e366fb60d10dc/Common/Orders/Fills/EquityFillModel.cs#L124). **C1 / E1 / EXTERNAL / ENGINEERING / NOT_EVALUATED**.

MarketFill verifica abertura do mercado e escolhe ask/bid com slippage conforme direção. Barras e relógios próprios; suporte genérico a equities não demonstra calendário, custos ou eventos B3.

Testes: Não examinados, salvo ficha explícita. Reuso sugerido: referência parcial ou adapter isolado, após gate da capacidade. Dados próprios B3 e equivalência econômica não verificados.

### R03 — polakowo/vectorbt

Commit `34b6d5935e3ea3eccd549e2592bc0f455b8045f5`. [Trecho vectorbt/portfolio/nb.py:72–156](https://github.com/polakowo/vectorbt/blob/34b6d5935e3ea3eccd549e2592bc0f455b8045f5/vectorbt/portfolio/nb.py#L72). **C1 / E1 / EXTERNAL / ENGINEERING / NOT_EVALUATED**.

buy_nb explicita caixa, fees, slippage e granularidade de quantidade. Mudam as convenções de ordem e tamanho; Commons Clause exige avaliação do uso. Não é oráculo de eventos brasileiros.

Testes: Não examinados, salvo ficha explícita. Reuso sugerido: referência parcial ou adapter isolado, após gate da capacidade. Dados próprios B3 e equivalência econômica não verificados.

### R05 — stefan-jansen/zipline-reloaded

Commit `943010b9da848e317fc520de87edade2b884d329`. [Trecho src/zipline/data/adjustments.py:458–539](https://github.com/stefan-jansen/zipline-reloaded/blob/943010b9da848e317fc520de87edade2b884d329/src/zipline/data/adjustments.py#L458). **C1 / E1 / EXTERNAL / ENGINEERING / NOT_EVALUATED**.

Razão de ajuste de dividendo usa fechamento anterior à ex-data e exclui razão inválida. Ajustar sinal e creditar recebível são contratos diferentes; evitar dividendos duplicados no PnL.

Testes: Não examinados, salvo ficha explícita. Reuso sugerido: referência parcial ou adapter isolado, após gate da capacidade. Dados próprios B3 e equivalência econômica não verificados.

### R07 — robertmartin8/PyPortfolioOpt

Commit `a6638d2e06dae6f444fd022cfd4b3c528902a85b`. [Trecho pypfopt/risk_models.py:509–543](https://github.com/robertmartin8/PyPortfolioOpt/blob/a6638d2e06dae6f444fd022cfd4b3c528902a85b/pypfopt/risk_models.py#L509). **C2 / E1 / EXTERNAL / ENGINEERING / NOT_EVALUATED**.

Ledoit-Wolf constant_variance chama sklearn; testes verificam forma, identificadores e PSD. Não é linhagem independente de sklearn. nan_to_num exige política explícita para faltantes. PSD não prova alocação superior.

Testes: Asserções pertinentes inspecionadas; NÃO executadas por nós.. Reuso sugerido: referência parcial ou adapter isolado, após gate da capacidade. Dados próprios B3 e equivalência econômica não verificados.

### R08 — dcajasn/Riskfolio-Lib

Commit `632a9e48fbaf2b9f8e83864a492332364b6ed32c`. [Trecho riskfolio/src/RiskFunctions.py:356–398](https://github.com/dcajasn/Riskfolio-Lib/blob/632a9e48fbaf2b9f8e83864a492332364b6ed32c/riskfolio/src/RiskFunctions.py#L356). **C1 / E1 / EXTERNAL / ENGINEERING / NOT_EVALUATED**.

CVaR_Hist ordena retornos e calcula perda média de cauda com convenção de quantil. Pouca cauda e dados dependentes limitam estimativa. Alpha e sinal de perda precisam casar no teste diferencial.

Testes: Não examinados, salvo ficha explícita. Reuso sugerido: referência parcial ou adapter isolado, após gate da capacidade. Dados próprios B3 e equivalência econômica não verificados.

### R09 — bashtage/arch

Commit `704bb70e48372e3ccccdde7da379811657ad0224`. [Trecho arch/bootstrap/base.py:1586–1606](https://github.com/bashtage/arch/blob/704bb70e48372e3ccccdde7da379811657ad0224/arch/bootstrap/base.py#L1586). **C2 / E1 / EXTERNAL / ENGINEERING / NOT_EVALUATED**.

StationaryBootstrap usa p=1/bloco e delega amostragem; teste compara implementações Python/Numba/Cython. As três implementações compartilham desenho; comparação numérica não é independência econômica nem teste de cobertura B3.

Testes: Asserções pertinentes inspecionadas; NÃO executadas por nós.. Reuso sugerido: referência parcial ou adapter isolado, após gate da capacidade. Dados próprios B3 e equivalência econômica não verificados.

### R10 — statsmodels/statsmodels

Commit `1d2307006379fd78ed4f921a92d7fe8c069565f7`. [Trecho statsmodels/tsa/statespace/kalman_filter.py:857–914](https://github.com/statsmodels/statsmodels/blob/1d2307006379fd78ed4f921a92d7fe8c069565f7/statsmodels/tsa/statespace/kalman_filter.py#L857). **C1 / E1 / EXTERNAL / ENGINEERING / NOT_EVALUATED**.

filter executa filtro de Kalman e por padrão não conserva dados necessários ao smoothing. Parâmetros estimados com futuro ainda vazam mesmo usando filter; estimar em janela causal.

Testes: Não examinados, salvo ficha explícita. Reuso sugerido: referência parcial ou adapter isolado, após gate da capacidade. Dados próprios B3 e equivalência econômica não verificados.

### R11 — scikit-learn/scikit-learn

Commit `8c54c136cac4982a0dac7bee8b8fbcada411fe10`. [Trecho sklearn/model_selection/_split.py:1314–1327](https://github.com/scikit-learn/scikit-learn/blob/8c54c136cac4982a0dac7bee8b8fbcada411fe10/sklearn/model_selection/_split.py#L1314). **C1 / E1 / EXTERNAL / ENGINEERING / NOT_EVALUATED**.

TimeSeriesSplit subtrai gap da posição de início de teste e corta índices. Gap é contagem de amostras; painel irregular exige agrupar datas e purgar intervalos reais de labels.

Testes: Não examinados, salvo ficha explícita. Reuso sugerido: referência parcial ou adapter isolado, após gate da capacidade. Dados próprios B3 e equivalência econômica não verificados.

### R12 — microsoft/LightGBM

Commit `7d3d1d829981fc670629f63f00e11ce25d6624f5`. [Trecho src/objective/rank_objective.hpp:74–148](https://github.com/microsoft/LightGBM/blob/7d3d1d829981fc670629f63f00e11ce25d6624f5/src/objective/rank_objective.hpp#L74). **C2 / E1 / EXTERNAL / ENGINEERING / NOT_EVALUATED**.

Objetivo calcula gradientes por query e há classe LambdaRank/NDCG; teste usa grupos de ranking. Query deve representar data; relevância discreta exige contrato. Teste de ranking inspecionado não é resultado financeiro.

Testes: Asserções pertinentes inspecionadas; NÃO executadas por nós.. Reuso sugerido: referência parcial ou adapter isolado, após gate da capacidade. Dados próprios B3 e equivalência econômica não verificados.

### R16 — stefan-jansen/alphalens-reloaded

Commit `f0a07c22d554e4b4036983cc80320b432714fe7e`. [Trecho src/alphalens/performance.py:28–77](https://github.com/stefan-jansen/alphalens-reloaded/blob/f0a07c22d554e4b4036983cc80320b432714fe7e/src/alphalens/performance.py#L28). **C1 / E1 / EXTERNAL / ENGINEERING / NOT_EVALUATED**.

IC é Spearman por data; opção remove média de retornos por grupo. Requer labels admissíveis e perdas amostrais explícitas. Em utils.py:227–318, filter_zscore usa média/desvio dos retornos futuros e pode introduzir lookahead se ativado; o default observado é None. Manter desativado em evidência causal.

Testes: Não examinados, salvo ficha explícita. Reuso sugerido: referência parcial ou adapter isolado, após gate da capacidade. Dados próprios B3 e equivalência econômica não verificados.

### R20 — wilsonfreitas/python-bcb

Commit `c431f1dd4c5321658d7879f9ef825df427bdd3fb`. [Trecho bcb/sgs/__init__.py:380–408](https://github.com/wilsonfreitas/python-bcb/blob/c431f1dd4c5321658d7879f9ef825df427bdd3fb/bcb/sgs/__init__.py#L380). **C1 / E1 / EXTERNAL / ENGINEERING / NOT_EVALUATED**.

get obtém JSON de cada série e concatena DataFrames; suporta retorno de texto original. Não há contrato de vintage nesse caminho; salvar resposta, horário e definição da série separadamente.

Testes: Não examinados, salvo ficha explícita. Reuso sugerido: referência parcial ou adapter isolado, após gate da capacidade. Dados próprios B3 e equivalência econômica não verificados.

### R32 — hmmlearn/hmmlearn

Commit `e01a10e99df1042e4c1e6b7c822fd292dd37502f`. [Trecho src/hmmlearn/base.py:294–318](https://github.com/hmmlearn/hmmlearn/blob/e01a10e99df1042e4c1e6b7c822fd292dd37502f/src/hmmlearn/base.py#L294). **C1 / E1 / EXTERNAL / ENGINEERING / NOT_EVALUATED**.

decode map usa posteriors de score_samples; documentação especifica smoothing com todas as emissões. Decodificar toda a história e usar estados como sinal passado introduz futuro; diagnóstico ex post é outro uso.

Testes: Não examinados, salvo ficha explícita. Reuso sugerido: referência parcial ou adapter isolado, após gate da capacidade. Dados próprios B3 e equivalência econômica não verificados.

### R33 — deepcharles/ruptures

Commit `ee1c8ff8a548d54c641b2bb471562165931f31c7`. [Trecho src/ruptures/detection/pelt.py:50–124](https://github.com/deepcharles/ruptures/blob/ee1c8ff8a548d54c641b2bb471562165931f31c7/src/ruptures/detection/pelt.py#L50). **C1 / E1 / EXTERNAL / ENGINEERING / NOT_EVALUATED**.

PELT calcula partição de custo mínimo até n_samples sobre o sinal recebido. Segmentação é offline; não usar quebras finais como alertas históricos sem replay em prefixos.

Testes: Não examinados, salvo ficha explícita. Reuso sugerido: referência parcial ou adapter isolado, após gate da capacidade. Dados próprios B3 e equivalência econômica não verificados.

### R35 — scikit-learn-contrib/MAPIE

Commit `7e888f5249bf942912207d398525d3259a5f07c0`. [Trecho mapie/regression/time_series_regression.py:296–330](https://github.com/scikit-learn-contrib/MAPIE/blob/7e888f5249bf942912207d398525d3259a5f07c0/mapie/regression/time_series_regression.py#L296). **C1 / E1 / EXTERNAL / ENGINEERING / NOT_EVALUATED**.

ACI atualiza alpha_t conforme erro de cobertura observado e gamma. Só atualizar após maturação do label; cobertura marginal não garante cobertura condicional por regime nem lucro.

Testes: Não examinados, salvo ficha explícita. Reuso sugerido: referência parcial ou adapter isolado, após gate da capacidade. Dados próprios B3 e equivalência econômica não verificados.

## Críticas, linhagem e manutenção

- vectorbt: licença lida inclui Commons Clause. Sua condição adicional impede tratá-lo simplesmente como Apache permissiva. Referência para pesquisa não equivale a aprovação de distribuição comercial.
- mlfinlab: README diz que o repositório serve a bugs/feature requests; alegação comercial de testes não recebe C2. Acesso pago não presumido.
- PyPortfolioOpt usa sklearn no caminho Ledoit-Wolf padrão: os dois não são votos independentes para essa implementação. Alphalens e sucessor compartilham linhagem; FinRL/Meta/FinGPT compartilham ecossistema.
- [PR542 exchange_calendars](https://github.com/gerrymanoim/exchange_calendars/pull/542) corrige tipos de timezone com pandas 3.0; release 4.13.1 aponta a correção. Calendário e versão pandas precisam ser fixados juntos. Fixtures BVMF examinadas incluem Carnaval, Quarta-feira de Cinzas e exceções; as asserções da classe base não foram lidas, portanto fixtures encontradas não recebem C2.
- HMM e PELT: implementações examinadas usam a sequência informada; interpretação retrospectiva não é estado disponível em tempo real. Isso é limite de uso, não defeito da biblioteca.
- DSR: seções do paper sobre seleção, não normalidade e número efetivo de trials examinadas. Não tratar probabilidade derivada como probabilidade de lucro pessoal. PBO/CSCV: método e limitações examinados; mesmas amostras não criam validação prospectiva. Nenhum dos dois corrige dado vazado.
- Referência AQR usada apenas como contexto sobre fatores; estratégias ilustrativas e amostras estrangeiras não certificam implementação B3. Não foi feita replicação externa independente pertinente nesta rodada: E4 não atribuído.

## Fontes e acessibilidade

ODbL foi observada nos catálogos DFP/ITR; não é autorização universal para PDFs individuais. A CVM informa reapresentações semanais. Download atual não comprova vintage; o contrato deve manter competência, publicação/recebimento, processamento, ingestão e revisão separadamente. APIs SGS e wrappers não certificam vintages. NEFIN é candidato a controle de fatores, não carteira pessoal investível.

DATA_ACCESSIBILITY e DATA_PIT_QUALITY permanecem UNKNOWN para o dataset econômico da proposta. Páginas públicas acessíveis não justificam nota 5 para cobertura, temporalidade ou direito de redistribuição. Nenhuma compra/assinatura ou quota paga foi consumida por iniciativa nossa. Instrumentos adicionais entram apenas como benchmark/informação; B3 continua mercado-alvo.
