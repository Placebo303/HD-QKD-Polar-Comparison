# V31 deterministic finite-graph redesign gate — report

Status: IN PROGRESS (production run launched 2026-08-20).

## Executive summary

- Fixed F03 GF32+GF32, V25 source-conditioned channel, m1=16, n=1024 and n=2048.
- M1 pre-registered DE confirmation PASSED 60/60 (30/30 per n) with V26 adapter (57s).
- M2 deterministic families implemented: PEG-capacity-aware (occupancy<=31 hard gate) and QC-cyclic-projective control.
- M3 Bob-only full-window validation running; summary/FER/waterfall/failure-position comparison pending.

## Gate status (2026-08-21)

- M1: PASS (60/60 DE confirmation; 30/30 per n, m1=16)
- M2: COMPLETE
  - `PEG-capacity-aware` n=1024 and n=2048: DETERMINISTIC REJECT on construction
    hard gate — L2 matrices are GF(32) rank-deficient (e.g., m=200->rank199,
    m=414->rank413), so full row rank fails.
  - `QC-cyclic-projective` n=1024 and n=2048: construction OK (full rank,
    projective-safe, max support occupancy <=9).
- M3: RUNNING (n=1024 QC packet). Source 1M window COMPLETE (100/100 blocks):
  `l1_ok=98`, `l2_ok=0`, `exact=0`, `tag=0`, `false_accept=0` -> 1M exact =
  tag FER = 1.0 for the QC-cyclic family at n=1024. 1p5M/2M n=1024 and the
  n=2048 QC window still running to complete the waterfall/failure-position
  comparison.
- Read-only verifier: pending

Evidence root:
`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_20260820/run_01/`

## To be filled at closeout

- M2 construction results per n per family (rank, projective hard gate, occupancy, 4/6/8-topology)
- M3 per-n per-family FER/syndrome convergence/waterfall/failure positions
- Final terminal: `finite_graph_pass` or `finite_graph_fail`
- Verifier `ok=true` / problems list
