# Coverage audit

No detector-level coverage percentage is reported because no real signal panel was
frozen. A denominator calculated before resolving source availability would give a
false appearance of eligibility.

Known source-level coverage:

- original recovered database: 2,647 distinct trading dates, 2016-01-04 through
  2026-08-27; 1,149,872 raw price rows; 1,784 tickers;
- 43 approved adjustment rows for 36 tickers;
- 1,579 legacy fundamental rows for 127 tickers;
- 2,227 quarantine rows for 799 tickers;
- later research version: 95 cash events for four tickers only;
- latest evidence review: 50 net values, 22 payment dates, 28 corporate records
  and 1,248 intervals remain uncertified.

Required future output by detector/year remains: expected asofs, available asofs,
scorable and unscorable ticker-asofs, estimable and non-estimable outcomes, and
coverage rate with explicit exclusion reasons.
