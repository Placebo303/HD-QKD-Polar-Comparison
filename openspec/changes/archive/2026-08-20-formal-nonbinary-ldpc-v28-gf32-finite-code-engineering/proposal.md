# V28R — GF32×GF32 finite-code engineering repair

## Status

The earlier V28 `ACCEPT` and `run_01` are retained as historical evidence but
are **superseded_by_independent_review** and **invalid_for_V29**. The original
identity/row-prefix matrix did not implement the frozen `lambda={2:1}` contract.

## Objective

Materialize the V27-passing `n=1024`, F03 (`GF(32)+GF(32)`) split as two
Bob-only finite-code layers. L1 is one shared 6×1024 degree-two matrix. L2 is
an independently constructed source-specific degree-two matrix with
194/200/202 rows. V28R performs only synthetic/noiseless and fixed controlled
smoke checks; it does not perform FER or qualification.

## Frozen boundary

- Reuse the pinned `GF2mField.create(32)`, `_coefficient`, `gf_rank`, and V10
  `decode_fftqspa`; no new field arithmetic or BP decoder.
- Use the V26 train `ChannelAdapter` posterior centered relative to Bob's
  observed layer symbols. L2 receives the actual returned `x1_hat` from L1;
  Alice truth never enters the decoder.
- Freeze the tag to the first eight bytes of
  `SHA256(bytes(x1)||bytes(x2))`; no alternate seed tag exists.
- Do not read holdout data, `pairs.parquet`, raw `.ttbin`, or run DE/MC-DE.

## Acceptance and terminal state

The verifier reconstructs matrices, ranks, edge/pair order, degree histograms,
leakage/tag, source-delay binding, and sequential posterior-call semantics. It
writes `readonly_verify.json`. Only an all-pass run may use
`engineering_ready_for_retrospective_gate`; controlled errors are fail-closed
diagnostics and are not a correction/FER claim.
