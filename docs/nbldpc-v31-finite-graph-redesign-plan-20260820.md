# V31 deterministic finite-graph redesign gate — plan (2026-08-20)

Status: FROZEN BY USER OBJECTIVE — implementation complete, tests passing (11/11),
M1 60/60 DE confirmation PASSED (30/30 per n), production gate launched (2026-08-20).
This is the successor to V30R (`finite_graph_fail`, archived).

## Objective

Create and execute a V31 deterministic finite-graph redesign gate with:

1. No rerun of V30R balanced packets.
2. Fixed F03 GF32+GF32 and V25 source-conditioned channel.
3. Pre-registered 30-call DE confirmation for `m1=16` (per n, both
   n=1024 and n=2048 must pass).
4. Projective-capacity-aware PEG construction with hard
   `support pair occupancy <= 31`.
5. One deterministic QC/protograph-style control family:
   `QC-cyclic-projective`.
6. Bob-only validation at n=1024 and n=2048 comparing waterfall, syndrome
   convergence, exact/tag FER, and failure positions.
7. No random matrix-library search, no seed tuning, no qualification or
   promotion.
8. Read-only verifier must pass; then close with finite pass/fail.

## Frozen documents

- OpenSpec change:
  `openspec/changes/formal-nonbinary-ldpc-v31-deterministic-finite-graph-redesign-gate/`
- Proposal / design / tasks / spec:
  `proposal.md`, `design.md`, `tasks.md`,
  `specs/formal-nonbinary-ldpc-v31-deterministic-finite-graph-redesign-gate/spec.md`

## Key numbers

| n | source | m_total | m1 | m2 | f_total |
|---|---:|---:|---:|---:|---:|
| 1024 | 1M | 200 | 16 | 184 | 1.297145 |
| 1024 | 1p5M | 206 | 16 | 190 | 1.294093 |
| 1024 | 2M | 208 | 16 | 192 | 1.294947 |
| 2048 | 1M | 413 | 16 | 397 | 1.29775 |
| 2048 | 1p5M | 426 | 16 | 410 | 1.29764 |
| 2048 | 2M | 430 | 16 | 414 | 1.29847 |

## Files to implement

- `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v31.py`
- `comparison_bench/src/comparison_bench/cli/run_nonbinary_v31_gate.py`
- `comparison_bench/tests/test_nonbinary_v31.py`

## Evidence root

`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_20260820/run_01/`

## Gate sequence

M0 (read-only audit) → M1 (60-call DE confirmation) → M2 (two deterministic
families per n) → M3 (full Bob-only validation windows at both n) → read-only
verifier → close with `finite_graph_pass` / `finite_graph_fail`.
