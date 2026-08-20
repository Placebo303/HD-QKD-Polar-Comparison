# V31 — deterministic finite-graph redesign gate — ARCHIVE

Status: ARCHIVED — terminal `finite_graph_fail` (2026-08-21).

- FROZEN_BY_USER_OBJECTIVE (2026-08-20); implemented, executed, and closed.
- M1 DE confirmation PASS (60/60; 30/30 per n, m1=16).
- M2: `PEG-capacity-aware` deterministically rejected (L2 rank-deficient) at
  both n; `QC-cyclic-projective` constructed OK at both n.
- M3: n=1024 full window (300/300) exact/tag FER = 1.0 (L2 never
  `converged_no_syndrome`); n=2048 bounded 1M prefix confirms same failure.
- Read-only verifier `ok=true`, `problems=[]`; terminal `finite_graph_fail`.
- No push; no V30R rerun; no random search; no seed tuning; no
  qualification/promotion.
- Canonical evidence:
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_20260820/run_01/`
- Report: `docs/nbldpc-v31-deterministic-finite-graph-redesign-report-20260820.md`.
