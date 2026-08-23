# predictor-stocks

Domínio 2 de um framework de previsão multi-domínio (TCC): previsão **cross-sectional**
de ações da B3 — quais ações performam melhor *relativo às outras*. Motor interpretável
(momentum 12-1) primeiro, instrumento de medição (walk-forward + block bootstrap) segundo,
ML por último e só se pagar líquido.

**Documentos canônicos:** [docs/DESIGN.md](docs/DESIGN.md) (a constituição do projeto) e
[HANDOFF.md](HANDOFF.md) (estado atual, decisões, hipótese pré-registrada).

## Estado atual / Como rodar

Marcos **M1–M6 implementados** (núcleo, validados em dados sintéticos); o veredito real
da H1 exige o COTAHIST físico da B3. Consome o `predictor_core` via `vendor/` (não
editar — `predictor-core` é a fonte). Python 3.13 global, sem venv (DESIGN §1).
Suíte: `py -3.13 -m pytest tests/ -q` (144 verdes).

```powershell
py -3.13 main.py                              # status (versões, hashes, contagens)
py -3.13 main.py ingest <COTAHIST_AXXXX.ZIP>  # M1: parse posicional -> prices_raw
py -3.13 main.py adjust                        # M2: detector de saltos -> quarentena
py -3.13 main.py universe <YYYY-MM-DD>         # M3: universo point-in-time
py -3.13 main.py backtest                      # M5: walk-forward + pedágio -> veredito H1 + relatório
py -3.13 main.py paper <YYYY-MM-DD>            # M6: carteira forward + liquida execução
py -3.13 main.py analyst [rótulo]             # §9b: briefing consultivo read-only (reports/ai/)
py -3.13 -m pytest tests/ -q                  # suíte — sempre verde no main
```
Sem COTAHIST real, o `backtest` responde "inconclusivo"; o gerador sintético
(`src/cotahist.py`) destrava o pipeline para teste. `backtest` grava um relatório do
veredito em `reports/` e emite um evento de telemetria em `events.jsonl`.

## Estrutura

```
main.py                  ponto de entrada (status + comandos M1–M6 + analyst)
docs/DESIGN.md           constituição — ler inteiro antes de mexer
HANDOFF.md               estado vivo do projeto
config.yaml              parâmetros (H1-FROZEN = imutáveis pós-rodada)
vendor/predictor_core/   biblioteca core vendorizada (net/obs/infra/stats/replay + testing)
src/                     pipeline (db, config, ingest, adjust, universe, factor,
                         portfolio, execution, backtest, report, paper, analyst, ...)
tests/                   pytest — sempre verde no main
data/                    SQLite + arquivos COTAHIST (fora do git)
reports/                 relatórios do veredito (fora do git); reports/ai/ = analista
```

## Fronteira

Instrumento de medição metodológica para um TCC. **Não é recomendação de investimento.**

## Domínio novo: predictor-rj (event study, RJ na B3)

Módulo independente adicionado em 2026-08-23: rallies ≥50% em ações de
empresas em recuperação judicial. Reaproveita `prices_raw`/`vendor/`, schema
próprio (`0004_rj_domain_schema`), config separado (`config_rj.yaml`).
Documento canônico: [docs/RJ_DESIGN.md](docs/RJ_DESIGN.md). Ver HANDOFF.md
para estado atual — M0, dados sintéticos, `rj_universe` ainda vazia.

```powershell
py -3.13 -m pytest tests/test_rj_smoke_synthetic.py tests/test_rj_power_gate.py -q
```

