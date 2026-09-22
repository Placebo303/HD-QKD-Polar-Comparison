# D7 X1–X4 A1 authorization record R1 — X1 pre-EXECUTE

- Cycle: `V72P2D7-ROOT-CAUSE-RESET`
- Change: `formal-ir-d7-root-cause-and-route-reset`
- Role: X1 execution operator only. This record does not accept the phase,
  change thresholds, or authorize X2–X4.
- Authority:
  - `.workbuddy/tasks/D7_X1_X4_EXECUTION_MASTER_R1_TASK_PACKET.md` (sole
    operational packet; §7 X1, §8 gate handling, §9 STOP)
  - `.workbuddy/tasks/D7_X1_X4_EXECUTION_MASTER_R1_A1_TASK_PACKET.md`
    (authorization addendum; one serial attempt X1–X4, per-phase gates)
- Prerequisite boundary accepted before this record: Phase P P01–P10
  (`PHASE_P_PRE_EXECUTE_READINESS_R1.md`,
  `PHASE_P_INDEPENDENT_READINESS_REVIEW_R1.md`, verdict
  `PASS_WITH_FINDINGS`; lifecycle `X1_READY_AWAITING_EXPLICIT_AUTHORIZATION`).

## 1. Verbatim user authorization and scope

Verbatim user authorization (A1 Task Packet, `## Authority` section):

> 我可以授权执行X1-X4，一次性完成都可以

A1 addendum scope (paraphrase-free summary of its binding clauses):

- one sequential attempt of X1, X2, X3, X4 under the master packet; all
  frozen commands, inputs, roots, ceilings, claim limits, no-overwrite rules,
  and STOP conditions remain binding;
- progression gates: X2 only after X1 exit 0 + frozen success contract; X3
  only after X2 full coverage without resource/crash/nonfinite/engineering
  blocker and a passing independent X2 Pre-RESULT review (or
  `X3_NOT_APPLICABLE_NO_FAILED_CALLS`); X4 only after X3 completes / is not
  applicable / returns a reviewed non-blocking diagnostic and a passing
  independent X3 Pre-RESULT review;
- D7-H, G1 rerun, real data, n=1024, tuning, promotion, and everything
  outside X1–X4 remain unauthorized;
- each phase receives exactly one process-start attempt; set only the
  imminent phase flag true; restore it false immediately after the attempt,
  before review or progression; a refusal, exception, timeout, crash,
  resource stop, partial root, or failed review consumes that phase
  authorization and terminates the chain; no retry/resume/alternate
  root/seed replacement/parameter adjustment/cleanup/later-phase execution;
- this X1 execution is authorized contiguously, but this record authorizes
  and enables **X1 only**. X2, X3, X4 authorizations remain unused and must
  not be exercised by this operator without the intervening independent
  reviews and main-thread progression decisions.

## 2. Branch verification (read-only; no switch)

```text
$ git rev-parse --abbrev-ref HEAD
formal-ir-v72p1-addendum-clean
$ git rev-parse HEAD
278fdf0742255de0d030649965b6feffb11bc23d
```

- Required branch: `formal-ir-v72p1-addendum-clean` — MATCH; no checkout,
  switch, stash, reset, or staging performed.
- HEAD hash recorded for provenance only (packet §8: a commit ID is
  provenance, not an execution lock).
- Pre-existing dirty worktree (unrelated to this phase), used as the
  no-write baseline: `git --no-optional-locks status --porcelain | sort`
  = 2104 entries, md5 `df682a08b9d224e9999ef7f1b23033c5`.

## 3. Execution-state check (`docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/cycle_state.yaml`)

All execution/authorization flags false at record creation:

| Flag | Value |
|------|-------|
| `x1_consistency_probe_authorized` | false |
| `x2_multigraph_execution_authorized` | false |
| `x3_reference_ladder_authorized` | false |
| `x4_g2_execution_authorized` | false |
| `d7h_execution_authorized` | false |
| `decoder_executed` | false |
| `multigraph_executed` | false |
| `g2_executed` | false |
| `g1_rerun_authorized` | false |
| `result_solidification_authorized` | false |
| `scientific_promotion` | false |

- X1 target: **no output root by design** (packet §7 X1: stdout/stderr
  transcript only; zero writes, zero roots). There is no X1 root to check
  for absence.
- X2/X3/X4 frozen roots verified absent (raw output):

```text
$ for r in workspace/d7_r1_multigraph_20260913_r1 \
           workspace/d7_r1_reference_ladder_20260913_r1 \
           workspace/v72p2d5_g2/20260906_r1; do
      [ -e "$r" ] && echo "PRESENT: $r" || echo "ABSENT: $r"; done
ABSENT: workspace/d7_r1_multigraph_20260913_r1
ABSENT: workspace/d7_r1_reference_ladder_20260913_r1
ABSENT: workspace/v72p2d5_g2/20260906_r1
```

- `x1_x4_authorization_granted: true`, `x1_x4_authorization_consumed:
  false`; no authorization consumed at record creation.

## 4. Environment probe (separate commands, no decoder executed)

```text
$ test -x .venv/bin/python
VENV_PYTHON_EXECUTABLE_OK
$ .venv/bin/python -c "import numpy, pytest, sys; print(sys.version.split()[0], numpy.__version__)"
3.12.3 2.5.3
$ timeout --version
timeout (GNU coreutils) 9.4
$ pwd
/mnt/d/Code/HD-QKD_Polar_Comparison
```

## 5. Exact frozen command and WSL execution mapping

Master packet §7 X1 literal (Windows host):

```powershell
.venv\Scripts\python.exe scripts\v72p2d7_consistency_multigraph.py --historical-provenance-probe
```

Executed WSL form (this checkout):

```text
timeout -k 30 120 .venv/bin/python scripts/v72p2d7_consistency_multigraph.py --historical-provenance-probe
```

Environment mapping (explicit): this checkout executes in WSL, where
`AGENTS.md` §8 and all accepted D7 execution records freeze the interpreter
as `.venv/bin/python` (precedent: D7-E closeout A1; D7-F prereg §4). The
mapping changes only the interpreter path/separator; the script path,
`--historical-provenance-probe` flag, working directory (repo root), and
command semantics are byte-identical to the packet literal.

## 6. Outer watchdog, process ownership, budgets, stop rules

- Outer watchdog: `timeout -k 30 120` (SIGTERM at 120 s; SIGKILL 30 s
  later at 150 s), single foreground process, no detach.
- Process ownership: the attempt is launched by this X1 operator as one
  foreground `bash` invocation from the repo root; at launch the `timeout`
  process pid is written to
  `/tmp/opencode/x1_r1_attempt_20260913/timeout_pid.txt` (pid + the invoking
  tool command ID are copied into `X1_OPERATOR_RETURN_R1.md`). No other
  operator/agent launches a concurrent X phase.
- Budgets: outer watchdog 120 s; RSS < 2 GiB; exactly 1 historical
  row-layered decoder call on the built-in 2x2 GF32 fixture; writes = 0;
  roots created = 0.
- Success contract (packet §7 X1): exit 0; JSON record with provenance
  exactly `CHECK_UPDATED`, beliefs finite, shape valid, `iterations >= 1`,
  `decoder_calls: 1`, `writes: 0`; no file/root created.
- Failure terminal: any other return is `X1_PROVENANCE_PROBE_FAILED`; STOP,
  no retry or repair inside the attempt.
- HARD STOP (packet §9): branch mismatch or scoped drift; target root
  exists; missing authorization; inferred authorization; provenance not
  exactly `CHECK_UPDATED` or not exactly one decoder call; any retry/resume/
  tuning/D7-H/real/n=1024 action.
- Recording rule (packet §8): X1 has no result root; its literal command,
  exit code, stdout, stderr, start/end timestamps, watchdog disposition, and
  consumption record are retained in the cycle docs, pending independent
  review.

## 7. Authorization-consumption rule for this attempt

- Pre-attempt edit: set only `x1_consistency_probe_authorized: true` in
  `cycle_state.yaml`; all other flags remain false.
- The first process start of
  `timeout -k 30 120 .venv/bin/python scripts/v72p2d7_consistency_multigraph.py --historical-provenance-probe`
  consumes the X1 authorization, regardless of success, refusal, crash, or
  timeout.
- Immediately after the attempt (before review or progression), restore
  `x1_consistency_probe_authorized: false`.
- No retry, resume, root/seed replacement, tuning, cleanup, or later-phase
  execution. Preserve evidence in place.
- This record is pre-EXECUTE readiness evidence, not acceptance; the
  operator does not accept its own work.
