# ADDED Requirements

## Requirement: Same-sample fixed-label endpoint diagnostic

The CLI SHALL declare EXPLORE and consume only the accepted degree-admitted
DV3 constructor/deep endpoints and original192 mapped synthetic truths.
Each arm SHALL use its own syndrome and capture the actual decoder output.
No construction, label search, resampling or implicit production from tests.

### Scenario: Complete paired replay

- WHEN the frozen source and execution gates pass
- THEN one bounded384-call attempt reports exact/wrong/fail, paired and per-graph
  outcomes, accounting/resources and explicit same-sample claim ceiling.

### Scenario: Source or resource failure

- WHEN a frozen source check or budget fails
- THEN retain actual partial evidence and STOP without fallback or rerun,
  keeping full-performance totals null and awaiting independent review.
