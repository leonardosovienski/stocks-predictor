# Stocks Predictor — estado corrente

**Vigência:** 2026-09-04

Este é o ponto de entrada técnico corrente. O código, Git/CI e
`RESEARCH_FREEZE.md` prevalecem sobre documentação histórica.

## Estado canônico

```text
role = FROZEN_RESEARCH_ASSET + REUSABLE_COMPONENT_LIBRARY + NEGATIVE_RESULT_CASE
research_state = FROZEN
scientific_state = CLOSED
commercial_state = NOT_A_PRODUCT
new_scientific_trials = 0
```

As famílias de fatores e a linha RJ estão encerradas/congeladas — **7 hipóteses
julgadas (H1/H2/H4/H5/H6/H7/H8), 0 comprovadas.** H7 (fator de qualidade, ROE
isolado, dado real DFP/CVM 2018-2026) foi pré-registrada e julgada em
2026-09-03/04 (decisão explícita do operador de testar a única fronteira de
dado novo que restava): IC 95% diff-Sharpe cruza zero, DSR 0,5795 < 0,95 —
NÃO COMPROVADA, mesmo resultado das seis anteriores. Não procurar novo alpha
nem reinterpretar resultados negativos. Reabertura (de qualquer uma das 7)
exige o dossiê completo definido em `RESEARCH_FREEZE.md` e informação
materialmente nova. Ver HANDOFF.md "VEREDITO H7" para o registro completo.

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
