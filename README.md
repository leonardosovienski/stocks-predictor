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
- Core compartilhado: `predictor-core 2.3.x` por wheel oficial;
- Ops compartilhado: `predictor-ops 3.1.x` por wheel oficial;
- `vendor/predictor_core/` é preservado como artefato histórico de integridade e não é
  a dependência-alvo da arquitetura moderna;
- CI: Python 3.13, Ruff, Pyright na linha RJ, pytest+coverage, build/wheel smoke e
  gitleaks.

A migração de infraestrutura não altera thresholds, famílias, universo, janelas,
FDR, seleção de episódios nem qualquer outro parâmetro científico congelado do RJ.

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
uv run ruff check src tests main.py
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
uv run python src/rj_power.py --n-companies 20 30 40 --effects 0.5 1.0 1.5 2.0 --fast

# runner integrado: universo -> episódios -> famílias -> judge -> relatório
uv run python src/rj_pipeline.py --db data/stocks.db --asof 2026-08-24 \
    --free-float-csv free_float.csv --out reports/rj_run.json
```

Módulos aditivos desta geração:

- `src/rj_power.py` — análise de poder/MDE prospectiva via Monte Carlo sobre
  o próprio judge (decide se o N disponível sustenta o desenho ANTES de
  coletar dado real);
- `src/rj_pipeline.py` — runner integrado fail-closed (universo -> episódios
  -> famílias -> judge -> relatório JSON + persistência idempotente),
  incluindo a checagem secundária (episódios múltiplos, janela de 252
  pregões) como verificação separada, nunca fundida ao veredito primário;
- `src/ingest_rj_universe.py` — snapshots datados e append-only da lista
  pública de emissores em RJ (migração 0005): a lista é um retrato de hoje;
  sem snapshots, quem saiu (falência/encerramento/deslistagem) some do
  universo histórico — viés de sobrevivência proibido pelo protocolo §3.
  Diff entre retratos gera a fila de revisão humana (source+approved_by);
- `src/ingest_cvm.py` — dados abertos da CVM: IPE (a data de ENTREGA do fato
  relevante é o `known_at` exigido pelo protocolo §8) e FRE (ações em
  circulação = free float da família `liquidity`); parsing por palavra-chave
  normalizada, fail-loud em coluna ausente;
- `src/rj_families_next.py` — famílias NEXT-GEN (MAX/lottery, emissão de
  ações, migração de base retail, Altman Z, CHS-NIMTA) inspiradas na
  literatura de distressed/lottery. EXPLORATÓRIAS: assert em código garante
  disjunção com as 8 pré-registradas — entrar no FDR exige NOVO pré-registro;
- `src/rj_judge_robust.py` — Romano-Wolf por permutação conjunta (robustez ao
  BH pré-registrado) e haircut out-of-sample de 36% (Harvey-Liu) para a
  futura etapa econômica;
- `src/rj_outcomes.py` — rally ajustado ao mercado (outcome AUXILIAR, nunca
  fundido aos congelados) e walk-forward expanding-window para a fase de
  validação preditiva com modelo;
- `src/rj_coda.py` — tratamento CoDa de razões contábeis (imputação de zeros
  auditável + CLR) para não perder empresas por dado faltante em N pequeno.

Testes correspondentes: `tests/test_rj_power.py`, `tests/test_rj_pipeline.py`
(inclui a trava de invariância do ajuste corporativo retroativo sobre os
scores das famílias), `tests/test_rj_next_gen.py` e `tests/test_rj_ingest.py`.

## Layout

```text
main.py                  entry point legado/CLI do domínio histórico
pyproject.toml           runtime, package e dependências compartilhadas
STOCKS_CURRENT_STATE.md  estado corrente desta geração
config.yaml              parâmetros do domínio cross-sectional histórico
config_rj.yaml           parâmetros congelados da linha RJ
docs/DESIGN.md           protocolo histórico de fatores
docs/RJ_DESIGN.md        protocolo canônico da linha RJ
src/                     implementação dos dois domínios
vendor/predictor_core/   snapshot legado preservado; não editar
tests/                   gates automatizados
data/                    dados locais/SQLite fora do Git
reports/                 resultados e registros históricos
```

## Fronteira econômica

Identificar retrospectivamente um rally ou encontrar associação estatística não prova
lucro. A linha RJ primeiro precisa demonstrar sinal temporal válido; somente uma etapa
econômica posterior pode testar entrada, saída, preço executável, liquidez, custos e
P&L prospectivo.

Nenhuma mudança de infraestrutura neste repositório autoriza capital real.
