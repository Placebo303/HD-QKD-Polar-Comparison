# Archive disposition: formal-nonbinary-ldpc-v17-multibit-structured-de-gate

- Date: 2026-10-04
- Disposition: completed
- Evidence state: verified_complete_reviewed_fail_terminal_spec_forbids_merge
- Source evidence: tasks.md:L3-L8 records CLOSED terminal mechanism_unverified, one production gate run, strict replay, independent E02 review ACCEPT and C01 closeout; old decision-log:L2989-L3010 records the gate terminal and diagnostic boundary.
- Known review/execution state: Failed gate result and strict replay were independently reviewed and accepted as a bounded diagnostic; no finite code or qualification.
- Frozen merge boundary: no; spec.md header explicitly says gate_state=fail SHALL NOT merge; preserve the six frozen V17 requirements as archived evidence only.
- Next action from frozen table: archive completed with gate failure; no delta merge under the spec header
- Ambiguity or unknown retained: Do not generalize the unverified mechanism terminal to all structured/nonbinary LDPC.
- Delta merge: none, as explicitly specified by the frozen table.

## Original tracked files
- openspec/changes/formal-nonbinary-ldpc-v17-multibit-structured-de-gate/design.md
- openspec/changes/formal-nonbinary-ldpc-v17-multibit-structured-de-gate/evidence/v17_gate_decision.json
- openspec/changes/formal-nonbinary-ldpc-v17-multibit-structured-de-gate/evidence/v17_gate_manifest.json
- openspec/changes/formal-nonbinary-ldpc-v17-multibit-structured-de-gate/evidence/v17_multibit_channel_model.json
- openspec/changes/formal-nonbinary-ldpc-v17-multibit-structured-de-gate/evidence/v17_replay_evidence.json
- openspec/changes/formal-nonbinary-ldpc-v17-multibit-structured-de-gate/evidence/v17_stage0.json
- openspec/changes/formal-nonbinary-ldpc-v17-multibit-structured-de-gate/evidence/v17_stage2.json
- openspec/changes/formal-nonbinary-ldpc-v17-multibit-structured-de-gate/proposal.md
- openspec/changes/formal-nonbinary-ldpc-v17-multibit-structured-de-gate/specs/formal-nonbinary-ldpc-v17-multibit-structured-de-gate/spec.md
- openspec/changes/formal-nonbinary-ldpc-v17-multibit-structured-de-gate/tasks.md

## Phase-B delta disposition

Title-level consolidation is recorded in `openspec/changes/reboot-repository-organization-20261004/S6_DELTA_MERGE.tsv` under change key `formal-nonbinary-ldpc-v17-multibit-structured-de-gate`. Included titles: 0; remaining listed titles are omitted or already equivalent, with the specific reason retained in that ledger. This resolves the earlier pending-merge filing snapshot; current AGENTS and reboot R1–R9 govern. Filing/consolidation confers no new scientific acceptance or execution authorization.
