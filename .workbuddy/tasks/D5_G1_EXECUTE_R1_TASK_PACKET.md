# D5-G1-EXECUTE-R1 — one authorized frozen G1 attempt

## 0. Authority and terminal rule

The user gave this exact authorization in the session dispatching this packet:

> 我现在明确授权执行 G1：授权对冻结的 g1 命令进行且仅进行一次调用；授权由“尝试”消耗而非由“成功”消耗；不许重试、不许重跑、不许恢复、不许修改任何参数；不许执行 G2。

This authorizes exactly one attempt of the command frozen in
`G1_PRE_EXECUTE_PACKET_R1.md`. The attempt consumes authorization regardless of
success, refusal, exception, timeout, partial output, or result. There is no
retry, rerun, resume, second root, parameter adjustment, or G2 execution.

Two valid returns only:

1. all steps completed and the one attempt recorded; or
2. STOP before the attempt on a concrete pre-run blocker, or after the attempt
   after first revoking authorization, with raw evidence and no repair.

## 1. Fixed baseline

- Repo: `D:/Code/HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`
- Expected initial HEAD: `6494b623`
- Accepted implementation: `cf61ee63f5b76b0223838717b1344e0e7c3867ee`
- Frozen packet: `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_PRE_EXECUTE_PACKET_R1.md`
- Passing review:
  `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_PRE_EXECUTE_REVIEW_R1.md`
  with verdict `G1_PRE_EXECUTE_REVIEW_PASS`
- Formal output root: `workspace/v72p2d5_g1/20260907_r2`
- Retained VOID root: `workspace/v72p2d5_g1/20260906_r1` — never read for
  numerical evidence, modified, compared for performance, or reused
- G2 root: `workspace/v72p2d5_g2` — must remain absent

Later untracked task files and known CRLF porcelain churn are non-blocking when
`git diff --numstat` and `git diff --cached --numstat` show no content change.
Do not normalize or clean them.

## 2. Hard prohibitions

- Do not invoke G1 before STEP 4, or more than once in total.
- Do not invoke P0, G2, any other phase, Model-F prepare/verify, or any
  production decoder outside the single authorized G1 command.
- Do not alter command text, cwd, seeds, parameters, roots, budgets, watchdog,
  environment, or implementation.
- Do not retry after exit 0, 3, 124, another nonzero exit, exception, crash,
  partial root, or missing/malformed evidence.
- Do not resume or reuse a partial root. Retain it as VOID in place.
- Do not read CAL/VAL/parquet/raw rows or call `pandas.read_parquet`.
- Do not delete, move, rename, overwrite, normalize, hash, or repair anything
  under `workspace/`.
- Do not edit `.py`, OpenSpec, frozen packets, existing review text, decision
  log, memory, or unrelated files.
- Do not change any authorization except the one required
  `g1_execution_authorized false→true→false` lifecycle.
- Do not change `next_gate`, promotion, P0 acceptance, G1 implementation
  acceptance, or any other state field.
- Do not use `git add -A`, `git add .`, `git commit -a`, push, reset, stash,
  checkout, clean, rebase, revert, amend, or renormalize.
- Do not interpret or accept the result and do not propose/authorize G2.

## 3. STEP 1 — fresh pre-attempt gate

Record literal output and STOP before any state edit if any condition fails:

1. branch is exactly `formal-ir-v72p1-addendum-clean` and expected baseline
   `6494b623` is current HEAD;
2. review file exists and its sole final verdict is
   `G1_PRE_EXECUTE_REVIEW_PASS`;
3. current core and two accepted tests have zero diff from `cf61ee63`;
4. all nine `*_execution_authorized` values are false;
5. `scientific_promotion: false` and
   `next_gate: INDEPENDENT_G1_PRE_EXECUTE_REVIEW`;
6. accepted implementation/root fields equal the fixed baseline;
7. proposed `workspace/v72p2d5_g1/20260907_r2` is absent;
8. G2 root is absent;
9. retained VOID-G1, P0, G0, G0-recovery, Model-F, and structure roots match
   the Pre-EXECUTE review's top-level name/size/mtime snapshot;
10. `git diff --numstat` and `git diff --cached --numstat` are empty before
    this task's writes. Porcelain EOL churn and unrelated untracked files are
    informational only.

Also verify the exact watchdog binary exists. Do not rerun pytest, compile,
the reachability probe, or watchdog rehearsal: those are frozen fresh evidence
in the passing independent review, and no accepted source changed afterward.

## 4. STEP 2 — record authorization and enable exactly G1

Create only:

`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_AUTHORIZATION_RECORD_R1.md`

It must contain:

- the user's authorization above verbatim;
- initial branch/HEAD/lifecycle/root evidence;
- accepted implementation and passing Pre-EXECUTE review;
- the exact frozen command;
- frozen 440 calls, 900 s scientific operator-wall gate, 960 s watchdog with
  30 s kill grace, known peak RSS `<2 GiB`, signal, seven outcomes, and four
  no-overwrite files;
- explicit attempt-consumption and no-retry/no-resume/G2 prohibition;
- obligation to restore the key to false immediately after the attempt, before
  reading output or drafting the operator return.

Edit `cycle_state.yaml` in exactly one place:

```text
g1_execution_authorized: false
```

to:

```text
g1_execution_authorized: true
```

Stage exactly these three paths:

1. `G1_PRE_EXECUTE_REVIEW_R1.md` (the independently authored uncommitted report,
   byte-for-byte unchanged);
2. `G1_AUTHORIZATION_RECORD_R1.md`;
3. `cycle_state.yaml`.

Require `STAGED_COUNT 3` and no other staged path, then commit exactly:

```text
chore(v72p2d5): authorize one frozen G1 invocation

Records the independent Pre-EXECUTE PASS and the user's explicit authorization
for exactly one attempt of the frozen G1 command. Attempt consumes authorization;
no retry, rerun, resume, parameter change, or G2 execution is permitted.

Co-Authored-By: OpenAI Codex <codex@openai.com>
```

If staging or commit fails, STOP before execution. The attempt is not consumed.
Do not leave the key true: restore it to false without committing and report
the blocker, unless restoration itself fails, in which case report that exact
critical state.

## 5. STEP 3 — final immediate pre-invocation check

After the authorization commit and immediately before invocation, require:

- `g1_execution_authorized: true`, every other authorization false;
- new G1 root absent and G2 root absent;
- exact watchdog binary present;
- frozen command still byte-for-byte identical in the packet;
- no tracked/staged content change after the authorization commit.

Any failure: do not invoke; restore G1 authorization false and record the
pre-execution blocker. Authorization remains unconsumed because no attempt was
made.

## 6. STEP 4 — the single authorized attempt

From repository root, start an operator stopwatch immediately around exactly
this command and invoke it once only:

```powershell
& 'C:\Program Files\Git\usr\bin\timeout.exe' -k 30 960 python scripts/v72p2d5_gf32_rate_mother.py --phase g1
```

Capture exact command, invocation count, stdout, stderr, exit code, and operator
outer wall seconds. Do not pipe, redirect, add flags, alter environment, or run
through a second wrapper. PowerShell stopwatch bookkeeping around the exact
line is allowed; it must not change the child command.

Once the process is launched, `G1 invoked exactly once=true` and authorization
is consumed. Exit meanings are records, not permission to retry:

- `0`: normal process completion; continue to STEP 5;
- `124`: watchdog timeout; retain any partial root VOID; continue to STEP 5;
- `3`: refusal; continue to STEP 5;
- any other exit/exception/crash: continue to STEP 5.

Never issue the command again for any reason.

## 7. STEP 5 — revoke immediately

Before opening or interpreting any produced file, change exactly:

`g1_execution_authorized: true→false`.

Verify all nine authorization keys false. If the edit fails, report the
critical blocker immediately and keep trying only the same state restoration;
do not inspect results first and do not modify any other field.

## 8. STEP 6 — record, do not accept

After revocation, stat the proposed G1 root without modifying it.

Create only:

`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_OPERATOR_RETURN_R1.md`

Record:

1. verbatim user authorization and both commit/base identities;
2. exact command, invocation count exactly one, exit code, operator outer wall,
   stdout, stderr, and watchdog interpretation;
3. root existence plus top-level filename/size/mtime listing;
4. if and only if the normal four-file bundle exists, literal scalar content
   required by frozen packet §4.7, including every per-f exact/syndrome/
   iteration/nonfinite/RSS aggregate, `decoder_calls`, stored `wall_seconds`,
   run peak RSS, `outcome`, and `passed`;
5. arithmetic-only recomputation: 440 call identity, failure fractions,
   attempted/count bounds, iteration bounds, signal predicate, stored outcome
   consistency, stored wall against 900 s, operator outer wall against 900 s,
   and RSS known + `<2 GiB`;
6. whether operator outer wall requires a later Pre-RESULT override of a stored
   outcome;
7. if root is absent/partial/malformed, say exactly that and label it recorded
   VOID/BLOCKED without manufacturing missing values;
8. pre/post stat comparison for every protected formal root and confirmation
   G2 remained absent;
9. authorization restored false and every prohibition result;
10. `NOT_ACCEPTED / PRE_RESULT_REVIEW_REQUIRED` and all nonclaims.

Reading the newly created G1 scalar files for this record is authorized.
Reading CAL/VAL/raw rows, Model-F arrays again, or VOID-G1 content is not.

Do not call a normal result accepted, qualified, valid FER, leakage, key rate,
or permission for G2. Do not change `next_gate` yet.

Stage exactly `cycle_state.yaml` and `G1_OPERATOR_RETURN_R1.md`. Require
`STAGED_COUNT 2`, then commit exactly:

```text
result(v72p2d5): record one authorized frozen G1 invocation

Records the sole authorized attempt, command outcome, operator wall, output
root, and literal G1 scalar evidence. g1_execution_authorized is restored to
false. Result not accepted; independent Pre-RESULT review remains required.

Co-Authored-By: OpenAI Codex <codex@openai.com>
```

Do not push.

If the run produced no ordinary bundle, still make the consumed-attempt record
and revocation commit. Never repair or rerun.

## 9. STEP 7 — final gates

Verify and report:

- all nine authorizations false;
- `next_gate` unchanged at `INDEPENDENT_G1_PRE_EXECUTE_REVIEW`;
- exactly two new commits after `6494b623`;
- G2 absent;
- no `.py`, OpenSpec, frozen packet, decision-log, or memory content change;
- no tracked/staged residual content change;
- no protected workspace root changed except the one-time additive proposed G1
  root created by the authorized command;
- no push.

Do not run tests or the G1 command again after execution.

## 10. Return format

Report these ten items:

1. verbatim user authorization;
2. fresh STEP 1 gate evidence;
3. authorization commit SHA and its three staged paths;
4. exact single command, invocation count, exit code, outer wall, stdout,
   stderr, watchdog status;
5. output-root listing and literal scalar payload, or exact absent/partial state;
6. arithmetic checks and frozen signal/outcome consistency without scientific
   interpretation;
7. revocation/operator-return commit SHA and its two staged paths;
8. final status plus pre/post protected-root equality and G2 absence;
9. true/false checklist: G1 invoked exactly once; authorization consumed; any
   retry/rerun/resume; command/parameter/seed/root change; P0/G2/other phase;
   G1 authorization false now; any other authorization changed; next_gate
   changed; any workspace delete/move/rename/overwrite; any `.py`/OpenSpec/
   frozen packet/decision-log/memory edit; pushed;
10. explicit statement that the record is not accepted and independent
    Pre-RESULT review is required.

End exactly:

`G1 已执行一次，授权已消耗；结果仅记录、尚未接受，必须经过独立 Pre-RESULT 复审；G2 未授权、未执行。`

