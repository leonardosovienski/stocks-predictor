# BIG_WINNER_DETECTION_V1

Retrospective, falsification-first protocol for the pre-existing Stocks Predictor
mechanisms. This experiment is isolated from H1-H22 and does not alter any prior
trial, verdict, ledger, protocol, database, or prospective observation.

## Current state

`BLOCKED_BEFORE_REAL_SIGNAL_FREEZE`.

The implementation and synthetic contract tests exist, but no real label or result
has been generated. The preserved databases do not establish all `available_at`
fields needed by the absolute PIT contract, and no available database certifies
complete total-return/corporate-action outcomes for the B3 universe. Under the
pre-registered stop conditions, numbers derived by filling those gaps would be
invalid evidence.

Run the stdlib contract suite with the Codex-provided auxiliary Python:

```text
python -m unittest discover experiments/BIG_WINNER_DETECTION_V1/tests -v
```

The real sequence remains: resolve the gates in `audit/data_contract.md`; generate
all eligible detector rankings; freeze once with `lib/freeze.py`; verify the freeze;
only then run `lib/outcome_stage.py` and `lib/evaluation_stage.py`.

## Boundaries

- No new model, ensemble, weight optimization, supervised learning, or threshold search.
- No system-level result unless a pre-existing deterministic PIT aggregator is proven.
- `TRUE_PROSPECTIVE_EVIDENCE = NOT_AVAILABLE`.
- This experiment cannot prove future alpha, profit, suitability, or capital readiness.
