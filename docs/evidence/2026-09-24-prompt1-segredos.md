# Prompt 1 — Gate de segurança dos segredos (stocks-predictor) — 2026-09-24

Escopo: histórico Git completo do `stocks-predictor` (espelho `--mirror` de `github.com/leonardosovienski/stocks-predictor`
em 2026-09-24T16:37Z: 100 refs = `main` `36081a6` + 96 `refs/pull/*/head` + 3 tags; **488 commits**, todos alcançáveis
pelo `main`), árvore de `main`, CI e controles preventivos. Nenhum código do repositório foi executado, nenhum `.env`
foi carregado, nenhuma API de broker ou de dados foi chamada, nenhum segredo foi verificado contra provedor. Nenhum
valor secreto aparece neste documento (valores longos mascarados na análise; gitleaks com `--redact`; trufflehog com
`--no-verification` e os campos brutos descartados antes de gravar).

Convenções: **PROVEN** = constatado nesta sessão (comando, arquivo, commit); **DECLARED** = descrito em documento, não
comprovado aqui; **UNKNOWN** = indeterminado.

## A. Gate

**SECRET_ROTATION_GATE = CLEARED**

- Nenhum segredo no histórico: gitleaks e trufflehog no histórico inteiro deram 23 candidatos, **0 credencial**. São
  16 falsos positivos comprovados por recomputação ou por serem vetores sintéticos, e 7 falsos positivos por contexto:
  digests de manifesto que apontam para arquivos não versionados (seção C).
- Nenhuma credencial compartilhada com o incidente do cripto: **PROVEN**. Nenhuma das 5 classes do incidente aparece
  em nenhum dos 488 commits, e o stocks não usa credencial nenhuma (seção B).
- Não existe `docs/evidence/secret-rotation-attestation.md` neste repositório; não é necessária pelo critério acima.
  Remover do Git não é rotação; nada foi removido.

## B. Evidências de bloqueio ou incidente

| Item | Estado | Evidência |
|---|---|---|
| Marca `BLOCKED_PENDING_SECRET_ROTATION`, doc de incidente ou de rotação neste repo | ausente — PROVEN | `git grep` em `main` |
| Commits sobre controle de segredos | PROVEN | `c4e9819` (trava de credenciais no vendor), `2c188e0` e `36f83dc` (guard de segredos na telemetria), `e67d244` (gitleaks-action v3), `4398262` (escopo das exceções do scanner e prova de detecção) |
| Incidente do cripto | DECLARED | `cripto-predictor@174573d:docs/SECURITY_INCIDENT_SERPAPI.md`: 5 classes — `GEMINI_API_KEY`, `SERP_API_KEY`, `GROQ_API_KEY`, `CEREBRAS_API_KEY`, `MISTRAL_API_KEY`; rotação confirmada verbalmente pelo dono em 2026-08-19; revogação das chaves antigas e checagem de uso indevido seguem como `EXTERNAL_BLOCKER` (`docs/ERRATA_2026-08-21.md` §2) |
| Atestação de rotação do cripto (`docs/evidence/secret-rotation-attestation.md`) | ausente no clone local `174573d` — PROVEN | `git ls-tree` |
| As 5 classes do cripto no stocks | nenhuma em nenhum dos 488 commits — PROVEN | `git grep -i <nome> $(git rev-list --all)`; "SerpAPI" só em docstring/comentário do Core vendorizado (`vendor/predictor_core/kernel/net.py:4,56`), descrevendo a camada do cripto |
| Credenciais usadas pelo stocks | nenhuma — PROVEN | o código só lê variáveis de caminho e controle (`DB_PATH_ENV`, `REPORTS_ENV`, `TRIALS_PATH_ENV`, `FAULT_ENV`, `EVENTS_ENV`); `require_secrets` nunca é chamado fora de `vendor/`; hosts só públicos e sem autenticação (dados.cvm.gov.br, arquivos.b3.com.br, bvmf.bmfbovespa.com.br, sistemaswebb3-listados.b3.com.br, www.b3.com.br, github.com); nenhum broker |

## C. Achados do scan (sem valores)

Ferramentas (instaladas em `~/predictors/tools/secscan`, checksum da release conferido): gitleaks 8.24.3 e
trufflehog 3.97.9.

| Varredura | Comando (resumo) | Resultado |
|---|---|---|
| gitleaks, config do repo | `gitleaks git <espelho> --log-opts="--all" --config .gitleaks.toml --redact` | 4 = exatamente as 4 impressões do `.gitleaksignore` (o espelho não tem diretório de trabalho, então o gitleaks não leu o ignore) |
| gitleaks, regras padrão sem allowlists | `gitleaks git <espelho> --log-opts="--all" --redact` | 13 |
| trufflehog | `trufflehog git file://<clone> --no-verification --json --no-update` | 10, todos `verified: false` |
| CI `secrets`, run 36003599626 (`workflow_dispatch` em `36081a6`) | gitleaks-action: `gitleaks detect --redact` + árvore rastreada + controle positivo | **375 commits varridos** (log do job, linha 162), "no leaks found"; árvore de 1899 arquivos sem achados; controle positivo detectou o token sintético (1 achado esperado) |
| gitleaks no repo de evidência, run 35986948802 | `4e98a67..61fc017` | sem achados |

Achados (ferramenta/regra · commit · arquivo:linha · tipo provável · estado atual no `main` · como foi resolvido):

| Ferramenta/regra | Commit | Arquivo:linha | Tipo provável | Estado | Veredito |
|---|---|---|---|---|---|
| gitleaks generic-api-key | `6fd9c9fbc2` | `experiments/BIG_WINNER_IMPROVEMENT_PROGRAM_V1/prospective/decision_artifacts/2025-07-31_c249ba216beeb81a.json:876` | sha256 lógico | presente | FP PROVEN: `logical_key` recomputado a partir de `signal_asof`, `model_identity`, `config_hash` e `dataset_hash` (`prospective_big_winner.py:69`) |
| gitleaks generic-api-key | `d57ffa65d8` | `docs/engineering/2026-09-10-r8/evidence.json:156` | digest de arquivo | presente | FP PROVEN: sha256 de `tests/test_secrets_telemetry.py` |
| gitleaks generic-api-key | `d57ffa65d8` | `docs/engineering/2026-09-10-r8/evidence.json:173` | digest de arquivo | presente | FP PROVEN: sha256 de `tools/explore_b3_dividends_api.py` |
| gitleaks generic-api-key | `93fa05f513`, `ec96f06183` | `research/session-20260907/deliverables/real-integration-delivery-manifest.json:886,894,950` | digest de arquivo | presente | FP PROVEN: sha256 de `tests/test_secrets_telemetry.py`, `tools/explore_b3_dividends_api.py`, `vendor/predictor_core/testing/secrets.py` |
| gitleaks generic-api-key | `3b5e8b1398` | `src/trials_gate.py:85` | import Python | removido | FP PROVEN: linha de import das constantes congeladas da H1/H2 do módulo `config` (sem valor; não reproduzida aqui para não disparar a mesma regra) |
| gitleaks generic-api-key | `36f83dc9fe` | `vendor/predictor_core/CORE_MANIFEST.json:11` | digest de arquivo | removido | FP PROVEN: sha256 de `vendor/predictor_core/testing/secrets.py` em `36f83dc` |
| gitleaks generic-api-key | `c0efb360fe`, `10d4328ba2` | `vendor/predictor_core/CORE_MANIFEST.json:33` | digest de arquivo | presente | FP PROVEN: sha256 de `vendor/predictor_core/testing/secrets.py` |
| trufflehog URI | `ec1862f0d5` | `tests/test_external_intelligence.py:213` | URL com credencial | presente | FP PROVEN: vetor sintético `user:pass` do teste que exige a recusa de URL com credencial |
| trufflehog ProtocolsIO | `860996d20d` | `docs/open_source_research/OSS-20260911-01/closure/preservation-before.json:44`; `.../continuation-v3/delivery-manifest.json:9` | digest de arquivo | presente | FP PROVEN: sha256 de `docs/open_source_research/OSS-20260911-01/continuation-v3/protocols.py` |
| trufflehog Parsers | `860996d20d` | `docs/open_source_research/OSS-20260911-01/{registry.json:1153, continuation-v2/registry.json:1297, second_wave.json:127}` | digest de manifesto | presente | FP por contexto (DECLARED): campo `sha256` de entrada `{path, url, bytes}` do arquivo externo `brasa/parsers/b3/__init__.py`, não versionado |
| trufflehog ProtocolsIO/Parsers | `aca772196a` | `research/session-20260909/publication/local/FONTES_WEB_ORIGINAIS/MANIFESTO_DEPENDENCIAS.json:2592,17082,33264,42390` | digest de manifesto | presente | FP por contexto (DECLARED): campo `sha256` de entradas `{path, original_path, size}` de `protocols.pyi` (typeshed) e `pygments/lexers/parsers.py`, não versionados |

Segredo real encontrado: **nenhum**. Nenhum valor foi exibido.

Exceções do scanner no repositório: `.gitleaks.toml` (5 allowlists) e `.gitleaksignore` (4 impressões). As 13
ocorrências do histórico cobertas por elas (4 pelo ignore, 9 pelas allowlists) foram recomputadas acima (PROVEN). A
allowlist do digest da observação H18/H19 não casa nenhum achado no histórico (sem efeito observado).

## D. Controles preventivos

| Controle | Existe? | Status | Evidência |
|---|---|---|---|
| `.env` no `.gitignore` | não | PROVEN | `.gitignore` sem padrões de env, secret, key, cred, token ou pem |
| `.env.example` | não | PROVEN | `git ls-tree` |
| Pre-commit de secret scanning | não | PROVEN | sem `.pre-commit-config.yaml`; hooks só de exemplo |
| Secret scanning no CI, histórico inteiro | sim, funcionando | PROVEN | `.github/workflows/ci.yml:129-170`; run 36003599626: 375 commits, árvore de 1899 arquivos, controle positivo |
| Exceções do scanner documentadas e estreitas | sim | PROVEN | as 13 ocorrências cobertas por exceções foram recomputadas |
| Guard de segredos na telemetria | sim, funcionando | PROVEN | `tests/test_secrets_telemetry.py`; suíte de 2026-09-24 com 1049 passed (predictor-qualification run 36003615207) |
| URL com credencial recusada | sim, funcionando | PROVEN | `stocks_predictor/external_intelligence.py:415-417`, `stocks_predictor/operational_store.py:121`; `tests/test_external_intelligence.py` na suíte verde |
| Trava contra placeholders (`require_secrets`) | só no vendor, sem uso | PROVEN | `vendor/predictor_core/kernel/settings.py:38` |
| Documentação de rotação | não | PROVEN | nenhum arquivo |

## E. Ações humanas

1. **Stocks:** nenhuma credencial a rotacionar ou revogar; nenhuma classe de credencial em uso.
2. **Cripto (fora deste repo):** confirmar no painel de cada provedor a revogação das 5 chaves antigas
   (`GEMINI_API_KEY`, `SERP_API_KEY`, `GROQ_API_KEY`, `CEREBRAS_API_KEY`, `MISTRAL_API_KEY`) e a ausência de uso
   indevido; registrar em `docs/evidence/secret-rotation-attestation.md` do cripto. Remover do Git não é rotação.
3. **Preventivo (recomendado, não feito aqui):** `.env` e `*.env` no `.gitignore` antes de qualquer credencial entrar
   no projeto; hook de pre-commit com gitleaks.

## Próximo passo

- O Prompt 2 pode assumir como **PROVEN**:
  - gate CLEARED;
  - o stocks não usa credencial nem broker e só acessa endpoints públicos da B3 e da CVM;
  - o histórico completo (488 commits, todas as refs) não tem segredo;
  - o CI de segredos varre o histórico inteiro e tem controle positivo.
- **DECLARED:** o estado do incidente do cripto (revogação e uso indevido, externo) e 7 falsos positivos por contexto
  (digests de arquivos não versionados).
- **UNKNOWN:** nada que bloqueie o Prompt 2.
