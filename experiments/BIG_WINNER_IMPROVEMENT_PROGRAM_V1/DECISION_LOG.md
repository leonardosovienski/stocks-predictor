# Decision log

## 2026-09-19 — V2 selection

Evidence: V1_PRICE frozen scorecard, overlap, trajectories and annual blocks. Alternatives: M6, Reversal, ensembles, regime/sector conditioning, no candidate. Chosen: unchanged M12 top-20% baseline. Reason: clearest mechanism, lowest dependency/leakage surface and strongest—not conclusive—historical signal. Scientific consequence: candidate is unvalidated and only future post-freeze decisions can confirm it. Implementation: selection freeze, deterministic scorer, ledger and shadow pipeline.

## 2026-09-19 — historical repair

Decision: do not modify duplicated V1_PRICE episode files. Preserve hashes and produce a corrected, separately identified derivation. Consequence: historical integrity remains auditable.
