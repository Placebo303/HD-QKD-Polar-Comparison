# D7-C — one authorized bidirectional-oracle invocation and Pre-RESULT R1

## 0. Verbatim authorization

> 我现在明确授权执行 D7-C bidirectional oracle：仅允许按冻结的
> `D7_C_EXECUTION_PACKET_R1.md`，在已记录且验证可用的 WSL venv-on-PATH
> 环境中，使用冻结命令对一个全新的
> `workspace/d7_c_bidirectional_oracle_<uuid>/` 根调用一次；共 128 个冻结
> scientific decoder calls，授权由首次 scientific decoder 尝试消耗，不因失败、
> 超时、部分结果或环境异常恢复；不得重试、重跑、恢复、复用根、修改参数或更换
> estimator；不得执行 R1d、任何 `--phase`、正式 G1/G2、CAL、VAL、real/raw 或
> 跨层 APP。执行结束后立即回收授权并进行独立 Pre-RESULT 复审，复审通过前不得
> 接受或提交结果。

This packet implements only that authority.

## 1. Baseline

- Current WSL checkout of `HD-QKD_Polar_Comparison`
- Branch `formal-ir-v72p1-addendum-clean`
- Expected HEAD `4ba36bfb`
- Frozen packet `D7_C_EXECUTION_PACKET_R1.md`
- Implementation review `D7_C_IMPLEMENTATION_REVIEW_PASS`
- Pre-EXECUTE review
  `D7_C_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION`
- Gate `D7_C_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`
- `d7c_execution_authorized: false`
- decoder/result false; no attempt/completion fields yet
- no `workspace/d7_c_bidirectional_oracle_*` root and no UUID
- D7-B R2 root immutable; R1d/G2 absent; all other authorization false
- layer-interface implementation remains deferred; D7-C does not use it

The D7-B and Model-F roots are protected inputs. Before execution inspect only
names/sizes/mtime. The authorized scientific command may read the accepted
Model-F binary root; no other step may read Model-F content. No CAL/VAL/parquet/
raw/real or VOID content is permitted.

Preserve unrelated dirty/CRLF and pending SOP/workbuddy changes. Use explicit
manifests/content numstat. No clean/reset/checkout/stash/rebase/amend/broad
stage/push.

## 2. Exact scientific command

After all gates pass, generate exactly one UUID v4 and instantiate:

```bash
timeout -k 30 1800 python scripts/v72p2d7_gf32_bidirectional_oracle.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_c_bidirectional_oracle_<uuid>
```

Invoke this argv exactly once. Do not add arguments, pipes, tee, redirection,
`PYTHONPATH`, alternate estimator, alternate Python executable or replacement
root. A parent timing/capture harness may preserve the child argv exactly.

The shell may activate or prepend the already reviewed venv to PATH before the
command. Record the exact activation/PATH adapter and prove `command -v python`,
`python --version`, NumPy version and `sys.executable`. This operational adapter
must not alter repository files or scientific argv.

Environment probes run as separate commands. Never chain RSS, timeout,
interpreter, Model-F metadata and scientific execution in one shell line.

## 3. Fresh gates E01–E14

Before generating the UUID or changing state:

- E01 branch/HEAD and five D7-C commits `86f6baf6`, `0c304875`, `391fc6b0`,
  `ca00b234`, `4ba36bfb` are present in order;
- E02 packet/prereg/A1 proposal review/implementation review/Pre-EXECUTE
  verdicts are unique and consistent;
- E03 scoped implementation/script/tests equal reviewed commits; v35/D5/D7-A/
  D7-B and frozen scientific constants have no content drift;
- E04 state, gate and all authorization fields match §1;
- E05 zero D7-C roots and no prior D7-C UUID;
- E06 D7-B R2 and Model-F metadata match accepted snapshots; R1d/G2 absent;
- E07 protected-root metadata matches Pre-EXECUTE; no content reads;
- E08 activate the reviewed WSL venv-on-PATH adapter as a separate operation;
- E09 interpreter/NumPy/WSL identities match reviewed environment or differences
  are non-scientific and explicitly accepted by the frozen compatibility range;
- E10 live stdlib RSS is finite, positive and `<2GiB`, with KiB→bytes rule;
- E11 GNU `timeout` resolves and version/metadata matches; repeat 3-second
  rehearsal only if executable/environment changed, as its own command;
- E12 external-cwd local-source bind probe reaches exact Model-F loader and
  exact historical decoder sentinels without reading artifact/calling decoder/
  creating root;
- E13 unauthorized exact-shape probe exits 3 before Model-F/decoder/root;
- E14 parent `workspace/` is writable while chosen target remains uncreated;
  do not pre-create target.

If any gate fails, STOP before authorization and do not generate UUID.

## 4. Authorization commit

Generate the sole UUID only after E01–E14 PASS. Confirm target absent twice.
Create:

`docs/research_cycles/V72P2D7-GF32-BIDIRECTIONAL-ORACLE/D7_C_AUTHORIZATION_RECORD_R1.md`

Include §0 verbatim, UUID/root/command, all gates, interpreter/PATH adapter,
times/timezone, estimator identity, one-attempt rule and claim ceiling.

Change only `d7c_execution_authorized: false -> true`. Stage exactly record and
state; commit locally:

`chore(d7-c): authorize one frozen bidirectional-oracle invocation`

Do not add attempt/result fields yet. Reconfirm target absent.

## 5. Single execution and immediate revocation

Run the exact command once. Capture start/end local+UTC, exact child argv,
invocation count, exit, outer wall, stdout/stderr and timeout-124 status.

When it returns, before interpreting root contents, change only
`d7c_execution_authorized: true -> false` and commit alone:

`chore(d7-c): consume and revoke one-shot execution authorization`

Never relaunch, resume, replace UUID or manually call decoder. Record
`scientific_attempt_consumed: true` only when at least one decoder attempt is
evidenced; otherwise `NOT_VERIFIABLE`, never grounds for retry.

## 6. Unaccepted operator return

After revocation, inspect only the new D7-C UUID root. It is immutable from
process exit onward. Create uncommitted:

`D7_C_OPERATOR_RETURN_R1.md`

under the D7-C cycle directory. Record:

- process and lifecycle evidence;
- exact six-file/no-subdir inventory or honest partial/absent state;
- manifest estimator, Model-F identity, seeds, f/rows, call ordering;
- scheduled/invoked/missing/duplicate counts;
- per `(f,layer)` marginal/oracle paired 2×2 counts;
- exact/syndrome/iterations/crash/nonfinite/status summaries;
- all four stratum labels and stored run terminal;
- call/stored/outer wall and RSS limits;
- belief-provenance labels and proof no returned belief crossed layers;
- `NOT_ACCEPTED / PRE_RESULT_REVIEW_REQUIRED` and nonclaims.

Do not inspect CAL/VAL/raw or modify/fill the root.

## 7. One read-only verify

If root structure permits, invoke exactly once:

```bash
python scripts/v72p2d7_gf32_bidirectional_oracle.py --verify workspace/d7_c_bidirectional_oracle_<uuid>
```

Capture literal output/exit. This command must not load Model-F or decoder. If
root absent/unreadable, record `VERIFY_NOT_RUN`; do not retry.

## 8. Independent Pre-RESULT

Use a reviewer context separate from execution. It reads only frozen contracts,
code and the new root. Create only `D7_C_PRE_RESULT_REVIEW_R1.md` and
independently check R01–R20:

- R01 verbatim authorization, fresh UUID and exactly-one lifecycle;
- R02 exact WSL argv, PATH adapter disclosure and estimator identity;
- R03 fresh six-file/no-subdir root or honest partial state;
- R04 manifest 16 seeds ×2 f ×4 conditions and exact call order;
- R05 accepted concentration semantics and prior formulas;
- R06 no CAL/VAL/raw/real/VOID or cross-layer returned-belief use;
- R07 record uniqueness/completeness and exactly 128 normal calls;
- R08 pair identity equality across marginal/oracle conditions;
- R09 exact remains separate from syndrome and oracle truth never upgrades it;
- R10 iterations/status/symbol-errors/unsatisfied arithmetic;
- R11 nonfinite/crash accounting and fail-closed priority;
- R12 per-stratum marginal/oracle/both/neither 2×2 counts sum to 16;
- R13 oracle-only/marginal-only and all four stratum labels recomputed;
- R14 run terminal independently recomputed in frozen T1–T11 order;
- R15 120/1500/1800 wall and exit/watchdog consistency;
- R16 RSS finite/known/max and `<2GiB` gate;
- R17 scalar-only payload and belief-provenance wording;
- R18 sole verifier outcome and verifier limitations;
- R19 authorization false, no prohibited phase/root/action;
- R20 root read twice unchanged, protected metadata unchanged, no push.

Recompute from CSV/JSON; do not trust summary/report. Any discrepancy is
FAIL/BLOCKED and receives no repair/rerun.

Allowed verdicts:

- `D7_C_PRE_RESULT_REVIEW_PASS_R1`
- `D7_C_PRE_RESULT_REVIEW_FAIL_R1`
- `D7_C_PRE_RESULT_REVIEW_BLOCKED_R1`

PASS means internal coherence only, not result acceptance or route authority.

## 9. Conditional solidification

Only after PASS:

- update state factually with attempts=1, completed according to coherent normal
  completion, decoder/result booleans, UUID/root/stored terminal; auth remains
  false; set `next_gate: INDEPENDENT_D7_C_RESULT_ACCEPTANCE_R1`; do not set
  accepted/qualification/promotion;
- stage only UUID root, authorization record, operator return, Pre-RESULT review
  and state;
- commit locally:
  `result(d7-c): record one reviewed bidirectional-oracle invocation`;
- no push and no scientific memory/decision conclusion before main acceptance.

On FAIL/BLOCKED, retain root immutable and uncommitted; return/review remain
uncommitted; only authorization/revocation commits stand. No retry or repair.

## 10. Hard prohibitions

At most one scientific command and one verifier command. No R1d, `--phase`,
G1/G2, CAL/VAL/parquet/raw/real, cross-layer APP, estimator/parameter/code/test/
OpenSpec/frozen-packet edits, result-root mutation, broad Git operation or push.
Do not claim FER, leakage, key rate, qualification or general algorithm success.

## 11. Return

Report delta only: E01–E14; UUID/command/times/exit/wall/stdout/stderr; auth and
revoke SHAs; root inventory; 128-call and pair arithmetic; four stratum labels;
terminal/resources; verify; R01–R20/verdict; conditional result SHA; final
state/roots/auth/no-push; supported and unsupported claims.

PASS ending:

`D7-C 已按冻结命令执行一次，授权已消耗并回收；结果通过独立 Pre-RESULT 一致性复审但尚未被主线程接受，D7-B 根保持 immutable，R1d、G1、G2 均未授权。`

FAIL/BLOCKED ending:

`D7-C 已到达唯一终态，授权已消耗并回收；Pre-RESULT 未通过，结果根原地保留且未提交，禁止重跑，R1d、G1、G2 均未授权。`

