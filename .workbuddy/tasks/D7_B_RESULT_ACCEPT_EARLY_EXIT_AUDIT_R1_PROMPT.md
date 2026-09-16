# Prompt — D7-B scoped acceptance and early-exit belief audit

在当前 `HD-QKD_Polar_Comparison` checkout 中完整执行：

`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D7_B_RESULT_ACCEPT_EARLY_EXIT_AUDIT_R1_TASK_PACKET.md`

主线程的受限裁决已冻结在 §0：接受 R2 生命周期和
`D7_B_RESOURCE_OVERRUN` 原终局；RSS null 是 telemetry unknown，不是测得超限；64/64
exact+syndrome 只支持 truth-centered prior 下的 hard-decision sanity region，不能改写成
`EASY_REGIME_CONFIRMED`。49 个 iteration-0 返回和 tractable posterior 0.5/0.4 误差
必须先做 soft-belief 合同归因。

连续自主完成 Phase A 接受记录 → E01–E12 零-decoder分析 → I1/I2/I3 分层裁决 → 独立
review → 路线 gate 与 scoped local commits。只在 A01–A16 完成或一个硬 STOP 时返回。

禁止任何 decoder 调用、D7-B 重跑、R1d、D7-C/D、`--phase`、G1/G2、Model-F、CAL、
VAL、real/raw、VOID 内容读取；R2 根完全 immutable。允许读取其五个标量文件、源码和
冻结文档，并用 D7-A 独立 oracle 做纯数学计算。不得修改生产代码或实现修复。

必须分别判断：hard-decision correctness、v35 belief-return contract、D5 layer-interface
expectation、D7-B posterior metric validity。不要因 `final_beliefs` 名称自行假定它是
syndrome-conditioned posterior。独立 reviewer 必须重算代表性 posterior 和 49/15 分组。

所有 authorization 保持 false，只逐路径 stage、本地 commit、不 push；pending SOP/
workbuddy 和包外脏树不进入提交。按 §11 报 delta，并使用规定的精确结束句。
