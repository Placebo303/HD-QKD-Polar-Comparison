# Archive disposition: formal-nonbinary-ldpc-v14-efficiency-gate

- Date: 2026-10-04
- Disposition: completed
- Evidence state: verified_complete_reviewed_fail_terminal
- Source evidence: tasks.md:L3-L8 says COMPLETE/gate_state=fail with independent implementation verifier, one production execute, independent gate review ACCEPT and strict replay; old decision-log:L2871-L2904 records freeze/implementation and L2908-L2925 records the reviewed terminal.
- Known review/execution state: Single frozen gate run, independent E02 review ACCEPT, strict replay; failure terminal accepted and route bounded.
- Frozen merge boundary: yes, merge all four spec requirements: Structured channel model is frozen and cross-fitted; Gate decides before construction; Mechanism regression gate Stage 0; Claim boundary.
- Next action from frozen table: archive completed; merge the four listed requirements and retain the fail boundary
- Ambiguity or unknown retained: Gate failure is a completed result; it does not establish information-theoretic impossibility.
- Exact-title merge outcome is recorded during phase B; this phase-A record preserves the frozen scope only and grants no new execution, qualification, or route acceptance.

## Original tracked files
- openspec/changes/formal-nonbinary-ldpc-v14-efficiency-gate/design.md
- openspec/changes/formal-nonbinary-ldpc-v14-efficiency-gate/evidence/v14_gate_decision.json
- openspec/changes/formal-nonbinary-ldpc-v14-efficiency-gate/evidence/v14_gate_manifest.json
- openspec/changes/formal-nonbinary-ldpc-v14-efficiency-gate/evidence/v14_replay_evidence.json
- openspec/changes/formal-nonbinary-ldpc-v14-efficiency-gate/evidence/v14_stage0_q4_qsc_regression.json
- openspec/changes/formal-nonbinary-ldpc-v14-efficiency-gate/evidence/v14_stage1_structured_smallq.json
- openspec/changes/formal-nonbinary-ldpc-v14-efficiency-gate/evidence/v14_stage2_q1024_threshold.json
- openspec/changes/formal-nonbinary-ldpc-v14-efficiency-gate/evidence/v14_structured_channel_model.json
- openspec/changes/formal-nonbinary-ldpc-v14-efficiency-gate/proposal.md
- openspec/changes/formal-nonbinary-ldpc-v14-efficiency-gate/specs/formal-nonbinary-ldpc-v14-efficiency-gate/spec.md
- openspec/changes/formal-nonbinary-ldpc-v14-efficiency-gate/tasks.md

## Phase-B delta disposition

Title-level consolidation is recorded in `openspec/changes/reboot-repository-organization-20261004/S6_DELTA_MERGE.tsv` under change key `formal-nonbinary-ldpc-v14-efficiency-gate`. Included titles: 5; remaining listed titles are omitted or already equivalent, with the specific reason retained in that ledger. This resolves the earlier pending-merge filing snapshot; current AGENTS and reboot R1–R9 govern. Filing/consolidation confers no new scientific acceptance or execution authorization.
