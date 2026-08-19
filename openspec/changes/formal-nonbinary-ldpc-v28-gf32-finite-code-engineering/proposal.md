# V28 — GF32×GF32 Deterministic Finite-Code Engineering

## What
Turn the V27-passing source-adaptive split at `passing_block_len=1024` into concrete,
deterministic two-layer **GF(32) parity-check** finite-code matrices plus a Bob-only
sequential decoder. V28 performs **no DE / no MC-DE / no FER**: it constructs the matrices,
verifies structural and decoding correctness on frozen inputs, and stops at
`engineering_ready_for_retrospective_gate`. V29 then runs the retrospective finite-code
gate on frozen V25 holdout data.

## Why
V27 proved *asymptotic* feasibility (density-evolution convergence) of the finite-leakage-
margin split `(m1, m2, R1, R2)` for block_len ∈ {1024..8192}, sources {1M, 1p5M, 2M}. The
minimal passing block_len is **1024**, confirmed at the m1_ep offset-0 candidate for every
source. V28 materializes that split as real GF(32) codes so V29 can measure finite-code
behavior (layer FER, overall FER) on frozen holdout — without re-deriving the split.

## Scope (in scope)
- Reuse `comparison_bench/.../formal_ir/nonbinary_field.GF2mField.create(32)` — pinned
  GF(32) (m=5, primitive polynomial `0b100101`). **No new field math.**
- Reuse the deterministic three-shift-cyclic mother-matrix construction
  (`nonbinary_codebook._matrix` topology `three_shift_cyclic_information_half_plus_identity_
  parity_half`), generalized to `(m_i, n)` with a frozen seed per (layer, source prefix).
- Two layers: **L1** = high 5 bits/symbol, **L2** = low 5 bits/symbol, each a GF(32) code
  of length `n = 1024`. Block = `n` symbols of 10 bits = `L1 ⊕ L2` (GF(32)×GF(32), A02/F03).
- Source determines **only the public syndrome row prefix** of the frozen mother matrix
  (no secret/material change; prefix is public and leak-accounted).
- Reuse the **GF(32) FFT-QSPA decoder** (`nonbinary_qspa.decode_nonbinary_fft_qspa` /
  `nonbinary_v10_...` FFT-QSPA) for layer decoding. **No new decoder science.**
- Final **64-bit public verification tag**: computed over the decoded `(x1, x2)` block;
  `syndrome_bits + tag_bits` constitute the total leakage (see accounting).
- Verification checks: matrix dimensions, exact GF(32) rank (`gf_rank` == `m_i`), syndrome
  consistency `s_i = H_i · x_i`, source row-prefix accounting, noiseless decode,
  controlled-error decode, deterministic seed replay, Bob-only sequential (L1→L2) semantics.
- Terminal state **only** `engineering_ready_for_retrospective_gate`.

## Out of scope (forbidden in V28)
- No density evolution / MC-DE (that was V27).
- No fresh / raw `.ttbin` reads.
- No degree / m1 / m2 / MET search; no re-tuning; no re-derivation of the split.
- No finite FER / qualification / promotion claim in V28 (that is V29, which is gated).
- No push.

## Affected specs
New delta spec `specs/formal-nonbinary-ldpc-v28-gf32-finite-code-engineering/spec.md`
(adds the `v28_gf32_finite_code` capability and its acceptance criteria).
