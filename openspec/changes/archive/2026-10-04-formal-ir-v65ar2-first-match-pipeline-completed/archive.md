# Archive disposition: formal-ir-v65ar2-first-match-pipeline

- Date: 2026-10-04
- Disposition: completed
- Evidence state: implementation_independently_reviewed; pipeline_not_executed
- Source evidence: docs/research_cycles/V65AR2/PRE_EXECUTE_VERDICT.md:L1-L68 identifies the independent reviewer and reviewed implementation SHA, independent 15-test rerun, 20-test suite, and execution authorization boundary; specs/spec.md:§§2-11 define the implementation contract.
- Known review/execution state: Independent read-only code/scientific review PASS; historical record reports 15/15 independent rerun and 20/20 total tests. Verdict says no decoder invocation and no EXECUTE_AUTH; this supports implementation scope only.
- Frozen merge boundary: Implementation-only: frozen candidate/tier and processing point (§2); additive metadata Phase R (§3); first-match and UNREACHABLE state machine (§4, §9); materialization-only Stage0 and fake-tested Stage1 estimator/rate semantics (§5-6); TEST identity-only/report guards (§7-8); decoder-free, additive no-overwrite, and run_01 guards (§10-11). Exclude raw production execution, Stage2/TEST32 result claims, qualification, and promotion.
- Next action from frozen table: Archive reviewed implementation clauses only; exclude production pipeline results and all decoder/qualification clauses.
- Ambiguity or unknown retained: Old implementation 3a6c4fa is explicitly ENGINEERING_INVALID and excluded. The accepted implementation SHA is ffe40e66; plan and tasks still contain execution-gated future phases.
- Exact-title merge outcome is recorded during phase B; this phase-A record preserves the frozen scope only and grants no new execution, qualification, or route acceptance.

## Original tracked files
- openspec/changes/formal-ir-v65ar2-first-match-pipeline/INVALID_RESULT_NOTE.md
- openspec/changes/formal-ir-v65ar2-first-match-pipeline/design.md
- openspec/changes/formal-ir-v65ar2-first-match-pipeline/proposal.md
- openspec/changes/formal-ir-v65ar2-first-match-pipeline/specs/spec.md
- openspec/changes/formal-ir-v65ar2-first-match-pipeline/tasks.md

## Phase-B delta disposition

Title-level consolidation is recorded in `openspec/changes/reboot-repository-organization-20261004/S6_DELTA_MERGE.tsv` under change key `formal-ir-v65ar2-first-match-pipeline`. Included titles: 20; remaining listed titles are omitted or already equivalent, with the specific reason retained in that ledger. This resolves the earlier pending-merge filing snapshot; current AGENTS and reboot R1–R9 govern. Filing/consolidation confers no new scientific acceptance or execution authorization.
