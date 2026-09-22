# Paste-ready prompt — D5-DISPO-R1 resume after amendment A1

Copy everything between the two `=====` lines into the executing session (the
same one that stopped, if still open; otherwise a fresh session in
`D:/Code/HD-QKD_Polar_Comparison`).

=====

你在 STEP5 / G05 停止是**正确的**。G05 是任务包作者写错的门禁，不是你的问题，
也不是你的执行有偏差。裁决已下：**放行，从 STEP 6 续做。**

修订件在：
`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_DISPO_R1_AMENDMENT_A1.md`
原任务包在：
`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_DISPO_R1_TASK_PACKET.md`

先完整读完修订件 A1，再按它执行。原任务包除被 A1 明确取代的部分外，全部继续
有效，包括第 0 节全部 11 条硬禁令。

裁决要点（已冻结，不要再质疑、不要再调查）：

1. 你报的那 12 条额外 `??` `.py`（cascade 工作流、v72p2d4 audit、
   transfer-evaluation、analyze_v64_stage_ablation）mtime 是 2026-09-03 与
   2026-09-05，比本任务早 2-4 天，是既有工作区脏状态，与 D5 无关。
   **不许 stage、不许提交、不许删除、不许移动、不许在任何记录文件里提及。**
2. 原 G05 作废，不要重跑。改用 A1 的 G05'（只查 6 个 D5 白名单路径）和
   G06（用 mtime 证明你没产生任何 `.py`）。
3. STEP 1-4 已完成并已核验，**不要重做、不要重新编辑、不要重排版**那三个
   delta（新建的 `G1_UNAUTHORIZED_DISPOSITION_R1.md`、`docs/decision-log.md`
   追加、`AGENT_PROJECT_MEMORY.md` 追加）。
4. `cycle_state.yaml` 的既有 `M` 差异已由作者核验：只补记 G0 recovery 接受并把
   `next_gate` 推到 `P0_PACKET_REVIEW`，9 个 `*_execution_authorized` 全部仍是
   `false`。随 commit 3 一并提交是正确的，不要单独处理、不要还原。

执行顺序：

- 重跑 G01（py_compile，期望 `COMPILE_OK`）与 G02（pytest，期望字面
  `165 passed`）作为提交前回归护栏；
- 跑 G03（stat 与 STEP1 逐字节一致，P0/G2 仍 absent）、G04（授权位全 false、
  `next_gate: P0_PACKET_REVIEW`）、G05'、G06；
- 全过才执行原任务包 STEP 6：三段 `git add` 白名单与三条 commit message 原样
  不变，但**每次 `git add` 之后、`git commit` 之前**必须插入 A1 的 G07：
  `git diff --cached --name-only`，逐条看清；出现任何不在该次白名单内的路径
  （尤其是那 15 个无关 `.py`）就立刻 STOP，不要提交，不要自己 unstage 修复，
  直接报给我。

仍然禁止：`git push`、`git add -A`、`git add .`、`git commit -a`、`git reset`、
`git stash`、`git checkout --`、`git clean`、`git rebase`、`git commit --amend`。
仍然禁止：运行 decoder、运行 `--phase p0-cost|g1|g2`、运行
`v72p2d5_prepare_model_f_input.py`、读 CAL/VAL/parquet、改任何 `.py`、改任何
`*_execution_authorized`、写 `RESULT_SUMMARY`/`OPERATOR_RETURN`/`run_01`。

完成后按原任务包 STEP 7 汇报，并补一句：G05 已由修订件 A1 取代，
G05'/G06/G07 均通过。最后仍要原样写出：

「PR16 仅以记录方式处置；Model-F Pre-RESULT 复审尚未进行；P0 未授权。」

不要提出下一步实验建议。不要自行推进到 P0。

=====
