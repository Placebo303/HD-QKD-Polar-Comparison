# Archive Note — formal-nonbinary-ldpc-v24-structured-single-edge-de-optimization

Status: ARCHIVED (M3 closeout complete; V24 gate FAIL, 2026-08-18)

## Why archived
- V24 ran the frozen bounded single-edge M0-M2 gate on the V17 q=1024
  structured channel at design rate ~0.9375 (f_total <= 1.3).
- Terminal state: `fail` = `single_edge_bounded_optimization_failed`.
  M0 mechanism PASS; 135 valid candidates from 8192 attempts; screen/refine/
  holdout all 0-converged; 0/4 finalists passed all five holdout seeds
  (final entropy floor ~0.20-0.32). 314 DE calls, 4.87 h accumulated (< 24 h).
- Read-only verifier ok=True, recomputed terminal fail.

## Preserved
- Code: `nonbinary_v24_single_edge_de.py` (module), `run_v24_single_edge_de.py`
  (CLI), `test_nonbinary_v24_single_edge_de.py` (21 tests, all pass).
- Evidence:
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v24_20260818/run_20260818T135145_prod/`
- Report: `docs/nbldpc-v24-gate-report-20260818.md`.
- Engineering acceptance: `evidence/engineering_review_i11.json`.

## Successor boundary
- `fail` closes the bounded single-edge optimization. True MET/multi-edge DE,
  and any adjustment to q / channel decomposition / f target, are separate
  changes requiring a new explicit user authorization. No finite-code/FER/
  qualification/promotion/MET was run. No push.
