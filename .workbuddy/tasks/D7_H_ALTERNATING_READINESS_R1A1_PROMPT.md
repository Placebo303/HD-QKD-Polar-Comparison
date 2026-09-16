# D7-H Alternating Readiness R1A1 Prompt

在 `HD-QKD_Polar_Comparison`、分支 `formal-ir-v72p1-addendum-clean` 执行：

`.workbuddy/tasks/D7_H_ALTERNATING_READINESS_R1A1_TASK_PACKET.md`

完整读取任务包、根 `AGENTS.md`、D7-G OpenSpec/实现/双评审/acceptance/state，以及当前未提交的 D7-H packet pair、prereg/state/OpenSpec 草案。按 Phase A→F 长时间自主推进，只回 §11 delta。

当前 D7-H 文件只是未提交草案，不是权威冻结。先按 R1A1 修正：只有 STAGE0 无条件 mandatory；STAGE1 必须由 STAGE0 的 exact `CHECK_EXTRINSIC` 门控；STAGE2 必须由 STAGE1 同样门控；最少32、最多96 calls；coverage 按三阶段完整链计。修正并经独立 packet review PASS 后，先单独提交 freeze，再写实现。

实现保持最小：一个 module、一个 test、一个 script，复用 D7-E/F/G 窄接口，不造通用 turbo 框架。核心科学门是 explicit code extrinsic 和 cavity/no-returned-evidence；posterior 路径必须被 poison 测试阻断。顺带修复 D7-G 已接受 additive API 引起的一个 stale field-list test，只更新兼容性断言，不删数值门。

允许 OpenSpec、实现、tiny fake/in-memory tests、独立 reviewer-go 评审和本地 scoped commits；reviewer-go 的独立测试结果可直接采用，不重复完整套件。绝对禁止 D7-H scientific run、UUID/root、Model-F 内容读取、CAL/VAL/real/raw、R1d/G1/G2、任何 `--phase`、push 或脏树清理。

任何 packet 内部矛盾、无法证明 cavity 性质、前驱漂移、scope 扩张或新增 in-scope regression 立即 STOP。双评审 PASS 后停在 `D7_H_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`，不得请求或推断执行授权。
