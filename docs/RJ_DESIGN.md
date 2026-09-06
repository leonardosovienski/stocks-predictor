# DESIGN.md — predictor-rj

> Documento canônico. Mudar qualquer parâmetro marcado [RJ-FROZEN] em
> `config.yaml` depois de ver resultado real = nova hipótese, novo
> pré-registro, nova rodada. Sem exceções.

Este arquivo faltava no pacote entregue em 2026-08-23 — README.md e
HANDOFF.md já o referenciavam como documento canônico antes de ele existir
(revisão externa, ponto 8). Escrito agora para fechar essa referência quebrada.

## 1. Pergunta de pesquisa

Existem condições, eventos ou padrões observáveis que aparecem repetidamente
ANTES de rallies especulativos (≥50%) em ações de empresas em recuperação
judicial na B3, e que sejam **conhecíveis no momento da decisão** — não
apenas reconhecíveis depois do fato?

Não é objetivo do estudo concluir que empresas em RJ são bons investimentos.

## 2. Dois datasets, nunca fundidos

**Descritivo (ex-post):** usa `episodes.find_local_trough` — escolhe o fundo
olhando a janela inteira. Responde "o que caracterizou os episódios que já
aconteceram?". Contém lookahead por construção. Nunca usado para simular
decisão em tempo real.

**Preditivo (point-in-time):** usa `episodes.point_in_time_candidates` — em
cada dia D, D só é candidato se for a mínima de uma janela retroativa fixa
terminando em D. Nenhum dado de D+1 em diante participa. É o único dataset
válido para a pergunta "dá para prever antes?" (revisão externa, ponto 1 —
o ajuste mais importante feito na primeira revisão do protocolo).

Toda família tem uma versão contemporânea (medida no candidato, válida só
para o dataset descritivo) e, quando fizer sentido, uma versão antecedente
(medida estritamente antes de D, válida para o dataset preditivo). Ex.:
`volume_dynamics_contemporaneous` vs. `volume_dynamics_antecedent`.

## 3. Universo primeiro, rally depois

A base é a lista completa de companhias com ações negociadas na B3 que
entraram em RJ no período `config.yaml:universe.period_start..period_end` —
incluindo as que nunca tiveram rally, as ilíquidas, e (quando houver dado
confiável) as posteriormente deslistadas. Classificar quem teve rally só
DEPOIS do universo estar fechado. Nunca partir de uma lista de casos
notáveis lembrados de memória — isso já é viés de seleção antes do primeiro
cálculo.

## 4. Definição canônica de rally

Fechamento ajustado → fechamento ajustado, ≥50%, dentro de uma janela máxima
em PREGÕES (não dias corridos). Duas janelas pré-registradas, nunca fundidas
(revisão externa, ponto 3):

- **Primária:** 60 pregões — captura o fenômeno "explosivo" que motivou o
  estudo (AMER3 +194% em poucos pregões).
- **Secundária:** 252 pregões — outcome auxiliar; misturar as duas contaria
  deriva lenta de 11 meses como o mesmo fenômeno que um rally de dias.

Intraday é variável secundária, nunca o outcome principal (PMAM3 teve pico
intraday; se isso virasse o critério, os casos deixariam de ser comparáveis
entre si).

## 5. Censura

Uma empresa só entra no grupo controle definitivo ("sem rally") se sua
janela de observação (`censoring_horizon_trading_days`) já COMPLETOU.
Empresa recente demais fica marcada `censored` — não é "não teve rally", é
"ainda não sabemos".

## 6. Empresa → episódios

Unidade estatística primária = primeiro episódio de cada empresa, mas
**"primeiro" segundo regra fixada a priori, nunca escolhida olhando qual
candidato teve rally** (revisão externa, 2ª rodada, ponto 3 — o próprio
risco que a separação ex-post/preditivo já havia resolvido, reaparecendo
pela porta da seleção de episódio).

Regra congelada: `episodes.select_primary_episode` = o primeiro candidato
cronologicamente entre os gerados por `point_in_time_candidates` (que já
exige janela retroativa completa — ver §2b). Episódios secundários
(`episodes.select_secondary_episodes`) exigem separação mínima de
`primary_window_trading_days` pregões do último candidato mantido — evita
contar uma sequência de mínimas locais próximas como "episódios distintos".

O bootstrap do judge usa `cluster_key=ticker` precisamente para essa
dependência: na análise primária degenera em iid (1 episódio/empresa), mas
protege automaticamente qualquer análise que misture episódios múltiplos.

### 2b. Janela completa obrigatória no gerador point-in-time

`point_in_time_candidates` só considera D um candidato válido se já
existirem `backward_lookback` pregões de histórico DESDE o pedido de RJ até
D (`i - idx_rj >= backward_lookback`). Sem essa exigência, o 1º pregão
pós-RJ seria candidato trivial (janela de 1 ponto = mínimo de si mesmo), o
2º também se caísse, etc. — uma enxurrada de "fundos" causada só pela
empresa ter acabado de entrar no universo, não por nenhuma propriedade real
da série (revisão externa, 2ª rodada, ponto 2).

## 7. 8 famílias PREDITIVAS + 1 descritiva, não 114 hipóteses

As 114 hipóteses do relatório de Fase 1 original são condensadas em famílias
mensuráveis (`config.yaml:families`). **Exatamente 8 são PREDITIVAS** e
entram no FDR primário (`families.PREDICTIVE_FAMILIES`, com assert em
código garantindo que o número não deriva silenciosamente de novo — revisão
externa, 2ª rodada, ponto 1, depois que `volume_dynamics` foi desdobrada em
contemporânea+antecedente e o registry passou a ter 9 entradas sem que o
pré-registro fosse atualizado):

drawdown, liquidity, volume_dynamics_antecedent, rj_stage, ownership,
momentum_volatility, time_since_rj, info_trigger.

`volume_dynamics_contemporaneous` é computada e reportada, mas fica FORA do
FDR — é descritiva por design (medida no candidato, só reconhecível como
"o fundo" depois do fato; ver §2).

Cada família preditiva tem:
- 1 métrica operacional definida em código (`stocks_predictor/rj_families.py`)
- 1 direção esperada declarada ANTES de qualquer rodada (`positive`,
  `negative`, `ambiguous` quando o próprio banco de hipóteses original
  diverge internamente, ou `categorical` quando a família não admite ordem)

`rj_stage` é tratada como categórica, não ordinal (revisão externa, ponto
4) — "estágio 3" (encerrada) não implica por construção maior chance de
rally que "estágio 2" (homologada); a suposição de monotonia era
injustificada e foi removida.

## 8. Anti-lookahead informacional

Eventos discretos (`rj_events`) distinguem `event_date` (a que o evento se
refere), `published_at` (quando foi tornado público) e `known_at` (a partir
de quando é conhecível — o campo que toda feature informacional DEVE
filtrar). Um fato relevante sobre uma reunião de 10/05 publicado na noite de
11/05 não existia para uma decisão simulada em 10/05 (revisão externa,
ponto 7).

## 9. Julgamento estatístico

Unidade de teste: diferença de médias (ou V de Cramér, para `rj_stage`)
entre grupo-rally e grupo-controle, por família, na análise primária.

- **IC do effect size:** bootstrap não-paramétrico, `scheme=cluster`
  (`cluster_key=ticker`) — preserva a dependência empresa→episódios sem
  inflar N artificialmente.
- **P-valor:** permutação do rótulo grupo entre empresas.
- **Múltiplas comparações:** Benjamini-Hochberg FDR entre as **8 famílias
  PREDITIVAS** (`config.yaml:judge.fdr_alpha`, `families.PREDICTIVE_FAMILIES`)
  — não o DSR do domínio de ações, que é específico de série de retornos por
  período e não se aplica a uma comparação transversal de médias. A família
  descritiva fica fora do denominador (§7).
- **Influência/estabilidade** (`config.yaml:influence_analysis`, renomeado
  de "validation" na 2ª revisão — ponto 4): leave-one-company-out mede se
  uma empresa sozinha carrega o resultado, NÃO é validação preditiva (ponto
  6 da 1ª revisão). Validação preditiva de verdade exige um modelo treinado
  em N-1 e testado na empresa excluída — só faz sentido quando houver
  modelo, não apenas comparação de médias.
- **Power gate:** antes de qualquer hipótese real, o judge precisa provar
  sensibilidade (detecta effect size plantado em dado sintético) e
  especificidade (taxa de falso positivo pós-FDR compatível com o alpha
  nominal, em muitas repetições de ruído puro) — ver
  `tests/test_rj_power_gate.py`. Sem isso, um NO-GO não é interpretável: não
  se sabe se o judge é cego.

## 10. O que NÃO fazer

- Não misturar dataset descritivo e preditivo na mesma tabela sem a coluna
  que os distingue.
- Não testar as 114 sub-hipóteses individualmente — elas ficam registradas
  como notas exploratórias dentro de cada família, nunca como testes N+1.
- Não ajustar parâmetro [RJ-FROZEN] depois de ver o resultado da rodada.
- Não declarar família "significativa" sem ter passado pelo FDR.
- Não tratar `event_date` como se fosse `known_at`.
