# Archive disposition: formal-ir-v72p2d5-model-f-input-preparation

- Date: 2026-10-04
- Disposition: completed
- Evidence state: accepted_model_f_input_and_reviewed_readiness; production_gates_unrun
- Source evidence: docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/MODEL_F_INPUT_RESULT_ACCEPTANCE_R1.md:L1-L6,L22-L34,L52-L90 records user-authorized MODEL_F_INPUT_RESULT_ACCEPTED, Pre-EXECUTE R2 PASS, Pre-RESULT R2 PASS, C01-C11 PASS, and no promotion/authorization; MODEL_F_INPUT_PRE_RESULT_REVIEW_R2.md:L79-L168 supplies the independent review; specs/spec.md:L5-L62 defines exact clauses.
- Known review/execution state: One authorized prepare and one read-only verify completed; independent Pre-RESULT R2 PASS with C01-C11; user-authorized main result acceptance is explicit. Acceptance covers Model-F CAL input only; all production authorization/promotion flags remain false.
- Frozen merge boundary: limited implementation/readiness scope: S-MODEL-F-INPUT (S-MF-01..04); S-MODEL-F-BUILD (S-MB-01..03); S-MODEL-F-WRITE (S-MW-01..02); S-MODEL-F-LOAD (S-ML-01..02); S-MODEL-F-RUN (S-MR-01 and only the CAL-only/no-VAL/no-decoder prepare/verify behavior of S-MR-02); S-PATH-01..05; S-MODEL-F-CONSUME S-MC-01..02 and S-TEST-ISOLATION TS01..TS10 only as reviewed implementation-readiness contracts, not production execution. Exclude P0/G1/G2 decoder/performance results and authorization. Do not merge S-SP-01 or the no-real-prepare prohibition in S-MR-02 as written: an authorized CAL prepare+verify was later executed and accepted; amend that lifecycle text before merge.
- Next action from frozen table: Archive completed limited-scope after recording the contradiction; merge only the named input/readiness clauses after revising the no-execution wording, and leave all P0/G1/G2 scientific/production clauses unmerged.
- Ambiguity or unknown retained: Proposal, tasks, S-SP-01 and S-MR-02 say no real prepare in this change, but the later authorized prepare/verify and result acceptance are explicit. The accepted artifact is a CAL-only Model-F input, not a decoder, P0, G1, G2, FER, leakage, or key result.
- Exact-title merge outcome is recorded during phase B; this phase-A record preserves the frozen scope only and grants no new execution, qualification, or route acceptance.

## Original tracked files
- openspec/changes/formal-ir-v72p2d5-model-f-input-preparation/design.md
- openspec/changes/formal-ir-v72p2d5-model-f-input-preparation/proposal.md
- openspec/changes/formal-ir-v72p2d5-model-f-input-preparation/specs/spec.md
- openspec/changes/formal-ir-v72p2d5-model-f-input-preparation/tasks.md

## Phase-B delta disposition

Title-level consolidation is recorded in `openspec/changes/reboot-repository-organization-20261004/S6_DELTA_MERGE.tsv` under change key `formal-ir-v72p2d5-model-f-input-preparation`. Included titles: 8; remaining listed titles are omitted or already equivalent, with the specific reason retained in that ledger. This resolves the earlier pending-merge filing snapshot; current AGENTS and reboot R1–R9 govern. Filing/consolidation confers no new scientific acceptance or execution authorization.
