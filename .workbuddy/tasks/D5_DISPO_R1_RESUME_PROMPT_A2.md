# Paste-ready prompt — D5-DISPO-R1 resume after amendment A2

Copy everything between the two `=====` lines into the executing session.

=====

你在 G06 停止**又是对的**。G06 的 cutoff 是任务包作者写死错了，不是你的问题。
连续两次 STOP 说明围栏在正常工作，不是你的执行有偏差。裁决已下：
**放行，跑完 G06' 后直接进 STEP 6。**

修订件 A2 在：
`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_DISPO_R1_AMENDMENT_A2.md`
（A1 在同目录 `D5_DISPO_R1_AMENDMENT_A1.md`，原任务包
`D5_DISPO_R1_TASK_PACKET.md`）

先完整读完 A2，再按它执行。任务包与 A1 除被 A2 明确取代的部分外全部继续有效，
包括第 0 节全部 11 条硬禁令。

裁决要点（已冻结，不要再质疑、不要再调查）：

1. 你点名的 `comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py`
   mtime `2026-09-07T03:48:38`，比任务包文件自身的 mtime
   `2026-09-07T04:04:24` **早 16 分钟**。它属于任务包之前的 test-isolation
   返工（`TEST_ISOLATION_REWORK_EVIDENCE_R1.md`），且 03:58 的 `git status`
   快照已把它列为 `M`。你没有著任何 `.py`。原 G06 的 `03:00` cutoff 作废。
2. **G03 由作者裁定 PASS**：作者已用你 STEP 1 报告里的字面值逐条比对，g1 四文件
   （267/146/2593/126 及对应 mtime_ns）、model_f_input 两文件（208467/752）、
   两个 G0 根全部相等，p0_cost/g2 仍 absent。不要重跑 G03，不要再去找 STEP 1
   字面值。
3. **不要重做** STEP 1-4，也不要重跑 G01、G02、G04、G05'。它们已通过并被接受。

执行顺序：

- 只跑 A2.3 的 **G06'**（cutoff 自锚定到任务包文件自身 mtime）。期望
  `NEWER_THAN_PACKET []` + `G06_OK`。若 shell 撑不住多行 `python -c`，用语义
  相同的单行形式即可，在汇报里说明一句。
- `G06_OK` 后**直接进 STEP 6**：三段 `git add` 白名单与三条 commit message 原样
  不变；每次 `git add` 之后、`git commit` 之前必须插入 A1 的 **G07**：
  `git diff --cached --name-only`，逐条看清；出现任何不在该次白名单内的路径
  （尤其是那 15 个包外 `.py`）就立刻 STOP，不要提交，不要自己 unstage 修复，
  直接报给我。

仍然禁止：`git push`、`git add -A`、`git add .`、`git commit -a`、`git reset`、
`git stash`、`git checkout --`、`git clean`、`git rebase`、`git commit --amend`。
仍然禁止：运行 decoder、运行 `--phase p0-cost|g1|g2`、运行
`v72p2d5_prepare_model_f_input.py`、读 CAL/VAL/parquet、改任何 `.py`、改任何
`*_execution_authorized`、写 `RESULT_SUMMARY`/`OPERATOR_RETURN`/`run_01`。

完成后按原任务包 STEP 7 汇报，并补一句：G05 由 A1 取代、G06 由 A2 取代、
G03 由作者裁定 PASS，G05'/G06'/G07 均通过。最后仍要原样写出：

「PR16 仅以记录方式处置；Model-F Pre-RESULT 复审尚未进行；P0 未授权。」

不要提出下一步实验建议。不要自行推进到 P0。

=====
