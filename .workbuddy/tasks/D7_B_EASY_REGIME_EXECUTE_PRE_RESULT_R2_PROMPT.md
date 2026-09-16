# Prompt — D7-B WSL R2 one-shot execution and Pre-RESULT

在当前 WSL checkout 中完整执行：

`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D7_B_EASY_REGIME_EXECUTE_PRE_RESULT_R2_TASK_PACKET.md`

若该 Windows 表示路径在 WSL 不可直接访问，从当前 checkout 定位同一文件；不要把机器
特定 `/mnt/...` 路径写入代码或科学合同。

用户的新授权已逐字写在 §0，仅适用于一个全新 R2 UUID。旧 UUID
`0f1ad3ec-f9e0-463f-a7dd-d9880ff7230c` 与旧授权永久耗尽，严禁复用。

连续自主完成 E01–E12 → 唯一 UUID → auth false→true scoped commit → 精确 WSL 命令
一次 → 立即 true→false 单独 commit → NOT_ACCEPTED return → 最多一次只读 verify →
独立 Pre-RESULT R01–R18 → 仅 PASS 后固化。长运行无输出不是中止理由；由冻结 1800s
GNU timeout 终止。

所有环境探针逐条执行，严禁 shell chain。不得安装 pytest/依赖、改代码/参数、添加
PYTHONPATH、重试、恢复、换 UUID。严禁 R1d、任何 `--phase`、G1/G2、Model-F、CAL、
VAL、real/raw、VOID 内容读取。结果根在进程退出后 immutable。只逐路径 stage，本地
commit，不 push；pending SOP/workbuddy 管理改动不得进入提交。

Pre-RESULT reviewer 必须独立于 executor，并从 CSV/JSON 重算。PASS 前不提交结果，
PASS 后也不自行接受科学结论；FAIL/BLOCKED 保留根、不提交、不修复、不重跑。

按 §11 仅报 delta，使用与 verdict 对应的精确结束句。
