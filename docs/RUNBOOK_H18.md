# Runbook — do zero até medir os critérios da H18/H19

**Objetivo:** sair de uma máquina limpa e chegar às contagens que respondem
os critérios de aceite 2, 3 e 4 da auditoria de 2026-09-04
(`reports/auditoria_2026-09-04.md`) — os que nunca foram medidos.

**O que este runbook NÃO faz:** não roda H17, H18 nem H19. Rodar qualquer
uma delas hoje é prematuro (ver §7).

> **Sobre a procedência dos comandos.** Os comandos abaixo foram lidos do
> código (`main.py`, `tools/*.py`) e do `HANDOFF.md`, não escritos de
> memória. As etapas §0–§2 e §6 foram exercitadas; as que dependem de rede
> à CVM/B3 (§3–§5) **não foram** — nenhuma sessão de agente teve acesso a
> `dados.cvm.gov.br` (403 na política de rede). Onde eu não verifiquei,
> está marcado.

---

## 0. Pré-requisitos (uma vez por máquina)

Windows, **Python 3.13 global**, **nunca criar venv** (EDR corporativo
quarentena venvs — regra do `CLAUDE.md`).

```powershell
py -3.13 --version        # deve responder 3.13.x  (nesta máquina: 3.13.14)
```

**Nesta máquina, `python` NÃO é o 3.13.** Resolve para
`C:\Users\Superleo13\AppData\Local\Python\pythoncore-3.14-64\python.exe`
(3.14.6), verificado em 2026-09-06. Por isso `py -3.13` em tudo, sem exceção
— e por isso as dependências precisam ser instaladas com `py -3.13 -m pip`,
ou dá `ModuleNotFoundError` sem explicar a causa.

**Use `py -3.13` em TODOS os comandos deste runbook, não `python`.** Numa
máquina com mais de um interpretador, `python` resolve para o que estiver
primeiro no PATH — que pode ser um 3.14 ou 3.12. O `pyproject.toml` aceita
`>=3.13,<3.15`, mas o CI exercita **só o 3.13**, e ingestão que escreve no
banco não é lugar para estrear interpretador não testado.

Se `py -3.13` não responder, **pare**: instale o 3.13 antes de seguir, ou
decida conscientemente (e registre no HANDOFF) rodar noutra versão.

O `predictor-core` **não está no PyPI público** — distribuição só por wheel
de GitHub Release do repo irmão:

```powershell
py -3.13 -m pip install --upgrade "https://github.com/leonardosovienski/core-predictor/releases/download/v3.2.0/predictor_core-3.2.0-py3-none-any.whl"
py -3.13 -m pip install --upgrade PyYAML pytest
```

As dependências ficam no site-packages **daquele** interpretador. Instalar
com `python` e rodar com `py -3.13` (ou o contrário) dá
`ModuleNotFoundError` sem explicar a causa.

Sintoma de core desatualizado: `pyproject.toml` exige `>=3.2,<4`; uma 3.1 ou
anterior instalada quebra o import com erro pouco óbvio. Confira com
`python -c "import predictor_core; print(predictor_core.__version__)"` — tem
que dizer `3.2.0`.

> **Antes da medição, sob 3.2.0 (migração de 2026-09-06).** O atestado em
> `trials.harness_attestation.json` foi emitido com o core 3.1.0 e **um bump do
> core invalida o atestado**: reemita antes de rodar, ou a H18 não registra
> trial. E o 3.2.0 recusa emitir atestado a partir de árvore de trabalho suja —
> `git status` limpo antes de reemitir, senão o `code_version` sai com `;dirty`
> e a trial nasce marcada como irreprodutível. O ganho que justificou a
> migração: o Deflated Sharpe agora **trava** (`strict`) quando o desconto não é
> estimável, em vez de devolver PSR disfarçado de DSR em silêncio.

---

## 1. Repo atualizado

```powershell
cd C:\Users\Superleo13\stocks-predictor-work
git checkout main
git pull origin main
```

**Este é o caminho REAL, verificado em 2026-09-06.** Uma versão anterior
deste runbook mandava `cd C:\Claude-projetos\Claude\stocks-predictor`, que
NÃO EXISTE — era um palpite. `C:\Claude-projetos\Claude` contém apenas
`lol-predictor`.

### ⚠️ Existem QUATRO checkouts deste projeto na máquina

Rodar no errado grava no banco errado, sem aviso:

| caminho | `stocks.db` |
|---|---|
| `C:\Users\Superleo13\stocks-predictor-work` | **o real (~1,1M linhas)** |
| `C:\Users\Superleo13\.kimi-work\predictors-audit\stocks-predictor` | ~108 KB, vazio |
| `C:\Users\Superleo13\Documents\Codex\2026-08-27\le-x20\work\repo` | ~116 KB, vazio |
| `C:\Users\Superleo13\Documents\Codex\2026-09-02\...` | ~140 KB, vazio |

Confirme sempre com `python main.py`: `prices_raw` tem de dar ~1.149.872.
Se der 0, você está no checkout errado.

Se o caminho mudar um dia, localize assim (não adivinhe):

```powershell
Get-ChildItem C:\Users\Superleo13 -Recurse -Depth 5 -Directory -Filter stocks_predictor -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
```

### Artefatos LOCAIS não versionados — não apague

Vivem na raiz do repo, fora do git, e a ingestão depende deles:

    universo_2018_2026.txt        <- ingest_h7_real.py e ingest_fre_shares_real.py
    ticker_of_2019.json
    ticker_of_proposto.json
    dfp_2023_companies.txt
    dividend_exploration.txt
    universo_snapshots.txt

Se `universo_2018_2026.txt` sumir, `ingest_fre_shares_real.py` deriva o
universo do próprio banco; `ingest_h7_real.py` NÃO — ele quebra.

**Todo comando deste runbook roda a partir da raiz do repositório.**
`git pull` de outro diretório responde `fatal: not a git repository`, e
`main.py`/`tools\*.py` viram `No such file or directory`.

Precisa conter os PRs #52, #53 e #54 (correção do FRE + os dois scripts).

---

## 2. Diagnóstico — onde você está

```powershell
py -3.13 main.py                    # status: config_hash, contagem por tabela, trials
py -3.13 -m pytest tests\ -q        # precisa estar VERDE antes de qualquer ingestão
```

Leia a contagem de `prices_raw` no status:

| `prices_raw` | significado | vá para |
|---|---|---|
| ~1,1 milhão | banco real, pronto | **§4** |
| 0 | só schema | **§3** |

---

## 3. [só se `prices_raw` = 0] Reconstruir a base de preços

**Rede limpa.** Não verificado por mim — o download da B3 é inalcançável do
ambiente do agente.

Baixar os COTAHIST anuais (a função existe; não há CLI para ela):

```powershell
py -3.13 -c "import sys; sys.path.insert(0,'stocks_predictor'); import ingest_cotahist as ic; [ic.download_cotahist(a,'data/cotahist') for a in range(2016,2027)]"
```

Carregar cada zip e rodar o detector de saltos:

```powershell
Get-ChildItem data\cotahist\COTAHIST_A*.ZIP | ForEach-Object { py -3.13 main.py ingest $_.FullName }
py -3.13 main.py adjust                        # detector de saltos -> quarentena
py -3.13 main.py splits-review splits.csv      # exporta candidatos p/ revisão HUMANA
# revise splits.csv à mão, aprove linha a linha, então:
py -3.13 main.py splits-import splits.csv
```

O passo de revisão humana dos splits não é burocracia: `adjustments` só
aceita linha aprovada, e é o que impede um grupamento virar "queda de 80%"
no fator.

---

## 4. DFP — lucro, patrimônio, accruals

**Rede limpa.** Escreve em `fundamentals`. Não verificado por mim.

```powershell
py -3.13 tools\ingest_h7_real.py --dry-run    # só mostra o mapeamento por ano
py -3.13 tools\ingest_h7_real.py              # grava
```

**Rode isto mesmo que o H7 já tenha sido ingerido antes.** O upsert
(`ingest_cvm.py:568`) faz backfill explícito das colunas acrescentadas
depois: `receita_liquida`/`net_margin` (migração 0010) e
`fluxo_caixa_operacional`/`accruals` (0011, H17). `COALESCE` só preenche o
que está `NULL` e nunca sobrescreve valor existente, então re-rodar não
duplica nem recontabiliza — mas é o que traz os accruals da H17 para um
banco ingerido antes dessa migração.

Depende de `universo_2018_2026.txt` na raiz do repo (artefato local, não
versionado). Se ele sumiu, use o `ingest_fre_shares_real.py` da §5 como
referência: ele deriva o universo do próprio banco quando o arquivo falta.

---

## 5. FRE — quantidade de ações

**Rede limpa.** Escreve `fundamentals.shares_outstanding`. Não verificado
por mim contra o arquivo real.

```powershell
py -3.13 tools\ingest_fre_shares_real.py --dry-run
py -3.13 tools\ingest_fre_shares_real.py
```

**Faça o `--dry-run` primeiro e olhe o número de empresas casadas por ano.**
Se vier baixo, o problema é o mapeamento CNPJ↔ticker (via FCA), e é melhor
descobrir antes de gravar. O script não inventa ticker: companhia sem
mapeamento é pulada.

Este passo depende da correção do PR #53: o FRE **não publica** a
quantidade total de ações emitidas, só a em circulação e o percentual que
ela representa; o total é derivado (`circulação ÷ percentual`). Sem essa
correção, o que ia para o banco era o free float travestido de capital
total. Se o script levantar `ValueError` nomeando "quantidade TOTAL de
ações", isso é o fail-loud funcionando — não force, me chame.

---

## 6. A medição

**Somente leitura. Não escreve em lugar nenhum.** Exercitado contra banco
sintético.

```powershell
py -3.13 tools\cobertura_h18.py
py -3.13 tools\cobertura_h18.py --desde 2018-01-01     # janela explícita
```

Saída: contagem bruta por coluna de `fundamentals` (critério 2) e, por data
de rebalance, quantos papéis do universo point-in-time têm cada sinal
disponível (critérios 3 e 4), com H18/H19 lado a lado com H7/H9/H12/H13.

**Este script mede cobertura, nunca desempenho** — as funções de sinal são
consumidas só via `len()`. A trava e o motivo dela estão no topo do
arquivo. Não afrouxe sem ler.

Cole a saída inteira para eu fechar os critérios.

---

## 7. O que NÃO rodar ainda

```powershell
py -3.13 main.py backtest-h 17     # NÃO
py -3.13 main.py backtest-h 18     # NÃO
py -3.13 main.py backtest-h 19     # NÃO
```

Cada uma consome uma tentativa **irreversível** do denominador do DSR, e
`RESEARCH_FREEZE.md` §11 não permite reabrir. Antes delas falta:

1. **Decisão do embargo do FRE** (bloqueante) — os 90 dias são calibrados
   para a DFP, cujo prazo de entrega é de 3 meses; o FRE tem prazo maior.
   Aplicar o mesmo embargo aos dois deixa uma janela em que o sinal vê dado
   ainda não público.
2. **Base de desdobramento** — `preço_cru(asof) × ações(ref_date do FRE)`
   põe as duas pernas em bases diferentes se houve split no intervalo.
3. **Os critérios 2, 3 e 4** — que é o que §6 mede.

E vale para qualquer atalho: rodar "só para ver", mesmo com
`PREDICTOR_TRIALS_PATH` apontando para arquivo temporário, contamina a
decisão de rodar para valer. O ledger fica intacto; você não.

---

## 8. Checagem de integridade (antes e depois)

```powershell
Get-FileHash trials.json -Algorithm MD5
git status --porcelain
```

Nenhuma etapa deste runbook altera `trials.json` nem parâmetro `[FROZEN]`.
Se o hash mudar, algo saiu do script — pare e investigue.

Referência atual: `98BFC543DE1E80E2EAEC981E876E5A0C`.

---

## Erros comuns

| sintoma | causa | correção |
|---|---|---|
| `fatal: not a git repository` | você não está na raiz do repo | `cd` para a pasta do projeto (§1) |
| `can't open file 'C:\WINDOWS\system32\main.py'` | idem | idem |
| `ERROR: file or directory not found: tests\` | idem | idem |
| caminho do python mostra `pythoncore-3.14` ou outra versão | `python` resolveu para o interpretador errado | use `py -3.13` em tudo (§0) |
| `ModuleNotFoundError: predictor_core` | deps instaladas noutro interpretador | reinstale com `py -3.13 -m pip` (§0) |
| `ValueError: ... quantidade TOTAL de ações` | fail-loud do FRE funcionando | **não contorne** — ver §5 |

---

## Resumo executável

Copie o bloco INTEIRO — as duas primeiras linhas são o que mais falha.

```powershell
cd C:\Users\Superleo13\stocks-predictor-work    # caminho REAL (ver §1)
py -3.13 --version                                # tem de dizer 3.13.x

# uma vez por máquina
py -3.13 -m pip install --upgrade "https://github.com/leonardosovienski/core-predictor/releases/download/v3.2.0/predictor_core-3.2.0-py3-none-any.whl"
py -3.13 -m pip install --upgrade PyYAML pytest

# sempre
git pull origin main
py -3.13 main.py                              # onde estou?
py -3.13 -m pytest tests\ -q                  # 361 passed antes de tudo

py -3.13 tools\ingest_h7_real.py              # DFP  (rede limpa)
py -3.13 tools\ingest_fre_shares_real.py      # FRE  (rede limpa)
py -3.13 tools\cobertura_h18.py               # medir -> me mandar a saída
```
