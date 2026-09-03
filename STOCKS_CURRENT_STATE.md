# Stocks Predictor — estado corrente

**Vigência:** 2026-09-03

Este é o ponto de entrada técnico corrente. O código, Git/CI e
`RESEARCH_FREEZE.md` prevalecem sobre documentação histórica.

## Estado canônico

```text
role = FROZEN_RESEARCH_ASSET + REUSABLE_COMPONENT_LIBRARY + NEGATIVE_RESULT_CASE
research_state = FROZEN_EXCEPT_H7_PENDING_JUDGMENT   # ver HANDOFF.md, 2026-09-03
scientific_state = CLOSED_FOR_H1_H2_H4_H5_H6_H8      # H7 pré-registrada, não julgada
commercial_state = NOT_A_PRODUCT
new_scientific_trials = 1   # H7, pré-registrada 2026-09-03, código pronto, rodada real pendente
```

As famílias de fatores JÁ JULGADAS (H1/H2/H4/H5/H6/H8) e a linha RJ estão
encerradas/congeladas. Não reinterpretar esses resultados negativos nem
reabri-los sem o dossiê completo definido em `RESEARCH_FREEZE.md`. **H7**
(fator de qualidade, ROE isolado) foi pré-registrada por decisão explícita do
operador em 2026-09-03 — não é reabertura, é a única fronteira de dado novo
que restava; ver HANDOFF.md para o pré-registro completo e os passos
mecânicos pendentes (rodada real exige `stocks.db` real + rede à CVM,
indisponíveis neste ambiente de auditoria).

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
