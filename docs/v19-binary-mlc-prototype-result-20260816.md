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
