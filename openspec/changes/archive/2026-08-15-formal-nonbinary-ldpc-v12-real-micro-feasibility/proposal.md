# Proposal: V12 Nonbinary LDPC Real Micro-Feasibility

## Status

Proposed and plan-frozen on 2026-08-12. This change is documentation-only at
creation time. It does not authorize a real-data partition, production plan,
decoder execution, qualification, or promotion.

## Why

V10 terminated `failed_ensemble` and V11 terminated `failed_coupling` before
any finite GF(1024) decoder or real frame was exercised. Those results reject
their frozen ensemble and spatial-coupling hypotheses, not the narrower
possibility that a finite nonbinary LDPC decoder can exactly correct at least
one compatible real frame.

V12 asks that narrower question with the smallest source-compatible canary.
It reuses the accepted V7 R1A finite GF(1024), `n=256` engineering baseline,
uses one previously tractable real-data stratum, and freezes four fresh frames
before decoding. The result is a proof-of-correction feasibility observation,
not a performance estimate.

## Scope

- Reconstruct, without modifying, the V7 R1A GF(1024), `n=256`, `m=170`,
  full-rank degree-2 PEG matrix and primary flooding FFT-QSPA decoder.
- Bind exactly the 10 dB Type-II, q=1024, Gray, bw200, contiguous
  256-symbol domain.
- Build a new V12-only partition containing exactly four collision-free
  `sacrificed_real_canary` frames after excluding all discoverable historical
  frame and payload identities.
- Use the frozen V7 R1A `p=.20` QSC prior without fitting V12 frames.
- Execute the four-frame canary at most once and verify it once without
  decoder reexecution.
- Record every denominator, status, syndrome, tag, control bit, iteration,
  and leakage contribution.

## Out of Scope

- Reopening or tuning V10/V11, G1-G3, spatial coupling, or DE evidence.
- Prefix search, blind rate adaptation, matrix or edge-label search, altered
  degree profile, extra iterations, fallback decoders, EMS/list decoding,
  bit-symmetric front ends, multilevel/product codes, or external code.
- Splitting one 256-symbol frame into 64-symbol decoder inputs, concatenating
  64-symbol frames, or using the old 20 dB final-IR tuning/confirmation data.
- Development/confirmation roles, more strata or frames, FER estimation,
  qualification, promotion, or formal method comparison.

## Affected Areas

- New V12 implementation under `comparison_bench/src/comparison_bench/` only.
- New V12 tests under `comparison_bench/tests/` only.
- Future test artifacts under fresh `workspace/nbldpc_v12_*` roots.
- A future approved production package under one fresh additive V12-specific
  directory in `comparison_bench/outputs_comparison/formal_ir_methods/`.
- `src/`, `experiments/`, `tools/`, `results/`, all V1-V11 sources/evidence,
  and every existing output remain unchanged.

## Decision Requested

Approve only V12 implementation plus T0/T1/T2 fake-lifecycle testing. A main-
thread read-only review must separately authorize T3, the real-source
partition, the production plan, and the one real execute.
