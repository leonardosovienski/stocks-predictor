# Correções de dados e execução — 7 de setembro de 2026

Implementação autorizada pelo usuário após a auditoria: corrigir datas/versões da
CVM, unidades monetárias, base de ações, simulação de execução e retorno total.
Nenhuma hipótese econômica foi rodada. Não há nova evidência de rentabilidade.

## O que mudou

| Problema comprovado | Comportamento corrigido | Validação |
|---|---|---|
| Valor de uma retificação usava o primeiro recebimento do exercício | Junção por CNPJ, exercício **e versão**; observações separadas e imutáveis | ZIP oficial DFP 2023 completo: 475 documentos; Energisa v3 recebida em 15/03/2024 |
| Parser removia o ponto decimal e ignorava MIL/UNIDADE | Decimal da CVM convertido explicitamente para reais; moeda/escala desconhecida falha | Receita Ambev 2023 = R$ 79.736.856.000 |
| Dia da entrega não prova publicação antes do fechamento | `received_at` preservado; `available_at` no dia seguinte quando só há data | Disponibilidade da Energisa a partir de 16/03, sem antecipar a versão |
| FRE misturava maior quantidade com recebimento mais antigo | Cada `ID_DOC` conserva sua própria quantidade e data | 455 documentos reconstruídos no ZIP 2023; teste com retificação que muda a quantidade |
| `Data_Referencia` do FRE tratada como base do desdobramento | Base efetiva e equivalência entre ações totais e preço do papel precisam de fonte explícita; sem elas o múltiplo fica inelegível | BBAS: base posterior ao split mantém a quantidade; base desconhecida não gera valor |
| Compra recebia retorno anterior à execução | Nova simulação executa estritamente depois do sinal, em abertura, fechamento ou cenário adverso | Gap antes da entrada excluído; execução adiada só no papel sem cotação |
| Pesos fixos implicavam rebalanceamento diário gratuito | Quantidades mantidas entre ordens; pesos variam com preços; redimensionamento paga custo | Carteira que sobe e depois reverte volta ao NAV correto, sem ganho artificial |
| Benchmark renormalizava apenas papéis cotados | Mesma contabilidade de posições, caixa, custos e preços para ambas as carteiras | Carteira igual ao benchmark produz curva idêntica |
| Falta de cotação removia ou disfarçava posições | Última marca preservada com diagnóstico; gap é reconhecido quando o papel volta; cotação final ausente impede resultado completo | Controle de suspensão e retorno à negociação |
| FRE usava pagamento como data-ex e montante agregado/free float como valor por ação | Importador público dessa aproximação bloqueado; retorno total exige eventos por papel, data-ex, valor por ação e cobertura documentada | Eventos inválidos/duplicados e falta de cobertura falham antes da escrita |
| Proventos simultâneos e splits misturavam bases | Proventos da mesma data somados antes da composição; bases de cada evento preservadas | Queda de R$100 a R$90, proventos de R$4+R$6 e split posterior produzem índice 100/100/100 |
| Provento podia ser creditado no dia errado | Na carteira, direito nasce na data-ex antes das ordens; vira caixa no pagamento, sem novo ganho | Quem compra na data-ex não recebe o direito anterior |
| Embargo declarado era inerte | Instrumento novo exige `train_end` para embargo positivo; aplica meses completos de separação | Parâmetro sem fronteira explícita rejeitado; teste verifica mudança das datas elegíveis |

## Integração e preservação

`ingest_cvm.ingest_dfp_year` e `ingest_fre_shares_year` agora escrevem nas novas
tabelas `fundamentals_pit` e `shares_pit`. A migração **0013** é adicional; não
altera migrações anteriores nem faz backfill destrutivo. `ingestion_issues`
registra documentos excluídos por falta ou ambiguidade na junção de versão.
Entradas idênticas são idempotentes; mudanças na mesma identidade imutável
levantam erro. Importações são transacionais.

Os fatores públicos H17/H18/H19 consultam somente as novas tabelas. Não existe
fallback para valores monetários ou datas da tabela histórica. A versão mais
recente elegível sem valor não recupera silenciosamente um valor obsoleto.

`backtest.walk_forward` chama `simulation.py`, o instrumento corrigido. Os
runners das hipóteses já julgadas usam explicitamente `legacy_walk_forward`,
preservando a reprodução histórica. Parsers e retornos históricos permanecem
sob nomes `legacy_*`; os testes que verificam esses números agora indicam
explicitamente que são testes históricos. As correções possuem testes novos,
com expectativas calculadas à mão e fixtures reais. Não se trata de mudar
os valores esperados dos testes antigos para fazê-los passar.

**Os runners H17/H18/H19 e o dispatcher CLI estão bloqueados antes de leitura
de desempenho.** O CLI bloqueia antes de `_conn()`, migrações ou registro de
baseline. Alterar o instrumento e a política diária de disponibilidade exige
novo pré-registro antes da observação. Os lacres, config, atestado e ledgers
históricos permanecem intactos. Nenhuma observação real H17/H18/H19 foi feita.

## O que a correção de código não consegue preencher

- Os arquivos examinados não certificam a data efetiva da quantidade de ações
  nem que ações totais × preço de uma classe representa a capitalização de
  uma empresa com ON, PN ou units. Os 455 documentos FRE foram preservados,
  mas permanecem sem base certificada. São dados disponíveis, **não 455
  observações elegíveis para valor**. `basis_by_document` aceita evidência
  explícita na reconstrução de uma nova cópia; não converte o rótulo do ano
  ou a aprovação do capital em data da quantidade.
- O FRE contém também `capital_social`: para BBAS aparecem 5.730.834.040 ON,
  diferentes dos 5.730.799.931,446 derivados do percentual arredondado de float.
  O campo de aprovação desse capital é de 2023, embora a quantidade reflita
  o desdobramento posterior. Portanto esse campo também não certifica a base
  temporal. Nenhuma das duas quantidades é promovida silenciosamente.
- Falta uma série histórica verificada de proventos por papel, com datas-ex
  e cobertura contínua. Não é possível recuperar isso apenas corrigindo a
  fórmula do montante do FRE. A API nova rejeita essa aproximação e aceita
  eventos documentados, inclusive cobertura de períodos sem proventos.
- A validação empírica de parsing nesta sessão cobre o ZIP integral de 2023.
  Isso não equivale a reconstruir todos os anos de 2018–2026. Uma cópia
  demonstrativa pode aplicar apenas os mapeamentos explicitamente informados.
- O instrumento novo é long-only, fracionário e de custo percentual fixo.
  Não valida execução real com R$5–10 mil, lotes/fracionário da B3, impostos,
  impacto, capacidade, insolvência de ativos ou disponibilidade de empréstimo.
  Posição sem preço final falha em vez de receber uma liquidação inventada.
- O índice de retorno total assume reinvestimento teórico na data-ex. A
  carteira executável registra recebíveis e caixa na data de pagamento;
  reinvestimentos seguem ordens posteriores, com custos.
- Não há modelo estimado neste instrumento. A implementação de separação
  por meses não afirma validar purge de labels sobrepostas de um futuro ML.

## Reconstrução reproduzível em cópia

`tools/rebuild_cvm_copy.py` recebe um plano offline, com ZIPs e mapas por ano.
Recusa o mesmo caminho do banco original ou qualquer destino já existente;
abre a origem em modo somente leitura, usa SQLite backup e aplica a migração
somente na nova cópia. Valida hash da origem e integridade SQLite. Não baixa
arquivos, infere símbolos, calcula sinais ou escreve no ledger.

Exemplo de plano (caminhos absolutos devem ser preenchidos com fontes reais):

```json
{"years":[{"year":2023,"dfp_zip":"DFP_2023.zip","dfp_map":"mapa_dfp_2023.json",
"fre_zip":"FRE_2023.zip","fre_map":"mapa_fre_2023.json"}]}
```

Campos opcionais `fre_basis` apontam para JSON por `ID_DOC`, com `basis_date`,
`basis_source` e `price_basis_source`, quando as três informações forem
comprovadas. A base desconhecida fica nula, não é estimada. Uma evidência
nova deve entrar numa reconstrução nova; não substitui registros imutáveis.

```powershell
py -3.13 tools/rebuild_cvm_copy.py --source-db CAMINHO_ORIGINAL --output-db NOVA_COPIA --plan PLANO_JSON
```

Para proventos, `cash_events.import_verified_events(conn, payload, coverage)`
recebe CSV UTF-8 com `ticker,event_id,ex_date,payment_date,value_per_share,source`
e intervalos explícitos `ticker,start_date,end_date,source`. `event_id` deve
identificar o evento econômico estável, não a linha de um download. Eventos
com IDs diferentes na mesma data podem ser direitos distintos e são somados;
o código não inventa uma identidade econômica a partir de ticker/data.

## Validação desta revisão

Ambiente: Python 3.13, Core 3.2.0 oficial em diretório isolado, sem novas
dependências de runtime. Checagem dirigida antes da suíte completa:
**47 testes aprovados**, incluindo 36 novos testes/parâmetros e 11 da auditoria.
O resultado da suíte completa, commit e hashes de entrega são registrados
no relatório final junto ao pacote; nenhuma afirmação de lucro decorre disso.

Fontes brutas usadas: [DFP 2023](https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_2023.zip)
e [FRE 2023](https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FRE/DADOS/fre_cia_aberta_2023.zip).
Hashes constam em `repair-real-validation.json` do pacote de entrega.


### Resultado final

- **422 testes passaram** em 139.14s com coverage e Core 3.2.0;
  commit de código testado `608ac2c709db239128886545168548049026f03b`.
- Ruff aprovado; Pyright: zero erros, zero avisos. Wheel construída e
  importada com sucesso fora do checkout, incluindo os módulos novos.
- Ledger derivado conferido pelo migrador existente: idempotente.
- Cópia demonstrativa do banco real: 3 documentos DFP + 3 FRE de 2023
  (Ambev, Banco do Brasil e Energisa); todas as tabelas históricas iguais
  à origem por contagem e SHA-256 do conteúdo. A origem manteve seu hash.
- As derivações completas de 2023 foram exportadas em JSONL: 475 DFP e
  455 FRE, independentemente do mapeamento demonstrativo de três emissores.
- Nenhum push, investimento, nova tentativa científica ou desempenho
  protegido. A cobertura histórica completa de proventos e as bases
  certificadas das ações permanecem pendentes de fonte, explicitamente.
