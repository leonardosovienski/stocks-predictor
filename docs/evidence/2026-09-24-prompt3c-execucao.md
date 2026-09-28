# Prompt 3c — Foundation model zero-shot e execução real (stocks-predictor) — 2026-09-24

Base: Prompts 3a e 3b (PRs #100 e #101). Branch cumulativa `feature/prompt3c-forecast-20260924`:

| Commit | Conteúdo |
|---|---|
| `b07f670` | Protocolo de previsão e especificações da execução real |
| `5048a80` | Chronos isolado e CDI |
| `ab66a48` | Identidade da rf no manifesto; execução final |

Execução local no PC 2 (WSL Ubuntu 24.04, Python 3.13.15). Nenhuma credencial, nenhuma ordem.

Downloads **autorizados pelo dono nesta sessão** (resposta de 2026-09-24): checkpoint Chronos-Bolt small e pacote
`chronos-forecasting` num venv isolado; CDI da SGS 12 do BCB; COTAHIST 2019–2025, que é para o Prompt 4 e não é
usado aqui.

Convenções: **PROVEN** = constatado nesta sessão; **DECLARED** = descrito, não comprovado aqui; **UNKNOWN** =
indeterminado.

## A. Resumo

- **Foundation model avaliado, e perde para o baseline.**
  - `amazon/chronos-bolt-small` @ `772f3d25` rodou zero-shot, sem rede, com pesos conferidos.
  - No período limpo 2026-04-07..2026-09-09 (747 tarefas, todas posteriores ao corte de contaminação de
    2024-11-25), o CRPS foi **19,9% pior** que o do passeio aleatório gaussiano (0,0722 contra 0,0602;
    t = 7,7). A cobertura do intervalo de 80% ficou em 72,2%.
  - Status pela regra pré-declarada: **INSUFFICIENT_SAMPLE**. Detectar 5% de melhora exigiria 1.552 tarefas.
  - Sem evidência de ranking: IC −0,013 e Rank IC 0,016 em 5 origens.
- **Carteira pelo ranking do Chronos:** −11,5% líquido; Sharpe em excesso do CDI −1,68; PSR 0,14; turnover 19,4.
  EW: −9,5% e Sharpe −1,69. BOVA11: −0,6% e Sharpe −0,74.
- **Todas as decisões são NO_DECISION.** A política recusa decidir com 108 pregões (< 504) e sem DSR/PBO.
  Nenhum resultado negativo foi escondido.
- **Dados:** `COTAHIST_A2026.ZIP` (sha256 `34b77468…`) → PIT v2 com limitações (seção F); CDI SGS 12 (sha256 do
  bruto `b91bbcd9…`, série `567b931f…`, 1.942 pregões de 2019-01-02 a 2026-09-23).
  - O período, os parâmetros e a fonte foram versionados em `b07f670`, antes da primeira execução.
  - Janela pela regra da especificação: 2026-04-07..2026-09-09.
- **Suíte integral isolada** no commit limpo `ab66a48`: **1.158 passed + 71 subtests, 0 falhas**, 349,56 s, cobertura
  de 80%. PROVEN.

## B. Foundation model: proveniência (verificada em 2026-09-24)

| Campo | Valor |
|---|---|
| ID / revisão | `amazon/chronos-bolt-small` @ `772f3d25d38aec6d914c8949dab4462e2d46f5d8` |
| Pesos | `model.safetensors`, 190.888.824 bytes, sha256 `06a6a19bbe74bc10a9cd193bd4bf2bf638ae07f7e0d51653ae7ab8ea968a21dd` (= LFS oid do Hugging Face; conferido antes de cada uso); `config.json` sha256 `9ca0ebbe…` |
| Licenças | pesos Apache-2.0 (card e tag da API, sem gate); código `chronos-forecasting` 2.3.2 Apache-2.0 (PyPI) |
| Datas | commit dos pesos 2024-11-13T13:28:57Z; repositório público 2024-11-25T08:18:08Z → **corte 2024-11-25** |
| Ambiente isolado | `~/predictors/runtime/stocks/chronos-venv` com Python 3.13.15, torch 2.14.0+cpu, chronos-forecasting 2.3.2, transformers 5.17.0, accelerate 1.15.0, numpy 2.5.3, pandas 3.0.6, einops 0.8.2, safetensors 0.8.0, huggingface-hub 1.33.0. [Freeze completo](../engineering/2026-09-24-protocol-v2/evidence/prompt3c/chronos-venv.freeze.txt). Nada disso entra no `uv.lock` do projeto |
| Execução | `tools/chronos_forecast.py`: `env -i`, `unshare --net` (rede inalcançável constatada), `HF_HUB_OFFLINE=1`, 4 threads, contexto de 64 fechamentos, quantis 0,1–0,9 no passo 21. 747 previsões em 6 s; 0 linhas com quantis cruzados. A reexecução deu entradas **idênticas** |
| Vínculo | tarefas `833b86f7…` (`tasks_sha256`); previsões `403b8a2e…` ([arquivo](../engineering/2026-09-24-protocol-v2/evidence/prompt3c/chronos-forecasts.json)) |

## C. Tabela de entrega

Janela 2026-04-07..2026-09-09 (108 pregões), protocolo v2 + spec `0a129bd05767`, custos da H1 congelada (3 + 7,5 +
7,5 bps por lado), universo PIT com ADV ≥ R$ 5 mi em 63 pregões, **sem deslistagens conhecidas** (limitação da
fonte), rf = CDI SGS 12. Execução final no commit `ab66a48`.

| candidato | protocolo | período | universo | custos | métrica de forecast | IC / Rank IC | Sharpe líq. (excesso rf) | max DD | turnover | beta | PSR | DSR (pior) | PBO | decision | run_id |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| passeio aleatório gaussiano | v2 | idem | sem deslistadas | N/A | CRPS 0,0602; WQL 0,0529; cobertura 80% = 85,1%; n = 747 | N/A (mediana constante) | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A (previsor) | `0511b781…` |
| passeio aleatório empírico | v2 | idem | sem deslistadas | N/A | CRPS 0,0634 (5,3% pior que o gaussiano; t = 6,6); WQL 0,0558; cobertura 70,8% | N/A (mediana constante) | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A (previsor) | `83e24daf…` |
| **chronos-bolt-small** zero-shot | v2 | idem | sem deslistadas | N/A | CRPS **0,0722** (19,9% pior que o gaussiano; t = 7,7); WQL 0,0614; cobertura 72,2%; contaminação **INSUFFICIENT_SAMPLE** (747 < 1.552) | IC −0,013 / Rank IC 0,016 (5 origens; t −0,27 / 0,23) | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A (previsor) | `90f31fe7…` |
| carteira pelo ranking do Chronos (quintil superior da mediana) | v2 | idem | sem deslistadas | H1 | N/A | N/A | **−1,68** (líquido −11,47%) | −22,71% | 19,44 | 1,05 | 0,14 | N/A (1 candidato: V[SR] não estimável) | N/A (1 configuração) | NO_DECISION: < 504 pregões; DSR e PBO não estimáveis | `d0a320c2…` |
| EW do universo | v2 | idem | sem deslistadas | H1 | N/A | N/A | −1,69 (líquido −9,53%) | −23,06% | 3,77 | 1,05 | 0,14 | N/A | N/A | NO_DECISION | `69746943…` |
| buy-and-hold BOVA11 | v2 | idem | — | H1 | N/A | N/A | −0,74 (líquido −0,63%) | −16,20% | 2,46 (compra inicial numa janela curta) | 1 | 0,32 | N/A | N/A | NO_DECISION | `6f3db56d…` |
| momentum 12-1 | — | — | — | — | — | — | N/A: 172 pregões em 2026 < 252 do lookback | — | — | — | — | — | — | não executado | — |

Política `1.0.0`, sha256 `4898b7c7…`, `PROPOSED_PENDING_OWNER_APPROVAL`. As decisões ficam no ledger como registros
`DECISION`: 8 no total, somando as três execuções.

## D. Suíte, validação, N_trials e política

- **Suíte integral isolada** (`env -i`, `unshare --net`; mesmo comando do CI):

  | Commit | Resultado |
  |---|---|
  | `b07f670` | 1.156 passed + 71 subtests, 0 falhas |
  | `5048a80` | 1.158 passed + 71 subtests, 0 falhas |
  | `ab66a48` | **1.158 passed + 71 subtests, 0 falhas**, cobertura de 80% |
- **Testes:** 14 em `tests/test_v2_forecast.py`, mais 2 asserções de rf nos testes do 3b.
- **Mutação** (4 defeitos injetados, 4 detectados):

  | Defeito injetado | Testes que falharam |
  |---|---|
  | Sem filtro de salto | 1 |
  | Corte pela data mais antiga | 1 |
  | Proveniência opcional | 2 |
  | Perda quantílica sem τ | 2 |
- **Parâmetros:** h = 21; contexto de 64; níveis 0,1–0,9; limiar de salto 0,30 (congelado); baseline gaussiano;
  poder com α = 0,05, 1 − β = 0,8 e melhora mínima de 5%; rebalanceamento mensal; execução em D+1 na abertura.
- **N_trials:**
  - O ledger real tem 16 execuções. São três rodadas: a primeira sem rf e sem Chronos (4), a segunda com Chronos
    e CDI (6), a final depois da correção de proveniência (6). Com o limite inferior de 71, N = 87.
  - Grade: {87, 174, 435} + N_upper 150.
  - O DSR não é estimável: há um só candidato de carteira, e V[SR] precisa de pelo menos 2 Sharpes da família.
    O PBO também não, com uma só configuração.
  - As rodadas repetidas não mudaram nenhuma métrica. Elas estão no ledger e contam no N, o que só deixa o N
    mais conservador.
- **Resultado final:** [real-execution-final.json](../engineering/2026-09-24-protocol-v2/evidence/prompt3c/real-execution-final.json)
  (sha256 `dd395a54…`). O ledger (40 registros, cabeça registrada no resultado) fica em
  `~/predictors/runtime/stocks/real3c/`, fora do Git, porque contém nome do host e pid.

## E. Amostra e contaminação

- Corte do Chronos em 2024-11-25. As 747 tarefas (5 origens, de 140 a 154 papéis cada) são todas posteriores:
  não há contaminação pelo período.
- Poder: com o desvio pareado observado para o Chronos (0,0423), detectar 5% de melhora de CRPS exigiria 1.552
  tarefas, e há 747. **INSUFFICIENT_SAMPLE** para a pergunta pré-declarada.
  - A diferença observada é de outra ordem: 19,9% **pior**, com t = 7,7.
  - Esse t supõe tarefas independentes. As do mesmo mês são correlacionadas, então o t é otimista.
- Com 5 origens, o IC por período tem n = 5. Nada se conclui sobre ranking.

## F. Limitações de dados

- **Sobrevivência:** o COTAHIST não informa deslistagens. Um papel que deixou de negociar fica "listado" e com a
  marcação parada.
- **Eventos:**
  - Os preços não são ajustados. Nas tarefas de previsão, janelas com |r| > 30% foram excluídas (17).
  - Nas carteiras não há filtro, e o viés foi medido, não corrigido: 6 movimentos > 30% em papéis da EW, como
    SBSP3 −80,2% e ORVR3 −75,7%, que têm cara de desdobramento. O efeito é de cerca de −1,5% do NAV se forem todos
    artificiais.
  - Proventos em dinheiro não foram creditados. O BOVA11 não distribui.
- **Janela curta:** 108 pregões avaliados; momentum 12-1 é impossível; o mínimo de 504 da política não é
  atingido.
- **rf:** CDI diário da SGS 12, gravado com recibo (URL, horário, sha256). Todos os pregões da janela têm taxa;
  nenhum caiu no `RiskFreeError`.

## G. Interpretação (estritamente dos resultados)

- Na janela 2026-04-07..2026-09-09, para 21 pregões à frente em ações líquidas da B3, o Chronos-Bolt small
  zero-shot teve CRPS 19,9% pior que um passeio aleatório gaussiano com volatilidade do próprio contexto.
  - Foi subdisperso: 72,2% de cobertura para 80% nominal.
  - Não ranqueou os papéis melhor que o acaso: Rank IC 0,016 em 5 origens.
- A carteira pelo ranking dele perdeu 11,5% líquido, perto da EW (−9,5%), com giro 5 vezes maior.
- Pela régua pré-declarada, a amostra é insuficiente (INSUFFICIENT_SAMPLE) e a política não decide. Não há
  evidência a favor do modelo, e há um resultado negativo consistente nesta janela.

## Próximo passo

- **O Prompt 4 pode assumir como PROVEN:**
  - o protocolo v2 completo (dados PIT, execução em D+1, custos líquidos, baselines, CPCV, DSR com grade de N,
    PBO, política versionada, ledger com rf e política no manifesto);
  - o caminho de dado real local (COTAHIST com hash → PIT v2) com limitações declaradas;
  - o CDI da SGS 12 versionado;
  - o foundation model avaliado zero-shot, pior que o baseline e INSUFFICIENT_SAMPLE;
  - COTAHIST 2019–2025 baixados e verificados (2021–2025 iguais aos hashes do D-16; 2019 e 2020 como primeira
    aquisição).
- **DECLARED:** datas e licenças do Chronos (Hugging Face e PyPI, 2026-09-24); N_upper = 150.
- **UNKNOWN:**
  - eventos societários com data de anúncio;
  - fundamentos da CVM no PC 2 (necessários para H17, H18 e H19);
  - o conteúdo dos bancos do PC 1.
- **Regras que valem para o Prompt 4:** a `reopen_policy` do `RESEARCH_FREEZE.md` proíbe reabrir família
  encerrada sem 6 campos revisados por um humano. As hipóteses H1–H16 e H20–H22 só recebem a régua nova sobre o
  artefato histórico, sem reexecução.
