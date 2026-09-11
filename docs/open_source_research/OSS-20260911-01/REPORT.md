# Stocks Predictor — resultado da rodada de pesquisa

**Decisão: investir primeiro na capacidade de confiar em identidade, datas e retorno total; depois medir ranking. Não há evidência nesta rodada que justifique substituir o runtime ou instalar um modelo sofisticado.**

Rodada `OSS-20260911-01`, baseline `80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5`. Foram registradas 60 entradas de discovery, 56 com identidade confirmada por conteúdo/metadados, e 15 fichas de implementação focadas. A matriz agrupa alternativas em 22 capacidades. O único experimento executado foi mecânico e sintético: **8/8 controles aprovados**. Nenhuma nova avaliação de retorno histórico, operação financeira ou integração permanente.

## O que já existe e onde estão as limitações

O código tem parser COTAHIST, fontes versionadas por hash, universo com corte temporal, fundamentos por versão/recebimento, ranking simples, motor com quantidades/caixa, controles de fonte e perfil pessoal. Foram lidas implementações e asserções selecionadas; oito propriedades do motor foram executadas diretamente no auxiliar stdlib. Isso não equivale a validar o pacote instalado ou a operação completa.

Três limites materiais apareceram no caminho inspecionado: deduplicação por prefixo de ticker não é identidade histórica CNPJ/ISIN; o embargo atual é uma regra de calendário, não validador geral de labels e treinamento; o gate aritmético de edge usa erro padrão iid e declara não corrigir dependência. Há componentes melhores que o histórico legacy, mas corrigi-los não reabilita automaticamente hipóteses antigas.

A documentação vigente ainda aponta valores líquidos, datas de pagamentos e eventos societários incompletos. Custos e cenário pessoal também permanecem incompletos. Os 12 bancos foram localizados pelo catálogo, mas **não acessados nem recontados**. A CI do SHA atual e o wheel Core instalado não foram confirmados nesta rodada. [Detalhes e cobertura](BASELINE.md).

## Respostas às dez perguntas do mandato

1. **O que funciona?** Os oito controles de contabilidade/cronologia passaram. Fonte versionada, painel e universo têm implementação inspecionada. Operação integral e lucro pessoal continuam sem comprovação nesta rodada.
2. **Que dados faltam?** Identidades/transições, versões disponíveis na decisão e termos completos de eventos/recebíveis. CVM DFP/ITR/FCA/FRE, B3 e documentos de emissores são fontes candidatas; devem ser reconciliadas por versão. A CVM atualiza reapresentações: acesso ao arquivo atual não é prova de disponibilidade histórica. [Catálogo DFP](https://dados.cvm.gov.br/dataset/cia_aberta-doc-dfp).
3. **Que análises podem valer mais que outro modelo?** Cobertura por data/emissor, diagnósticos de identidade, perdas amostrais, rank IC por data, turnover, exposições e decomposição de custo. São perguntas observáveis sobre confiabilidade e utilidade, sem pressupor alpha.
4. **Ranking relativo venceu forecasting?** Não foi feito confronto controlado admissível. A preferência inicial do DESIGN é uma hipótese; IC histórico ou catálogo de modelos não a comprova. X05 propõe a comparação e está bloqueado por dados/protocolo.
5. **Quais referências ajudam?** Qlib para fit delimitado, sklearn para entender limites do gap, Alphalens para IC por data, arch para inferência, LEAN/Zipline para convenções, PyPortfolioOpt/Riskfolio para risco. Nenhuma substitui nossos ledgers, fontes ou gates. [Fichas por commit](SURVEY.md).
6. **O que transfere à B3?** Contratos de validação, métricas e cálculo numérico transferem com adaptação. Estratégias, calendários, short, lotes, custos e eventos precisam de prova local. NEFIN é referência de fatores brasileiros, com metodologia própria, não carteira pessoal equivalente. [NEFIN](https://nefin.com.br/data/risk-factors/).
7. **Que ferramentas melhoram ciência sem alpha?** Validador temporal, testes diferenciais de caixa, bootstrap, multiplicidade, contratos de dados e diagnóstico de exposição. HMM/PELT ex post e SHAP podem explicar dados/modelos, mas não certificar previsões.
8. **Quais composições?** C02 (calendário+labels+inferência+replay) primeiro; C01 (identidade+PIT+eventos+ranking) depois; C03 (ranking+risco+fatores+custos) condicionada. Rejeitar reabertura disfarçada e duplicação de infraestrutura; adiar redes/RL. [Matriz](CAPABILITY_MATRIX.md).
9. **Quais cinco experimentos?** X01 identidade/PIT; X02 contabilidade diferencial; X03 leakage/inferência sintética; X04 diagnóstico de fatores/risco; X05 ranking versus regressão. Cada um tem pergunta, teste, orçamento, critério e gate em [EXPERIMENTS.md](EXPERIMENTS.md).
10. **O que executar em seguida?** Tornar X01 documentalmente executável, fixando a amostra de 12 documentos sem consultar retorno. Resolver resultados de qualidade antes de escolher modelo ou novo backtest. Isso é pesquisa, sem autorização financeira.

## Prioridade e evidência

Os scores são intervalos de potencial/risco, com confiança baixa e análise de pesos .60/.70/.80. A sobreposição não sustenta um ranking numérico fino. A fila econômica não recebe número inventado. As vistas por categoria reutilizam os mesmos IDs; 60 referências não viraram 60 tarefas. [Registro estruturado](registry.json).

MECH-01 verificou entrada posterior ao sinal, custo, split, direito/pagamento, ausência de cotação, mudança de futuro e fechamento posterior. Erro observado zero nos casos analíticos definidos; C3/E5 somente nesse escopo. Não houve benchmark executado contra biblioteca externa, teste do Core instalado, E6 ou validação de ganho financeiro. [Recibo](mechanical-receipt.json).

## Limites da entrega

Esta rodada avança da baseline à descoberta e à decisão, mas **não completa a auditoria exaustiva solicitada**: faltam aprofundamento sistemático de testes/issues/releases, contratos de dados econômicos, CI/wheel atuais e benchmarks externos em Linux. A busca terminou por orçamento, sem alegação de saturação. Bancos e protocolos permaneceram preservados. H21/H22 mantêm seus estados documentais, sem novo julgamento. [Decisões e pendências](DECISIONS.md).

Fontes locais de pesquisa e downloads com hashes estão em `C:\STOCKS\work\oss-20260911-01`; documentação da iniciativa em `docs/open_source_research/OSS-20260911-01/` no checkout. Esta cópia de entrega usa o diretório de outputs definido pela sessão. Nenhum commit ou push foi realizado.
