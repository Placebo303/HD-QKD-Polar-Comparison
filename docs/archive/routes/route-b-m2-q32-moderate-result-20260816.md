# Route B M2 Result — q=32 moderate seeded searches all failed

Status: COMPLETE — exploratory negative result

## Result
- q=32 folded real structured channel
- Seeded with the q=16 rate=0.60 successful degree distribution
- Rates 0.60 and 0.65, 8 seeds each
- Budget: pop_size=10, max_gen=10, n_samples=2000, max_iter=50
- All 16 runs: `entropy_converged=False`

## Interpretation
- q=32 did not converge under a moderate-budget search.
- This may be due to insufficient search budget rather than a fundamental q=32 limit; it shows that moving to larger q is not a cheap win.
- q=16 rate=0.60 remains the best verified folded-proxy result (f≈4.18).

## Evidence
- `comparison_bench/outputs_comparison/nonbinary_diagnostics/v18_b2_m2_q32_r060_r065_seeded_moderate_allfail_20260816/m2_q32_moderate_allfail_summary.json`
- raw outputs under `workspace/nbldpc_v18_b2_q32_r060_seeded_par/` and `workspace/nbldpc_v18_b2_q32_r065_seeded_par/`
