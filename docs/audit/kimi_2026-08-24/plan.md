# Plano de Execução — Auditoria stocks-predictor (estudo RJ)

## Estágio 0 — Setup
- Clonar repo (branch main), ler README.md, docs/RJ_DESIGN.md, config_rj.yaml, STOCKS_CURRENT_STATE.md
- Instalar deps; verificar wheels predictor-core/ops vs vendor/predictor_core shim
- Rodar suíte pytest baseline

## Estágio 1 — Auditoria profunda (subagents paralelos)
- A1 (reviewer): domínio RJ core — rj_episodes, rj_families, rj_judge vs RJ_DESIGN.md
- A2 (reviewer): 8 módulos PR#5 — rj_power, rj_pipeline, ingest_rj_universe, ingest_cvm, rj_families_next, rj_judge_robust, rj_outcomes, rj_coda
- A3 (reviewer): domínio histórico — factor.py, backtest.py, adjust.py
- Foco: lookahead, off-by-one, div/0, None silencioso, empates min/max, seeds, I/O, regras 1-6

## Estágio 2 — Testes e validação funcional (coder)
- pytest completo com tracebacks
- rj_power.py --fast: validar tabela poder/MDE
- SQLite sintético + rj_pipeline end-to-end + relatório JSON
- Testes novos reproduzindo bugs (teste antes da correção)

## Estágio 3 — Correções e melhorias (coder)
- Corrigir bugs confirmados com testes
- Melhorias de engenharia sem violar regras
- Metodologia nova apenas como módulos next-gen com assert de disjunção

## Estágio 4 — Entrega
- Relatório estruturado (bugs, correções, riscos, melhorias, backlog)
- Commits limpos / format-patch em /mnt/agents/output/
