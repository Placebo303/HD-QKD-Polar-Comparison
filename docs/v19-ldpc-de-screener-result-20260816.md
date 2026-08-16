# V19 LDPC DE Screener — per-plane BSC regular-ensemble diagnostic

Status: COMPLETE (diagnostic)

## What it does
- Uses frozen `nonbinary_v7_r2_de.binary_bsc_threshold` (q=2 exact DE) to screen regular `(dv,dc)` LDPC ensembles.
- For each V17 per-plane BSC crossover, tries to find a regular ensemble whose DE threshold exceeds the plane error and whose rate is close to the f≈1.3 target.
- The frozen DE tool limits check degree `dc <= 13`.

## Result (N=2048, f≈1.3 target)
- Only planes 8 and 9 found regular ensembles within the frozen DE bound:
  - plane 8: (dv=3, dc=13), threshold≈0.0268 > p=0.0204, m≈473 (target 384)
  - plane 9: (dv=3, dc=10), threshold≈0.0421 > p=0.0375, m≈614 (target 615)
- Planes 0–7 have target `m/N` so small that regular `dc<=13` cannot reach the required high rate.
- This explains why the existing v4/v5 binary MLC uses irregular/structured high-rate codes instead of regular LDPC within the frozen DE bound.

## Consequence
- Reaching f≤1.3 needs either:
  - extending the DE tool to support larger check degrees (new scientific/engineering change), or
  - using irregular/structured LDPC or Polar with better construction, or
  - accepting the existing v4/v5 MLC f≈4.17.

## Evidence
- `comparison_bench/outputs_comparison/nonbinary_diagnostics/v19_ldpc_de_screener_20260816/ldpc_de_screener.json`
- CLI: `comparison_bench/src/comparison_bench/cli/run_v19_ldpc_de_screener.py`
