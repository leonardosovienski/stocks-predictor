> **Nota de versionamento (2026-09-06).** Este parecer nasceu em
> `reports/auditoria_2026-09-04.md`, e `reports/*` é ignorado pelo git — ou
> seja, existia apenas na máquina efêmera onde foi escrito. Movido para
> `docs/` porque não é artefato de rodada (que é o que `reports/` guarda):
> é documento, e some junto com o container se não for versionado.
>
> **O conteúdo abaixo é o original, sem edição.** Três conclusões dele foram
> corrigidas por medições posteriores; as correções estão no `HANDOFF.md`
> (entradas de 2026-09-05 e 2026-09-06), não neste arquivo — emendar o
> parecer depois do fato apagaria o registro do que se sabia quando.
>
> Em resumo, para quem ler só isto:
> - **Critérios 2, 3 e 4:** medidos em 2026-09-05, APROVADOS.
> - **Critério 1:** aprovado — as ações totais não existem no FRE, mas são
>   deriváveis de `circulação ÷ percentual`.
> - **Critério 5 / §B3:** o parecer estimou "lookahead de ~2 meses". Certo
>   até 2022, ERRADO de 2023 em diante, onde o erro inverte de sinal e vira
>   ~305 dias de conservadorismo. Corrigido em 2026-09-06 com `known_at`
>   observado (`DT_RECEB`).
> - **§B4 (desdobramento):** confirmado concreto (BBAS3 dobra entre 2022 e
>   2023) e corrigido em 2026-09-06.

---

# Auditoria independente — stocks-predictor
**Data:** 2026-09-04 · **Alvo:** `main` @ `45bb2ef` (PR #51 mergeado) · **Auditor:** sessão independente

---

## Ressalva de método (declarada antes de qualquer conclusão)

O pedido pedia uma **Fase 1 cega**, antes de abrir o Apêndice A. **Não consegui
executar isso literalmente:** o Apêndice A estava no mesmo arquivo de prompt que li
por inteiro no primeiro comando da sessão. A ancoragem que o pedido queria evitar
existiu.

Mitigação e evidência de que os achados são meus: os três achados que classifico como
mais graves (**B1, B2, B3** abaixo) **não estão no Apêndice A** e não são refinamentos
de nenhum item dele. O achado B1 é, inclusive, o **contrário** da suspeita A2. Onde só
confirmo o Apêndice, digo que só confirmo.

---

## PASSO 0 — capacidade real desta sessão

| # | verificação | comando | resultado |
|---|---|---|---|
| 1 | banco com dado real | `ls -la data/` | ❌ **não existe `stocks.db`** — só `data/.gitkeep` (0 bytes). Não é "só schema": não há banco |
| 2 | acesso à CVM | `curl https://dados.cvm.gov.br/.../dfp_cia_aberta_2023.zip` | ❌ **bloqueado** — `curl: (56) CONNECT tunnel failed, response 403`; o status do proxy registra `connect_rejected / policy denial` para `dados.cvm.gov.br:443` |
| 3 | suíte | `python3.13 -m pytest tests/ -q` | ✅ **354 passed in 91.73s** |

```
$ curl -sS "$HTTPS_PROXY/__agentproxy/status"
  "recentRelayFailures": [{"kind":"connect_rejected",
    "detail":"gateway answered 403 to CONNECT (policy denial or upstream failure)",
    "host":"dados.cvm.gov.br:443"}]
```

**Consequência, declarada agora e não renegociada depois:** os critérios de aceite
**1, 2, 3 e 4 são INVERIFICÁVEIS nesta sessão.** Não baixei FRE real, não contei
`shares_outstanding`, não medi tamanho de universo. Onde eles aparecem abaixo, a
resposta é "não verificado" — com uma exceção importante: consegui **falsificar** o
critério 1 por outra via (§B1), o que é um resultado negativo válido sem precisar do
arquivo.

**Nota de ambiente:** a suíte só roda depois de instalar `predictor_core`/`predictor_ops`
como wheels dos repos irmãos. O `CLAUDE.md` ainda diz que a fonte da verdade é
`vendor/predictor_core/`, mas `tests/conftest.py:18` **asserta o oposto**
(`assert "vendor" not in ...predictor_core.__file__`). Documentação desatualizada em
relação ao código — não é bug, é armadilha para o próximo implementador.

---

## FASE 1 — achados próprios

### B1 · `shares_outstanding` é preenchido com o FREE FLOAT, silenciosamente — BUG, e é fatal para H18/H19

**Severidade: alta. Falsifica o critério de aceite nº 1.**

`_find_col` casa por **substring**:

```python
def _find_col(header, keywords):
    normed = [_norm(h) for h in header]
    for kw in keywords:
        for i, h in enumerate(normed):
            if kw in h:           # <-- substring
                return i
```

E as duas chaves do FRE colidem no mesmo nome de coluna real:

```python
_FRE_FLOAT_COLS = {
    "shares_outstanding": ("quantidade_total_acoes", "qtd_acoes_total"),
    "free_float":         ("quantidade_acoes_circulacao", "acoes_em_circulacao", "circulacao"),
}
```

O cabeçalho real do `fre_cia_aberta_distribuicao_capital_{ano}.csv` — **confirmado pelo
próprio operador** e registrado no `HANDOFF.md:58-61` ("Fonte confirmada … via
`tools/explore_dividend_sources.py`, rodado pelo operador") — é
`Quantidade_Total_Acoes_Circulacao`. Normalizado:
`quantidade_total_acoes_circulacao`, que **contém** `quantidade_total_acoes`.

```
$ python3.13 -c '<_find_col contra o cabeçalho real>'
  company              -> Nome_Companhia
  ref_date             -> Data_Referencia
  shares_outstanding   -> Quantidade_Total_Acoes_Circulacao
  free_float           -> Quantidade_Total_Acoes_Circulacao      <-- MESMA COLUNA
```

Ponta a ponta, com uma companhia de 1.000.000 de ações e 400.000 em circulação:

```
$ python3.13 -c '<ingest_fre_shares_year contra o cabeçalho real>'
  linhas ingeridas: 1
  free_float lido pelo mesmo parser:
    [{'company':'CIA X','ref_date':'2020-12-31',
      'shares_outstanding': 400000.0, 'free_float': 400000.0}]
```

**Não falha. Não avisa. Grava 400.000 como "ações totais".**

Consequências:

1. `market_cap = preço × 400.000` em vez de `× 1.000.000` → **capitalização subestimada
   pelo percentual de free float**.
2. `E/P` e `B/M` ficam **inflados por `1 ÷ (fração de free float)`**. Na B3, onde
   controle concentrado é a norma e o free float varia de ~15% a ~100%, esse fator
   varia por um múltiplo de **~6x entre papéis**.
3. Isso não é ruído: é um **confundidor sistemático**. H18/H19 ranqueariam
   predominantemente por **concentração acionária**, não por valor. Um veredito
   (qualquer que fosse) seria sobre a hipótese errada — e consumiria uma tentativa do
   denominador do DSR sem possibilidade de reabertura (RESEARCH_FREEZE §11).
4. `Quantidade_Total_Acoes_Circulacao` no FRE é **ações em circulação**, não capital
   social total. Pelo que consigo determinar do layout, **este arquivo não expõe a
   quantidade total de ações emitidas** — ou seja, o insumo que H18/H19 exigem pode
   não existir nesta fonte. Isso precisa ser confirmado contra o arquivo real (não
   consegui: §Passo 0.2).

**Por que os testes não pegam:** `tests/test_h18_h19_value.py:207` constrói um
cabeçalho sintético com **duas colunas separadas** —
`Quantidade_Total_Acoes;Quantidade_Acoes_Circulacao` — que a CVM não publica e que o
próprio HANDOFF do projeto não menciona. Nesse cabeçalho inventado as duas chaves
resolvem distinto e o teste passa. **É o caso-livro de teste que passa por construção.**
Viola diretamente a regra do `CLAUDE.md`: "golden tests com dados reais no parse".

**Efeito colateral pré-existente, fora do escopo de H18/H19:** num layout FRE com
quebra ON/PN (`Quantidade_Acoes_Ordinarias_Circulacao`, `..._Preferenciais_...`,
`Quantidade_Total_Acoes_Circulacao`), a chave `free_float` cai pelo keyword genérico
`"circulacao"` na **primeira** coluna que o contém — a de **ordinárias** — enquanto
`shares_outstanding` pega a total. Isto é, a família `liquidity` pode estar usando
free float só de ON há tempo. **Não verificado contra arquivo real**; sinalizado.

---

### B2 · Dois parâmetros `[H1-FROZEN]` estão selados no hash mas o backtest nunca os lê

**Severidade: média-alta (integridade do pedágio). Confirma e amplia A7.**

```
$ grep -rn "purge_embargo_months" --include=*.py .
  ./stocks_predictor/config.py:105  (só na lista de chaves do selo)
  ... (nenhuma ocorrência em backtest.py)
$ grep -n "next_open" stocks_predictor/backtest.py
  (nada — next_open_after só é usado por paper.py)
```

- `config.yaml:21` → `price: next_open  # [H1-FROZEN] abertura D+1`
- `config.yaml:30` → `purge_embargo_months: 1  # [H1-FROZEN]`

Ambos entram em `config.py` no conjunto de chaves congeladas de **todas as 18
hipóteses** (linhas 102-530), logo entram no `config_hash` que sela cada
pré-registro. Nenhum dos dois altera o resultado de `walk_forward`.

O que `walk_forward` realmente faz (`backtest.py:145`): o sinal é calculado no
fechamento de `t` e os retornos do período são `[d for d in all_dates if t < d <= t1]`
— ou seja, o primeiro retorno computado é `close(t+1)/close(t) − 1`. **A liquidação
efetiva é no fechamento do próprio dia do sinal**, não na abertura de D+1. É a
premissa otimista clássica (você não negocia ao fechamento que está usando para
decidir).

**Sendo justo com a sessão anterior:** isto está **declarado** no docstring do módulo
(`backtest.py:14-16`: "a robustez de execução a 3 preços … e o purge/embargo formal
ficam para a evolução do M5"). Não é ocultação. O problema é que o **selo criptográfico
afirma uma coisa e a máquina faz outra** — e o `config.yaml` carimba `[H1-FROZEN]
abertura D+1` num parâmetro inerte. Quem auditar o `config_hash` daqui a dois anos vai
concluir, errado, que os 16 vereditos foram produzidos com execução em D+1.

Não é motivo para reabrir H1-H16 (o viés é o mesmo para estratégia e benchmark, ambos
medidos close-to-close). É motivo para corrigir o comentário e a lista de chaves, ou
implementar o parâmetro.

---

### B3 · O embargo de 90 dias está calibrado para a DFP e é aplicado, errado, ao FRE

**Severidade: média-alta. Ataca diretamente o critério de aceite nº 5.**

`_value_signals` (`factor.py:295-298`) resolve as duas pernas com o **mesmo** embargo:

```python
fundamento = _fundamental_signals(conn, tickers, asof, disclosure_embargo_days, column)
shares     = _fundamental_signals(conn, tickers, asof, disclosure_embargo_days, "shares_outstanding")
```

`disclosure_embargo_days=90` foi escolhido para a **DFP** (CVM Res. 80: entrega em até
**3 meses** do encerramento do exercício). Mas `shares_outstanding` vem do **FRE**, cujo
prazo regulamentar de entrega é de **5 meses** do encerramento do exercício.

Aplicando 90 dias a uma linha FRE com `ref_date = 2020-12-31`, o sinal a considera
conhecida em **2021-03-31** — enquanto o formulário pode legalmente só ser público em
**2021-05-31**. **Janela de ~2 meses em que o sinal enxerga dado ainda não divulgado.**
É lookahead informacional, exatamente a espécie que o design §0.2 chama de defeito
capital.

A ironia é que o docstring de `ingest_fre_shares_year` (linhas 767-775) argumenta longa
e corretamente que casar as datas de DFP e FRE à força seria "lookahead sutil e
silencioso" — e então o consumidor aplica o **embargo da DFP** ao FRE, reintroduzindo o
problema pelo outro lado.

**Confiança:** alta na estrutura do argumento; **os prazos regulamentares (3 vs. 5
meses) devem ser confirmados pelo operador** — não consegui verificar fonte primária
(sem rede). Se o prazo do FRE for outro, o número muda; a assimetria (dois formulários,
um só embargo) permanece um defeito de modelagem.

**Correção mínima:** embargo por FONTE, não por chamada — a linha de `fundamentals`
já carrega `source` (`"CVM FRE {year}"` vs. o da DFP), então o embargo pode ser
derivado dela em vez de ser um único parâmetro do chamador.

---

### B4 · Erro de base em desdobramentos — confirmo o mecanismo, e a correção é viável

Cheguei ao mesmo ponto de A3 por conta própria antes de conferir. `_value_signals`
compõe `preço_cru(asof) × shares(ref_date do FRE)`. As duas pernas estão em **datas
diferentes**, e `_price_at` corrige apenas o `quote_factor` da B3 (`db.price_expr`) —
que é fator de **lote de cotação**, não de desdobramento.

Se houve split/grupamento entre a `ref_date` do FRE e `asof`, as pernas ficam em bases
diferentes e o market cap erra **pelo fator do desdobramento**. Num split 1:2 o preço
cai à metade e a contagem de ações do FRE ainda é a antiga → market cap subestimado em
50% → **E/P dobra** → o papel salta para o quintil superior por artefato mecânico.

**Resposta à pergunta de A3 ("a tabela `adjustments` permite corrigir?"): sim.**

```sql
CREATE TABLE IF NOT EXISTS adjustments (
    ticker TEXT, ex_date TEXT, factor REAL,
    type TEXT,        -- 'split','grupamento','dividendo','jcp','outro'
    source TEXT, approved_by TEXT, ...)
```

Tem `ticker`, `ex_date`, `factor` e `type` distinguindo split/grupamento de provento.
A correção é aplicar o produto dos `factor` de `type IN ('split','grupamento')` com
`ex_date` entre a `ref_date` do FRE e `asof` sobre a contagem de ações. `_value_signals`
não faz nada disso hoje, e **nenhum teste cobre o caso** (`test_h18_h19_value.py` não
tem um único teste de desdobramento).

---

### B5 · Accruals usa ativo final, não médio — desvio real de Sloan, mas defensável

Confirmo A5. `compute_fundamentals`: `accruals = (lucro − FCO) / ativo_total`, com
`ativo_total` do **fim** do exercício. Sloan (1996) escala pelo ativo **médio**.

Meu parecer: **desvio, não erro**, e menor do que parece. O ranking é
**cross-seccional dentro de um mesmo rebalance**; o viés de usar ativo final em vez de
médio é proporcional à taxa de crescimento do ativo de cada empresa, que é de segunda
ordem para o *ordenamento*. É também o que boa parte da literatura aplicada faz. Duas
ressalvas honestas: (a) prejudica desproporcionalmente empresas em crescimento
acelerado ou pós-aquisição; (b) a implementação segue Hribar & Collins (2002)
(demonstração de fluxo de caixa) e não a versão balanço-patrimonial do Sloan original —
o que é uma **melhoria** metodológica, não um desvio, e vale registrar como tal.

Recomendação: **não mudar antes de rodar** (mexer agora é ajustar parâmetro de hipótese
pré-registrada). Registrar o desvio no pré-registro e seguir.

---

### B6 · Constantes de parsing da DFC: consistentes, mas não verificadas

Sobre A1, o que consegui e o que não consegui:

- ✅ `_open_zip_csv(zbytes, "dfc_mi_con")` é **inequívoco por construção**: a função
  levanta exceção se casar ≠1 arquivo, e `dfc_mi_con` não colide com `dfc_md_con`
  (método direto) nem com `dfc_mi_ind` (individual). Fail-loud correto.
- ✅ `_CASHFLOW_OPS_CODE = "6.01"` e `("caixa","operaciona")` são **consistentes** com o
  plano de contas CVM que conheço (6.01 = "Caixa Líquido Atividades Operacionais";
  6.02 investimento, 6.03 financiamento). O cruzamento código **E** descrição é a
  disciplina certa: um sozinho erra, os dois juntos errarem é improvável.
- ❌ **Não verificado contra arquivo real** — sem rede. Nota: `"operaciona"` truncado
  cobre "operacionais/operacional/operacionais(is)" e é escolha deliberada e boa.
- ⚠️ Risco residual real: `_pick_account` chaveia por `(_norm(company), ref_date)`, ou
  seja **por nome de empresa normalizado**, não por CNPJ — apesar de `cnpj` estar sendo
  parseado e disponível. Duas companhias com denominação social parecida colidiriam, e
  a colisão vira `None` (fail-closed, não fabrica número — isso está certo), mas
  **derruba silenciosamente linhas boas**. Usar CNPJ como chave seria estritamente
  melhor e o dado já está lá.

---

### B7 · Preço cru vs. ajustado (A4): **concordo com a sessão anterior**

O argumento dela está certo e é bem construído: multiplicar a série retro-ajustada pela
contagem de ações vigente produziria uma capitalização que nunca existiu, com erro
crescente quanto mais para trás. Para **retorno**, série ajustada; para **nível de
preço num múltiplo**, preço cru. Não tenho contra-argumento — a sessão anterior
acertou, e o docstring de `_price_at` (linhas 246-258) documenta a decisão melhor do
que a maioria do repositório.

O que ela **não** viu é que essa decisão correta é justamente o que abre o B4: preço
cru significa que o efeito do split fica na perna do preço e precisa ser espelhado na
perna das ações. Acertar A4 sem tratar B4 é meio caminho.

---

### B8 · Achados menores

| # | achado | severidade |
|---|---|---|
| B8.1 | `parse_fre_capital_total_rows` já existe, é **fail-loud**, chaveia por **CNPJ** e lê explicitamente `quantidade_total_acoes_circulacao` — mas `ingest_fre_shares_year` **não a usa**, preferindo o caminho opcional por nome de empresa. Há duas rotas para o mesmo dado, e H18/H19 usam a frágil. | média |
| B8.2 | Docstring de `ingest_fre_shares_year` referencia `factor._market_cap_signals`, função que **não existe** (é `_value_signals`). | baixa |
| B8.3 | `CLAUDE.md` afirma vendor como fonte da verdade; `conftest.py:18` asserta o contrário. | baixa |
| B8.4 | `trials.json` está **íntegro e coerente**: 15 entradas, H1-H16 menos H3 (que nunca existiu), timestamps monotônicos, Sharpe por-período em todas. O N do DSR para uma H18 seria 16. Sem anomalia. | ok |

---

## FASE 2 — conferência contra o Apêndice A

| item | veredito | nota |
|---|---|---|
| **A1** DFC 6.01 / keywords / `dfc_mi_con` | **parcialmente confirmado, risco menor que o atribuído** | constantes consistentes com o plano de contas; `_open_zip_csv` é fail-loud e inequívoco. Não verificado contra arquivo real. Achei um risco adjacente que ela não viu: chave por nome de empresa em vez de CNPJ (§B6) |
| **A2** `shares_outstanding` pode nunca ser populado | **REFUTADO — e o problema real é pior** | ela previu *0 linhas em silêncio*. O que acontece é **N linhas com o número errado** (free float) em silêncio. Falha silenciosa com `n=0` seria detectável na primeira rodada; dado plausível e errado, não. Ela acertou o cheiro (teste com cabeçalho sintético) e errou o diagnóstico. Ver §B1 |
| **A3** erro de base em desdobramentos | **CONFIRMADO — é bug** | mecanismo confirmado; `adjustments` **permite** corrigir; nenhum teste cobre. Ver §B4 |
| **A4** preço cru vs. ajustado | **CONFIRMADO, ela está certa** | concordo sem ressalva quanto ao mérito. Ver §B7 |
| **A5** accruals: ativo final vs. médio | **CONFIRMADO como desvio, não erro** | e ela subestimou o próprio acerto: a implementação segue Hribar-Collins, o que é *melhor* que o Sloan original. Ver §B5 |
| **A6** embargo de 90 dias | **CONFIRMADO e AMPLIADO** | para a DFP, 90 dias é o prazo regulamentar exato — apertado mas defensável. Ela não percebeu que o **mesmo** embargo é aplicado ao **FRE**, cujo prazo é maior — aí há lookahead. Ver §B3 |
| **A7** integridade do pedágio | **`trials.json` íntegro; mas achei uma brecha que ela não** | N do DSR correto, ledger coerente (§B8.4). Porém dois parâmetros `[FROZEN]` estão selados e **não são consumidos** pelo backtest (§B2) — o selo pode ser "alterado" sem quebrar golden test justamente porque não afeta resultado nenhum |

### O que achei que NÃO está no Apêndice A

1. **B1** — a colisão de substring que grava free float como ações totais. *O achado mais grave desta auditoria.*
2. **B2** — `execution.price` e `purge_embargo_months` selados mas inertes; execução real é close-to-close, não D+1.
3. **B3** — embargo da DFP aplicado ao FRE.
4. **B6/B8.1** — chave por nome de empresa quando o CNPJ está disponível, e a existência de uma rota fail-loud melhor (`parse_fre_capital_total_rows`) que a ingestão de H18/H19 ignora.

---

## Critérios de aceite da H18 — medição

**Nenhum limiar foi proposto por mim depois de ver resultado: não vi nenhum
resultado.** Não rodei H17, H18 nem H19, em nenhuma forma, com ou sem
`PREDICTOR_TRIALS_PATH`. Não olhei retorno, Sharpe, PSR ou DSR de nada.

| # | critério | veredito | evidência |
|---|---|---|---|
| 1 | coluna de ações existe no FRE real e vem preenchida | ❌ **FALHA** | não pela via pedida (sem rede), mas por análise: a coluna que o parser encontra é `Quantidade_Total_Acoes_Circulacao` = **ações em circulação**, não ações totais (§B1). O insumo que H18 exige pode não existir nesta fonte |
| 2 | `shares_outstanding` não-nulo para fração relevante | ⛔ **não verificado** | sem banco e sem rede. E irrelevante enquanto (1) falhar: a coluna virá preenchida, com o número errado |
| 3 | as duas pernas coexistem elegíveis nas datas de rebalance | ⛔ **não verificado** | sem banco. Ressalva independente: mesmo com dado, a elegibilidade está mal-especificada por causa do embargo único (§B3) |
| 4 | universo mediano comparável a H7/H9/H12/H13 | ⛔ **não verificado** | sem banco |
| 5 | nenhum papel entra no sinal antes do dado ser público | ❌ **FALHA** | §B3: embargo de 90 dias (calibrado para DFP) aplicado a linhas FRE, cujo prazo de entrega é maior. Verificado por inspeção; prazos regulamentares a confirmar pelo operador |

**Placar: 2 falhas, 3 não verificados, 0 aprovados.**

---

## Entregável — respostas diretas

**1. A infraestrutura faz o que diz fazer? Onde ela engana?**

Em boa parte, sim — e melhor do que a média. O `_pick_account` fail-closed, o
`_open_zip_csv` que se recusa a escolher entre dois arquivos, o `ORDEM_EXERC='ÚLTIMO'`,
a armadilha do CD_CONTA "2" incluindo PL documentada no código, a decisão de preço cru,
a correção do bug de `cost_pending` — isso é trabalho cuidadoso e os docstrings são
honestos sobre limitações.

Ela engana em três pontos:

- **`_find_col` por substring** dá a *aparência* de tolerância a renomeação e entrega
  **colisão silenciosa** entre duas chaves de significado oposto. O módulo abre dizendo
  que existe para evitar "perder uma coluna por renomeação silenciosa" — e o modo de
  falha que ele de fato tem é pior: pegar a coluna **errada** sem avisar.
- **Os selos `[FROZEN]`** afirmam propriedades (`execução em D+1`, `purge/embargo`) que
  o backtest não tem.
- **Os testes de parse** usam cabeçalhos escritos pela própria equipe e por isso
  confirmam a implementação em vez de testá-la.

**2. H17/H18/H19 estão corretas, ou têm bug?**

- **H17 (accruals):** sem bug identificado. O desvio de Sloan é defensável e a fonte
  (DFC-MI) é genuinamente nova, como o RESEARCH_FREEZE §11 exige. Pendência: golden
  test contra DFC real. **Provavelmente pronta para rodar quando houver banco e rede.**
- **H18 (E/P) e H19 (B/M):** **têm bug, e o mesmo bug.** B1 é bloqueante: o insumo
  central está errado por construção. B3 (lookahead do FRE) e B4 (base de split) são
  dois bugs adicionais independentes, cada um capaz de contaminar o ranking sozinho.

**3. A ingestão nova funciona contra arquivo real da CVM?**

**Não verificado para DFP/DFC** (sem rede). **Para o FRE: não — e essa parte eu
consigo afirmar**, porque o cabeçalho real está registrado no HANDOFF pelo próprio
operador e o parser demonstravelmente casa a coluna errada contra ele.

**4. Vale rodar a H18?**

**Não.** Não é dúvida de limiar: **dois dos cinco critérios falham por inspeção** e os
outros três são inverificáveis nesta sessão. Rodar hoje queimaria uma tentativa
irreversível do denominador do DSR para medir "concentração acionária com lookahead de
2 meses", não valor.

Antes de rodar, na ordem: **(i)** baixar um FRE real e imprimir o cabeçalho — isso
sozinho decide se H18/H19 são viáveis nesta fonte; **(ii)** corrigir B1 (chave por
CNPJ, fail-loud, sem substring ambíguo, golden test com CSV real); **(iii)** decidir o
embargo por fonte (B3); **(iv)** decidir sobre B4 — corrigir via `adjustments` ou
declarar a limitação no pré-registro; **(v)** só então medir os critérios 2, 3 e 4.

**Ponto que exige decisão sua, não minha:** se o FRE realmente não expuser ações
totais, H18/H19 precisam de **outra fonte** (o próprio COTAHIST não a tem; a B3
publica capital social por outra via). Isso é mudança de fonte de dado, o que pelo
`CLAUDE.md` é dúvida de design não coberta — **parei e estou perguntando** em vez de
escolher uma fonte sozinho.

**5. O que a sessão anterior errou, exagerou ou deixou passar?**

- **Errou:** o diagnóstico de A2 (previu falha ruidosa; o modo real é silencioso e
  pior). E testou parsers contra cabeçalhos que ela mesma escreveu, contrariando regra
  explícita do `CLAUDE.md` — e essa escolha é exatamente o que escondeu B1.
- **Exagerou:** nada relevante. Não encontrei nenhuma afirmação inflada. Ela marcou
  como "não verificado" tudo o que de fato não verificou, e o Apêndice A é um exercício
  de auto-crítica honesto — A3 e A5 são achados reais que ela levantou contra o próprio
  trabalho. A1 ela classificou como risco mais alto do que se sustenta.
- **Deixou passar:** B1, B2, B3, B6/B8.1. E subestimou o próprio acerto em A5
  (Hribar-Collins é melhoria, não desvio) e em A4 (está certa, sem ressalva).

**Veredito sobre a sessão anterior:** trabalho competente e intelectualmente honesto,
com um furo grave e um padrão de teste que o tornava invisível. Não é caso de
desconfiar do conjunto; é caso de trocar o método de teste de parse.

---

## Integridade

Nada foi commitado, escrito no banco (não há banco) ou alterado em `trials.json`.

```
$ md5sum trials.json trials_v2.json trials.harness_attestation.json   # antes E depois
98bfc543de1e80e2eaec981e876e5a0c  trials.json
b85e548a789924139da79e854a3ac70a  trials_v2.json
a2cb67242fea41cae76e62990eae11d7  trials.harness_attestation.json

$ git status --porcelain
(vazio — nada modificado. `reports/` é ignorado pelo git 
 (.gitignore:4 `reports/*`), então este relatório nem sequer aparece como 
 arquivo novo: não há risco de commit acidental.)
```

H17/H18/H19 **não foram executadas**. Nenhuma métrica de desempenho foi observada.
Nenhum parâmetro `[FROZEN]` foi tocado. Nenhuma hipótese de H1 a H16 foi reaberta.
