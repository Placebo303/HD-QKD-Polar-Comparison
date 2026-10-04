# Frozen Phase 3 Terra Operator Packet

Main thread owns requirements, production lifecycle, acceptance, thresholds,
and scientific conclusions. Terra low is implementation/test operator only.
The operator must also read and implement
`phase3-synthetic-contract.md` as a normative contract.

## Allowed files

- New `formal_ir/ldpc_v5_synthetic_qualification.py`
- New `cli/run_ldpc_v5_synthetic_qualification.py`
- New `cli/verify_ldpc_v5_synthetic_qualification.py`
- New `tests/test_ldpc_v5_synthetic_qualification.py`
- Phase 3 implementation checkbox after the complete candidate

No Phase-1/v1-v4/v5-development edits, no contract/handoff/memory/decision
edits, no frozen baseline edits, no historical artifact edits, and no official
production output.

## Implementation IDs

- P3-01 exact plan with development-package prerequisite binding and
  V5-C2 policy/h2/channel/codebook bindings
- P3-02 8-root/512-seed schedule (bob/delta frame roots, per stratum/round
  Toeplitz roots) and predecessor+development isolation
- P3-03 deterministic nominal/stress synthetic frame generator
  (PCG64, delta order minus, plus, zero) with new domain-separated roots
- P3-04 prepare-only fresh directory and post-write plan validation
- P3-05 exact 256-order execute (2 strata x 128 frames, data-stratum
  placeholder bw120) with per-frame public verification hooks
- P3-06 transcript/CSV/artifact DAG and immutable failure finalization
- P3-07 126/128 per-stratum gates, all denominators, zero forbidden failures
- P3-08 strict read-only verifier with no decoder reexecution
- P3-09 production/test separation and no-overwrite/no-resume

## Acceptance IDs

Implement and pass every T0--T2 item in
`phase3-synthetic-contract.md §8`. Tests explicitly inject a fake runner
and use a fresh `workspace/<task>/<uuid>` root with pytest cache disabled.
No test may call the production decoder, official package writer, or official
synthetic directory.

Return only after P3-01--P3-09 and T0--T2 are complete, or on one concrete
contract blocker with exact command, traceback, attempted remedies, and the
single main-thread decision required. Do not return partial progress and do
not make an acceptance conclusion.
