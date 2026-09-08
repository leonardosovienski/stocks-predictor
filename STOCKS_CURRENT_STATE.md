## Teste de desempenho H20 (08/09/2026 UTC)

Pedido: testar se melhorou a projeção de lucro. Protocolo 9286129 anterior ao
cruzamento com retornos; medidor 2488171. 31 trimestres de 2018-07-02 a 2026-04-01,
três seleções congeladas, três preços e dois custos, sem tuning. 29/03/2018 retida
como bloqueada por cobertura; nenhuma data elegível removida pelo desempenho.

Diagnóstico de marcações com rotação integral hipotética, sem caixa ordinário,
impostos ou manutenção: anualização na abertura/custo base 11,00% controle comum,
14,02% valor/rentabilidade, 14,58% retenção. Adverso/custo dobrado 2,05%, 4,74%, 5,25%.
Retenção é a sequência pretendida, sem execução contínua da banda de peso de 2,5%.
Economia real de turnover não foi inferida. Lucro/projeção futura permanecem null.

Diferença média retenção-controle na abertura +0,197 pp/trimestre; IC descritivo
95% [-3,61; +3,92] pp, sem ajuste por seleção. Segunda metade -0,34 pp/trimestre
brutos; vantagem recente também negativa nos outros preços. Drawdown adverso
com custo dobrado -48,24%. Melhora composta aparente, incremento inconclusivo.

639 testes completos +11 testes da medição. Reprodução de 1.448 arquivos,
9.732 células e 12 cenários anteriores, conferência independente de 465 médias,
30 trajetórias e 54 pares. Nova observação byte idêntica aa184580bf5b...;
replay financeiro antigo idêntico e bloqueado. Zero inventários integrais de
caixa disponíveis para os 231 intervalos trimestrais de cada seleção H20.
Runtime de produção inalterado, extratos históricos lidos com mode=ro e hashes
verificados; bancos principais, ledgers, quarentenas e fontes preservados.

18 cenários adicionais registrados/observados, contagem conservadora mínima
53 configurações/55 avaliações históricas; sem holdout ou Proof. Não promover
H20 ou ajustar parâmetros. INCONCLUSIVE_NET_PROFIT / OPERATIONAL_NO_GO mantido.
Relatório: docs/research/2026-09-08-h20-profit-test-results.md. Arquivo reproduzível
em research/session-20260908/h20-profit-test; saídas também na raiz durável,
outputs/h20-profit-test-20260908. Nenhuma ordem, gasto, agente, instalação ou push.

# Estado vigente — implementação H20 de 08/09/2026 UTC

H20 implementada: valor com rentabilidade dos acionistas, retenção até 30% do
ranking e tolerância de 2,5% do capital para ajustes de posições mantidas.
Três alternativas no mesmo universo; protocolo def8e96 anterior à medição.
31/32 datas elegíveis, 372/384 entradas simuladas; 12 casos da data de cobertura
insuficiente permanecem bloqueados. Substituições planejadas 96→70 com tolerância;
não são giro financeiro ou economia real de uma carteira contínua.

639 testes no runtime 9ecf5eb, 92 na wheel fora do checkout, Ruff e Pyright no
escopo novo. H20 reproduzida byte a byte; replay H19 e diagnóstico anterior
preservados. Agora mínimos 35 configurações registradas / 37 avaliações históricas
de retorno; zero retorno novo. H19 permanece congelada e NO_GO, lucro desconhecido.
Relatório e uso: [H20](docs/research/2026-09-08-h20-results.md).

# Estado anterior — continuidade de 08/09/2026 UTC

Revisão adicional de 17 fontes sobre modelos semelhantes concluída:
[mecanismos, resultados externos e prioridades](docs/research/2026-09-08-similar-models.md).
Revisão documental, sem novo sinal, backtest ou mudança de veredito. Priorizar
custo de manutenção e execução, depois viabilidade de valor com rentabilidade;
PEAD condicionado a fontes e ML adiado. Histórico externo não valida a H19.

**H19 permanece Discovery/inconclusiva; NO_GO operacional. Pausar a reconstrução
manual extensa até existir uma rota barata de fontes e manutenção.**

Foi implementada a tributação de leilões ordinários a partir da base fiscal
individual e corrigida a reutilização de líquidos/impostos entre carteiras.
248 compras iniciais nas seleções congeladas foram simuladas; não são giro nem
lucro da carteira contínua. Permanecem 356 datas, 389 líquidos, zero certificados
para 1.237 intervalos e zero dos 36 registros societários aprovados/integrados.

613 testes na suíte completa (0ac04cb); ajuste final bebe1f7 validado por 3 testes
do diagnóstico e 69 testes no pacote externo. Replay real idêntico, exit 2,
lucro null. Nenhum retorno histórico novo; mínimos 32 configurações/37 avaliações.
Fontes, bancos, ledgers e vereditos anteriores preservados.

[Resultado, cenários econômicos e limites](docs/research/2026-09-08-feasibility-results.md).
O começo de HANDOFF.md contém a execução atual; os textos abaixo são históricos.

# Estado vigente — revisão final de 07/09/2026

**H19 trimestral está em Discovery; H18 é controle; H17 já foi observada e ficou
inconclusiva. Nenhum lucro líquido executável foi demonstrado. NO_GO para operar.**

A revisão final passou 592 testes e os controles técnicos declarados. Faltam
356 datas no cadastro de pagamentos, cobertura de caixa de 1.237 intervalos e
integração fiscal/física de 36 registros societários. Isso impede um replay
econômico completo; saída de auditoria bloqueada não é lucro zero.
O código, as cotações e os testes não substituem essas evidências.

O estado mais recente está no início de [HANDOFF.md](HANDOFF.md) e em
[revisão final](docs/research/2026-09-07-final-review.md). Os textos abaixo são
históricos: referências a H18/H19 não observadas e a RJ como linha ativa foram
superadas. As estatísticas antigas continuam associadas às suas versões.

# Atualização anterior 2026-09-07 — H17 Discovery observada

H17 agora tem duas saídas históricas de um único protocolo exploratório: primeira
medição e correção documentada de quatro falsas divergências de fatores. A última
execução completou 94 meses elegíveis, mediu 5.352/5.399 células e classificou a
rodada como INCONCLUSIVE_DATA_QUALITY. IC disponível médio -0,013201; diferença
mensal apenas nos 59 meses completos -0,161341 p.p. Sem rentabilidade executável,
holdout intacto identificado, GO ou confirmação. H18/H19 seguem não observadas.

Código testado `4f487098e702004a88f02fe65d62a008c6df618b`, 483 testes aprovados.
Ver os registros append-only em `docs/research/2026-09-07-h17-observations.jsonl`
e `docs/research/2026-09-07-h17-budget-update.json`. Os estados abaixo são históricos
e suas referências a H17 nunca vista foram superadas por esta atualização.

## Integração real concluída em 2026-09-07

Motor v3 corrigido: bonificação com direito/entrega separados e dimensionamento correto no
preço adverso. A primeira matriz encontrou quatro falhas; após correção, os 36 controles reais
passaram (R$5/10 mil, três preços, dois custos). Suíte completa: 463 testes, cobertura 86%;
lint, Pyright configurado e wheel instalada fora do checkout aprovados. Código testado:
`5c09c7b8ffebefef00467cbab12481f3535a7837`. Fontes e bancos originais preservados por hash.

Capital original CVM validado em três documentos com escala própria e base em 31/12/2023;
isso não resolve toda a base histórica de capitalização. Nenhum retorno H17–H19 observado,
nenhum trial científico novo. O painel DFP/FCA foi verificado em 104 datas sem performance.
Rentabilidade continua INCONCLUSIVE_DATA_QUALITY e os runners H17–H19 permanecem pausados.
[Resultado completo e limites](docs/research/2026-09-07-real-integration-results.md).

## Complemento executado em 2026-09-07

Reconstruídos 2016–2026 em cópia isolada: 4.177 DFP, 4.824 observações de
circulação, 7.450 registros de capital emitido e 4.336 vínculos FCA. Coletados
9.812 registros B3 de 100 emissores. Reconciliados 184 recebíveis B3/RI;
95 recebíveis com quatro intervalos de cobertura importados apenas na cópia.
FRE inválido é rejeitado por documento, com motivo persistente. Migração 0014
isola observações de fontes das entradas de fatores. Nenhum desempenho protegido.

Ainda faltam bases efetivas de ações, versões históricas completas, cobertura
dos demais emissores e eventos sem dinheiro. H17–H19 permanecem pausadas.
Detalhes: [relatório de fontes](docs/research/2026-09-07-source-completion.md).
Validação completa e hashes são registrados no manifesto da entrega.

# Stocks Predictor — estado corrente

> ## Correções implementadas em cópia isolada — 2026-09-07
>
> As APIs públicas de ingestão agora gravam versões separadas, em reais,
> nas tabelas PIT da migração 0013. Base de ações desconhecida não gera
> múltiplo; retorno total exige eventos por papel e cobertura documentada.
> O novo `backtest.walk_forward` mantém quantidades, negocia após o sinal
> e contabiliza caixa/custos igualmente para estratégia e benchmark.
> Os runners julgados usam explicitamente o instrumento `legacy_*`.
> H17/H18/H19 estão bloqueadas no CLI antes de banco/ledger/desempenho:
> validar o dataset reconstruído e registrar a metodologia corrigida primeiro.
>
> [Implementação, evidências e limites](docs/research/2026-09-07-repairs.md).
> Suíte completa: **422 testes aprovados**, com cobertura; lint e Pyright verdes.
> Parser validado no ZIP integral 2023: 475 documentos DFP e 455 FRE.
> Nenhum resultado protegido observado; nenhuma dependência de runtime nova.


**Vigência:** 2026-09-06 (auditoria de prontidão; nenhuma nova rodada)

**H17-H19: PAUSE antes de desempenho.** A auditoria em
[docs/research/2026-09-06-readiness.md](docs/research/2026-09-06-readiness.md)
encontrou no DFP real associação de valores revisados à primeira entrega e
escala monetária incorreta. Os 100% de `known_at` preenchidos não demonstram
PIT por versão. `tools/audit_dfp_readiness.py` reproduz os bloqueios sem
avaliar retornos e sem abrir o banco. Não está ligado automaticamente ao
dispatcher de backtests; é uma checagem de auditoria com exit code 2 em falha.

Este é o ponto de entrada técnico corrente. O código, Git/CI e
`RESEARCH_FREEZE.md` prevalecem sobre documentação histórica.

## Estado canônico

```text
role = ACTIVE_RESEARCH_ASSET + REUSABLE_COMPONENT_LIBRARY + NEGATIVE_RESULT_CASE
research_state = REOPENED_BY_NEW_DATA_SOURCE          # ver HANDOFF.md, 2026-09-04
scientific_state = CLOSED_FOR_H1_THROUGH_H16          # as 16 primeiras seguem julgadas
                                                      # e FECHADAS; H17-H19 pré-registradas,
                                                      # NÃO rodadas
commercial_state = NOT_A_PRODUCT
new_scientific_trials = 3                             # H17 accruals, H18 E/P, H19 B/M
```

As famílias de fatores JÁ JULGADAS (H1/H2/H4/H5/H6/H7/H8/H9/H10/H11/H12/H13/
H14/H15/H16 — 15 no total, todas NOT_SUPPORTED; H3 não executada) e a linha RJ estão
encerradas/congeladas. **H11** (momentum 12-1 em RETORNO TOTAL, proventos
reinvestidos — corrige o viés só-preço das 9 anteriores) julgada
2026-09-04: NOT_SUPPORTED (DSR 0,8430 < 0,95 — o maior de toda a série).
**H12** (margem líquida isolada) e **H13** (crescimento de receita YoY,
primeira hipótese de CRESCIMENTO testada) julgadas na mesma sessão: ambas
NOT_SUPPORTED com DSR bem abaixo do limiar (0,1952 e 0,2598) — junto com
H7/H9 (ROE/alavancagem isoladas), esgotam o baralho de fatores extraíveis
da DFP consolidada da CVM sem uma fonte de dado genuinamente nova (fluxo
de caixa, múltiplos de mercado, dado intraday/institucional) ou universo
diferente. **H14** (proximidade da máxima 52 semanas), **H15** (surto de
volume) e **H16** (efeito virada-de-mês, primeira hipótese de TIMING
puro do domínio, motor de backtest dedicado) julgadas 2026-09-04: também
NOT_SUPPORTED (DSR 0,3249 / 0,2826 / 0,0052 — H16 a mais baixa de toda a
série). Com H14-H16, esgota-se também a linha de padrões técnicos/
calendário testável com os dados de preço já ingeridos (COTAHIST). Ver
HANDOFF.md "VEREDITO H11"/"VEREDITO H12 e H13"/"VEREDITO H14, H15 e H16"
para detalhes completos. Reabertura de qualquer uma das 16 exige o
dossiê completo definido em `RESEARCH_FREEZE.md` e informação
materialmente nova.

## H17-H19 — re-pré-registradas, aguardando integridade de dados (2026-09-06)

Decisão do operador de reabrir a pesquisa por **fonte de dado nova**, não por
recombinação do que já foi observado (o que seria p-hacking e segue recusado):

| # | fator | direção | dado novo | lacre |
|---|---|---|---|---|
| H17 | accruals `(lucro − FCO)/ativo` (Sloan 1996) | quintil INFERIOR | DFC-MI consolidada da CVM — 1ª demonstração nova desde o M2 | `e6cf9bd7454750c3` |
| H18 | earnings yield `E/P` (Basu; Fama-French) | quintil SUPERIOR | `shares_outstanding` (FRE, migração 0011) | `cbea4d3c98ac3422` |
| H19 | book-to-market `B/M` (Fama-French) | quintil SUPERIOR | idem H18 | `d96753f2af7b39a6` |

H18/H19 são os **primeiros fatores de VALOR** do domínio — as 15 julgadas
mediram qualidade do negócio ou comportamento do preço, nunca a razão entre
os dois. São hipóteses separadas de propósito (fluxo vs. estoque), cada uma
com registro próprio. Há 15 tentativas executadas; a ordem das três ainda
precisa ser congelada. O N nominal seria 16/17/18 na ordem de execução,
sem representar uma contabilidade completa de escolhas adaptativas.

**Estado: NENHUMA rodada real executada; dados ingeridos, prontidão refutada.**
Cobertura remensurada em conexão somente-leitura: medianas H17=56,
H18=49,5 e H19=53 em 104 datas. A ingestão precisa resolver versão/unidade
e base de ações em derivação isolada antes de qualquer veredito.

As 15 hipóteses já julgadas permanecem FECHADAS: nada aqui as reabre, e a
`reopen_policy` de `RESEARCH_FREEZE.md` §11 (6 campos + revisão humana)
continua valendo integralmente para elas.

## Dependência e vendor

- contrato: `predictor-core>=3.0,<4`;
- resolução canônica do CI/lock: wheel oficial `predictor-core==3.2.0`;
- `vendor/predictor_core/`: arquivo histórico íntegro, não runtime normal e não
  incluído no pacote `stocks-predictor`;
- `poc_leak.py`: PoC histórico contra o vendor legado, ativado apenas por execução
  explícita; importá-lo é inerte;
- `tests/conftest.py` e `tests/test_core_import_path.py`: impedem resolução silenciosa
  para o vendor;
- `tests/test_replay.py`: protege a fronteira temporal do Core instalado.

Estado:

```text
STOCKS_RUNTIME_CORE_SOURCE = CANONICAL_PACKAGE_ONLY
STOCKS_VENDOR_RUNTIME = UNREACHABLE_BY_DEFAULT
STOCKS_VENDOR_MIGRATION = CLOSED
LEGACY_VENDOR_LOOKAHEAD_CASE = PRESERVED
CANONICAL_TEMPORAL_GUARD = PASS
VENDOR_REINTRODUCTION_GUARD = PASS
```

## Alterações permitidas

Bug real, segurança, preservação, integridade de dependência — e o trabalho das
hipóteses H17-H19 pré-registradas acima. Mudanças de manutenção não promovem claim
científica ou comercial, e pré-registro NÃO é resultado: nenhuma claim pode ser feita
sobre H17-H19 antes da rodada real e do pedágio.

## Fontes

1. `RESEARCH_FREEZE.md` — estado científico, decisões e política de reabertura;
2. `pyproject.toml` e `uv.lock` — contrato de dependências;
3. `.github/workflows/ci.yml` — ambiente canônico de validação;
4. `poc_leak.py` e testes de import/replay — preservação e regressão anti-drift;
5. Git/CI — evidência mecânica atual.
