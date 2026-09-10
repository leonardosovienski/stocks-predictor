
# stocks-predictor

**Próxima tarefa:** [auditoria técnica integral, crítica e executável](docs/continuation/PROMPT_AUDITORIA_INTEGRAL_20260909.md).
O mandato completo foi consolidado com o usuário; sua execução ainda está pendente.
Ele amplia a revisão para lógica, arquitetura, dados, fontes, pressupostos e
finalidade econômica, sem obrigação de preservar a linha H21.
[Artefatos da sessão e cobertura da publicação](research/session-20260909/publication/README.md).
Os registros abaixo descrevem os resultados existentes, sujeitos à nova auditoria.

Projeto de pesquisa econômica de ações da B3. A linha ativa de validação é
**H21 — exposição simples via BOVA11**, medida em uma história exploratória
com resultado condicional. Eventos do ETF e despesas reais ainda impedem
concluir lucro líquido executável ou prever lucro futuro.
[Resultados](docs/research/2026-09-09-h21-results.md) e
[reprodução H21](research/session-20260909/h21/README.md).

O [complemento R2 de dados/fontes](docs/research/2026-09-09-data-completion-r2.md)
recuperou os 12 bancos únicos, reproduziu as auditorias das fontes 13/14 e reuniu
demonstrações BOVA11 que cobrem 2018 a março de 2026, incluindo comparativos.
As 2.159 cotações até 08/09/2026 da R1 estão preservadas, sem recalcular H21.
[Catálogo e pendências](docs/research/2026-09-09-data-readiness.json): cobertura
integral de eventos e despesas ainda parcial. XP é a preferência; canal/assessor,
capital, horizonte e limite de perda não foram informados. Rico é alternativa condicional.

H20 tem implementação de retenção, bandas, proventos e reserva de impostos;
sua reconstrução ampla está estacionada, com incremento inconclusivo.
H19 e avaliações anteriores preservam seus protocolos e limites.
Não há autorização para operar capital ou ativar o paper legado.

As linhas H1–H16 e `predictor-rj` permanecem como histórico científico. Os relatórios
antigos preservam resultados de suas respectivas versões; não descrevem o estado
corrente. [HANDOFF.md](HANDOFF.md) registra a continuidade mais recente.

**Leitura corrente:** [STOCKS_CURRENT_STATE.md](STOCKS_CURRENT_STATE.md) para estado
técnico atual e [docs/RJ_DESIGN.md](docs/RJ_DESIGN.md) para o protocolo RJ.
[docs/DESIGN.md](docs/DESIGN.md) e [HANDOFF.md](HANDOFF.md) preservam o domínio e a
continuidade histórica e devem ser interpretados pela data.

## Localização e documentação

Raiz local única: `C:\STOCKS`; código em `stocks-predictor`,
pesquisa/logs em `work`, entregas em `outputs`, prompt original em `instructions`.
ZIP de migração reunido; nove COTAHIST e os 12 bancos únicos recuperados,
com fontes 13/14 separadas em `data/recovery-r2`. Catálogo: `data/CATALOG.json`.
A árvore inteira de 60.023 caminhos não foi materializada.
[Mapa](docs/continuation/LOCAL_PATHS_20260909.json) e
[índice completo dos Markdown](docs/DOCUMENTATION_INDEX.md).

H21 integrada pelo [PR69](https://github.com/leonardosovienski/stocks-predictor/pull/69),
SHA `4a85d4317657ac5ddaffcacf889b6341cf9c4b0a`.
A [CI184 desse SHA](https://github.com/leonardosovienski/stocks-predictor/actions/runs/34386092297)
passou 782 testes regulares, cobertura 78%; 17 testes arquivados não executados.
Revisões documentais posteriores não são novos experimentos.
Relatórios e caminhos antigos preservam proveniência datada.

## Estado técnico

- Python: `>=3.13,<3.15`;
- package metadata: `pyproject.toml`;
- Core compartilhado: `predictor-core >=3.2,<4` por wheel oficial;
- Ops: não é dependência declarada deste domínio no estado atual;
- `vendor/predictor_core/` é preservado como artefato histórico de integridade e não é
  a dependência-alvo da arquitetura moderna;
- CI: Python 3.13, Ruff, Pyright no escopo de `pyproject.toml` (inclui H20, fontes, H21 e economics), pytest+coverage, build/wheel smoke e
  gitleaks.

A migração de infraestrutura não altera thresholds, famílias, universo, janelas,
FDR, seleção de episódios nem qualquer outro parâmetro científico congelado do RJ.

Uma primitiva econômica opt-in `REBALANCE/HOLD` vive em
`stocks_predictor/economic_gate.py`. Ela exige que o limite conservador da vantagem
bruta pague turnover e hurdle, mas ainda não está ligada ao walk-forward congelado nem
autoriza capital. Integração futura exige hipótese nova e janela forward nova.

## Linha histórica: predictor-rj

Pergunta central: existem condições, eventos ou padrões observáveis **antes** de
rallies em ações de empresas em RJ, de forma conhecível no momento da decisão?

O protocolo separa análise ex-post de análise point-in-time, trata censura,
pré-registra famílias e aplica correção por múltiplos testes. O estado científico
corrente continua sendo o documentado em `STOCKS_CURRENT_STATE.md`/`RJ_DESIGN`; modernizar
packaging, Core/Ops ou CI não constitui evidência de hipótese.

Os comandos `uv` desta seção são para Linux CI ou outro ambiente autorizado
com produção disponível. **Não executar instalações/venv no Windows atual.**
Aqui, Python 3.12.14 do Codex atende somente aos
[auxiliares stdlib H21](research/session-20260909/h21/README.md).
Python 3.13/Core/pytest não estão disponíveis localmente. Comandos RJ abaixo são
referência histórica; não iniciar automaticamente pesquisa ou ingestão.

```bash
uv sync --all-extras --python 3.13
uv run pytest -q
uv run pyright
uv run ruff check stocks_predictor tests main.py
uv build
```

Os testes específicos da mecânica RJ podem ser executados com:

```bash
uv run pytest tests/test_rj_smoke_synthetic.py tests/test_rj_power_gate.py -q
```

Ferramentas da linha RJ (contribuição 2026-08-24 — nenhum parâmetro
[RJ-FROZEN] alterado; são aditivas ao protocolo):

```bash
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
stocks_predictor/        implementação das linhas de pesquisa e simulação em ações
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
| Classificação do `poc_leak.py` | [`poc_leak.py`](poc_leak.py), `RESEARCH_FREEZE.md` §6 | `HISTORICAL_POC`, não reproduzível contra o Core 3.0.0 da época do fechamento |
| Fechamento da linha RJ (`ARCHIVED`) | `RESEARCH_FREEZE.md` §9, [`docs/RJ_DESIGN.md`](docs/RJ_DESIGN.md), [`docs/audit/kimi_2026-08-24/`](docs/audit/kimi_2026-08-24/) | Zero dados reais coletados; protocolo preservado, sem ingestão nova |
| Localização/backup do banco operacional real (`stocks.db`) | `RESEARCH_FREEZE.md` §1 | Caminho na máquina local, contagens por tabela, hash SHA-256 do backup offsite |
| Regra para reabrir qualquer fator ou a linha RJ | `RESEARCH_FREEZE.md` §11 (`reopen_policy`) | Exige 6 campos preenchidos (resultado anterior, motivo do fechamento, nova informação, etc.) — nunca decisão em silêncio |

**Verificação de que está tudo no Git remoto:** todo o conteúdo acima chegou à branch
`main` do GitHub via pull requests já mergeados
([#18](https://github.com/leonardosovienski/stocks-predictor/pull/18), [#19](https://github.com/leonardosovienski/stocks-predictor/pull/19), [#20](https://github.com/leonardosovienski/stocks-predictor/pull/20), [#21](https://github.com/leonardosovienski/stocks-predictor/pull/21),
[#22](https://github.com/leonardosovienski/stocks-predictor/pull/22)). Para confirmar localmente a qualquer momento:

```powershell
git fetch origin main
git log origin/main --oneline -10   # mostra os commits mais recentes
git show origin/main:RESEARCH_FREEZE.md | Select-Object -First 5   # confirma que existe na main remota
```

A validação confirmada da base H21 está vinculada ao SHA e à CI184 acima.
Para qualquer HEAD posterior, conferir a execução correspondente antes de declarar
a suíte aprovada. Contagens de versões antigas são histórico, não checks do HEAD.

## Fronteira econômica

Identificar retrospectivamente um rally ou encontrar associação estatística não prova
lucro. A linha RJ primeiro precisa demonstrar sinal temporal válido; somente uma etapa
econômica posterior pode testar entrada, saída, preço executável, liquidez, custos e
P&L prospectivo.

Nenhuma mudança de infraestrutura neste repositório autoriza capital real.
