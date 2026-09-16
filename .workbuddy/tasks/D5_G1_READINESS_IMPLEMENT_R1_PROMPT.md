你是 D5 G1 readiness 的实现 session。严格实现已独立通过的 G1 packet review；不要重新定义科学规则，不要授权或执行 G1。

任务包全文：
`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_G1_READINESS_IMPLEMENT_R1_TASK_PACKET.md`

先完整读完，再按 §1→§9 执行。OpenSpec 四文件必须先创建，之后才能编辑代码。

本任务的唯一目标是让 G1 达到可做独立 Pre-EXECUTE 评审的实现候选状态：

- G1 正式根改为唯一新根 `workspace/v72p2d5_g1/20260907_r2`；旧 `20260906_r1` 永久 VOID，不许读其数字、不许复用、不许覆盖、不许比较。
- Windows RSS 用 stdlib ctypes 测当前 Python 进程 working set；每个完成 block 采样，持久化 per-f 和 run peak；None 或 >=2 GiB 不得 pass。
- 每个 f 增加 APP/oracle syndrome 与 iteration 聚合、nonfinite、peak RSS；不写 raw symbols/beliefs/priors/per-block records。
- signal 规则固定为：零 nonfinite、非递减、top exact>0、且严格改善或两点都饱和 1.0。全零和正数平 plateau 都 fail；双 1.0 pass。
- completed-path outcome 优先级固定为 nonfinite → wall>900 → RSS unknown/over → trend pass → no-signal fail；`passed` 仅在 `G1_TREND_PASS` 为 true。
- pre-exec blocked、watchdog timeout、Python exception 属操作员侧终态，不许为了写四文件而捕获异常或造 partial-result 恢复框架。
- G1/G2 writer 对 `app_failure_fraction` 直接必需键访问；不加兼容层。
- 两测试文件的 formal-root helper 加 no-subdirectory 不变量；不做递归哈希。

硬禁令：不许运行 decoder 或任何 CLI `--phase`；不许 prepare/verify；不许读 CAL/VAL/parquet 行；测试不许读真实 Model-F 根；不许修改任何 workspace 证据；不许创建新 G1/G2 正式根；不许改授权位、cycle state、decision-log、memory 或冻结结果；不许新增依赖、重试/恢复/manifest/hash 框架；不许 push 或清理已知 EOL churn。

测试中的 authorized synthetic 调用必须同时显式传 fake decoder、注入数组和 tmp out_dir。basetemp 必须是本任务专属的 `workspace/` 子目录，跑后只删自己创建并已验证路径的目录。

提交严格两次：先 review+OpenSpec 五路径，再 core+两测试三路径。每次 stage 后必须打印暂存清单；混入任何路径立即 STOP，不要自行 reset/checkout。

遇到需求歧义不要猜，按 §9 STOP，给出唯一需要主线裁决的问题。全部完成后按 §9 汇报，并原样写：

`G1 readiness 实现候选完成，等待独立代码评审；G1 未授权、未执行；新 G1 根与 G2 根仍不存在。`

