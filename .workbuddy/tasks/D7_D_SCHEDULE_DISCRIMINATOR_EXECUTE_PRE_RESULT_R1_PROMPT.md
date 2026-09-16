# D7-D execute + Pre-RESULT operator prompt R1

你是 D7-D flooding-vs-layered schedule discriminator 的一次性授权执行操作员。完整且唯一权威任务包：

`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D7_D_SCHEDULE_DISCRIMINATOR_EXECUTE_PRE_RESULT_R1_TASK_PACKET.md`

先完整读完任务包、`AGENTS.md`、`AGENT_PROJECT_MEMORY.md`、冻结的
`D7_D_EXECUTION_PACKET_R1.md`、prereg、实现评审和 Pre-EXECUTE 评审，再严格按 §1→§11
连续执行。用户的逐字授权已写在任务包 §0；不得扩大或重新解释。

你可以自主托管至运行结束，不要因运行较慢、结果阴性或普通操作判断回来询问。只有两种
返回：全部完成；或命中任务包定义的具体 STOP/BLOCKED 条件后，附失败 ID、原始输出和唯一
所需裁决并停止。

关键边界：

- 先逐项完成 E01-E14；任一失败都不得生成 UUID、翻授权或执行。
- WSL 环境探针必须逐条运行，禁止把 RSS、timeout、Python、root 或科学命令链在一行。
- 只生成一个 UUID，只运行任务包 §2 的冻结 scientific argv 一次；256 calls，不得重试、
  重跑、恢复、换根、补 cell、并发或改任何科学输入。
- 进程返回后，在读取结果内容前先把 `d7d_execution_authorized` 单独翻回 false 并提交。
- 操作员不得自审。必须使用独立 reviewer context 完成 §8；reviewer 直接从 CSV/JSON 重算，
  不能采信 operator return、summary 或 report 的结论。
- PASS 前不得固化结果；FAIL/BLOCKED 不修复、不重跑、不提交结果根。
- 不执行 R1d、任何 `--phase`、正式 G1/G2、CAL、VAL、real/raw、跨层 APP；不 push。

若 Pre-RESULT PASS，按 §9 只作事实固化，不接受科学结果，不写科学性 decision-log/memory
结论。最后按 §11 只报 delta，并使用任务包指定的精确结束句。
