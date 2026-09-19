# Data contract and coverage gate

## Audited datasets

| Dataset id | Source/version | Coverage | PIT safe for signals | Outcome safe | SHA-256 |
|---|---|---|---|---|---|
| `ORIGINAL_PROJECT_DB` | recovered immutable original `project/data/stocks.db` | prices 2016-01-04..2026-08-27; 1,149,872 rows; 1,784 tickers | NO — source publication/ingestion availability and action/mapping lineage incomplete | NO | `a22739794ba4a43a11544338d4a91e14cb6a0b1f7b132ab460f96d3359f63cf4` |
| `HISTORY_2016_2026` | preserved research version | same price range; 95 cash events/4 tickers | NO — reconstructed research version | NO — cash coverage is not universe-complete | `e21a89c38f2792c826291baa1175da4fe9dfbf626316635a536f7c28b250146a` |
| `CATALOG_R2` | local 12-database catalog | preservation metadata | metadata only | metadata only | recorded at execution receipt |

All database access during audit is read-only. No original receives migrations,
ingestion, reconciliation or inferred values.

## Required fields

Every activated dataset must record source, source version, coverage, observation
date, publication time/date, conservative `available_at`, ingestion time, revision
and restatement policy, corporate-action policy, ticker mapping, currency, units,
PIT status and content hash. Date-only publication becomes available on the first
subsequent trading session.

The preserved price rows provide observation dates but not a complete per-row
historical `published_at`, `available_at`, revision and mapping lineage. Legacy
fundamentals mix reference date, estimated embargo and later observed receipt paths.
The missing fields cannot be inferred in favor of eligibility.

## Outcome gate

The label requires total return from next-open execution to the last valid session
on or before 12 calendar months, including cash/stock events and economically valid
settlement for delisting, merger, acquisition, liquidation or reorganization.
Using the last quote before disappearance is prohibited. The currently certified
coverage is insufficient, so unresolved cases cannot be silently excluded or
treated as losses/zeros.

Decision: `PIT_SAFE = NO` and `OUTCOME_COMPLETE = NO` for the available real panel.
The correct status is `INCONCLUSIVE_DATA_QUALITY`, not a numeric detector verdict.
