# Detector registry — frozen before outcomes

`NOT_SUPPORTED` is retained as historical scientific status and does not by itself
prevent replay. Eligibility below is stricter: the mechanism also needs a faithful
rule and PIT-safe required inputs.

| Detector | Historical identity | Direction | Historical status | Replay fidelity | V1 eligibility |
|---|---|---|---|---|---|
| `DETECTOR_MOMENTUM_12_1` | H1, adjusted return 252-to-21 | higher | NOT_SUPPORTED / power-limited | exact algorithm exists | BLOCKED_PIT_ACTION_AVAILABILITY |
| `DETECTOR_LOW_VOL_252` | H2, realized vol 252 | lower | NOT_SUPPORTED | exact algorithm exists | BLOCKED_PIT_ACTION_AVAILABILITY |
| `DETECTOR_REVERSAL_21` | H5, 21-day return | lower | NOT_SUPPORTED, historical anti-signal | exact algorithm exists | BLOCKED_PIT_ACTION_AVAILABILITY |
| `DETECTOR_MOMENTUM_6_1` | H6, adjusted return 126-to-21 | higher | NOT_SUPPORTED | exact algorithm exists | BLOCKED_PIT_ACTION_AVAILABILITY |
| `DETECTOR_MOMENTUM_LOW_VOL` | H8, top 40% momentum then lower half vol | historical two-stage rule | NOT_SUPPORTED; limited positive point estimate | exact rule exists | BLOCKED_PIT_ACTION_AVAILABILITY |
| `DETECTOR_ROE` | H7 | higher | NOT_SUPPORTED / INCONCLUSIVE_DATA_QUALITY | legacy replay uses estimated embargo | NOT_REPLAYABLE_STRICT_PIT |
| `DETECTOR_LEVERAGE` | H9 | lower | NOT_SUPPORTED / INCONCLUSIVE_DATA_QUALITY | legacy replay uses estimated embargo | NOT_REPLAYABLE_STRICT_PIT |
| `DETECTOR_ROE_LEVERAGE` | H10, top 40% ROE then lower half leverage | historical two-stage rule | NOT_SUPPORTED / INCONCLUSIVE_DATA_QUALITY | estimated embargo | NOT_REPLAYABLE_STRICT_PIT |
| `DETECTOR_MOMENTUM_TOTAL_RETURN` | H11 | higher | NOT_SUPPORTED; apparent positive limited | approximate dividend source | NOT_REPLAYABLE_TOTAL_RETURN_INCOMPLETE |
| `DETECTOR_NET_MARGIN` | H12 | higher | NOT_SUPPORTED / INCONCLUSIVE_DATA_QUALITY | estimated embargo | NOT_REPLAYABLE_STRICT_PIT |
| `DETECTOR_REVENUE_GROWTH` | H13 | higher | NOT_SUPPORTED / INCONCLUSIVE_DATA_QUALITY | estimated embargo | NOT_REPLAYABLE_STRICT_PIT |
| `DETECTOR_52W_HIGH` | H14 | higher | NOT_SUPPORTED; limited positive point estimate | exact algorithm exists | BLOCKED_PIT_ACTION_AVAILABILITY |
| `DETECTOR_VOLUME_SURGE` | H15, mean volume 21/252 minus one | higher | NOT_SUPPORTED | exact raw-volume algorithm exists | BLOCKED_DATASET_AVAILABLE_AT_PROOF |
| `DETECTOR_ACCRUALS` | H17 | lower | INCONCLUSIVE_DATA_QUALITY | corrected discovery differs from frozen legacy path | MODIFIED_REPLAY_ONLY |
| `DETECTOR_EARNINGS_YIELD` | H18 | higher | DISCOVERY_NO_PRIORITY_UPGRADE | corrected versioned derivation exists | MODIFIED_REPLAY_ONLY |
| `DETECTOR_BOOK_TO_MARKET` | H19 | higher | DISCOVERY_NO_PRIORITY_UPGRADE | corrected versioned derivation exists | MODIFIED_REPLAY_ONLY |

H3 was never executed or defined as an eligible frozen mechanism. H4 is position
sizing over the full universe and does not select winners. H16 is turn-of-month
timing. H20 is construction/buffering. H21 and H22 are market/ETF decisions. None
enters the confirmatory detector family.

No detector is removed because of a negative result. No detector is admitted from
an outcome observed in this experiment. The primary multiplicity family will be all
and only detectors whose blocked eligibility is later resolved before signal freeze.
