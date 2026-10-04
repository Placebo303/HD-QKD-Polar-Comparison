# Route B M2 Result — q=32 high-rate seeded searches all failed

Status: COMPLETE — exploratory negative result

## Result
- q=32 folded real structured channel
- Seeded with the q=16 rate=0.60 successful degree distribution
- Rates 0.70 and 0.75, 8 seeds each
- Budget: pop_size=15, max_gen=15, n_samples=3000, max_iter=60
- All 16 runs: `entropy_converged=False`

## Interpretation
- q=32 did not converge at high rates under this larger moderate budget.
- The current DE search framework does not readily transfer the q=16 success to q=32.
- q=16 rate=0.60 (f≈4.18) remains the best verified folded-proxy result.

## Evidence
- `comparison_bench/outputs_comparison/nonbinary_diagnostics/v18_b2_m2_q32_r070_r075_seeded_allfail_20260816/m2_q32_r070_r075_seeded_allfail_summary.json`
- raw outputs under `workspace/nbldpc_v18_b2_q32_r070_seeded_par/` and `workspace/nbldpc_v18_b2_q32_r075_seeded_par/`
