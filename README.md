<!-- ════════════════════════════════════════════════════════════════════
RECONCILIAÇÃO DE EVIDÊNCIA — 2026-06-19 (corrige drift; fonte: ECOSYSTEM_STATUS.md na raiz)
Marcas: [V] verificada por execução · [I] inferida · [NV] não verificada.

- [V] Ambiente: a máquina tem APENAS Python 3.14.6 (não 3.13). Rode tudo com a venv
  raiz C:\Claude\.venv\Scripts\python.exe. O texto "Python 3.13 global" abaixo é DRIFT.
- [V] Marcos: M1–M6 estão implementados E rodados sobre DADO REAL — COTAHIST 2024+2025
  ingerido (5,76M linhas). As frases "M0 completo / próximo M1 bloqueado" e "validados
  em dados sintéticos" abaixo são DRIFT (contradição interna do README antigo).
- [V] Instrumento validado: parser reconcilia 5/5 blue-chips com jan/2024; split do
  BBAS3 (2024-04-16) detectado e quarentenado. Cadeia de medição calibrada.
- [V] Veredito H1 sobre dado real: NÃO COMPROVADA (n=228, IC ΔSharpe ≈ [-2,4, +0,7],
  cruza zero). Interpretar como SUBPOTENTE (mudo), não como "momentum não funciona".
- [V] Override operacional: $STOCKS_DB_PATH aponta a CLI para um DB alternativo.
- [I] Próximo experimento decisivo: rodar a H1 congelada sobre 2010–2025 (mais anos).
- Status de produção: PESQUISA (instrumento pronto, amostra curta).
═════════════════════════════════════════════════════════════════════ -->

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
editar — `predictor-core` é a fonte). Suíte: `python -m pytest tests/ -q` (93 verdes).

```powershell
python main.py                              # status (versões, hashes, contagens)
python main.py ingest <COTAHIST_AXXXX.ZIP>  # M1: parse posicional -> prices_raw
python main.py adjust                        # M2: detector de saltos -> quarentena
python main.py universe <YYYY-MM-DD>         # M3: universo point-in-time
python main.py backtest                      # M5: walk-forward + pedágio -> veredito H1
python main.py paper <YYYY-MM-DD>            # M6: carteira forward + liquida execução
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
