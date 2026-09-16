# X2 operator return R1 — D7 X1–X4 master A1 authorized attempt (COMPLETE)

- Cycle: `V72P2D7-ROOT-CAUSE-RESET`
- Change: `formal-ir-d7-root-cause-and-route-reset`
- Packet: `.workbuddy/tasks/D7_X1_X4_EXECUTION_MASTER_R1_TASK_PACKET.md`
  §7 X2, §8, §9; Addendum A1
- Predecessor gate: X1 `X1_RERUN_VERIFIED`
  (`X1_RERUN_VERIFICATION_REVIEW_R1.md`), state `X1_COMPLETE_VERIFIED`
- Branch (unchanged, not switched): `formal-ir-v72p1-addendum-clean`;
  HEAD `278fdf0742255de0d030649965b6feffb11bc23d` (unchanged after attempt)
- Operator role: one authorized X2 attempt only; no retry/resume/cleanup/
  replacement/tuning, no self-acceptance, no later phase, no commit/push.

## 1. Pre-EXECUTE checklist (recorded before the process start)

| Item | Required | Observed |
|---|---|---|
| Branch / HEAD | `formal-ir-v72p1-addendum-clean` / `278fdf07…` | match |
| `x2_multigraph_execution_authorized` before start | false | false (then set true only for this attempt) |
| Target root `workspace/d7_r1_multigraph_20260913_r1` | ABSENT | ABSENT |
| Model-F input `workspace/v72p2d5_model_f_input/20260907_r1` | present | PRESENT (matches `MODEL_F_INPUT_FORMAL_ROOT`) |
| Exact command | frozen §7 X2 literal | match (§2) |
| Outer watchdog | `timeout -k 30 960` (900 s stored wall + 60 s guard) | applied |
| Per-call watchdog 120 s | owned externally | no separate in-process enforcement is possible inside the frozen single CLI invocation; every call wall is recorded in `call_records.csv` and checked post-hoc |
| RSS < 2 GiB | enforced by runner (`RSS_LIMIT_BYTES`, checked after each call) | enforced |
| Process ownership | recorded pid | `timeout` pid 506191 (`timeout_pid.txt`) |

## 2. Literal command, execution identity, exit

Master packet literal (Windows host):

```powershell
.venv\Scripts\python.exe scripts\v72p2d7_consistency_multigraph.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_r1_multigraph_20260913_r1 --wall-budget-s 900
```

Executed WSL form, exactly as launched (interpreter mapping per `AGENTS.md`
§8; same mapping as the X1 attempts):

```text
timeout -k 30 960 .venv/bin/python scripts/v72p2d7_consistency_multigraph.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_r1_multigraph_20260913_r1 --wall-budget-s 900
```

- cwd `/mnt/d/Code/HD-QKD_Polar_Comparison`; one foreground attempt, no detach.
- Start `2026-09-13T13:24:17+0800` / `2026-09-13T05:24:17Z`;
  end `2026-09-13T13:26:31+0800` / `2026-09-13T05:26:31Z`.
- Outer wall `134509 ms`; watchdog disposition
  `COMPLETED_BEFORE_OUTER_WATCHDOG`.
- Exit code directly captured from the `timeout` invocation: **0**.
- Transcripts `/tmp/opencode/x2_r1_20260913/`:
  - `meta.txt` md5 `3ee4ece4c1198b1b98513db8f501fbaa`
  - `stdout.txt` md5 `b1dd21a95aaa8e80c649626a5f846754`
  - `stderr.txt` md5 `d41d8cd98f00b204e9800998ecf8427e` (empty)
  - `attempt.sh`, `timeout_pid.txt` (506191), `status_before.txt`,
    `status_after.txt`, `status_diff.txt` (empty), `repo_files_touched.txt`
- stdout verbatim (one line):

```text
terminal=GRAPH_SENSITIVITY_OBSERVED out=workspace/d7_r1_multigraph_20260913_r1 calls=384
```

- stderr: empty. No residual `v72p2d7_consistency` process after the attempt.

## 3. Result root and file manifest (fresh, no overwrite)

Root `workspace/d7_r1_multigraph_20260913_r1` was ABSENT before the attempt
and was created by this run with exactly the seven frozen evidence files:

```text
across_graph_summary.json  4318 B
block_pairs.csv            7177 B
call_records.csv          72866 B
command_log.txt             271 B
graph_summary.csv           630 B
manifest.json              1559 B
report.md                   784 B
```

No-overwrite evidence: `manifest.no_overwrite: true`; pre/post
`git status --porcelain | sort` byte-identical (`status_diff.txt` 0 lines);
an independent file-window scan
(`find . -newer 2026-09-13T13:24:16+0800 ! -newer 2026-09-13T13:26:33+0800`,
excluding the new root) found **zero** other repo files modified during the
attempt; the Model-F input root had **0** files touched after start. No X2
root existed before, so no result could be overwritten.

## 4. Raw summary fields (no interpretation)

- `manifest.json`: `terminal: GRAPH_SENSITIVITY_OBSERVED`;
  `phase: X2_MULTIGRAPH_EXPLORATORY`;
  `scope: EXPLORATORY_SYNTHETIC_SINGLE_IMPLEMENTATION`;
  `decoder_calls: 384`; `wall_budget_s: 900.0`;
  `model_f_root: workspace/v72p2d5_model_f_input/20260907_r1`;
  `no_overwrite: true`.
- `across_graph_summary.json`: `terminal: GRAPH_SENSITIVITY_OBSERVED`;
  `decoder_calls: 384`; `slots_total: 384`; `slots_recorded: 384`;
  `stop_reason: None`; `stored_wall_seconds: 131.54233913499047`.
- `command_log.txt` raw terminal block:
  `terminal: GRAPH_SENSITIVITY_OBSERVED`, `decoder_calls: 384`,
  `slots_total: 384`, `stop_reason: None`.
- `call_records.csv` (384 rows):
  - per graph: g0 = 128, g1 = 128, g2 = 128;
  - per f: f1.0 = 192, f1.2 = 192; per (graph, f): 64 each (6 cells);
  - per arm: 96 each of `L1_MARGINAL`, `L1_TO_L2_TRANSFER`, `L2_MARGINAL`,
    `L2_TO_L1_TRANSFER`;
  - `invoked = True`: 384; crash statuses: 0; blocked statuses: 0;
    `finite = False`: 0; `provenance = CHECK_UPDATED`: 384;
  - statuses: `converged_no_syndrome` = 348, `converged_exact` = 36;
  - exact/syndrome separation present as distinct columns: `exact = True`
    36, `syndrome_ok = True` 36 (per (g, f1.2): g0 13, g1 10, g2 13);
  - max per-call `wall_s`: 0.49074098900018726 s (all ≤ 120 s); sum
    131.54233913499047 s (≤ 900 s);
  - max runner-recorded `rss_bytes`: 133185536 B ≈ 0.1240 GiB (< 2 GiB).
- Outer wall 134.5 s < 960 s watchdog.

## 5. Authorization-consumption record

- `x2_multigraph_execution_authorized: true` was set immediately before the
  single process start and restored `false` immediately after the attempt
  returned, before any validation or reporting (verified false).
- Consumption markers (additive in `cycle_state.yaml`):
  `x2_authorization_consumed: true`, `x2_process_starts: 1`,
  `x2_decoder_calls: 384`, `x2_terminal: GRAPH_SENSITIVITY_OBSERVED`,
  `x2_root: workspace/d7_r1_multigraph_20260913_r1`,
  `x2_operator_return: docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/X2_OPERATOR_RETURN_R1.md`,
  `multigraph_executed: true`, `decoder_executed: true`.
- X3 (`x3_reference_ladder_authorized`), X4
  (`x4_g2_execution_authorized`), D7-H, G1 rerun, real data, n=1024, tuning,
  promotion: untouched, false, unconsumed
  (`x3/x4_authorization_consumed: false`).

## 6. No later phase, no retry, no commit

- Exactly one X2 process start; no retry, resume, root replacement, seed
  substitution, parameter change, or cleanup.
- X3/X4 frozen roots remain ABSENT:
  `workspace/d7_r1_reference_ladder_20260913_r1`,
  `workspace/v72p2d5_g2/20260906_r1`. No G1/D7-H/real/n=1024 action.
- No commit, no staging, no push; branch and HEAD unchanged.

## 7. Terminal class and next gate

Raw terminal `GRAPH_SENSITIVITY_OBSERVED` with full 384/384 coverage and no
`stop_reason` — a scientific/coverage terminal, not an
engineering/resource/crash/incomplete class. This operator records raw
outputs only and does not accept the phase. Per A1, the next gate is an
independent X2 Pre-RESULT review; X3 remains unauthorized.

Scope notes (non-blocking, for the reviewer):

- The pre-execution guard `test_frozen_execution_roots_remain_absent` in
  `test_v72p2d7_r1_x1x4_entrypoints.py` pins the now-superseded absence of
  the X2 root and will fail while `workspace/d7_r1_multigraph_20260913_r1`
  exists.
- The marker test `test_cycle_state_marker_and_all_flags_false` pins
  `X1_COMPLETE_VERIFIED` / `X2_EXECUTION` as required for the Part A X1
  closeout and is now superseded by the X2 state advancement; it will fail
  until a scoped update at the next state-changing boundary.

Both updates were outside this packet's authorized edits and were not
performed here; the Part A green runs (1 passed marker, 57 passed suite) were
recorded before the X2 attempt.
