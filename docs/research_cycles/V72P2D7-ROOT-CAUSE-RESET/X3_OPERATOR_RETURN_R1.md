# X3 operator return R1 — D7 X1–X4 master A1 attempt (COMPLETE)

- Cycle: `V72P2D7-ROOT-CAUSE-RESET`
- Change: `formal-ir-d7-root-cause-and-route-reset`
- Packet: `.workbuddy/tasks/D7_X1_X4_EXECUTION_MASTER_R1_TASK_PACKET.md`
  (§7 X3, §8, §9); Addendum A1; remediation grant A2
  (`A2_X2_X4_REMEDIATION_AUTHORIZATION_R1.md`)
- Predecessor gate: X2 `X2_PRE_RESULT_REVIEW_PASS`
  (`X2_PRE_RESULT_REVIEW_R1.md`), state `X2_COMPLETE_VERIFIED`
- Branch (unchanged, not switched): `formal-ir-v72p1-addendum-clean`;
  HEAD `278fdf0742255de0d030649965b6feffb11bc23d` (unchanged after attempt)
- Operator role: one authorized X3 attempt only; no retry/resume/cleanup/
  replacement/tuning, no self-acceptance, no later phase, no commit/push.

## 1. Pre-EXECUTE checklist (recorded before the process start)

| Item | Required | Observed |
|---|---|---|
| Branch / HEAD | `formal-ir-v72p1-addendum-clean` / `278fdf07…` | match |
| `x3_reference_ladder_authorized` before start | false | false (then set true only for this attempt) |
| Target root `workspace/d7_r1_reference_ladder_20260913_r1` | ABSENT | ABSENT (13:49:42 / 13:50:40 pre-checks) |
| X2 root `workspace/d7_r1_multigraph_20260913_r1` | present and frozen | PRESENT; 7 files, mtimes 13:26:31, unchanged through the attempt |
| X4 root `workspace/v72p2d5_g2/20260906_r1` | absent | ABSENT |
| Exact command | frozen §7 X3 literal | match (§2) |
| Outer watchdog | `timeout -k 30 3660` (3600 s stored wall + 60 s guard) | applied |
| Per-call watchdog 480 s | owned externally by this operator; per-call wall recorded per row | recorded (max 1.7976 s) |
| RSS < 2 GiB | enforced by runner (`RSS_LIMIT_BYTES`, checked per call) | enforced |
| Process ownership | recorded pid | `timeout` pid 538493 (`timeout_pid.txt`) |

True-condition binding probe (Phase P acceptance requirement, before
authorization consumption): from the repo root with `.venv/bin/python`, the
core module was loaded in the real production layout exactly as the CLI
runner does (`comparison_bench/src` on `sys.path`, module by file path) and
`bind_reference_ladder_decoders()` was called against the real v35 module
with sentinel decoder functions installed to prove zero invocations.

```text
$ .venv/bin/python /tmp/opencode/x3_r1_20260913/bind_probe.py
BIND_PROBE_OK
keys=FLOODING_90,ROW_LAYERED_360,ROW_LAYERED_90
signatures=(h,prior,syndrome) x3
closure_v35_identity=true
row90_kwargs=(max_iter=90,damping_alpha=1.0,warm_beliefs=None,field=None)
row360_kwargs=(max_iter=360,damping_alpha=1.0,warm_beliefs=None,field=None)
flooding90_kwargs=(max_iter=90,field=None)
decoder_invocations=0
PROBE_EXIT=0
```

The probe created no file and no root (X3 root ABSENT after it; repo
`git status --porcelain | sort` byte-identical), and consumed no
authorization (`x3_reference_ladder_authorized` still false). Focused
Pre-EXECUTE tests (fake-injected, no production path; fresh basetemp
`workspace/v72p2d7_x1x4_test_x3pre_1789278661_12124`): `py_compile` OK;
`pytest -k "x3 or rl_bind"` **21 passed, 36 deselected**, exit 0.

## 2. Literal command, execution identity, exit

Master packet literal (Windows host):

```powershell
.venv\Scripts\python.exe scripts\v72p2d7_consistency_multigraph.py --reference-ladder --x2-root workspace/d7_r1_multigraph_20260913_r1 --out-root workspace/d7_r1_reference_ladder_20260913_r1 --wall-budget-s 3600
```

Executed WSL form, exactly as launched (interpreter mapping per `AGENTS.md`
§8; same mapping as the X1/X2 attempts):

```text
timeout -k 30 3660 .venv/bin/python scripts/v72p2d7_consistency_multigraph.py --reference-ladder --x2-root workspace/d7_r1_multigraph_20260913_r1 --out-root workspace/d7_r1_reference_ladder_20260913_r1 --wall-budget-s 3600
```

- cwd `/mnt/d/Code/HD-QKD_Polar_Comparison`; one foreground attempt, no
  detach.
- Flag set true 13:51:44 +0800; start `2026-09-13T13:51:53+0800` /
  `2026-09-13T05:51:53Z`; end `2026-09-13T13:58:07+0800` /
  `2026-09-13T05:58:07Z`.
- Outer wall `374622 ms`; watchdog disposition
  `COMPLETED_BEFORE_OUTER_WATCHDOG`.
- Exit code directly captured from the `timeout` invocation: **0**.
- Transcripts `/tmp/opencode/x3_r1_20260913/`:
  - `meta.txt` md5 `1d76664897ca4f0c9adfc4281e148c70`
  - `stdout.txt` md5 `f90a534a5ce5c914fbb4f0e0dd4c6490` (177 bytes)
  - `stderr.txt` md5 `d41d8cd98f00b204e9800998ecf8427e` (empty)
  - `bind_probe.py` md5 `fa81a1d6320d7591c0c8d9a78c8e32e6`; output
    `bind_probe_output.txt` md5 `7e5dab2132b0372142ebff3c86053edf`
  - `attempt.sh`, `preexecute.txt`, `flag_set_at.txt`, `timeout_pid.txt`
    (538493), `status_before.txt`, `status_after.txt`, `status_diff.txt`
    (empty), `root_artifacts.txt`, `x3_raw_analysis.txt`,
    `no_overwrite_evidence.txt`
- stdout verbatim (one line):

```text
terminal=X3_REFERENCE_LADDER_COMPLETED out=/mnt/d/Code/HD-QKD_Polar_Comparison/workspace/d7_r1_reference_ladder_20260913_r1 selected=156 ladder_calls=468 reconstruction_calls=4
```

- stderr: empty. No residual `v72p2d7_consistency` process after the attempt.

## 3. Result root and file manifest (fresh, no overwrite)

Root `workspace/d7_r1_reference_ladder_20260913_r1` was ABSENT before the
attempt and was created by this run with exactly the seven frozen evidence
files:

```text
command_log.txt               311 B
ladder_records.csv         101172 B
manifest.json                1288 B
paired_summary.csv          20640 B
report.md                     503 B
selected_records.csv        24318 B
summary.json                 1218 B
```

No-overwrite evidence: `manifest.no_overwrite: true`; pre/post
`git status --porcelain | sort` byte-identical (md5
`df682a08b9d224e9999ef7f1b23033c5`, 2104 entries; `status_diff.txt` 0 lines);
an independent file-window scan
(`find . -newer 2026-09-13T13:51:53+0800 ! -newer 2026-09-13T13:58:10+0800`,
excluding the new root) found **zero** other repo files modified during the
attempt; the X2 root's seven files retain their 13:26:31 mtimes and the
Model-F input root was not touched. `selected_records.csv` carries a 13:51
mtime (written before any decoder was bound), the other six files 13:58.

## 4. Raw results (no interpretation)

Manifest / summary / command log:

- `manifest.json` and `summary.json`: `terminal:
  X3_REFERENCE_LADDER_COMPLETED`; `phase: X3_REFERENCE_LADDER`;
  `claim_label`/`scope`: `STRONG_REFERENCE_DIAGNOSTIC`; `stop: null`;
  `no_overwrite: true`; `baseline_gate` text as frozen;
  `model_f_root: workspace/v72p2d5_model_f_input/20260907_r1`.
- Budgets: `stored_wall_seconds: 372.2475444819138` (<= 3600);
  `peak_rss_bytes: 134381568` (~0.1252 GiB < 2 GiB); max per-call
  `wall_s`: 1.7975539110047976 s (<= 480 s).

Selector and call accounting:

- Selected records **S = 156** (all `f = 1.2`, `invoked = true`,
  non-crash, `finite = true`, `exact = false`; no dedup/replacement):
  per graph 51 / 54 / 51; per role 87 `SOURCE` / 69 `TARGET`; per arm
  `L1_MARGINAL` 39, `L1_TO_L2_TRANSFER` 40, `L2_MARGINAL` 48,
  `L2_TO_L1_TRANSFER` 29; stored rows exact/syndrome false for all 156.
- Plan (written in `manifest.json` before binding): `selected_records:
  156`, `ladder_calls: 468`, `reconstruction_calls: 4`, `total_calls: 472`.
- Actual calls: ladder **3S = 468** (156 per arm), reconstruction **R = 4**,
  total **472**; `ladder_calls + reconstruction_calls = 472 <= 576` — PASS.
- `ladder_records.csv` 472 rows: `LADDER` 468 (`ROW_LAYERED_90` 156,
  `ROW_LAYERED_360` 156, `FLOODING_90` 156), `SOURCE_RECONSTRUCTION` 4.
- `paired_summary.csv` 156 rows; summed `ladder_calls` 468,
  `reconstruction_calls` 4.

Baseline replay gate (hard gate before comparative interpretation):

- `ROW_LAYERED_90` replay equality against the stored X2 record:
  **156/156 rows `baseline_replay_match = True`**; all 4
  `SOURCE_RECONSTRUCTION` rows also `True`; `mismatch_field` empty on every
  row; no `X3_BASELINE_REPLAY_MISMATCH_BLOCKED`; `stop: null`.

Per-arm raw records (156 calls each; all finite, all
`provenance = CHECK_UPDATED`, zero crash):

| Arm | exact | syndrome_ok | changed_vs_current | status |
|---|---|---|---|---|
| `ROW_LAYERED_90` | 0 | 0 | 0 | `converged_no_syndrome` 156 |
| `ROW_LAYERED_360` | 1 | 1 | 1 | `converged_no_syndrome` 155, `converged_exact` 1 |
| `FLOODING_90` | 0 | 0 | 0 | `converged_no_syndrome` 156 |

`paired_summary.csv` arm columns: `arm_360_exact` True 1 / False 155,
`arm_360_changed` True 1 / False 155 (the one changed record is graph 0);
`flooding_exact` False 156, `flooding_changed` False 156. These are raw
counters only; no diagnostic conclusion is drawn here.

## 5. Authorization-consumption record

- `x3_reference_ladder_authorized: true` was set immediately before the
  single process start (13:51:44) and restored `false` as the operator's
  next action after the attempt script returned (the attempt script's own
  post-attempt bookkeeping ran first; verified false 13:59:35, with no
  decoder work in between). Confirmed false; no residual process.
- Consumption markers (additive in `cycle_state.yaml`):
  `x3_authorization_consumed: true`, `x3_process_starts: 1`,
  `x3_decoder_calls: 472`, `x3_selected_records: 156`,
  `x3_reconstruction_calls: 4`, `x3_ladder_calls: 468`,
  `x3_root: workspace/d7_r1_reference_ladder_20260913_r1`,
  `x3_terminal: X3_REFERENCE_LADDER_COMPLETED`,
  `x3_operator_return: docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/X3_OPERATOR_RETURN_R1.md`,
  `x1_x4_authorization_consumed: PARTIAL_X1_X2_X3_CONSUMED_X4_UNUSED`.
- The A2 remediation grant (one scoped fix + one second attempt on a
  first-attempt failure) was not needed: this first X3 attempt completed
  with a non-blocking terminal.
- X4 (`x4_g2_execution_authorized`), D7-H, G1 rerun, real data, n=1024,
  tuning, promotion: untouched, false, unconsumed
  (`x4_authorization_consumed: false`).

## 6. No later phase, no retry, no commit

- Exactly one X3 process start; no retry, resume, root replacement, seed
  substitution, parameter change, or cleanup.
- X4 frozen root remains ABSENT: `workspace/v72p2d5_g2/20260906_r1`. No
  G1/D7-H/real/n=1024 action.
- No commit, no staging, no push; branch and HEAD unchanged.

## 7. Terminal class and next gate

Raw terminal `X3_REFERENCE_LADDER_COMPLETED`, exit 0, full coverage of the
156 selected failed f=1.2 records, baseline replay equality 156/156, no
stop reason — a completed scientific/coverage terminal, not an
engineering/resource/crash class. This operator records raw outputs only and
does not accept the phase. Per A1, the next gate is an independent X3
Pre-RESULT review; X4 remains unauthorized.

Scope notes (non-blocking, for the reviewer):

- The two stale tests noted in `X2_OPERATOR_RETURN_R1.md` §7
  (`test_cycle_state_marker_and_all_flags_false`,
  `test_frozen_execution_roots_remain_absent`) were updated in this same
  boundary to the post-X3 reality; see §8.
- `repo_files_touched.txt` from the attempt script is again vacuous
  (0 bytes); no-overwrite rests on `status_diff.txt`, the byte-identical
  git status, the explicit window scan, and the X2 mtime check.

## 8. Post-attempt test updates and run

Superseded tests updated without weakening their checks:

- `test_cycle_state_marker_and_all_flags_false`: still asserts every
  execution flag false and `historical_evidence:
  RETAINED_BYTE_IDENTICAL`; lifecycle now
  `state`/`terminal = X3_EXECUTION_COMPLETE_PENDING_INDEPENDENT_REVIEW`,
  `next_gate = X3_INDEPENDENT_PRERESULT_REVIEW`.
- `test_frozen_execution_roots_remain_absent` ->
  `test_execution_roots_state_after_x3`: `workspace/d7_r1_multigraph_20260913_r1`
  and `workspace/d7_r1_reference_ladder_20260913_r1` must be present
  directories; `workspace/v72p2d5_g2/20260906_r1` must remain absent.

Command (fresh basetemp, repo venv, no production decoder path in any
test; all decoders fake/injected, the one real-import bind test never
invokes a wrapper):

```text
.venv/bin/python -m pytest -p no:cacheprovider -q \
  --basetemp=workspace/v72p2d7_x1x4_test_x3post_1789279418_4411 \
  comparison_bench/tests/test_v72p2d7_r1_x1x4_entrypoints.py
```

Result: **57 passed**, exit **0** (log
`/tmp/opencode/x3_r1_20260913/post_x3_test_run.txt`).

## 9. A2 remediation statement (user-required disclosure)

No implementation remediation was used for X3: the first attempt completed
with a non-blocking terminal, so the A2 one-fix-one-second-attempt grant was
not triggered. Files changed at this boundary: this return, `cycle_state.yaml`
(state/markers only), `X2_PRE_RESULT_REVIEW_R1.md` and
`A2_X2_X4_REMEDIATION_AUTHORIZATION_R1.md` (records), and
`comparison_bench/tests/test_v72p2d7_r1_x1x4_entrypoints.py` (two superseded
lifecycle/root test expectations only). None of these changes any matrix,
seed, row, arm, threshold, root, command, budget, provenance semantic,
terminal, or claim ceiling, and none can affect the exploration goals: X2
graph sensitivity remains the recorded `GRAPH_SENSITIVITY_OBSERVED` result,
X3 strong-reference diagnosis rests on the raw 468-ladder-call records above,
and X4 G2 length discrimination remains untested and unauthorized.
