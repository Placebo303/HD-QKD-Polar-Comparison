# Route B M2 Result — seeded DE searches at rate=0.62/0.63 also all failed

Status: COMPLETE — negative result

## Result
- q=16 folded real structured channel
- Seeded each DE population's first member with the known rate=0.60 converging degree distribution.
- rate=0.62 and 0.63, 8 seeds each (16 runs), same budget as prior multi-start searches.
- All 16 runs: `entropy_converged=False`.

## Interpretation
- The q=16 folded DE boundary is **not an artifact of random initialization**. Seeding with the best known good distribution does not make rate>0.60 converge.
- To go beyond f≈4.18, the q=16 folded-proxy DE approach has hit a practical wall in this search framework.

## Evidence
- `comparison_bench/outputs_comparison/nonbinary_diagnostics/v18_b2_m2_r062_r063_seeded_allfail_20260816/m2_seeded_allfail_summary.json`
- raw outputs under `workspace/nbldpc_v18_b2_r062_seeded_par/` and `workspace/nbldpc_v18_b2_r063_seeded_par/`
