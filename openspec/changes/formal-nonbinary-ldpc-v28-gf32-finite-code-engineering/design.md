# V28 Design — GF32×GF32 Deterministic Finite-Code Engineering

## 1. V27-selected parameters (frozen; do not re-optimize)
Minimal passing block_len = **1024** (all four block_lens passed; 1024 is the smallest).
Per source, the confirmed candidate is the m1_ep offset-0 split:

| source | m_total | m1 (L1 checks) | m2 (L2 checks) | R1 = 1−m1/1024 | R2 = 1−m2/1024 |
|--------|---------|----------------|----------------|----------------|----------------|
| 1M     | 200     | 6              | 194            | 0.994140625    | 0.810546875    |
| 1p5M   | 206     | 6              | 200            | 0.994140625    | 0.8046875      |
| 2M     | 208     | 6              | 202            | 0.994140625    | 0.802734375    |

L1 has m1 = 6 checks for **all** sources → `H_mother_L1` is shared (6 × 1024).
L2 has source-specific m2 ∈ {194, 200, 202} → `H_mother_L2` is built with
`max(m2) = 202` rows; source `s` uses the public prefix `H_mother_L2[:m2_s, :]`.

## 2. Field
`GF2mField.create(32)` → q=32, m=5, poly `0b100101`, basis polynomial, symbols ∈ [0,32).
Pinned, immutable (verified by `field_id`). No new arithmetic.

## 3. Mother-matrix construction (deterministic, seeded)
Reuse `nonbinary_codebook._matrix(q, seed, shifts)` topology
`three_shift_cyclic_information_half_plus_identity_parity_half`, generalized to `(m, n)`:
- `H_mother_L1`: `m=6`, `n=1024`, frozen `seed_L1`, `shifts_L1`.
- `H_mother_L2`: `m=202`, `n=1024`, frozen `seed_L2`, `shifts_L2`.
All entries ∈ GF(32). `gf_rank(H, field) == m` is a hard acceptance gate (full rank; the
code has dimension `n − m`).
Layer matrix for (layer, source): `H = H_mother_layer[:m_layer(source), :]`.

## 4. Two-layer sequential decode (Bob-only)
- x1 ∈ GF(32)^n (high 5 bits), x2 ∈ GF(32)^n (low 5 bits); block symbol = 10 bits.
- Alice computes `s1 = H_L1 · x1`, `s2 = H_L2 · x2` (GF(32) matrix mult).
- Bob decodes **L1 first** from `s1` using the L1 channel posterior (from V25/V26 adapter,
  true-symbol centered): `decode_nonbinary_fft_qspa(prior_L1, s1, manifest_L1, matrices_L1)`.
- Then decodes **L2 conditioned on decoded x1** (true-predecessor-conditioned finite analog):
  `decode_nonbinary_fft_qspa(prior_L2|x1, s2, manifest_L2, matrices_L2)`.
- No Alice oracle; no top-K truth selection; failures are reported, not replaced.

## 5. 64-bit tag + leakage accounting
- Final **64-bit public verification tag** computed over the decoded `(x1, x2)` block
  (frozen verification: SHA-256 truncated to 64 bits, or the existing `locked_seed` tag
  mechanism from `ldpc.py`/`ldpc_v5.py`). Tag is verification only, not secret.
- **Total leakage per source** = `syndrome_bits + tag_bits`
  = `(m1 + m2) · log2(32) + 64` = `(m_total)·5 + 64` bits.
  - 1M: 200·5 + 64 = **1064 bits**; n·H_source(1M)=1024·0.801037825≈820.26 → f≈1.297 < 1.3.
  - 1p5M: 206·5 + 64 = 1094 bits; n·H≈1024·0.825565... → f < 1.3.
  - 2M: 208·5 + 64 = 1104 bits; n·H≈1024·0.83256... → f < 1.3.
- The 64-bit tag is **only** in the total block leakage, never between layers (matches V27).

## 6. Reproduction / freeze binding
- All seeds, shifts, field spec, dimensions, and the 64-bit tag derivation are frozen in a
  `v28_config.json` written to the additive run root; `verify_v28` reconstructs matrices and
  re-runs the structural + decode checks from `v28_config.json` + persisted artifacts.

## 7. Terminal state
- Only `engineering_ready_for_retrospective_gate`. No FER/qualification/promotion claim.
