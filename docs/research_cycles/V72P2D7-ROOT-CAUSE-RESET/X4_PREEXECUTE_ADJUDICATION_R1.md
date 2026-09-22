# X4 Pre-EXECUTE adjudication record R1

- Cycle: `V72P2D7-ROOT-CAUSE-RESET`
- Change: `formal-ir-d7-root-cause-and-route-reset`
- Packet: `.workbuddy/tasks/D7_X1_X4_EXECUTION_MASTER_R1_TASK_PACKET.md`
  (§7 X4 P08/P09, §8, §9); Addendum A1 (`## Required independent reviews`:
  "Before X4 execution, close or explicitly adjudicate these carried
  findings ...").
- Authority: the three findings carried by the Phase P independent
  readiness review
  (`PHASE_P_INDEPENDENT_READINESS_REVIEW_R1.md`, §"Non-blocking findings
  carried to phase Pre-EXECUTE", items 1/5/3) and the A2 remediation record
  (`A2_X2_X4_REMEDIATION_AUTHORIZATION_R1.md`).
- Adjudication verdict: **`ACCEPTED-AS-IS`** with mandatory operator
  conditions (below). No implementation change is made for these findings;
  no matrix, seed, root, command, budget, provenance semantic, terminal, or
  claim-ceiling item is touched.
- Prerequisite gate: X3 Pre-RESULT review PASS
  (`X3_PRE_RESULT_REVIEW_R1.md`); state `X3_COMPLETE_VERIFIED`;
  `next_gate: X4_EXECUTION`.
- Role: operator record only; it does not authorize X4 (the separate
  `x4_g2_execution_authorized` flag and A1 chain do), does not accept any
  result, and does not alter the frozen contract.

## 1. Carried finding (a) — repo-rooted existence check vs CWD-relative writer

**Finding.** `run_g2_bridge` builds the existence-checked root as
`Path(repo_root) / d5.G2_FORMAL_ROOT` when `frozen_root` is not injected,
while the writer reached through `run_g2_synthetic` resolves the relative
`G2_FORMAL_ROOT` from the process CWD.

**Adjudication `ACCEPTED-AS-IS`.** Under the frozen command the two paths
coincide: the CLI passes `repo_root=ROOT` (the repository root resolved from
`__file__`), and the attempt is launched with CWD = repository root, so
`repo_root / "workspace/v72p2d5_g2/20260906_r1"` and CWD-relative
`workspace/v72p2d5_g2/20260906_r1` are the same directory. Overwrite is
impossible on either path: the bridge raises `FileExistsError` before calling
the runner if the repo-rooted root exists, and the writer
(`_write_stage_evidence`, reached via `write_g2_evidence`) independently
raises `FileExistsError` if the CWD-relative directory exists, before
creating anything.

**Mandatory operator conditions:**

1. Run the frozen command from the repository root
   (`/mnt/d/Code/HD-QKD_Polar_Comparison`); record CWD in the pre-EXECUTE
   block.
2. Verify the frozen root and its parent are ABSENT immediately before the
   attempt, and verify the created root at exactly
   `/mnt/d/Code/HD-QKD_Polar_Comparison/workspace/v72p2d5_g2/20260906_r1`
   after the attempt (same inode/directory; four frozen files).
3. Retain the no-overwrite check (pre/post status diff, file-window scan,
   `FileExistsError` contract); the writer raising on an existing path is
   the overwrite guard — no code change is needed.

## 2. Carried finding (b) — non-dict runner coercion

**Finding.** `run_g2_bridge` maps any non-dict runner return to `{}`
(`result = result if isinstance(result, dict) else {}`), so a malformed
runner return would surface as a zero-call, undefined-grade bridge result
instead of an explicit error.

**Adjudication `ACCEPTED-AS-IS` (latent/test-only).** Unreachable with the
production runner: the bridge's default runner is
`d5.run_g2_synthetic(authorized=True)`, which returns one result dict, and
any loader/decoder/writer failure raises (the CLI maps it to exit 3 before
printing a grade). The coercion branch can only be exercised by an injected
test runner. No production path can convert a failure into a `{}` grade
because the bridge is called with `run_g2_fn=None` under the frozen command.

**Mandatory operator condition:** if the attempt's CLI prints
`G2 bridge refused: ...` or exits 3, record it as an engineering/refusal
terminal (authorization consumed, BLOCKED), never as a grade. Do not add a
guard in this attempt (out of the frozen X4 delta and unnecessary for the
production path).

## 3. Carried finding (c) — external 120 s per-call watchdog ownership

**Finding.** The frozen X4 contract has a single-call <=120 s budget owned
externally (`PER_CALL_WATCHDOG_S = 120.0` is defined in the D7 core module
but is not enforced in-process for G2); the frozen G2 evidence set
(`results.json`, `table.csv`, `report.md`, `execution_summary.json`)
contains **no per-call wall field and no per-call timestamps** — only
aggregate `wall_seconds`, `peak_rss_bytes`, and per-f counters. Therefore a
per-call 120 s violation is **NOT machine-observable in the frozen evidence
set**; only the total wall is machine-observable (and the grade blocks if
`wall > 3600 s` or `peak RSS >= 2 GiB`).

**Adjudication `ACCEPTED-AS-IS` with an explicitly owned external guard.**

**Mandatory operator conditions:**

1. Record the exact outer watchdog command and owner in the X4 operator
   return: `timeout -k 30 3660 .venv/bin/python
   scripts/v72p2d7_consistency_multigraph.py --g2`, launched as exactly one
   foreground process from the repository root by this X4 operator
   (`timeout` = total-wall owner, SIGTERM at 3660 s, SIGKILL at 3690 s;
   stored budget 3600 s).
2. Record that the per-call 120 s budget is externally owned by this X4
   operator and is not machine-observable in the frozen evidence; the
   binding machine-observable guards for this attempt are total wall
   (watchdog) and the grader's wall/RSS block conditions.
3. Apply process-level stall monitoring for the attempt: a separate monitor
   process owned by this operator samples the CPU time of the attempt's
   process tree; if no CPU-time progress occurs for **>120 s**, the monitor
   terminates that process tree (SIGTERM, then SIGKILL after 30 s) and the
   attempt is voided as `BLOCKED` (no retry, evidence retained in place).
   Record the exact monitor command, owner, and disposition in the return;
   distinguish the three dispositions `COMPLETED_BEFORE_OUTER_WATCHDOG` /
   `STALL_MONITOR_TERMINATED_VOID` / `OUTER_WATCHDOG_EXPIRED`.
4. Report total wall and watchdog disposition; do not claim per-call
   compliance beyond the recorded aggregate evidence.

## 4. X4 preconditions (frozen, verified at adjudication time)

- Frozen root `workspace/v72p2d5_g2/20260906_r1`: **ABSENT** (its parent
  `workspace/v72p2d5_g2/` is also absent) at record creation.
- Matrix: `n = 256`; `f = 1.0, 1.1, 1.2`; rows L1 = **196, 215, 235**
  and L2 = **172, 189, 206** (recomputed from `_rows_required` at these
  f/width/frozen-ceiling values); **200 blocks per f** (seeds
  2026091000..2026091199); oracle subset **40 per f**; max decoder calls
  **1320** (= 200 x 3 x 2 + 40 x 3).
- Budgets: total stored wall <= **3600 s** (outer watchdog 3660 s);
  single call <= **120 s** externally owned (see §3); RSS < **2 GiB**
  (grader blocks at >= `G2_RSS_BUDGET_BYTES`).
- Four-state grading vocabulary only: `G2_SYNTHETIC_QUALIFIED`,
  `G2_INCONCLUSIVE`, `G2_CURRENT_CONFIGURATION_FAILED`,
  `IMPLEMENTATION_OR_NUMERICAL_BLOCKED` (`GRADE_QUALIFIED`,
  `GRADE_INCONCLUSIVE`, `GRADE_FAILED`, `GRADE_BLOCKED` in the mother
  module).
- Bridge preconditions: `x4_g2_execution_authorized` true (set immediately
  before the single process start; restored false immediately after); every
  D5 execution flag false (`structure`, `g0`, `g0-recovery`, `p0-cost`,
  `g1`, `g2`, `synthetic`, `real`, `formal` — all verified false in
  `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/cycle_state.yaml`); D7
  `d7h_execution_authorized` false; no G1 rerun, no D7-H, no n=1024, no
  tuning, no promotion.
- Input: accepted internal D5 Model-F input root
  `workspace/v72p2d5_model_f_input/20260907_r1`; writer creates exactly the
  four frozen G2 files; no other phase runs.

## 5. Disposition

The three carried findings are adjudicated `ACCEPTED-AS-IS` with the
operator conditions in §1–§3. No code, config, threshold, or contract change
is required or made. This record closes the A1 "before X4 execution" finding
gate and clears the X4 Pre-EXECUTE block, subject to the recorded
conditions.
