你是 D5 G1 readiness 的窄修复 session。当前候选的 fake RSS 测试全绿，但真实 Windows `_rss_bytes()` 返回 None，已确认是 ctypes WinAPI 签名缺失，不是科研数据问题。

任务包全文：
`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_G1_RSS_ABI_FIX_R1_TASK_PACKET.md`

完整读完后严格执行。只允许改 core、rate-mother 测试、现有 readiness OpenSpec tasks 三文件。

修复点唯一：为 `GetCurrentProcess` 与 `GetProcessMemoryInfo` 声明正确的 HANDLE/BOOL/DWORD/POINTER ctypes 签名。保留 Unix resource 路径、现有采样与 outcome 逻辑。不要顺手重构。

必须补一个不 monkeypatch 的 live smoke：在当前 Windows 上直接调用真实 `_rss_bytes()`，断言返回正整数。原有 fake windll 测试必须升级为能验证 `argtypes/restype` 真正被设置；只返回一个假数字但忽略 ABI 声明不算覆盖。

硬禁令：无 decoder、无任何 `--phase`、无 prepare/verify、无 CAL/VAL/parquet 行、无 workspace 证据写入、无新 G1/G2 根、无授权/状态变更、无依赖、无 push、无清理工作区。

跑 focused + 完整三文件套件，basetemp 必须在 `workspace/` 下且只删自己的目录。再做一次操作员级真实 `_rss_bytes()` 调用，必须报告类型和值。

只 stage 三个允许文件，提交信息照抄任务包。完成后按 §7 汇报，最后原样写：

`Windows RSS ABI blocker 已修复，等待独立代码评审；G1 未授权、未执行；新 G1 根与 G2 根仍不存在。`

