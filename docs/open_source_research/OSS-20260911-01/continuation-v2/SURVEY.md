# Pesquisa externa — complemento v2

A [triagem inicial e fichas de código](../SURVEY.md) e seus hashes permanecem válidos para os commits fixados. Há60 entradas,56 identidades confirmadas; não60 soluções aprovadas. Esta revisão acrescenta testes, releases e problemas materiais em15 referências.13 têm asserções selecionadas inspecionadas; R08/R20 permanecem C1. Uma release observada pode ser diferente do commit de código auditado; não os equiparar. Nenhum pacote externo executado.

## R01 — microsoft/qlib

Código `79633dd9506ea689e5400dea0197717b5b3d74b7`; licença: MIT. [Releases](https://github.com/microsoft/qlib/releases): v0.9.7. Verificação máxima desta alegação: **C2**, EXTERNAL/ENGINEERING; resultado econômico NOT_EVALUATED.

Teste: `tests/data_mid_layer_tests/test_processor.py:34-56`. ZScoreNorm comparado à fórmula sobre fixture; não testa sozinho resistência a futuro.

[Issue/PR/discussão material](https://github.com/microsoft/qlib/issues/2252): Relato aberto sobre CWD e FileLock do workflow; evitar acoplamento ao tracking antes de teste de isolamento.

Decisão: referência de contrato/diagnóstico; versões, licença e dependências fixadas antes de qualquer execução. Dados B3 e causalidade continuam responsabilidade local.

## R02 — QuantConnect/Lean

Código `8ee075a39918f2df6fe9e0a5944e366fb60d10dc`; licença: Apache-2.0. [Releases](https://github.com/QuantConnect/Lean/releases): v2.4.0.1 no painel de releases; não é versão do HEAD auditado. Verificação máxima desta alegação: **C2**, EXTERNAL/ENGINEERING; resultado econômico NOT_EVALUATED.

Teste: `Tests/Common/Orders/Fills/EquityFillModelTests.cs:48-89`. Asserções de quantidade, ask/close, status e mensagem; fixture rejeita dado sem assinatura de mercado.

[Issue/PR/discussão material](https://github.com/QuantConnect/Lean/issues/2762): Relato histórico de fills stale encerrado; o teste atual explicitamente mudou para esperar dado novo. Não transportar bug antigo ao HEAD.

Decisão: referência de contrato/diagnóstico; versões, licença e dependências fixadas antes de qualquer execução. Dados B3 e causalidade continuam responsabilidade local.

## R03 — polakowo/vectorbt

Código `34b6d5935e3ea3eccd549e2592bc0f455b8045f5`; licença: Apache-2.0 + Commons Clause; arquivo LICENSE.md examinado. [Releases](https://github.com/polakowo/vectorbt/releases): v1.1.0. Verificação máxima desta alegação: **C2**, EXTERNAL/ENGINEERING; resultado econômico NOT_EVALUATED.

Teste: `tests/test_portfolio.py:974-1003`. Records de taxas comparados a números explícitos. O contrato de chamada/caixa continua importante.

[Issue/PR/discussão material](https://github.com/polakowo/vectorbt/issues/290): Discussão sobre indicadores que repintam e streaming; preço fornecido pelo usuário não é certificado pela engine.

Decisão: referência de contrato/diagnóstico; versões, licença e dependências fixadas antes de qualquer execução. Dados B3 e causalidade continuam responsabilidade local.

## R05 — stefan-jansen/zipline-reloaded

Código `943010b9da848e317fc520de87edade2b884d329`; licença: Apache-2.0. [Releases](https://github.com/stefan-jansen/zipline-reloaded/releases): 3.1.1. Verificação máxima desta alegação: **C2**, EXTERNAL/ENGINEERING; resultado econômico NOT_EVALUATED.

Teste: `tests/data/test_adjustments.py:86-198`. Ratios 0.95/0.90 e descarte de ratio não positivo/NaN têm assert. A asserção de payout usa o próprio resultado como esperado e não é oráculo independente de datas.

[Issue/PR/discussão material](https://github.com/stefan-jansen/zipline-reloaded/pull/264): PR NumPy2 incorporado; release3.1.1 declara Python3.13, não prova compatibilidade3.14 do nosso runner.

Decisão: referência de contrato/diagnóstico; versões, licença e dependências fixadas antes de qualquer execução. Dados B3 e causalidade continuam responsabilidade local.

## R07 — robertmartin8/PyPortfolioOpt

Código `a6638d2e06dae6f444fd022cfd4b3c528902a85b`; licença: MIT. [Releases](https://github.com/robertmartin8/PyPortfolioOpt/releases): v1.6.0; URL agora PyPortfolio/PyPortfolioOpt. Verificação máxima desta alegação: **C2**, EXTERNAL/ENGINEERING; resultado econômico NOT_EVALUATED.

Teste: `tests/test_risk_models.py:258-298`. PSD/formato e shrinkage; sklearn é dependência, não confirmação independente.

[Issue/PR/discussão material](https://github.com/robertmartin8/PyPortfolioOpt/issues/737): Relato aberto em CLA sobre covariância singular; PSD não implica invertibilidade. Não é falha demonstrada no LedoitWolf inspecionado.

Decisão: referência de contrato/diagnóstico; versões, licença e dependências fixadas antes de qualquer execução. Dados B3 e causalidade continuam responsabilidade local.

## R08 — dcajasn/Riskfolio-Lib

Código `632a9e48fbaf2b9f8e83864a492332364b6ed32c`; licença: BSD-3-Clause. [Releases](https://github.com/dcajasn/Riskfolio-Lib/releases): Sem GitHub Releases publicados na página consultada. Verificação máxima desta alegação: **C1**, EXTERNAL/ENGINEERING; resultado econômico NOT_EVALUATED.

Teste: `tests/test_RiskFunctions.py: caminho 404`. CVaR_Hist lido; nenhuma asserção pertinente localizada nesta busca. Não declarar pacote sem testes.

[Issue/PR/discussão material](https://github.com/dcajasn/Riskfolio-Lib/discussions/42): Mantenedor distingue problema inviável de solver incompatível. Exemplo usa MOSEK; não assumir acesso ou custo zero.

Decisão: referência de contrato/diagnóstico; versões, licença e dependências fixadas antes de qualquer execução. Dados B3 e causalidade continuam responsabilidade local.

## R09 — bashtage/arch

Código `704bb70e48372e3ccccdde7da379811657ad0224`; licença: NOASSERTION. [Releases](https://github.com/bashtage/arch/releases): v8.0.0. Verificação máxima desta alegação: **C2**, EXTERNAL/ENGINEERING; resultado econômico NOT_EVALUATED.

Teste: `arch/tests/bootstrap/test_bootstrap.py:714-730`. Compara variantes do sampler; não prova cobertura inferencial.

[Issue/PR/discussão material](https://github.com/bashtage/arch/issues/801): Relato aberto: jackknife IID em BCa de blocos e comprimento interno do studentized. Escolher percentile fixo para primeiro benchmark e medir cobertura, não presumir BCa superior.

Decisão: referência de contrato/diagnóstico; versões, licença e dependências fixadas antes de qualquer execução. Dados B3 e causalidade continuam responsabilidade local.

## R10 — statsmodels/statsmodels

Código `1d2307006379fd78ed4f921a92d7fe8c069565f7`; licença: BSD-3-Clause. [Releases](https://github.com/statsmodels/statsmodels/releases): 0.15.0. Verificação máxima desta alegação: **C2**, EXTERNAL/ENGINEERING; resultado econômico NOT_EVALUATED.

Teste: `statsmodels/tsa/statespace/tests/test_kalman.py:134-208`. Estados filtrados e likelihood contra resultados de referência; convenção de inicialização reconciliada.

[Issue/PR/discussão material](https://github.com/statsmodels/statsmodels/issues/2768): Pedido histórico encerrado sobre missing no smoother puro. Diferenciar filtro causal de smoother; não apresentar limitação de2016 como bug vigente.

Decisão: referência de contrato/diagnóstico; versões, licença e dependências fixadas antes de qualquer execução. Dados B3 e causalidade continuam responsabilidade local.

## R11 — scikit-learn/scikit-learn

Código `8c54c136cac4982a0dac7bee8b8fbcada411fe10`; licença: BSD-3-Clause. [Releases](https://github.com/scikit-learn/scikit-learn/releases): 1.9.0 na página de releases; documentação stable consultada exibia1.9.1. Verificação máxima desta alegação: **C2**, EXTERNAL/ENGINEERING; resultado econômico NOT_EVALUATED.

Teste: `sklearn/model_selection/tests/test_split.py:1869-1923`. Índices esperados exatos para gap=2; demonstra exclusão de linhas, não purga de labels sobrepostos por intervalo.

[Issue/PR/discussão material](https://github.com/scikit-learn/scikit-learn/issues/24243): Pedido aberto de skip entre splits ilustra distinção entre espaçamento e gap; não é bug do splitter.

Decisão: referência de contrato/diagnóstico; versões, licença e dependências fixadas antes de qualquer execução. Dados B3 e causalidade continuam responsabilidade local.

## R12 — microsoft/LightGBM

Código `7d3d1d829981fc670629f63f00e11ce25d6624f5`; licença: UNKNOWN. [Releases](https://github.com/microsoft/LightGBM/releases): v4.7.0; URL agora lightgbm-org/LightGBM. Verificação máxima desta alegação: **C2**, EXTERNAL/ENGINEERING; resultado econômico NOT_EVALUATED.

Teste: `tests/python_package_test/test_engine.py:697`. Teste de ranking/early stop examinado junto de query groups do objetivo; sem resultado B3.

[Issue/PR/discussão material](https://github.com/microsoft/LightGBM/issues/5283): Issue fechada sobre group sem corpo acessível; evidência fraca, não usada como diagnóstico. Contrato de grupos vem do código/documentação.

Decisão: referência de contrato/diagnóstico; versões, licença e dependências fixadas antes de qualquer execução. Dados B3 e causalidade continuam responsabilidade local.

## R16 — stefan-jansen/alphalens-reloaded

Código `f0a07c22d554e4b4036983cc80320b432714fe7e`; licença: UNKNOWN. [Releases](https://github.com/stefan-jansen/alphalens-reloaded/releases): v0.4.5. Verificação máxima desta alegação: **C2**, EXTERNAL/ENGINEERING; resultado econômico NOT_EVALUATED.

Teste: `tests/test_performance.py:74-140`. IC esperado ±1 e ajuste por grupo; testes não demonstram causalidade automática dos labels.

[Issue/PR/discussão material](https://github.com/stefan-jansen/alphalens-reloaded/issues/21): Relato aberto sobre normalização de spread long-short/gross exposure; comparar mesma base de capital antes de reportar ganho.

Decisão: referência de contrato/diagnóstico; versões, licença e dependências fixadas antes de qualquer execução. Dados B3 e causalidade continuam responsabilidade local.

## R20 — wilsonfreitas/python-bcb

Código `c431f1dd4c5321658d7879f9ef825df427bdd3fb`; licença: UNKNOWN. [Releases](https://github.com/wilsonfreitas/python-bcb/releases): v0.4.0. Verificação máxima desta alegação: **C1**, EXTERNAL/ENGINEERING; resultado econômico NOT_EVALUATED.

Teste: `tests/test_sgs.py: caminho 404`. SGS JSON/concat lido; nenhum teste de vintage localizado.

[Issue/PR/discussão material](https://github.com/wilsonfreitas/python-bcb/issues/66): Mantenedor registra mudanças IFData2000-2024/2025+ como investigação aberta. Não extrapolar a SGS; contrato por série é necessário.

Decisão: referência de contrato/diagnóstico; versões, licença e dependências fixadas antes de qualquer execução. Dados B3 e causalidade continuam responsabilidade local.

## R32 — hmmlearn/hmmlearn

Código `e01a10e99df1042e4c1e6b7c822fd292dd37502f`; licença: UNKNOWN. [Releases](https://github.com/hmmlearn/hmmlearn/releases): Sem GitHub Releases publicados na página consultada. Verificação máxima desta alegação: **C2**, EXTERNAL/ENGINEERING; resultado econômico NOT_EVALUATED.

Teste: `src/hmmlearn/tests/test_base.py:62-167`. Forward/backward/Viterbi e posteriors contra exemplo numérico; confirma diferença de objetos, não causalidade de predict na série completa.

[Issue/PR/discussão material](https://github.com/hmmlearn/hmmlearn/issues/540): Relato aberto sobre estados que usam futuro; coerente com implementação e teste. Rejeitar uso retrospectivo suavizado como sinal causal.

Decisão: referência de contrato/diagnóstico; versões, licença e dependências fixadas antes de qualquer execução. Dados B3 e causalidade continuam responsabilidade local.

## R33 — deepcharles/ruptures

Código `ee1c8ff8a548d54c641b2bb471562165931f31c7`; licença: UNKNOWN. [Releases](https://github.com/deepcharles/ruptures/releases): v1.1.10. Verificação máxima desta alegação: **C2**, EXTERNAL/ENGINEERING; resultado econômico NOT_EVALUATED.

Teste: `tests/test_detection.py:71-110`. PELT retorna fim da série e nenhuma quebra no sinal constante com penalidade; não é detector online.

[Issue/PR/discussão material](https://github.com/deepcharles/ruptures/discussions/166): Mantenedor explica que penalidade BIC depende da likelihood/custo. Não importar a mesma penalidade para l1/l2/normal.

Decisão: referência de contrato/diagnóstico; versões, licença e dependências fixadas antes de qualquer execução. Dados B3 e causalidade continuam responsabilidade local.

## R35 — scikit-learn-contrib/MAPIE

Código `7e888f5249bf942912207d398525d3259a5f07c0`; licença: UNKNOWN. [Releases](https://github.com/scikit-learn-contrib/MAPIE/releases): v1.5.0. Verificação máxima desta alegação: **C2**, EXTERNAL/ENGINEERING; resultado econômico NOT_EVALUATED.

Teste: `mapie/tests/test_time_series_regression.py:359-421`. Update de conformity score e erro por amostra grande; exemplo de teste aceita cobertura0.916 para nominal0.95, não garantia universal.

[Issue/PR/discussão material](https://github.com/scikit-learn-contrib/MAPIE/issues/974): Relato aberto sobre quantil corrigido em amostra pequena virar limite finito; não reproduzido. Exigir teste da fronteira de n antes de integrar.

Decisão: referência de contrato/diagnóstico; versões, licença e dependências fixadas antes de qualquer execução. Dados B3 e causalidade continuam responsabilidade local.

## Fontes e resultados negativos

NEFIN: método §§3–5 examinado: escolhe classe mais negociada no ano anterior, critério de negociação em mais de80% dos dias com volume diário acima deR$500mil, forma carteiras/fatores com regras e defasagens próprias e usa preços ajustados. Isso restringe a população e não demonstra vintage completo. Fatores long-short e risco livre de swap DI não são execução pessoal equivalente. [Método](https://nefin.com.br/resources/NEFIN_methodology.pdf).

DSR e PBO, analisados na primeira parte, tratam seleção e múltiplas tentativas, não fabricam amostra independente. AQR é evidência externa sobre fatores em outro desenho, não aprovação de hipóteses B3 encerradas. Não foi localizada/reproduzida uma replicação independente pertinente que certifique lucro do Stocks. E4/E6 ficam ausentes. Issues são relatos dos respectivos projetos, não bugs reproduzidos por nós; bugs históricos encerrados não foram imputados ao HEAD.

## Ondas e recursos

Ondas1–2:50 sementes OSS,10 fontes/papers;15 fichas focadas; correções de identidade. Onda3: asserções faltantes e releases. Onda4: críticas/issues e contratos de fonte. As ondas3–4 mudaram limites e confiança, sem exigir nova capacidade além das22 já agrupadas. Encerramento por cobertura útil dos nove eixos e orçamento finito, não alegação de auditoria exaustiva de todos os projetos. A API pública retornou403 por quota no lote de30 consultas; erros conservados em acquisition.json. Não repetimos a API; páginas públicas e busca primária permitiram verificar releases/issues. Dois caminhos de testes deram404 e continuam não localizados. Custos monetários adicionais: zero contratado. Bytes obtidos no complemento constam do recibo; conteúdo consultado pela ferramenta web não tem contador de bytes disponibilizado.
