# predictor-stocks

Domínio 2 de um framework de previsão multi-domínio (TCC): previsão **cross-sectional**
de ações da B3 — quais ações performam melhor *relativo às outras*. Motor interpretável
(momentum 12-1) primeiro, instrumento de medição (walk-forward + block bootstrap) segundo,
ML por último e só se pagar líquido.

**Documentos canônicos:** [docs/DESIGN.md](docs/DESIGN.md) (a constituição do projeto) e
[HANDOFF.md](HANDOFF.md) (estado atual, decisões, hipótese pré-registrada).

## Estado atual / Como rodar

Marcos **M1–M6 implementados** (núcleo, validados em dados sintéticos) + Ondas 0–2 de
governança/julgamento (2026-07-02); o veredito real da H1 exige o COTAHIST físico da
B3. Consome o `predictor_core` via `vendor/` (não editar à toa — mudança exige bump de
VERSION + `python scripts/sync_core.py --stamp`; a suíte verifica os hashes). Suíte:
`python -m pytest tests/ -q` (116 verdes; 2 `slow` de ~70s, deseleção `-m "not slow"`).

```powershell
python main.py                              # status (versões, hashes, contagens)
python main.py ingest <COTAHIST_AXXXX.ZIP>  # M1: parse posicional -> prices_raw
python main.py adjust                       # M2: detector de saltos -> quarentena
python main.py universe <YYYY-MM-DD>        # M3: universo point-in-time
python main.py backtest                     # M5: walk-forward + pedágio -> veredito H1
python main.py paper <YYYY-MM-DD>           # M6: carteira forward + liquida execução
```
Sem COTAHIST real, o `backtest` responde "inconclusivo"; o gerador sintético
(`src/cotahist.py`) destrava o pipeline para teste.

## Status

M0–M6 núcleo completo sobre dados sintéticos; Ondas 0–2 (governança, pedágio de 2
lentes real, execução D+1 open, replay estrutural, telemetria) fechadas em 2026-07-02.
Próximo: carregar o COTAHIST real (golden tests sobre registros de verdade) e rodar o
veredito da H1 uma única vez, como pré-registrado. Estado detalhado: `HANDOFF.md`.

## Rodar

Python 3.13 global, sem venv (restrição de ambiente — ver DESIGN §1):

```powershell
python main.py              # status do projeto (somente leitura)
python -m pytest tests/ -v  # suíte de testes — deve estar sempre verde
```

Os comandos de pipeline (`ingest`, `adjust`, `backtest`, `paper`) nascem com os
respectivos marcos; antes disso, `main.py` responde qual marco os libera.

## Estrutura

```
main.py                  ponto de entrada (status; comandos nascem por marco)
docs/DESIGN.md           constituição — ler inteiro antes de mexer
HANDOFF.md               estado vivo do projeto
config.yaml              parâmetros (H1-FROZEN = imutáveis pós-rodada)
vendor/predictor_core/   biblioteca core vendorizada (sync via scripts/sync_core.py)
src/                     pipeline (db, config, ingest, adjust, universe, factor, ...)
scripts/                 utilitários dev (sync_core.py)
tests/                   pytest — sempre verde no main
data/                    SQLite + arquivos COTAHIST (fora do git)
reports/ai/              artefatos consultivos do analista IA (fora do git)
```

## Fronteira

Instrumento de medição metodológica para um TCC. **Não é recomendação de investimento.**
