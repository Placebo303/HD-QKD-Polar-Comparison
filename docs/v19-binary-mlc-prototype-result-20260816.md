# V19 Binary-MLC Prototype — synthetic per-plane LDPC all-correct datapoint

Status: COMPLETE (prototype, diagnostic_only)

## What was run
- Per Gray bit-plane (10 planes), use existing frozen binary LDPC v4 H1 matrices.
- If H1 decode fails, use v5 H2 stacked fallback (same as v5 C2 behavior).
- Synthetic BSC errors with V17 per-plane error probabilities, N=256 symbols/frame.
- 50 frames per plane, deterministic seed.

## Result
- **0 failures across all 500 plane-frame trials**.
- Average syndrome bits/frame ≈ 587 bits.
- Measured `f ≈ 4.169` (using H_full=0.549955 bits/symbol).
- Fallback only needed on plane 6 in 3/50 frames.
- This is a real working per-plane binary-MLC datapoint, but the existing v4/v5 codebook is still far from the ideal f≈1.0 because H1 row counts are conservative.

## Relation to Route B/C
- Confirms that per-plane MLC is a viable correction pipeline on the V17 structured channel.
- The gap between ideal f≈1.0 and current v4/v5 f≈4.17 is due to finite-length LDPC rates/row counts, not a conceptual blocker.
- Next step: design higher-rate per-plane codes / Polar-like capacity-approaching codes, or reduce row counts with better matrices, to approach f≤1.3.

## Evidence
- `comparison_bench/outputs_comparison/nonbinary_diagnostics/v19_binary_mlc_prototype_20260816/binary_mlc_prototype.json`
- CLI: `comparison_bench/src/comparison_bench/cli/run_v19_binary_mlc_prototype.py`

## Exploratory high-rate random LDPC attempt (not accepted)
- Tried N=2048 random LDPC with per-plane syndrome rows set to `max(ceil(log2 N), ceil(N*h2(p)*1.2))`, target f≈1.22.
- Random regular/light construction failed on many planes (especially p≥0.0046), so this is **not** a usable f≤1.3 code yet.
- It confirms that reaching f≈1.3 requires optimized code design / Polar-like capacity-approaching codes, not naive random LDPC.
- This exploratory attempt is recorded in `workspace/v19_mlc_highrate_test.out`; it is not a production claim.

## Exploratory Polar SC/SCL attempt (not accepted)
- Tried Polar SC and existing CA-SCL (list size 4) with N=2048, PW-order construction, per-plane syndrome rows targeting f≈1.32.
- Both SC and SCL still had many frame errors at the target high rates.
- This indicates that reaching f≤1.3 needs better polar construction / larger list / CRC-aided design or optimized LDPC, not just reusing the current PW-order SC/SCL decoder as-is.
- Exploratory outputs: `workspace/v19_mlc_polar_test.out`, `workspace/v19_mlc_scl_test.out`.

## CA-SCL list=32 experimental decoder
- Added an experimental copy of the CA-SCL decoder with `kListSize=32` under
  `comparison_bench/src/comparison_bench/formal_ir/v19_ca_scl.cpp` + wrapper.
- Noiseless test passes, so the wrapper/decoder plumbing is correct.
- At N=2048/4096 and target f≈1.3, simple PW-order + list=32 still has frame errors on multiple planes.
- This confirms that reaching f≤1.3 needs further code construction work (GA/tailored frozen sets, CRC, larger list, or different code family), not just a list-size bump.
