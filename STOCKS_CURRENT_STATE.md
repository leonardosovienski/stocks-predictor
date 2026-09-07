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
> 47 testes dirigidos passaram; suíte completa será registrada na entrega.
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
