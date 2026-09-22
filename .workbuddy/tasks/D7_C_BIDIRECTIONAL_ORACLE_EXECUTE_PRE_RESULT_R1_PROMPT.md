# Prompt — execute one authorized D7-C bidirectional-oracle run

在当前 WSL checkout 中完整执行：

`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D7_C_BIDIRECTIONAL_ORACLE_EXECUTE_PRE_RESULT_R1_TASK_PACKET.md`

若 Windows 表示路径不可直接访问，从当前 checkout 定位同一文件，禁止硬编码 `/mnt/...`。

用户授权已逐字写入 §0。只允许一个新 UUID、一次冻结 scientific command、128 个固定
calls；首次 decoder 尝试消耗授权，任何失败/超时/部分根/环境异常都不得重试、恢复、
换根、改 estimator 或参数。

连续自主完成 E01–E14 → 新 UUID → false→true scoped commit → 精确 WSL command 一次
→ 立即 true→false 单独 commit → NOT_ACCEPTED return → 最多一次只读 verify → 独立
Pre-RESULT R01–R20 → 仅 PASS 后固化。长时间无输出不是中止理由，由 1800s GNU timeout
负责终止。

先单独激活已评审 venv-on-PATH，并分别记录 `command -v python`、版本、RSS、timeout、
sentinel；禁止把环境探针或科学命令 chain 在一起。PATH 适配不能改变冻结 child argv，
不得添加 PYTHONPATH。

严禁 R1d、任何 `--phase`、G1/G2、CAL/VAL/real/raw/VOID、跨层 APP、代码/测试/OpenSpec/
冻结包修改。只有唯一科学命令可读取 accepted Model-F。进程退出后结果根 immutable。
只逐路径 stage、本地 commit、不 push；pending SOP/workbuddy 和包外脏树不得进入提交。

reviewer 必须独立于 executor，从 CSV/JSON 重算 paired 2×2 counts、四 strata 与 terminal。
PASS 前不得提交结果；PASS 后也不自行接受科学结论。FAIL/BLOCKED 不修复、不重跑。

按 §11 仅报 delta，并使用对应精确结束句。
