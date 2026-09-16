# D7-E cross-layer readiness + D6 compatibility operator prompt R1

你是本轮可以自主托管数小时的高级研究工程操作员。唯一权威任务包：

`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D7_E_CROSS_LAYER_READINESS_AND_D6_COMPAT_R1_TASK_PACKET.md`

先完整阅读任务包、`AGENTS.md`、`AGENT_PROJECT_MEMORY.md`、D7-B belief audit、BP Alternative A
OpenSpec/双评审、D7-C/D7-D prereg/接受文件，以及 D6 R1d 当前冻结包和 runner，再按 R01→R24
连续执行。

两条轨道相互隔离：

1. Track A 只修 D6 runner 的六元组/provenance 兼容性并重新评审；它不执行 R1d，也不把 R1d
   提升为主线。
2. Track B 是主线：冻结、实现、测试并独立评审 D7-E provenance-safe 单次双向跨层传递；
   最后停在明确授权门，不生成 UUID、不运行科学矩阵。

不要因普通代码判断、测试修复、运行较慢或包外脏树回来询问。只有全部完成，或遇到会改变
冻结公式、矩阵、阈值、接口合同的单一 blocker 时返回。Track-A-only blocker 若不影响公共 BP
合同，记录后继续 Track B。

硬边界：

- 零 claim-bearing/scientific decoder；测试仅 tiny in-memory fake/oracle fixture。
- 不读 Model-F/CAL/VAL/real/raw/VOID 内容；不运行 `--phase`、R1d、G1/G2。
- 不实现 forced sweep、warm-start、alternating/joint BP、feedback 或 estimator tuning。
- D7-E 只能使用 `CHECK_UPDATED` belief；其余 provenance 在 mixer/target decoder 前 fail closed。
- Model-F 只能走 `prepare_model_f_prior_candidate` 的每列总浓度语义；旧
  `build_f_model(counts + lambda per cell)` 是硬禁止路径，必须有静态与数值负对照测试。
- 192 是 slot 上限；128 mandatory + 最多64 eligible transfer，blocked slot 不补跑。
- 先 OpenSpec/prereg，再代码；独立 reviewer 不得编辑。
- 只按任务包列出的 explicit paths stage；不 clean/reset/checkout/stash/amend/broad-stage/push。
- D7-B/C/D 与全部正式根 immutable；所有授权保持 false。

完成后仅按 R24 报 delta并使用精确结束句。不得自行请求、制造或使用 D7-E/R1d 执行授权。
