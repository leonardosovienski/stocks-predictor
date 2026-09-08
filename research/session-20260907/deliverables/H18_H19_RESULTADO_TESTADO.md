# H18 e H19 executadas — resultado de pesquisa

H18 (lucro/preço) e H19 (patrimônio/preço) foram executadas nas versões mensal e trimestral. As quatro configurações receberam **NO_PRIORITY_UPGRADE**. H19 apresentou a evidência exploratória mais consistente, mas nenhuma passou o critério econômico e de estabilidade registrado. **Não há lucro líquido demonstrado nem GO para investir.**

O orçamento informado de R$5–10 mil foi usado como contexto econômico. Estes diagnósticos não simulam uma conta com esse capital.

## O que foi medido

96 sinais mensais, de janeiro de 2018 a dezembro de 2025. Há 93 meses elegíveis e 31 trimestres elegíveis. O universo usa vínculos históricos CVM/FCA, no máximo 60 emissores por data, com uma única classe ON e mediana de liquidez diária de pelo menos R$1 milhão. A mediana final é 39 empresas com fator por data; seleciona-se o quinto de maior múltiplo invertido.

Foram obtidos 745 dos 750 capitais originais necessários; cinco documentos permanecem ausentes/inválidos. Os balanços oferecem 748 lucros anuais atribuíveis ao controlador e 750 patrimônios líquidos excluindo não controladores. A capitalização usada é uma aproximação observável: ações declaradas menos tesouraria, traduzidas por eventos de unidade e multiplicadas pelo preço. Ela mantém a defasagem do balanço e não é a capitalização exata em cada data. Documentos só entram depois da divulgação.

## Resultado após as correções

“Spread” é a diferença entre a média de retorno por preço das selecionadas e a média do universo elegível. A coluna de períodos completos exclui períodos com qualquer retorno não medido, portanto sofre seleção por disponibilidade futura. Os valores trimestrais foram divididos por três para comparação aritmética; não são rentabilidade mensal executável.

| Configuração | Períodos completos / elegíveis | Spread em períodos completos, p.p./mês | IC disponível médio | Cenário adverso + custo de 72 bps, p.p./mês |
|---|---:|---:|---:|---:|
| H18 mensal | 77/93 | +0.686 | +0.0003 | -0.859 |
| H18 trimestral | 16/31 | +0.799 | +0.0247 | -0.466 |
| H19 mensal | 77/93 | +0.912 | +0.0253 | -0.882 |
| H19 trimestral | 16/31 | +1.046 | +0.0491 | -0.468 |

No cenário adverso, cada retorno ausente vale −100% quando o papel está selecionado e +100% quando está fora da seleção; o mesmo retorno atribuído entra na estratégia e no benchmark. É um cenário severo, **não um limite matemático**. São deduzidos 36 ou 72 pontos-base por período de manutenção como obstáculos econômicos, sem alegar custo executável calibrado. O benchmark recebe custo incremental zero nessa comparação.

O gate exigia IC positivo e spread adverso positivo em ambas as metades fixadas, 2018–2021 e 2022–2025, além de média adversa após 72 bps de pelo menos 0,42% ao mês equivalente. O patamar é uma referência de pesquisa próxima de R$500/ano sobre R$10 mil; não é projeção de lucro nem preferência já confirmada pelo usuário.

H18 tem IC negativo na primeira metade nas duas frequências. H19 tem IC positivo nas duas metades, mas falha nos cenários adversos. O spread condicional favorável de H19 não permite descartar viés de dados ausentes, risco de empresas em dificuldade ou diferenças setoriais.

## Correções que alteraram a medição

- O extrato antigo tinha 387.101 cotações e filtrava classificações BDI. O novo contém 391.824, com 4.723 adicionais e zero preços anteriores alterados. Americanas continuou negociando após 19/01/2023 sob BDI 08. Sua perda entre as aberturas de 02/01 e 01/02/2023, **−79,20%**, agora é medida. A classificação e os campos constam do [layout oficial COTAHIST da B3](https://www.b3.com.br/data/files/33/67/B9/50/D84057102C784E47AC094EA8/SeriesHistoricas_Layout.pdf).
- Natura em 18/09/2019 e Porto Seguro em 21/10/2021: uma bonificação de 100% registrada pela B3 era aplicada novamente como split legado. O documento primário passou a contar uma vez; o registro antigo permanece na trilha de auditoria.
- Qualicorp, Hering, Americanas, Petz e Hapvida tiveram movimentos superiores a 30% confirmados nas linhas originais da B3. Foram mantidos com alerta explícito, incluindo as perdas. Demais saltos sem revisão continuam faltantes.
- As quatro seleções, fatores, datas e critérios foram preservados. Foram recuperadas 28 células antes sem retorno; nenhum retorno anteriormente medido mudou.

A primeira rodada está preservada. O diagnóstico corrigido mantém **17 retornos sem medição no mensal e 18 no trimestral**, por família, correspondendo a 35 intervalos distintos. Fusões, mudanças de instrumento, subscrições e cisões ainda exigem termos próprios. A elegibilidade original também permanece congelada, inclusive exclusões provocadas pelo filtro de qualidade antigo. Isto é correção da medição de uma seleção já observada, não validação de uma estratégia completamente reconstruída.

## Estado da pesquisa

H1–H16 foram revisadas quanto à confiabilidade; H3 não foi executada e há 15 trials legados. Os vereditos NOT_SUPPORTED foram preservados. As falhas de datas, pesos, benchmark e fontes tornam sua evidência desigual, sem justificar promover automaticamente resultados antigos positivos. H17 já foi observada e continua inconclusiva; os problemas adicionais encontrados no painel de eventos também limitam a leitura daquele diagnóstico, que não foi rerodado nesta etapa.

H18 e H19 deixaram de ser hipóteses nunca vistas. O mínimo acumulado é **20 configurações e 25 avaliações de retorno**, incluindo as revisões. O total adaptativo histórico é desconhecido. As revisões não são evidência independente; não há holdout histórico intacto e nenhuma Proof foi consumida.

A regra de parada desta rodada foi aplicada. H18 perde prioridade. H19 é uma pista para investigação de fontes e retorno total, sem promoção por ter um gráfico ou spread favorável. O ganho de informação seguinte depende de resolver os eventos restantes para todos os ativos afetados, e depois incorporar dividendos/JCP, caixa, quantidades, custos, impostos pertinentes e uma alternativa de caixa. Variar parâmetros ou adicionar ML aos mesmos dados não resolve esses pontos.

## Código e reprodução

A última versão de código foi validada com **515 testes aprovados em 140,09 segundos**, cobertura de testes de 81%, Ruff no escopo do CI, Pyright no escopo configurado, construção da wheel e importação fora do checkout. Os testes incluem documentos reais da CVM e linhas originais da B3. A cobertura não é certificação científica.

Código testado: `2a86e0cf4c6dac53c267390e57235d3ad6b87a80`. Protocolo inicial: `b6a2cc4ba4cbe8fb2d614427ad4d26a3193c7943bbba4e4c9449982ff72a1dde`. Protocolo de correção: `1f4ad50cd682f4611f16676f64cf56de1c37a5eeab9704b8f7257fc816c1ab0f`.

O pacote `STOCKS_H18_H19_TESTADOS.zip` inclui código, dados, documentos de capital, extratos de contas e cotações primárias, protocolos e ambas as observações. `RODAR_PESQUISA_STOCKS.py` confere os hashes, extrai em `work/` e reproduz as duas versões offline, sem instalação, venv ou ordens. O resultado da verificação fica em `H18_H19_REPRODUCAO_VERIFICADA.json`.

Os bancos operacional e de fontes testadas foram preservados. Não houve operação financeira, gasto com dados ou alteração do Core.
