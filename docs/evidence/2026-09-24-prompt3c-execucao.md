# Prompt 3c — Foundation model zero-shot e execução real (stocks-predictor) — 2026-09-24

Base: Prompts 3a e 3b (PRs #100 e #101). Código e especificações no commit `b07f670` da branch cumulativa
`feature/prompt3c-forecast-20260924`. Execução local no PC 2 (WSL Ubuntu 24.04, Python 3.13.15). Nenhuma credencial,
nenhuma ordem e **nenhum download**.

Convenções: **PROVEN** = constatado nesta sessão; **DECLARED** = descrito, não comprovado aqui; **UNKNOWN** =
indeterminado.

## A. Resumo

- **Foundation model: BLOQUEADO até autorização de download.**
  - A licença foi conferida agora (seção B) e permite o uso: Apache-2.0 no código e nos pesos.
  - O checkpoint (`amazon/chronos-bolt-small`, 190.888.824 bytes) e o pacote `chronos-forecasting` (com torch,
    transformers e pandas) não existem no PC 2. Usá-los exige download, e a regra manda parar e perguntar.
  - A integração está pronta. O modelo entra por um arquivo `stocks-forecasts/1` com proveniência completa,
    gerado num ambiente isolado. A avaliação dele é a mesma dos baselines, restrita às origens depois do corte.
- **Execução real feita com o único dado real local:** `COTAHIST_A2026.ZIP` (sha256 `34b77468…`, de 2026-01-02 a
  2026-09-09, 172 pregões), convertido para o formato PIT v2 com as limitações declaradas (seção F).
  - O período, os parâmetros e a fonte foram fixados e versionados no commit `b07f670` antes da primeira
    execução: [spec](../engineering/2026-09-24-protocol-v2/prompt3c-real-forecast-spec.json),
    [protocolo](../engineering/2026-09-24-protocol-v2/prompt3c-real-protocol-config.json).
  - Janela pela regra "primeiro pregão com contexto completo (64) até o fim do arquivo": **2026-04-07 a
    2026-09-09**, 108 pregões.
- **Taxa livre de risco: indisponível no PC 2.** O Sharpe em excesso, o PSR e a decisão ficam N/A ou NO_DECISION.
- **Todas as decisões são NO_DECISION.** Nenhuma carteira ou previsor ficou elegível: faltam rf, amostra (108 <
  504 pregões), DSR e PBO. Nenhum resultado foi escondido. A carteira EW perdeu 9,5% na janela, com viés de dado
  medido (seção F).
- **Suíte integral isolada** no commit limpo `b07f670`: **1.156 passed + 71 subtests, 0 falhas, 0 erros, 0 skips**,
  297,11 s, cobertura de 80% (piso 77; módulos do 3c entre 84% e 93%). PROVEN.

## B. Candidato de foundation model (verificado em 2026-09-24)

| Campo | Valor |
|---|---|
| ID | `amazon/chronos-bolt-small` (família Amazon Chronos; 48M de parâmetros, CPU) |
| Revisão fixável | `772f3d25d38aec6d914c8949dab4462e2d46f5d8` (HEAD de `main`; os commits depois de 2024-11-13 só mudam o README) |
| Pesos | `model.safetensors`, 190.888.824 bytes, LFS sha256 `06a6a19bbe74bc10a9cd193bd4bf2bf638ae07f7e0d51653ae7ab8ea968a21dd`; último commit que tocou os pesos: `0e96a1377adc`, 2024-11-13T13:28:57Z |
| Licença dos pesos | Apache-2.0 (card e tag `license:apache-2.0` na API do Hugging Face); sem gate |
| Licença do código | `chronos-forecasting` 2.3.2 no PyPI: Apache-2.0 (classifier OSI) |
| Publicação verificável | repositório criado em 2024-11-25T08:18:08Z (API `createdAt`) |
| Corte de contaminação | **2024-11-25**, a data mais recente entre o commit dos pesos e a publicação |
| Período avaliável | origens 2026-04-06, 04-30, 05-29, 06-30 e 07-31 (alvos até 2026-09-09): 747 tarefas, **todas depois do corte** |
| Dependências que entrariam | torch, transformers, accelerate, pandas, numpy, einops. Não entram no projeto: rodariam num venv isolado em `~/predictors/runtime`, que só grava o arquivo de previsões |

Alternativa conferida: `amazon/chronos-2` (Apache-2.0, pesos de 2025-10-30, 477.930.472 bytes). Também seria
pós-corte para 2026, mas é maior. O `chronos-bolt-tiny` (34,6 MB) é a opção mínima. Status de contaminação do
Chronos: **UNKNOWN**, porque nada foi executado. Com a variância pareada observada nos baselines, 747 tarefas
superam as 153 necessárias para detectar 5% de melhora de CRPS. Isso supõe independência entre tarefas, o que é
otimista.

## C. Tabela de entrega

Janela 2026-04-07..2026-09-09, protocolo v2 + spec `0a129bd05767`, custos de 3 + 7,5 + 7,5 bps por lado (os da H1
congelada), universo PIT com ADV ≥ R$ 5 mi em 63 pregões, **sem deslistagens conhecidas** (limitação da fonte).

| candidato | protocolo | período | universo | custos | métrica de forecast | IC / Rank IC | Sharpe líq. (excesso rf) | max DD | turnover | beta | PSR | DSR (pior) | PBO | decision | run_id |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| passeio aleatório gaussiano | v2 | idem | sem deslistadas | N/A | CRPS 0,0602; WQL 0,0529; cobertura 80% = 85,1%; n = 747 | N/A (mediana constante) | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A (previsor) | `f7433c04…` |
| passeio aleatório empírico | v2 | idem | sem deslistadas | N/A | CRPS 0,0634 (5,3% pior que o gaussiano, t = 6,6); WQL 0,0558; cobertura 80% = 70,8% | N/A (mediana constante) | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A (previsor) | `4c7f7fe2…` |
| chronos-bolt-small @ `772f3d25` | v2 | idem | sem deslistadas | — | **BLOQUEADO** (download não autorizado) | — | — | — | — | — | — | — | — | — | — |
| carteira pelo ranking do Chronos | v2 | idem | sem deslistadas | H1 | — | — | **BLOQUEADO** | — | — | — | — | — | — | — | — |
| EW do universo | v2 | idem | sem deslistadas | H1 | N/A | N/A | N/A (sem rf local); retorno líquido −9,53% | −23,06% | 3,77 | 1,05 | N/A | N/A | N/A | NO_DECISION | `4f25763d…` |
| buy-and-hold BOVA11 | v2 | idem | — | H1 | N/A | N/A | N/A (sem rf local); retorno líquido −0,63% | −16,20% | 2,46 (compra inicial numa janela curta) | 1 | N/A | N/A | N/A | NO_DECISION | `8b3e9996…` |
| momentum 12-1 | — | — | — | — | — | — | N/A: 172 pregões no arquivo, menos que os 252 do lookback | — | — | — | — | — | — | não executado | — |

Motivos do NO_DECISION (registrados no ledger, política `1.0.0`, sha256 `4898b7c7…`): taxa livre de risco
ausente; 108 pregões < 504; DSR e PBO não estimáveis; baselines exigidos sem métrica em excesso de rf.

## D. Suíte, validação, N_trials e política

- **Suíte integral isolada** (`prompt3c_suite.sh`: `env -i`, `unshare --net`; mesmo comando do CI), no commit limpo
  `b07f670`: **1.156 passed + 71 subtests, 0 falhas**, 297,11 s, rede inalcançável, ambiente só com
  `HOME`, `LANG` e `PATH`. A execução real rodou em paralelo, fora do worktree, e não sujou a árvore.
- 12 testes novos (`tests/test_v2_forecast.py`); 107 testes no `v2`. Mutação: 4 defeitos injetados, 4 detectados:

  | Defeito injetado | Testes que falharam |
  |---|---|
  | Sem filtro de salto | 1 |
  | Corte pela data mais antiga | 1 |
  | Proveniência opcional | 2 |
  | Perda quantílica sem τ | 2 |
- **Parâmetros:**
  - h = 21; contexto de 64 pregões consecutivos; níveis 0,1–0,9; limiar de salto de 0,30 (congelado).
  - Baseline de comparação: passeio aleatório gaussiano.
  - Poder: α = 0,05, 1 − β = 0,8, melhora mínima detectável de 5%.
  - Rebalanceamento mensal; execução em D+1 na abertura.
- **N_trials:** 4 execuções no ledger da execução real, mais o limite inferior de 71 = N = 75. Grade {75, 150, 375}
  mais N_upper = 150. O DSR não foi calculado: sem rf e sem família de candidatos com retorno em excesso.
- **Política:** `1.0.0`, sha256 `4898b7c7…`, `PROPOSED_PENDING_OWNER_APPROVAL`.
- **Resultado:** [real-execution.json](../engineering/2026-09-24-protocol-v2/evidence/prompt3c/real-execution.json)
  (sha256 `3eda54de…`). O ledger tem 10 registros (cabeça `82ea39bb…`) e fica fora do repositório, em
  `~/predictors/runtime/stocks/real3c/`, porque contém nome do host e pid.

## E. Amostra e contaminação

- Previsores sem pré-treino: `NOT_APPLICABLE`.
- Chronos: corte em 2024-11-25. Todas as 747 tarefas (5 origens, de 140 a 154 papéis cada) são posteriores. O status
  seria `CLEAN_POST_CUTOFF` ou `INSUFFICIENT_SAMPLE` conforme a variância pareada do próprio modelo; hoje é
  **UNKNOWN**, porque ele não foi executado.
- 5 origens é pouco para IC por período: o Rank IC de um ranqueador teria n = 5 no ICIR. Conclusões sobre
  ranking exigiriam mais meses.

## F. Limitações de dados

- **Sobrevivência:** o COTAHIST não informa deslistagens. Dentro de 2026, o universo inclui todos que negociaram,
  mas um papel que deixou de negociar fica "listado" e com a marcação parada.
- **Point-in-time / eventos:**
  - Sem eventos societários nem proventos, os preços não são ajustados.
  - Nas tarefas de previsão, janelas com |r| diário > 30% são excluídas (17 no contexto ou no alvo).
  - Nas carteiras não há filtro, e o viés foi medido, não corrigido: 6 movimentos diários > 30% em papéis da
    carteira EW (SBSP3 −80,2% em 2026-04-29; ORVR3 −75,7% em 2026-08-11; ANIM3 −32,8%; HAPV3 −33,1%;
    BHIA3 −33,3%; AZEV4 +35,5%), com peso de cerca de 0,6% cada. Juntos, somam cerca de −1,5% do NAV se forem
    todos artificiais. Os dois maiores têm cara de desdobramento.
  - Proventos em dinheiro não creditados também puxam o retorno das ações para baixo. O BOVA11 não distribui.
  - Não reexecutei nada depois de ver esses números.
- **Taxa livre de risco:** ausente (SGS 11/12 não versionadas no PC 2).
- **Janela curta:** 172 pregões no total e 108 avaliados. Momentum 12-1 é impossível, e o mínimo de 504 da
  política não é atingido.

## G. Interpretação (estritamente dos resultados)

- Na janela 2026-04-07..2026-09-09, o passeio aleatório gaussiano tem CRPS 5,3% menor que o empírico. A diferença
  pareada tem t = 6,6, mas as tarefas do mesmo mês são dependentes, então o t é otimista.
- O empírico é subdisperso (cobertura de 70,8% para 80% nominal) e o gaussiano, levemente sobredisperso (85,1%).
- O BOVA11 ficou praticamente estável (−0,6%). A EW líquida caiu 9,5%, com parte da queda explicada por dado não
  ajustado (seção F).
- Não há evidência de estratégia ou de modelo: nenhuma decisão foi possível.

## Próximo passo

- **O Prompt 4 pode assumir como PROVEN:**
  - o protocolo v2 completo (dados PIT, execução, custos, baselines, CPCV, DSR/PBO, política e ledger);
  - o caminho de dado real local (COTAHIST com hash → PIT v2) com limitações declaradas;
  - a avaliação probabilística (CRPS/WQL) com filtro de salto;
  - a integração de modelo pré-treinado por arquivo com proveniência;
  - as suítes isoladas e verdes nos commits limpos.
- **DECLARED:** a data de publicação e a licença do Chronos (API e card do Hugging Face e PyPI, 2026-09-24).
- **UNKNOWN:**
  - o desempenho do Chronos;
  - a série real de CDI/Selic;
  - dados históricos de 2019–2025 com eventos e anúncios, necessários para reavaliar hipóteses de 12 meses.
- **Bloqueios que dependem do dono:**
  1. autorizar o download do checkpoint e do pacote (ou trazer do PC 1);
  2. autorizar o download da SGS 12 (CDI) ou 11 (Selic) do BCB para 2026;
  3. decidir de onde vem a história 2019–2025 com eventos (bancos do PC 1). Sem isso, o Prompt 4 só consegue
     reavaliar hipóteses no artefato histórico (régua nova sobre resultado antigo), não reexecutar.
