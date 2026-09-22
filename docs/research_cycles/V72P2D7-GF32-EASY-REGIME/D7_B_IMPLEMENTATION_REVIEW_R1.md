# D7-B independent implementation review R1

Review mode: separate verification pass over the landed implementation/test/
runner source (read in full), with representative values recomputed through
reviewer-written code sharing no logic with the implementation (literal A1
matrix restated; own degree/BFS/DFS counts; GF32 rank via generator-2
log-table elimination; own prior arithmetic; black-box terminal checks).
Limitation: single-operator context — no second agent was available (same
limitation as D7-A, mitigated by structural independence of the
recomputation rather than re-running the implementation). Green tests were not
trusted on their own.

## Checks

- **A1 literal**: implementation `build_tree_6` equals the reviewer-stated
  c0=[0,1,2]/[1,7,13], c1=[2,3,4]/[29,1,7], c2=[4,5]/[13,29] exactly. PASS.
- **Nine feasibility**: V=9, E=8, rows [3,3,2], vars [1,1,2,1,2,1], connected
  (9/9 BFS), acyclic (E=V-1, full DFS, zero back-edges), no isolated, coeffs
  1..31, independent rank 3 — all recomputed PASS.
- **No [2,3,2] dispatch**: literal `2,3,2` absent from the implementation;
  the superseded tuple survives only as prereg/manifest/test rejection prose,
  never a builder or branch. PASS.
- **No search**: matrix construction is literal (no RNG, no trial loop, no
  best-of); truths alone use the frozen seeds. PASS.
- **Priors**: PAIR spot check (0.49/0.49/0.02-30) plus positivity/
  normalization gates recomputed PASS.
- **Schedule arithmetic**: 64 cells in tier-major order, caps
  [1,2,4,8,16,32,90], worst case 448 with the 420 hard stop. PASS.
- **Terminals T1–T9**: all nine priority outcomes reproduced black-box in
  exact order (5 preemptions, alert on P99-fail or tractable-violation,
  confirmed/partial/no-region). PASS.
- **Exactness**: tree dual calc agrees to ≤3.3e-16 across all 16 TREE_6 cells
  (far under the 1e-10 gate); single-check reuse is bit-identical to the D7-A
  oracle; production never enters the exact path. PASS.
- **DI/lazy bind**: import binds nothing; unauthorized/dry-run/help create no
  root (exit 3 / matrix print); tests bind production exactly once (n=3 single
  check, k∈{1,2} — the allowed tiny fixture); every other test is fake-driven.
  PASS.
- **Scope**: scoped diff is exactly 10 D7-B files (7 plan + 3 impl); v35/D5/
  oracle untouched; no Model-F/CAL/VAL/real/raw/formal/VOID reads; no
  workspace/d7_b_easy_regime_* root; `_EXECUTION_CONSUMED` false; no push. PASS.

## Verdict

`D7_B_IMPLEMENTATION_REVIEW_PASS`

No rework required (zero of one allowed narrow reworks consumed).
