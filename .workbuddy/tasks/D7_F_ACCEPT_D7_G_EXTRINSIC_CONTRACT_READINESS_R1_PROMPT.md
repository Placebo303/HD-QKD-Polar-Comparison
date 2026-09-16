# D7-F Acceptance + D7-G Extrinsic Contract Readiness R1 Prompt

在 `HD-QKD_Polar_Comparison`、分支 `formal-ir-v72p1-addendum-clean` 执行：

`.workbuddy/tasks/D7_F_ACCEPT_D7_G_EXTRINSIC_CONTRACT_READINESS_R1_TASK_PACKET.md`

完整读取任务包、根 `AGENTS.md`、D7-F prereg/packet/结果/Pre-RESULT/state、D7-E acceptance、现行 v35 decoder 与 BP provenance OpenSpec。按 Phase A→G 长时间自主推进，只回 §11 delta。

先受限接受 D7-F，再冻结并实现 D7-G 的 code-factor extrinsic 接口。核心合同是冷启动且至少一轮 check sweep 后，显式输出 `L_code_ext = L_post - log(p_in)`（仅差行常数）；iteration 0 输出 neutral + `NO_CHECK_EVIDENCE`，warm start 保持不可用。不得把 posterior 改名为 extrinsic，也不得让任何现有 D5/D6/D7 consumer 自动切换到新字段。

最重要验收是独立两层树 factor-graph 证明：构造 posterior 回传会重复计算源 syndrome 的负对照，同时证明显式 code-extrinsic 的前后向消息与独立 sum-product 一致。树图对精确分布；loopy 图只对独立 recurrence，不对 MAP。若这项不能证明，立即 STOP，不弱化容差或改写科学问题。

这是零生产/科学运行任务。只允许 tiny in-memory certification；不得读 Model-F/CAL/VAL/real/raw/VOID，不得运行 D7-F/D7-G/H/R1d/G1/G2 或任何 `--phase`。允许完成 OpenSpec、最小实现、测试、双独立评审和本地 scoped commits。reviewer-go 的独立测试可直接采用，不重复完整套件。不得 push、broad-stage 或清理包外脏树。

双评审 PASS 后只接受接口合同并停在 `D7_H_ALTERNATING_DISCRIMINATOR_PACKET_FREEZE`；不要在本任务内冻结、实现、请求或执行 D7-H。
