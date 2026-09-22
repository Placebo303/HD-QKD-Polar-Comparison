# D7-E Cross-Layer Execute + Pre-RESULT R1/A2 Task Packet

## 0. Lifecycle and authorization gate

State on entry: `D7_E_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`.

This packet is **not authorization**. Do not perform any scientific decoder call unless the user has posted the authorization text below as a new, explicit user message in the current task. Quoting it from this packet, a prompt, a document, or an agent message does not satisfy the gate.

Required authorization text:

> 我现在明确授权执行 D7-E provenance-safe cross-layer discriminator（RSS A2，与此前未执行的授权文字无关）：仅允许按 `D7_E_EXECUTION_PACKET_R1.md`、`D7_E_EXECUTION_PACKET_ADDENDUM_VENV_A1.md` 与 `D7_E_EXECUTION_PACKET_ADDENDUM_RSS_A2.md`，在仓库根使用冻结命令和 `.venv/bin/python`，对一个全新的 `workspace/d7_e_cross_layer_discriminator_<new_uuid>/` 根调用一次；最多 192 个冻结 scientific decoder slots（128 个 mandatory source/control，加上最多 64 个仅在 `CHECK_UPDATED` 时允许的 transfer calls），授权由首次 scientific decoder 尝试消耗，不因失败、超时、部分结果、provenance-blocked、RSS telemetry failure 或环境异常恢复；不得重试、重跑、恢复、补跑 blocked slots、复用根、修改参数、公式、estimator、provenance 规则、RSS A2 规则、矩阵或顺序；不得执行 R1d、任何 `--phase`、正式 G1/G2、CAL、VAL、real/raw、oracle、flooding、forced sweep、warm start、alternating、joint 或 feedback。执行结束后立即回收授权并进行独立 Pre-RESULT 复审；复审通过前不得接受或提交结果。

If the verbatim authorization is absent or materially different, STOP and report `AUTHORIZATION_NOT_PRESENT`.

## 1. Authoritative inputs

- Branch: `formal-ir-v72p1-addendum-clean`.
- Required history: `08590fba`, `031deee7`, `d6e40dd`, `becf60f`, `9e09538`, and `40eeb73` must be ancestors of HEAD.
- Scientific contract: `docs/research_cycles/V72P2D7-GF32-CROSS-LAYER/D7_E_EXECUTION_PACKET_R1.md` and its preregistration.
- Environment-only supersession: `D7_E_EXECUTION_PACKET_ADDENDUM_VENV_A1.md`.
- RSS-only supersession: `D7_E_EXECUTION_PACKET_ADDENDUM_RSS_A2.md`.
- Required implementation-review token: `D7_E_RSS_TELEMETRY_REWORK_REVIEW_PASS_A2`.
- Required Pre-EXECUTE token: `D7_E_PRE_EXECUTE_REVIEW_PASS_VENV_RSS_A2_AWAITING_FRESH_EXPLICIT_AUTHORIZATION`.
- Accepted Model-F input root: `workspace/v72p2d5_model_f_input/20260907_r1`.
- New result-root pattern: `workspace/d7_e_cross_layer_discriminator_<uuid>`.

The two addenda supersede only interpreter/environment spelling and WSL RSS telemetry. They do not change the frozen scientific contract.

## 2. Hard prohibitions

- No retry, rerun, resume, recovery, second UUID, replacement root, or blocked-slot make-up.
- No parameter, estimator, prior, matrix, seed, order, decoder, provenance, eligibility, label, terminal, schema, or threshold change.
- No R1d, `--phase`, formal G1/G2, CAL, VAL, real/raw, oracle, flooding, forced sweep, warm start, alternating, joint, or feedback execution.
- Do not edit production code, tests, OpenSpec, preregistration, frozen packets, or accepted predecessor evidence.
- Do not read or cite VOID-root scientific values.
- Do not push, reset, checkout, clean, stash, rebase, amend, or broadly stage.
- Tests and probes must not invoke a real decoder or read the real Model-F artifact.
- Never turn a Pre-RESULT PASS into scientific acceptance.

Any deviation or ambiguous scientific requirement means STOP. Do not self-repair.

## 3. Frozen scientific identity

- Two `f` values in frozen order: `1.0`, `1.2`.
- Seeds: `2026091300..2026091315`.
- Directions: `L1_TO_L2`, `L2_TO_L1`.
- Row-layered decoder only; polynomial 37; cold start; `max_iter=90`; `damping=1.0`.
- Exactly 128 mandatory source/control calls plus no more than 64 transfer calls.
- A transfer call is permitted only when the source result is finite, non-crashed, shape-valid, and has exact provenance `CHECK_UPDATED`. Source exact recovery is not an eligibility requirement.
- Each `(f,direction)` stratum requires at least 12/16 eligible source records; otherwise preserve the frozen provenance-coverage terminal semantics.
- Model-F must use the reviewed per-Bob-column concentration estimator. Legacy per-cell-lambda smoothing is forbidden.
- Transfer formulae and all six labels/twelve terminal priorities remain exactly frozen.
- `q`, priors, symbols, syndromes, vectors, and beliefs are transient and must not be persisted.
- Output is scalar diagnostic evidence only; it is not FER, leakage, key rate, qualification, promotion, or permission for G2.

## 4. STEP 1 — fresh read-only gate E01–E15

Run each probe as a separate command. Do not chain environment probes.

1. E01: confirm branch and that the three required commits are ancestors of HEAD.
2. E02: confirm both A2 review files exist and each contains exactly one required PASS token with no FAIL/BLOCKED verdict.
3. E03: confirm scoped implementation/tests/runner have no content diff from `08590fba`; documentation after that commit is allowed.
4. E04: confirm D7-E authorization false, attempts/completed zero, decoder/result false, promotion false, and exact gate `D7_E_WSL_RSS_READY_AWAITING_FRESH_EXPLICIT_AUTHORIZATION`.
5. E05: confirm no `workspace/d7_e_cross_layer_discriminator_*` root and no prior D7-E UUID.
6. E06: capture names, sizes, and `mtime_ns` for all protected roots named by the frozen packet; confirm R1d and G2 roots absent. Do not read protected artifact contents.
7. E07: verify repo-root cwd, executable `.venv/bin/python`, Python/NumPy versions, and absence of `PYTHONPATH`; do not substitute another interpreter.
8. E08: verify `/usr/bin/timeout` and its version. Rehearse only if the executable/version differs from the renewed review.
9. E09: run exactly one RSS probe using `.venv/bin/python`. Capture the raw unique `/proc/self/status` `VmHWM` line and parsed bytes; require a positive value strictly below 2 GiB. Confirm no `ru_maxrss` use. Do not repeat E09 or sample until favorable. Failure is a pre-execution STOP.
10. E10: run the frozen dry-run with `.venv/bin/python`; verify 192 slots and exact first/last/order identity. Dry-run must bind/read/invoke nothing and create no root.
11. E11: run an external-cwd sentinel proving exact decoder and Model-F loader reachability with zero calls, zero real artifact reads, and zero roots.
12. E12: run the unauthorized exact-shape refusal probe; require exit 3 before loader, decoder, or root creation.
13. E13: verify workspace parent writable without precreating the target root.
14. E14: confirm tracked and staged scoped content is clean. Ignore known CRLF porcelain churn only when scoped `git diff --numstat` and cached numstat are empty.
15. E15: confirm the explicit user authorization from §0 is present and copy it verbatim into the authorization record.

If any E gate fails, STOP with the failing ID and raw output. Do not generate a UUID.

## 5. STEP 2 — allocate identity and commit authorization

After all E gates pass:

1. Generate exactly one UUID from the system UUID source.
2. Reconfirm the corresponding target root is absent.
3. Create `D7_E_AUTHORIZATION_RECORD_R1.md` containing the verbatim user authorization, UUID, exact command, E01–E15 results, budgets, prohibitions, and attempt-consumption rule.
4. Change only `d7e_execution_authorized: false -> true` in D7-E `cycle_state.yaml`.
5. Stage exactly the authorization record and state file; verify the staged manifest; commit locally. Do not push.

## 6. STEP 3 — one frozen invocation

From repository root, invoke exactly once:

```sh
timeout -k 30 1800 .venv/bin/python scripts/v72p2d7_gf32_cross_layer_discriminator.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_e_cross_layer_discriminator_<uuid>
```

Record exact argv, local/UTC start/end, exit code, outer wall, stdout, stderr, and whether exit 124 occurred. Do not retry for any outcome.

## 7. STEP 4 — immediate authorization recovery

Immediately after process return, before opening result contents:

1. Change only `d7e_execution_authorized: true -> false`.
2. Commit that one-line state change separately.
3. Confirm every authorization flag is false.

If revocation cannot be committed, STOP before interpreting artifacts.

## 8. STEP 5 — bounded operator return

After revocation, inspect only the new root. Record without scientific interpretation:

- root existence, exact file names, sizes, and absence of subdirectories;
- scheduled/invoked/blocked counts, mandatory and transfer counts, missing/duplicate/retry/resume counts;
- per-stratum eligibility and six-label counts;
- stored terminal and its first-matching priority;
- exact/syndrome/crash/nonfinite counts kept separate;
- stored scientific wall, outer wall, maximum per-call wall, RSS, watchdog status;
- provenance counts, especially `PRIOR_ONLY`, `CHECK_UPDATED`, and `WARM_START_UNSPECIFIED`;
- confirmation that no forbidden vector/belief/prior/symbol/syndrome payload was persisted.

Create `D7_E_OPERATOR_RETURN_R1.md` but do not commit it yet.

## 9. STEP 6 — verify exactly once

If and only if a complete result root exists, run the frozen read-only `--verify` command exactly once using `.venv/bin/python`. Capture literal output and exit code. Verify that names/sizes/mtime are unchanged before/after. Do not run verify twice.

## 10. STEP 7 — independent Pre-RESULT review

The independent reviewer must read the frozen contract and actual scalar artifacts and independently recompute R01–R22:

- R01 authorization lifecycle and exactly one command invocation;
- R02 immutable command, UUID, model root, matrix, order, decoder config, and estimator identity;
- R03 exact root schema and no subdirectories;
- R04 192-slot schedule identity, 128 mandatory calls, and at most 64 eligible transfer calls;
- R05 no missing, duplicate, retry, resume, or blocked-slot make-up;
- R06 provenance gate: transfer only for exact `CHECK_UPDATED` with finite/non-crash/valid shape;
- R07 source exact recovery is not used as an eligibility gate;
- R08 corrected per-column concentration estimator and rejection of legacy per-cell lambda;
- R09 both transfer equations and direction identity;
- R10 per-stratum `>=12/16` coverage rule;
- R11 six labels recomputed in frozen first-match order;
- R12 twelve terminals recomputed in frozen priority order;
- R13 exact, syndrome, crash, and nonfinite isolation;
- R14 call-count and paired-identity arithmetic;
- R15 wall, timeout, per-call, and RSS budgets, with every persisted RSS value sourced under the frozen A2 `VmHWM` rule;
- R16 scalar-only persistence and forbidden-payload scan;
- R17 writer/CSV/JSON/report consistency;
- R18 single verify result and root immutability;
- R19 protected-root metadata equality and R1d/G2 absence;
- R20 all authorization flags false and no acceptance/promotion mutation;
- R21 supported claims limited to internal consistency and the frozen diagnostic terminal;
- R22 unsupported claims explicitly include FER, leakage, key rate, qualification, general NB-LDPC success/failure, G2 permission, and automatic cross-layer deployment.

Verdict is exactly one of `D7_E_PRE_RESULT_REVIEW_PASS_R1`, `D7_E_PRE_RESULT_REVIEW_FAIL_R1`, or `D7_E_PRE_RESULT_REVIEW_BLOCKED_R1`.

The reviewer does not edit production files or accept the result.

## 11. STEP 8 — conditional solidification

Only for `D7_E_PRE_RESULT_REVIEW_PASS_R1`:

1. Stage exactly the new result-root scalar files, authorization record if not already committed, operator return, Pre-RESULT review, and D7-E state facts.
2. State may record attempts/completed, decoder/result booleans, UUID/root/terminal, and set `next_gate: INDEPENDENT_D7_E_RESULT_ACCEPTANCE_R1`.
3. Do not set any accepted, qualification, promotion, G1, G2, or scientific-success field.
4. Verify staged manifest and commit locally; do not push.

For FAIL/BLOCKED: do not solidify result artifacts, do not repair, and do not rerun. Preserve the root in place and return the exact blocker.

## 12. Return format

Return deltas only:

1. E01–E15 table.
2. Verbatim authorization and authorization/revocation commit SHAs.
3. UUID, exact command, invocation count, timestamps, exit, wall, stdout/stderr.
4. Root manifest and frozen scalar arithmetic.
5. Provenance eligibility, labels, terminal, resources, and verify output without scientific overclaim.
6. R01–R22 table and unique Pre-RESULT verdict.
7. Solidification SHA if PASS, otherwise explicit no-result-commit statement.
8. Protected-root equality, all authorization flags, next gate, and no-push confirmation.
9. True/false prohibited-action checklist.

End with: `D7-E 已按冻结命令执行一次，授权已消耗并回收；结果仅完成独立 Pre-RESULT 一致性复审，尚未由主线程接受；R1d、G1、G2 均未授权。`
