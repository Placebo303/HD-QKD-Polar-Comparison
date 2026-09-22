# Prompt — D7-B WSL launch binding rework and renewed Pre-EXECUTE

在当前 WSL 服务器上的 `HD-QKD_Polar_Comparison` checkout 中执行完整任务包：

`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D7_B_WSL_LAUNCH_REWORK_PRE_EXECUTE_R1_TASK_PACKET.md`

若 WSL 中仓库显示为 `/mnt/...`，先从当前 checkout 自身解析对应文件；不要把 Windows
路径或 `/mnt/...` 写成新的代码默认值。

主线程已裁决：上次唯一调用是
`D7_B_PRE_EXECUTION_LAUNCH_BINDING_BLOCKED`，不是 decoder/easy-regime 结果。旧授权和
UUID 永久耗尽，不得重试、恢复或复用。根因候选是 file-location 顶层加载 v35 导致其
`from .nonbinary_field` 丢失 package context；必须先零-decoder复现，若根因不同立即 STOP。

你可自主连续完成 T0→T5：保留 blocked provenance、OpenSpec/WSL command addendum、
最小 local-source package import 修复、L01–L12、独立 code review、actual-WSL renewed
Pre-EXECUTE、scoped local commits 与 closeout。只在全部 W01–W16 完成或一个硬 blocker
出现时返回。

修复优先采用 ponytail-lite：runner 根据 resolved `__file__` 把本 checkout 的
`comparison_bench/src` 加入当前进程导入路径，再走正常 package import。不要安装包、
设置全局 PYTHONPATH、复制 decoder、构造通用 import framework，亦不得修改 v35、D5、
D7-A 或任何科学参数/schema。

所有环境探针必须逐条独立执行，禁止把 RSS、timeout 检查、rehearsal、runner probe
链在一个 shell 命令中。只允许 bind/import 到准确 v35 callable，绝不调用 decoder。

严禁 D7-B scientific run、新 UUID、授权翻转、任何 `--phase`、R1d、G1/G2、Model-F、
CAL、VAL、real/raw、VOID 内容读取、结果根创建、broad Git 操作或 push。pending SOP/
workbuddy 管理文件不得 stage。

PASS 后停止在
`D7_B_PRE_EXECUTE_REVIEW_PASS_WSL_R2_AWAITING_FRESH_AUTHORIZATION`，旧授权不能复活。
按任务包 §9 报 delta，并使用规定的精确结束句。
