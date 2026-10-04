# Frozen Phase 2 Terra Operator Packet

Main thread owns requirements, production lifecycle, acceptance, thresholds,
and scientific conclusions. Terra low is implementation/test operator only.
The operator must also read and implement
`phase2-artifact-contract.md` as a normative contract.

## Allowed files

- New `formal_ir/ldpc_v5_development.py`
- New `cli/run_ldpc_v5_development.py`
- New `cli/verify_ldpc_v5_development.py`
- New `tests/test_ldpc_v5_development.py`
- Phase 2 implementation checkbox after the complete candidate

No Phase-1/v1-v4 edits, no contract/handoff/memory/decision edits, no frozen
baseline edits, no historical artifact edits, and no official production
output.

## Implementation IDs

- P2-01 exact plan, partition/predecessor/source/environment binding
- P2-02 18-root/9,216-seed schedule and predecessor isolation
- P2-03 prepare-only fresh directory and post-write plan validation
- P2-04 exact 4,608-order execute with development-only source access
- P2-05 transcript/CSV/artifact DAG and immutable failure finalization
- P2-06 candidate aggregation, 510/512 gates, ranking, and selection
- P2-07 strict read-only verifier with no decoder reexecution
- P2-08 production/test separation and no-overwrite/no-resume

## Acceptance IDs

Implement and pass every T0--T3 item in
`phase2-development-contract.md §9`. Tests explicitly inject a fake runner
and use a fresh `workspace/<task>/<uuid>` root with pytest cache disabled.
No test may call the production decoder, official partition output writer, or
official development directory.

Return only after P2-01--P2-08 and T0--T3 are complete, or on one concrete
contract blocker with exact command, traceback, attempted remedies, and the
single main-thread decision required. Do not return partial progress and do
not make an acceptance conclusion.
