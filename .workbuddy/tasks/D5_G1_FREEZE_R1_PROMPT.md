你是 D5 G1 冻结包的文档执行 session。本任务只冻结包，不实现、不授权、不执行。

任务包全文：
`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_G1_FREEZE_R1_TASK_PACKET.md`

先完整读完，再严格按 STEP 1→8 执行。不要改写要求、不要回答五个 open question、不要推进到 Pre-EXECUTE 或 G1 执行。

关键事实：

- P0 已仅按 `COST_MEASUREMENT_ONLY` 接受；`next_gate` 已是 `G1_PACKET_REVIEW`。
- 旧 G1 根 `workspace/v72p2d5_g1/20260906_r1/` 是未授权测试事故产物，已永久标记 `VOID_RETAINED_IN_PLACE`。它必须原地不变，绝不允许复用、覆盖、比较或引用为性能结果。
- 当前生产常量仍指向这个旧根，所以 G1 现在不可执行。包内提出的新根是 `workspace/v72p2d5_g1/20260907_r2/`，但必须留给独立评审明确接受或替换。
- 当前 G1 schema 缺少 syndrome/iteration/RSS 的充分观测；两个 writer 还有重复的 `app_failure_fraction` fallback；守卫快照只看顶层。这些都必须写成执行前的小型实现 delta，而不是在本任务里修。
- 当前 G1 的 `passed = monotonic and nonfinite == 0` 会让全零 exact 率也通过。不要替主线决定这是否可接受；把它作为 `OQ-G1-SIGNAL` 留给独立评审作前瞻裁决。

硬禁令：

- 不许运行 decoder，不许运行任何 `--phase`，不许运行 prepare/verify。
- 不许读取 CAL/VAL/parquet 行，不许修改或创建任何 `workspace/v72p2d5_*` 内容。
- 不许改任何 `.py`、既有 `.md`、OpenSpec、decision-log、memory 或 `cycle_state.yaml`。
- 只允许新建 `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_EXECUTION_PACKET_R1.md`。
- 只允许 stage 并提交这一文件；禁止 `git add .`、`git add -A`、`commit -a`、push、reset、stash、checkout、clean、rebase、amend。
- 发现偏差只 STOP 汇报，不自行修复。

冻结参数必须逐项写全：n_IR=64；f=1.0/1.2；rows 49/59 与 43/52；图种子 2026090501/2026090502；块种子 2026090600..0699；100 paired blocks/f；oracle 前20/f；440 calls；历史 GF32、cold start、max_iter=90、damping=1.0；总预算900s；四文件 no-overwrite；Model-F 固定根；L1→L2；oracle纯诊断。

必须携带 D1–D6、L1–L4/L-RSS/L-SCALE/L-ITER/T1，以及五个仍为 OPEN 的 OQ-G1-ROOT/RSS/SIGNAL/WATCHDOG/OUTCOME。不得把任何 OQ 写成已决定。

无需跑 pytest。提交前只做任务包要求的只读根快照、授权核对、`.py` 内容差异为空核对，以及 staged 恰一文件核对。

完成后按 STEP 8 汇报，并以这句收尾：

`G1 执行包已冻结待独立评审；G1 未授权、未执行；新 G1 根尚未创建；G2 未授权。`
