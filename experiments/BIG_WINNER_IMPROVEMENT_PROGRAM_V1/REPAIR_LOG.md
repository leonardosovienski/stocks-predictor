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
