# Matriz e priorização v2

Registro único revisado: [registry.json](registry.json). [Matriz inicial/composições](../CAPABILITY_MATRIX.md). Ordem abaixo respeita dependências; os intervalos sobrepostos não permitem declarar vencedor por diferença pequena. Scores são juízos de potencial, não medição de rentabilidade.

|Ordem|ID/capacidade|Ação|VALUE|COST/RISK|PRIORITY|
|---|---|---|---|---|---|
|1|K02 Versões e disponibilidade de fundamentos|IMPROVE|[70.0, 90.0]|[35.0, 55.0]|[62.5, 82.5]|
|2|K01 Identidade histórica CNPJ/ISIN/classe|IMPROVE|[67.0, 87.0]|[48.0, 68.0]|[56.5, 76.5]|
|3|K03 Eventos e recebíveis reconciliados|AUGMENT|[67.0, 87.0]|[51.0, 83.0]|[52.0, 75.6]|
|4|K05 Validação de treino e labels por data|ADD|[73.0, 93.0]|[41.0, 61.0]|[62.8, 82.8]|
|5|K06 Inferência temporal e multiplicidade|AUGMENT|[71.0, 91.0]|[50.0, 70.0]|[58.7, 78.7]|
|6|K21 Viabilidade por capital e custos|IMPROVE|[68.0, 88.0]|[35.0, 67.0]|[57.5, 81.1]|
|7|K07 Diagnóstico de ranking e atrito|AUGMENT|[60.0, 80.0]|[35.0, 55.0]|[55.5, 75.5]|
|8|K04 Contrato de calendário e observação|VALIDATE|[55.0, 75.0]|[35.0, 55.0]|[52.0, 72.0]|
|9|K08 Teste diferencial de contabilidade|VALIDATE|[61.0, 81.0]|[48.0, 68.0]|[52.3, 72.3]|
|10|K09 Covariância e risco de cauda|RESEARCH|[56.0, 76.0]|[52.0, 72.0]|[47.6, 67.6]|
|11|K10 Fatores brasileiros como controle|RESEARCH|[57.0, 77.0]|[33.0, 65.0]|[50.4, 74.0]|
|12|K15 Incerteza preditiva e calibração|RESEARCH|[53.0, 73.0]|[56.0, 76.0]|[44.3, 64.3]|
|13|K14 Macro com vintages|AUGMENT|[39.0, 59.0]|[50.0, 82.0]|[32.7, 56.3]|
|14|K17 ARIMA/VAR/Kalman e baselines temporais|RESEARCH|[45.0, 65.0]|[49.0, 69.0]|[40.8, 60.8]|
|15|K20 Registro e contratos de dados|KEEP|[60.0, 80.0]|[20.0, 40.0]|[60.0, 80.0]|
|16|K11 Ranking relativo versus forecast|RESEARCH|None|None|None|
|17|K12 Value/quality/ranking com baixo giro|RESEARCH|None|None|None|
|18|K22 Relações, neutralização e features|RESEARCH|None|None|None|
|19|K16 RF/ExtraTrees/boosting baselines|RESEARCH|None|None|None|
|20|K13 Regimes causais para sizing|RESEARCH|None|None|None|
|21|K18 Redes temporais e Transformers|RESEARCH|None|None|None|
|22|K19 RL e notícias/LLMs|RESEARCH|None|None|None|

## Como ler as notas

0=nenhum valor demonstrável/baixo custo demonstrado;3=benefício material fundamentado/custo intermediário;5=alto valor no escopo/alto custo. A ponta superior de valor é a estimativa fundamentada; a inferior reduz1 ponto por incerteza. Custo usa estimativa e mais1 ponto; custo de dados não certificado usa0..5, sem fingir que é zero. Cada nota tem justificativa em registry.json. Pesos são exatamente os do mandato; sensibilidade calcula mistura valor/custo60/40,70/30,80/20 e cada peso de valor±20% renormalizado. Há sobreposição ampla: usar dependências e valor da informação. Econômicas ficam sem número pela falta de evidência pertinente, mantendo perfil ECONOMIC.

K03 é alto valor/alto custo documental. K02/K07 são incrementos menores com teste estreito. K20 já existe: seu score de utilidade não autoriza duplicar tracking ou substituir Core. NO_VERIFIED_ADVANTAGE econômico; garantias locais a preservar não são alegação de superioridade sobre produtos inteiros. Prevalência/gap/diferenciação UNKNOWN com justificativa; amostra por capacidade não mede mercado competitivo. Redundância permanece visível e alternativas semelhantes já agrupadas, sem desconto duplo.

## Vistas por categoria — mesmos IDs

|Vista|Fila de capacidades|
|---|---|
|Melhorias imediatas|K02,K01,K05,K06,K21|
|Novas análises|K07,K09,K10,K15,K17|
|Filtros/ranking|K01,K02,K05,K07,K11,K12|
|Fontes/datasets|K02,K01,K03,K10,K14|
|Ferramentas|K04,K06,K08,K09,K20|
|Features/estratégias|K22,K12,K11,K16,K13,K18,K19|
|Validação|K05,K06,K08,K15,K20|
|Risco/execução|K03,K04,K08,K09,K21|
|Referências|R51/R53 paraPIT;R11 paraCV;R09 parabootstrap;R16 paraIC;R02/R05 paraexecução;R07/R08 para risco;R56 parafatores|
|Composições|C02 validação;C01 dados+ranking;C03 risco+exposição|

C02 = K04+K05+K06+K08: rejeitar tempo inválido e comparar contabilidade. C01 = K01+K02+K03+K07: formar painel admissível e diagnosticar ranking. C03 = K07+K09+K10+K21: separar exposição e custos de informação incremental. Nenhuma combinação foi validada como estratégia; ablação remove uma peça de cada vez no mesmo painel futuro admissível. Falhas comuns: mesma fonte revisada, filtro de sobrevivência, custo omitido e parâmetro escolhido vendo o resultado.

Os seis contratos de fontes em registry.json separam cobertura, campos, relógios, licença, quota/custo, DATA_ACCESSIBILITY e DATA_PIT_QUALITY. Notas de acesso indicam acesso documental observado, não preço/cobertura de produção. Nenhum contrato certifica toda a história B3.
