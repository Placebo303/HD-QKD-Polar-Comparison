# Route B M2 Result — structured-DE search found converging candidate

Status: COMPLETE (M2 real-search milestone)

## Result
- q=16 folded real structured channel (V17 per-bit-plane model + Gray average + fold)
- rate=0.5, DE search found a converging degree distribution:
  - `entropy_converged=True`, `converged_iter=33`, `error_prob=0.0`
- Channel entropy H ≈ 0.3829 bits/symbol
- Leakage = 2.0 bits/symbol (rate 0.5 × 4 bits)
- **Efficiency f ≈ 5.22** (better than R3 legacy f≈8–12, still above literature f≈1.1)

## Evidence
- `comparison_bench/outputs_comparison/nonbinary_diagnostics/v18_b2_m2_real_search_20260816/`
