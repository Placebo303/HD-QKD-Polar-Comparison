# Frozen Phase 4 Terra Operator Packet

Main thread owns requirements, production lifecycle, acceptance, thresholds,
and scientific conclusions. Terra low is implementation/test operator only.
The operator must also read and implement
`phase4-real-contract.md` as a normative contract.

## Allowed files

- New `formal_ir/ldpc_v5_real_qualification.py`
- New `formal_ir/ldpc_v5_confirmation_arrays.py` (first read-only
  confirmation array access; the Phase-1 partition module stays frozen)
- New `cli/run_ldpc_v5_real_qualification.py`
- New `cli/verify_ldpc_v5_real_qualification.py`
- New `tests/test_ldpc_v5_real_qualification.py`
- Phase 4 implementation checkbox after the complete candidate

No Phase-1/v1-v4/v5-development/v5-synthetic edits, no contract/handoff/
memory/decision edits, no frozen baseline edits, no historical artifact
edits, and no official production output.

## Implementation IDs

- R4-01 exact plan with partition-lock prerequisite binding (confirmation
  partition, 128/stratum) and Phase 3 synthetic readiness binding
- R4-02 6-root/768-seed schedule (toeplitz verification roots per real
  stratum/round) and predecessor+development+synthetic isolation
- R4-03 read-only confirmation array loader with exact role enforcement
  (loader never invoked for development/changed/unknown rows)
- R4-04 prepare-only fresh directory and post-write plan validation
- R4-05 exact 384-order execute (3 strata x 128 real frames) with per-frame
  public verification hooks
- R4-06 transcript/CSV/artifact DAG and immutable failure finalization
- R4-07 126/128 per-stratum gates, all denominators, zero forbidden failures
- R4-08 strict read-only verifier with no decoder reexecution
- R4-09 production/test separation and no-overwrite/no-resume

## Acceptance IDs

Implement and pass every T0--T2 item in
`phase4-real-contract.md §9`. Tests explicitly inject a fake runner and a
fake lock/array loader, and use a fresh `workspace/<task>/<uuid>` root with
pytest cache disabled. No test may call the production decoder, official
package writer, official partition lock, or official real directory.

Return only after R4-01--R4-09 and T0--T2 are complete, or on one concrete
contract blocker with exact command, traceback, attempted remedies, and the
single main-thread decision required. Do not return partial progress and do
not make an acceptance conclusion.

## Precondition (main thread, not operator)

Phase 4 may be prepared only after the Phase 3 official package verifies
`ready_for_real_qualification=true`. The operator must not prepare or execute
Phase 4 before that gate and main-thread approval.
