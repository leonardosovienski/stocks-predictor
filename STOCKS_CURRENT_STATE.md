# Stocks Predictor — estado corrente

**Vigência:** 2026-09-04

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
H14/H15/H16 — 16 no total, todas NOT_SUPPORTED) e a linha RJ estão
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

## H17-H19 — pré-registradas, aguardando rodada real (2026-09-04)

Decisão do operador de reabrir a pesquisa por **fonte de dado nova**, não por
recombinação do que já foi observado (o que seria p-hacking e segue recusado):

| # | fator | direção | dado novo | lacre |
|---|---|---|---|---|
| H17 | accruals `(lucro − FCO)/ativo` (Sloan 1996) | quintil INFERIOR | DFC-MI consolidada da CVM — 1ª demonstração nova desde o M2 | `aece696b814c0fd9` |
| H18 | earnings yield `E/P` (Basu; Fama-French) | quintil SUPERIOR | `shares_outstanding` (FRE, migração 0011) | `dded266f1bb712f1` |
| H19 | book-to-market `B/M` (Fama-French) | quintil SUPERIOR | idem H18 | `dabaa53adc9b9349` |

H18/H19 são os **primeiros fatores de VALOR** do domínio — as 16 anteriores
mediram qualidade do negócio ou comportamento do preço, nunca a razão entre
os dois. São hipóteses separadas de propósito (fluxo vs. estoque), cada uma
com N próprio no DSR (17/18/19).

**Estado: código pronto e testado, NENHUMA rodada real executada.** Exigem
ingestão nova (DFC-MI e ações em circulação) na máquina do operador antes de
qualquer veredito. Ver HANDOFF.md "H17, H18 e H19 ABERTAS — PRÉ-REGISTRO".

As 16 hipóteses já julgadas permanecem FECHADAS: nada aqui as reabre, e a
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
