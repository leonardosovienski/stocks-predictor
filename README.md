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
editar — `predictor-core` é a fonte). Suíte: `py -3.12 -m pytest tests/ -q` (93 verdes).

```powershell
py -3.12 main.py                              # status (versões, hashes, contagens)
py -3.12 main.py ingest <COTAHIST_AXXXX.ZIP>  # M1: parse posicional -> prices_raw
py -3.12 main.py adjust                        # M2: detector de saltos -> quarentena
py -3.12 main.py universe <YYYY-MM-DD>         # M3: universo point-in-time
py -3.12 main.py backtest                      # M5: walk-forward + pedágio -> veredito H1
py -3.12 main.py paper <YYYY-MM-DD>            # M6: carteira forward + liquida execução
```
Sem COTAHIST real, o `backtest` responde "inconclusivo"; o gerador sintético
(`src/cotahist.py`) destrava o pipeline para teste.

## Status

M0 (Gênese) completo. Próximo: M1 — ingestão COTAHIST (bloqueado em obter o layout
posicional oficial da B3; o parser não pode ser escrito de memória).

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
