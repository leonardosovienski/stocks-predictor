# Registro da primeira etapa — histórico

Este relatório preserva a entrega A–F anterior às correções de contexto e à autorização de publicação. Contagens, permissões e testes abaixo são históricos. O estado da continuação está no [fechamento da revisão](README.md).

# Auditoria Stocks — corte 15/09/2026

## A. Resultado e autorização

Autorização atual: auditoria e correções com testes; preservar dados e protocolos,
sem publicar nem operar. Isso substitui a restrição original de somente leitura
apenas para as correções e testes autorizados. Não iniciou nova pesquisa econômica.

Stocks está em main, 3066321e599ee15dd0ace4167d2791545ce6eb95, checkout limpo ao
final. CAIN está em checkpoint/conversa-v2-parcial-20260914,
24f784c5dde1fa66c262ad5899f4fd8d02526adf, com duas alterações locais desta rodada.
Corte mecânico final em selection-verification.json. Leituras não são snapshot
atômico dos ambientes. Nenhum remoto ou instalação principal foi atualizado.

H17 foi observada e permanece inconclusiva. H18/H19 foram executadas em Discovery,
sem promoção; H19 contínua não calculou o histórico real. H20 não demonstra vantagem
incremental líquida. H21 tem resultado histórico condicionado. H22 foi rejeitada
nas comparações registradas. Não há novo lucro validado, operação ou Proof.

## B. Manifesto e alcance

selection-verification.json lista 47 fontes selecionadas, caminhos e SHA256,
85 ocorrências literais. Isso verifica cobertura do inventário, não compreensão.
derived-ledger.json preserva os registros nativos H1–H19/H21 e as 75 entradas R7,
22 claims e 24 frentes; IDs de arquivos, trials e hipóteses não são intercambiáveis.
r3-reference-reconciliation.json verifica 31/31 hashes dos recibos históricos.
pending-coverage.json contabiliza fontes não integralmente examinadas e impacto.

Fontes principais relativas a C:/STOCKS/stocks-predictor:
trials.json, trials_v2.json; docs/research/2026-09-07-prior-hypotheses-review.json;
docs/research/2026-09-07-h17-{registration.md,discovery-protocol.json,first-observation.md,observations.jsonl};
research/session-20260907/deliverables/h17-{first-observation,corrected-observation,correction-and-integrity,reproduction-verification}.json;
docs/research/2026-09-07-{value-observations.jsonl,value-results.md,reorganization-results.md,profit-validation-results.md,h19-continuous-decision.json};
docs/research/2026-09-08-h20-{results,profit-test-results,remediation-results}.md;
docs/research/2026-09-09-h21-{results.md,observations.jsonl,forward-plan.json};
docs/research/2026-09-10-r5/{results.json,README.md,reproduction.json};
docs/audit/2026-09-10-r7/{current.json,baseline-v2.json}.

Leitura anterior desta mesma auditoria conferiu os 12 bancos e 1448 entradas do
pacote restaurado H20; não houve nova execução científica. Os 794 registros de
direitos de fontes não equivalem a 794 revisões semânticas; 792 não têm direito
de item verificado e dois identificam licença da base. Essa cobertura não foi
convertida em aprovação dos documentos primários ou de seu uso externo.

Não foram abertos resultados protegidos nem coortes novas. Não foram consultados
outros predictors para transferir conclusões. CAIN foi consultado somente para
proveniência, seleção documental e o erro conhecido de representação Stocks.

## C. Ledger e scorecards

H1 momentum 12-1; H2 baixa volatilidade; H3 combinação não executada; H4 sizing
inverso à volatilidade; H5 reversão 21 dias; H6 momentum 6-1; H7 ROE; H8 momentum
com baixa volatilidade; H9 baixa alavancagem; H10 ROE com baixa alavancagem;
H11 momentum com proventos aproximados; H12 margem; H13 crescimento da receita;
H14 proximidade da máxima 52 semanas; H15 volume relativo; H16 virada do mês.

Há 15 trials legados e H3 não executada. Relatórios preservam não comprovação;
trials_v2 tem H1 JUDGED/NOT_SUPPORTED e demais estados UNKNOWN. A revisão
secundária preserva NOT_SUPPORTED e qualifica confiabilidade. Não preencher
UNKNOWN automaticamente. H5 é negativa sob medição legada; H4/H16 negativas
fracas; H7/H8/H14 sinais positivos limitados; H11 aparente positivo com retorno
total não verificado; demais inconclusivas. Código legado usa fechamento,
reposição diária implícita de pesos e benchmark assimétrico, limitando a inferência.

H17: 05:27:41.850382+00:00 e 05:33:31.134125+00:00 de 07/09/2026; códigos
00a4a13b649e23a2af1200d4ea8ab69f5ed1094b e
4f487098e702004a88f02fe65d62a008c6df618b. Protocolo
H17-DISCOVERY-PRICE-DIAGNOSTIC-1. Mantém 96 meses previstos, 94 elegíveis,
5399 células; completos 56→59, medidos 5348→5352, faltantes 51→47,
selecionados faltantes 15→14. IC Spearman médio -0.0131890045→-0.0132013727.
Spread mensal em fração -0.00252220783→-0.00161341221; multiplicar por 100
converte para -0.252221→-0.161341 pontos percentuais, apenas aritmética de unidade.
Quatro conflitos mecânicos corrigidos, 5395 desfechos preservados; estados
INCONCLUSIVE_DATA_QUALITY iguais. IC usa sinal de accruals invertido e retorno
por preço; não é intervalo de confiança. O spread usa meses completos, sujeitos
a seleção pela disponibilidade futura; faltam dividendos/JCP e P&L executável.

Sete células ausentes H17 coincidem por asof, ISIN, entrada e saída com reparos
posteriores H18: QUAL3, NATU3, HGTX3, PSSA3, AMER3, PETZ3, HAPV3. Isso sustenta
revisar compatibilidade de fontes, não transplantar resultados. Nenhuma nova
observação H17 foi criada. Reproduções relatadas nos recibos são históricas e
não replicações independentes. Denominador adaptativo completo permanece desconhecido.

H18 lucro/preço e H19 patrimônio/preço: quatro configurações mensal/trimestral,
93/93 meses e 31/31 trimestres após reorganizações. NO_PRIORITY_UPGRADE em todas.
Spread bruto final em p.p./mês: H18M 0.5587; H18Q 0.4094; H19M 0.6259; H19Q
0.5988. Divisão trimestral por três é aritmética. Mudança para direitos societários
altera estimando; não somar versões. Os 12 intervalos descritivos posteriores
incluem zero. H19Q após 72 pb: +0.359 p.p./mês, intervalo [-0.658,+1.435].
Bootstrap em blocos de um ano, 10000 repetições, pós-descoberta, sem correção por
busca desconhecida. H19 contínua implementada/testada, full_history_executed=false,
net_profit_brl=null, INCONCLUSIVE_DATA_QUALITY/NO_GO_UNVALIDATED_NET_PROFIT.

H20: valor, valor+rentabilidade e buffer; redução de substituições não mede giro
financeiro. Incremento médio trimestral +0.197 p.p., intervalo [-3.61,+3.92],
inconclusivo. 372/384 compras iniciais calculadas e 12 bloqueadas não são 384
backtests completos. Motor contínuo e testes controlados não certificam caixa real.

H21: BOVA11 buy-and-hold, 4 especificações/8 avaliações em um histórico,
2050 preços entre 02/01/2018 e 01/04/2026. Lucro histórico condicionado a custos,
eventos e tributação modelados; não alpha, perfil pessoal ou promessa prospectiva.
Plano forward 2026–2027 não é observação. Não iniciar coleta nesta rodada.

H22: regra mensal de média de dez meses, compra/caixa contra hold pareado;
24 avaliações planejadas,22 calculadas,2 inviáveis por despesas,11 comparações
negativas. H22_REJECTED_IN_REGISTERED_SCENARIOS; HISTORICAL_HOLD_PROFIT_CONDITIONAL;
FULL_OR_FUTURE_PROFIT_NOT_VALIDATED. Janelas sobrepostas não são confirmações independentes.

RJ: famílias preditivas/descritiva arquivadas, evidência sintética/mecânica;
OSS: cinco protótipos stdlib, X05 econômico não executado. Não comparáveis aos
resultados reais H17–H22. Não existe vencedor universal demonstrado entre modelos.

## D. Conflitos e frases permitidas

- H17 nunca executada: somente descreve nota anterior; contradita como estado atual.
- H18/H19 sem observação: histórico anterior; ledgers posteriores mostram execução.
- Código 2: audit_dfp_readiness.py retorna não aprovação/erro tratado; H19 continuous
  devolve BLOCKED_MISSING_EVIDENCE. Não é aprovação, não descreve H17, lucro não é zero.
- H5 “IC cruza zero / negativo”: rótulo combinado, não erro aritmético provado;
  intervalo [-0.6406,-0.1009] está abaixo de zero. Retificada a acusação anterior.
- H20 arquivos faltantes: pacote restaurado verificável, não desculpa para
  converter lacuna de caixa em falha já corrigida.
- CI/testes aprovados: sustentam engenharia naquele código/cenário, não lucro.
- Snapshot/Bundle recebidos: corpos e metadados têm coberturas distintas; recibo
  QA não demonstra principal nem todas as hipóteses. Referência não materializa arquivo.
- CAIN A02 falhou em contexto/resposta histórica. Seleção ampliada não apaga essa
  falha nem demonstra correção da resposta gerada.

Claims C01–C22 e overlays estão preservados integralmente no ledger derivado.
Erros anteriores resolvidos não foram reabertos sem evidência nova. Pendências
R7 I10–I14/I16 continuam explicitadas, com significado da revisão atual.

## E. Próximas verificações mínimas

1. H17: confrontar os sete reparos posteriores com entradas e estimando congelados;
   aceite é correspondência de fontes, identidade, data e regra, mantendo duas
   observações intactas. Nova medição teria identidade/revisão própria e protocolo.
2. H19/H20: reconciliar 50 líquidos faltantes, incluindo 22 datas, 28 registros
   societários e 1248 intervalos não certificados na revisão R7; fontes completas
   antes de repetir quatro avaliações fixas. Não inferir que ausência vale zero.
3. CAIN: QA separado de contexto e resposta, candidata/corpus identificados e
   rubrica externa. Aceite exige fidelidade temporal, unidades e abstenções;
   publicação/admissão continua fora da autorização desta rodada.
4. H21: perfil pessoal incompleto e observação futura; não substituir prazo,
   custos, tributação ou risco por defaults. Verificar recibo prospectivo elegível
   quando existir, sem antecipar a janela nem parar ao encontrar positivo.
5. H22: manter rejeição registrada. Nova regra requer novo protocolo, não otimização
   retroativa. Nenhuma nova família foi criada.

Dimensionamento confirmatório precisa efeito mínimo, variância/dependência,
unidade e precisão/poder; parâmetros não estabelecidos não foram inventados.
As lacunas documentais precedem treino, ML ou nova busca adaptativa.

## F. Correção local e CAIN

Somente tools/hypothesis_sources.json e docs/COBERTURA_PROJETOS_20260913.md,
em C:/CAIN/projeto, foram alterados. Oito fontes primárias/documentais acrescentadas;
39 fontes anteriores e projetos alheios intactos. Não alterou pacote Stocks,
seletor/prompt/modelo CAIN, permissões, bancos ou configuração pessoal.

13 testes passaram; primeira tentativa 8 passed/5 setup errors por pasta ausente,
recuperada sem reduzir testes. 47 fontes/85 ocorrências conferidas, duas saídas
H17 iguais aos hashes do ledger, 31/31 recibos R3. Testes usam fixtures e bancos
temporários; não houve exportação Stocks, ingestão ou inferência. Git diff --check
passou. Suíte integral Stocks/Linux não executada: nenhum pacote foi alterado.

Conhecimento documental: oito novas fontes listadas no inventário e seus hashes.
Material de avaliação: evaluation-only.json, cinco casos conhecidos, fora do corpus.
Reserva futura depende de avaliador separado e freeze; não se alega cegamento.

Sabemos que há estudos reais, negativos e inconclusivos, correções rastreáveis e
engenharia demonstrada em escopos concretos. Não sabemos lucro futuro/pessoal,
efeito líquido confirmatório ou fidelidade atual da LLM. Podemos afirmar apenas
conclusões condicionais acima. A menor próxima verificação é de fonte/revisão e
contexto, não um novo modelo. Auditoria encerrada no escopo conhecido, com pendências
contabilizadas; não significa projeto integralmente validado ou todos os erros extintos.
