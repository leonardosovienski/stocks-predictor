# BIG_WINNER_DETECTION_V2 design

Identifier: `BIG_WINNER_V2_MOMENTUM_12_1_BASELINE`.

Decision: `NO_DEFENSIBLE_V2_PREDICTIVE_CHANGE`. The prospectively evaluated candidate is the unchanged M12 baseline: adjusted price return from session -252 to -21, higher is better, deterministic top 20% (`ceil`) with ticker ascending tie-break, universe top 60 by 126-session median traded value and minimum 252-session history, next-open execution.

This is chosen for mechanism, simplicity, PIT feasibility and low leakage surface—not because of a post-hoc V2 backtest. Status is always `UNVALIDATED_PROSPECTIVE_CANDIDATE` until mature future evidence exists.

Primary endpoint: lift over PIT base rate, with precision, recall, selection fraction and early-hit recall jointly reported. Promotion requires at least 24 mature monthly cohorts, lift lower 95% bound >1, lift point estimate >=1.15, early-hit recall >=0.15, selection fraction <=0.20, no leakage/data-integrity failure and positive results in both halves. Kill if after 24 mature cohorts lift point estimate <=1, upper 95% bound <1.15, operational integrity fails, or outcome coverage falls below 80%.
