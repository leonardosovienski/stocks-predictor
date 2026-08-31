# predictor-stocks — Documento de Design e Handoff para Implementação
**Data:** 12/06/2026 · **Versão:** 1.1 · **Status:** design aprovado, implementação autorizada por marcos
**Leia este documento INTEIRO antes de escrever qualquer linha de código.**

> **Changelog v1.1 (12/06/2026, durante o M0):** revisão editorial, sem mudança de
> decisão de mérito. (1) §3: comentário de `portfolio.py` dizia "decil superior",
> contradizendo a decisão de quintil do §6 e da H1 — corrigido; (2) §6: a decisão
> decil→quintil, antes embutida num parêntese, virou texto limpo. Decisões tomadas
> durante a implementação (parser YAML stdlib, moving-block antes de stationary)
> são registradas no HANDOFF.md, não aqui — este documento fixa o design; o HANDOFF
> registra a execução.

---

## 0. Contexto e linhagem

Este é o **domínio 2** de um framework de previsão multi-domínio (TCC + projeto de longo
prazo). O domínio 1 é o `wc-predictor` (futebol, Copa 2026): Python+SQLite, 75 testes
verdes, auditado, **em produção operacional — intocável**. A metodologia do framework
foi extraída dele e é inegociável:

1. **Camadas em ordem:** motor estatístico interpretável PRIMEIRO → instrumento de
   medição (backtest, métrica, significância) SEGUNDO → ML/IA por último, só como
   geradora de features que a medição prova que pagam. ML nunca substitui o motor.
2. **Forward-only, sempre:** nenhuma informação posterior ao instante da decisão pode
   tocá-la. Lookahead é o defeito capital.
3. **Pré-registro:** toda hipótese tem critério de sucesso fixado ANTES de ver o dado.
   "Inconclusivo" é resultado válido. Mover a trave depois do chute é proibido.
4. **Ledger append-only:** toda decisão é registrada com contexto completo de auditoria
   no momento em que é tomada, nunca reescrita.
5. **Medição antes de modelagem:** na dúvida, amplie o que você mede antes de mudar o
   que você modela.

Arquitetura geral decidida: **multirepo**. Um repositório por domínio + `predictor-core`
(biblioteca autônoma) consumido por **vendoring** (`vendor/predictor_core/` com carimbo
de versão; sync por script). NUNCA instalar o core via pip global. Domínios não se
importam entre si, jamais.

**Regra de extração por demanda:** o `predictor-core` só recebe uma peça quando este
domínio a exigir de fato. Não generalize especulativamente. O que ações exigir do core
(ex.: block bootstrap) entra no core; o que for específico de ações fica aqui.

## 1. Ambiente real (restrições, não sugestões)

- **Windows**, Python 3.13 **global** (EDR corporativo quarentenou venvs — não criar
  venv; não depender de venv).
- Política de dependências: **stdlib-first**. `numpy` está PRÉ-APROVADO desde o M0
  (matriz de retornos cruzada e stationary bootstrap justificam; implementá-los em
  stdlib pura seria purismo pagando juros). `pandas` NÃO está pré-aprovado: o parse
  posicional do COTAHIST é trivial em stdlib; se a dor aparecer no M1, justificar no
  portão e o humano decide. Qualquer outra dependência de runtime exige justificativa
  registrada no HANDOFF. Dependências dev (pytest) seguem o precedente do domínio 1.
- Rede corporativa com proxy/WAF. Downloads bulk (COTAHIST) devem rodar via o cron em
  **rede limpa** (mesma operação do domínio 1) ou manualmente; o código deve separar
  "baixar" de "processar" para que o processamento rode offline.
- SQLite com WAL + busy_timeout (padrão do core.infra). Banco local, single-writer.

## 2. O que este domínio é (e o adversário)

Sistema de previsão **cross-sectional** de ações da B3: prever quais ações performam
melhor *relativo às outras*, não timing de mercado. Decisão de design: cross-sectional
primeiro porque o sinal é menos diluído (análogo de começar por 1x2 e não placar exato).

- **Adversário:** a eficiência do mercado. Não existe bookmaker nem CLV aqui.
- **Benchmarks (a linha de base a bater, fixados a priori):**
  (a) buy-and-hold do universo equiponderado;
  (b) carteiras aleatórias com o MESMO turnover e MESMO número de posições do modelo
  (distribuição de referência — o modelo precisa estar na cauda dela).
- **Régua:** Sharpe líquido de custos (primária), Sortino, max drawdown, turnover
  (secundárias). Tudo LÍQUIDO — backtest bruto é teatro.
- **Liquidação:** retorno realizado da carteira a preços executáveis, menos custos.

## 3. Arquitetura do repositório

```
predictor-stocks/
  vendor/predictor_core/     # vendorizado, com VERSION carimbada — NÃO editar local
  stocks_predictor/
    ingest_cotahist.py       # download (rede limpa) + parse posicional → raw
    adjust.py                # camada de ajustes (proventos/splits) → adjusted
    universe.py              # universo point-in-time por liquidez
    returns.py               # matriz de retornos a partir do adjusted
    factor.py                # motor interpretável: momentum 12-1 (único fator no início)
    portfolio.py             # construção: quintil superior, equiponderado, long-only
    execution.py             # modelo de execução e custos
    backtest.py              # walk-forward + ledger + métricas
    paper.py                 # ledger forward (paper trading) — o anti-tautologia
    db.py                    # schema + migração idempotente (helpers do core.infra)
    report.py                # relatório vs. benchmarks + ICs
  tests/
  config.yaml
  HANDOFF.md
```

## 4. Camada de dados — COTAHIST (B3)

**Fonte primária:** arquivos COTAHIST da própria B3 (oficial, gratuito, bulk, anual
`COTAHIST_AXXXX.ZIP` + mensal/diário). Inclui papéis deslistados (sem viés de
sobrevivência na fonte). Formato: registros posicionais de largura fixa (245 bytes),
layout oficial documentado pela B3 — **obter o layout oficial e codificar o parse a
partir dele, com testes golden sobre registros reais**, não de memória.

Campos necessários no mínimo: data do pregão, código BDI, código de negociação
(ticker), tipo de mercado, preços de abertura/máx/mín/último, quantidade e volume
financeiro, fator de cotação. Preços vêm com 2 decimais implícitos (÷100).

**Filtros de ingestão:** mercado à vista, lote padrão (códigos BDI/TPMERC conforme
layout oficial — confirmar no documento, não assumir). Tudo o mais entra cru no banco
mas fora do universo.

### As três armadilhas estruturais (cada uma com defesa no schema)

1. **Viés de sobrevivência:** o universo NUNCA é definido por composição atual de
   índice. É derivado dos próprios dados, point-in-time (ver §5).
2. **Ações corporativas:** COTAHIST traz preço NEGOCIADO, sem ajuste. Momentum sobre
   preço bruto é lixo (split parece queda de 50%). Defesa em camadas:
   - tabela `prices_raw` = o dado como publicado, append-only, intocável;
   - tabela `adjustments` = fatores de ajuste por papel/data, com FONTE registrada;
   - série ajustada é VIEW/derivação, nunca sobrescreve o cru;
   - **detector de saltos**: variação overnight além de limiar configurável (ex.
     |r|>30%) sem ajuste registrado → papel entra em quarentena e o evento é logado
     para investigação. Nenhum retorno em quarentena alimenta o fator.
   - Fonte dos fatores de ajuste é o ponto mais fraco do domínio — ver M2 (portão).
3. **Lookahead de execução:** sinal calculado com fechamentos até D só é executável em
   D+1 (abertura). O backtest liquida SEMPRE a preço posterior ao instante do sinal.
   Teste automatizado obrigatório: nenhuma linha do ledger pode ter preço de execução
   com timestamp ≤ timestamp do sinal.

### Schema (princípios; detalhar no M0)

- `prices_raw(date, ticker, open, high, low, close, volume_fin, qty, fator, ...)` —
  append-only, espelho do COTAHIST filtrado.
- `adjustments(ticker, ex_date, factor, type, source, inserted_at)` — append-only.
- `quarantine(ticker, date, reason, resolved_at)`.
- `universe_snapshots(asof_date, ticker)` — composição point-in-time materializada
  (auditável: dá pra responder "qual era o universo em 2019-03-29" para sempre).
- `decisions(...)` — o ledger (ver §7).
- `runs(run_id, config_hash, code_version, started_at, params_frozen_until, ...)`.
- Convenções do domínio 1: migração idempotente no connect, WAL, write-once onde
  aplicável via COALESCE, `config_hash` para detectar staleness.

## 5. Universo point-in-time

Definição (parâmetros no config, valores iniciais pré-registrados):
- Em cada data de rebalanceamento `asof`, universo = top **N=60** papéis por **mediana
  de volume financeiro diário na janela [asof−126 pregões, asof)**, usando SOMENTE
  dados ≤ asof. Excluir papéis em quarentena e papéis com menos de 252 pregões de
  histórico (necessário pro momentum 12-1).
- Um ticker por empresa (na colisão ON/PN, fica o de maior liquidez na janela).
- O snapshot do universo é materializado e nunca recalculado retroativamente com
  código novo sem novo `run_id`.

## 6. Motor interpretável (camada 1): momentum 12-1

UM fator. Zoológico de fatores é proibido até a Hipótese #1 ser julgada.

- Sinal em `asof` (último pregão do mês): retorno acumulado ajustado de
  [asof−252, asof−21] (12 meses excluindo o último — o clássico, que evita a reversão
  de curtíssimo prazo).
- Carteira: **quintil superior do universo, equiponderado, long-only** (parâmetro
  pré-fixado). Racional da escolha de quintil: o decil clássico com N=60 daria só
  6 papéis — concentração excessiva; o quintil (12 papéis) garante diversificação
  mínima sem diluir o sinal.
  Long-only porque short na B3 envolve aluguel (custo/disponibilidade) — complexidade
  adiada deliberadamente, registrada como evolução futura.
- Rebalanceamento mensal: sinal no fechamento do último pregão; execução na ABERTURA
  do primeiro pregão do mês seguinte.
- Sem ML, sem fundamentos, sem fator adicional. Cada um desses é uma hipótese futura
  com pré-registro próprio, só depois que a régua existir e o baseline for julgado.

## 7. Modelo de execução, custos e ledger

- Preço de execução: abertura de D+1. Se papel não negociou em D+1, próxima abertura
  disponível (logado).
- **Custos (fixados a priori, parâmetros no config):** emolumentos+liquidação B3
  0,03%; corretagem 0; spread+slippage **0,15% por lado** como premissa conservadora
  para o universo líquido. Total ida-e-volta ≈ 0,36%. A sensibilidade ao custo entra
  no relatório (rodar também com 2× o custo).
- **Ledger `decisions`** — a linha tem duas partes (costura definida no framework):
  - parte EVAL (universal): `run_id, asof, ticker, signal_value, rank, conviction_band,
    frozen_mode, inserted_at` — escrita no momento da decisão;
  - parte RISK (extensão deste domínio): `exec_date, exec_price, exit_date, exit_price,
    cost_paid, realized_return_net, holding_days` — preenchida na liquidação,
    write-once.
  - PROIBIDO: colunas de CLV/odds/bookmaker. Não existem neste domínio.

## 8. Instrumento de medição (camada 2) — as mutações exigidas do core

- **Walk-forward com params frozen:** janela de calibração → parâmetros congelados →
  janela de teste adiante. Embargo de 1 mês entre calibração e teste (amostras de
  retorno se sobrepõem — purged split).
- **Significância: block bootstrap.** O `ci_mean` (percentile iid) do core é INVÁLIDO
  para séries de retorno autocorrelacionadas. Este domínio exige do core o segundo
  método da família: **stationary/moving-block bootstrap** sobre a série temporal de
  retornos da estratégia vs. benchmark (comprimento de bloco como parâmetro, default
  21 pregões, sensibilidade reportada). ESTA é a primeira evolução por demanda do
  `predictor-core` — implementar no vendor + marcar para upstream no sync.
- Métrica de julgamento: diferença de Sharpe líquido (estratégia − benchmark
  equiponderado) com IC bootstrap em blocos; posição vs. distribuição das carteiras
  aleatórias de mesmo turnover.
- **Paper ledger forward (`paper.py`):** o análogo da captura de aberturas do futebol
  e o anti-tautologia definitivo. Após o backtest, o sistema roda forward: a cada
  rebalanceamento real, registra a carteira ANTES dos preços futuros existirem (cron
  diário em rede limpa, mesmo padrão operacional do domínio 1). É a única validação
  que nenhum lookahead pode contaminar. Começa em M6 e nunca para.

## 9. HIPÓTESE #1 (pré-registrada — copiar para o HANDOFF no M0)

> **H1:** Carteira long-only do quintil superior de momentum 12-1, universo B3
> point-in-time (top 60 por liquidez, janela 126 pregões), equiponderada,
> rebalanceamento mensal com execução na abertura de D+1 e custo total de 0,36%
> ida-e-volta, obtém **Sharpe líquido superior ao buy-and-hold equiponderado do mesmo
> universo**, com IC 95% (stationary bootstrap, bloco 21) da diferença de Sharpe
> excluindo zero, na janela de teste walk-forward.
> **Janela:** calibração/aquecimento até 2017-12; teste 2018-01 → último COTAHIST
> anual completo. **Critérios fixados antes de qualquer rodada.** Resultado
> inconclusivo (IC contém zero) é válido e encerra a hipótese como "não comprovada
> nesta janela" — sem repescagem de parâmetros.

Ajustes de parâmetros após ver resultados = nova hipótese, novo pré-registro, nova
janela. Sem exceções.

## 9b. IA nas beiradas — o analista somente-leitura (permitido desde M2)

Distinção formal que o princípio de camadas autoriza: IA como GERADORA DE SINAL é
proibida até a H1 ser julgada (M6); IA como ANALISTA SOMENTE-LEITURA do que já está
no banco é permitida como ferramenta de auditoria, sob fronteira dura:

**Usos permitidos:**
- Triagem de quarentena: classificar saltos detectados (provável grupamento vs.
  provável erro de fonte vs. inexplicado) como SUGESTÃO para decisão humana;
- **Rascunho do CSV de proventos (M2, rota a):** o analista compila a lista de
  eventos corporativos candidatos do período (lendo quarentena + fontes externas)
  como PROPOSTA; o humano revisa e aprova; só a aprovação humana entra em
  `adjustments`, com source registrada. A IA propõe, o humano assina, o banco só
  recebe o assinado — isso reduz o fardo de manutenção manual sem abrir mão da
  trilha;
- Narração de relatórios: transformar a saída numérica do backtest/paper em texto;
- Revisão de código e análise de logs do cron;
- Sumários de qualidade de dado (cobertura, buracos, papéis com comportamento anômalo).

**Regras invioláveis:**
- A IA NUNCA escreve no banco. Nenhuma tabela, nenhuma linha, nunca.
- A IA NUNCA resolve quarentena: sugere; o humano decide; a trilha em
  `adjustments`/`quarantine` registra a decisão humana.
- Nenhuma saída de IA entra no caminho de cálculo do sinal, do universo, dos retornos
  ou do ledger. Zero. Se um dia entrar, é feature de ML e cai na regra do M7+ com
  pré-registro próprio.
- Toda saída de IA é artefato consultivo salvo em `reports/ai/` com data — auditável,
  descartável, fora do pipeline.

Implementação: módulo `analyst.py` isolado, que LÊ o SQLite e produz arquivos em
`reports/ai/`. Sem dependência do pipeline sobre ele; deletá-lo inteiro não pode
quebrar nenhum teste do sistema de previsão.

## 10. Marcos de implementação (portões: nada avança com teste vermelho)

- **M0 — Gênese.** Esqueleto do repo, vendor do `predictor-core` (net, obs, helpers
  db, ci_mean) com carimbo de versão, config.yaml, schema inicial, HANDOFF.md com a
  H1 copiada. Aceite: estrutura criada, migração roda, suíte (ainda mínima) verde.
- **M1 — Ingestão crua.** Download COTAHIST (separado do parse), parser posicional
  com testes golden sobre registros reais (incluindo casos de borda: fator de cotação
  ≠1, papéis fracionários, encoding), carga em `prices_raw`. Aceite: um ano completo
  carregado; contagens batem com o arquivo; reprocessar é idempotente.
- **M2 — Ajustes (PORTÃO CRÍTICO).** Detector de saltos + quarentena + tabela de
  ajustes. Plano em duas frentes (problemas distintos, defesas distintas):
  - **Splits/grupamentos (saltos grandes — o detector PEGA):** fator inferido do
    próprio COTAHIST: detector acha o salto, razão de preços ao redor do evento
    sugere proporção redonda (1:2, 1:4, 1:5, 10:1...), fator proposto entra em
    `adjustments` com source='inferred' após validação cruzada com fechamento
    ajustado de fonte terciária (yfinance .SA) usada SÓ como verificador — nunca
    como fonte primária de preço. Salto sem proporção plausível = quarentena.
  - **Dividendos/JCP (pequenos — o detector NÃO pega; o perigo é o silêncio):**
    retorno só-preço subestima retorno total e o viés NÃO é neutro — papéis de
    momentum tendem a yield menor, logo omitir proventos FAVORECE a estratégia
    contra o benchmark (viés a nosso favor = o pior tipo). Duas rotas, escolher e
    pré-registrar ANTES do M4:
    (a) **[recomendada]** ingerir proventos de fonte nomeada (CSV curado de eventos
    corporativos — fundamentus/statusinvest como origem; yfinance como cross-check)
    e medir estratégia E benchmark em retorno total; ou
    (b) rodar a H1 em retorno só-preço com a limitação e a DIREÇÃO do viés escritas
    no pré-registro ("positivo marginal é suspeito por construção") — aceitável só
    como primeira passada.
  Aceite: 5+ eventos de split/grupamento conhecidos reproduzidos corretamente na
  série ajustada; zero papéis do universo com salto não explicado; rota de
  dividendos decidida e registrada no HANDOFF. **Se nenhuma fonte de proventos
  fechar e a rota (b) for inaceitável, PARAR e voltar ao design — não improvisar.**
- **M3 — Universo + retornos + benchmarks.** Snapshots point-in-time, matriz de
  retornos, série do benchmark equiponderado e gerador de carteiras aleatórias.
  Aceite: teste automatizado prova que nenhum snapshot usa dado > asof.
- **M4 — Fator + carteira + execução.** Momentum 12-1, quintil, custos. Aceite: teste
  anti-lookahead do ledger (exec_ts > signal_ts, sem exceção); golden master de uma
  janela curta congelado como fixture.
- **M5 — Medição.** Walk-forward purgado, block bootstrap (evolução do core no
  vendor), relatório vs. benchmarks com sensibilidade a custo.
  **Especificação do bootstrap (anti-alucinação — implementar a especificação, não
  improvisar):** stationary bootstrap de Politis & Romano (1994): comprimentos de
  bloco ~ Geométrica(p=1/L), L default 21 pregões, índices circulares (wrap-around),
  RNG com seed obrigatória. Rota alternativa aprovável no portão: moving-block
  (blocos fixos de tamanho L) primeiro — mais simples de implementar corretamente —
  com stationary como refinamento.
  **Aceite do bootstrap (propriedades mecânicas, não leitura de código):**
  (a) TESTE DE COBERTURA: sobre ≥500 séries simuladas com média conhecida e
  autocorrelação AR(1), o IC 95% cobre a verdade em 95%±2pp dos casos — um bootstrap
  com a geometria de blocos errada FALHA aqui de forma detectável;
  (b) comprimento médio empírico dos blocos ≈ L;
  (c) distribuição dos índices reamostrados ~uniforme;
  (d) reprodutível com seed;
  (e) o caso sintético: série autocorrelacionada onde o percentile iid subestima a
  largura do IC e o block a acerta.
  **Robustez de execução obrigatória:** a mesma carteira liquidada a TRÊS preços —
  abertura de D+1, fechamento de D+1, e o pior dos dois por operação — além da
  rodada com 2× o custo. O rebalanceamento mensal concentra execução no leilão de
  abertura (gaps e liquidez pontual); se a H1 só sobrevive na abertura e morre no
  fechamento de D+1, fragilidade de execução é REFUTAÇÃO, não detalhe.
  Aceite geral: todas as propriedades (a)–(e) verdes; relatório com as quatro
  variantes de custo/execução.
- **M6 — Julgamento da H1 + paper forward.** Rodar a H1 EXATAMENTE como pré-registrada,
  uma vez, e registrar o veredito no HANDOFF (comprovada / refutada / inconclusiva).
  Ligar o `paper.py` no cron diário. Aceite: veredito escrito; paper ledger gravando.
- **M7+ — O MAPA COMPLETO DO FUTURO (nomeado aqui para nada se perder; NADA disto é
  autorizado por este documento; cada item exige pré-registro próprio, só após o
  veredito da H1):**
  - **H2 — segundo fator:** reversão de curto prazo (1 mês) como fator independente;
    teste de correlação com momentum antes de combinar.
  - **H3 — combinação de fatores:** só se H1 e H2 sobreviverem individualmente;
    combinação simples (média de ranks) antes de qualquer peso otimizado.
  - **H4 — sizing:** volatility targeting (peso inverso à vol realizada) vs.
    equiponderado; julgado por Sharpe líquido E drawdown.
  - **H5 — short:** perna vendida do último quintil, com custo de aluguel B3 real
    como parâmetro; só se a perna comprada já estiver validada.
  - **H6 — features de ML (a última camada, como manda o framework):** modelo
    treinado walk-forward gerando UM score adicional que entra como candidato a
    fator, julgado pela MESMA régua dos fatores interpretáveis (block bootstrap vs.
    baseline que já inclui H1..H4 aprovados). Template de pré-registro: feature
    definida, dado de treino delimitado no tempo, critério de incremento líquido
    fixado. ML que não paga incremento LÍQUIDO sobre o baseline interpretável é
    descartado — sem exceção, sem "mas é IA".
  - **Análise de regime (consultiva):** estabilidade do fator por subperíodos —
    relatório, não chave de liga/desliga (timing de regime seria H própria).
  - Promoção ao `predictor-core`: ao fim do M6, revisar com o framework quais peças
    deste domínio sobem (block bootstrap já marcado; candidatos: walk-forward
    purgado, gerador de carteiras aleatórias como benchmark genérico).

## 11. Guardrails para o implementador (Claude Code)

- PROIBIDO: ML/IA gerando sinal em qualquer forma antes do M6 julgado (a IA analista
  do §9b é a única exceção, e ela é somente-leitura); IA escrevendo no banco ou
  resolvendo quarentena; lookahead de qualquer
  espécie; sobrescrever `prices_raw` ou linhas do ledger; instalar o core via pip;
  importar código de outro domínio; adicionar dependência de runtime sem registrar
  justificativa no HANDOFF; ajustar parâmetros da H1 após qualquer rodada de
  resultado; "consertar" dados na mão sem trilha em `adjustments`/`quarantine`.
- OBRIGATÓRIO: testes antes de avançar de marco; golden tests com dados reais no
  parse; teste anti-lookahead automatizado; HANDOFF atualizado ao fim de cada marco
  (estado, decisões, próximos passos — o HANDOFF nunca pode mentir sobre a suíte);
  separação download/processamento; tudo reproduzível por `run_id`+`config_hash`.
- Em dúvida de design não coberta aqui: PARAR e perguntar, não decidir em silêncio.
  Decisões contra-intuitivas deste documento (long-only, um fator só, custos
  conservadores, quarentena agressiva) são deliberadas — não "otimizar".

## 12. Fronteira

Este sistema é um instrumento de medição metodológica para um TCC. Não é recomendação
de investimento; o veredito sobre qualquer estratégia é do backtest e do paper ledger,
sob os critérios pré-registrados — e a operação com dinheiro real está fora do escopo
deste documento.
