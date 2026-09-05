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
python --version          # precisa ser 3.13.x
```

O `predictor-core` **não está no PyPI público** — distribuição só por wheel
de GitHub Release do repo irmão:

```powershell
python -m pip install --upgrade "https://github.com/leonardosovienski/core-predictor/releases/download/v3.1.0/predictor_core-3.1.0-py3-none-any.whl"
python -m pip install --upgrade PyYAML pytest
```

Sintoma de core desatualizado: `pyproject.toml` exige `>=3.0,<4`; uma 2.x
instalada quebra o import com erro pouco óbvio. Confira com
`python -c "import predictor_core; print(predictor_core.__version__)"`.

---

## 1. Repo atualizado

```powershell
cd C:\caminho\para\stocks-predictor
git checkout main
git pull origin main
```

Precisa conter os PRs #52, #53 e #54 (correção do FRE + os dois scripts).

---

## 2. Diagnóstico — onde você está

```powershell
python main.py                    # status: config_hash, contagem por tabela, trials
python -m pytest tests\ -q        # precisa estar VERDE antes de qualquer ingestão
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
python -c "import sys; sys.path.insert(0,'stocks_predictor'); import ingest_cotahist as ic; [ic.download_cotahist(a,'data/cotahist') for a in range(2016,2027)]"
```

Carregar cada zip e rodar o detector de saltos:

```powershell
Get-ChildItem data\cotahist\COTAHIST_A*.ZIP | ForEach-Object { python main.py ingest $_.FullName }
python main.py adjust                        # detector de saltos -> quarentena
python main.py splits-review splits.csv      # exporta candidatos p/ revisão HUMANA
# revise splits.csv à mão, aprove linha a linha, então:
python main.py splits-import splits.csv
```

O passo de revisão humana dos splits não é burocracia: `adjustments` só
aceita linha aprovada, e é o que impede um grupamento virar "queda de 80%"
no fator.

---

## 4. DFP — lucro, patrimônio, accruals

**Rede limpa.** Escreve em `fundamentals`. Não verificado por mim.

```powershell
python tools\ingest_h7_real.py --dry-run    # só mostra o mapeamento por ano
python tools\ingest_h7_real.py              # grava
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
python tools\ingest_fre_shares_real.py --dry-run
python tools\ingest_fre_shares_real.py
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
python tools\cobertura_h18.py
python tools\cobertura_h18.py --desde 2018-01-01     # janela explícita
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
python main.py backtest-h 17     # NÃO
python main.py backtest-h 18     # NÃO
python main.py backtest-h 19     # NÃO
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

## Resumo executável

```powershell
# uma vez
python -m pip install --upgrade "https://github.com/leonardosovienski/core-predictor/releases/download/v3.1.0/predictor_core-3.1.0-py3-none-any.whl"

# sempre
git pull origin main
python main.py                              # onde estou?
python -m pytest tests\ -q                  # verde antes de tudo

python tools\ingest_h7_real.py              # DFP  (rede limpa)
python tools\ingest_fre_shares_real.py      # FRE  (rede limpa)
python tools\cobertura_h18.py               # medir -> me mandar a saída
```
