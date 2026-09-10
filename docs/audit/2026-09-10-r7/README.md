# R7 — execução do consolidado da auditoria

Pedido: reunir e executar os achados, limitações, propostas, falhas de teste,
omissões e correções das rodadas anteriores. Capital confirmado nesta conversa:
**R$5.000**. Base de trabalho: main
`0e2c79185d9f62ba69af028b1b601649d6b5f257`. Trabalho individual em `C:\STOCKS`.

**A engenharia e a rastreabilidade avançaram; o pedido integral ainda tem itens
abertos. Lucro líquido pessoal, executável ou futuro não foi demonstrado.**
Custos e prazo pessoais não foram inferidos da tolerância a perdas. Nenhuma ordem,
movimentação de capital, instalação no Windows ou automação foi realizada.

## Entrega e estado único

- [Consolidado legível](CONSOLIDADO.md): estado, resultado e condição restante de
  cada um dos 75 itens principais e dos 78 registros de caixa/societários.
- [Registro atual](current.json), [base histórica V2](baseline-v2.json) e
  [reprodução](REPRODUCTION.md): os 16 achados originais, dez correções R4, duas R5,
  25 limites, 16 propostas e seis complementos do chat permanecem rastreáveis.
- [Revisão de fontes](SOURCE_REVIEW.md), [matriz de condições](SOURCE_RIGHTS.md) e
  [794 registros por arquivo](source-rights.json).
- [Histórico de CI](evidence/ci-history.json), incluindo falhas anteriores;
  [PR78](https://github.com/leonardosovienski/stocks-predictor/pull/78) concentra
  os checks e a integração da rodada.

As 1.590 ocorrências de 15 classes, 24 frentes, 22 afirmações e resultados
históricos também foram preservados. O registro separa resolução no escopo,
implementação com limite, dependência de dados, informação pessoal, tempo futuro
e conclusão científica já obtida. Os grupos se sobrepõem e não devem ser somados
como se fossem defeitos independentes.

## O que mudou no código e na infraestrutura

| Mudança | Efeito verificado | Limite |
|---|---|---|
| Origem por conteúdo/versão | Cópia estável antes do parsing; conflito exige nova versão; catálogo e preços atômicos; replay idempotente | Opt-in; sem migração dos bancos ou certificação PIT retroativa |
| Evidência econômica datada | Datas com fuso, maturidade, observação anterior ao corte e duplicatas verificadas | Datas fornecidas e independência ainda exigem prova |
| Nome do método RJ | `joint_max_t` descreve o algoritmo; alias antigo preserva compatibilidade | Não foi inventado stepdown nem alterado o veredito científico |
| Perfil econômico | Capital R$5.000, custos financeiros/projeto/tempo separados; desconhecidos explícitos | Falta cenário pessoal completo; nunca habilita capital |
| Análise estática | Pyright cobre todo o pacote; Ruff F/E9; contratos opcionais/imports Core corrigidos | Tipagem básica e cobertura de ramos 79%, não prova universal |
| CI e distribuição | Actions por SHA, ferramentas por hash, dois builds idênticos, smoke da wheel fora do checkout | Ambiente controlado; runner e patches de Python ainda evoluem |
| Evidências antigas | 17 testes arquivados executados em etapa própria e aprovados | Não significa executar todos os scripts científicos já arquivados |
| Materializador | 830 arquivos da Fonte15 reconstruídos do delta de seis arquivos e Fonte14 | Necessita os dados externos identificados pelos manifestos |
| Registro único | Confere populações, identidades, evidências e documento gerado; recusa fechamento sem prova | Identidade não substitui revisão semântica da suficiência |

A [CI220](https://github.com/leonardosovienski/stocks-predictor/actions/runs/34514230223)
passou nas duas versões de Python: **877 testes ativos, 17 arquivados, 49 subtestes
no Python3.14, Pyright sem erros e cobertura de ramos 79%**, incluindo as regressões
do registro, build auxiliar e custo do trabalho. Os 18 testes stdlib novos também
passaram localmente. O PR registra o check do head documental final; a CI220
corresponde ao commit `09bcd66fff9060426ac597f22f53af2a55c7e49a`.

Além dos testes sintéticos, a API de ingestão versionada foi aplicada ao ZIP B3
de 2026 já adquirido: **55.986 preços de 408 tickers entre 02/01 e 09/09/2026**,
em um banco novo de conferência. Replay com zero inserções e integridade SQLite
aprovada, conforme [recibo](evidence/real-versioned-ingestion.json). O filtro é
BDI02/mercado010; não contém todos os instrumentos nem substitui os bancos ou
protocolos históricos. Os [12 bancos anteriores e o V2](evidence/preservation.json)
mantiveram seus hashes.

## Desempenho observado

[Recibo com todas as medições](evidence/real-ingestion-benchmark.json): dois
extratos reais preservados de 2018/2026, três repetições por revisão, processo
novo por medição. As linhas finais foram idênticas. Medianas do pico RSS:

| Extrato | Antes | Depois | Tempo de parede antes → depois |
|---|---:|---:|---:|
| 2018 | 46.608.384 bytes | 27.979.776 bytes | 0,1736772 s → 0,1601500 s |
| 2026 | 35.454.976 bytes | 26.169.344 bytes | 0,0799864 s → 0,0865762 s |

A memória do processo caiu cerca de 40% e 26%; o tempo do segundo extrato ficou
cerca de 8% maior. O RSS inclui Python e SQLite. Não houve medição separada de
alocadores, carga concorrente ou garantia de velocidade para qualquer arquivo.

## O que permanece aberto e por quê

**I10/I11/I13/I14:** publicação histórica/identidade por intervalo, cobertura
contínua de eventos BOVA11, custos aplicáveis e caixa societário ainda incompletos.
Permanecem **50 líquidos, 22 datas e 28 registros societários**. A revisão não
encontrou prova suficiente para preencher esses campos. Um prazo máximo de
pagamento não foi convertido em data realizada, nem um valor bruto em líquido.
Há pagamentos futuros e decisões de titulares que não podem ser observados hoje.

**I12:** o capital deixou de ser desconhecido, mas faltam prazo, taxas efetivas,
residência fiscal e custo do projeto/tempo para um resultado pessoal. Não é
necessário login de corretora para informar essas premissas.

**I16:** o plano prospectivo mantém zero observações concluídas. A janela fixa
termina na primeira sessão em/após 10/09/2027; o tempo ainda não transcorreu.
Revisão por este mesmo assistente não constitui auditoria independente.

**I15 está resolvido quanto aos arquivos.** A diferença estrita de float de
2,22e-16 é preservada e distinguida da falta de arquivos, com replay por tolerância
previamente registrada. A omissão de fechamento da descrição do PR75 foi
[corrigida de fato](evidence/pr75-closure-and-actions.json).

H22 continua rejeitada; lucro nominal histórico condicional de outros cenários
não foi promovido a lucro futuro ou superioridade líquida. Nenhuma nova seleção
de estratégia por retorno foi realizada nesta rodada. As condições restantes
estão individualizadas, sem marcar o trabalho integral como 100% concluído.
