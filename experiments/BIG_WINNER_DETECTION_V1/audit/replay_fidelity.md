# Replay fidelity audit

The repository intentionally separates corrected current code from frozen legacy
reproduction. `backtest.walk_forward` routes to the causal v3 simulator, while the
historical runners explicitly call `legacy_walk_forward`. Replacing one with the
other changes execution, holdings, events and potentially rankings/outcomes; it is
not a cosmetic bug fix.

- Price-only detector formulas and their directions remain reconstructible.
- Strict PIT use of legacy fixed-embargo fundamentals is not established.
- The corrected CVM versioned derivations are not automatically exact replays of
  the historical mechanisms.
- H17-H19 discovery repairs and reorganization handling are separate observations;
  they cannot be backported and called the original detector.
- No historical system aggregator exists.

Any future activation must attach detector-specific equivalence tests before using
`SEMANTICALLY_EQUIVALENT_REPLAY`. Otherwise it remains `MODIFIED_REPLAY` and outside
the primary confirmatory endpoint.
