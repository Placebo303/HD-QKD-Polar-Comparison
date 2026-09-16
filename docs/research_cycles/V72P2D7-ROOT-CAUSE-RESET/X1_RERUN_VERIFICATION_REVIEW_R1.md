# X1 rerun verification review R1 — independent verification record

- Cycle: `V72P2D7-ROOT-CAUSE-RESET`
- Change: `formal-ir-d7-root-cause-and-route-reset`
- Packet: `.workbuddy/tasks/D7_X1_X4_EXECUTION_MASTER_R1_TASK_PACKET.md`
  §7 X1, §8, §9; Addendum A1
- Scope: independent verification of the single authorized X1 rerun recorded
  in `X1_OPERATOR_RETURN_R2.md`, against the raw transcripts in
  `/tmp/opencode/x1_r1_rerun_20260913/`. Nothing was re-executed, repaired,
  retried, cleaned, staged, or committed by this review.
- Branch: `formal-ir-v72p1-addendum-clean`; HEAD
  `278fdf0742255de0d030649965b6feffb11bc23d`.

## 1. Verdict

**`X1_RERUN_VERIFIED`**

## 2. Command, exit, transcripts

Executed command (WSL form of the frozen §7 X1 literal):

```text
timeout -k 30 120 .venv/bin/python scripts/v72p2d7_consistency_multigraph.py --historical-provenance-probe
```

- Exit code: **0** (direct capture from the `timeout` invocation, recorded in
  `meta.txt` as `EXIT_CODE=0`).
- Outer wall: **1686 ms**; watchdog disposition
  `COMPLETED_BEFORE_OUTER_WATCHDOG`; timeout process pid **436289**
  (`timeout_pid.txt`).
- Start `2026-09-13T13:01:39+0800` / `2026-09-13T05:01:39Z`; end
  `2026-09-13T13:01:41+0800` / `2026-09-13T05:01:41Z`.
- Transcripts `/tmp/opencode/x1_r1_rerun_20260913/` (retained, untouched):
  - `meta.txt` md5 `0209b8af170e3c3c575501443d4e6562`
  - `stdout.txt` md5 `b978bbd94c065b9b9c861bd46139d3e1` (301 bytes)
  - `stderr.txt` md5 `d41d8cd98f00b204e9800998ecf8427e` (empty, 0 bytes)
- stdout verbatim:

```json
{"accepted_check_updated": true, "belief_shape_ok": true, "beliefs_finite": true, "decoder_calls": 1, "iterations": 90, "mode": "historical_provenance_probe", "ok": true, "provenance": "CHECK_UPDATED", "resolved_decoder_identity": "historical_g0_decoder", "resolved_is_historical": true, "writes": 0}
```

- stderr: empty.

## 3. Frozen X1 success-contract check (packet §7 X1)

| Contract item | Required | Observed | Verdict |
|---|---|---|---|
| exit code | 0 | 0 (direct) | pass |
| provenance | exactly `CHECK_UPDATED` | `CHECK_UPDATED` | pass |
| beliefs finite | true | `beliefs_finite: true` | pass |
| belief shape valid | true | `belief_shape_ok: true` | pass |
| iterations | >= 1 | 90 | pass |
| decoder calls | exactly 1 | `decoder_calls: 1` | pass |
| writes | 0 | `writes: 0` | pass |
| output root/files | none | none created | pass |
| resolved decoder identity | historical | `historical_g0_decoder`, `resolved_is_historical: true` | pass |

All rows pass. Informational (no contract effect): `iterations=90` equals
`MAX_ITER`, which is consistent with either v35 decoder exit path (converged
at the last iteration or non-converged exit); the frozen JSON omits `status`
and `syndrome_ok`, so the exit path cannot be distinguished from the record
and is not part of the X1 success contract.

## 4. Single-attempt, no-write, untouched-evidence checks

- **Single rerun start**: exactly one launch under this authorization; the
  earlier consumed attempt evidence at `/tmp/opencode/x1_r1_attempt_20260913/`
  and all R1 failure records are untouched.
- **No-write**: `status_diff.txt` (0 lines; pre/post
  `git --no-optional-locks status --porcelain | sort`) and
  `repo_files_touched.txt` (empty; `find . -newer meta.txt`) were both
  recorded by the attempt script; independently re-checked by a file-window
  scan (`find . -newer 2026-09-13T05:01:38Z ! -newer 2026-09-13T05:01:43Z`):
  zero repo files matched. The only scan diagnostics were the pre-existing
  permission-denied ACL noise on legacy `workspace/**` and pytest-cache
  directories (`AGENTS.md` §8 known-benign).
- **Flag restored false**: `x1_consistency_probe_authorized` is `false` in
  `cycle_state.yaml` after the attempt; X2/X3/X4/D7-H/G1/real/n=1024 remain
  false and unconsumed (`x2/x3/x4_authorization_consumed: false`).
- **X2–X4 unused**: no later phase ran; frozen roots
  `workspace/d7_r1_multigraph_20260913_r1`,
  `workspace/d7_r1_reference_ladder_20260913_r1`,
  `workspace/v72p2d5_g2/20260906_r1` remain absent.
- **No commit/staging/push**: branch `formal-ir-v72p1-addendum-clean` and
  HEAD `278fdf07` unchanged; no staging, commit, push, cleanup, retry, or
  repair.

## 5. Disposition

X1 rerun independently verified as `X1_RERUN_VERIFIED`. X1 is complete; the
state advances to `X1_COMPLETE_VERIFIED` with `next_gate: X2_EXECUTION`.
This record grants no authorization and accepts no scientific claim beyond
the single-fixture provenance probe (`CHECK_UPDATED` observed; no
qualification, promotion, or comparative/real-data claim).
