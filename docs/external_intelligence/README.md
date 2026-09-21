# EXTERNAL_INTELLIGENCE_V1

`EXTERNAL_INTELLIGENCE_V1` is a research-only, append-only staging boundary for official B3 and
CVM data. It does not feed factors, rankings, portfolios, paper trading, or BIG_WINNER_V2. Its
scientific and economic states are `NOT_EVALUATED`.

## Architecture and ownership

Stocks owns source-specific acquisition, parsing, identity, and temporal semantics. Predictor Core
provides the SQLite connection and deterministic migration runner. Predictor Ops may execute the
non-interactive CLI with its existing `MARKET_COLLECTION` job contract. CAIN may consume a future
explicit `ResearchSnapshotV1` or `ResearchBundleV1`; it does not read this database and Stocks does
not import CAIN.

The database is deliberately separate from the managed COTAHIST/scientific database. Tables are
prefixed `external_`; raw bytes live outside SQLite under `sha256/<prefix>/<digest>`. Immutable
triggers prohibit update/delete of raw registrations, versions, observations, security links,
receipts, and rejected rows.

## Source contracts

| Family | Official contract | Normalized scope | Identity |
|---|---|---|---|
| B3 lending | BDI `BTBLendingOpenPosition` and `BTBLoanBalance` JSON tables | Open positions and loan balances/rates | Direct ticker + ISIN |
| CVM VLMO | Annual `vlmo_cia_aberta_<year>.zip` | Management/security movements | CNPJ; temporal security link when FCA evidence exists |
| CVM buyback | `cia_aberta_recompra_acoes.zip` | Program, quantities, intermediaries; executed quantity/value remain unknown | CNPJ; temporal security link when FCA evidence exists |
| CVM IPE | Annual `ipe_cia_aberta_<year>.zip` | Metadata and document reference only | CVM protocol/version, or an explicit official-metadata composite when protocol is absent |
| CVM FCA | Annual FCA ZIP | Temporal CNPJ-to-ticker intervals used only for identity | CNPJ + ticker + filing availability + trading interval |

Schema headers are exact contracts. A missing/extra/reordered field, malformed archive, incomplete
B3 pagination, or unpublished B3 response fails explicitly. HTTPS URLs containing credentials or
credential-like query parameters are rejected.

## Time and PIT policy

`available_at` and `first_seen_at` are the official HTTP `Date` observed by the collector. A source
date alone is not treated as proof of historical availability. Therefore the current acquisitions
are `PIT_STRICT` only from collector first-seen time onward; they do not reconstruct earlier PIT
knowledge. `received_at` must not exceed `available_at`.

`tradable_session` is the first actually observed B3 session strictly after the Sao Paulo local
collection date. It is `NULL` with reason `NO_SUBSEQUENT_OBSERVED_B3_SESSION` if a read-only
`prices_raw` calendar does not prove such a session. This is fail-closed and does not infer weekdays
or holidays. A future event/reference date is permitted, but an IPE reference more than 50 years
after collection is preserved as an immutable source rejection.

FCA security identity is admissible only on or after its filing availability and within its reported
trading interval. Company-level CVM rows remain unresolved when no admissible link exists; no current
ticker is backfilled into history.

## Version, raw, lineage, and rejection policy

Every source version identifies publisher, dataset, logical period, parser version, exact raw SHA-256,
byte length, URL, fetch time, and prior different version for the same logical period. Republishing
creates a new immutable version. Replaying identical bytes is idempotent. B3 responses are retained
page by page because the official endpoint is paginated; a partial page set rolls back the database.

Each observation references exactly one source version and stores its natural key, normalized payload,
PIT state, time fields, and identity state. Source-local invalid or duplicate rows are retained in
`external_rejections` and remain in receipt denominators. Parser/schema failures roll back the complete
collector transaction. Raw bytes written before a transaction failure may remain content-addressed
and unregistered; a later identical retry safely reuses them.

## CLI

All commands are non-interactive and emit JSON. Collection requires a separate external database,
raw root, and receipt path.

```text
python -m stocks_predictor external collect b3-lending --db C:\STOCKS\work\external.sqlite --raw-root C:\STOCKS\work\external-raw --receipt C:\STOCKS\work\receipts\b3.json --reference-date 2026-09-18
python -m stocks_predictor external collect cvm-vlmo --db DB --raw-root RAW --receipt RECEIPT --year 2026
python -m stocks_predictor external collect cvm-buyback --db DB --raw-root RAW --receipt RECEIPT
python -m stocks_predictor external collect cvm-ipe --db DB --raw-root RAW --receipt RECEIPT --year 2026
python -m stocks_predictor external collect cvm-fca-identity --db DB --raw-root RAW --receipt RECEIPT --year 2026
python -m stocks_predictor external verify --db DB --raw-root RAW --receipt RECEIPT
python -m stocks_predictor external status --db DB --receipt RECEIPT
```

For controlled offline replay, CVM collectors accept `--source-file` only with an explicit
`--observed-at` UTC timestamp. B3 needs two independently paginated official responses and therefore
does not accept a single source file. `--trading-db` is opened read-only and used only as an observed
session calendar.

## Operations, publication, and rollback

[`ops-job.example.json`](ops-job.example.json) uses Predictor Ops schema v2. It is compatibility
evidence, not an activated schedule: `SCHEDULING = NOT ACTIVATED`.

Existing `ResearchSnapshotV1` and `ResearchBundleV1` exports remain the publication boundary. This
mission does not publish external observations and does not change CAIN. A future exporter must carry
the source-version IDs, raw hashes, availability, PIT status, identity status, and rejection counts;
CAIN must never query the staging database.

Rollback is operational: stop the job and point future runs at a new external database/raw root.
Because evidence is immutable, do not delete or edit an applied version to “undo” it. The scientific
pipelines require no rollback because no import or automatic feature promotion exists.

Known limitations: public B3 history is limited by current BDI availability; broad historical PIT has
not been reconstructed; CVM files can contain anomalies/duplicates; IPE semantic classification is
`NOT_IMPLEMENTED`; buyback execution quantities/values are not inferred; no analyst consensus, paid
source, CDA/Entrega corpus, feature selection, backtest, or capital action is included.
