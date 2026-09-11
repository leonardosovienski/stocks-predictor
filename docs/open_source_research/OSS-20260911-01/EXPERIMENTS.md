# Experimentos e gates

## Executado nesta rodada

MECH-01 foi registrado em [G1.json](G1.json) antes de rodar [mechanical.py](mechanical.py). [Recibo](mechanical-receipt.json): **8/8 PASS**, erro observado 0 nos controles analíticos. Python 3.12.14 stdlib, módulo simulation.py por caminho, sem instalar pacote/Core. Isso é C3/E5/LOCAL/ENGINEERING/POSITIVE somente nesses controles; não C4 contra engine externo, nem E6 ou lucro. Uma tentativa, zero tuning, nenhum dado de mercado. Comando: `python -I -B -X utf8 mechanical.py` no auxiliar autorizado; script contém caminho canônico do módulo. Para outro host, adaptar o caminho em cópia identificada e registrar novo recibo.

## Até cinco próximos experimentos

Ordenação por dependência, informação e custo. Os protocolos abaixo distinguem desenho de prontidão: campos materiais pendentes impedem READY_FOR_EXPERIMENT. Nenhum esboço autoriza integrar produção ou capital.

### X01 — O painel preserva exatamente a informação admissível ao acrescentar versões e vínculos futuros?

**Capacidades:** K01, K02

**Teste mínimo:** Fixture sintética de 3 emissores, mudança de ticker, 2 classes, 2 versões e conflito; depois amostra documental fixada de 12 documentos sem retorno.

**Baseline:** document_panel.fundamentals_asof e deduplicação atual por prefixo; comparar mapa CNPJ/ISIN proposto separadamente.

**Dados:** Sintético primeiro; amostra pública só após listar documentos/versões e limites de leitura.

**Métrica/critério:** vazamentos e conflitos silenciosos = 0; nenhum caso ambíguo elegível; equivalência exata nos casos sem mudança.

**Decisão:** Qualquer vazamento bloqueia uso econômico; divergências justificadas aprovam apenas o contrato, não alpha.

**Pré-requisitos:** Fixar os 12 documentos e seus direitos; nenhuma leitura de resultados protegidos.

**Orçamento:** 1 fixture fixa; 12 documentos; zero tuning; até 1 dia de engenharia estimado.

**Próximo gate:** G1 detalhado para amostra documental; G2 apenas após fontes admissíveis.

**Estado:** CANDIDATE

### X02 — Stocks e uma referência externa concordam no mesmo contrato de caixa e eventos?

**Capacidades:** K03, K08

**Teste mínimo:** Expandir MECH-01 para 12 casos analíticos predefinidos; 4 adicionais: venda sem caixa liquidado, bonificação atrasada, fração societária e custo fixo. LEAN/Zipline só nos casos suportados; unsupported explícito.

**Baseline:** Equações Decimal e MECH-01: 8/8 controles locais já aprovados.

**Dados:** Sintéticos; nenhum banco original; inputs iguais por caso.

**Métrica/critério:** Reconciliação <= R$0,01 para caixa monetário e 1e-8 para quantidades; datas idênticas; zero financiamento de recebível não liquidado.

**Decisão:** Diferença de convenção -> NOT_DIRECTLY_COMPARABLE; divergência no contrato comum -> diagnóstico; concordância não prova previsão.

**Pré-requisitos:** Linux permitido, dependências/licença fixadas, revisão de runner externo e contrato de liquidação comum.

**Orçamento:** 12 casos, uma configuração por engine; sem otimização; até 1 dia estimado.

**Próximo gate:** G1 para o engine externo; G2 se divergência material merecer investigação.

**Estado:** DEFER

### X03 — O avaliador rejeita vazamentos e mede incerteza sob dependência?

**Capacidades:** K05, K06

**Teste mínimo:** Controles de datas irregulares e labels sobrepostos; controles positivos/negativos de fit fora do treino. Bootstrap: 500 séries AR(1), T=504, phi fixos 0 e 0.5, seeds 20260911..20261410, L=21, 1000 reamostras, antes de dados B3.

**Baseline:** Gap de calendário atual, fórmula SE iid de economic_gate e Core travado; arch como referência separada.

**Dados:** Somente sintético; sem amostra histórica protegida.

**Métrica/critério:** Zero overlaps admitidos e zero falsas rejeições nos controles disjuntos; cobertura nominal 95% avaliada com intervalo binomial, largura e viés reportados.

**Decisão:** Se 95% ficar fora do IC binomial da cobertura, não aceitar como calibrado nesse DGP; não ajustar L procurando aprovação. Falha de runtime é infraestrutura.

**Pré-requisitos:** Core instalado em Linux autorizado; versões e algoritmo exato fixados; núcleo auxiliar atual não certifica isso.

**Orçamento:** 2 DGP fixos, 500 séries cada; nenhum tuning; tempo máximo a registrar no host antes da execução.

**Próximo gate:** G1 complementar de recursos/versões; G2 se revelar lacuna relevante.

**Estado:** CANDIDATE

### X04 — Diagnósticos distinguem retorno de exposição comum e efeito de custos?

**Capacidades:** K07, K09, K10

**Teste mínimo:** Painel sintético com fator comum conhecido, residual nulo e residual plantado; comparar IC por data, turnover e risco com fórmulas de referência. Posteriormente NEFIN apenas em dados permitidos.

**Baseline:** Ranking simples equiponderado; Alphalens para IC, PyPortfolioOpt para covariância, Riskfolio para ES.

**Dados:** 20 ativos x 120 datas sintéticas; retornos, covariância e custos definidos antes de executar; sem tratar 2400 linhas como amostras independentes.

**Métrica/critério:** Sinal perfeito produz rank IC=1 nos casos sem empate; ruído não recebe selo de alpha; matriz PSD e custos reconciliados; tolerâncias por fórmula no G1.

**Decisão:** Avançar somente se controles separarem exposição e informação incremental; manter habilitador se nenhum alpha existir.

**Pré-requisitos:** Fixture final congelada, políticas de faltantes e unidade de inferência; dependências externas em Linux.

**Orçamento:** 3 controles, sem tuning, no máximo 1 dia estimado.

**Próximo gate:** G1 da fixture; G2 condicionado à utilidade incremental.

**Estado:** CANDIDATE

### X05 — Objetivo relativo acrescenta valor sobre regressão de retorno com as mesmas features?

**Capacidades:** K11, K12, K16

**Teste mínimo:** Após admissibilidade: uma regressão linear regularizada, LightGBM regressão e LightGBM ranking por data; mesmos dados, informação e orçamento; carteira top-K idêntica por regra.

**Baseline:** Regra simples admissível e caixa/benchmark com risco comparável; sem reabrir momentum/value julgados por outro nome.

**Dados:** Painel B3 PIT novo admissível e splits congelados; datas/target exatos PENDENTES de contrato. Nenhum backtest autorizado por este esboço.

**Métrica/critério:** Primária: incremento líquido contra baseline com IC temporal; secundárias rank IC, turnover, drawdown e exposição. NDCG exige relevância fixada.

**Decisão:** Sem intervalo sustentando incremento, INCONCLUSIVE/DEFER; rejeitar apenas escopo avaliado. Holdout já exposto nunca E6-H.

**Pré-requisitos:** X01-X04, dados e custos, seis campos de linhagem e revisão humana se família encerrada, período reservado identificado.

**Orçamento:** Máximo 3 famílias, 5 configurações por família; registrar todas, inclusive abortadas; recursos a fixar em G1.

**Próximo gate:** BLOCKED_DATA/BLOCKED_PERMISSION; G1 ainda não satisfeito; não executar.

**Estado:** BLOCKED_DATA

## Bloqueios de execução

O Windows permite auxiliares stdlib e não permite instalar dependências externas. O workflow vigente só dispara por push/PR; o mandato não autoriza criar commits/push para habilitar CI de benchmarks. Assim, benchmark externo Linux está DEFER por ambiente/acionamento, não por resultado científico negativo. Core instalado e versões completas dos engines ainda precisam de verificação. X05 depende de dados e admissibilidade científica; não apresentar datas de split inventadas como protocolo executável.
