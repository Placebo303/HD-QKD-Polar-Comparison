# Route B M2 Boundary — q=16 folded structured-DE best verified result

Status: COMPLETE (current M2 stage boundary)

## Best verified result
- q=16 folded real structured channel (V17 per-bit-plane model + Gray + fold)
- **rate=0.60**, seed `2026081707`, pop_size=20/max_gen=20/n_samples=10000/max_iter=100
- `entropy_converged=True`, `converged_iter=85`, `error_prob=0.0`
- H ≈ 0.3829 bits/symbol, syndrome leakage = (1-0.60)*4 = 1.6 bits/symbol
- **Efficiency f ≈ 4.18**

## Negative results defining the boundary
- rate=0.61: 8 seeds all failed
- rate=0.62: 8 seeds all failed
- rate=0.63: 8 seeds all failed
- rate=0.65: 8 seeds all failed
- Seeded variants at rate=0.62/0.63 (using the rate=0.60 success as one population member): all 16 failed
- q=32 exploratory seeded searches at rates 0.60/0.65/0.70/0.75: all failed under moderate budgets

## Interpretation
- The current DE search framework, random or seeded, cannot find a converging q=16 folded distribution above rate=0.60.
- Larger folded q does not provide an easy win under the tried budgets.
- To approach f≈1.3, a fundamentally stronger DE/channel-model/code-design approach is required than the current V18-B2 harness.

## Evidence
- `v18_b2_m2_r06_par_seed7_20260816/`
- `v18_b2_m2_r063_par_allfail_20260816/`
- `v18_b2_m2_r061_r062_par_allfail_20260816/`
- `v18_b2_m2_r062_r063_seeded_allfail_20260816/`
- `v18_b2_m2_q32_r060_r065_seeded_moderate_allfail_20260816/`
- `v18_b2_m2_q32_r070_r075_seeded_allfail_20260816/`
