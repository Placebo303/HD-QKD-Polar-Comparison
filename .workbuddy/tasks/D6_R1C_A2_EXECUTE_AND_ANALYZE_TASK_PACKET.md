# D6 R1c-A2 §8 — authorized execution and analysis packet

## 0. Authority, role, and terminal conditions

The user gave this exact authorization:

> 我现在明确授权执行 D6 R1c-A2 §8：仅允许使用冻结的 R1c-A2 实现，对一个全新的 `workspace/d6_graph_mother_r1c_<uuid>/` 根进行一次 development-only 执行；使用固定 Model-F 输入根和 `--workers 18` 请求值，实际并发只能按已评审的 RSS 规则向下调整；总计不超过 2500 次 decoder 调用、12 小时 wall、单次调用 120 秒、总 RSS 小于 2 GiB。授权由首次科学 decoder 尝试消耗；不得重试、恢复、复用任何 VOID 根、修改参数或代码，不得执行任何 `--phase`、正式 G1、G2、VAL、real/raw。运行结束后必须停止并进行独立 Pre-RESULT 复审，复审通过前不得接受或提交结果。

This packet delegates the complete bounded sequence: fresh gate, authorization
record, exactly one R1c-A2 development run, immediate revocation, mechanical
verification, independent Pre-RESULT review, and evidence analysis. It does not
delegate result acceptance, a successor proposal, G2, or another decoder run.

The operator is strong and autonomous inside this boundary. Do not return for
routine implementation or analysis choices. There are only two returns:

1. complete all applicable steps and return the delta report; or
2. STOP on a concrete hard-gate failure, with failing ID, command, raw output,
   actions already taken, and the one decision required from the main thread.

Never describe partial progress as completion.

## 1. Frozen baseline and inherited contract

- Repository: `D:/Code/HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`
- Expected starting HEAD: `5bd82418`
- A2 prereg/OpenSpec commit: `03eff680`
- A2 implementation/test commit: `15f1de79`
- A2 independent-review commit: `5bd82418`
- Accepted code-readiness verdict:
  `D6_GRAPH_MOTHER_IMPLEMENTATION_REVIEW_R1C_A2.md` = PASS
- Accepted Pre-EXECUTE verdict:
  `D6_GRAPH_MOTHER_PRE_EXECUTE_REVIEW_R1C_A2.md` = PASS, while correctly
  withholding execution authorization until the user statement above
- Frozen runner:
  `scripts/v72p2d6_graph_mother_development.py`
- Fixed Model-F input:
  `workspace/v72p2d5_model_f_input/20260907_r1`
- New output root pattern:
  `workspace/d6_graph_mother_r1c_<uuid>/`
- Requested workers: `18`; effective workers may only decrease through the
  reviewed runtime RSS gate (`18/14/12/8`), and must be recorded
- Budgets: at most 2500 total setup + scientific decoder calls; 43200 seconds
  run wall; 120 seconds per call; aggregate RSS strictly below 2147483648 bytes
- No retry of any cell; timeout/crash consumes that cell
- Scientific arms, rows, seeds, priors, decoder settings, selection rules,
  terminal thresholds, and scalar-only six-file schema remain exactly frozen
  by R1/R1c/A1/A2.

The three roots below are permanently VOID and may only be checked by name and
existence. Do not open, hash, compare numerically, delete, move, resume, or reuse:

- `workspace/d6_graph_mother_r1_923a25897087495ab4605870e561f3cc`
- `workspace/d6_graph_mother_r1_e8ee45a4669c4738bf7e96d926ba7e5c`
- `workspace/d6_graph_mother_r1_f15cfa29baa2458e804c80a9f1045140`

Known unrelated worktree state, including the V35 report content change, CRLF
porcelain churn, perf-v38 material, and unrelated untracked paths, must be
preserved. Never clean, normalize, revert, stage, or include it.

## 2. Hard prohibitions

- No code, test, OpenSpec, prereg, frozen-contract, scientific-parameter, or
  decoder change after this packet begins.
- No retry, rerun, resume, recovery, second output root, parameter adjustment,
  manual cell replay, or evidence mixing after the first scientific call.
- No `--phase`, formal G1, G2, P0, VAL, real/raw data, n1024 formal execution,
  production qualification, or scientific promotion.
- No VOID-content read and no write/delete/move/rename/overwrite under any
  protected formal root.
- No broad stage, push, reset, stash, checkout, clean, rebase, revert, amend,
  renormalization, or EOL cleanup.
- No acceptance of the D6 result. Pre-RESULT PASS permits evidence
  solidification only; scientific route/acceptance remains a main-thread act.
- Decoder calls may occur only inside the single authorized runner invocation.
  Tests and reviewers must not invoke a real decoder.

## 3. E0 — fresh pre-run gate

Perform this gate read-only. STOP before any authorization edit if any item
fails:

1. branch and HEAD equal §1;
2. the three commit manifests are exactly 3 prereg/OpenSpec paths, 3
   implementation/test paths, and 2 review paths as reported;
3. the runner/core/test scoped files have zero content diff from `15f1de79`;
4. both A2 review documents have their stated PASS and no unresolved blocker;
5. `development_decoder_authorized: false`; all other execution authorization
   keys false; `scientific_promotion: false`; G2 absent;
6. fixed Model-F root is present; inspect only names/sizes/mtime at this gate;
7. all three VOID roots receive only existence checks;
8. no `workspace/d6_graph_mother_r1c_*` root exists;
9. task-scoped staged diff is empty and the only true unrelated worktree
   content diff is recorded but untouched;
10. Python, worker-count choices, internal 43200/120/2500/<2GiB gates, no-retry
    behavior, fail-closed fsync, and `verify_command` still match A2 review.

Do not rerun qualification pytest merely to repeat the accepted A2 review. A
source or contract drift is a STOP, not permission to repair.

Generate exactly one UUID after E0 passes. Resolve the target and prove it is a
new child of repository `workspace/` matching
`d6_graph_mother_r1c_<uuid>`. Never generate a replacement UUID later.

## 4. E1 — authorization record and enablement

Create:

`docs/research_cycles/V72P2D6-GF32-GRAPH-MOTHER/D6_GRAPH_MOTHER_AUTHORIZATION_R1C_A2.md`

Record the verbatim authorization, E0 evidence, commits/reviews, resolved fresh
root, exact command, budgets, attempt-consumption point, VOID list, no-retry
rule, and mandatory revocation/Pre-RESULT sequence.

Change exactly:

`development_decoder_authorized: false` → `true`

in the D6 `cycle_state.yaml`. Change no other state field. Stage exactly the
authorization record and cycle state; commit locally, no push, with:

```text
chore(v72p2d6): authorize one frozen R1c-A2 development run

Records the user's explicit authorization for one fresh-root R1c-A2 run.
Authorization is consumed by the first scientific decoder attempt; no retry,
resume, parameter change, formal G1, G2, VAL, real/raw, or VOID reuse.

Co-Authored-By: OpenAI Codex <codex@openai.com>
```

If this commit fails, restore the key to false and STOP without execution.

## 5. E2 — the single authorized invocation

Immediately recheck `development_decoder_authorized: true`, all other
authorization keys false, fresh target absent, G2 absent, scoped source diff
empty, and no staged changes.

Instantiate and record this exact command using the single UUID from E0:

```powershell
python scripts/v72p2d6_graph_mother_development.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d6_graph_mother_r1c_<uuid> --workers 18
```

Invoke that command exactly once from the repository root. Capture start/end
local and UTC timestamps, process exit code, outer wall seconds, stdout, and
stderr. Do not pipe or modify the child command. A surrounding stopwatch that
does not alter the child is allowed.

Authorization is consumed when the first scientific decoder attempt begins.
If the runner exits before any scientific decoder attempt, report whether its
own artifacts prove zero calls; do not guess and do not rerun. Once any
scientific call begins, every outcome consumes authorization.

## 6. E3 — immediate revocation

After the process terminates, before opening result payloads, change exactly:

`development_decoder_authorized: true` → `false`.

Verify all authorization keys false and G2 absent. Do not interpret results
while the key is true. If revocation fails, keep attempting only this same
false restoration and report a critical blocker; do nothing else.

Commit the state restoration locally by itself, no push:

```text
chore(v72p2d6): consume and revoke R1c-A2 development authorization

Restores development_decoder_authorized to false after the sole authorized
runner invocation. Result remains unreviewed and unaccepted.

Co-Authored-By: OpenAI Codex <codex@openai.com>
```

## 7. E4 — mechanical verification and operator evidence

Now inspect only the new root and run exactly one non-decoding verifier call:

```powershell
python scripts/v72p2d6_graph_mother_development.py --out-root workspace/d6_graph_mother_r1c_<uuid> --verify
```

This verifier is allowed once and is not a decoder retry. Capture its complete
output and exit. Never use `--model-f-root` or `--workers` with verify.

Expected ordinary evidence is exactly six top-level files:

- `manifest.json`
- `structure_records.csv`
- `selected_arms.json`
- `decoder_records.csv`
- `summary.json`
- `command_log.txt`

Create an uncommitted operator report:

`docs/research_cycles/V72P2D6-GF32-GRAPH-MOTHER/D6_GRAPH_MOTHER_OPERATOR_RETURN_R1C_A2.md`

Record command/times/exit/wall, invocation count, whether authorization was
consumed, effective workers and RSS decision, call accounting, timeouts,
crashes/nonfinite/disagreements, checkpoint/fsync status, six-file inventory,
verifier result, frozen terminal label and all scalar summaries. Recompute the
registered arithmetic directly from the six files. Report absent, partial, or
malformed evidence literally; do not repair it.

Protected roots receive post-run names/sizes/mtime comparison only. Model-F
content is not reread. VOID roots remain existence-only. G2 must remain absent.

## 8. E5 — independent Pre-RESULT review

Delegate a genuinely independent, read-only reviewer. The execution operator
must not self-review. The reviewer may read the frozen documents, scoped code,
and the new six-file development root, and may create only:

`docs/research_cycles/V72P2D6-GF32-GRAPH-MOTHER/D6_GRAPH_MOTHER_PRE_RESULT_REVIEW_R1C_A2.md`

The reviewer must independently check at least:

- immutable run identity, UUID uniqueness, no VOID/formal-root reuse;
- exact arms/seeds/rows/decoder/prior/sample-sharing contract;
- setup/scientific/effective call accounting and `<=2500`;
- 43200-second wall, 120-second cell watchdog, no retries, PID/respawn records;
- requested/effective workers and aggregate RSS, with unknown or `>=2GiB`
  receiving the frozen blocking outcome;
- crash/nonfinite/syndrome/exact separation and no oracle promotion;
- blind selection and terminal-priority recomputation;
- six-file schema, scalar-only payload, deterministic ordering, checkpoint and
  fsync evidence;
- operator wall versus stored wall and chunk-wall semantics;
- verifier result, protected-root equality, authorization false, G2 absent;
- claim boundary: CAL-only finite development evidence, not formal G1/G2,
  real-data performance, FER, leakage, key rate, qualification, or promotion.

Verdict must be one of `D6_R1C_A2_PRE_RESULT_REVIEW_PASS` or
`D6_R1C_A2_PRE_RESULT_REVIEW_FAIL`. FAIL blocks result solidification. It does
not authorize repair or rerun.

## 9. E6 — analysis and solidification after PASS only

If Pre-RESULT FAILs, STOP. Commit only the false authorization state if not
already committed; leave the new root immutable and uncommitted, return the
review blocker, and do not patch or rerun.

If Pre-RESULT PASSes, perform deep but bounded analysis of existing scalar
evidence. No new decoder calls. Produce:

`docs/research_cycles/V72P2D6-GF32-GRAPH-MOTHER/D6_GRAPH_MOTHER_RESULT_R1C_A2.md`

The analysis must separate:

1. structural ranking and selected arms;
2. canary, confirmation, and scaling evidence;
3. APP exact, syndrome, oracle-only diagnostics, crash/nonfinite, iterations,
   wall, and RSS per arm/n/layer/prefix;
4. paired-seed contrasts against B0/B1 and among T/M arms;
5. registered terminal classification with every predicate shown;
6. what was learned about graph/mother topology;
7. limitations and strongest supportable claim;
8. one recommended next mainline decision, without implementing or executing
   it.

Do not call the result accepted. Do not alter authorization, promotion, formal
G1/G2, or D5 accepted-result fields. Update D6 cycle state only with factual
development-run bookkeeping and set `next_gate` to an independent main-thread
result-acceptance/route-decision gate; never mark acceptance yourself.

Append concise durable deltas to `docs/decision-log.md` and
`AGENT_PROJECT_MEMORY.md`. Preserve append-only semantics.

Commit after PASS in one scoped result commit containing only:

- the immutable fresh UUID development root's six files;
- `D6_GRAPH_MOTHER_OPERATOR_RETURN_R1C_A2.md`;
- `D6_GRAPH_MOTHER_PRE_RESULT_REVIEW_R1C_A2.md`;
- `D6_GRAPH_MOTHER_RESULT_R1C_A2.md`;
- D6 `cycle_state.yaml` factual bookkeeping;
- append-only decision log and project memory.

No code/OpenSpec/test file belongs in this commit. No push.

## 10. Final report

Return deltas only:

1. E0 gate and resolved UUID root;
2. authorization and revocation commit SHAs;
3. exact runner invocation, invocation/scientific-call counts, timestamps,
   exit, outer wall, stdout/stderr;
4. requested/effective workers, call/wall/watchdog/RSS accounting;
5. six-file inventory and verify output;
6. frozen terminal and decisive scalar evidence, with no overclaim;
7. independent Pre-RESULT verdict and findings;
8. result commit SHA if PASS, or exact uncommitted state if FAIL;
9. protected-root equality, three VOID roots existence-only, G2 absence, all
   authorizations false, final gate, and no push;
10. true/false list for retry/rerun/resume, parameter/code change, `--phase`,
    formal G1/G2, VAL/real/raw, VOID read/reuse, protected-root mutation, and
    unauthorized decoder calls.

End exactly:

`D6 R1c-A2 已完成唯一授权的 development-only 执行；授权已消耗并恢复为 false；结果已完成独立 Pre-RESULT 复审与有界分析，但尚未由主线程接受；正式 G1 未重跑，G2 未授权、未执行。`
