# System contract — pre-outcome freeze

This contract was written before any real winner label was constructed. The source
state is commit `9363ce242cb8e732b7c5222dd09b0d0715b323b9` on the dedicated experiment
branch. Existing scientific files and external databases remain unchanged.

## Engines

- Valid current execution engine: `stocks_predictor.simulation`, version
  `stocks-causal-execution-v3`, reached by `backtest.walk_forward`.
- Historical replay engine: `backtest.legacy_walk_forward`. It uses closing-price
  returns, historical/latest quarantine reconstruction, implicit daily equal-weight
  behavior and asymmetric benchmark treatment. It can document historical
  semantics but is not a valid current causal outcome engine.
- Current signal-side universe: `universe.select_universe`, with dates strictly
  before `asof` and temporally guarded quarantine resolution.
- Historical signal-side universe: `universe.legacy_select_universe`; use would
  require explicit `EXACT_REPLAY` labeling and cannot assert strict PIT.

## Historical universe and execution

The original registered universe is top 60 issuer roots by median financial volume
over 126 trading sessions before `signal_asof`, minimum 252 historical sessions,
spot market only, one four-letter issuer prefix retained, with quarantine exclusion.
Signals are monthly at the last trading close. The V1 execution contract is the
first eligible next open strictly after the signal; the 12-month outcome starts at
that execution. Same-close execution is forbidden.

The four-letter prefix rule is only a historical heuristic, not a certified
CNPJ/ISIN mapping. Until mappings, reorganizations, suspensions, delistings and
settlements are temporally resolved, affected observations are not scorable or have
non-estimable outcomes.

## Detector identity

The registry is in `detector_registry.md`. H4 is sizing, H16 is market timing, H20
is portfolio construction, and H21/H22 are ETF/market rules rather than individual
cross-sectional detectors. They are not silently recast as winner detectors.

No pre-existing deterministic PIT system-level aggregator was demonstrated.

```text
SYSTEM_LEVEL = NOT_DEFINED
```

## PIT sources

Potentially admissible only after dataset-level proof:

- COTAHIST spot OHLC/volume observations, restricted to dates available by the
  signal and an immutable identified source version;
- CVM filings using actual receipt/publication availability, never reference date
  alone or a retrospectively chosen fixed embargo;
- corporate actions whose signal-side availability is proven no later than the
  signal.

Current non-PIT/insufficient sources include legacy fundamentals with fixed 90-day
embargo, current-state ticker identity, future resolution of quarantine, and any
corporate-action reconstruction without contemporaneous `available_at`.

## Missing data

`UNIVERSE_ELIGIBLE` and `DETECTOR_SCORABLE` are separate. Missing/invalid input is
never zero, neutral, median, or a miss. Only the enumerated `NOT_SCORABLE_*` states
are accepted. The primary population is the detector-specific scorable population.

## Known limitations and gate

The external catalog marks every preserved database
`economic_completeness_certified=false`. The most complete original price database
has 1,149,872 price rows from 2016-01-04 through 2026-08-27, 1,784 tickers, 43
adjustments, 1,579 legacy fundamental rows, and 2,227 quarantine rows. A later
preserved research version has only 95 cash events for four tickers. The latest
audit still records 50 uncertified net cash values, 22 missing payment dates, 28
pending corporate records and 1,248 uncertified intervals.

Therefore real signal freeze and all real outcomes are blocked until temporal
source availability and complete corporate-action/terminal economics are proved.
