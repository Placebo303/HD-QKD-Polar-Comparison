# Route B M1b Result — V18-B1 q=4 DE Reproduction (corrected gate evaluation)

Status: COMPLETE — gate PASS (after fixing threshold evaluation)

## Result
- p_gate=0.062 corrected screening produced 7 eligible candidates.
- Best eligible threshold_proxy ≈ 0.067578125.
- delta = |0.067578125 - 0.069| ≈ 0.001422 <= 0.012 → **PASS**.
- Earlier NO_THRESHOLD was caused by gate evaluation reading only top-level
  `threshold_proxy` while eligible candidates carried the real thresholds.

## Evidence
- `comparison_bench/outputs_comparison/nonbinary_diagnostics/v18_b1_m1b_20260816/repro_summary.json`
- `comparison_bench/outputs_comparison/nonbinary_diagnostics/v18_b1_m1b_20260816/repro.json`
