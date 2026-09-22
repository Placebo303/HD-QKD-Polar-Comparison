# Prompt — accept D7-C and autonomously prepare heavy D7-D schedule discriminator

在当前 WSL checkout 中完整执行：

`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D7_C_ACCEPT_D7_D_SCHEDULE_FREEZE_IMPLEMENT_PRE_EXECUTE_R1_TASK_PACKET.md`

主线程已按任务包 §0 接受 D7-C 为有边界的
`D7_C_RESULT_ACCEPTED_BIDIRECTIONAL_DEPENDENCE_DIAGNOSTIC`：f=1.2 两层都有 strong oracle
lift，但这不证明 alternating/joint BP 能自行启动。先完成 D7-C acceptance commit，再进入
D7-D；不得直接实现跨层 BP。

这是重型自主 readiness 任务。连续完成：D7-C 接受 → D7-D OpenSpec/prereg → flooding
独立 tiny correctness certification F01–F08 → 256-call paired schedule harness/verifier →
S01–S22 → 回归 → 独立 implementation review → WSL Pre-EXECUTE → scoped local commits。
仅在 A01–A20 全部完成或硬 STOP 时返回，不要逐步询问。

D7-D 唯一变量是 schedule：ROW_LAYERED vs FLOODING。所有 blocks、f、conditions、priors、
H、rows、syndrome、decoder配置完全配对。不得加入 damping/clipping/restart/min-sum、
graph/mother、更多 disclosure、跨层 APP 或调参。iteration 不能单独当性能指标，必须记录
check/edge updates 与 wall。

本任务不授权 256 次 scientific run。严禁真实 Model-F 内容、production decoder call、
UUID、授权翻转、D7-C 重跑、R1d、任何 `--phase`、G1/G2、CAL/VAL/real/raw/VOID。测试仅
fake/tiny synthetic；flooding certification FAIL 时保留最小反例并停止，不顺手修 decoder。

环境探针分步运行；WSL RSS 用 stdlib resource，不装 psutil。只逐路径 stage、本地 commit、
不 push；pending SOP/workbuddy 和包外脏树不进入提交。

PASS 后停在 `D7_D_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION`，不生成 UUID、
不请求之外执行、不自行授权。按 §16 报 delta并使用精确结束句。
