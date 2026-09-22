# Prompt — autonomous heavy D7-C bidirectional-oracle readiness

先等待当前 D7-B early-exit audit 任务完全结束并释放 Git/test 状态。然后在同一 checkout
中完整执行：

`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D7_C_BIDIRECTIONAL_ORACLE_FREEZE_IMPLEMENT_PRE_EXECUTE_R1_TASK_PACKET.md`

启动硬门：必须存在独立 verdict
`D7_B_EARLY_EXIT_SOFT_BELIEF_AUDIT_REVIEW_PASS`。若 FAIL/BLOCKED、当前任务仍运行或存在
未收口的 in-scope 修改，立即 STOP，不并发抢 Git。

这是可长时间自主托管的重型准备任务。连续完成 OpenSpec/prereg、128-call 四条件矩阵、
runner/verifier、C01–C20、相关回归、独立 implementation review、独立 Pre-EXECUTE 和
scoped local commits。不要逐步骤询问；仅在 H01–H20 全部完成或一个硬 blocker 时返回。

D7-C 只做单层 marginal/oracle 机制诊断，不消费 L1 `final_beliefs`，所以可携带前一审计
的 metric/interface 限制继续准备，但不得修复或绕过该审计。严禁 D7-C scientific run、
真实 Model-F 内容读取、任何 production decoder call、新 UUID、authorization flip、R1d、
`--phase`、G1/G2、CAL/VAL/real/raw/VOID。

冻结矩阵必须是 16 paired blocks × f{1.0,1.2} ×
{L1 marginal,L1|true U2,L2 marginal,L2|true U1}=128 calls；只比较现有 row-layered，
不混 flooding/damping/restart/min-sum/graph search。oracle 纯诊断，不是协议恢复。

WSL RSS 必须改用 stdlib `resource` 并在未来执行前 fail closed；不得安装 psutil。所有
环境探针分步执行，禁止 shell chain。测试只用 fake joint/model/decoder；外部 sentinel
只能到达首次绑定点，绝不调用。

只逐路径 stage、本地 commit、不 push；pending SOP/workbuddy 和包外脏树不得进入提交。
PASS 后停在 `D7_C_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION`，不得生成 UUID、
请求之外执行或自授授权。

按 §12 报 delta，并使用规定的精确结束句。
