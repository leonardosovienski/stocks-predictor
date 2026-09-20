# Repair log

## REPAIR-001

- Problem: detailed episode artifacts were emitted with the last loop value.
- Evidence: all seven historical JSONs have identical class counts, while frozen scorecard summaries differ.
- Root cause: output writes occurred after the detector loop and reused `episode_results`.
- Affected module: V1_PRICE evaluation artifact writer.
- Scientific impact: detailed cards/miss lists mislabeled; primary scorecard metrics unaffected.
- Patch: preserve originals; new post-mortem builder recomputes detector-specific rows.
- Tests: cross-check reconstructed counts against frozen scorecard.
- Before: seven duplicated detailed outputs.
- After: new `analysis/hit_miss_map.csv` has detector-specific counts.
- Outcome-dependent? NO (repair restores intended mapping; no selection change).
- Changes detector semantics? NO.
- Commit SHA: recorded by final Git history.
- Final status: COMPLETE.

## REPAIR-002

- Problem: no immutable prospective evidence boundary.
- Patch: append-only hash-chained ledger, freeze verification and backfill exclusion.
- Outcome-dependent? NO. Changes detector semantics? NO.
- Final status: COMPLETE.

## REPAIR-003

- Problem: first real shadow invocation could not import the repository package from `tools/` and depended on unavailable `predictor_core` for universe construction.
- Evidence: `ModuleNotFoundError`; recorded during clean auxiliary-runtime execution.
- Root cause: missing repository path bootstrap and unnecessary runtime dependency.
- Patch: explicit repository import root and stdlib-equivalent strict PIT universe implementation.
- Tests: real database shadow run plus unit suite.
- Outcome-dependent? NO. Changes detector semantics? NO.
- Final status: COMPLETE; final freeze superseded explicitly.

## REPAIR-004

- Problem: an idempotent retry changed receipt status from `APPENDED` to `IDEMPOTENT_EXISTING`, making the immutable artifact bytes differ.
- Evidence: second real shadow run raised `FileExistsError`.
- Root cause: attempt status was embedded in permanent artifact receipt.
- Patch: persist only stable logical key, event hash and eligibility; return attempt status separately.
- Tests: real double-run and regression test.
- Outcome-dependent? NO. Changes detector semantics? NO.
- Final status: COMPLETE; prior freeze hash preserved and explicitly superseded.
