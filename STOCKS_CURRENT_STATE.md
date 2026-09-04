# Stocks Predictor — estado corrente

**Vigência:** 2026-09-04

Este é o ponto de entrada técnico corrente. O código, Git/CI e
`RESEARCH_FREEZE.md` prevalecem sobre documentação histórica.

## Estado canônico

```text
role = FROZEN_RESEARCH_ASSET + REUSABLE_COMPONENT_LIBRARY + NEGATIVE_RESULT_CASE
research_state = FROZEN                                # ver HANDOFF.md, 2026-09-04
scientific_state = CLOSED_FOR_H1_THROUGH_H13           # todas as 12 hipóteses julgadas
commercial_state = NOT_A_PRODUCT
new_scientific_trials = 0
```

As famílias de fatores JÁ JULGADAS (H1/H2/H4/H5/H6/H7/H8/H9/H10/H11/H12/H13
— 12 no total, todas NOT_SUPPORTED) e a linha RJ estão encerradas/congeladas.
**H11** (momentum 12-1 em RETORNO TOTAL, proventos reinvestidos — corrige o
viés só-preço das 9 anteriores) julgada 2026-09-04: NOT_SUPPORTED (DSR
0,8430 < 0,95 — o maior de toda a série). **H12** (margem líquida isolada)
e **H13** (crescimento de receita YoY, primeira hipótese de CRESCIMENTO
testada) julgadas na mesma sessão: ambas NOT_SUPPORTED com DSR bem abaixo
do limiar (0,1952 e 0,2598) — junto com H7/H9 (ROE/alavancagem
isoladas), esgotam o baralho de fatores extraíveis da DFP consolidada da
CVM sem uma fonte de dado genuinamente nova (fluxo de caixa, múltiplos de
mercado, dado intraday/institucional) ou universo diferente. Ver
HANDOFF.md "VEREDITO H11"/"VEREDITO H12 e H13" para detalhes completos.
Reabertura de qualquer uma das 12 exige o dossiê completo definido em
`RESEARCH_FREEZE.md` e informação materialmente nova.

## Dependência e vendor

- contrato: `predictor-core>=3.0,<4`;
- resolução canônica do CI/lock: wheel oficial `predictor-core==3.0.0`;
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

Somente bug real, segurança, preservação ou integridade de dependência. Mudanças de
manutenção não promovem claim científica ou comercial.

## Fontes

1. `RESEARCH_FREEZE.md` — estado científico, decisões e política de reabertura;
2. `pyproject.toml` e `uv.lock` — contrato de dependências;
3. `.github/workflows/ci.yml` — ambiente canônico de validação;
4. `poc_leak.py` e testes de import/replay — preservação e regressão anti-drift;
5. Git/CI — evidência mecânica atual.
