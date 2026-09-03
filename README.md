# stocks-predictor

Predictor econômico de ações da B3 do ecossistema PREDICTORS. A linha de pesquisa
**ativa** é `predictor-rj`: investigar, com informação disponível no instante da
decisão, se condições observáveis antecedem rallies especulativos em empresas em
recuperação judicial.

O domínio cross-sectional/fatores anterior permanece preservado no repositório como
histórico científico. Seus vereditos não são apagados nem promovidos pela linha RJ.

**Leitura corrente:** [STOCKS_CURRENT_STATE.md](STOCKS_CURRENT_STATE.md) para estado
técnico atual e [docs/RJ_DESIGN.md](docs/RJ_DESIGN.md) para o protocolo RJ.
[docs/DESIGN.md](docs/DESIGN.md) e [HANDOFF.md](HANDOFF.md) preservam o domínio e a
continuidade histórica e devem ser interpretados pela data.

## Estado técnico

- Python: `>=3.13,<3.15`;
- package metadata: `pyproject.toml`;
- Core compartilhado: `predictor-core 3.0.x` por wheel oficial;
- Ops: não é dependência declarada deste domínio no estado atual;
- `vendor/predictor_core/` é preservado como artefato histórico de integridade e não é
  a dependência-alvo da arquitetura moderna;
- CI: Python 3.13, Ruff, Pyright na linha RJ, pytest+coverage, build/wheel smoke e
  gitleaks.

A migração de infraestrutura não altera thresholds, famílias, universo, janelas,
FDR, seleção de episódios nem qualquer outro parâmetro científico congelado do RJ.

Uma primitiva econômica opt-in `REBALANCE/HOLD` vive em
`stocks_predictor/economic_gate.py`. Ela exige que o limite conservador da vantagem
bruta pague turnover e hurdle, mas ainda não está ligada ao walk-forward congelado nem
autoriza capital. Integração futura exige hipótese nova e janela forward nova.

## Linha ativa: predictor-rj

Pergunta central: existem condições, eventos ou padrões observáveis **antes** de
rallies em ações de empresas em RJ, de forma conhecível no momento da decisão?

O protocolo separa análise ex-post de análise point-in-time, trata censura,
pré-registra famílias e aplica correção por múltiplos testes. O estado científico
corrente continua sendo o documentado em `STOCKS_CURRENT_STATE.md`/`RJ_DESIGN`; modernizar
packaging, Core/Ops ou CI não constitui evidência de hipótese.

```powershell
uv sync --all-extras --python 3.13
uv run pytest -q
uv run pyright
uv run ruff check stocks_predictor tests main.py
uv build
```

Os testes específicos da mecânica RJ podem ser executados com:

```powershell
uv run pytest tests/test_rj_smoke_synthetic.py tests/test_rj_power_gate.py -q
```

Ferramentas da linha RJ (contribuição 2026-08-24 — nenhum parâmetro
[RJ-FROZEN] alterado; são aditivas ao protocolo):

```powershell
# poder prospectivo: dado o N do universo, qual o menor efeito detectável?
uv run python stocks_predictor/rj_power.py --n-companies 20 30 40 --effects 0.5 1.0 1.5 2.0 --fast

# runner integrado: universo -> episódios -> famílias -> judge -> relatório
uv run python stocks_predictor/rj_pipeline.py --db data/stocks.db --asof 2026-08-24 \
    --free-float-csv free_float.csv --out reports/rj_run.json
```

Módulos aditivos desta geração:

- `stocks_predictor/rj_power.py` — análise de poder/MDE prospectiva via Monte Carlo sobre
  o próprio judge (decide se o N disponível sustenta o desenho ANTES de
  coletar dado real);
- `stocks_predictor/rj_pipeline.py` — runner integrado fail-closed (universo -> episódios
  -> famílias -> judge -> relatório JSON + persistência idempotente),
  incluindo a checagem secundária (episódios múltiplos, janela de 252
  pregões) como verificação separada, nunca fundida ao veredito primário;
- `stocks_predictor/ingest_rj_universe.py` — snapshots datados e append-only da lista
  pública de emissores em RJ (migração 0005): a lista é um retrato de hoje;
  sem snapshots, quem saiu (falência/encerramento/deslistagem) some do
  universo histórico — viés de sobrevivência proibido pelo protocolo §3.
  Diff entre retratos gera a fila de revisão humana (source+approved_by);
- `stocks_predictor/ingest_cvm.py` — dados abertos da CVM: IPE (a data de ENTREGA do fato
  relevante é o `known_at` exigido pelo protocolo §8) e FRE (ações em
  circulação = free float da família `liquidity`); parsing por palavra-chave
  normalizada, fail-loud em coluna ausente;
- `stocks_predictor/rj_families_next.py` — famílias NEXT-GEN (MAX/lottery, emissão de
  ações, migração de base retail, Altman Z, CHS-NIMTA) inspiradas na
  literatura de distressed/lottery. EXPLORATÓRIAS: assert em código garante
  disjunção com as 8 pré-registradas — entrar no FDR exige NOVO pré-registro;
- `stocks_predictor/rj_judge_robust.py` — Romano-Wolf por permutação conjunta (robustez ao
  BH pré-registrado) e haircut out-of-sample de 36% (Harvey-Liu) para a
  futura etapa econômica;
- `stocks_predictor/rj_outcomes.py` — rally ajustado ao mercado (outcome AUXILIAR, nunca
  fundido aos congelados) e walk-forward expanding-window para a fase de
  validação preditiva com modelo;
- `stocks_predictor/rj_coda.py` — tratamento CoDa de razões contábeis (imputação de zeros
  auditável + CLR) para não perder empresas por dado faltante em N pequeno.

Testes correspondentes: `tests/test_rj_power.py`, `tests/test_rj_pipeline.py`
(inclui a trava de invariância do ajuste corporativo retroativo sobre os
scores das famílias), `tests/test_rj_next_gen.py` e `tests/test_rj_ingest.py`.

## Layout

```text
main.py                  entry point legado/CLI do domínio histórico
pyproject.toml           runtime, package e dependências compartilhadas
STOCKS_CURRENT_STATE.md  estado corrente desta geração
RESEARCH_FREEZE.md       manifesto do congelamento científico (ver seção abaixo)
config.yaml              parâmetros do domínio cross-sectional histórico
config_rj.yaml           parâmetros congelados da linha RJ
docs/DESIGN.md           protocolo histórico de fatores
docs/RJ_DESIGN.md        protocolo canônico da linha RJ
stocks_predictor/                     implementação dos dois domínios
vendor/predictor_core/   snapshot legado preservado; não editar
tests/                   gates automatizados
data/                    dados locais/SQLite fora do Git
reports/                 resultados e registros históricos
trials.json              registro legado de trials (schema original, versionado)
trials_v2.json           registro de trials no schema prospectivo canônico
tools/                   utilitários de manutenção (ex.: migração de schema de trials)
```

## Congelamento científico (RESEARCH_FREEZE.md) — mapa do que está onde

O domínio cross-sectional de fatores (momentum, low-vol, vol-target, reversão e a
interseção momentum×low-vol) está **congelado** — pesquisa ativa encerrada, nenhuma
família reaberta sem passar pela `reopen_policy`. Tudo que sustenta essa decisão está
documentado e versionado; nada disto vive só no chat que gerou:

| O quê | Onde no repo | O que prova |
|---|---|---|
| Manifesto completo do congelamento (17 seções: preservação, schema de trials, PIT, purge/embargo, vendor, custos, multiplicidade, RJ, component inventory, case studies, red team, valor comercial, checkpoints finais) | [`RESEARCH_FREEZE.md`](RESEARCH_FREEZE.md) | Decisão e evidência de cada item, com citação de arquivo/linha |
| Vereditos dos 6 fatores testados (H1, H2, H4, H5, H6, H8 — todos "não comprovados"; H5 é anti-sinal) | [`reports/`](reports/), citados em `RESEARCH_FREEZE.md` §12 | Resultado científico de cada hipótese |
| Schema de trials legado | [`trials.json`](trials.json) | Registro original, intocado |
| Schema de trials prospectivo (canônico) | [`trials_v2.json`](trials_v2.json) | Migração não-destrutiva/idempotente do legado |
| Script da migração de schema | [`tools/migrate_trials_schema.py`](tools/migrate_trials_schema.py) | Reprodutível: `python tools/migrate_trials_schema.py --check` |
| Decisão sobre purge/embargo (`DOCUMENTED_HISTORICAL_LIMITATION`) | `RESEARCH_FREEZE.md` §4 | Config declara mas não implementa; decisão explícita, não silenciosa |
| Prova em código de que purge/embargo é inerte hoje | [`tests/test_purge_embargo_limitation.py`](tests/test_purge_embargo_limitation.py) | Quebra sozinho se alguém implementar purge de verdade no futuro |
| Prova em código de que o runtime não resolve para o vendor congelado | [`tests/test_core_import_path.py`](tests/test_core_import_path.py) | `predictor_core` sempre resolve para o pacote instalado, não `vendor/` |
| Prova em código de survivorship/PIT (delisting + listagem tardia) | [`tests/test_universe.py`](tests/test_universe.py) | Inclui `test_excludes_delisted_ticker_stale_before_window` e `test_newly_listed_ticker_does_not_appear_before_its_ipo_date` |
| Classificação do `vendor/predictor_core/` | `RESEARCH_FREEZE.md` §5 | `ARCHIVE_FOR_REPRODUCTION`, guard ativo em `tests/conftest.py` |
| Classificação do `poc_leak.py` | [`poc_leak.py`](poc_leak.py), `RESEARCH_FREEZE.md` §6 | `HISTORICAL_POC`, não reproduzível contra o Core 3.0.0 atual |
| Fechamento da linha RJ (`ARCHIVED`) | `RESEARCH_FREEZE.md` §9, [`docs/RJ_DESIGN.md`](docs/RJ_DESIGN.md), [`docs/audit/kimi_2026-08-24/`](docs/audit/kimi_2026-08-24/) | Zero dados reais coletados; protocolo preservado, sem ingestão nova |
| Localização/backup do banco operacional real (`stocks.db`) | `RESEARCH_FREEZE.md` §1 | Caminho na máquina local, contagens por tabela, hash SHA-256 do backup offsite |
| Regra para reabrir qualquer fator ou a linha RJ | `RESEARCH_FREEZE.md` §11 (`reopen_policy`) | Exige 6 campos preenchidos (resultado anterior, motivo do fechamento, nova informação, etc.) — nunca decisão em silêncio |

**Verificação de que está tudo no Git remoto:** todo o conteúdo acima chegou à branch
`main` do GitHub via pull requests já mergeados
([#18](../../pull/18), [#19](../../pull/19), [#20](../../pull/20), [#21](../../pull/21),
[#22](../../pull/22)). Para confirmar localmente a qualquer momento:

```powershell
git fetch origin main
git log origin/main --oneline -10   # deve mostrar os merges dos PRs #18-#22
git show origin/main:RESEARCH_FREEZE.md | Select-Object -First 5   # confirma que existe na main remota
uv run pytest -q                    # suíte completa, incluindo os testes novos do congelamento
```

A suíte completa (252 testes, incluindo os 5 novos desta rodada) passa 100% sobre o
`origin/main` no momento deste commit.

## Fronteira econômica

Identificar retrospectivamente um rally ou encontrar associação estatística não prova
lucro. A linha RJ primeiro precisa demonstrar sinal temporal válido; somente uma etapa
econômica posterior pode testar entrada, saída, preço executável, liquidez, custos e
P&L prospectivo.

Nenhuma mudança de infraestrutura neste repositório autoriza capital real.
