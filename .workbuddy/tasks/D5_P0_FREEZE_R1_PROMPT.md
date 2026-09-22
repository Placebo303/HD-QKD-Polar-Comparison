# Paste-ready prompt — D5-P0-FREEZE-R1 (weak session)

Copy everything between the two `=====` lines into a fresh session opened in
`D:/Code/HD-QKD_Polar_Comparison`.

=====

你是这个仓库的执行 session。本次任务是**写一份文档 + 一次本地 git 提交**，
零科研执行、零授权。

任务包全文在：
`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_P0_FREEZE_R1_TASK_PACKET.md`

第一步：完整读完这个文件，一行都不要跳过。然后严格按 STEP 1 → STEP 5 顺序执行，
不要重排、不要合并、不要跳步。

**本任务的性质：你是在誊写一份冻结文档。**你需要的每一个数值，任务包 §3 都已经
给全了。**不要自己推导、不要重算、不要"改进"任何数值，也不要跑去源码里找。**
§3 里没有的东西，就 STOP 并报告。

必须遵守的框架：

1. 任务包第 0 节有 13 条硬禁令。任何一条被触发，立刻停止，不要继续，不要自行
   修复，直接把失败的步骤号和原始输出报给我。
2. 你只能新建 **1 个**文件：
   `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/P0_EXECUTION_PACKET.md`。
   **本任务不修改任何既有文件**——`cycle_state.yaml` 一个字都不许动，
   decision-log 与 AGENT_PROJECT_MEMORY 这次都不写。G03 会检查这一点：出现任何
   ` M ` 就是违规。
3. **不许运行任何 `--phase`**。`scripts/v72p2d5_gf32_rate_mother.py` 只允许
   `--help`，别的一律不许。不许运行 decoder，不许运行
   `v72p2d5_prepare_model_f_input.py`，不许 `pandas.read_parquet`，不许读
   CAL/VAL/原始数据。本任务也**不需要跑 pytest**，不要跑。
4. **`workspace/v72p2d5_p0_cost/20260906_r1/` 必须在你做完之后仍然不存在。**
   `workspace/` 下一律不许新建/删/移/改名/复制/写入。
5. **`p0_cost_execution_authorized` 保持 `false`，`next_gate` 保持
   `P0_PACKET_REVIEW`。本任务不授权 P0，也不执行 P0。**
6. 一个 `.py` 都不许改。
7. **§4 的五个 OPEN QUESTIONS（OQ-P0-1 .. OQ-P0-5）原样誊写成"未解决的问题"，
   不许回答、不许挑一个答案、不许标记为已解决。**那是评审的活，不是你的活。
   同理，§3 里的 `R-R1` / `R-R2` 两条残余风险要**逐字**抄进文档。
8. git 只允许 STEP 4 的一次白名单 `git add` + 一次 `git commit`。**严禁**
   `git add -A`、`git add .`、`git commit -a`、`git push`、`git reset`、
   `git stash`、`git checkout --`、`git clean`、`git rebase`、
   `git commit --amend`。commit message 照抄任务包原文，含 `Co-Authored-By` 行。
   G05 期望 `STAGED_COUNT 1` 且 `OUT_OF_SCOPE []`；不是 1 就 STOP，不提交、
   **不要 unstage、不要 clean**。
9. 不许写 `RESULT_SUMMARY.md`、`OPERATOR_RETURN.md`、任何 `run_01`。
10. 不许给出任何科研结论，也**不许说 P0 已就绪、已批准或安全**。

背景（已冻结，不要质疑、不要改写）：
- `cycle_state.yaml` 当前 `next_gate: P0_PACKET_REVIEW`。P0 被授权之前，必须先把
  这次要跑的东西白纸黑字冻结下来，交独立评审比对源码与既定计划。
- 你写的就是那份冻结文档。你**不是**评审，也**不是**授权者。后面还有两步与你无关：
  独立 Pre-EXECUTE 评审，以及之后单独的显式授权。
- P0 是成本预检，不是实验。它只产出耗时、迭代数、RSS 和对 G1/G2 的成本外推，
  不建立任何正确性、码率点性能、FER、泄漏或密钥率结论。文档里要照抄这条边界。
- 下列输出不是失败：`LF will be replaced by CRLF` 警告。POSIX 命令用等价
  PowerShell 形式也可以（`grep` 用 `Select-String` 等），汇报里说一句。

完成后按 STEP 5 汇报全部 5 项，并明确写出：

**P0 执行包已冻结待评审；P0 未授权、未执行，P0 正式根仍不存在；
`next_gate` 仍为 `P0_PACKET_REVIEW`；五个 open question 均未解决，留给评审裁决。**

不要提出下一步实验建议。不要回答 open question。不要自行开始评审。

=====
