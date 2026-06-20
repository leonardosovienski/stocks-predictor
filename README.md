# predictor-stocks

Domínio 2 de um framework de previsão multi-domínio (TCC): previsão **cross-sectional**
de ações da B3 — quais ações performam melhor *relativo às outras*. Motor interpretável
(momentum 12-1) primeiro, instrumento de medição (walk-forward + block bootstrap) segundo,
ML por último e só se pagar líquido.

**Documentos canônicos:** [docs/DESIGN.md](docs/DESIGN.md) (a constituição do projeto),
[HANDOFF.md](HANDOFF.md) (estado vivo, decisões, hipótese pré-registrada) e
[ECOSYSTEM_STATUS.md](../ECOSYSTEM_STATUS.md) na raiz (estado consolidado da plataforma).

## Estado atual

Marcos **M1–M6 implementados** e **rodados sobre dado real** — COTAHIST 2024+2025
ingerido (`prices_raw` cobre 2024-01-02 → 2025-12-30, 5,76M linhas). Suíte: **96 testes
verdes**. Consome o `predictor_core` via `vendor/` (não editar — `../predictor_core` é a
fonte; sync por `scripts/sync_core.py`).

**Veredito da H1 hoje:** com os 2 anos disponíveis (n=228 pregões), o IC95% da diferença de
Sharpe ≈ [−2,4, +0,7] **cruza zero → "não comprovada"**. Ler como **subpotente** (amostra
curta), não como "momentum não funciona". E note (DESIGN §9): a janela pré-registrada da H1
é **2018→** — os 2 anos atuais são um *proxy*, não o experimento pré-registrado. Veredito
defensável exige o COTAHIST histórico (ver "Pendências").

Classificação de produção: **pesquisa** — instrumento de coleta validado, amostra/experimento
ainda incompletos.

## Ambiente e como rodar

Esta máquina tem **apenas Python 3.14.6**. Runner canônico: `C:\Claude\.venv\Scripts\python.exe`
(carrega o stack completo: numpy, scipy, pandas, pytest). Rode de `C:\Claude\predictor-stocks`.
Atalho usado abaixo: `$py = "C:\Claude\.venv\Scripts\python.exe"`.

```powershell
& $py main.py                               # status (versões, hashes, contagens)
& $py main.py ingest <COTAHIST_AXXXX.ZIP>   # M1: parse posicional -> prices_raw
& $py main.py adjust                         # M2: detector de saltos -> quarentena
& $py main.py universe <YYYY-MM-DD>          # M3: universo point-in-time
& $py main.py backtest                       # M5: walk-forward + pedágio -> veredito H1
& $py main.py paper <YYYY-MM-DD>             # M6: carteira forward + liquida execução
& $py -m pytest tests/ -q                    # suíte (96 verdes — sempre verde no main)
```

**Override operacional:** a env var `STOCKS_DB_PATH` aponta toda a CLI para um banco
alternativo (snapshot/CI/dry-run) sem editar `config.yaml`. O gerador sintético
(`src/cotahist.py`) destrava o pipeline para teste sem o arquivo real da B3.

## Diagnósticos e validação — como rodar cada arquivo

| Arquivo | O que faz | Como rodar |
|---------|-----------|------------|
| `tests/` (suíte) | 96 testes — sempre verde no main | `& $py -m pytest tests/ -q` |
| `tests/test_lens2_coverage.py` | **Portão de aceite da LENTE 2** (cobertura ~95%) | `& $py -m pytest tests/test_lens2_coverage.py -v` |
| `lens2_calibration_study.py` | Estudo: percentil vs t-blocos × L × método → tabela de cobertura/largura/custo | `& $py lens2_calibration_study.py` |
| `lens2_coverage_test.py` | Mede a cobertura da régua ATUAL (percentil) — mostra a liberalidade | `& $py lens2_coverage_test.py` |
| `dividend_sensitivity.py` | Sensibilidade do veredito da H1 ao viés de dividendo (rota-b) | `& $py dividend_sensitivity.py` |
| `check_db.py` | Inspeção rápida do SQLite (cobertura, contagens) | `& $py check_db.py` |

> A régua calibrada vive em `predictor_core.stats.calibrated_ci` (intervalo-t por blocos,
> cobertura validada ~95%). O default da plataforma continua o percentil (liberal, medido
> em 85–93%); migrar um experimento para a calibrada é decisão de **novo pré-registro**.

**Utilitários de plataforma** (em `C:\Claude\scripts`, rodar de qualquer lugar):
`test-audit-loop.ps1` (roda as 3 suítes + sync-check) · `sync_all.ps1` (propaga o
`predictor_core` aos vendors) · `events_tail.py` (painel unificado do `events.jsonl`).

## Estrutura

```
main.py                  ponto de entrada (status + comandos M1–M6)
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

## Pendências (o que falta para um veredito defensável)

- **Janela da H1:** obter COTAHIST 2010–2025 e rodar a H1 **exatamente como pré-registrada**
  (janela 2018→). Os 2 anos atuais são proxy subpotente.
- **Robustez de execução (M5):** liquidar a 3 preços (abertura/fechamento D+1/pior) + 2× custo
  — o DESIGN §M5 chama isso de obrigatório (e fragilidade aí é refutação); hoje só 1 preço.
- **Ajustes (M2):** `adjustments` está vazia (rota-b, só-preço); splits são **quarentenados**,
  não reproduzidos na série ajustada — o aceite "5+ splits reproduzidos" do M2 segue aberto.
- **Régua:** migrar (sob novo pré-registro) do percentil liberal para `calibrated_ci`.

## Fronteira

Instrumento de medição metodológica para um TCC. **Não é recomendação de investimento.**
