# X01 — cobertura econômica observável

Unidade medida:800 linhas de execução de pagamentos da Fonte15, não800 empresas nem800 evidências independentes. Manifesto original `1c6410bebc9627d6dea8ae6ac4a9034823786fa47c48c26a8632c529c8560c46` preservado. Apenas inputs de eventos, metadados e bytes de fontes foram lidos; nenhum preço/retorno/avaliador congelado. Conferimos668 arquivos primários referidos. [Cobertura por ativo/emissor/data/campo](X01-coverage.json), [painel por evento](X01-panel-integrated.jsonl), [join que respeita cadastro vazio mais recente](X01-joincheck.json).

|Dimensão|Resultado|Limite econômico|
|---|---|---|
|Ativos|98 tickers nas800 linhas;123 no inventário de intervalos|Populações diferentes; não é universo admissível X05|
|Emissores|56 CNPJs candidatos no join parcial;357 linhas com candidato único|FCA2023 não cobre toda história, equivalência de ISIN/classe ou eventos intermediários|
|Datas|494 ex-datas,2018-07-04..2026-04-01; tabelas anuais anexas|Data do direito não é disponibilidade da informação nem recebimento|
|Campos|800 ISIN/brutos;750 líquidos de cenário;778 datas/known_on;770 available_on|Presença não prova correção de unidade/tributo nem caixa pessoal|
|Fonte|778 linhas têm todas as referências primárias verificáveis por hash|Hash não prova completude de eventos ou publicação histórica|
|Temporalidade|0 valores registrados available_on<=ex_date nesta população|Metadados caracterizam confirmação posterior; não habilitam feature de valor conhecido na ex-data. Não significa que pagamento posterior seja contabilmente inválido|
|Reconstrução condicional|750 linhas com líquido de cenário+data|Não certifica a sequência completa de direitos, caixa, classes ou custos|
|Cobertura contínua|1237 intervalos em evidence.json;cash_coverage=[]|0 atestações explícitas nesse campo. Auditoria mais ampla usa1248 incluindo11 adicionais; não misturar denominadores|
|Eventos societários|8 ações integradas no input;28 gaps no registro de auditoria preservado|São contagens de objetos distintos;8 não resolve automaticamente os28|
|Painel econômico certificado|0 linhas certificadas integralmente nesta revisão|Estado de certificação, não afirmação de que todas as800 estejam erradas|

DOC03 continua principalmente controle de rejeição:11 dos12 documentos sem ticker elegível. Não foi promovido a evidência de painel econômico.

## Cadeia de admissibilidade

IDENTIDADE: ticker→CNPJ/ISIN/classe com início/fim efetivos e documento já disponível; mudança de ticker não é novo emissor. PIT: competência, versão, recebimento e corte de decisão separados; faltantes não são preenchidos com versão futura. EVENTOS: inventário contínuo positivo/negativo por intervalo, além dos documentos que contêm eventos. VALORES: unidade pré/pós-split, direito, capital emitido versus autorizado e frações. CUSTOS/RECEBIMENTOS: bruto/líquido condicionado, data confirmada, crédito negociável versus liquidação, arredondamento e custo explicitamente assumido.

O painel novo torna cada bloqueio visível por linha. Não altera Fonte15 nem converte imposto modelado em fato pessoal. Nenhuma nova certificação jurídica/fiscal foi realizada; usamos apenas as classificações históricas preservadas. O futuro confronto pode usar cenários de custo explícitos para pesquisa condicional, mas não declarar lucro pessoal sem informação correspondente.

## Único próximo recorte

TOTS3/BRTOTSACNOR8, intervalo2020-04-01..2020-07-01 já exigido no inventário, contendo split3:1 em2020-05-04 e crédito2020-05-06. A escolha usa uma fronteira de unidades/tempo e fonte já rastreada, não desempenho. Há16 pagamentos TOTS3 no inventário total com líquido de cenário+data e fontes, mas isso não cobre automaticamente este intervalo.

Próxima ação: reconstruir esse **único intervalo ponta a ponta**, começando pela identidade/PIT vigente e pela atestação do inventário completo de eventos. Critério de encerramento: todos os campos necessários têm evidência e convenção explícita, ou um bloqueio documental individualizado impede a linha. Sem retorno, sem reabrir hipótese antiga, sem extrapolar para todas as ações. Só então expandir cobertura ou alimentarX02 com o caso real.
