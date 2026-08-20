# V31 deterministic finite-graph redesign gate — report

Status: IN PROGRESS (production run launched 2026-08-20).

## Executive summary

- Fixed F03 GF32+GF32, V25 source-conditioned channel, m1=16, n=1024 and n=2048.
- M1 pre-registered DE confirmation PASSED 60/60 (30/30 per n) with V26 adapter (57s).
- M2 deterministic families implemented: PEG-capacity-aware (occupancy<=31 hard gate) and QC-cyclic-projective control.
- M3 Bob-only full-window validation running; summary/FER/waterfall/failure-position comparison pending.

## Gate status

- M1: PASS (60/60)
- M2: in progress
- M3: pending
- Read-only verifier: pending

Evidence root:
`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_20260820/run_01/`

## To be filled at closeout

- M2 construction results per n per family (rank, projective hard gate, occupancy, 4/6/8-topology)
- M3 per-n per-family FER/syndrome convergence/waterfall/failure positions
- Final terminal: `finite_graph_pass` or `finite_graph_fail`
- Verifier `ok=true` / problems list
