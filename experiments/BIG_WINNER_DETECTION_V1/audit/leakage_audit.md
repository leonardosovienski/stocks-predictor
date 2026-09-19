# Adversarial leakage audit

## Mechanical defenses implemented

- Separate modules for signal generation, freeze, outcome generation and evaluation.
- Signal input path denylist for outcomes, labels, episodes, peaks, drawdowns and cards.
- AST dependency test prevents signal code importing outcome/evaluation modules.
- Every signal input requires `available_at <= signal_asof`.
- Date-only publications are delayed to the next trading session.
- Execution is strictly the next eligible open.
- Missing scores remain non-scorable and cannot become zero/median.
- Deterministic top 20% selection uses score then ticker ascending.
- Freeze manifest validates file hash, row count and its own canonical payload.
- Outcome loading fails unless `FREEZE_VALID = TRUE`.
- Synthetic future-feature positive control is detected and rejected.
- Negative score permutation preserves detector/asof selection size.

## Real-data findings

| Threat | Status |
|---|---|
| Future prices / same-close execution | guarded in implementation; real run not started |
| Publication timestamps / restatements | FAIL_CLOSED: incomplete legacy lineage |
| Ticker mappings / reorganizations / delistings | FAIL_CLOSED: not universe-complete |
| Corporate actions | FAIL_CLOSED: cash and stock outcome coverage incomplete |
| Survivorship/current universe | historical raw data includes delisted observations, but identity/event proof remains incomplete |
| Global normalization/preprocessing | no new normalization or fitted estimator in V1 |
| Retrospective direction/threshold | fixed in detector registry and protocol before outcomes |
| Winner access before freeze | no real winner list/return loaded or generated |
| Outcome-aware exclusions | forbidden; unresolved outcomes must remain counted as non-estimable |

Overall: `LEAKAGE_AUDIT = NOT_PASSED_FOR_REAL_DATA`. This is a stop condition,
not evidence against or for any detector.
