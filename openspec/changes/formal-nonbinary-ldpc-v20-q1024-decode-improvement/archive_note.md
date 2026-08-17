# Archive Note — formal-nonbinary-ldpc-v20-q1024-decode-improvement

Status: ARCHIVED (M5 complete, 2026-08-16)

## Why archived
- V20 M5 (bounded-weight ML) reached a stable diagnostic endpoint.
- Best result: n=64 + bounded4, 31/64 exact, FER=0.515625.
- n=80 + bounded5 top-K alternative has high variance (40/96, FER=0.5833) and did
  not reliably beat n64.
- M2 simple variants (edge-label, rho, random dense) did not improve over PEG.
- Subagent recommendation: archive current V20 M5; if continuing, open a new change
  for top-K candidate + public hash / blind reconciliation selection.

## Preserved
- All evidence under:
  - `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v20_20260816/`
  - `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_primary_20260816/n6_comparison_v6_q1024_v20_final/`
- Tests: 33 passed.
- Claim boundary: diagnostic_only.

## Audit addendum (2026-08-16)
- `31/64` reclassified as `oracle_aided_best_of_cascade_upper_bound` (not executable FER).
- `40/96` reclassified as `top4_oracle_list_coverage` (not executable FER).
- standalone bounded4 `30/64` = `unverified_bob_only_estimate`.
- `v01_readonly_verify.json` = `counting_only_verifier` (not semantic acceptance, not strict replay).
- Actual archive moves to `openspec/changes/archive/` after Phase 0 closeout per
  `docs/nbldpc-v21-bob-only-plan-20260816.md`.
