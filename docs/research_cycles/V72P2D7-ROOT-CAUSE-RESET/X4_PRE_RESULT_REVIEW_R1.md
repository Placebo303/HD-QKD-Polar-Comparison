# X4 independent Pre-RESULT review R1

- Cycle: `V72P2D7-ROOT-CAUSE-RESET`
- Change: `formal-ir-d7-root-cause-and-route-reset`
- Packet: `.workbuddy/tasks/D7_X1_X4_EXECUTION_MASTER_R1_TASK_PACKET.md`
  (§7 X4, §8, §9); Addendum A1 (`## Required independent reviews`)
- Review subject: `X4_OPERATOR_RETURN_R1.md` and the immutable X4 evidence
  root `workspace/v72p2d5_g2/20260906_r1` (4 files, frozen), read against
  the X4 Pre-EXECUTE adjudication
  (`X4_PREEXECUTE_ADJUDICATION_R1.md`, conditions (a)/(b)/(c)) and the
  transcripts in `/tmp/opencode/x4_r1_20260913/`.
- Review mode: independent read-only recomputation from the raw
  `results.json` / `table.csv` / `report.md` / `execution_summary.json` and
  the attempt transcripts; nothing was re-executed, repaired, retried,
  cleaned, staged, or committed.
- Branch: `formal-ir-v72p1-addendum-clean`; HEAD
  `278fdf0742255de0d030649965b6feffb11bc23d`.
- Recording note: the operator transcribed the independent review's frozen
  findings into this record and re-verified the raw counts below against the
  X4 artifacts; the operator did not perform or accept the review.

## 1. Verdict

**`X4_PRE_RESULT_REVIEW_PASS`**

## 2. Raw recomputation summary

Attempt identity (from `/tmp/opencode/x4_r1_20260913/`):

- Exact launched command
  `timeout -k 30 3660 .venv/bin/python scripts/v72p2d7_consistency_multigraph.py --g2`
  from cwd `/mnt/d/Code/HD-QKD_Polar_Comparison`; one foreground attempt,
  start `2026-09-13T14:33:05+0800` / `2026-09-13T06:33:05Z`, end
  `2026-09-13T15:08:48+0800` / `2026-09-13T07:08:48Z`.
- Exit code **0**; outer wall **2143830 ms** (2143.83 s); watchdog
  disposition `COMPLETED_BEFORE_OUTER_WATCHDOG`; `timeout` pid **548229**,
  stall-monitor pid **548227** (launcher pid 548208).
- stdout verbatim (one line):
  `grade=G2_CURRENT_CONFIGURATION_FAILED out=.../workspace/v72p2d5_g2/20260906_r1 decoder_calls=1320`;
  stderr 0 B; no residual process after the attempt.
- Stall monitor (adjudication condition (c)): log = **430 log lines =
  429 SAMPLE + 1 MONITOR_START; 0 stalls**; `idle_s=0.0` at every SAMPLE;
  `grep -c STALL_MONITOR_TERMINATED_VOID` = **0**; no `STALL_DETECTED`,
  `KILL_TREE_*`, or void markers.

Coverage recomputation (raw `table.csv` + `results.json`; frozen matrix
n=256, f list `[1.0, 1.1, 1.2]`, 200 blocks per f, seeds
2026091000..2026091199, oracle subset 40 per f):

| f | attempted | L1 exact | L2 exact | L1 syndrome | L2 syndrome | provenance CHECK_UPDATED | transfer invoked | transfer blocked | oracle exact | calls |
|---|---|---|---|---|---|---|---|---|---|---|
| 1.0 | 200 | 0 | 0 | 0 | 0 | 200 | 200 | 0 | 0 | 440 |
| 1.1 | 200 | 0 | 0 | 0 | 0 | 200 | 200 | 0 | 0 | 440 |
| 1.2 | 200 | 0 | 0 | 0 | 0 | 200 | 200 | 0 | 0 | 440 |
| **total** | **600** | **0** | **0** | **0** | **0** | **600** | **600** | **0** | **0** | **1320** |

- Call accounting: per f `200 x 2 + 40 = 440`; 3 f x 440 = **1320** = the
  frozen §7 maximum (no over-ceiling path); stored `decoder_calls: 1320`.
- Exact/syndrome separation preserved: app L1/L2 exact and syndrome counts
  are 0/0 per f and are not merged into each other or into success.
- `monotonic: true`; `crashes: 0`; `nonfinite: 0`; `block_length: 256`;
  `frozen_rows` exactly `1.0 -> m1 196 / m2 172`, `1.1 -> 215 / 189`,
  `1.2 -> 235 / 206`.

Grading rule and evaluation (from
`comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`,
`_grade_g2`, lines 2385-2398, `G2_TOTAL_BUDGET_S = 3600.0`,
`G2_RSS_BUDGET_BYTES = 2 * 1024**3`):

1. `nonfinite > 0` -> `IMPLEMENTATION_OR_NUMERICAL_BLOCKED`; observed
   nonfinite **0** -> not blocked.
2. `wall_seconds > 3600` -> blocked; observed stored wall
   **2141.9420988290076 s <= 3600** -> not blocked.
3. `peak_rss_bytes >= 2147483648` -> blocked; observed
   **159182848 B (~0.1483 GiB) < 2 GiB** -> not blocked.
4. `top_rate >= 0.9 and monotonic` -> `G2_SYNTHETIC_QUALIFIED`; observed
   last-f (`f=1.2`) `app_exact_rate` **0.0** -> not qualified.
5. `top_rate >= 0.5` -> `G2_INCONCLUSIVE`; observed **0.0 < 0.5** -> no.
6. Otherwise `GRADE_FAILED` = **`G2_CURRENT_CONFIGURATION_FAILED`** — the
   recomputed evaluation and the stored grade agree; `passed: false`;
   `runtime_status: G2_RUNTIME_UNVERIFIED`; only the frozen four-state
   vocabulary was emitted.

Root and file manifest (fresh, created by the run):

```text
results.json              5207 B  md5 036a5e72f475f2860c123967acfb7cbc
table.csv                  362 B  md5 d3140f6d27de7f41ee7496792df68d61
report.md                  277 B  md5 586c557c2fd2f534621484829d0fc2c8
execution_summary.json     416 B  md5 b770193d17f5ec102bb1af53c2e79b31
```

- Exactly the frozen four-file G2 schema; `formal_root:
  workspace/v72p2d5_g2/20260906_r1`, `phase: g2`;
  `output_files` = the four files.

## 3. No-overwrite and adjudication conditions

No-overwrite: pre-attempt root and parent ABSENT (`preexecute.txt`);
pre/post `git status --porcelain | sort` byte-identical (both md5
`df682a08b9d224e9999ef7f1b23033c5`, `status_diff.txt` 0 lines); independent
window scan over the attempt window outside the new root found zero
modified files (30 permission-denied legacy pytest/workspace ACL
directories only, no file paths); the bridge `FileExistsError` pre-check
and the writer's own `FileExistsError` guard are intact; the Model-F input
root `workspace/v72p2d5_model_f_input/20260907_r1` and all earlier roots
were untouched.

Adjudication conditions:

- (a) repo-rooted existence check vs CWD-relative writer: the attempt ran
  from the repository root, so both resolve to the exact frozen path; the
  created root is at
  `/mnt/d/Code/HD-QKD_Polar_Comparison/workspace/v72p2d5_g2/20260906_r1`.
- (b) non-dict runner coercion: not triggered — the CLI printed a
  four-state grade and exited 0 (no `G2 bridge refused:` and no exit 3).
- (c) per-call 120 s: **satisfied as adjudicated** — the per-call budget is
  externally owned and is not machine-observable in the frozen G2 evidence
  (no per-call wall field or per-call timestamps); the operator-owned
  stall monitor (`stall_monitor.py`, `--stall-s 120`, SIGTERM then
  SIGKILL) ran for the whole attempt with continuous CPU progress
  (`idle_s=0.0` at all 429 samples, 0 stall markers), and the outer
  `timeout -k 30 3660` watchdog completed before expiry
  (`COMPLETED_BEFORE_OUTER_WATCHDOG`). No per-call 120 s compliance beyond
  the recorded aggregate evidence is claimed.

## 4. Boundary confirmations

- Terminal classification: grade `G2_CURRENT_CONFIGURATION_FAILED` from the
  frozen four-state vocabulary with exit 0, four frozen files at the exact
  frozen root, and no stall — an attempt-completed coverage/engineering
  outcome with a valid raw grade, not a refusal/timeout/artifact/root
  mismatch blocker. Exactly one process start; no retry, resume,
  replacement, tuning, or cleanup.
- Authorization: `x4_g2_execution_authorized` set true 14:32:44 and
  restored **false** as the operator's next action (verified 15:09:18, no
  decoder work in between); all other execution flags false
  (`x1`/`x2`/`x3`/`d7h`/`g1_rerun`/`result_solidification`); A2
  remediation grant unused; D5 `g2_execution_authorized` and the other
  eight D5 execution flags remain false.
- Repository boundary: branch `formal-ir-v72p1-addendum-clean`, HEAD
  `278fdf07` unchanged; **no commit, no staging, no push**; Model-F input
  root, historical evidence, and earlier roots byte-identical.
- Independent test rerun (fresh basetemp, repo venv, all decoders
  fake/injected — zero production decoder calls):

  ```text
  .venv/bin/python -m pytest -p no:cacheprovider -q \
    --basetemp=workspace/v72p2d7_x1x4_test_x4final_1789285046_557045 \
    comparison_bench/tests/test_v72p2d7_r1_x1x4_entrypoints.py
  ```

  Result: **57 passed**, exit **0**.

## 5. Claim ceiling

- The record is a raw four-state G2 grade at the frozen matrix; no
  diagnostic conclusion beyond it is drawn. No `ROUTE_DEAD`, no n=1024,
  no G1 rerun, no D7-H, no tuning, no real-data, and no promotion claim is
  made; `G2_RUNTIME_UNVERIFIED` is retained and no
  `IMPLEMENTATION_OR_NUMERICAL_BLOCKED` was emitted. The failing grade is a
  current-configuration length-discrimination diagnostic only; phase
  acceptance and any route decision belong to the main thread.

## 6. Non-blocking notes (for the main thread)

1. Sample-count wording: `X4_OPERATOR_RETURN_R1.md` previously said
   "430 samples"; corrected in this closeout to the precise
   "430 log lines = 429 SAMPLE + 1 MONITOR_START; 0 stalls". The raw log
   has exactly 430 lines and 0 stall markers, so this is a wording
   precision fix only.
2. Stale pre-execution markers: `cycle_state.yaml` still carries
   `g2_status: G2_PENDING_NOT_FAILED_NOT_SKIPPED_NOT_SUPERSEDED` and
   `g2_runtime_status: G2_RUNTIME_UNVERIFIED` inherited from
   `G2_STATUS_NOTE_R1.md`, while the executed attempt now supplies
   `G2_CURRENT_CONFIGURATION_FAILED` at the D7 level. Updating those
   D5-derived markers is a main-thread acceptance decision; this closeout
   deliberately leaves them unchanged (additive edits only).
3. Runtime projection: P0's 485 s projection (already rejected as a G2
   runtime estimate by `G2_STATUS_NOTE_R1.md`) vs the measured stored wall
   2141.94 s (outer 2143.83 s); the measured value is authoritative and
   the projection was not used for any decision. The measurement is within
   the 3600 s budget.
4. Memory/troubleshooting updates (X4 outcome and these notes) are
   deferred to memory triage at the phase boundary.

## 7. Disposition

X4 independently reviewed as `X4_PRE_RESULT_REVIEW_PASS`. X4 is complete
and verified; state advances to
`X4_COMPLETE_VERIFIED_AWAITING_MAIN_THREAD_ROUTE_DECISION` with
`next_gate: MAIN_THREAD_ROUTE_DECISION_D7H`. This record grants no
authorization, accepts no scientific claim, does not authorize D7-H,
n=1024, solidification, or promotion, and consumes no phase authorization.
