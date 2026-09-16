# Prompt — D7-B easy-regime A1 feasible TREE_6

继续仓库 `D:/Code/HD-QKD_Polar_Comparison`、分支
`formal-ir-v72p1-addendum-clean` 的 D7-B 工作。完整读取并依次遵守：

1. `D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D7_B_EASY_REGIME_FREEZE_IMPLEMENT_PRE_EXECUTE_R1_TASK_PACKET.md`
2. `D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D7_B_EASY_REGIME_FREEZE_IMPLEMENT_PRE_EXECUTE_A1_TASK_PACKET.md`

A1 仅取代 R1 §3.3 的 `TREE_6` 定义；冲突处以 A1 为准，其余 R1 全部继续有效。

主线程裁决：原 `[2,3,2]` 只有 7 条边，不可能连接 9 个 Tanner 顶点。改为固定
`[3,3,2]` 与显式拓扑 `c0=[v0,v1,v2]`、`c1=[v2,v3,v4]`、
`c2=[v4,v5]`，系数逐行 `[1,7,13]`、`[29,1,7]`、`[13,29]`。
先完成 A1 九项纯结构证明和旧规格负回归；不许搜索替代 topology、labels 或 seeds。

上次 STOP 为零提交、零修改、零 decoder 调用。新鲜核对 HEAD 仍为 `f98dde08`、授权
全 false、保护根不变、G2/R1d/D7-B 根缺席后，可复用 T0 结论并从 R1 T1 连续自主
执行到 T6。不要每个小步骤回来询问；仅在全部 A1-01–A1-08 与 B01–B20 完成，或命中
一个具体硬 STOP 时返回。

本轮仍只允许冻结、实现、fake/unit qualification、独立实现评审和独立 Pre-EXECUTE。
严禁 D7-B scientific run、授权翻转、任何 `--phase`、R1d、G1/G2、Model-F、CAL、
VAL、real/raw、正式/VOID 内容读取或结果根创建。只逐路径 stage，本地 commit，不 push；
pending SOP/workbuddy 管理改动不得进入科学提交。

PASS 后必须停止在
`D7_B_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION`，不得自授执行。
按 A1.6 和 R1 §10 汇报，并使用规定的精确结束句。
