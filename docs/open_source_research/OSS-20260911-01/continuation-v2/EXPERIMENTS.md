# Experimentos executados e não executados

O [G1](G1.json) foi gravado antes de [controls.py](controls.py). Uma tentativa, zero tuning, sem instalação/rede/dados de mercado. [Recibo integral](controls-receipt.json); Python auxiliar3.12.14. Não altera código de domínio. Oito controles MECH-01 anteriores continuam no [recibo original](../mechanical-receipt.json).

## Resultados novos

PIT02:12/12 controles e3/3 documentos públicos PASS. Limites de disponibilidade, revisão, conflito, ticker ambíguo, duas classes, vínculo futuro/expirado, cadastro vazio, três emissores e referência futura. Os três documentos não são a amostra de12 documentos reais proposta anteriormente; não declarar X01 inteiro executado. São teste de engenharia C3/E5/LOCAL/POSITIVE de contratos específicos.

UNC02:500 séries de504 pontos por phi, sementes previamente fixadas, normalidade e inovação unitária, burn-in200. Comparamos economic_gate.estimate_edge sem mudanças com variância finita analítica AR(1). Cobertura bilateral de zero; isto não é taxa de acerto econômico.

|phi|Método|Cobertura|Wilson95%|Critério nominal 95%|
|---|---|---|---|---|
|0|IID atual|92,4%|89,74–94,41%|FAIL|
|0|Oráculo|92,8%|90,19–94,75%|FAIL|
|0,5|IID atual|71,8%|67,70–75,57%|FAIL|
|0,5|Oráculo|92,4%|89,74–94,41%|FAIL|

Não aprovamos calibração de nenhum método: o controle positivo não satisfez o critério. Resultados preservados, sem rerun com novas sementes. A diferença grande sob dependência ilustra a inadequação de aplicar erro padrão IID fora de suas hipóteses, já declaradas no módulo; não é bug de implementação provado. A variância exata usa cov(Xt,Xt+k)=phi^k/(1-phi²) e soma todos os pares: o fator assintótico de erro padrão para phi0,5 é sqrt(3). A comparação é C4 de benchmark numérico local/STATISTICAL, E5 da reprodução específica, com resultado global INCONCLUSIVE pela calibração; não C4 de arch, Core ou engine externo. O oráculo conhece o DGP e não é estimador utilizável em mercado. Sementes emparelhadas tornam métodos dependentes; não contar como quatro estudos independentes.

RANK02:20 ativos sintéticos, scores crescentes e retornos de−10% a−8,1%. Ordenação perfeita(IC=1), top5 perde8,3% bruto e8,4% após custo ilustrativo de0,1%; caixa sintético0%. Falsifica apenas a implicação “IC perfeito garante lucro”. Não é confronto de modelos treinados, não refuta utilidade do ranking e não estima custos do usuário.

## Até cinco próximos experimentos — ordem revisada

1. **X03, calibração/leakage:** preservar UNC02 e investigar o controle nominal antes de ampliar claims. Comparar implementação independente do DGP, datas irregulares e purga por intervalo; arch percentile com blocos21,1000 replicações,500 séries por DGP. Zero sobreposição admitida; reportar cobertura/largura, inclusive falhas. Próximo gate:G1 fechado para host/dependências; execução externa bloqueada por Linux não disponível. O runner Linux anexo é protocolo, não resultado.
2. **X01, identidade/PIT documental:** DOC03 fixou e verificou12 documentos FCA; a etapa restante é unir documentos financeiros, classe e eventos sem preço/retorno. Três documentos de capital e12 metadados FCA não equivalem ao painel completo. Zero conflito silencioso/vazamento; fixar o manifesto do painel integrado antes de executar. Próximo gate:G1 da amostra, depois G2 apenas contratual.
3. **X02, contabilidade diferencial:**12 casos do protocolo original, comparador LEAN/Zipline com contrato de caixa/eventos explícito. TolerânciasR$0,01 e1e−8 quantidade; datas idênticas; unsupported não conta PASS. Oito casos locais já passaram. Host Linux/runner/licença são pré-requisitos; G1 de engine pendente.
4. **X04, exposições e custos:**painel sintético20×120, fator comum/residual nulo/residual plantado; Alphalens/PyPortfolioOpt/Riskfolio contra fórmulas. IC por data, PSD, turnover e custo reconciliados. Não confundir120 datas com2400 observações independentes. RANK02 é só controle lógico preliminar; benchmark dos pacotes não executado. G1 deve fixar fixtures e versões.
5. **X05, ranking versus regressão:**linear regularizada, boosting regressão e ranking com mesmos inputs/splits/carteira/custos. Até3 famílias×5 configurações, todas registradas. Incremento líquido e intervalo temporal versus baseline/caixa/risco comparável. BLOCKED_DATA/PROTOCOL: PIT/eventos/custos e janela admissível; seis campos de linhagem+revisão humana se reabrir família encerrada. Não há data de holdout inventada. Próximo gate:G1 após requisitos; não pronto para execução.

Protocolos originais detalhados e orçamentos preservados em [EXPERIMENTS inicial](../EXPERIMENTS.md). X01/X03/X04 tiveram subcontroles novos identificados; nenhum foi falsamente marcado completo por executar apenas uma parte. NÃO EXECUTADOS: benchmark externo de engine, bootstrap arch, otimizadores e treino B3. Nenhum E6-H/E6-P novo.

## Complemento documental DOC03

Após os controles iniciais, baixamos o FCA2023 oficial (434.044 bytes), com hash no [manifesto](DOC03-manifest.json), ODbL declarada no catálogo. Antes da verificação foram fixados12 documentos: os primeiros quatro por competência/versão/ID dos três primeiros CNPJs com quatro documentos, em ordem lexicográfica; nenhuma escolha por preço/retorno. [12/12 verificações passaram](DOC03-receipt.json) para identidade/metadados e nenhum vínculo antes do corte convencional. Onze documentos não geraram ticker admissível; o último gerou VSPT3/VSPT4. Essa amostra é principalmente um controle de rejeição e NÃO demonstra cobertura de doze empresas negociáveis. O parser registrou504 issues no arquivo completo; não os apagamos nem os classificamos todos como defeitos da fonte. O ZIP fica em C:/STOCKS/work/oss-20260911-01/continuation-v2/fca2023.zip, fora do Git.

DOC03 avança X01 no contrato FCA, mas não completa o painel financeiro/identidade/eventos de X01. Três documentos de capital já reconciliados são outra amostra. Disponibilidade no dia seguinte é convenção conservadora; nenhum horário intradiário observado foi inventado. O [runner documental](documentary.py) separa aquisição/manifesto de --verify. O [runner Linux](linux_bootstrap_protocol.py) é código de protocolo para arch, não executado; requer ambiente permitido, versões e recibo imutável de dependências antes do G1 de execução. Foi verificada apenas sua sintaxe localmente.
