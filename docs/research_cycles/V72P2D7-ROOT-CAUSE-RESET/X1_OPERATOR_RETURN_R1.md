# X1 operator return R1 — D7 X1–X4 master A1 (BLOCKED)

- Cycle: `V72P2D7-ROOT-CAUSE-RESET`
- Change: `formal-ir-d7-root-cause-and-route-reset`
- Packet: `.workbuddy/tasks/D7_X1_X4_EXECUTION_MASTER_R1_TASK_PACKET.md` §7 X1, §8, §9
- Addendum: `.workbuddy/tasks/D7_X1_X4_EXECUTION_MASTER_R1_A1_TASK_PACKET.md`
- Pre-EXECUTE record: `A1_X1_X4_AUTHORIZATION_RECORD_R1.md`
- Branch (unchanged, not switched): `formal-ir-v72p1-addendum-clean`;
  HEAD `278fdf0742255de0d030649965b6feffb11bc23d` (unchanged after attempt)
- Operator role: X1 execution only; no retry, no repair, no cleanup, no
  self-acceptance, no later phase.

## 1. Literal command and execution identity

Master packet literal (Windows host):

```powershell
.venv\Scripts\python.exe scripts\v72p2d7_consistency_multigraph.py --historical-provenance-probe
```

Executed WSL form, exactly as launched (frozen semantics; interpreter mapping
per `AGENTS.md` §8, D7-E closeout A1, D7-F prereg §4):

```text
timeout -k 30 120 .venv/bin/python scripts/v72p2d7_consistency_multigraph.py --historical-provenance-probe
```

- cwd: `/mnt/d/Code/HD-QKD_Polar_Comparison`
- Outer watchdog: `timeout -k 30 120` (SIGTERM at 120 s, SIGKILL at 150 s)
- Timeout process pid (ownership, single foreground process): `340420`
  (`/tmp/opencode/x1_r1_attempt_20260913/timeout_pid.txt`)
- Launch command id: one foreground bash invocation
  `bash /tmp/opencode/x1_r1_attempt.sh` by this X1 operator; no detach, no
  concurrent phase.
- Start: `2026-09-13T12:02:31+0800` / `2026-09-13T04:02:31Z`
- End: `2026-09-13T12:02:33+0800` / `2026-09-13T04:02:33Z`
- Outer wall: `2142 ms`
- Watchdog disposition: `COMPLETED_BEFORE_OUTER_WATCHDOG`
- Exit code (directly captured from the `timeout` invocation, not inferred
  from artifacts): **2**

Raw `meta.txt`:

```text
REPO=/mnt/d/Code/HD-QKD_Polar_Comparison
CWD=/mnt/d/Code/HD-QKD_Polar_Comparison
COMMAND=timeout -k 30 120 .venv/bin/python scripts/v72p2d7_consistency_multigraph.py --historical-provenance-probe
START_LOCAL=2026-09-13T12:02:31+0800
START_UTC=2026-09-13T04:02:31Z
EXIT_CODE=2
END_LOCAL=2026-09-13T12:02:33+0800
END_UTC=2026-09-13T04:02:33Z
WALL_MS=2142
TIMEOUT_DISPOSITION=COMPLETED_BEFORE_OUTER_WATCHDOG
```

## 2. stdout / stderr verbatim

stdout (md5 `f41e519d74f8de1dff7562ed8c26ff0c`, 299 bytes):

```json
{"accepted_check_updated": false, "belief_shape_ok": true, "beliefs_finite": true, "decoder_calls": 1, "iterations": 0, "mode": "historical_provenance_probe", "ok": false, "provenance": "PRIOR_ONLY", "resolved_decoder_identity": "historical_g0_decoder", "resolved_is_historical": true, "writes": 0}
```

stderr (md5 `8df6c7f91a1ba9d3fd9ee52ad291de08`, 27 bytes):

```text
X1_PROVENANCE_PROBE_FAILED
```

## 3. Frozen X1 success-contract check

| Contract item (packet §7 X1) | Required | Observed | Verdict |
|---|---|---|---|
| exit code | 0 | 2 | **FAIL** |
| provenance token | exactly `CHECK_UPDATED` | `PRIOR_ONLY` | **FAIL** |
| `accepted_check_updated` | true | false | **FAIL** |
| iterations | >= 1 | 0 | **FAIL** |
| beliefs finite | true | true | pass |
| belief shape valid | true | true | pass |
| decoder calls | exactly 1 | 1 | pass |
| writes | 0 | 0 | pass |
| file/root created | none | none (see §5) | pass |

Terminal: **`X1_PROVENANCE_PROBE_FAILED`** (exit 2 plus the exact stderr
label). Per packet §7/§9 this is the X1 failure terminal: STOP; no retry or
repair inside the execution attempt.

## 4. Authorization-consumption record

- X1 authorization `x1_consistency_probe_authorized`: set `true` immediately
  before the process start; consumed by the first process start; restored
  `false` immediately after the attempt, before writing this record and
  before any review/progression. Verified false afterward (line 19 of
  `cycle_state.yaml`; all other flags remain false).
- Per A1, the nonzero X1 engineering terminal consumes X1 and terminates the
  entire serial chain. X2 (`x2_multigraph_execution_authorized`), X3
  (`x3_reference_ladder_authorized`), X4
  (`x4_g2_execution_authorized`) authorizations are **unused / not
  consumed** and must not be exercised without a new user decision.
- D7-H, G1 rerun, real data, n=1024, tuning, promotion: untouched and
  unauthorized.
- `cycle_state.yaml` delta: only the one-line toggle `true` -> `false`
  (net-zero content); all other content unchanged. Consumption markers
  (`x1_authorization_consumed`, etc.) were intentionally not edited because
  the operator brief scoped this operator's `cycle_state.yaml` edits to the
  single flag; this record is the consumption evidence for the main
  thread/reviewer.

## 5. No-write / no-root evidence

- JSON record reports `writes: 0`.
- `git --no-optional-locks status --porcelain | sort` identical before and
  after the attempt: diff = 0 lines (`status_diff.txt` empty).
- `find . -path ./.git -prune -o -newer <attempt marker> -type f -print`:
  0 repo files touched (`repo_files_touched.txt` empty; the only stderr
  noise was pre-existing permission-denied ACL warnings on legacy
  `workspace/**`/pytest-cache directories, AGENTS.md §8 known-benign).
- X1 has no output root by design; none created.
- X2/X3/X4 frozen roots re-verified absent after the attempt:
  `workspace/d7_r1_multigraph_20260913_r1`,
  `workspace/d7_r1_reference_ladder_20260913_r1`,
  `workspace/v72p2d5_g2/20260906_r1` — all `ABSENT`.

## 6. Retained evidence (nothing deleted or cleaned)

- Attempt transcripts, outside the repo worktree:
  `/tmp/opencode/x1_r1_attempt_20260913/` —
  `meta.txt` (md5 `a95c7768c995634af48681025b78871c`), `stdout.txt`,
  `stderr.txt`, `timeout_pid.txt`, `status_before.txt`, `status_after.txt`,
  `status_diff.txt` (empty), `repo_files_touched.txt` (empty).
- Capture script: `/tmp/opencode/x1_r1_attempt.sh`.
- This return and the pre-EXECUTE record in
  `docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/`.

## 7. Changed-file manifest, no commit / no push

- New: `docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/A1_X1_X4_AUTHORIZATION_RECORD_R1.md`
- New: `docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/X1_OPERATOR_RETURN_R1.md`
- Modified (net-zero toggle): `docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/cycle_state.yaml`
- No commit, no staging, no push; branch and HEAD unchanged.

## 8. Return: BLOCKED

- Last completed gate: X1 Pre-EXECUTE record (`A1_X1_X4_AUTHORIZATION_RECORD_R1.md`)
  and the one authorized X1 process start; X1 result contract evaluated.
- Failing check and raw output:
  `timeout -k 30 120 .venv/bin/python scripts/v72p2d7_consistency_multigraph.py --historical-provenance-probe`
  -> exit 2; stdout `{"accepted_check_updated": false, ..., "iterations": 0,
  "provenance": "PRIOR_ONLY", "ok": false, ...}`; stderr
  `X1_PROVENANCE_PROBE_FAILED`.
- Authorization: X1 consumed; X2/X3/X4 unused.
- Retained evidence: §6 (no cleanup, no retry, no repair).
- No later phase ran; no X2/X3/X4/G1/D7-H/real/n=1024 action occurred.
- One main-thread decision needed: the scientific disposition of the X1
  provenance failure — whether to open a new reviewed root-cause/repair
  packet for the historical G0 decoder's `PRIOR_ONLY` / zero-iteration
  return (with any new user authorization), or to record the D7 provenance
  route as blocked. No retry, repair, or cleanup is authorized in this
  chain; this operator does not accept this phase.
