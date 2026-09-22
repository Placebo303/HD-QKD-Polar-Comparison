你是 D5 G1 单次正式尝试的独立 Pre-RESULT 评审。你没有执行该次运行，不得采信操作员的 PASS 或算术；必须直接读取冻结包、两个执行提交、当前聚合/分类源码和新 G1 根的四个标量文件，自行复算。

任务包全文：
`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_G1_PRE_RESULT_REVIEW_R1_TASK_PACKET.md`

基线：分支 `formal-ir-v72p1-addendum-clean`；授权提交 `f4d577fb6b53cc58a23ada532331a5df3fac357f`；consumed-attempt return 提交 `58c68961a1dedad58f52145e9f23942f2c476e4a`；接受实现 `cf61ee63f5b76b0223838717b1344e0e7c3867ee`；新结果根 `workspace/v72p2d5_g1/20260907_r2`。

完整读完任务包后按 §1→§8 做只读复审。结论只能是 `G1_PRE_RESULT_REVIEW_PASS` 或 `G1_PRE_RESULT_REVIEW_FAIL`；任何 STOP 条件触发就贴原始证据并停止，不修复。

必须独立核验：

- 两提交只完成 G1 false→true→false、授权记录/评审落地和 operator return；
- frozen 参数和唯一调用身份未漂移，G2 从未出现；
- 新根恰四文件且 JSON/CSV/report/execution-summary 同值；
- 440 calls 算术、每 f 的 attempted/exact/failure/syndrome/iterations/nonfinite/RSS；
- exact、syndrome、oracle、nonfinite/crash 完全隔离，syndrome 绝不能并入 exact 或降低 failure；
- 0/0 exact 虽然单调，但 `top>0` 为 false，因此必须是 `G1_COMPLETED_NO_SIGNAL_FAIL` 且 `passed=false`；
- stored wall 238.86517630005255 s 和 operator wall 239.110 s 都≤900；peak RSS 115142656 已知且<2GiB；资源通过不得把 no-signal 改成 trend pass；
- 四文件没有 raw symbols、priors、beliefs、逐块记录、CAL/VAL 行或 secret material。

硬禁令：不许运行 decoder、任何 `--phase`、重试、重跑、恢复、prepare/verify、pytest、compile 或 probe；不许读 CAL/VAL/parquet/raw rows；不许打开或引用旧 VOID-G1 内容；不许改动任何 workspace 证据、代码、既有文档、OpenSpec、状态、decision-log、memory；不许任何 git 写或 push；不许修复、接受结果、授权 G2 或另一次 G1。

唯一允许的新建文件：
`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_PRE_RESULT_REVIEW_R1.md`
不提交、不 push、不改 `cycle_state.yaml`。

PASS 仅说明这份“完成但无信号失败”的记录内部自洽，可交主线程另行做结果接受裁决；PASS 不会把结果变成趋势通过，不构成 FER、泄漏、密钥率、资格、方法成功、G2 readiness 或重跑许可。

完成后按任务包 §8 汇报，并原样结束：

`G1 结果仅按“完成但无信号失败”候选接受性完成复审；本复审不是结果接受，不授权重跑或 G2。`
