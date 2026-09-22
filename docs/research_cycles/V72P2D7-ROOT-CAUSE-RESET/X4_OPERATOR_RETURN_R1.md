# X4 operator return R1 — D7 X1–X4 master A1 attempt (COMPLETE)

- Cycle: `V72P2D7-ROOT-CAUSE-RESET`
- Change: `formal-ir-d7-root-cause-and-route-reset`
- Packet: `.workbuddy/tasks/D7_X1_X4_EXECUTION_MASTER_R1_TASK_PACKET.md`
  (§7 X4, §8, §9); Addendum A1; remediation grant A2
  (`A2_X2_X4_REMEDIATION_AUTHORIZATION_R1.md`)
- Predecessor gates: X3 Pre-RESULT review `PASS`
  (`X3_PRE_RESULT_REVIEW_R1.md`), state `X3_COMPLETE_VERIFIED`; X4
  Pre-EXECUTE adjudication `ACCEPTED_AS_IS_WITH_CONDITIONS`
  (`X4_PREEXECUTE_ADJUDICATION_R1.md`)
- Branch (unchanged, not switched): `formal-ir-v72p1-addendum-clean`;
  HEAD `278fdf0742255de0d030649965b6feffb11bc23d` (unchanged after attempt)
- Operator role: one authorized X4 attempt only; no retry/resume/cleanup/
  replacement/tuning, no self-acceptance, no later phase, no commit/push.

## 1. Pre-EXECUTE block (recorded before the process start, 14:30:39 +0800)

| Item | Required | Observed |
|---|---|---|
| Branch / HEAD | `formal-ir-v72p1-addendum-clean` / `278fdf07…` | match |
| `x4_g2_execution_authorized` before start | false | false (set true 14:32:44 only for this attempt) |
| Frozen root `workspace/v72p2d5_g2/20260906_r1` | ABSENT | ABSENT |
| Frozen parent `workspace/v72p2d5_g2` | ABSENT | ABSENT |
| CWD | repository root | `/mnt/d/Code/HD-QKD_Polar_Comparison` |
| Exact command | frozen §7 X4 literal | match (§2) |
| Outer watchdog | `timeout -k 30 3660` (3600 s stored budget + 60 s guard) | applied; owned by this operator |
| Per-call 120 s | externally owned; NOT machine-observable in the frozen G2 evidence set (no per-call wall field) | recorded; covered by §1.1 stall monitor |
| RSS < 2 GiB | grader blocks at `G2_RSS_BUDGET_BYTES` | applied by grader |
| D5 flags | all false | all false (9 keys, raw output in `preexecute.txt`) |
| D7 `d7h_execution_authorized` / G1 rerun / tuning | false | false |
| Model-F input root | present | `workspace/v72p2d5_model_f_input/20260907_r1` |

Adjudication conditions (a)/(b)/(c) applied: the attempt ran from the repo
root so the repo-rooted existence check and the CWD-relative writer coincide
at the exact frozen path; the production runner path is the dict-returning
`run_g2_synthetic` (a refusal/failure would have exited 3, not graded); the
external 120 s per-call budget is operator-owned and not machine-observable
in the frozen evidence (only aggregate wall/RSS are), covered by the stall
monitor below.

### 1.1 Process ownership and stall monitoring (exact)

- Attempt launcher: `attempt.sh` (pid recorded via `launcher_pid.txt`), which
  ran exactly one foreground frozen command inside a dedicated session
  (`setsid`, launched 14:32:55 +0800 solely so a tool-call cap cannot kill
  the attempt; the operator polled it; no second attempt and no second
  process start).
- `timeout` pid **548229** (`timeout_pid.txt`); monitor pid **548227**
  (`stall_monitor_pid.txt`).
- Stall monitor (adjudication condition c):
  `.venv/bin/python /tmp/opencode/x4_r1_20260913/stall_monitor.py --pidfile … --log … --stall-s 120`
  — operator-owned, samples the attempt process tree's summed CPU ticks
  every 5 s; if no CPU progress for >120 s it SIGTERMs/SIGKILLs the tree and
  marks the attempt void.
- Monitor self-check before arming: CPU-progressing process → clean
  `MONITOR_EXIT_PROCESS_GONE` exit 0; stalled `sleep` → `STALL_DETECTED` →
  `KILL_TREE_SIGTERM` → `STALL_MONITOR_TERMINATED_VOID` (no leftover).
- Monitor result for the attempt: **430 log lines = 429 SAMPLE + 1
  MONITOR_START; 0 stalls**; continuous CPU progress (`idle_s=0.0` at every
  SAMPLE), 0 stall markers (`grep -c STALL_MONITOR_TERMINATED_VOID` = 0);
  the monitor was stopped by `attempt.sh` after the command returned.
- Per-call 120 s statement: the frozen X4 evidence
  (`results.json`, `table.csv`, `report.md`, `execution_summary.json`) has
  no per-call wall field or per-call timestamps, so no per-call 120 s
  statement is machine-observable; the machine-observable guards are the
  outer watchdog and the grader's wall/RSS block conditions.

## 2. Literal command, execution identity, exit

Master packet literal (Windows host):

```powershell
.venv\Scripts\python.exe scripts\v72p2d7_consistency_multigraph.py --g2
```

Executed WSL form, exactly as launched:

```text
timeout -k 30 3660 .venv/bin/python scripts/v72p2d7_consistency_multigraph.py --g2
```

- cwd `/mnt/d/Code/HD-QKD_Polar_Comparison`; one attempt, no detach of the
  command itself, no retry/resume.
- Flag set true 14:32:44 +0800; start `2026-09-13T14:33:05+0800` /
  `2026-09-13T06:33:05Z`; end `2026-09-13T15:08:48+0800` /
  `2026-09-13T07:08:48Z`.
- Outer wall `2143830 ms` (2143.83 s); watchdog disposition
  `COMPLETED_BEFORE_OUTER_WATCHDOG`.
- Exit code directly captured from the `timeout` invocation: **0**.
- Transcripts `/tmp/opencode/x4_r1_20260913/`: `meta.txt`,
  `stdout.txt` (130 B), `stderr.txt` (0 B), `attempt.sh`,
  `stall_monitor.py`, `stall_monitor.log` (430 log lines = 429 SAMPLE + 1
  MONITOR_START; 0 stalls),
  `stall_monitor_pid.txt` (548227), `timeout_pid.txt` (548229),
  `launcher_pid.txt`, `preexecute.txt`, `flag_set_at.txt`,
  `flag_restore.txt`, `status_before.txt`, `status_after.txt`,
  `status_diff.txt` (0 lines), `repo_files_touched.txt` (vacuous, 0 B),
  `window_scan_outside_x4root.txt`, `final_verification.txt`,
  `x4_raw_analysis.txt`, `attempt_console.txt`, `post_x4_test_run.txt`.
- stdout verbatim (one line):

```text
grade=G2_CURRENT_CONFIGURATION_FAILED out=/mnt/d/Code/HD-QKD_Polar_Comparison/workspace/v72p2d5_g2/20260906_r1 decoder_calls=1320
```

- stderr: empty. No residual `v72p2d7_consistency` / `--g2` process after
  the attempt (`ps` check, `NO_RESIDUAL_PROCESS`).

## 3. Result root and file manifest (fresh, no overwrite)

Root `workspace/v72p2d5_g2/20260906_r1` was ABSENT before the attempt (its
parent also absent) and was created by this run with exactly the four frozen
G2 files:

```text
results.json              5207 B  md5 036a5e72f475f2860c123967acfb7cbc
table.csv                  362 B  md5 d3140f6d27de7f41ee7496792df68d61
report.md                  277 B  md5 586c557c2fd2f534621484829d0fc2c8
execution_summary.json     416 B  md5 b770193d17f5ec102bb1af53c2e79b31
```

- `results.json` / `execution_summary.json`: `formal_root:
  workspace/v72p2d5_g2/20260906_r1`, `phase: g2`, `grade:
  G2_CURRENT_CONFIGURATION_FAILED`, `passed: false`,
  `runtime_status: G2_RUNTIME_UNVERIFIED`, `output_files` = the four files.
- No-overwrite evidence: pre-attempt root and parent ABSENT; the bridge
  refuses (`FileExistsError`) before the runner if the repo-rooted root
  exists and the writer independently raises `FileExistsError` on an
  existing directory; pre/post `git status --porcelain | sort` byte-identical
  (`status_diff.txt` 0 lines); independent window scan over the attempt
  window outside the new root found **zero** modified files (30
  permission-denied legacy pytest/workspace ACL directories only, no file
  paths); the Model-F input root and all earlier roots were untouched.
  `repo_files_touched.txt` from the attempt script is vacuous again (0 B;
  known find/mtime limitation on this mount) — the no-write case rests on
  the absent-root pre-check, the status diff, and the window scan.

## 4. Raw results (no interpretation)

Coverage and call accounting:

- `decoder_calls: **1320**` (== the frozen maximum 1320; no over-ceiling
  path). Per f: 200 blocks x 2 calls (L1 + L2/transfer) + 40 oracle calls =
  **440**; 3 f x 440 = 1320.
- `block_length: 256`; `f_list: [1.0, 1.1, 1.2]`; frozen rows exactly
  `1.0 -> m1 196 / m2 172`, `1.1 -> m1 215 / m2 189`, `1.2 -> m1 235 /
  m2 206`; seeds 2026091000..2026091199 (200).
- All three f rows: `attempted 200`, `app_exact_count 0`
  (`app_exact_rate 0.0`, `app_failure_fraction 1.0`),
  `oracle_exact_count 0`, `app_l1_exact_count 0`, `app_l2_exact_count 0`,
  `app_l1_syndrome_ok_count 0`, `app_l2_syndrome_ok_count 0`,
  `provenance_check_updated_count 200`, `transfer_invoked_count 200`,
  `transfer_blocked_count 0`.
- `monotonic: true`; `crashes: 0`; `nonfinite: 0`.

Grade (four-state vocabulary, raw):

- **`G2_CURRENT_CONFIGURATION_FAILED`**; `passed: false`; the other three
  vocabulary states were not emitted. Raw counters recorded above; no
  diagnostic conclusion is drawn here.

Budgets:

- Stored wall **2141.9420988290076 s** (<= 3600 s); outer wall 2143.83 s
  (< 3660 s watchdog); peak RSS **159182848 B** (~0.1483 GiB < 2 GiB);
  single-call budget externally owned (see §1.1).

## 5. Authorization-consumption record

- `x4_g2_execution_authorized: true` was set immediately before the single
  process start (14:32:44) and restored `false` as the operator's next
  action after the attempt returned (verified 15:09:18, no decoder work in
  between; the first residual check in `flag_restore.txt` self-matched its
  own `pgrep` command line, and the precise `ps`/`grep -v grep` check is
  `NO_RESIDUAL_PROCESS`).
- Consumption markers (additive in `cycle_state.yaml`):
  `x4_authorization_consumed: true`, `x4_process_starts: 1`,
  `x4_decoder_calls: 1320`,
  `x4_root: workspace/v72p2d5_g2/20260906_r1`,
  `x4_grade: G2_CURRENT_CONFIGURATION_FAILED`,
  `x4_terminal: G2_CURRENT_CONFIGURATION_FAILED`,
  `x4_operator_return: …/X4_OPERATOR_RETURN_R1.md`, `g2_executed: true`,
  `x1_x4_authorization_consumed: ALL_CONSUMED_X1_X2_X3_X4_EXECUTED`.
- The A2 remediation grant (one scoped fix + one second attempt on a
  first-attempt failure) was **not** used: this first X4 attempt completed
  with a frozen four-state grade and readable evidence; no remediation was
  needed or performed.
- D7-H (`d7h_execution_authorized`), G1 rerun, real data, n=1024, tuning,
  promotion: untouched, false, unconsumed. All nine D5 execution flags
  remain false. `g1_rerun_authorized`, `result_solidification_authorized`,
  `scientific_promotion` remain false.

## 6. No later phase, no retry, no commit

- Exactly one X4 process start; no retry, resume, root replacement, seed
  substitution, parameter change, or cleanup. The root is retained in place
  unmodified.
- No G1/D7-H/real/n=1024 action; no other D5 phase; no new root besides the
  frozen G2 root.
- No commit, no staging, no push; branch and HEAD unchanged.

## 7. Terminal class and next gate

Raw outcome: exit 0, four frozen files at the exact frozen root, grade
`G2_CURRENT_CONFIGURATION_FAILED` (one of the four frozen states), outer
watchdog disposition `COMPLETED_BEFORE_OUTER_WATCHDOG`, no stall, budgets
within limits — an attempt-completed engineering/coverage outcome with a
valid scientific grade, not a refusal/timeout/artifact/root-mismatch
blocker. This operator records raw outputs only and does not accept the
phase. Per A1, the next gate is an independent X4 Pre-RESULT review; X4 is
consumed, D7-H remains unauthorized.

## 8. Post-attempt test updates and run

Superseded tests updated without weakening their checks
(`comparison_bench/tests/test_v72p2d7_r1_x1x4_entrypoints.py`):

- `test_cycle_state_marker_and_all_flags_false`: still asserts every
  execution flag false and `historical_evidence:
  RETAINED_BYTE_IDENTICAL`; lifecycle now
  `state`/`terminal = X4_EXECUTION_COMPLETE_PENDING_INDEPENDENT_REVIEW`,
  `next_gate = X4_INDEPENDENT_PRERESULT_REVIEW`.
- `test_frozen_execution_roots_remain_absent` ->
  `test_execution_roots_state_after_x4`: all three executed roots
  (`d7_r1_multigraph_20260913_r1`, `d7_r1_reference_ladder_20260913_r1`,
  `v72p2d5_g2/20260906_r1`) must be present directories.
- `test_x4_cli_rejects_true_d5_flag_without_production_run`: the former
  pre-X4 root-absence assertion is replaced by a frozen-root snapshot check
  (same file set and mtimes before/after the refused invocation); the
  refusal (`rc == 3`, "must remain false") and no-production-run
  (`run_g2_fn=_boom`) asserts are unchanged.

Command (fresh basetemp, repo venv, no production decoder path in any test;
all decoders fake/injected):

```text
.venv/bin/python -m pytest -p no:cacheprovider -q \
  --basetemp=workspace/v72p2d7_x1x4_test_x4post_1789283649_550294 \
  comparison_bench/tests/test_v72p2d7_r1_x1x4_entrypoints.py
```

Result: **57 passed**, exit **0** (log
`/tmp/opencode/x4_r1_20260913/post_x4_test_run.txt`).

## 9. A2 remediation statement (user-required disclosure)

No implementation remediation was used for X4: the first attempt completed
with a frozen four-state grade, so the A2 one-fix-one-second-attempt grant
was not triggered (mirrors X3). Files changed at this boundary: this
return, `X3_PRE_RESULT_REVIEW_R1.md` (new review record),
`X4_PREEXECUTE_ADJUDICATION_R1.md` (new adjudication record),
`cycle_state.yaml` (additive state/markers only), and
`comparison_bench/tests/test_v72p2d7_r1_x1x4_entrypoints.py` (three
superseded lifecycle/root test expectations only). None of these changes
any matrix, seed, row, arm, threshold, root, command, budget, provenance
semantic, terminal, or claim ceiling, and none can affect the exploration
goals: the X4 G2 length-discrimination measurement rests entirely on the
raw 1320-call evidence above, and X1/X2/X3 records are untouched.
