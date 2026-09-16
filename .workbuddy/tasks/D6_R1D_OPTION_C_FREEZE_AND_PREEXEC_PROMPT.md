# D6 R1d Option C freeze and Pre-EXECUTE prompt

你负责把主线程的 D6 Option C 裁决完整落地并推进到 R1d 独立
Pre-EXECUTE PASS。完整任务包：

`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D6_R1D_OPTION_C_FREEZE_AND_PREEXEC_TASK_PACKET.md`

先完整阅读任务包及其直接引用的 A3/A5/A6 文档，然后连续完成 OpenSpec、裁决记录、R1d 执行包、最小实现、测试、独立代码评审和独立 Pre-EXECUTE。不要为普通工程判断或中间进度询问主线程；只有全部完成或遇到会改变冻结科学契约的单一 blocker 才返回。

主线程裁决已经确定，不得重新投票或扩大探索：选择 Option C，不抬 SC/M 旋钮；R1d arms 恰为 B0/B1/T1；T2 仅保留 rank-bound 记录、不执行；批准新 R1d schema 增加 `row_degree_min`、`rows_below_degree_2` 和 eligible/schema version marker，历史 A2 schema/root 永久不改。

首要任务是先把 R1d 的完整 cell schedule 展开，并逐 cell 对照 A5 validity matrix 证明 frozen eligibility+I1 都通过。若原冻结流程必然要求某个无效 cell，立即 STOP 上报精确冲突，不得静默删 cell、换 rows、换 seed 或降低 gate。

实现只服务于 eligible-only 路径：B0/B1 controls、T1 唯一新 arm、scaling fallback 仅 T1；沿用 A4/A6 已接受提速。保留 E2 prior、rows、seeds、decoder、90 iterations、damping、L1→L2、oracle diagnostic-only、thresholds、2500 calls/12h/120s/<2GiB/no-retry。新根只能是 fresh `workspace/d6_graph_mother_r1d_<uuid>/`，本任务不得创建它。

严格禁止任何真实 decoder、`--phase`、正式 G1、G2、VAL、real/raw；禁止复用或读取 A2/VOID 数字作为 R1d 科学输入；禁止改历史根、调参、启动 A/B repair、push 或清理脏树。测试只能 fake/tmp。

最终必须得到独立 verdict
`D6_R1D_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION`，然后 STOP，不能自授执行。按任务包 §9 回 delta，并原样结束：

`Option C 已落地：D6 R1d 仅保留 B0/B1/T1 并完成独立 Pre-EXECUTE；R1d 尚未授权、未执行，历史 A2 根未复用，G2 未授权、未执行。`
