# Baseline factual — OSS-20260911-01

SHA `80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5`, branch `main`, checkout canônico `C:\STOCKS\stocks-predictor`. Git inicialmente limpo; HEAD remoto conferido igual. Um worktree, sem reset/stash. Fotografia e hashes congelados em [baseline.json](baseline.json), antes de discovery externo. Data observada UTC 11/09/2026 (sessão local iniciada em 10/09). Não é lacre criptográfico contra o proprietário: hash identifica os bytes e a rodada separa o histórico.

## Permissões e preservação

O pedido atual adota o mandato de pesquisa do arquivo fornecido. A autorização ampla antiga em AGENTS não é usada para commits, push, integração ou novas operações. Restrições de Windows permanecem: Python auxiliar 3.12.14 stdlib; produção exige >=3.13,<3.15. Nenhum venv/instalação, Core novo, automação, ordem ou escrita em banco original. Conteúdo externo só foi lido.

RESEARCH_FREEZE §11 exige seis campos e revisão humana para reabrir famílias encerradas. DESIGN de junho registra arquitetura e escopo históricos; vendoring/cron ali descritos não superam as regras atuais de wheel e ausência de operação. Notas de H17-H19 não observadas são históricas e não substituem os registros posteriores. Nenhum avaliador formal ou holdout protegido foi executado.

## Caminhos inspecionados

| Fluxo | Evidência nesta rodada | Limite |
|---|---|---|
| COTAHIST → parser → fonte versionada | [cotahist.py:40](https://github.com/leonardosovienski/stocks-predictor/blob/80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5/stocks_predictor/cotahist.py#L40), [operational_store.py:115](https://github.com/leonardosovienski/stocks-predictor/blob/80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5/stocks_predictor/operational_store.py#L115), C1 | Formato/data/fator positivo e hash não certificam cobertura ou ajuste econômico |
| DFP → versão → painel | [cvm_pit.py:101](https://github.com/leonardosovienski/stocks-predictor/blob/80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5/stocks_predictor/cvm_pit.py#L101), [document_panel.py:21](https://github.com/leonardosovienski/stocks-predictor/blob/80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5/stocks_predictor/document_panel.py#L21), testes test_document_panel.py lidos: C2 | `receipt_dates` usa dia recebido +1 como cutoff conservador diário, não timestamp observado de publicação |
| Universo → score → quintil | [universe.py:28](https://github.com/leonardosovienski/stocks-predictor/blob/80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5/stocks_predictor/universe.py#L28), [portfolio.py:76](https://github.com/leonardosovienski/stocks-predictor/blob/80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5/stocks_predictor/portfolio.py#L76), C1 | Histórico mínimo/liquidez/quarentena; prefixo de 4 caracteres ainda é heurística de emissor |
| Sinal → próxima sessão → caixa/quantidades | [simulation.py:89](https://github.com/leonardosovienski/stocks-predictor/blob/80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5/stocks_predictor/simulation.py#L89), C3 restrito | MECH-01 sintético 8/8; não valida instalação, liquidação tributária ou todos os eventos |
| Backtest histórico e atual | [backtest.py:735](https://github.com/leonardosovienski/stocks-predictor/blob/80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5/stocks_predictor/backtest.py#L735), [simulation.py:326](https://github.com/leonardosovienski/stocks-predictor/blob/80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5/stocks_predictor/simulation.py#L326), C1 | `legacy_*` preservado; motor atual com train_end/embargo, sem pipeline geral de ajuste ML/purga por label |
| Edge → custo → decisão de manter | [economic_gate.py:32](https://github.com/leonardosovienski/stocks-predictor/blob/80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5/stocks_predictor/economic_gate.py#L32), C1 | SE iid normal explicitamente limitado; não corrige dependência ou seleção adaptativa |
| Dado maturado → gate | [temporal_evidence.py:29](https://github.com/leonardosovienski/stocks-predictor/blob/80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5/stocks_predictor/temporal_evidence.py#L29), C1 | Rejeita futuro/duplicação informados; não prova veracidade do timestamp ou independência |
| Perfil pessoal → prontidão | [research_profile.py:7](https://github.com/leonardosovienski/stocks-predictor/blob/80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5/stocks_predictor/research_profile.py#L7), C1 | Campos faltantes não viram zero; cenário completo não seria validação de lucro |

## Core, ambiente e CI

`pyproject.toml` exige PyYAML >=6,<7 e Core >=3.2,<4; uv.lock aponta wheel oficial 3.2.0. Imports reais localizados: kernel.infra em db/config, net em ingestão, measurement.bootstrap/stats em backtest, trials/harness em trials_gate. Responsabilidade B3 segue no domínio. Vendor não é prova da versão instalada. **Artefato instalado Core: NÃO VERIFICADO nesta máquina.**

Workflow lido: Linux 3.13/3.14, lint/tipos, hashes, cobertura mínima 77%, testes ativos e históricos, build repetido e wheel fora do checkout. Consulta do conector de workflows para SHA atual retornou lista vazia; isso não prova ausência de CI. **CI do SHA atual: NÃO CONFIRMADA nesta rodada.** CI232 citada nos documentos pertence a bf7b3bc, não foi transferida ao HEAD atual.

## Dados e hipóteses

Catálogo externo localizado em `C:\STOCKS\data\CATALOG.json`; diretório recovery-r2 existe. Seus números são registros prévios, não recontagem atual. **12 bancos: NOT_ACCESSED**; não concluir base vazia nem recuperação completa. Catálogo distingue original, versões de pesquisa e fixtures. Não foram lidos preços futuros ou retornos protegidos.

Estado documental vigente: 15 trials legados; H3 não executada. H1/H2/H4–H16 encerradas sem suporte, com limitações de medição/revisão registradas em `2026-09-07-prior-hypotheses-review.json`. H17 teve discovery exposto e permanece inconclusiva por dados; runners formais H17-H19 bloqueados. H18/H19 têm pesquisas posteriores separadas: pré-registro antigo não significa amostra intocada. H20 mantém lacunas de fontes. H21 é histórico condicional; plano prospectivo termina na primeira sessão em/após 10/09/2027. H22 rejeitada nos pares calculáveis segundo estado atual; nenhum resultado foi recalculado.

Estado atual registra 50 valores líquidos, 22 datas e 28 registros societários incompletos, com sobreposição. O catálogo mais antigo registra 52/24/28 para fonte14: versões diferentes, não somar ou sobrescrever. Fonte15 não é substituição automática de 13/14. Capital R$5.000 aparece como confirmado na documentação vigente; não houve nova confirmação pessoal nesta rodada. Custos/prazo/fiscalidade permanecem sem comprovação suficiente.

## Cobertura

Inspecionados: entradas, DESIGN, restrições relevantes do freeze, configurações, CI, componentes e testes citados acima; pesquisas por símbolos nos demais módulos. Executado: apenas MECH-01 stdlib. Protegidos: avaliadores congelados, lacres e plano prospectivo. Não acessados: conteúdo dos bancos, credenciais, broker, dados futuros. Ainda não verificados: inventário linha a linha de todos os módulos, wheel Core, CI atual, direitos individuais de todas as fontes e runtime externo. `DESCONHECIDO` na matriz não significa ausência. Esta é auditoria focal dos caminhos críticos, não auditoria exaustiva de toda a árvore.
