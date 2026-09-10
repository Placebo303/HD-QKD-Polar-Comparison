# D7-A — GF32 decoder ground-truth certification (proposal)

## What

Certify whether the historical GF32 row-layered FFT-QSPA decoder in
`comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py`
(plus the D5 layer bridge in `v72p2d5_gf32_rate_mother.py`) faithfully
implements its intended finite-iteration sum-product algorithm and
field/syndrome conventions — using a new, independently written,
slow-by-design reference oracle on tiny synthetic in-memory fixtures only.

## Why

D5/D6 stopped local graph/mother patching (`D5_D6_LOCAL_GRAPH_MOTHER_PATCHING_STOPPED`).
R1d is paused (`R1D_PAUSED_PENDING_DECODER_CERTIFICATION`). Before any further
performance attribution (D7-B/C/D) or a conditional R1d, the project must know
whether the historical decoder kernel itself is correct. A correctness defect
would invalidate downstream conclusions; a PASS bounds the bottleneck search to
schedule/interface/ensemble instead.

## Scope

In scope:

- GF32 arithmetic tables and symbol labels vs independent polynomial arithmetic.
- FFT check-node update vs independent direct-SP enumeration (deg 2/3).
- Tree-graph decoder marginals vs exact enumeration (tol 1e-10).
- Loopy-graph per-sweep beliefs vs an independent same-schedule recurrence
  (never finite-BP-vs-MAP).
- Coefficient/syndrome direction discrimination.
- `final_beliefs` representation and the L1→soft-APP→L2 bridge
  (`_run_layered_block`, `app_fed_l2_prior`).
- New files only: `v72p2d7_gf32_decoder_certification.py` (oracle),
  `test_v72p2d7_gf32_decoder_certification.py` (tests), this OpenSpec change,
  and three cycle docs.

Out of scope (explicitly not authorized):

- Any claim-bearing/formal decoder run, Model-F, CAL/VAL, real/raw data,
  VOID contents, `--phase`, R1d, G1, G2, D7-B/C/D execution, push.
- Any production-code change in the first pass, except a disabled-by-default
  D7-only trace hook in v35 if (and only if) `max_iter=1,2,3` beliefs prove
  insufficient. Default plan: no hook.

## Decision boundary

- PASS (`D7_A_DECODER_CERTIFICATION_PASS`) → next route is
  `D7_B_EASY_REGIME_PACKET_FREEZE` readiness only (no D7-B execution).
- FAIL (earliest causal class among arithmetic / check-update / tree-posterior /
  layered-dynamics / layer-interface) → `D7_A_SCOPED_CORRECTNESS_REWORK_PROPOSAL`;
  no in-task fix, no R1d.
- BLOCKED → one exact missing item, no verdict.
