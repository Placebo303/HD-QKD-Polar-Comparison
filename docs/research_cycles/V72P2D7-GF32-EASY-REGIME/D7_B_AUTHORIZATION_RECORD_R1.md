# D7-B authorization record R1 (one frozen easy-regime invocation)

## 0. Verbatim user authorization (§0 sole authority)

> 我现在明确授权执行 D7-B easy-regime：仅允许按已冻结的
> `D7_B_EXECUTION_PACKET_R1.md` 对一个全新的
> `workspace/d7_b_easy_regime_<uuid>/` 根进行且仅进行一次调用；授权由首次
> scientific decoder 尝试消耗，不因失败、超时或部分结果而恢复；不得重试、
> 重跑、恢复、复用根或修改任何参数；不得执行 R1d、任何 `--phase`、正式
> G1/G2、Model-F、CAL、VAL、real/raw。执行后必须停止并进行独立
> Pre-RESULT 复审，复审通过前不得接受或提交结果。

## 1. UUID and target root (exactly one UUID generated, no fallback)

- UUIDv4: `0f1ad3ec-f9e0-463f-a7dd-d9880ff7230c`
- Source: single read of `/proc/sys/kernel/random/uuid` (exactly one generation;
  no second UUID exists anywhere in this task).
- Target root: `workspace/d7_b_easy_regime_0f1ad3ec-f9e0-463f-a7dd-d9880ff7230c`
- E05/E10 verified before this record: zero `workspace/d7_b_easy_regime_*` roots;
  chosen root absent; parent `workspace/` writable; root NOT pre-created.

## 2. Exact instantiated command (exactly-once invocation)

Frozen packet form (PowerShell):

```powershell
& 'C:\Program Files\Git\usr\bin\timeout.exe' -k 30 1800 python scripts/v72p2d7_gf32_easy_regime.py --out-root workspace/d7_b_easy_regime_<uuid>
```

Instantiated invocation (this environment provides bash only; no
`powershell`/`pwsh` binary exists — verified `which` exit 1):

```bash
PATH="$HOME/.venvs/hd-qkd-polar-comparison/bin:$PATH" timeout -k 30 1800 python scripts/v72p2d7_gf32_easy_regime.py --out-root workspace/d7_b_easy_regime_0f1ad3ec-f9e0-463f-a7dd-d9880ff7230c
```

Environment-equivalence facts (wrapper only; inner command text unchanged):

- Watchdog: GNU coreutils `timeout -k 30 1800` (`timeout --version` → 9.4).
  Git-for-Windows `timeout.exe` is the same GNU timeout program with identical
  `-k 30 1800` semantics. `timeout.exe` existence verified at
  `/mnt/c/Program Files/Git/usr/bin/timeout.exe` (size 41752,
  mtime 2025-11-17 18:24:08 +0800); it cannot launch a Linux ELF interpreter
  from WSL, so the POSIX twin is used. No tee/redirection/pipeline is added to
  the scientific command; stdout/stderr/exit/outer-wall are captured by an
  outer wrapper that leaves the inner command text unchanged.
- Interpreter: bare `python` is absent on default PATH in this environment
  (`python --version` → 127). `python` is resolved via the project venv
  `~/.venvs/hd-qkd-polar-comparison/bin` on PATH: CPython 3.12.3,
  numpy 2.4.4 (verified live). No argument, order, path, seed, cap, prior,
  structure, threshold, budget or environment injection is changed.
- Recorded interpreter limitation (environment fact, not a gate failure and not
  a code/packet edit): the venv has no `psutil`, so frozen `_rss_bytes()`
  returns `None`; per frozen code (`over = ... or rss_unknown`) the run will
  record `rss_bytes: null` rows and `resource_overrun: true` in aggregates,
  mapping to terminal `D7_B_RESOURCE_OVERRUN` under frozen T1–T9 priority unless
  a higher-priority terminal preempts. This is frozen-code behavior on this
  host; it is recorded literally and reviewed, never repaired or retried.
  Installing packages is forbidden, so the interpreter is used as-is.

## 3. Fresh gates E01–E10 (read-only, immediately before authorization)

- E01 PASS: branch `formal-ir-v72p1-addendum-clean`; HEAD `7f439036`
  (`7f4390367f33f4ebf531f5d2488322ae5b690839`); frozen commits all present:
  `a5d5ce4e` (impl), `f40e3376` (freeze), `7f439036` (readiness/closeout).
- E02 PASS: frozen packet `D7_B_EXECUTION_PACKET_R1.md` and prereg
  `D7_B_PREREG_R1.md` present; verdicts
  `D7_B_IMPLEMENTATION_REVIEW_PASS` and
  `D7_B_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION` present and
  agreeing (frozen R1+A1, no execution yet, authorization still false).
- E03 PASS: `git diff a5d5ce4e --stat -- <3 scoped impl/test/script paths>`
  empty (exit 0, no output). Scoped cycle paths clean in status.
- E04 PASS: `cycle_state.yaml` matches §1 exactly:
  `d7b_execution_authorized: false`, attempts 0, completed 0,
  `decoder_executed: false`, `result_created: false`, all other execution
  authorization keys false, `scientific_promotion: false`,
  `next_gate: D7_B_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`.
- E05 PASS: `ls -d workspace/d7_b_easy_regime_*` → no such file; exactly one
  UUID generated (`0f1ad3ec-f9e0-463f-a7dd-d9880ff7230c`); chosen root absent.
- E06 PASS: no `workspace/*v72p2d7*` roots (no D7-B/R1d/G2 root for this
  cycle; other-cycle names such as `d6_r1d_tests_*` / `v72p2d5_*` are out of
  scope and untouched). No formal/VOID/Model-F/CAL/VAL/real/raw content read —
  metadata-only directory names used. Pre-EXECUTE review enumerates no
  protected-root size/mtime table beyond absence assertions, so absence is
  re-verified and recorded here.
- E07 PASS: `timeout.exe` exists (path/size/mtime above). Prior accepted 3 s
  rehearsal evidence exists in Pre-EXECUTE review (exit 124); per packet rule
  the rehearsal is NOT repeated.
- E08 PASS: live RSS probe as a separate command — system interpreter psutil
  RSS `13942784` bytes (positive int, < 2 GiB). Frozen `_rss_bytes()` under the
  execution venv returns `None` (no psutil there); recorded in §2 above.
- E09 PASS: scoped code unchanged since accepted Pre-EXECUTE review (E03
  empty) → no test rerun. (If code had differed, the rule would be STOP, not
  re-test.)
- E10 PASS: `test -w workspace` → writable; chosen root absent; root not
  pre-created.

Any gate fail would have blocked the flip and the invocation. All pass.

## 4. Time

- Local: 2026-09-10 19:14 CST (UTC+8); UTC: 2026-09-10 11:14.
- Start/end/wall times of the invocation itself are captured in the operator
  return (§5 record), not here.

## 5. Attempt-consumption and no-retry rules

- Authorization (`d7b_execution_authorized: true`) applies to exactly ONE
  invocation of the instantiated command in §2 and is consumed by the first
  scientific-decoder attempt regardless of outcome (success, failure, 124
  timeout, nonzero exit, partial root, unexpected output).
- No retry, rerun, resume, re-root, re-param, or replacement UUID under any
  outcome. No R1d, no `--phase`, no G1/G2, no Model-F/CAL/VAL/real/raw.
- Immediately after the process returns and before any scientific
  interpretation, `d7b_execution_authorized` is flipped true→false and
  committed alone. `command_invocations: 1` always after launch;
  `scientific_attempt_consumed: true` only if artifacts/logs prove ≥1 decoder
  attempt, else `NOT_VERIFIABLE` (never `false` as basis for retry).

## 6. Claim ceiling

- This record authorizes execution only. It accepts no scientific result.
- The result root (complete or partial) stays immutable and uncommitted until
  an independent Pre-RESULT review (R01–R16) writes its verdict.
- Easy-regime outcomes are never interpreted as FER, leakage, key rate,
  qualification, or actual-channel recovery.

(End of file)
