# Paste-ready prompt — D5-MODELF-ACCEPT-R1 (weak session)

Copy everything between the two `=====` lines into a fresh session opened in
`D:/Code/HD-QKD_Polar_Comparison`.

=====

你是这个仓库的执行 session。本次任务是**纯文档 + 一次本地 git 提交**，零科研执行。

任务包全文在：
`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_MODELF_ACCEPT_R1_TASK_PACKET.md`

第一步：完整读完这个文件，一行都不要跳过。然后严格按 STEP 1 → STEP 8 顺序执行，
不要重排、不要合并、不要跳步。

必须遵守的框架：

1. 任务包第 0 节有 12 条硬禁令。任何一条被触发，立刻停止，不要继续，不要自行
   修复，直接把失败的步骤号和原始输出报给我。
2. 每一步都给了期望输出。对不上就是 STOP 条件，不是让你调整期望值，也不是让你
   重跑到通过。**例外**：G02 的 `195 passed` 和 G06 的 `STAGED_COUNT 5` 是参考值，
   不是通过条件——G02 只有出现 failure 才 STOP，G06 以 `OUT_OF_SCOPE []` 为准；
   两者都照实报数。
3. 你只能新建 **1 个**文件：
   `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/MODEL_F_INPUT_RESULT_ACCEPTANCE_R1.md`。
   只能改 **3 个**既有文件：`cycle_state.yaml`（按 STEP 3 插入一段 + 末尾追加两行
   注释，其余一个字不许动）、`docs/decision-log.md`（仅追加）、
   `AGENT_PROJECT_MEMORY.md`（仅追加）。模板全文在任务包里，照抄并填实测值。
   除此之外不许新建、不许改任何文件。
4. 一个 `.py` 都不许改。
5. **绝对不许改 `workspace/v72p2d5_model_f_input/20260907_r1/` 里的任何文件**——
   不要去把 `model_f_input_summary.json` 的 `status` 从 `CANDIDATE` 改成
   `ACCEPTED`。那个根是不可变的，接受是记在 cycle 层面，loader 两个值都认。
   `workspace/` 下一律不许删/移/改名/复制/规范化/算 hash/以写模式打开。
6. **九个 `*_execution_authorized` 全部保持 `false`，`next_gate` 保持
   `P0_PACKET_REVIEW`，一个字都不许改。** 本次接受**不**授权 P0。
7. 不许运行 decoder、不许运行 `--phase p0-cost|g1|g2`、不许运行
   `v72p2d5_prepare_model_f_input.py`（prepare/verify 授权已消耗，禁止重放）、
   不许 `pandas.read_parquet`、不许读 CAL/VAL/原始数据。
8. git 只允许 STEP 7 的一次白名单 `git add` + 一次 `git commit`。**严禁**
   `git add -A`、`git add .`、`git commit -a`、`git push`、`git reset`、
   `git stash`、`git checkout --`、`git clean`、`git rebase`、`git commit --amend`。
   commit message 照抄任务包原文，含 `Co-Authored-By` 行。
   G06 若 FAIL：STOP，不提交，**不要 unstage、不要 clean**，带着已暂存的 index
   停住就是正确状态。
9. 不许写 `RESULT_SUMMARY.md`、`OPERATOR_RETURN.md`、任何 `run_01`。
10. 不许给出任何科研结论：不许说 FER、泄漏、密钥率、方法结论、G1 性能结论。

背景（已冻结，不要重新推导、不要质疑、不要改写）：
- 独立 Pre-RESULT 复审 R2 结论 `PRE_RESULT_REVIEW_PASS` /
  `READY_FOR_MAIN_RESULT_ACCEPTANCE`，C01-C11 全 PASS，`195 passed`。
  **就绪信号不等于接受**，本任务包执行的才是接受动作。
- **PR16 是"以记录方式清除"，不是条件达成。** R1 的 PR16 是"正式根必须缺席"
  这条形式检查，而 G1 根现在依然存在；R2 是把它按意图（未授权数字不得进入结果链）
  重新解释，判定该意图已被 `VOID_RETAINED_IN_PLACE` 处置闭合。这一条必须原样写进
  接受记录和 decision-log，**不许简写、不许含糊过去**。
- 两条残余风险必须原样带进记录：`R-R1` 生产侧默认仍绑定历史 decoder + 正式根，
  防复发只靠测试侧，未来 P0/G1/G2 包必须重验隔离；`R-R2` `M24`/`P12` 不再断言
  全局正式根缺席，只剩逐测试快照比对。
- 下列输出不是失败：`LF will be replaced by CRLF` 警告、
  `PytestConfigWarning: Unknown config option: cache_dir`、
  `workspace/v72p2d5_accept_r1_*` 这个 pytest basetemp 目录存在（不在白名单里，
  保持不提交即可）。POSIX 命令用等价 PowerShell 形式也可以，汇报里说一句。

完成后按 STEP 8 汇报全部 6 项，并明确写出：

**Model-F 输入已接受；PR16 是以记录方式清除、非条件达成；P0 未授权，
`next_gate` 仍为 `P0_PACKET_REVIEW`。**

不要提出下一步实验建议。不要自行开始 P0 的包。

=====
