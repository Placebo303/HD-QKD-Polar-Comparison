# D7-D — one authorized schedule-discriminator invocation and Pre-RESULT R1

## 0. Verbatim authorization

> 我现在明确授权执行 D7-D flooding-vs-layered schedule discriminator：仅允许按冻结的
> `D7_D_EXECUTION_PACKET_R1.md`，在已评审的 WSL venv-on-PATH 环境中，使用冻结命令对一个
> 全新的 `workspace/d7_d_schedule_discriminator_<uuid>/` 根调用一次；共 256 个冻结
> scientific decoder calls，授权由首次 scientific decoder 尝试消耗，不因失败、超时、
> 部分结果或环境异常恢复；不得重试、重跑、恢复、复用根、修改参数或改变 estimator、
> prior、矩阵、seed、decoder 配置及 schedule 顺序；不得执行 R1d、任何 `--phase`、正式
> G1/G2、CAL、VAL、real/raw 或跨层 APP。执行结束后立即回收授权并进行独立 Pre-RESULT
> 复审；复审通过前不得接受或提交结果。

This packet implements only that authority.

## 1. Frozen baseline

- Repository: `HD-QKD_Polar_Comparison`, WSL checkout.
- Branch: `formal-ir-v72p1-addendum-clean`.
- Expected entry HEAD: `63f91d265d5eb540d6ca2726a27cd84fb1028b45`.
- Commit order: `1f472c2a -> 3a058992 -> 43f07186 -> 727bca7a -> 63f91d26`.
- Required verdicts: `D7_D_IMPLEMENTATION_REVIEW_PASS` and
  `D7_D_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION`.
- Required gate: `D7_D_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`.
- `d7d_execution_authorized: false`; all other authorization and promotion fields false.
- No `workspace/d7_d_schedule_discriminator_*` root and no prior D7-D UUID.
- D7-C accepted root, D7-B R2 root, Model-F root and all protected roots are immutable;
  R1d/G2 roots absent. Inspect protected roots only by names/sizes/mtime.

Preserve unrelated dirty/CRLF and pending SOP/workbuddy changes. Use scoped content diffs and
explicit manifests. No clean/reset/checkout/stash/rebase/amend/broad stage/push.

## 2. Exact scientific command

After E01-E14 pass, generate one UUID v4 and instantiate exactly:

```bash
timeout -k 30 1800 python scripts/v72p2d7_gf32_schedule_discriminator.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_d_schedule_discriminator_<uuid>
```

Invoke this child argv exactly once. Do not add flags, pipes, tee, redirection, `PYTHONPATH`,
concurrency or alternate Python/root. A parent harness may only capture time/stdout/stderr/exit
while preserving the child argv. The reviewed venv may be activated/prepended to PATH before the
command; record the adapter and interpreter identity. Run environment probes as separate commands,
never as a chained shell line.

## 3. Fresh gates E01-E14

Before UUID generation or state change independently verify:

- E01 branch, entry HEAD and five commits in §1;
- E02 unique required review verdicts and frozen packet/prereg consistency;
- E03 D7-D module/test/runner equal reviewed implementation; frozen constants and predecessor code
  have no scoped content drift;
- E04 state/gate/all authorization fields match §1;
- E05 zero D7-D result roots and zero previous UUID;
- E06 accepted D7-C/D7-B and Model-F metadata match recorded snapshots; R1d/G2 absent;
- E07 all protected-root metadata matches Pre-EXECUTE without reading protected content;
- E08 activate the reviewed WSL venv-on-PATH adapter as a separate operation;
- E09 Python/NumPy/kernel identities match reviewed environment or remain within an explicitly
  frozen compatibility allowance;
- E10 stdlib `resource` RSS is finite, positive and `<2 GiB` using KiB-to-byte conversion;
- E11 GNU `timeout` resolves; repeat its 3-second rehearsal only if environment/executable changed;
- E12 external-cwd sentinels reach exactly the reviewed row-layered and flooding functions plus the
  D5 Model-F loader, with zero calls, zero artifact read and zero root;
- E13 unauthorized exact-shape probe exits 3 before loader/decoder/root;
- E14 `workspace/` is writable while the selected target remains absent; never pre-create it.

Any failure: STOP before authorization, do not generate UUID, repair, rerun gates out of order or
execute.

## 4. Authorization commit

After all gates pass, generate the sole UUID once and confirm its target absent twice. Create
`docs/research_cycles/V72P2D7-GF32-SCHEDULE-DISCRIMINATOR/D7_D_AUTHORIZATION_RECORD_R1.md`
containing §0 verbatim, UUID/root/command, E01-E14 evidence, environment, timestamps, 256-call
contract, one-attempt consumption and claim ceiling.

Change only `d7d_execution_authorized: false -> true`; stage exactly record+state and commit locally:

`chore(d7-d): authorize one frozen schedule-discriminator invocation`

Reconfirm target absent. Do not add attempt/result fields yet.

## 5. Single execution and immediate revocation

Run §2 exactly once. Capture local+UTC start/end, exact child argv, invocation count, exit, outer
wall, stdout/stderr and timeout-124 status. When the process returns, before interpreting any result
content, change only `d7d_execution_authorized: true -> false` and commit it alone:

`chore(d7-d): consume and revoke one-shot execution authorization`

Never relaunch, resume, replace UUID, repair code or manually call either decoder. Mark scientific
attempt consumed only when at least one decoder attempt is evidenced; otherwise use
`NOT_VERIFIABLE`, which never restores authorization.

## 6. Unaccepted operator return

After revocation inspect only the new D7-D UUID root. It is immutable from process exit onward.
Create uncommitted `D7_D_OPERATOR_RETURN_R1.md` in the D7-D cycle directory and record:

- lifecycle/process evidence and exact seven-file/no-subdirectory inventory or honest partial state;
- frozen matrix/order and scheduled/invoked/missing/duplicate counts;
- paired exact and syndrome-only counts for all 128 identities;
- all eight stratum rows/labels and stored run terminal;
- iterations, node/edge work, crashes, nonfinite, status and mismatch arithmetic;
- per-call/stored/outer wall, RSS, watchdog and budget comparison;
- schedule-only identity proof and scalar-payload/no-cross-layer-APP disclosure;
- `NOT_ACCEPTED / PRE_RESULT_REVIEW_REQUIRED` and all scientific nonclaims.

Do not fill, mutate or reinterpret missing/partial artifacts.

## 7. One read-only verify

If root structure permits, invoke exactly once:

```bash
python scripts/v72p2d7_gf32_schedule_discriminator.py --verify workspace/d7_d_schedule_discriminator_<uuid>
```

Capture literal output/exit and confirm bytes/mtime unchanged. If impossible, record
`VERIFY_NOT_RUN`; do not retry.

## 8. Independent Pre-RESULT review

Use a reviewer context separate from execution. It may read only contracts, scoped code and the new
root, create only `D7_D_PRE_RESULT_REVIEW_R1.md`, and independently recompute R01-R20:

- R01 authorization text, fresh UUID, one invocation and true-to-false lifecycle;
- R02 exact WSL argv/PATH adapter/environment disclosure;
- R03 seven-file/no-subdirectory root or honest partial state and post-exit immutability;
- R04 exact 256 order and 128 identity pairs with all non-schedule inputs equal;
- R05 estimator/prior/H/seed/condition/decoder configuration equals D7-C contract;
- R06 row-layered/flooding implementation identities and no third schedule/cross-layer APP;
- R07 uniqueness, completeness, missing/duplicate/retry accounting;
- R08 exact isolated from syndrome-only, crash and nonfinite;
- R09 iterations plus node/edge work arithmetic, including iteration-zero semantics;
- R10 each `paired_schedule.csv` row recomputed from decoder records;
- R11 all eight stratum counts and labels recomputed by frozen first-match rules;
- R12 terminal recomputed in frozen T1-T10 priority order;
- R13 no early stop/replacement/concurrency and exact call cap;
- R14 120/1500/1800+30 wall and timeout consistency;
- R15 finite positive RSS and `<2 GiB` gate;
- R16 seven-file scalar-only schema and prohibited-payload absence;
- R17 sole verifier result and verifier limitations;
- R18 D7-C/D7-B/Model-F/protected roots unchanged and R1d/G2 absent;
- R19 authorization false and no prohibited action/root/phase;
- R20 root read twice unchanged, scoped Git state clean, no push and claim ceiling preserved.

Recompute from CSV/JSON, never trust summary/report. Any discrepancy is FAIL/BLOCKED with no
repair/rerun. Allowed verdicts only:

- `D7_D_PRE_RESULT_REVIEW_PASS_R1`
- `D7_D_PRE_RESULT_REVIEW_FAIL_R1`
- `D7_D_PRE_RESULT_REVIEW_BLOCKED_R1`

PASS means internal coherence only, not result acceptance or route authority.

## 9. Conditional solidification

Only after PASS, update state factually with attempts/completion/decoder/result/UUID/root/terminal;
authorization stays false; set `next_gate: INDEPENDENT_D7_D_RESULT_ACCEPTANCE_R1`; do not set any
accepted, qualification or promotion field. Stage only the UUID root, authorization record,
operator return, Pre-RESULT review and state, then commit locally:

`result(d7-d): record one reviewed schedule-discriminator invocation`

No push and no scientific decision-log/memory conclusion before main-thread acceptance.

On FAIL/BLOCKED retain the root immutable and uncommitted; operator return/review remain uncommitted;
only authorization/revocation commits stand. Never retry or repair in this packet.

## 10. Hard prohibitions

At most one scientific command and one verifier command. No R1d, `--phase`, G1/G2, CAL/VAL/
parquet/raw/real, cross-layer APP, estimator/prior/matrix/seed/decoder/schedule changes, code/test/
OpenSpec/frozen-packet edits, result-root mutation, broad Git action or push. No FER, leakage, key
rate, qualification, promotion, general schedule superiority or general NB-LDPC claim.

## 11. Return

Report delta only: E01-E14; UUID/command/times/exit/wall/stdout/stderr; authorization/revocation SHAs;
root inventory; 256/128 arithmetic; paired tables; eight strata; terminal/resources/work; verify;
R01-R20/verdict; conditional result SHA; final state/roots/auth/no-push; supported/unsupported claims.

PASS ending:

`D7-D 已按冻结命令执行一次，授权已消耗并回收；结果通过独立 Pre-RESULT 一致性复审但尚未被主线程接受，D7-C/D7-B 根保持 immutable，R1d、G1、G2 均未授权。`

FAIL/BLOCKED ending:

`D7-D 已到达唯一终态，授权已消耗并回收；Pre-RESULT 未通过，结果根原地保留且未提交，禁止重跑，R1d、G1、G2 均未授权。`
