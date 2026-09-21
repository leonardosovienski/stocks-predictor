# EXTERNAL_INTELLIGENCE_V1 — implementation report

Report date: 2026-09-20. This report distinguishes code, observed source behavior, validation,
publication, and scientific/economic evidence. The QA database and raw evidence are outside Git at
`C:\STOCKS\work\external-intelligence-v1-qa`; failed attempts were retained beside successful runs.

## A. Baseline

| Item | Observed baseline |
|---|---|
| Initial branch | `main` |
| Initial SHA | `3f25895eeeaee9086c1f32f26ef1df920aeec79c` |
| Initial worktree | clean |
| Predictor Core | 3.2.1; `9bf43efe92459a0b484cac00f51170b2c70d420f` |
| Predictor Ops | 4.2.1; `b19e69527c0fda5cb1f96281d3a984fea1431768` |
| CAIN | 0.4.12; detached `24f784c5dde1fa66c262ad5899f4fd8d02526adf`; pre-existing dirty state |

The exact audit and frozen hashes are in `ARCHITECTURE_MAP.json` and
`BASELINE_PRESERVATION.json`. Core, Ops, CAIN, and the architecture registry were read-only.

## B. Architecture audit

| Component | Observed responsibility | Contract reused | Integration | Modified? |
|---|---|---|---|---|
| Predictor Core | shared infrastructure and publication contracts | `infra.connect`, `run_migrations`, SHA/content conventions, availability-aware replay | installed dependency/vendor only for auxiliary Windows checks | no |
| Stocks | B3/CVM domain authority, PIT and identity rules, collection, staging | package CLI and existing FCA temporal derivation | owns all new code/data contracts | yes |
| Predictor Ops | execute bounded non-interactive jobs | schema v2 `MARKET_COLLECTION`, command/cwd/timeout/artifact | compatible example only | no |
| CAIN | consume explicit publications and reason over admitted evidence | `ResearchSnapshotV1`/`ResearchBundleV1` boundary | no database access or code import | no |
| Ecosystem registry | canonical topology | seven-repository/ten-package registry observed | audit evidence only | no |

`ECOSYSTEM_AUDIT_STATUS = COMPLETE`.

## C. Implementation

| File | Purpose |
|---|---|
| `stocks_predictor/external_intelligence.py` | acquisition, raw/version storage, parsers, PIT/identity, receipts, verify/status |
| `stocks_predictor/operations.py` | adds the `external` CLI group |
| `tests/test_external_intelligence.py` | deterministic offline source/foundation/temporal/identity tests |
| `docs/external_intelligence/README.md` | architecture, contracts, runbook, limitations, rollback |
| `docs/external_intelligence/ops-job.example.json` | Predictor Ops v2 compatibility example |
| `docs/external_intelligence/ARCHITECTURE_MAP.json` | pre-change ecosystem audit |
| `docs/external_intelligence/BASELINE_PRESERVATION.json` | frozen V2 baseline/post-change hash evidence |
| `docs/external_intelligence/REPORT.md` | this factual handoff |

No feature adapter, ranking input, experiment, portfolio action, or automatic publication was added.

## D. Database

Three additive deterministic migrations create:

- `external_raw_objects`, `external_source_versions`, `external_security_links`;
- `external_observations`, `external_observation_securities`;
- `external_receipts`, `external_rejections`;
- indexes by source/period, company/as-of interval, and observation family/time;
- update/delete denial triggers for all evidence, version, identity, receipt, and rejection tables.

Foreign keys and checks enforce hash lengths, non-negative byte counts, interval order, receipt-before-
availability order, and declared PIT states. Raw files are immutable content-addressed objects. The
external database is not the managed COTAHIST/scientific database.

## E. Sources

| Source | Official endpoint/file pattern | Auth | Observed coverage/format | Version and PIT semantics | Current/historical limitation |
|---|---|---|---|---|---|
| B3 lending | `arquivos.b3.com.br/bdi/table/{table}/{date}/{date}/{page}/1000` | none | 2026-09-18; paginated JSON with exact column contracts | exact response-page hash; `PIT_STRICT` from HTTP Date | public BDI history/backfill not established; `HISTORICAL_BACKFILL_STATUS = INCOMPLETE` |
| CVM VLMO | `.../DOC/VLMO/DADOS/vlmo_cia_aberta_<year>.zip` | none | 2026 annual ZIP; document + detail CSV | annual exact ZIP hash; first-seen HTTP Date | source fields and reported granularity only; no inferred beneficial ownership |
| CVM buyback | `.../EVENTOS/RECOMPRA_ACOES/DADOS/cia_aberta_recompra_acoes.zip` | none | current historical ZIP; three CSVs | fetched-day logical version; first-seen HTTP Date | program data are not execution data; malformed intervals rejected |
| CVM IPE | `.../DOC/IPE/DADOS/ipe_cia_aberta_<year>.zip` | none | 2026 annual metadata CSV | protocol/version or explicit composite; first-seen HTTP Date | metadata only; semantic classification `NOT_IMPLEMENTED` |
| CVM FCA | `.../DOC/FCA/DADOS/fca_cia_aberta_<year>.zip` | none | 2026 identity rows | filing availability + trading interval | identity evidence only; no present-day ticker backfill |

All acquisitions are credential-free HTTPS. Current availability was observed live on 2026-09-20.
Earlier source dates do not establish historical first-seen availability.

## F. B3 lending

- Collection works end to end: official source → eight raw pages → SHA-256 → source versions →
  normalized observations → PIT/identity → receipt → verify/status.
- Latest observed period: 2026-09-18.
- Rows: 2,919 open-position + 4,698 loan-balance = 7,617.
- Example raw SHA-256: open page 1 `6119f2fd11fd5d4e56011529cc5c17ff25cd0f8f6c8229346274b5172d5f0dc3`;
  loan page 1 `a06bacd580e7ddc892b0a72e167f18919704d50496ceb49ca3948dffdddb08d3`.
- Direct ticker/ISIN identity is preserved. No subsequent session existed in the available read-only
  local price calendar, so live QA correctly left `tradable_session` null. Offline tests prove the
  first actual session after a weekend/holiday boundary.
- Historical backfill is incomplete and no lending feature is promoted.

## G. VLMO

The live 2026 annual file yielded 38,621 detail rows. Granularity is one reported management/security
movement row with document protocol/version and source row. Management group and related entity text
are preserved rather than reclassified. `available_at` is collector first-seen, not `Data_Referencia`
or movement date. Company/security resolution is only through already-available FCA intervals. No
scientific interpretation of holdings or transactions was performed.

## H. Buyback

The current structured file yielded 1,927 programs: 1,925 persisted and two invalid end-before-
deliberation rows retained as rejections. Program authorization quantities, intermediaries, state,
reason, and purpose are distinct from executed quantity/value, which remain `null`. The current ZIP
contains historical and recent programs, but its present fetch does not prove historical availability.

## I. IPE

The 2026 metadata file yielded 34,472 rows in final QA: 34,343 admitted document identities and 129
rejections (121 duplicate identities and eight references more than 50 years after collection).
Categories, type, species, subject, presentation, version, protocol,
and document link are preserved. Missing official protocols use a labeled deterministic metadata
composite. Document contents are not downloaded. Semantic classification is `NOT_IMPLEMENTED`.

## J. Data quality

| Dimension | Result |
|---|---|
| Engineering validity | offline contract tests pass; live acquisition and raw verification pass |
| Source completeness | complete only for the observed current files/pages; broad history is not certified |
| PIT strength | `PIT_STRICT` from collector first-seen onward; no reconstructed historical claim |
| Coverage | observed counts above; rejects and duplicates remain in denominators |

The fresh final QA verify observed 82,506 observations, 468 identity links, 132 rejections,
12 source versions, and zero hash/lineage issues. A subsequent live B3 replay read the same 7,617
rows and persisted zero, confirming idempotency against the exact response hashes.

## K. Ops

Real command shape:

```text
python -m stocks_predictor external collect b3-lending --db DB --raw-root RAW --receipt RECEIPT --reference-date 2026-09-18
```

`ops-job.example.json` conforms to the observed Predictor Ops schema v2 and includes
`MARKET_COLLECTION`, economic key, command, cwd, timeout, heartbeat, output limit, runtime,
provenance, and expected receipt. Ops was not modified. `SCHEDULING = NOT ACTIVATED`.

## L. CAIN/publication

Existing `ResearchSnapshotV1`/`ResearchBundleV1` producer-consumer boundaries were reused as the
future publication route; no external-intelligence export was activated. A future bundle must include
source-version IDs, raw hashes, PIT/identity states, and rejection counts. Stocks does not import CAIN.
CAIN does not access the Stocks database. No CAIN file or configuration was changed.

## M. Tests

| Suite | Passed | Failed | Skipped | Environment |
|---|---:|---:|---:|---|
| `unittest tests.test_external_intelligence` | 11 | 0 | 0 | auxiliary Windows Python 3.12 + read-only vendored Core |
| live official collection | 5 | 0 | 0 | isolated QA database under `C:\STOCKS\work` |
| `external verify` | 1 | 0 | 0 | isolated QA database/raw tree |
| focused external/V2 preservation tests | pass | 0 | 0 | Linux Python 3.13 and 3.14, diagnostic run `35554715248` |
| build, wheel smoke, coverage and secrets | pass | 0 | n/a | Linux Python 3.13/3.14; coverage 78%; diagnostic run `35554715248` |
| full pytest | 928 | 2 inherited | 65 subtests | each supported Linux runtime; failures reproduce from `main` |

Normal unit tests are offline. The Windows host has no permitted project venv/pytest installation;
that limitation is recorded rather than represented as a pass. The isolated diagnostic workflow
completed successfully in both supported runtimes and its `secrets` job passed. The ordinary workflow
remains red for inherited baseline defects: three Ruff unused imports in frozen/existing files, one
Pyright error in `prospective_big_winner.py`, the historical R8 code-population receipt, and a
platform-dependent historical manifest hash test. The same ordinary failures are present on baseline
run `35483073771`; they are not reclassified as implementation regressions.

## N. Baseline preservation

The seven frozen BIG_WINNER_V2/config/ledger raw hashes match the pre-change capture exactly, and
`git diff --name-only 3f25895e -- <seven frozen paths>` is empty. A portable LF-normalized comparison
also passes on Linux Python 3.13 and 3.14; the SQLite ledger remains byte-for-byte raw hashed. No
frozen file is in any implementation commit, and the new module has no automatic import into factors
or BIG_WINNER pipelines. `BIG_WINNER_V2_PRESERVATION_STATUS = PASS_UNCHANGED`.

## O. Git

Logical commits currently include:

- `d23881e` — ecosystem/frozen baseline audit;
- `ec1862f` — immutable PIT staging, collectors, CLI, and initial tests;
- `d89c5e0` — live-collector hardening and operational documentation;
- `295cc60` — paginated collector typing correction;
- `bf8d2c3` — exact frozen-ledger false-positive classification for secret scanning;
- `bb2e999`, `cffff02` — portable frozen-V2 preservation tests.

Candidate branch `external-intelligence-v1` was pushed through validated code SHA `cffff02`. The
separate evidence-only branch `external-intelligence-v1-ci-validation` passed diagnostic Linux run
`35554715248`; its continue-on-error treatment of inherited checks is not part of the candidate.
Because the ordinary repository gates remain red on defects reproduced from `main`, the candidate was
not integrated into or pushed as `main`. `GIT_REMOTE_INTEGRATION_STATUS = BRANCH_PUSHED_MAIN_NOT_INTEGRATED`.

## P. Status matrix

| Status | Value |
|---|---|
| `ECOSYSTEM_AUDIT_STATUS` | `COMPLETE` |
| `ENGINEERING_IMPLEMENTATION_STATUS` | `IMPLEMENTED_QA_VALIDATED_BASELINE_CI_BLOCKED` |
| `DATA_FOUNDATION_STATUS` | `IMPLEMENTED_QA_VERIFIED` |
| `B3_LENDING_IMPLEMENTATION_STATUS` | `IMPLEMENTED_QA_VERIFIED` |
| `B3_LENDING_DATA_QUALITY_STATUS` | `OBSERVED_CURRENT_PERIOD_HISTORY_INCOMPLETE` |
| `B3_LENDING_PIT_STATUS` | `PIT_STRICT_FROM_FIRST_SEEN` |
| `VLMO_IMPLEMENTATION_STATUS` | `IMPLEMENTED_QA_VERIFIED` |
| `VLMO_DATA_QUALITY_STATUS` | `OBSERVED_CURRENT_FILE` |
| `VLMO_PIT_STATUS` | `PIT_STRICT_FROM_FIRST_SEEN` |
| `BUYBACK_IMPLEMENTATION_STATUS` | `IMPLEMENTED_QA_VERIFIED` |
| `BUYBACK_DATA_QUALITY_STATUS` | `OBSERVED_WITH_2_REJECTIONS` |
| `BUYBACK_PIT_STATUS` | `PIT_STRICT_FROM_FIRST_SEEN` |
| `IPE_METADATA_IMPLEMENTATION_STATUS` | `IMPLEMENTED_QA_VERIFIED` |
| `IPE_METADATA_DATA_QUALITY_STATUS` | `OBSERVED_WITH_129_REJECTIONS` |
| `IPE_METADATA_PIT_STATUS` | `PIT_STRICT_FROM_FIRST_SEEN` |
| `OPS_COMPATIBILITY_STATUS` | `IMPLEMENTED_NOT_SCHEDULED` |
| `RESEARCH_PUBLICATION_COMPATIBILITY_STATUS` | `COMPATIBLE_NOT_PUBLISHED` |
| `BIG_WINNER_V2_PRESERVATION_STATUS` | `PASS_UNCHANGED` |
| `GIT_REMOTE_INTEGRATION_STATUS` | `BRANCH_PUSHED_MAIN_NOT_INTEGRATED` |
| `SCIENTIFIC_EVIDENCE_STATUS` | `NOT_EVALUATED` |
| `ECONOMIC_EVIDENCE_STATUS` | `NOT_EVALUATED` |

## Q. Open issues

- P0: none known.
- P1 in implementation scope: none known after live QA and supported-runtime diagnostic validation.
- P1 integration blocker outside this increment: ordinary repository CI remains red on baseline Ruff,
  Pyright, historical R8 receipt, and platform-dependent manifest-hash defects reproduced from `main`.
- P2: public historical B3 lending backfill is incomplete; IPE contents/CDA are not collected.
- P3: expose a richer rejection summary and calendar coverage metric in a later compatible increment.
- External blockers: no credentials are needed; broad historical source availability is not supplied
  by this implementation and cannot be inferred from current files.

## R. Scientific status

`engineering complete` is not `predictive evidence` and is not `economic evidence`. No new scientific
trial, backtest, multiplicity decision, profitability estimate, portfolio action, or capital action was
executed. `SCIENTIFIC_EVIDENCE_STATUS = NOT_EVALUATED` and
`ECONOMIC_EVIDENCE_STATUS = NOT_EVALUATED`.

## S. Next step

First repair or explicitly rebaseline the inherited ordinary-CI defects in a separately authorized
maintenance increment, rerun the unmodified gate, and only then integrate the candidate into `main`.
After that engineering gate closes, the justified next research increment is CDA + Entrega + a
confidentiality/licensing audit, because IPE currently exposes metadata only. Do not promote V3 and do
not start a scientific trial automatically. A first preregistered external-intelligence trial is later,
after historical PIT coverage and a fixed selection/multiplicity budget exist.
