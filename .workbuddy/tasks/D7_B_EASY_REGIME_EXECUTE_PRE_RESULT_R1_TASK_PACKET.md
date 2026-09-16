# D7-B — one authorized easy-regime invocation and independent Pre-RESULT R1

## 0. Verbatim user authorization

> 我现在明确授权执行 D7-B easy-regime：仅允许按已冻结的
> `D7_B_EXECUTION_PACKET_R1.md` 对一个全新的
> `workspace/d7_b_easy_regime_<uuid>/` 根进行且仅进行一次调用；授权由首次
> scientific decoder 尝试消耗，不因失败、超时或部分结果而恢复；不得重试、
> 重跑、恢复、复用根或修改任何参数；不得执行 R1d、任何 `--phase`、正式
> G1/G2、Model-F、CAL、VAL、real/raw。执行后必须停止并进行独立
> Pre-RESULT 复审，复审通过前不得接受或提交结果。

This packet operationalizes that authorization without expanding it.

## 1. Frozen sources and baseline

- Repository: `D:/Code/HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`
- Expected starting HEAD: `7f439036`
- Frozen execution packet:
  `docs/research_cycles/V72P2D7-GF32-EASY-REGIME/D7_B_EXECUTION_PACKET_R1.md`
- Preregistration:
  `docs/research_cycles/V72P2D7-GF32-EASY-REGIME/D7_B_PREREG_R1.md`
- Implementation review verdict: `D7_B_IMPLEMENTATION_REVIEW_PASS`
- Pre-EXECUTE verdict:
  `D7_B_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION`
- Implementation commit: `a5d5ce4e`
- Freeze commit: `f40e3376`
- Readiness/closeout commit: `7f439036`

The commit IDs are provenance, not authorization tokens. The verbatim user
statement in §0 is the sole authority.

Expected state before authorization commit:

- `d7b_execution_authorized: false`
- `d7b_execution_attempts: 0`
- `d7b_execution_completed: 0`
- `decoder_executed: false`
- `result_created: false`
- all other execution authorization keys false
- `scientific_promotion: false`
- `next_gate: D7_B_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`
- no `workspace/d7_b_easy_regime_*` root
- no R1d root and no G2 root

Known SOP/workbuddy administrative changes and unrelated dirty/CRLF paths are
outside scope. Preserve them. Use explicit path manifests and content
`numstat`; do not demand global porcelain cleanliness. Never clean, reset,
checkout, stash, rebase, amend, broad-stage or push.

Any baseline deviation is a hard STOP before authorization is flipped.

## 2. Exact frozen invocation

Generate exactly one UUID using the standard UUID v4 generator. Store its
literal value in the authorization record before execution. Do not generate a
second UUID for fallback.

Instantiate `<uuid>` in exactly this command and make exactly one invocation:

```powershell
& 'C:\Program Files\Git\usr\bin\timeout.exe' -k 30 1800 python scripts/v72p2d7_gf32_easy_regime.py --out-root workspace/d7_b_easy_regime_<uuid>
```

No argument, order, executable, timeout, path, seed, cap, prior, structure,
threshold, budget or environment injection may change. Do not add tee,
redirection or a shell pipeline to the scientific command. Capture stdout,
stderr, process exit code and outer wall with a wrapper that leaves the inner
command text unchanged.

Run environment probes as separate commands. Never chain RSS, binary checks,
watchdog rehearsal and the scientific command on one PowerShell line.

## 3. Fresh execution gates E01–E10

Perform fresh read-only checks immediately before the authorization commit:

- E01 branch, HEAD and three frozen commits are present;
- E02 frozen packet/prereg and both PASS verdicts exist and agree;
- E03 scoped implementation/test/script diff from `a5d5ce4e` is empty;
- E04 state matches §1 and every authorization key is false;
- E05 exactly zero D7-B result roots; chosen UUID root absent;
- E06 R1d and G2 roots absent; protected roots match Pre-EXECUTE metadata using
  names/sizes/mtime only; do not read formal or VOID contents;
- E07 `timeout.exe` exists; do not repeat the 3-second rehearsal unless its
  prior accepted evidence is missing or the binary metadata changed;
- E08 live RSS probe returns positive integer `<2GiB` as a separate command;
- E09 targeted compile/tests from the accepted Pre-EXECUTE review need not be
  rerun if scoped code is unchanged; if code differs, STOP rather than test it;
- E10 target parent can be created without the chosen root already existing;
  do not pre-create the root.

Record exact outputs in `D7_B_AUTHORIZATION_RECORD_R1.md`. If any gate fails,
do not flip authorization and do not invoke the command.

## 4. Authorization commit

Create:

`docs/research_cycles/V72P2D7-GF32-EASY-REGIME/D7_B_AUTHORIZATION_RECORD_R1.md`

It must contain §0 verbatim, the UUID/root, exact instantiated command, E01–E10
evidence, time zone, attempt-consumption rule, no-retry rule and claim ceiling.

Change only `d7b_execution_authorized: false -> true` in `cycle_state.yaml`.
Do not change attempts/completed/result fields yet.

Stage exactly those two paths and commit locally:

`chore(d7-b): authorize one frozen easy-regime invocation`

Include the repository-standard `Co-Authored-By: OpenAI Codex` trailer if used
by the current cycle. Do not push.

Recheck the target is absent immediately after the commit.

## 5. Exactly-once execution and immediate revocation

Invoke the instantiated command once. Authorization applies to this invocation
only. Never retry, rerun, resume, create another root, or manually call the
historical decoder if the command fails, returns 124/3/nonzero, partially
writes, or produces unexpected output.

Capture:

- start/end local and UTC times;
- exact command and UUID;
- invocation count (must be 1);
- process exit code;
- outer wall seconds;
- literal stdout and stderr;
- whether timeout exit 124 occurred;
- whether the root exists and its names/sizes/mtime metadata.

As soon as the process returns—and before scientific interpretation—change
only `d7b_execution_authorized: true -> false`. Commit this revocation alone:

`chore(d7-b): consume and revoke one-shot execution authorization`

This revocation happens regardless of whether the first decoder attempt was
reached. The single permitted command invocation is never restored. Record the
distinction later as:

- `command_invocations: 1` always after launch;
- `scientific_attempt_consumed: true` only if artifacts/logs prove at least one
  decoder call was attempted;
- `scientific_attempt_consumed: NOT_VERIFIABLE` if the process/root cannot
  establish it;
- never `false` as a basis for another invocation.

## 6. Operator return before acceptance

After authorization is false, inspect only the new UUID root. Do not open any
formal, VOID, Model-F, CAL, VAL, real/raw or R1d evidence.

Create uncommitted:

`docs/research_cycles/V72P2D7-GF32-EASY-REGIME/D7_B_OPERATOR_RETURN_R1.md`

Record literal facts without accepting them:

- command/exit/walls/stdout/stderr;
- root file inventory and no-subdirectory result;
- manifest identity and frozen parameters;
- scheduled/invoked/not-needed/budget-not-reached counts;
- stored terminal and all aggregate flags;
- per-tier/per-prior/per-seed exact+syndrome outcomes and first successful cap;
- tractable posterior/MAP errors;
- crash/nonfinite/status counts;
- max per-call wall, stored run wall, RSS known/max and limits;
- explicit `NOT_ACCEPTED / PRE_RESULT_REVIEW_REQUIRED`;
- all forbidden claims.

Do not edit the result root. Do not manually fill missing evidence. A partial
root remains immutable and is reviewed as partial/VOID.

## 7. One read-only verifier invocation

If and only if the root exists with enough structure to invoke the accepted
verifier, run exactly once:

```powershell
python scripts/v72p2d7_gf32_easy_regime.py --verify workspace/d7_b_easy_regime_<uuid>
```

This is a non-decoder, read-only verification command and is not a scientific
rerun. Capture its literal output and exit. Do not rerun it if it fails. If the
root is absent or unreadable, record `VERIFY_NOT_RUN` with the exact reason.

## 8. Independent Pre-RESULT review

Use a reviewer context that did not execute the run and does not edit code or
artifacts. Create only:

`docs/research_cycles/V72P2D7-GF32-EASY-REGIME/D7_B_PRE_RESULT_REVIEW_R1.md`

The reviewer independently checks R01–R16:

- R01 verbatim authorization, UUID and exactly-one invocation lifecycle;
- R02 frozen command/parameters match packet and prereg;
- R03 target was fresh, five files/no subdirs or honest partial-root status;
- R04 manifest tiers/priors/seeds/caps/budgets and TREE_6 A1 identity;
- R05 decoder-record schema, row accounting and call count `<=420`;
- R06 cap ladders ordered and later caps correctly marked after exact;
- R07 scheduled/invoked/not-needed/budget-not-reached arithmetic;
- R08 exact/syndrome/iterations/unsatisfied/symbol-error consistency;
- R09 SINGLE_CHECK_D3 and TREE_6 posterior/MAP tolerance;
- R10 crash/nonfinite and terminal-priority recomputation;
- R11 P99/P90/P60/PAIR roles and confirmed/partial conditions;
- R12 per-call wall, stored wall, outer wall, watchdog and RSS gates;
- R13 scalar-only payload and absence of priors/beliefs/truth/syndrome vectors;
- R14 accepted verifier output, including disclosed verifier limitations;
- R15 authorization now false, no other authorization/state overreach, no
  R1d/G1/G2/phase/data-boundary violation;
- R16 protected roots unchanged, result root read twice unchanged, no push.

The reviewer must recompute counts/classification from JSON/CSV, not merely
quote `summary.json`. Any discrepancy is blocking. Do not fix or rerun.

Allowed verdicts:

- `D7_B_PRE_RESULT_REVIEW_PASS`
- `D7_B_PRE_RESULT_REVIEW_FAIL`
- `D7_B_PRE_RESULT_REVIEW_BLOCKED`

PASS means only that the result is internally coherent and ready for separate
main-thread acceptance. It does not accept the scientific result or authorize
R1d/D7-C/D/G1/G2.

## 9. Result solidification rule

### If Pre-RESULT PASS

Only after the review verdict is written and read back:

1. update `cycle_state.yaml` factually:
   - `d7b_execution_authorized: false`
   - `d7b_execution_attempts: 1`
   - `d7b_execution_completed: 1` only for normal process completion with a
     coherent complete root, otherwise 0;
   - `decoder_executed: true` only if decoder calls are evidenced;
   - `result_created: true` only if the five-file root is complete;
   - add stored terminal and UUID/root fields;
   - `next_gate: INDEPENDENT_D7_B_RESULT_ACCEPTANCE`;
   - do not set `result_accepted`, qualification or promotion.
2. stage only the new UUID root, authorization record, operator return,
   Pre-RESULT review and cycle state;
3. verify the staged manifest contains no other workspace/docs path;
4. commit locally:

`result(d7-b): record one authorized easy-regime invocation and review`

Do not push. Do not update decision log or long-term memory with a scientific
conclusion before main-thread acceptance; only lifecycle facts may be appended
if required, preferably leave them for the acceptance packet.

### If FAIL or BLOCKED

- keep authorization false;
- do not commit the result root, operator return or review;
- retain the new root immutable in place, complete or partial;
- make no result/acceptance/state conclusion commit beyond the already committed
  authorization and revocation lifecycle;
- return the failing R-ID and exact evidence to the main thread.

No repair, retry, rerun, resume, parameter change or replacement UUID is
permitted.

## 10. Hard STOP rules

Before launch, STOP if any E gate fails. After launch, every anomaly becomes
record/review evidence, never a reason to invoke again.

At all times prohibit:

- R1d, any `--phase`, formal G1/G2;
- Model-F, CAL, VAL, real/raw or VOID content reads;
- edits to v35/D5/D7-A/D7-B production code, tests, OpenSpec or frozen packets;
- result-root mutation after process exit;
- more than one scientific command or verifier command;
- broad Git operations, cleanup or push;
- interpreting easy-regime outcomes as FER, leakage, key rate, qualification or
  actual-channel recovery.

## 11. Return format

Report deltas only:

1. verbatim authorization and E01–E10;
2. UUID, exact command, invocation count, exit, outer wall, stdout/stderr;
3. authorization and revocation commit SHAs;
4. root inventory and literal stored aggregates;
5. independently recomputed per-tier/prior outcomes and arithmetic;
6. time/RSS/call budget comparisons;
7. verifier command/output/exit or NOT_RUN reason;
8. R01–R16 table and independent verdict;
9. result commit SHA only if PASS, otherwise explicit no-result-commit;
10. final state/auth/protected roots/R1d/G2/no-push checklist;
11. supported and unsupported claim boundary.

If PASS, end exactly:

`D7-B 已按冻结命令执行一次，授权已消耗并回收；结果通过独立 Pre-RESULT 一致性复审但尚未被主线程接受，R1d、G1、G2 均未授权。`

If FAIL/BLOCKED, end exactly:

`D7-B 已按冻结命令执行至唯一终态，授权已消耗并回收；Pre-RESULT 未通过，结果根原地保留且未提交，禁止重跑，R1d、G1、G2 均未授权。`

