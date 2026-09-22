# D7-B — one authorized WSL R2 invocation and independent Pre-RESULT

## 0. Verbatim fresh authorization

> 我现在明确重新授权执行 D7-B easy-regime（WSL R2，与此前已耗尽的授权和 UUID
> 无关）：仅允许按 `D7_B_EXECUTION_PACKET_R1.md` 及
> `D7_B_EXECUTION_PACKET_ADDENDUM_WSL_A1.md`，使用命令
> `timeout -k 30 1800 python scripts/v72p2d7_gf32_easy_regime.py --out-root
> workspace/d7_b_easy_regime_<new_uuid>` 对一个全新的 UUID 根调用一次；授权由首次
> scientific decoder 尝试消耗，不因失败、超时、部分结果或启动异常恢复；不得重试、
> 重跑、恢复、复用任何旧 UUID 或修改参数；不得执行 R1d、任何 `--phase`、正式
> G1/G2、Model-F、CAL、VAL、real/raw。执行结束后立即回收授权并进行独立
> Pre-RESULT 复审，复审通过前不得接受或提交结果。

This fresh authority applies only to WSL R2. It does not revive the prior
authorization or UUID `0f1ad3ec-f9e0-463f-a7dd-d9880ff7230c`.

## 1. Baseline and binding contracts

- Repository: current WSL checkout corresponding to
  `HD-QKD_Polar_Comparison`; derive its path, do not hard-code `/mnt/...`.
- Branch: `formal-ir-v72p1-addendum-clean`
- Expected HEAD: `48a5d39`
- Original freeze: `D7_B_EXECUTION_PACKET_R1.md`
- WSL shell addendum: `D7_B_EXECUTION_PACKET_ADDENDUM_WSL_A1.md`
- WSL repair review: `D7_B_WSL_LAUNCH_REWORK_REVIEW_PASS`
- Renewed Pre-EXECUTE verdict:
  `D7_B_PRE_EXECUTE_REVIEW_PASS_WSL_R2_AWAITING_FRESH_AUTHORIZATION`
- Expected gate: `D7_B_WSL_READY_AWAITING_FRESH_EXPLICIT_AUTHORIZATION`
- `d7b_execution_authorized: false`
- attempts/completed `0/0`, decoder/result `false/false`
- no `workspace/d7_b_easy_regime_*` root, no R1d root, no G2 root

The previous R1 blocked launch, its two lifecycle commits, return, review and
disposition must remain immutable. It had no result root and no scientific
outcome. Do not reuse its UUID, files or command record as R2 evidence.

Known unrelated dirty/CRLF and pending SOP/workbuddy administration remain out
of scope. Use explicit manifests and content numstat. No clean/reset/checkout/
stash/rebase/amend/broad-stage/push.

## 2. Exact command and one-UUID rule

Generate one new UUID v4 exactly once after all preflight gates pass. Record it
before launch. Instantiate and invoke exactly:

```bash
timeout -k 30 1800 python scripts/v72p2d7_gf32_easy_regime.py --out-root workspace/d7_b_easy_regime_<new_uuid>
```

Do not add arguments, `PYTHONPATH`, environment overrides, pipes, tee,
redirection or wrappers that alter the inner command. A timing harness may
launch the command as a child while preserving its argv exactly and capturing
stdout/stderr/exit/wall.

This scientific command is invoked at most once. A startup failure, exit 124,
nonzero exit, partial root, missing file or unexpected terminal does not permit
another invocation.

Environment/preflight probes must be separate commands. Never chain RSS,
timeout, import/bind and scientific execution on one shell line.

## 3. Fresh gates R2-E01–E12

Before changing authorization:

- E01 branch/HEAD and commits `13c1c3c`, `cc387e7`, `04b7a8e`, `4b61039`,
  `48a5d39` are present in order;
- E02 original packet, WSL addendum and both WSL PASS verdicts agree;
- E03 scoped runner/core/test files equal the reviewed implementation; v35,
  D5, D7-A and scientific constants/schema have no drift;
- E04 state/gate/auth/attempt/result fields match §1;
- E05 old UUID is absent and permanently barred; zero D7-B result roots;
- E06 generate no UUID yet; confirm root parent and protected metadata only;
- E07 R1d/G2 absent and protected roots names/sizes/mtime match renewed review;
- E08 actual `sys.executable`, Python/NumPy, WSL kernel/distro recorded;
- E09 live RSS is positive integer `<2GiB`;
- E10 `timeout` resolves to reviewed GNU implementation and metadata/version is
  unchanged; do not repeat rehearsal unless binary/WSL environment changed;
- E11 from external cwd with initial repo/src absent from `sys.path`, runner
  package bind reaches exact v35 callable with zero invocation/root;
- E12 unauthorized exact-shape command using a disposable barred probe path
  exits 3 before bind/root; it is not the scientific UUID and must not create
  any directory.

If any gate fails, STOP before authorization and do not generate the R2 UUID.
Do not install pytest or dependencies as a remedy.

## 4. Authorization record and commit

After E01–E12 pass, generate the sole R2 UUID and confirm its root absent.
Create:

`docs/research_cycles/V72P2D7-GF32-EASY-REGIME/D7_B_AUTHORIZATION_RECORD_R2.md`

Include §0 verbatim, WSL environment, exact UUID/root/command, all gate outputs,
old-UUID prohibition, once-only rule, time zone and claim ceiling.

Change only `d7b_execution_authorized: false -> true`. Stage exactly record +
state and commit locally:

`chore(d7-b): authorize one fresh WSL R2 easy-regime invocation`

No attempt/result fields change yet. Reconfirm new root absent after commit.

## 5. Single invocation and immediate revocation

Run the exact instantiated command once. Capture start/end local+UTC, argv,
invocation count, exit, outer wall, literal stdout/stderr and timeout status.

When the process returns, before interpreting artifacts, change only
`d7b_execution_authorized: true -> false` and commit it alone:

`chore(d7-b): consume and revoke WSL R2 execution authorization`

Authorization remains false thereafter. Never relaunch.

Record:

- `command_invocations: 1`;
- `scientific_attempt_consumed: true` if at least one decoder attempt is
  evidenced;
- otherwise `NOT_VERIFIABLE`, never a basis to rerun.

## 6. Unaccepted operator return

Inspect only the new R2 UUID root after revocation. Do not read R1d, formal,
VOID, Model-F, CAL, VAL or real/raw contents.

Create uncommitted:

`D7_B_OPERATOR_RETURN_R2.md`

under the D7-B cycle directory. Include:

- execution provenance and exact process evidence;
- root names/sizes/mtime and no-subdirectory check;
- frozen manifest identity;
- scheduled/invoked/not-needed/budget-not-reached arithmetic;
- stored terminal/aggregate flags;
- per tier/prior/seed first exact cap and exact/syndrome status;
- tractable posterior/MAP errors;
- crashes/nonfinite/statuses;
- call, wall, watchdog and RSS comparisons;
- `NOT_ACCEPTED / PRE_RESULT_REVIEW_REQUIRED` and explicit nonclaims.

Do not modify or fill the result root after process exit. Partial output remains
immutable.

## 7. One read-only verify

If the root contains enough structure, run exactly once:

```bash
python scripts/v72p2d7_gf32_easy_regime.py --verify workspace/d7_b_easy_regime_<new_uuid>
```

Capture literal output/exit. This is a non-decoder read-only verifier, not the
scientific invocation. If root absent/unreadable, record `VERIFY_NOT_RUN`; do
not retry.

## 8. Independent Pre-RESULT R2

Use a reviewer context separate from execution. It may read only the new UUID
root and frozen D7-B contracts/code. It must independently recompute from CSV
and JSON rather than trusting summary/report.

Create only `D7_B_PRE_RESULT_REVIEW_R2.md`. Check R01–R18:

- R01 fresh authorization, old UUID exclusion and exactly-one lifecycle;
- R02 WSL command equals addendum and scientific argv unchanged;
- R03 fresh-root/no-overwrite/five-file/no-subdir or honest partial status;
- R04 manifest tiers, priors, seeds, caps, TREE_6 A1 and budgets;
- R05 records `<=420`, schema and uniqueness;
- R06 cap ordering/early-stop/not-needed semantics;
- R07 scheduled/invoked/not-needed/budget-not-reached reconciliation;
- R08 exact, syndrome, iterations, unsatisfied and symbol errors;
- R09 posterior/MAP tolerance for tractable tiers;
- R10 crash/nonfinite/status accounting;
- R11 terminal priority independently recomputed;
- R12 P99/P90 confirmation/partial predicates and P60/PAIR non-veto;
- R13 per-call/stored/outer wall and exit/watchdog consistency;
- R14 RSS known/max `<2GiB` or correct resource terminal;
- R15 scalar-only payload, no forbidden vectors/data;
- R16 one verifier result and disclosed verifier limits;
- R17 authorization false, no prohibited phase/data/root activity;
- R18 root read twice unchanged, protected metadata unchanged, no push.

Allowed verdicts:

- `D7_B_PRE_RESULT_REVIEW_PASS_R2`
- `D7_B_PRE_RESULT_REVIEW_FAIL_R2`
- `D7_B_PRE_RESULT_REVIEW_BLOCKED_R2`

Any discrepancy is FAIL/BLOCKED. No repair or rerun.

## 9. Solidification

Only after PASS:

- update state factually: attempts=1; completed=1 only for a coherent normal
  completion; decoder/result booleans only if evidenced; store UUID/root and
  terminal; keep auth false; set
  `next_gate: INDEPENDENT_D7_B_RESULT_ACCEPTANCE_R2`; do not accept result;
- stage only R2 root, authorization record, operator return, Pre-RESULT review
  and state;
- commit locally:
  `result(d7-b): record one reviewed WSL R2 easy-regime invocation`;
- do not push or append a scientific conclusion to memory before main-thread
  acceptance.

On FAIL/BLOCKED: auth remains false; retain root immutable; do not commit root,
return or review; no result/state conclusion commit beyond authorization and
revocation commits.

## 10. Hard boundaries

No retry/rerun/resume/replacement UUID; no R1d/`--phase`/G1/G2; no Model-F,
CAL, VAL, real/raw or VOID content; no code/test/OpenSpec/frozen-packet edits;
no result-root mutation; at most one scientific and one verifier invocation;
no broad Git operation or push; no FER/leakage/key-rate/qualification claim.

## 11. Return

Report delta only: E01–E12, UUID/command/process evidence, auth+revoke SHAs,
root/aggregates/recomputed matrix, resource arithmetic, verify, R01–R18 and
verdict, conditional result SHA, final state/roots/auth/no-push/nonclaims.

PASS ending:

`D7-B WSL R2 已按冻结命令执行一次，授权已消耗并回收；结果通过独立 Pre-RESULT 一致性复审但尚未被主线程接受，R1d、G1、G2 均未授权。`

FAIL/BLOCKED ending:

`D7-B WSL R2 已到达唯一终态，授权已消耗并回收；Pre-RESULT 未通过，结果根原地保留且未提交，禁止重跑，R1d、G1、G2 均未授权。`

