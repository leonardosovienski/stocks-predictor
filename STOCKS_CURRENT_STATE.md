# Stocks Predictor — estado corrente

**Vigência:** 2026-09-04

Este é o ponto de entrada técnico corrente. O código, Git/CI e
`RESEARCH_FREEZE.md` prevalecem sobre documentação histórica.

## Estado canônico

```text
role = FROZEN_RESEARCH_ASSET + REUSABLE_COMPONENT_LIBRARY + NEGATIVE_RESULT_CASE
research_state = FROZEN                                # ver HANDOFF.md, 2026-09-04
scientific_state = CLOSED_FOR_H1_THROUGH_H11           # todas as 10 hipóteses julgadas
commercial_state = NOT_A_PRODUCT
new_scientific_trials = 0
```

As famílias de fatores JÁ JULGADAS (H1/H2/H4/H5/H6/H7/H8/H9/H10/H11 — 10 no
total, todas NOT_SUPPORTED) e a linha RJ estão encerradas/congeladas.
**H11** (momentum 12-1 em RETORNO TOTAL, janela restrita 2018-2022,
proventos reinvestidos — corrige o viés só-preço declarado nas 9
anteriores) foi julgada com rodada real na máquina do operador em
2026-09-04: **NOT_SUPPORTED** (IC95% cruza zero; DSR 0,8430 < 0,95,
N=10) — o maior DSR de todas as 10 hipóteses, mas ainda abaixo do
limiar. A pesquisa de fatores está formalmente esgotada, incluindo a
correção do viés metodológico. Ver HANDOFF.md "VEREDITO H11" para
detalhes completos. Reabertura de qualquer uma das 10 exige o dossiê
completo definido em `RESEARCH_FREEZE.md` e informação materialmente
nova.

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
