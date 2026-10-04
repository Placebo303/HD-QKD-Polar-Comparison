# Archive disposition: formal-ir-v72p2d4-cal-gf32-model-rate-audit

- Date: 2026-10-04
- Disposition: completed
- Evidence state: implementation_independently_reviewed; descriptive_results_unreviewed_for_result_acceptance
- Source evidence: docs/research_cycles/V72P2D4-CAL-RATE/IMPLEMENTATION_REVIEW.md:L1-L35 and IMPLEMENTATION_REVIEW_R2.md:L1-L36 record R1/R2 independent implementation acceptance; RESULT_SUMMARY.md:L1-L35 and RESULT_SUMMARY_R2.md:L1-L35 record descriptive CAL-only outputs and no decoder/promotion; ATTEMPT_0_INVALID.md:L1-L38 excludes the invalid attempt.
- Known review/execution state: R1/R2 implementation reviews independently accept the implementation; the corresponding result summaries are descriptive and explicitly state decoder_executed=false and scientific_promotion=false. No separate Pre-RESULT/result-review receipt was found, so result interpretation is not included in the completed scope.
- Frozen merge boundary: Implementation-only audited CAL-only model/rate code and guards: S-COMMON, S-COUNTS, S-MODEL, S-METRIC, S-REPRO, S-SELECT, S-BUDGET, S-ROUTE, and S-STOP as covered by R1/R2 implementation reviews. Do not merge or promote the R1/R2 result interpretation; exclude decoder, qualification, and route claims.
- Next action from frozen table: Archive the reviewed implementation clauses only; preserve descriptive result summaries as historical records without merging result claims.
- Ambiguity or unknown retained: An invalid Attempt-0 remains non-evidence. R1/R2 results were run and summarized, but the located review records accept implementation only; the result claims remain outside this scope.
- Exact-title merge outcome is recorded during phase B; this phase-A record preserves the frozen scope only and grants no new execution, qualification, or route acceptance.

## Original tracked files
- openspec/changes/formal-ir-v72p2d4-cal-gf32-model-rate-audit/design.md
- openspec/changes/formal-ir-v72p2d4-cal-gf32-model-rate-audit/proposal.md
- openspec/changes/formal-ir-v72p2d4-cal-gf32-model-rate-audit/specs/spec.md
- openspec/changes/formal-ir-v72p2d4-cal-gf32-model-rate-audit/tasks.md

## Phase-B delta disposition

Title-level consolidation is recorded in `openspec/changes/reboot-repository-organization-20261004/S6_DELTA_MERGE.tsv` under change key `formal-ir-v72p2d4-cal-gf32-model-rate-audit`. Included titles: 9; remaining listed titles are omitted or already equivalent, with the specific reason retained in that ledger. This resolves the earlier pending-merge filing snapshot; current AGENTS and reboot R1–R9 govern. Filing/consolidation confers no new scientific acceptance or execution authorization.
