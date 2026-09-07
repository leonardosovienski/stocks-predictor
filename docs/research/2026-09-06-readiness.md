# Stocks — primeira entrega científica, técnica e econômica

Data: 6 de setembro de 2026, America/Sao_Paulo. Leituras registradas em UTC em 7 de setembro. Escopo exclusivo: `leonardosovienski/stocks-predictor`.

**Decisão: CONTINUE uma auditoria curta de dados; PAUSE a execução de H17–H19. Modo: DISCOVERY / DATA FEASIBILITY. Nenhum alpha confirmado ou capital autorizado.**

Com capital informado de **R$ 5.000–10.000**, a prioridade é resolver erros que tornariam a próxima rodada cientificamente ambígua e avaliar uma operação quase sem despesas fixas. A primeira entrega não recomenda executar as três hipóteses só porque existe cobertura. Os cinco critérios anteriores de H18 não bastam: foi encontrado um problema de vinculação entre versão e data de publicação nos dados reais.

Esta entrega foi produzida antes de alterações na implementação científica, novas famílias substanciais ou avaliação de desempenho de H17–H19. Todos os resultados históricos abaixo foram lidos de artefatos já existentes. Não foram recalculados.

## A. Estado — itens 1–4

### 1. CURRENT_SCIENTIFIC_STATE

| Campo | Reconstrução verificada |
|---|---|
| Estado oficial | `CLOSED_FOR_H1_THROUGH_H16`, com adendo para H17–H19 |
| Contagem real | **15** trials julgadas: H1, H2, H4–H16. H3 não foi executada; “16/16” é erro de contagem |
| CURRENT_CLOSED_FAMILIES | Momentum 12–1 e 6–1; baixa volatilidade; sizing 1/vol; reversão; interseções momentum/vol e ROE/alavancagem; ROE; alavancagem; momentum com proventos; margem; crescimento; proximidade da máxima; volume; virada do mês |
| CURRENT_OPEN_TRIALS | H17 accruals, H18 E/P, H19 B/M, pré-registradas, sem resultado real no ledger |
| Lacres vigentes conferidos no código | H17 `e6cf9bd7454750c3`; H18 `cbea4d3c98ac3422`; H19 `d96753f2af7b39a6` |
| CURRENT_CONFIRMATORY_RESULTS | Nenhuma evidência confirmatória positiva identificada; os julgamentos históricos são encerramentos locais, não demonstração de lucro executável |
| RJ | Arquivada, tabelas reais vazias; não abrir frente de pesquisa |
| Estado comercial | `NOT_A_PRODUCT`; nenhuma decisão paper registrada |
| Alocação recomendada | Domínio `WATCH`; dados essenciais `CONTINUE`; novas rodadas `PAUSE`; nenhuma frente Proof ativa |

### 2. Inconsistências documentais

- `STOCKS_CURRENT_STATE.md` e o adendo do freeze mostram os lacres de 4/set, superados pelo re-pré-registro de 6/set no HANDOFF. O manifesto do freeze ainda tem `active_hypotheses: []`.
- `trials.json` contém 15 registros; `trials_v2.json`, apenas 8, com denominador 8. O comando oficial `migrate_trials_schema.py --check` devolveu **DRIFT**. Tratar o v2 como fonte atual perderia sete tentativas.
- O ledger repete `2018-01-01 → 2026-07-03` para todas as trials, inclusive H11, cujo protocolo e relatório restringem a execução a 2018–2022. Metadados de janela não representam fielmente a amostra efetiva.
- Os relatórios afirmam execução na abertura D+1. O `walk_forward` calcula fechamento a fechamento a partir do fechamento usado no sinal. `execution.price` e `purge_embargo_months` não governam esse motor.
- “O mesmo viés afeta estratégia e benchmark, então não importa” não é uma conclusão válida: carteiras e turnovers diferem. A direção do efeito sobre a diferença precisa ser demonstrada, não presumida.
- H14–H16 têm relatórios íntegros na máquina local, ausentes do GitHub. Foram localizados e lidos; não precisam ser regenerados.
- `AGENTS.md`/design histórico proíbem pacote Core; contratos atuais usam wheel 3.2.0. `pyproject.toml` ainda descreve RJ como linha ativa. São resíduos de documentação, não mudanças científicas autorizadas.

### 3. Estado técnico real / CURRENT_INFRA_BLOCKERS

Base remota auditada: [commit d48d05d](https://github.com/leonardosovienski/stocks-predictor/commit/d48d05dc590c7e14a9186e7097c048c3020a6a53). Checkout operacional local: `0e99bc8b23bc4e5eea389fd1dfee10744c4fc362`, com arquivos auxiliares não versionados. Ele permanece intacto.

**Validação nesta sessão: 374 testes passaram em 81,27 s**, Python 3.13.14, wheel oficial Core 3.2.0 carregada em diretório isolado. Nenhum venv ou atualização global. O Core global do operador é 3.1.0; portanto executar ali não equivale ao ambiente atual do CI. [CI do commit auditado: sucesso](https://github.com/leonardosovienski/stocks-predictor/actions/runs/34061369536).

Bloqueios científicos concretos, apesar da suíte verde:

1. **DFP: a ingestão descarta `VERSAO` e associa valores à primeira `DT_RECEB` do exercício.** No ZIP oficial 2023, 80 combinações companhia/exercício da DRE consolidada têm recebimento da versão efetiva posterior à primeira entrega. Exemplo no banco: ENGI11, receita da versão 3, recebida em 15/mar/2024, associada a 12/mar/2024. Não foi verificado se todos os valores individuais mudaram; o vínculo de provenance exigido para afirmar PIT está ausente.
2. **Unidades monetárias erradas.** A DRE oficial usa ponto decimal e `ESCALA_MOEDA`; o parser remove o ponto e ignora a escala. ABEV3: `79736856.0000000000`, escala `MIL`, corresponde a R$ 79.736.856.000; o banco tem `7,9736856e17`, fator **10.000.000** maior. Ratios entre contas igualmente escaladas podem cancelar o erro; E/P e B/M em unidades econômicas não. O ZIP contém tanto `MIL` quanto `UNIDADE`, impedindo presumir um fator comum para todo o universo.
3. **Base temporal de ações no FRE.** BBAS3 tem 5.730.799.931 ações derivadas, documento recebido em 16/mai/2024 e rótulo de referência 31/dez/2023. A função atual aplica novamente o split de abril e devolve 11.461.599.863 em 31/mai/2024. É um forte caso de dupla aplicação: rótulo do formulário não prova a data-base da quantidade. A [Carta Anual do BB, p. 38](https://www.bb.com.br/docs/portal/bbbi/cartaanual25.pdf) confirma o desdobramento 1:2 em abril de 2024. A data do banco difere um dia da data societária citada; isso também pede reconciliação.
4. **Retorno total não validado.** A tabela de proventos contém 5 registros nos anos 2201/2919 e 761 chaves ticker/data com mais de uma linha. Duplicidade de chave não prova duplicidade econômica, pois podem existir parcelas legítimas; requer conciliação por evento. O código divide montantes por free float e usa pagamento como data-ex, além de misturar classes. Não usar H11 como controle de retorno total correto.
5. **Construção de carteira:** pesos fixos aplicados à média de retornos diários representam manutenção dos pesos todos os dias; isso não equivale a manter quantidades compradas até o rebalance mensal. Os custos não cobrem esse rebalance diário implícito. Benchmark renormaliza por papéis com cotação enquanto a estratégia mantém zeros para ausentes. São divergências mecânicas que precisam de controles sintéticos, não de nova performance real.

### 4. CURRENT_NEXT_IRREVERSIBLE_DECISION

Executar ou observar pela primeira vez o resultado de H17/H18/H19. **Não executada.** Antes disso: corrigir a cadeia documental em dados derivados, fechar execução/retorno/custos, fixar ordem e denominador, identificar dataset e código por hash, registrar a decisão e seu stopping rule. Fixar ordem H17→H18→H19 é uma proposta independente de performance, não uma ordem já congelada. N nominal das três seria 16/17/18, se todas forem executadas nessa ordem; o search efetivo pode ser maior.

## B. Evidência — itens 5–13

### 5. CURRENT_EVIDENCE_BUDGET / EVIDENCE_BUDGET

| Compartimento | Estado e limites |
|---|---|
| Historical Exploration | `restricted`: reutilizável como descoberta explicitamente adaptativa; 2018–2026 já informou numerosas decisões |
| Validation | `partially_consumed` no sentido de histórico exposto; nenhum split independente formalmente protegido identificado |
| Final Test | Histórico existente `consumed` para a cadeia geral de pesquisa; nenhum conjunto final intocado identificável por manifesto. H17–H19 não vistas não transformam a mesma janela em novo holdout |
| families_exposed | 15 candidatos julgados, com múltiplas interseções e escolhas posteriores; RJ somente sintética |
| adaptive_decisions_after_observation | Documentadas qualitativamente: H8 após momentum/low-vol, H10 após ROE/leverage, H11 após falhas/retorno total, abertura sequencial de novas famílias. Contagem exata desconhecida |
| Temporal OOS | Nenhuma reserva com data de corte/configuração e decisões pré/pós-observação demonstrada |
| Prospective | `not_started` no banco auditado; início, config hash, dataset definition hash: ausentes; zero observações identificadas nessa cadeia |
| Shadow | `not_started`; `decisions=0`; configuração/início ausentes |
| CURRENT_PROTECTED_EVIDENCE | O resultado ainda não observado de H17–H19 e futuras observações realmente prospectivas. Nenhum acesso ao desempenho das três nesta sessão |

Não é possível certificar ausência de observações em toda conversa ou máquina anterior. A conclusão de não execução é sustentada pelo ledger, HANDOFF e ausência de registros locais correspondentes, sem alegar onisciência.

### 6. CURRENT_SEARCH_BUDGET / SEARCH_BUDGET

Mínimos reconstruídos, sem zerar a busca histórica:

| Dimensão | Registro |
|---|---|
| hypothesis_families_tried | 15 candidatos nomeados executados, com famílias correlacionadas; não são 15 apostas independentes |
| feature_families_tried | Preço/momentum; volatilidade; reversão; ROE; alavancagem; margem; crescimento; máxima 52s; volume; calendário; interseções derivadas |
| data_sources_evaluated | B3 COTAHIST; CVM DFP, FRE/dividendos; IPE em infraestrutura histórica; verificações terceiras de splits. Total global exato desconhecido |
| target_variants_tried | Retorno só-preço; retorno com proxy de proventos; timing de exposição; sizing |
| horizon_variants_tried | Sinais 21/126/252 pregões, fundamentos anuais/YoY, rebalance mensal, calendário −1/+3; total adaptativo desconhecido |
| universe_variants_tried | Regra top-60 PIT compartilhada, universos efetivos contábeis menores; não confundir estes com 60 ativos sempre elegíveis |
| regime_definitions_tried | Não contabilizado; nenhuma série canônica de resultados por regime encontrada |
| transformations_tried | Ranks/quintis, inverso de vol, razões, interseções; contagem exata desconhecida |
| model_families_tried | Regras determinísticas; nenhum ML confirmado no ledger |
| hyperparameter_trials | Não reconstruível integralmente; uma configuração registrada por candidato, sem prova de ausência de buscas externas |
| portfolio_rules_tried | Quintis superior/inferior, equiponderado, pesos 1/vol, filtros 40%→metade, exposição em virada do mês |
| decision_rules_tried | IC95%; DSR pós-H1; drawdown adicional H4; regras de entrada/saída |
| economic_filters_tried | Gate econômico existe mas não é consumidor do paper nem evidência avaliada em dados reais |
| cost_models_tried | Flat por lado com evolução para custo por turnover; H16 transições caixa/posição. Stress real não sistematicamente arquivado |
| human_or_agent_pivots_after_results | Múltiplos documentados, total desconhecido. Não representar N=15 como contabilidade completa do adaptive search |

Nesta sessão: 0 novas hipóteses de retorno, 0 trials reais, 0 varreduras de parâmetros, 2 ZIPs de 2023 (DFP/FRE, cerca de 21,7 MB) para auditoria de dados, controles mecânicos sem P&L. Descobertas de bugs não são novas tentativas de alpha.

### 7–12. Histórico científico reconstruído

Contrato comum: universo B3 top-60 por liquidez dos 126 pregões anteriores, histórico mínimo 252, long-only; carteira mensal de quintil salvo H4/H8/H10/H16; custo assumido 18 bps por lado. Modelos determinísticos, sem treino; target econômico diferença de Sharpe sobre o benchmark. Dados de preços têm event_time=pregão; fundamentos têm event_time=exercício e, nas hipóteses julgadas, known_at estimado em +90 dias. As três novas usam data observada, com o defeito de versão apontado acima. Horizonte de manutenção mensal; retornos de avaliação diários. Não há estimativa convincente de poder para o efeito mínimo de interesse.

| H | Mecanismo / configuração distinta | n dias | IC95% diff-Sharpe; DSR | Classificação de evidência nesta auditoria |
|---|---|---:|---|---|
| H1 | Momentum 12–1; continuação de informação/preços | 2092 | [−0,3192; 0,2933]; sem DSR original | INCONCLUSIVE_METHOD; efeito não demonstrado |
| H2 | Baixa vol 252d; restrições de risco/atenção | 2092 | [−0,2850; 0,3958]; 0,7092 | INCONCLUSIVE_METHOD; dividendos omitidos podem prejudicar |
| H4 | 1/vol; construção/risco, não informação nova | 2092 | [−0,0297; 0,0742]; 0,6843 | LIKELY_NEGATIVE para ganho relevante no desenho testado; não prova ausência universal |
| H5 | Compra perdedores 21d; reversão/liquidez | 2092 | [−0,6406; −0,1009]; 0,1274 | CONFIRMED_NEGATIVE **no estimando só-preço testado**; não prova sobre retorno total |
| H6 | Momentum 6–1 | 2131 | [−0,3526; 0,3256]; 0,4565 | INCONCLUSIVE_METHOD |
| H8 | Momentum alto ∩ baixa vol; combinação | 2131 | [−0,1508; 0,4138]; 0,6050 | POSITIVE_EXPLORATORY fraco, já encerrado |
| H7 | ROE alto; qualidade | 1826 | [−0,2149; 0,4724]; 0,5795 | POSITIVE_EXPLORATORY fraco + INCONCLUSIVE_DATA_QUALITY |
| H9 | Alavancagem baixa | 1826 | [−0,3724; 0,1602]; 0,3479 | INCONCLUSIVE_DATA_QUALITY |
| H10 | ROE alto ∩ alavancagem baixa | 1826 | [−0,3820; 0,2029]; 0,3661 | INCONCLUSIVE_DATA_QUALITY |
| H11 | Momentum 12–1 com proxy de proventos, 2018–2022 | 1218 | [−0,0378; 0,7914]; 0,8430 | POSITIVE_EXPLORATORY aparente + INCONCLUSIVE_DATA_QUALITY; não replicado |
| H12 | Margem líquida alta | 1826 | [−0,3356; 0,1848]; 0,1952 | INCONCLUSIVE_DATA_QUALITY |
| H13 | Crescimento de receita YoY | 1597 | [−0,4562; 0,1611]; 0,2598 | INCONCLUSIVE_DATA_QUALITY; janela efetiva ainda menor |
| H14 | Preço perto da máxima de 252d | 2131 | [−0,2424; 0,3864]; 0,3249 | POSITIVE_EXPLORATORY fraco, encerrado |
| H15 | Volume 21/252d | 2131 | [−0,2527; 0,3129]; 0,2826 | INCONCLUSIVE_METHOD |
| H16 | Último + 3 primeiros pregões; fluxo/calendário | 2132 | [−1,4044; 0,2011]; 0,0052 | LIKELY_NEGATIVE; IC ainda cruza zero |
| RJ | Eventos de distress, 8 famílias previstas | 0 reais | Somente controles sintéticos | INCONCLUSIVE_INFRA_FAILURE/DATA; arquivada |

**CURRENT_INCONCLUSIVE_RESULTS:** a maior parte dos candidatos, pelas limitações acima; baixo poder é plausível, mas não foi demonstrado por power analysis no efeito relevante. **CURRENT_POSITIVE_EXPLORATORY_RESULTS:** H11, H7, H8 e H14 têm diferenças pontuais favoráveis em artefatos antigos, sob busca adaptativa e limitações. **Positivos replicados, confirmatórios, prospective e shadow: nenhum identificado.** Todos os 15 vereditos oficiais continuam `NOT_SUPPORTED`; a taxonomia analítica desta tabela não altera encerramentos nem legitima reabertura automática.

Meta-análise: recombinar fatores fracos já falhou duas vezes; reduzir janela de momentum não resolveu; sizing não mostrou incremento robusto; fontes contábeis introduziram fragilidade de dados; total return aproximado criou um resultado visualmente atraente que exige auditoria ainda mais forte. Não usar o Sharpe máximo como seleção. H5 não autoriza inverter o sinal. Qualquer reabertura exige informação material e registro próprio; não será feita neste ciclo.

### 13. Coortes protegidas

Nenhuma coorte prospectiva iniciada foi encontrada no banco (`decisions=0`). A ingestão de dados históricos em 2026 não cria evidência prospectiva. No ciclo atual, os valores dos sinais das novas hipóteses só são usados internamente por contagem de cobertura; nenhuma ordenação, associação a retorno, seleção ou métrica de desempenho é exibida.

## C. Dados — itens 14–18

### 14. CURRENT_DATASETS

Banco operacional: 257.163.264 bytes; SHA-256 `a22739794ba4a43a11544338d4a91e14cb6a0b1f7b132ab460f96d3359f63cf4` na leitura inicial.

| Dataset | Disponibilidade medida | Qualidade / limitações |
|---|---|---|
| COTAHIST | 1.149.872 linhas, 1.784 tickers, 2.647 datas; 04/jan/2016–27/ago/2026; 11 ZIPs anuais locais | Fonte negociada, não total return; mínimo de histórico e exclusão por quarentena; lote padrão, sem validação de execução no fracionário |
| Adjustments | 43: 40 splits + 3 grupamentos | Trilha humana preservada; data/base e cobertura completa não certificadas |
| Quarantine | 2.227 registros; 2.184 sem resolução | Não são 2.184 ativos; efeitos de seleção precisam ser auditados. `resolved_at` atual pode afetar universos passados |
| DFP | 733 linhas em 124 tickers com lucro; 718 FCO; 716 accruals/123 tickers | 2018–2026 por fonte; versão/escala problemáticas; mapa por nome, sem security master bitemporal |
| FRE ações | 846 linhas/126 tickers | Contagem derivada de free float/percentual, data observada; data-base do capital e classes/units pendentes |
| Fundamentals total | 1.579 linhas; 100% com known_at | Preenchimento integral confirmado; não equivale a PIT íntegro |
| Dividends | 2.384 linhas/105 tickers | Datas econômicas de 2015 a 2022 mais anos inválidos; ausência recente; proxy pagamento/ex; denominador e duplicidades pendentes |
| Paper/forward | 0 decisões; 1 run histórico; 60 linhas de snapshot | Sem amostra operacional de fills, custos, slippage ou resultado realizado |

### 15–17. PIT/known_at, CURRENT_DATA_GAPS e information hierarchy

Cobertura documentada no HANDOFF: 104 datas, mediana universo 60; H17 56, H18 49,5, H19 53; 12/13/13 datas vazias. Essas medianas medem disponibilidade, não estabilidade nem N independente. A checagem desta sessão usa conexão SQLite `mode=ro`, evitando a migração/escrita que o entrypoint original de cobertura permite ao abrir `db.get_connection()`.

Hierarquia atual: (1) corrigir informação PIT com versão, moeda, unidade e base de ações; (2) reconstruir proventos/eventos por instrumento; (3) medir alvo e carteira executáveis; (4) turnover, quantidades inteiras e fracionário; (5) somente então testar complexidade de modelo. O gargalo atual é qualidade/execução, não ML.

### 18. Novas fontes que podem mudar o information set

| Fonte | Profundidade, PIT e revisions | Custo / automação / valor |
|---|---|---|
| [DFP oficial](https://dados.cvm.gov.br/dataset/cia_aberta-doc-dfp) com versão | Histórico publicado desde 2010; reapresentações semanais; casar CNPJ+exercício+VERSAO. O ZIP atual pode não conter todos os valores antigos | Público, download já viável; alto valor para validar H17 existente, sem afirmar vantagem proprietária |
| [ITR oficial](https://dados.cvm.gov.br/dataset/cia_aberta-doc-itr) | Histórico desde 2011, trimestral, reapresentações; separar trimestre de acumulado e versão de publicação | Dado público, esforço moderado/alto; candidato a informação mais tempestiva, somente backlog por enquanto |
| [IPE oficial](https://dados.cvm.gov.br/dataset/cia_aberta-doc-ipe) | Histórico desde 2003, documentos/eventos por entrega; texto exige rótulos e identificação de eventos | Pode permitir eventos e divulgação sem varrer mercados externos; maior esforço de curadoria, backlog |
| [FRE oficial](https://dados.cvm.gov.br/dataset/cia_aberta-doc-fre), capital/classes/eventos | Dados estruturados com documentos; data de referência não basta para base do número de ações | Reutiliza fonte pública, mas é necessário provar completude por versão/instrumento e custo de reconstrução |
| Eventos oficiais de emissor/B3 | Datas-ex, pagamentos e classes; profundidade/automação integral ainda não verificada | Maior valor para retorno executável; não contratar fornecedor neste capital sem justificar custo |

Fontes públicas são acessíveis, mas não constituem automaticamente uma vantagem informacional. Consenso de analistas, intraday, opções e dados pagos ficam no backlog por custo e tempo de validação. Não houve pesquisa substancial fora de Stocks.

## D. Economia — itens 19–23

### 19–20. CURRENT_ECONOMIC_STATE e MINIMUM_ECONOMICALLY_INTERESTING_OUTCOME

Capital: **R$ 5 mil–10 mil, confirmado pelo operador**. Lucro anual mínimo e horas aceitáveis: não informados. Cenários abaixo são aritmética, não projeção de retorno.

| Edge anual incremental líquido de negociação, antes de custo fixo | R$ 5.000 | R$ 10.000 |
|---:|---:|---:|
| 2% | R$ 100 | R$ 200 |
| 5% | R$ 250 | R$ 500 |
| 10% | R$ 500 | R$ 1.000 |

Um serviço de R$ 50/mês custaria R$ 600/ano: 12% do capital de R$ 5 mil ou 6% do de R$ 10 mil, antes de gerar benefício. Uma hora mensal avaliada ilustrativamente em R$ 50 soma outros R$ 600/ano. Não foi atribuída essa preferência de tempo ao operador.

**Gate provisório para alocação de pesquisa**, não critério científico: buscar plausibilidade de pelo menos R$ 500/ano incrementais depois de todos os custos e contra alternativa passiva comparável; isso exige 10%/5% incrementais na faixa de capital, mais os custos fixos e tempo. É exigente e pode levar a `REAL_EDGE_BUT_ECONOMICALLY_TOO_SMALL`. Para aprofundar substancialmente, esse piso precisa ser confirmado ou substituído por preferência explícita. Até lá, teto de aquisição paga zero e trabalho de viabilidade curto.

### 21–22. Efeitos, custos, capacity/liquidity/turnover

Não existe estimativa de lucro líquido futuro confiável no estado atual. A hipótese de que pequenos ganhos seriam consumidos por custos é economicamente plausível; não foi medida com fills reais.

A premissa versionada é 0,18% por lado. Uma substituição integral mensal implicaria aproximadamente 4,32%/ano em fricção, antes de composição e entrada/saída terminal; com 2× custos, 8,64%. O turnover real pode ser menor, mas é necessário contabilizar ajustes de peso e quantidades, não só troca de nomes.

Uma carteira com 10–12 nomes deixa aproximadamente R$ 417–1.000 por posição nessa faixa de capital. Lote padrão pode inviabilizar pesos iguais; o [mercado fracionário da B3](https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/renda-variavel/acoes.htm) permite quantidades menores, mas preços, spread e arredondamento precisam ser medidos. O banco atual e o motor não provam essa execução. Impacto em grandes ações provavelmente é menos limitante que despesa fixa, lote e qualidade de execução; é inferência qualitativa, não capacity audit concluída.

Drawdowns históricos reportados frequentemente estão entre 35% e 68%; são medidas do motor antigo e não limites futuros. Probability of ruin, impostos por situação pessoal, benchmark líquido, risco de cauda e custo de capital não foram quantificados. Nenhuma classificação `EXECUTABLE_EDGE` ou `REALIZED_EDGE` é justificada.

### 23. Onde o dinheiro poderia vir

H17: evitar lucro pouco sustentado por caixa se houver sub-reação persistente. H18/H19: comprar lucro/patrimônio baratos depois de controlar riscos e erros de capitalização. Construção: evitar negócios cujo ganho marginal não paga custos, permitindo hold/abstenção. Com R$ 5–10 mil, economia operacional pode ter mais valor que um pequeno aumento de Sharpe. São teses, não descobertas.

## E. Estabilidade — itens 24–27

**24. IC/rank IC:** os “IC95%” publicados são intervalos de confiança da diferença de Sharpe, **não Information Coefficient**. Não encontrei painel canônico de Pearson IC, Spearman rank IC, decaimento ou monotonicidade de quantis. Não serão calculados em H17–H19 sob rótulo de cobertura.

**25. Cross-sectional stability:** não demonstrada; mediana de nomes não testa estabilidade do sinal. **26. Concentração por ativo/setor/liquidez:** carteiras pequenas; atribuição/top contributors/leave-one-out não arquivados de forma suficiente. Setor, classe e empresa não estão resolvidos por master PIT rigoroso. **27. Tempo/regime:** uma janela histórica majoritariamente compartilhada, H11 com janela diferente, fundamentos começando depois; sem replicação independente e sem evidência prospectiva. Conclusão: estabilidade desconhecida, não “estável”.

## F. Próxima pesquisa — itens 28–36

### 28. ECONOMIC_THESIS das candidatas

| Pergunta | H17 accruals | H18/H19 valor | Construção/hold |
|---|---|---|---|
| Como ganha dinheiro? | Retorno futuro de empresas com lucro mais persistente, líquido de turnover | Reprecificação/fluxos de empresas baratas | Economiza execução evitável preservando exposição útil |
| Quem paga? | Compradores que extrapolam lucros contábeis frágeis; hipótese | Vendedores com restrições ou aversão a riscos; hipótese | Reduz pagamentos de spread/fees; não exige contraparte desinformada |
| Por que existe? | Atenção limitada à conversão de lucro em caixa | Risco, restrições e extrapolação | Rebalance mecânico ignora custo marginal |
| Por que persistiria? | Complexidade contábil e fricções | Parte pode ser prêmio de risco, não alpha | Custos e indivisibilidade persistem |
| Competição? | Dado público limita vantagem; burden of proof alto | Fatores amplamente conhecidos, competição forte | Benefício específico da conta e do tamanho |
| Informação/constraint própria? | Nenhuma vantagem ainda demonstrada | Nenhuma vantagem ainda demonstrada | Pequeno capital e custos próprios são restrições reais |
| Limite de capacidade? | Liquidez e concentração | Liquidez, classes, value traps | Escala da carteira e tamanho mínimo de ordens |
| O que destrói o edge? | Revisões/PIT, turnover, efeito pequeno | Erro de market cap, dividendos omitidos, risco não compensado | Custo de ficar desviado da carteira ideal |
| Quando o mecanismo cessa? | Informação precificada rapidamente | Mudança de risco/precificação | Ganho de rebalance cresce acima do custo |
| Falsificação mais barata? | Vínculo versão/data e escala em arquivo real | Reconciliação de uma quantidade de ações e base de split | Aritmética de custo, lotes e tamanho da conta, antes de backtest |

### 29–32. RESEARCH_PRIORITY_SCORE, EVR e prioridade #1

Heurística ordinal. Positivos: probabilidade de edge, valor líquido, vantagem de dado, execução, capacidade, velocidade de falsificação. Negativos: overfitting, custo de pesquisa, dados, complexidade operacional, tempo até evidência deployable. Cada dimensão 0–5; total = soma positivos − negativos. As pontuações são julgamentos, sem probabilidades calibradas.

| Linha | Positivos (6) | Negativos (5) | Total | Decisão |
|---|---|---|---:|---|
| H17, condicionada a dados corretos | 2,1,2,3,4,5 | 2,2,0,2,4 | 7 | Prioridade de viabilidade |
| Construção/hold para pequeno capital | 2,2,0,3,4,4 | 3,2,0,2,4 | 4 | Backlog; já existe H4, evitar renomear busca |
| H18 | 2,1,1,2,4,4 | 3,3,0,3,4 | 1 | Aguardar reconciliação de capital |
| H19 | 2,1,1,2,4,4 | 3,3,0,3,4 | 1 | Mesma infra H18; sem escolher pelo resultado |
| ITR / evento de informação trimestral | 2,2,2,2,4,2 | 3,4,0,3,5 | −1 | Backlog |

**Prioridade #1: falsificar a prontidão de H17 por testes de provenance/unidades, antes de consumir seu resultado.** EVR alto pelo baixo custo e por resolver erros comuns às três abertas. Não implica alta probabilidade de alpha. A auditoria já encontrou uma falha material; o próximo trabalho é torná-la reproduzível e utilizável como bloqueio verificável. Não criar nova família para fugir do problema.

### 33–35. Plano, research funnel e stopping rule

`DATA FEASIBILITY → CHEAP FALSIFICATION → REJECT_READINESS / REPAIR → novo exame de protocolo → DISCOVERY → REPLICATION → PROOF CANDIDATE`. Nem documentação nem suíte verde autorizam saltar para confirmação.

- `MAX_EXPERIMENTS`: três controles mecânicos centrais — versão/data, unidade monetária, base de ações — sem retorno histórico novo.
- `MAX_COMPUTE_BUDGET`: execução local; até 30 minutos de CPU para a rodada de preflight, além de verificações já iniciadas.
- `MAX_DATA_ACQUISITION_COST`: R$ 0; usar os dois ZIPs já baixados.
- `MAX_ACTIVE_RESEARCH_EFFORT`: uma sessão curta para auditoria reproduzível; reavaliar antes de uma reconstrução de dados com vários dias de esforço.
- `MAX_PROSPECTIVE_WAIT_WINDOW`: nenhuma espera iniciada; não abrir coorte sem custo/efeito e tamanho amostral definidos.
- `MIN_EFFECT_WORTH_PURSUING` / `MINIMUM_ECONOMICALLY_INTERESTING_OUTCOME`: gate econômico provisório de R$ 500/ano incremental após custos, descrito acima.
- `MIN_EDGE_AFTER_STRESS`: positivo após custos dobrados, execução posterior e custo fixo; limiar estatístico e econômico detalhados só com protocolo revisado.
- `STOP_FOR_FUTILITY_RULE`: uma falha demonstrada de PIT/unidades rejeita prontidão; não rodar retornos para ver “se faz diferença”. Falta de solução reproduzível barata pausa a linha.
- `CRITERIA_FOR_ESCALATION`: dados versionados, classes e bases conciliadas, execução consistente e cenário econômico viável justificam novo orçamento.
- `CRITERIA_FOR_CONFIRMATION`: hipótese/configuração/histórico de busca congelados, dataset com hash, amostra independente identificada, controles e stress antes da revelação; DSR sozinho não basta.
- `CRITERIA_FOR_KILL`: falha econômica mesmo em cenário plausível favorável, custo de dados/manutenção incompatível ou impossibilidade de reconstruir informação no tempo.

### 36. Cinco próximas ações concretas

1. Registrar esta primeira entrega e preservar hashes do banco, ledger e config.
2. Transformar a falha versão/data e de escala em auditoria reproduzível contra o ZIP oficial, com saída somente de qualidade.
3. Verificar os controles com fixtures reais reduzidas e casos adversariais, sem alterar o parser histórico ou o banco operacional.
4. Preservar cópias dos relatórios locais H14–H16 e apontar drift do ledger, sem reescrever seus resultados.
5. Emitir veredito de prontidão e custo da próxima etapa; somente então decidir se uma reconstrução isolada dos dados merece esforço adicional. Nenhum comando `backtest-h 17/18/19` neste ciclo.

## G. Ideias autônomas — itens 37–39

**FREE_ALPHA_CANDIDATE: abstention/hold com quantidades inteiras.** Oportunidade: reduzir negócios pequenos cuja fricção excede o ganho marginal. Mecanismo `PORTFOLIO_CONSTRUCTION / EXECUTION`; existe por indivisibilidade e custos. Dados: holdings, preços executáveis do fracionário, custos e sinal previamente legitimado. Edge plausível: limitado à fricção evitada, ainda sem magnitude medida. Capacidade: suficiente em tese para R$ 5–10 mil; tempo até veredito mecânico de horas, até evidência deployable desconhecido. Custo baixo para cálculo mecânico, alto para provar preservação de alpha. Confiança baixa em retorno incremental; **BACKLOG**, abaixo de H17 viabilidade.

**FREE_ALPHA_CANDIDATE: informação trimestral de caixa disponibilizada por versão.** Mecanismo `INFORMATION_LATENCY`; hipótese de reação lenta a mudança de conversão de caixa. Dados ITR + entrega por versão + total return correto. Fonte confirmada publicamente; existência de edge não testada. Capacidade e efeito desconhecidos; custo de pesquisa moderado/alto; **BACKLOG**, abaixo da agenda atual. Não é reabertura automática de ROE/margem, nem autorizaria escolher janela depois de ver resultados.

**Cheapest falsification já concluída:** a prontidão de dados de H17–H19 foi refutada por vínculo de versão incorreto e escala monetária; o custo fixo de uma operação com R$ 5–10 mil pode consumir centenas de reais anuais. Isso modifica a alocação do research budget, sem produzir um novo claim de retorno. Nenhuma oportunidade fora de Stocks foi desenvolvida.

## Evidência reproduzível desta entrega

`state-evidence.json`: inventário, hashes e cópia de leitura dos ledgers históricos. `source-audit.json`: URLs, hashes dos ZIPs, cabeçalhos e exemplos de versão/escala. `audit-details.json`: lacres vigentes, contagens de proventos e efeito da função de split sobre a contagem do BBAS3. Artefatos locais são evidência de auditoria; não são novos resultados de estratégia.
