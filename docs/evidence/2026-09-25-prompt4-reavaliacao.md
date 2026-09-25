# Prompt 4 — Reavaliar hipóteses sem reabrir o espaço de busca (stocks-predictor) — 2026-09-25

Base: Prompts 3a–3c (PRs #100–#102 mergeadas; continuação do 3c na #103). Código no commit `bfdcf2f` da branch
cumulativa `feature/prompt4-reassessment-20260924`. Execução local no PC 2 (WSL Ubuntu 24.04, Python 3.13.15).
Nenhuma credencial, nenhuma ordem, nenhum backtest novo, nenhum download nesta etapa.

Convenções: **PROVEN** = constatado nesta sessão; **DECLARED** = descrito no repositório, não comprovado aqui;
**UNKNOWN** = indeterminado.

## 0. Verificação prévia (o que os Prompts 3a–3c deveriam ter entregue)

| Requisito | Onde | Estado |
|---|---|---|
| Dados point-in-time | `v2/dataset.py`, `v2/cotahist_dataset.py` | PROVEN (testes do 3a/3c) |
| Baselines | `v2/baselines.py` | PROVEN |
| Validação temporal e CPCV | `v2/walkforward.py`, `v2/cpcv.py` | PROVEN |
| Custos explícitos | `v2/costs.py`, `v2/engine.py` | PROVEN |
| Registro de tentativas | `v2/manifest.py` (TrialLedger) | PROVEN |
| Métricas de fator | `v2/factor_metrics.py` | PROVEN |
| DSR/PBO | `v2/metrics.py`, `v2/pbo.py` | PROVEN |
| Política versionada | `policy/stocks-evaluation-policy-v1.json` (`1.0.0`, sha256 `4898b7c7…`) | PROVEN, ainda `PROPOSED_PENDING_OWNER_APPROVAL` |

Nada faltou. Este prompt acrescentou `v2/reassessment.py` e `v2/preregistration.py`.

## A. Resumo

- **Nenhuma hipótese ganhou variante, filtro, parâmetro, universo ou período novo.** Nenhum backtest novo. As
  hipóteses encerradas receberam só a régua nova sobre o artefato histórico. A `reopen_policy` do
  `RESEARCH_FREEZE.md` exige 6 campos revisados por um humano para reabrir família encerrada.
- **H1–H16 (15 artefatos; a H3 nunca foi executada):** **NOT_SUPPORTED mantido, e mais conservador.**
  - O DSR histórico de cada veredito foi reproduzido exatamente a partir do próprio relatório.
  - Na grade de N atual {102, 150, 204, 510}, o pior DSR fica em no máximo 0,073, exceto a H11 (0,562). Todos
    abaixo de 0,95.
  - O retorno anual de todas, exceto a H11, ficou abaixo do CDI da mesma janela (9,41% a.a. em 2019–2026).
- **H17–H19:** continuam pausadas. Os runners estão bloqueados por governança: exigem o dataset reconstruído
  validado (PC 1) e a metodologia registrada por um humano. Os dados da CVM também não estão no PC 2.
- **H20, H21, H22, BIG_WINNER V1/V2 e RJ:** status mantidos (seção B).
- **Holdout prospectivo selado** no ledger: de 2026-09-10 a 2027-09-10, sha256 do selo `d2fc50e7…`. Nunca
  aberto.
- **Suíte integral isolada** no commit limpo `bfdcf2f`: **1.166 passed + 71 subtests, 0 falhas**, cobertura de
  80%. PROVEN.

## B. Tabela de entrega

N_trials do domínio: limite inferior de 71 (Prompt 2), mais 16 execuções reais do 3c, mais 15 reavaliações = **102**
(LOWER_BOUND). Os registros ficam no ledger do domínio (`~/predictors/runtime/stocks/real3c/ledger.jsonl`,
56 registros, cabeça `f9dc9367…`).

| hipótese | status anterior | protocolo aplicado | status novo | motivo | N_trials | run_id / evidência |
|---|---|---|---|---|---|---|
| H1 momentum 12-1 | CLOSED_JUDGED; NOT_SUPPORTED (IC cruza 0; DSR não publicado) | régua nova sobre o artefato (DSR na grade de N, com D = 1 aproximado; CDI) | NOT_SUPPORTED mantido, mais conservador | pior DSR 0,024 (N = 510); 0,67% a.a. contra CDI de 9,41% | 102 | `reports/h1_verdict_20260712T…md`; REASSESSMENT `bbf7e68f…` |
| H2 low-vol | CLOSED_JUDGED; NOT_SUPPORTED (DSR 0,7092, N = 2) | idem, com D implícito = 1,009 | idem | DSR 0,709 → 0,036; 2,22% a.a. contra 9,41% | 102 | `reports/h2_…`; `ebbccf24…` |
| H3 | CLOSED_JUDGED (mapa de admissão) | — | **NOT_REPRODUCIBLE** | nunca executada; não há artefato | 102 | `research_admission.closed_hypotheses`; Prompt 2 §5 |
| H4 vol-target | CLOSED_JUDGED; NOT_SUPPORTED (DSR 0,6843, N = 3) | idem (D = 1,008) | idem | DSR → 0,029; 1,48% a.a. | 102 | `reports/h4_…`; `88a475fa…` |
| H5 reversão 21d | CLOSED_JUDGED; NOT_SUPPORTED (anti-sinal; DSR 0,1274) | idem (D = 0,995) | idem | DSR → 0,0015; −10,19% a.a. | 102 | `reports/h5_…`; `9f24505c…` |
| H6 momentum 6-1 | CLOSED_JUDGED; NOT_SUPPORTED (DSR 0,4565) | idem (D = 0,990) | idem | DSR → 0,026; 1,24% a.a. | 102 | `reports/h6_…`; `1e798a65…` |
| H7 ROE | CLOSED_EMBARGO_ORIGINAL; NOT_SUPPORTED (DSR 0,5795) | idem (D = 1,001) | idem | DSR → 0,073; 4,37% a.a.; fundamento com embargo estimado | 102 | `reports/h7_…`; `bda9e09c…` |
| H8 momentum ∩ low-vol | CLOSED_JUDGED; NOT_SUPPORTED (DSR 0,6050) | idem (D = 1,022) | idem | DSR → 0,065; 4,44% a.a. | 102 | `reports/h8_…`; `f6048e21…` |
| H9 alavancagem | CLOSED_EMBARGO_ORIGINAL; NOT_SUPPORTED (DSR 0,3479) | idem (D = 1,005) | idem | DSR → 0,021; −1,15% a.a. | 102 | `reports/h9_…`; `3e293b46…` |
| H10 ROE ∩ alavancagem | CLOSED_EMBARGO_ORIGINAL; NOT_SUPPORTED (DSR 0,3661) | idem (D = 1,009) | idem | DSR → 0,023; −0,50% a.a. | 102 | `reports/h10_…`; `0cc4eb11…` |
| H11 momentum 12-1, retorno total | CLOSED_JUDGED; NOT_SUPPORTED (DSR 0,8430, N = 10) | idem (D = 1,042) | idem | DSR 0,843 → 0,562; 25,99% a.a. contra CDI de 6,33% (2019–2022), mas com IC da diferença cruzando 0 e DSR < 0,95 | 102 | `reports/h11_…`; `05e3f746…` |
| H12 margem líquida | CLOSED_EMBARGO_ORIGINAL; NOT_SUPPORTED (DSR 0,1952) | idem (D = 1,002) | idem | DSR → 0,025; −0,32% a.a. | 102 | `reports/h12_…`; `0ce17bd7…` |
| H13 crescimento de receita | CLOSED_EMBARGO_ORIGINAL; NOT_SUPPORTED (DSR 0,2598) | idem (D = 1,002) | idem | DSR → 0,045; 1,13% a.a. | 102 | `reports/h13_…`; `fcacfb82…` |
| H14 máxima de 52 semanas | CLOSED_JUDGED; NOT_SUPPORTED (DSR 0,3249) | idem (D = 1,014) | idem | DSR → 0,047; 3,25% a.a. | 102 | `reports/h14_…`; `f4ee8eab…` |
| H15 surto de volume | CLOSED_JUDGED; NOT_SUPPORTED (DSR 0,2826) | idem (D = 1,006) | idem | DSR → 0,033; 2,05% a.a. | 102 | `reports/h15_…`; `ba8636f1…` |
| H16 virada do mês | CLOSED_JUDGED; NOT_SUPPORTED (DSR 0,0052) | idem (D = 1,002) | idem | DSR → 0,0002; −3,98% a.a. | 102 | `reports/h16_…`; `ed0021cc…` |
| H17 accruals | PAUSED_INCONCLUSIVE_DATA_QUALITY (já observada: IC −0,0132) | nenhum: bloqueada | PAUSED mantido | exige dataset reconstruído validado e metodologia registrada por humano (`RESEARCH_FREEZE.md`); DFC/CVM ausente no PC 2; não pode virar confirmação | 102 | `docs/research/2026-09-07-h17-observations.jsonl` (`03c8f22d…`) |
| H18 E/P | PAUSED (pré-registrada, nunca observada) | nenhum: bloqueada | PAUSED mantido | mesmos bloqueios; FRE/ações em circulação ausentes no PC 2 | 102 | `RESEARCH_FREEZE.md` §ADENDO |
| H19 B/M | PAUSED (idem) | nenhum: bloqueada | PAUSED mantido | idem | 102 | idem |
| H20 | CLOSED_HISTORICAL | régua nova: não aplicável numericamente | mantido | a revisão de 2026-09-08 registra que a estratégia completa nunca foi testada em lucro líquido; não há métrica comparável | 102 | `docs/research/2026-09-08-chat-review.md` |
| H21 BOVA11 buy-and-hold | CLOSED_HISTORICAL_CONDITIONAL | política v1 | mantido; **não pode virar GO** | a política exige vencer o buy-and-hold do índice, e a H21 é esse baseline; o plano prospectivo vai até 2027-09-10, dentro do holdout selado | 102 | `docs/research/2026-09-09-h21-forward-plan.json` (`9f39f68a…`) |
| H22 | CLOSED_REJECTED (24 avaliações, 11 pares rejeitados) | régua nova | mantido | uma régua mais estrita não reverte rejeição | 102 | `docs/research/2026-09-10-r5/ledgers.json` (`9a4a3834…`) |
| BIG_WINNER V1 (16 + 7 detectores) | NOT_SUPPORTED / INCONCLUSIVE_DATA_QUALITY | nenhum (reusam os sinais da H1 e da H11) | mantido | família encerrada | 102 | `experiments/BIG_WINNER_*_V1/audit/detector_registry.md` |
| BIG_WINNER V2-H01 (momentum 12-1) | UNVALIDATED_PROSPECTIVE_CANDIDATE | nenhum histórico: reexecutar reabriria a família H1 | PENDING_PROSPECTIVE_EVIDENCE mantido | evidência só prospectiva (0 decisões elegíveis até agora); decisões depois de 2026-09-19 caem no holdout selado | 102 | `V2_SELECTION_FREEZE.yaml` (`44277c6c…`) |
| BIG_WINNER V2-H02/H03 e H04/H05 | rejeitadas e adiadas | nenhum | mantido | — | 102 | idem |
| RJ (8 famílias) | arquivada; só dado sintético | nenhum | **NOT_REPRODUCIBLE** com dado real | não há fonte real nomeada | 102 | `RESEARCH_FREEZE.md` §9 |
| Chronos-Bolt small zero-shot (3c) | INSUFFICIENT_SAMPLE / NO_DECISION | já no protocolo v2 | mantido | CRPS 19,9% pior que o baseline; amostra < 1.552 | 102 | `docs/evidence/2026-09-24-prompt3c-execucao.md` |
| Sonda `stocks:QUAL-PIT-MOM-001` | sonda de qualificação (D-16), não é hipótese de retorno | N/A | N/A | — | — | predictor-qualification `RAW_LOGS/d16` (DECLARED) |

## C. Incompatibilidades entre o protocolo antigo e o novo, e prováveis causas

Evidência: auditoria do Prompt 2. As listas por hipótese estão em `reassessment.BIASES` e em cada registro
`REASSESSMENT`.

| Incompatibilidade | Hipóteses | Direção |
|---|---|---|
| Execução no fechamento do sinal. Os relatórios **declaram** "abertura de D+1", mas o `legacy_walk_forward` executa no fechamento de D | H1, H2, H4–H16 | favorece a estratégia |
| Fundamento com embargo estimado (ref_date + 90 dias) em vez da data de divulgação | H7, H9, H10, H12, H13 | pode favorecer (informação antecipada) |
| Identidade pelo prefixo do ticker; quarentena pelo estado de resolução atual | todas as julgadas | sobrevivência mal tratada |
| Retorno só de preço | todas, exceto a H11 | o pré-registro da H1 declara que favorece momentum |
| Benchmark EW sem custo | todas | desfavorece a estratégia |
| Sharpe com rf = 0 | todas | superestima; o CDI foi positivo em todo pregão (mínimo diário de 0,0075% entre 2019 e 2026) |

Nenhuma hipótese "funcionava": todas foram NOT_SUPPORTED mesmo com vieses a favor. Então não há resultado
positivo antigo para atribuir a esses vieses. A régua nova só pode manter ou endurecer o veredito, e foi o que
aconteceu.

## D. Integridade experimental

- **Variantes novas em hipóteses encerradas: 0.**
- **Holdout acessado: NO.** Selado em 2026-09-25T15:00:35Z (registro 56, selo `d2fc50e7…`). Intervalo de
  2026-09-10 a 2027-09-10; conteúdo `FUTURE`, com o sha256 do arquivo gravado na abertura.
  - Condições: abrir só depois de 2027-09-10, com aprovação humana registrada (quem, quando, motivo, canal); uma
    única abertura; só hipóteses pré-registradas antes dela.
  - O último pregão local é 2026-09-09, então nada do intervalo foi lido.
- **Pré-registros antes de novos experimentos: N/A.** Não houve experimento novo. O mecanismo existe:
  `preregister` (17 campos, ID imutável) e `require_preregistration`, que barra backtest sem pré-registro.
- **Deduplicação: N/A**, sem candidata nova. O mecanismo `dedup_check` (|ρ| ≥ limiar → `REJECTED_REDUNDANT`, só no
  período de desenvolvimento) está testado.
- **Tentativas acrescentadas:** nenhuma execução de estratégia neste prompt; 15 registros `REASSESSMENT` e
  1 `HOLDOUT_SEALED`, todos no ledger. Nada foi apagado.
- **N_trials final: LOWER_BOUND 102.**
  - Sensibilidade do DSR com N = 102, 150, 204 e 510, e decisão pelo pior caso (N = 510).
  - N_upper = 150 é DECLARED do Prompt 2; como o N conhecido passou de 102, a grade inclui 5N = 510.

## E. Verificação

- 8 testes novos (`tests/test_v2_prompt4.py`):
  - reprodução exata dos 14 DSR publicados;
  - régua sempre mais conservadora;
  - pré-registro imutável e obrigatório;
  - holdout com abertura única e aprovação;
  - deduplicação;
  - CLI que nunca sobrescreve.
- Suíte integral isolada (`env -i`, `unshare --net`) no commit limpo `bfdcf2f`: 1.166 passed + 71 subtests,
  0 falhas, 324,78 s, cobertura de 80%.
- ruff limpo; pyright com 0 erros em 3.13 e 3.14; R8 re-selado com recibos novos (256 arquivos de código);
  gitleaks sem achados.
- Saídas:
  - [reassessment.json](../engineering/2026-09-24-protocol-v2/evidence/prompt4/reassessment.json) (sha256
    `b32b6333…`);
  - [governance-records.jsonl](../engineering/2026-09-24-protocol-v2/evidence/prompt4/governance-records.jsonl)
    (`66ae51e0…`): os 16 registros de governança, com hashes da cadeia, sem host nem pid. O campo `artifact`
    guarda o caminho local absoluto do relatório, sem segredo; a identidade do artefato é o sha256 ao lado.

## F. Conclusão

- **PROVEN:**
  - os 15 vereditos H1–H16 foram reproduzidos do artefato e ficam mais conservadores na régua nova;
  - nenhuma hipótese satisfaz a política v1;
  - o holdout prospectivo está selado e intocado;
  - nenhuma variante nova foi criada;
  - a suíte está verde no commit limpo.
- **DECLARED:**
  - os números dentro dos relatórios históricos (as séries de retorno estão no PC 1);
  - as janelas de teste de `trials.json` (a H11 diverge: o relatório diz 2018–2022 e o `trials.json`,
    2018–2026; usei 2018–2022);
  - N_upper = 150;
  - os status de H20, H21, H22, BIG_WINNER e RJ, que são os registrados no repositório.
- **UNKNOWN:** o N real de tentativas (limite inferior de 102); o desempenho de H17–H19; o conteúdo dos bancos do
  PC 1.
- **Limites de reprodutibilidade e de dados:**
  - A reexecução exata dos vereditos exige o banco do PC 1 (ajustes aprovados, fundamentos, ano de 2018). No PC 2,
    ela é NOT_REPRODUCIBLE.
  - O D do DSR vem do próprio DSR publicado. Para a H1, que não publicou DSR, usei momentos normais (aproximado).
  - A comparação com o CDI começa em 2019, porque a série baixada não cobre 2018; ela é indicativa para janelas
    que começam em 2018.
  - **Os COTAHIST de 2019 a 2025 (baixados e verificados) não foram usados aqui**, por três motivos:
    1. hipótese encerrada não pode ser reexecutada;
    2. H17–H19 dependem de dados da CVM e de desbloqueio humano;
    3. a reprodução exata depende do banco do PC 1.

    Os arquivos ficam disponíveis, com hash, para uma reabertura aprovada ou para hipóteses novas pré-registradas.
- **Nenhuma hipótese vira GO.**

## Próximo passo

- **Decisões do dono:**
  1. aprovar, ou ajustar, os limiares da política v1 (`PROPOSED_PENDING_OWNER_APPROVAL`);
  2. decidir se H17–H19 serão desbloqueadas, o que exige validar o dataset reconstruído do PC 1 e registrar a
     metodologia;
  3. qualquer reabertura de família encerrada exige os 6 campos da `reopen_policy`.
- **Hipóteses novas:** só com `preregister` antes do primeiro backtest e `dedup_check` contra os fatores
  existentes no período de desenvolvimento. O holdout selado só abre depois de 2027-09-10, com aprovação
  registrada.
- **Dado:** eventos societários com data de anúncio continuam sendo a maior lacuna para qualquer reavaliação
  executável.
