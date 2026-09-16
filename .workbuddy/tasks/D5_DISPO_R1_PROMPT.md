# Paste-ready prompt — D5-DISPO-R1 (weak session)

Copy everything between the two `=====` lines into a fresh session opened in
`D:/Code/HD-QKD_Polar_Comparison`.

=====

你是这个仓库的执行 session。本次任务是**纯文档 + 本地 git 提交**，零科研执行。

任务包全文在：
`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_DISPO_R1_TASK_PACKET.md`

第一步：完整读完这个文件，一行都不要跳过。然后严格按里面的 STEP 1 → STEP 7
顺序执行，不要重排、不要合并、不要跳步。

必须遵守的框架：

1. 任务包第 0 节有 11 条硬禁令。任何一条被触发，立刻停止，不要继续，不要
   自行修复，直接把失败的步骤号和原始输出报给我。
2. 每一步我都给了期望的字面输出（文件大小、mtime、`165 passed`、
   `COMPILE_OK` 等）。实际输出和期望对不上，就是 STOP 条件，不是让你调整
   期望值，也不是让你重跑到通过。
3. 你只能新建 **1 个**文件：
   `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_UNAUTHORIZED_DISPOSITION_R1.md`。
   另外只允许对 `docs/decision-log.md` 和 `AGENT_PROJECT_MEMORY.md` 做**追加**
   （append），模板在任务包 STEP 2/3/4 里给全了，照抄并填入实测数值即可。
   除此之外不许新建、不许改任何文件。
4. 一个 `.py` 都不许改。本次任务没有任何代码改动。
5. 不许运行 decoder，不许运行
   `scripts/v72p2d5_gf32_rate_mother.py --phase p0-cost|g1|g2`，不许运行
   `scripts/v72p2d5_prepare_model_f_input.py`（prepare 和 verify 都不许），
   不许 `pd.read_parquet`，不许读 CAL/VAL/原始数据。
6. `workspace/v72p2d5_*` 下的任何文件都不许删除、移动、改名、复制、规范化、
   算 hash、以写模式打开。只允许 `stat` 和 `json.load` 只读。
7. `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/cycle_state.yaml` 里所有
   `*_execution_authorized` 保持 `false`，`next_gate` 保持
   `P0_PACKET_REVIEW`，一个字都不许改。
8. git 只允许按任务包 STEP 6 的白名单逐条 `git add` + 3 次 `git commit`。
   **严禁** `git add -A`、`git add .`、`git commit -a`、`git push`、
   `git reset`、`git stash`、`git checkout --`、`git clean`、`git rebase`、
   `git commit --amend`。commit message 照抄任务包原文，包含
   `Co-Authored-By` 行。
9. 不许写 `RESULT_SUMMARY.md`、`OPERATOR_RETURN.md`、任何 `run_01`。
10. 不许给出任何科研结论：不许说 FER、泄漏、密钥率、不许说「G1 失败」、
    不许说「这个方法不行」、不许说 P0 可以授权。那个 G1 目录里的
    `decoder_calls=440` 是隔离缺陷的产物，不是实验结果。

背景（已冻结，不要重新推导、不要质疑）：
- 独立 Pre-RESULT 复审 `MODEL_F_INPUT_PRE_RESULT_REVIEW_R1.md` 结论是
  `PRE_RESULT_REVIEW_FAIL`，唯一 blocker 是 PR16：
  `workspace/v72p2d5_g1/20260906_r1/` 在 `g1_execution_authorized=false` 的
  情况下存在。
- 成因是测试隔离缺陷，记录在
  `UNAUTHORIZED_G1_TEST_EXECUTION_INCIDENT_20260907.md`；修复已完成并有证据
  `TEST_ISOLATION_REWORK_EVIDENCE_R1.md`（165 collected / 165 passed）。
- 用户 2026-09-07 已拍板：该 G1 目录**原地保留、记录作废**
  （`VOID_RETAINED_IN_PLACE`），不删不移；本次提交**只提交到本地，不 push**。
- 这两条是决定，不是建议。不要再讨论删除或移动方案。

完成后按任务包 STEP 7 汇报：贴出 STEP 1 与 G03 的两份 stat 表并说明是否完全
一致、`COMPILE_OK`、pytest 原文行、3 个 commit SHA、`git status -sb`，然后逐项
给出 true/false 清单，并明确写出这一句：

「PR16 仅以记录方式处置；Model-F Pre-RESULT 复审尚未进行；P0 未授权。」

不要提出下一步实验建议。不要自行推进到 P0。

=====
