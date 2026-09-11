# Encerramento da iniciativa OSS — OSS-20260911-01

**A fase de pesquisa OSS está encerrada com cinco capacidades experimentais implementadas, executadas e comparadas. Quatro são candidatas à integração de engenharia; o alocador com limite de giro permanece experimental. Nenhum ganho econômico B3 foi demonstrado.** O benchmark econômico X05 permanece adiado por um único blocker material: falta um painel B3 congelado que associe inputs disponíveis na decisão a labels econômicos completos para o mesmo universo/período dos quatro braços.

Não reiniciamos baseline, scoring ou discovery. A pesquisa direcionada aprofundou referências existentes e acrescentou duas capacidades/fonte de referência. O score original e os estados C/E permanecem nos registros anteriores; `closure-registry.json` adiciona avaliação de encerramento por ID. TOTS3 e UNC02 foram preservados, não reexecutados. Um blocker de dados não impediu nenhum dos cinco protótipos sintéticos.

## O que efetivamente trouxemos

| ID | Implementação | Comparação executada | Resultado medido | Decisão |
|---|---|---|---|---|
|K05|Normalizador com fit temporal imutável e disponibilidade|Treino0..9 versus acréscimo de100 valores futuros1e9; oráculo média4,5/variância8,25; entradas inválidas|Parâmetros preservados; fit futuro/tardio/constante recusados|INTEGRATE_CANDIDATE|
|K07|IC por data, empates, quantis e cobertura explícita|Controle com confundimento temporal;120 permutações e oráculo independente sem empates; labels faltantes|IC agregado enganoso+0,52381; IC por data−1; erro máximo do oráculo abaixo1e−12; ausência de label não altera seleção|INTEGRATE_CANDIDATE|
|K22|Neutralização por grupo datado e diagnóstico de residual|Score com offset setorial±10 e residual conhecido; puro fator e reversão|Média setorial absoluta10→0; IC com residual0,48795→1; reversão retorna−1; puro grupo não recebe IC definido|INTEGRATE_CANDIDATE somente diagnóstico|
|K21|Gate de participação ordem/volume disponível|6 casos de ordem/volume, incluindo insuficiência, dado tardio, zero, negativo e excesso; spike futuro|1 elegível e5 recusados corretamente; dado futuro não melhora elegibilidade|INTEGRATE_CANDIDATE|
|K09|Rebalanceamento limitado por half-L1 com reserva de taxas|20 rotações sintéticas, alvo do seletor atual,98% investido,2% caixa, taxa0,2% por notional, budget0,1|Custo acumulado7,5684%→0,79565% do NAV inicial; redução89,4872%. Na reversão, líquido−1,6% versus+1,568% da troca completa|KEEP_EXPERIMENTAL; rejeitar superioridade universal|

Os percentuais de K09 são efeitos de cenários artificiais fixados, não estimativas de custo ou rentabilidade da B3. O parâmetro de participação1% também é fixture, não limite recomendado. Não houve tuning, sementes, coleta de retornos ou mudança de critério após resultados. O benchmark principal passou33 checks. Uma verificação adicional motivada pela convenção de giro reconciliou40 vetores com `execution.weighted_turnover_cost`, erro máximo0; a CLI também executou o exemplo por arquivo JSON. Benchmark principal mediu cerca de0,015 segundo de computação, sem reivindicar ganho de velocidade contra outra biblioteca.

**FOUND/STUDIED**:60 referências herdadas, deep dives focados e R61/R62 adicionais. **IMPLEMENTED/EXECUTED/BENCHMARKED**: os cinco itens acima, em implementações próprias stdlib. **ECONOMICALLY_TESTED**: zero nesta fase. **Engine externo executado**: zero. Oráculo analítico independente não equivale a engine independente nem revisão humana independente. Os controles defeituosos são ablações plantadas, não bugs atribuídos ao Stocks sem prova.

O kit executável está em `research/oss/OSS-20260911-01`: `capabilities.py`, `tool.py`, protocolo, fixtures, benchmark e recibos. Ele é isolado, sem instalação, rede, banco ou ordens. Exemplo: `python -I -B -X utf8 tool.py ranking ranking-example.json novo-recibo.json`. A CLI recusa sobrescrever a saída. Para reproduzir benchmarks, usar os scripts em uma cópia de pesquisa e conservar o recibo original; os scripts de benchmark ainda apontam ao checkout canônico para comparar os módulos existentes.

## Top20 capacidades externas e gap map

| ID / capacidade | Stocks hoje | Ref A / B / C | Gap pertinente | Evidência / experimento / resultado | B3 | Ação / fila |
|---|---|---|---|---|---|---|
|K01 Identidade histórica CNPJ/ISIN/classe|PARCIAL; FCA/ISIN e joins existentes|R53,R05,R02|Cobertura contínua identidade|X01/TOTS3 incompleto preservado|Contrato transferível; uso empírico condicionado|IMPROVE / BLOCKED|
|K02 Versões e disponibilidade de fundamentos|PARCIAL; versões e disponibilidade modelada|R01,R51,R60|Contratos completos de PIT|DOC03 majoritariamente rejeição|Contrato transferível; uso empírico condicionado|IMPROVE / BLOCKED|
|K03 Eventos e recebíveis reconciliados|PARCIAL; eventos e recebíveis mecânicos|R02,R05|Calendário econômico completo|Split TOTS3 mecânico; liquidez UNKNOWN|Contrato transferível; uso empírico condicionado|AUGMENT / BLOCKED|
|K04 Contrato de calendário e observação|PARCIAL; calendário observado|R18,R19,R02|Calendário oficial/sessões e staleness|Não há novo teste de calendário|Contrato transferível; uso empírico condicionado|VALIDATE / EXPERIMENT_NEXT|
|K05 Validação de treino e labels por data|PARCIAL; corte cronológico, sem pipeline geral fit/transform|R01,R11|Estado ajustado por fold e disponibilidade|100 linhas futuras não alteram parâmetros;6 checks|Contrato transferível; uso empírico condicionado|ADD / IMPLEMENT_NOW|
|K06 Inferência temporal e multiplicidade|PARCIAL; governança e diagnóstico UNC02|R09,R57,R58|Inferência apropriada ao experimento real|IID inadequado; FAIL e diagnóstico preservados|Contrato transferível; uso empírico condicionado|KEEP / KEEP_CURRENT|
|K07 Diagnóstico de ranking e atrito|PARCIAL; seleção existe, painel IC/quantis incremental|R16,R01|IC por data, empates e cobertura de labels|IC agregado+0,524 versus por data−1;120 permutações|Contrato transferível; uso empírico condicionado|AUGMENT / IMPLEMENT_NOW|
|K08 Teste diferencial de contabilidade|CONTROLES LOCAIS; engine independente pendente|R05,R02,R03|Adapter e ambiente independente|40 custos locais reconciliados; engine externo não rodou|Contrato transferível; uso empírico condicionado|VALIDATE / BLOCKED|
|K09 Covariância e risco de cauda|Pesos iguais/inverso vol/custos; sem budget explícito no seletor|R61,R07,R08|Restrições de giro/exposição/capacidade|Custo sintético−89,49%; perde na reversão|Contrato transferível; uso empírico condicionado|AUGMENT / EXPERIMENT_NEXT|
|K10 Fatores brasileiros como controle|Controle sintético de fator já existente|R56,R10|Fatores brasileiros datados no painel|X04 prévio preservado; sem retorno real novo|Contrato transferível; uso empírico condicionado|AUGMENT / EXPERIMENT_NEXT|
|K11 Ranking relativo versus forecast|Pergunta econômica aberta|R01,R12,R13|Confronto comum forecasting/ranking|X05 não executado; sem vencedor|Contrato transferível; uso empírico condicionado|RESEARCH / BLOCKED|
|K12 Value/quality/ranking com baixo giro|Famílias value/quality já investigadas e protegidas|R16,R56,R59|Ganho incremental líquido não demonstrado|Não reabrir resultados antigos por novo wrapper|Contrato transferível; uso empírico condicionado|RESEARCH / RESEARCH_MORE|
|K13 Regimes causais para sizing|Não certificado como sinal causal|R32,R10|Filtro online sem smoothing retrospectivo|Deferido; sem teste novo|Contrato transferível; uso empírico condicionado|RESEARCH / RESEARCH_MORE|
|K14 Macro com vintages|SGS acessível; vintage é questão separada|R55,R20,R62|Relógio de revisão macro|ALFRED ensina contrato; não certifica macro B3|Contrato transferível; uso empírico condicionado|AUGMENT / RESEARCH_MORE|
|K15 Incerteza preditiva e calibração|Calibração preditiva não qualificada|R35,R29|Incerteza condicional ao modelo/alvo|Não aprovar conformal por cobertura conveniente|Contrato transferível; uso empírico condicionado|RESEARCH / RESEARCH_MORE|
|K16 RF/ExtraTrees/boosting baselines|Sem benchmark comum B3 destes modelos|R11,R12,R13|Baseline linear/árvore antes de complexidade|Aguardar painel X05; sem instalar modelos|Contrato transferível; uso empírico condicionado|RESEARCH / EXPERIMENT_NEXT|
|K17 ARIMA/VAR/Kalman e baselines temporais|Sem comparação admissível para alvo relevante|R10,R27,R30|Baselines temporais específicos|Deferir campeonato de preço absoluto|Contrato transferível; uso empírico condicionado|RESEARCH / RESEARCH_MORE|
|K20 Registro e contratos de dados|ADEQUADO ao escopo: registros, hashes e recibos|R40,R39,R41|Não há gap que justifique outro tracking|KEEP; não substituir Core ou duplicar serviço|Contrato transferível; uso empírico condicionado|KEEP / KEEP_CURRENT|
|K21 Viabilidade por capital e custos|Perfil e custo existem; volume não limita ordem individual|R61,R02|Gate ordem/volume disponível|5/6 casos inviáveis recusados;1/6 elegível|Contrato transferível; uso empírico condicionado|AUGMENT / IMPLEMENT_NOW|
|K22 Relações, neutralização e features|Features existem; neutralização por grupo não demonstrada|R05,R16,R61|Diagnóstico separando componente setorial|Média de grupo10→0;IC residual0,488→1 no controle|Contrato transferível; uso empírico condicionado|AUGMENT / IMPLEMENT_NOW|

K18 redes/Transformers e K19 RL/notícias/LLMs foram considerados no universo externo e ficam fora do top20 operacional por custo/baixo ganho incremental demonstrado. Isso é DEFER nesta fase, não prova de que esses métodos nunca funcionam. As ações/referências acima remetem aos IDs existentes. A [revisão técnica e de fontes](SOURCE_REVIEW.md) contém URLs, commits, diferenças e limites. Não existe denominador que permita medir prevalência competitiva; não usamos popularidade como evidência de lucro.

## Top10 gaps reais

1. Painel econômico de experimento que junte disponibilidade, universo e labels completos (K01–K03/K11).
2. Contrato reutilizável de fit/transform por fold, com disponibilidade (K05; protótipo entregue).
3. Diagnóstico de ranking por data com cobertura e empates (K07; entregue).
4. Separação de efeito setorial e score residual, sem chamar residual de alpha (K22; entregue).
5. Limite de participação de cada ordem, além de ranquear liquidez (K21; entregue).
6. Restrições de giro/concentração aplicadas antes da execução (K09; experimental).
7. Validação contábil por implementação externa com contrato comum (K08/X02).
8. Fatores brasileiros como controle empírico e não sinal automaticamente lucrativo (K10).
9. Relógios e vintages de macro/fundamentals com políticas por série (K02/K14).
10. Inferência própria do experimento, com denominador de tentativas e dependência (K06/K15). UNC02 não foi reaberto.

A solução atual é adequada para preservar evidência, impedir sobrescrita de snapshots, consultar liquidez histórica no escopo documentado, selecionar pesos iguais e cobrar custo ponderado. KEEP não significa identidade/PIT completos ou ausência de todos os bugs. Não há ganho demonstrado que justifique trocar banco/Core/ledgers ou o seletor base.

## Padrões recorrentes e independência

1. Fit separado de transform, congelado no treino — Qlib e scikit; adoção do contrato, não replicação econômica.
2. Avaliar ranking por data — Qlib e Alphalens, implementações de linhagens diferentes.
3. Tratar custo/ordem explicitamente — LEAN e Cvxportfolio, modelos diferentes, sem equivalência automática.
4. Restringir negociação pela liquidez — LEAN e Cvxportfolio; impacto e restrição não são o mesmo mecanismo.
5. Controlar composição de grupos/fatores — Cvxportfolio e Zipline; Alphalens/Zipline compartilham origem Quantopian.
6. Separar ajuste de preço de evento contábil — LEAN e Zipline; detalhes de liquidação precisam de contrato comum.
7. Reduzir giro conscientemente — Qlib TopkDropout e Cvxportfolio; nosso contraexemplo impede tratá-lo como benefício universal.
8. Tornar tempo explícito — CVM versões, ALFRED vintages e bibliotecas de calendário; relógios diferentes não são intercambiáveis.
9. Usar oráculos e testes diferenciais — suites de engines e implementações alternativas inspecionadas no survey; concordância não prova economia.
10. Rastrear artefatos/configuração — DVC/MLflow e mecanismos locais; benefício depende de evitar duplicação de infraestrutura.

Esses padrões priorizam investigação; não somamos forks ou wrappers como estudos independentes. Papers DSR/PBO oferecem argumentos e diagnósticos específicos, não replicam uma estratégia B3. Não se inferiu arquitetura interna de produtos comerciais.

## Ferramentas/fontes que mais valem nosso tempo

| Ferramenta ou grupo de alternativas | Uso escolhido | Substitui ou complementa? |
|---|---|---|
|Qlib|Referência de pipeline e pesquisa cross-sectional|Complementar conceitos; não importar plataforma inteira|
|Alphalens-reloaded|Diagnóstico de fatores e ranking|Pode evitar manter visualizações avançadas próprias via adapter futuro; não contabilidade|
|scikit-learn|Pipeline, baselines lineares/árvores e transformadores|Dependência futura pode substituir componentes ML artesanais; nenhum runtime novo agora|
|Cvxportfolio|Restrições de giro, participação e exposição|Referência/benchmark futuro; licença GPLv3 e solver pesam contra vendor automático|
|Zipline-reloaded|Ajustes e contabilidade de referência|Validar independentemente contrato comum quando ambiente permitir|
|LEAN|Casos de execução e slippage|Complementar/validar; não substituir o projeto|
|PyPortfolioOpt / Riskfolio|Covariância, alocação e cauda|Alternativas dentro de K09, escolher uma conforme teste; sem duplicar duas stacks|
|exchange_calendars|Calendário de sessões|Candidato a substituir tabelas ad hoc após comparação B3; depende de versão/feriados|
|NEFIN|Fatores brasileiros e fontes auxiliares|Adicionar fatores como controle, observando cobertura e direitos|
|CVM/BCB/ALFRED|Dados primários e contratos de disponibilidade|Integrar por fonte/campo; wrapper não cria vintage que não existe|

DVC, MLflow, Pandera e Great Expectations ficam como referências de engenharia; os ledgers existentes não justificam outro serviço nesta escala. Dados adicionais prioritários são fatores NEFIN e registros CVM/BCB que preencham campo material do painel. ALFRED é referência/possível fonte macro de contexto, não substituto do BCB. Opções, câmbio, commodities, curva DI, notícias/sentimento e dados alternativos só entram com hipótese, cobertura e custo; não foram integrados nesta fase.

## Novas linhas concretas — fila curta, sem forçar dez

1. X05: comparar quatro braços no mesmo painel admissível, sem precisar fechar todos os ativos da B3.
2. C03: score bruto versus residual setorial, mesma carteira/custos; ablar neutralização.
3. C03: carteira atual versus limite de giro, incluindo reversão e perda de oportunidade; ablar budget.
4. K21: limitação por participação versus liquidez agregada, medindo taxa de execução e capacidade, não apenas seleção.
5. K09/K10: pesos iguais versus uma única alternativa de risco, com exposição e custo casados.
6. K14: uma única série macro versionada usada causalmente versus versão final como controle de vazamento.

Essas são propostas; não reabrem automaticamente H1–H22. Qualquer reaproveitamento de família julgada precisa de linhagem e alteração material explicitadas. A seleção de dados e parâmetros deve anteceder consulta de desempenho.

## Rejeições e adiamentos

| Ideia/claim | Evidência ou razão | Decisão e escopo |
|---|---|---|
|IC agregado basta para ranking|Contraexemplo+0,524 com todos os ICs diários−1|REJECT, testado|
|Menor giro sempre melhora líquido|Reversão:−1,6% limitado versus+1,568% completo|REJECT, testado|
|Dado futuro no fit é inofensivo|A média all-row é contaminada; fit protegido não muda|REJECT, testado como ablação|
|Retirar ativo por label desconhecido é elegibilidade causal|Membership protegido permanece; spread viraUNKNOWN|REJECT como prática operacional; controle executado|
|Componente de grupo puro é informação residual|Demean produz zero e IC indefinido|REJECT, testado|
|Ordem viável porque papel tem volume passado|5 casos inválidos/insuficientes bloqueados|REJECT como garantia; controle executado|
|Mais tracking resolve nosso gargalo|Redundância com hashes/ledgers existentes|DEFER por julgamento, não benchmark negativo|
|Transformers/RL/LLM antes de baseline comum|Ganho incremental não demonstrado; dados/custo pesam|DEFER, não testado economicamente|
|Copiar engine/solver com licença não analisada|Custo de integração/licença/semântica|REJECT reutilização cega, não a ferramenta|
|Aceitar incerteza IID sob dependência testada|UNC02 histórico preservado|REJECT no escopo anterior; não reexecutado|

Não aprovamos bootstrap/HAC/conformal nesta fase. RMSE/accuracy não escolhem vencedor econômico. Também não tratamos neutralização de score como neutralidade da carteira ou retorno residual como alpha.

## O que integrar, manter e parar

**INTEGRATE — candidatos para integração posterior, sem alteração do runtime nesta fase:**

| Capacidade | Evidência | Arquivos/camada futura | Plano e testes necessários | Risco / rollback |
|---|---|---|---|---|
|K05 contrato fit/transform|6 checks, isolamento da contaminação futura|Novo adapter de preprocessing; preservar `simulation.py` legado|Timestamp tipado, múltiplas colunas, filas por fold; positivos/negativos e propriedade de append futuro; suíte Linux|Bloqueio excessivo/coluna constante; desligar adapter e conservar recibos|
|K07 diagnóstico por data|8 checks incluindo120 oráculos de permutação|Adapter de relatório; `report.py` só na integração autorizada|Calendário/labels, empates, cobertura por quantil, IC/estabilidade e snapshot; snapshot do relatório atual|Drop silencioso ou agregação enviesada; desativar seção nova|
|K21 participação|3 checks compostos,6 casos|Pré-trade research adapter de `execution.py`/perfil; universo base preservado|Volume em unidade coerente e janela de sessões, recência explícita, lotes, custo; recusar UNKNOWN|Volume previsto não executável e timestamp inteiro só de fixture; manter flag experimental/desligar gate novo|
|K22 diagnóstico setorial|6 checks, sinal puro/reversão|Adapter de fator/relatório, sem substituir famílias julgadas|Classificação PIT, grupos pequenos/ausentes, exposição da carteira medida separadamente; ablação|Remover prêmio real ou confundir demean com neutralidade; desligar transformação, manter diagnóstico|

O módulo tem benefício suficiente para propor esses contratos, não maturidade para liberar produção imediatamente. **KEEP_EXPERIMENTAL:** K09 e composições C01/C03; adapters externos ainda não executados. **REJECT/DEFER:** claims da tabela anterior, stack de modelos/serviços redundantes e retomada de arqueologia TOTS3 sem blocker local.

Arquitetura desejada: fontes versionadas → contratos de disponibilidade/identidade → snapshot elegível → fit por fold → score baseline/ranking → diagnóstico de ranking/fatores → restrições de risco/giro/capacidade → execução/recebíveis/custos → relatório e registro. Interfaces têm dados e hashes explícitos; engines externos entram por adapters de comparação. Gates respondem ao claim: parser/diagnóstico não precisa provar alpha; retorno líquido precisa de painel econômico e validação pertinente. Rollback nunca apaga evidência.

## X01–X05 no encerramento

X01/TOTS3 permanece incompleto exatamente como documentado. Nenhuma UNKNOWN foi preenchida. X02 externo permanece adiado por falta de ambiente Linux com adapter e versões fixadas; não é requisito global para métricas matemáticas. A verificação de40 custos locais não foi rotulada como X02 independente. X03/UNC02 mantém diagnóstico fechado e FAIL original. X04 ganhou diagnóstico setorial K22; a decomposição temporal anterior foi preservada sem nova execução.

X05 não foi economicamente executado. **Único blocker material de execução agora: painel admissível congelado para o confronto.** Não exigimos perfeição histórica geral, fechar TOTS3 se fora do universo escolhido, nem aprovação de todas as bibliotecas. Uma vez definido esse painel, registrar horizonte/período/universo/custos de cenário comuns e quatro braços: baseline simples, forecast absoluto regularizado, ranking simples e um ranker justificado, cada ajustável com o mesmo teto de5 configurações. Seleção do braço sofisticado pode ser LightGBM por grupos de data, após licença/ambiente e baseline; não há vencedor previamente escolhido. Inferência deve ser qualificada para seus labels reais, não retomar UNC02 abstratamente.

Retorno aparente: em X04 anterior, beta0,975 explicava o controle de exposição; residual bruto0,001 e custo0,002 davam−0,001 líquido no cenário correspondente. Nesta fase, offset setorial±10 desapareceu no diagnóstico; isso não estima fração de retorno real explicado. O custo-only K09 e sua reversão demonstram trade-off, não alpha. Não há percentual empírico B3 de alpha residual a declarar.

## Roadmap pós-iniciativa

**NOW:** (1) integrar posteriormente os adapters diagnósticos K05/K07 com testes proporcionais; (2) escolher um painel econômico mínimo e congelá-lo para X05, sem ampliar TOTS3; (3) colocar K21/K22 no caminho de pesquisa com contratos temporais reais e flags de rollback.

**NEXT:** executar X05 quando o painel existir; testar uma única ablação de giro/exposição; fazer X02 externo em Linux sobre os casos pequenos já definidos.

**LATER:** uma alternativa de covariância/portfólio, macro com vintage ou fonte de risco que preencha campo necessário; modelos complexos só após incremento mensurável.

**STOP:** reabrir UNC02/TOTS3 sem necessidade material; campeonato de modelos; documentação ou tracking redundante; retorno bruto/IC agregado como prova; trocar seed/critério para aprovação.

As três ações de maior impacto são o kit diagnóstico no fluxo de pesquisa, um painel mínimo para X05 e a camada de capacidade/exposição. A iniciativa OSS encerra a busca e a seleção; essas próximas integrações/experimentos são roadmap, não tarefas infinitas desta fase.

## Respostas finais obrigatórias — índice

1. Vinte capacidades: gap map. 2. Adequadas hoje: K20, seletor e custo ponderado no escopo; KEEP descrito acima. 3. Gaps: top10. 4. Sistemas funcionalmente melhores em etapas específicas: Qlib/scikit, Alphalens, Cvxportfolio, LEAN/Zipline; sem comparação econômica global. 5. Convergência e independência: dez padrões. 6. Cinco protótipos: K05/K07/K22/K21/K09. 7. Ganhos mensurados: isolamento, diagnóstico, restrições e custo sintético; zero alpha demonstrado. 8. Rejeições: tabela separa testes de julgamento. 9. Substituição: futura biblioteca de calendário/ML/visualização, nenhuma troca de núcleo agora. 10. Complementar/validar: ferramentas da tabela. 11. Fontes: NEFIN e CVM/BCB por campo; ALFRED para vintages quando pertinente. 12. Filtros/ranking promissores: capacidade, baseline simples, residual e giro com ablação. 13. Ranking versus forecasting: aberto, X05 não executado. 14. Fatores/custos: controles descritos, sem inferir B3. 15. Integráveis: quatro candidatos de engenharia. 16. Não implementar: claims rejeitados e complexidade sem ganho. 17. Arquitetura: adapters com contratos entre etapas. 18. Três ações: NOW.

## Recibos e preservação

`benchmark-receipt.json` liga protocolo, código, fixtures e resultados por SHA256. `cost-contract-receipt.json` identifica a função local comparada. `preservation-before.json` e `delivery-receipt.json` comprovam preservação dos arquivos científicos anteriores e módulos operacionais inventariados. Nenhum commit, hash, manifest ou recibo antigo foi substituído; HEAD permaneceu80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5. O índice documental recebe apenas entrada para os artefatos novos. Código experimental não altera o pacote/Core, bancos ou hipóteses encerradas. A suíte de runtime e o engine externo não foram executados neste Windows; não houve instalação.
