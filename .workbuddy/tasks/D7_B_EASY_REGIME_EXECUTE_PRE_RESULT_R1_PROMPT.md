# Prompt — execute one authorized D7-B invocation and Pre-RESULT review

在 `D:/Code/HD-QKD_Polar_Comparison`、分支
`formal-ir-v72p1-addendum-clean` 中完整执行：

`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D7_B_EASY_REGIME_EXECUTE_PRE_RESULT_R1_TASK_PACKET.md`

用户的逐字授权已经写在任务包 §0。它只允许按冻结
`D7_B_EXECUTION_PACKET_R1.md` 使用一个新 UUID 根调用科学命令一次；首次 scientific
decoder 尝试消耗授权，任何失败、超时、部分根或非预期终局都不得重试、重跑、恢复、
换 UUID 或改参数。

连续自主完成：新鲜 E01–E10 → 授权记录和 false→true scoped commit → 唯一科学命令
→ 进程返回后立即 true→false 单独 commit → NOT_ACCEPTED operator return → 最多一次
只读 `--verify` → 独立 Pre-RESULT R01–R16。不要在正常长运行期间因无输出而中止；
1800 秒外层 watchdog 是冻结终止边界。

环境探针必须分步执行，严禁把 RSS、`Test-Path timeout.exe`、watchdog rehearsal 或
科学命令链写在同一 PowerShell 命令中。

硬边界：不得执行 R1d、任何 `--phase`、正式 G1/G2；不得读取 Model-F、CAL、VAL、
real/raw、VOID 内容；不得修改代码、测试、OpenSpec、冻结包或结果根；不得 clean/reset/
checkout/stash/rebase/amend/broad-stage/push。pending SOP、OpenSpec 标准化和
`.workbuddy/tasks/` 管理文件不得进入科学提交。

Pre-RESULT reviewer 必须与 executor 分离并独立从 CSV/JSON 重算，不能只引用 summary。
PASS 前不得提交结果；PASS 后只固化结果与生命周期，不得自行接受科学结论。FAIL 或
BLOCKED 时保留唯一根、禁止修复和重跑、不提交结果。

只在完整结束或一个不可继续的硬 STOP 时返回，按任务包 §11 报 delta，并使用与 verdict
对应的精确结束句。
