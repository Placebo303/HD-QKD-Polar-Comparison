# D6 graph/mother — one-shot R1c-A2 development authorization record

Status: `AUTHORIZED_ONCE_R1C_A2_DEVELOPMENT_ONLY`.

## 1. Verbatim user authorization

> 我现在明确授权执行 D6 R1c-A2 §8：仅允许使用冻结的 R1c-A2 实现，对一个全新的 `workspace/d6_graph_mother_r1c_<uuid>/` 根进行一次 development-only 执行；使用固定 Model-F 输入根和 `--workers 18` 请求值，实际并发只能按已评审的 RSS 规则向下调整；总计不超过 2500 次 decoder 调用、12 小时 wall、单次调用 120 秒、总 RSS 小于 2 GiB。授权由首次科学 decoder 尝试消耗；不得重试、恢复、复用任何 VOID 根、修改参数或代码，不得执行任何 `--phase`、正式 G1、G2、VAL、real/raw。运行结束后必须停止并进行独立 Pre-RESULT 复审，复审通过前不得接受或提交结果。

## 2. E0 gate evidence (read-only, all pass)

- Branch `formal-ir-v72p1-addendum-clean`, HEAD `5bd82418` (§1 match).
- Commit 1 `03eff680`: exactly 3 prereg/OpenSpec paths.
- Commit 2 `15f1de79`: exactly 3 implementation/test paths
  (`scripts/v72p2d6_graph_mother_development.py`,
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d6_gf32_graph_mother.py`,
  `comparison_bench/tests/test_v72p2d6_gf32_graph_mother.py`).
- Commit 3 `5bd82418`: exactly 2 review paths.
- Scoped diff `15f1de79..HEAD` on the 3 implementation/test paths: empty.
  Scoped worktree diff: empty. Staged diff: empty.
- Implementation review `D6_GRAPH_MOTHER_IMPLEMENTATION_REVIEW_R1C_A2.md`: PASS,
  no unresolved blocker (non-blocking suggestions only).
- Pre-EXECUTE review `D6_GRAPH_MOTHER_PRE_EXECUTE_REVIEW_R1C_A2.md`:
  pass-with-comments, authorization correctly withheld pending this record.
- `cycle_state.yaml`: `development_decoder_authorized: false`, all other
  execution authorization keys false, `scientific_promotion: false`,
  `g2_execution_authorized: false`, `evidence_root: null`, `terminal: null`.
  No D6 G2 artifact (only unrelated V72P2D5 `v72p2d5_p0g1g2_*` roots exist).
- Model-F root `workspace/v72p2d5_model_f_input/20260907_r1` present
  (names/sizes/mtime only): `model_f_input_summary.json` (752 B),
  `model_f_input.npz` (208467 B), both 2026-09-07 02:07:07.
- Three VOID roots existence-checked only (all present, never opened):
  `workspace/d6_graph_mother_r1_923a25897087495ab4605870e561f3cc`,
  `workspace/d6_graph_mother_r1_e8ee45a4669c4738bf7e96d926ba7e5c`,
  `workspace/d6_graph_mother_r1_f15cfa29baa2458e804c80a9f1045140`.
- No `workspace/d6_graph_mother_r1c_*` root existed at gate time.
- Python 3.12.12; runner gates match A2 review: `CALL_BUDGET = 2500`,
  `WALL_BUDGET = 12*3600`, 120 s watchdog poll, RSS fail-closed
  `18/14/12/8(+1)`, `--workers` choices `(18,14,12,8,1)`, `verify_command`
  with 15 checks, no-retry semantics.

## 3. Resolved fresh root (single UUID, no replacement)

- UUID: `dd8c4defe67742a8b2bc1b634c116d6b`
- Out-root: `workspace/d6_graph_mother_r1c_dd8c4defe67742a8b2bc1b634c116d6b`
- Verified absent at gate; new child of repository `workspace/`.

## 4. Exact authorized command (invoke once, from repository root)

```powershell
python scripts/v72p2d6_graph_mother_development.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d6_graph_mother_r1c_dd8c4defe67742a8b2bc1b634c116d6b --workers 18
```

## 5. Budgets and consumption

- At most 2500 total setup + scientific decoder calls; 43200 s run wall;
  120 s per-call watchdog; aggregate RSS strictly below 2147483648 bytes.
- Requested workers 18; effective workers may only decrease via the reviewed
  runtime RSS gate (18/14/12/8) and must be recorded.
- Authorization is consumed when the first scientific decoder attempt begins.
  Every outcome after that point consumes authorization: no retry, rerun,
  resume, recovery, second root, parameter/code change, or manual cell replay.
- If the runner exits before any scientific decoder attempt, report whether
  its own artifacts prove zero calls; do not guess and do not rerun.

## 6. VOID and prohibition list

- VOID (existence-only, zero reuse): the three roots in §2.
- Forbidden: `--phase`, formal G1, G2, P0, VAL, real/raw data, n1024 formal
  execution, production qualification, scientific promotion/acceptance;
  VOID-content read; writes under any protected formal root; code/test/
  OpenSpec/prereg/parameter/decoder changes; broad stage, push, reset, stash,
  checkout, clean, rebase, revert, amend, renormalization, EOL cleanup.
- V35 report content change, CRLF porcelain churn, perf-v38 material, and
  unrelated untracked paths are preserved as-is.
- Only task-owned processes may be terminated.

## 7. Mandatory post-run sequence

1. E3: flip `development_decoder_authorized` true → false before opening any
   result payload; commit revocation alone.
2. E4: exactly one `--out-root ... --verify` call (no `--model-f-root`,
   no `--workers`); write uncommitted `D6_GRAPH_MOTHER_OPERATOR_RETURN_R1C_A2.md`
   with recomputation from the six files.
3. E5: genuinely independent read-only Pre-RESULT review producing
   `D6_GRAPH_MOTHER_PRE_RESULT_REVIEW_R1C_A2.md` with PASS/FAIL verdict.
   FAIL blocks solidification without repair or rerun.
4. E6: only on PASS, bounded scalar analysis into
   `D6_GRAPH_MOTHER_RESULT_R1C_A2.md`; no new decoder calls; no self-acceptance.
