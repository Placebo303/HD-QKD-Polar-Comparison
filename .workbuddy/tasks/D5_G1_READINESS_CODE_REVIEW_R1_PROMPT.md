你是 D5 G1 readiness 的独立只读代码评审。你没有编写 `614aab9e` 或 `cf61ee63`，不要采信实现者的 PASS、测试数或映射，必须读实际 diff/current source 并自行运行允许的检查。

任务包全文：
`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_G1_READINESS_CODE_REVIEW_R1_TASK_PACKET.md`

评审整体候选：

- `d47e7da1`：评审 + OpenSpec；
- `614aab9e`：G1 readiness 实现；
- `cf61ee63`：Windows RSS ABI 修复。

完整读完任务包后按 §2→§7 执行。结论只能是 `G1_READINESS_CODE_REVIEW_PASS` 或 `G1_READINESS_CODE_REVIEW_FAIL`。

必须特别打穿 RSS，而不是只看 fake：直接、无 monkeypatch 调用当前 Windows `_rss_bytes()`，必须得到正整数；核对 PROCESS_MEMORY_COUNTERS 在本机为 72 bytes，三处 WinAPI ctypes 签名在调用前设置。判断 fake 测试是否会在任一签名被移除时真正失败。

同时独立审计：200 次 RSS 采样和任一 None 阻断；per-f exact/syndrome/iterations/RSS 聚合；440 calls；五类正常返回 outcome 的优先级；`passed iff TREND_PASS`；G1/G2 writer fail-loud；新根/no-overwrite；两测试 helper 的 no-subdirectory；SAFE A/B/C/TIS；真实 Model-F 外部探针仍留给 Pre-EXECUTE。

硬禁令：不许运行 decoder 或任何 `--phase`，不许 prepare/verify，不许读 CAL/VAL/parquet 行，不许读取真实 Model-F artifact，不许改 workspace 正式证据，不许改代码/既有文档/OpenSpec/状态，不许任何 git 写操作。pytest 只用独立 `workspace/` basetemp，结束后只删除自己的目录。

只允许新建：
`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_READINESS_CODE_REVIEW_R1.md`
不提交、不 push、不修复发现。

若 live RSS 返回 None、任一真实授权调用可能触及旧 VOID 根、全零能重新 pass、RSS unknown 能 pass、writer 能静默补缺失 metric、或测试能触发 production decoder/formal root，均为 blocking FAIL。

完成后按任务包 §7 汇报，并原样写：

`G1 readiness 代码评审不构成执行授权；G1 未执行；新 G1 根与 G2 根仍不存在。`

