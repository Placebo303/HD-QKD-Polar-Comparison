# Route B M2 Result — rate=0.63 parallel search all failed

Status: COMPLETE — negative result

## Result
- q=16 folded real structured channel
- rate=0.63, 8 seeds, each pop_size=20/max_gen=20/n_samples=10000/max_iter=100
- All 8 runs: `entropy_converged=False`, `error_prob=1e18`
- Therefore rate=0.63 is **not reachable** with current DE search budget on the q=16 folded proxy.

## Consequence
- The verified converging boundary on q=16 folded proxy is between rate=0.60 (one seed converged, f≈4.18) and rate=0.63 (all failed).
- Fine-grained rates 0.61/0.62 may still be attempted to locate the exact boundary, but the efficiency gain is small.
- Bigger gains are expected from q=64/256/1024 structured DE or improved search, not from tiny rate increments at q=16.

## Evidence
- `comparison_bench/outputs_comparison/nonbinary_diagnostics/v18_b2_m2_r063_par_allfail_20260816/m2_r063_par_summary.json`
- raw outputs under `workspace/nbldpc_v18_b2_r063_par/seed_0..7/`
