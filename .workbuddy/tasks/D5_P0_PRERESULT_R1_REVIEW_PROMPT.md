# Paste-ready prompt — D5-P0-PRERESULT-R1 independent Pre-RESULT review

Copy everything between the two `=====` lines into a FRESH session opened in
`D:/Code/HD-QKD_Polar_Comparison`. Do not reuse the session that ran P0.

=====

你是本次的**独立只读评审**。你没有跑 P0，也没有参与之前任何一次 D5 任务包的执行；
不要采信任何既有说法（**包括任务包 §4 转述给你的那三条发现**），一切从产物和源码
重新推导。

任务包全文在：
`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_P0_PRERESULT_R1_REVIEW_PACKET.md`

先完整读完，再按 §2 → §8 执行。

被评审对象：`workspace/v72p2d5_p0_cost/20260906_r1/`（4 文件）与
`P0_OPERATOR_RETURN_R2.md`、`P0_AUTHORIZATION_RECORD_R2.md`、
`P0_EXECUTION_PACKET_ADDENDUM_A1.md`；冻结件 `P0_EXECUTION_PACKET.md`
必须逐字节未变。HEAD `b4696273`。

要裁的问题：**这个 P0 结果是否够格被接受为 P0 结论，是否支持推进到 G1 包。**
P0 是成本预检，不确立任何正确性、码率点表现、FER、泄漏、密钥率。这里的 PASS
只意味着"成本被测到且被如实记录"，仅此而已。

**§4 那三条发现必须你自己独立核实并裁定，不许照抄作者的说法：**

- **F1**：四条记录的 `rss_bytes` 全为 `null`。冻结契约把 RSS 列为记录项并设了
  2 GiB 参照。查清为什么是 null、契约是否因此未满足、这算**阻塞缺陷**、
  **记录在案的限制**、还是对一个只测 wall 的预检**无关紧要**。
- **F2**：`projected_g2_s` 可能在结构上不成立。外推是 `per_call × 调用数`，而
  `per_call` 取自 n=64 的块，G2 却是 n=256、行数约 4 倍。去源码确认这个外推
  **到底有没有随块宽或行数缩放**。若没有，说清 `projected_g2_s` 和
  `projection_blocked: false` 实际能支撑什么结论、`projected_g1_s`（与 P0 同宽）
  是否处境更稳，并明确回答：**G2 那个外推能不能用于任何决策。**
- **F3**：似乎每一次解码都跑满了迭代上限。app 记录 360 次迭代、oracle 180 次，
  而 `MAX_ITER = 90`。自己算清每条记录聚合了几次解码、单次迭代数是否正好等于上限。
  若是，说明它意味着什么、**不**意味着什么（P0 不记录正确性，所以这不是失败结论），
  以及 G1 包是否必须把它当成成本信号纳入考虑。

其余核验要点见任务包 §2/§3/§5/§6：生命周期与出处（`cycle_state.yaml` 跨两次提交
净差异为零、仅动过 `p0_cost_execution_authorized`、九位现在全 false、`next_gate`
未变、仅一次调用）、结果对冻结契约（宽 64、`f {1.0,1.2}`、种子
`2026090510/2026090511`、`m1 {49,59}`、`m2 {43,52}`、`decoder_calls` 12、四条记录、
外推可复算、四个文件互相自洽、无原始行/矩阵/先验/信念/校验子/绝对路径/校验和泄漏）、
以及 operator return 的措辞是否守住了 P0 边界。

硬约束：

- 授权 false。**P0 授权已消耗，无论你发现什么都不许重跑该 phase**；不许跑 decoder、
  不许跑 G1/G2、不许跑 prepare 脚本、不许读 CAL/VAL/parquet 行。
- **P0 输出根是证据，只读**：`workspace/` 下不许改/删/移/改名/覆盖/规范化/算 hash，
  你只能自建 pytest `--basetemp`。
- 不许让 `workspace/v72p2d5_g2/20260906_r1` 出现。
- 不许改 `cycle_state.yaml`、不许授权、不许接受、不许推广。
- 不许改任何 `.py`、既有 `.md`、OpenSpec。
- 不许 `git add/commit/push/reset/stash/checkout/clean/rebase/revert/add --renormalize`。
- **发现问题只报告，不修复。** 查不动的标 `NOT_VERIFIABLE` 并写明原因。
- 测试里 `test_T1_22_openspec_history_zero_mod` 因行尾问题失败属**已知不阻塞**
  （内容差异为 0）；**除它以外**任何失败都是发现。

产出：**只允许新建 1 个文件**
`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/P0_PRE_RESULT_REVIEW_R1.md`，
内容按任务包 §7。结论二选一：`P0_PRE_RESULT_REVIEW_PASS`（写明必须带进 G1 包的
限制条件，并声明这不是接受、不是 G1 授权、不是科研资格）或
`P0_PRE_RESULT_REVIEW_FAIL`（点名阻塞发现 + 主线需做的唯一决定）。

明确不主张的清单必须包含：无 FER、无泄漏、无密钥率、无资格、无方法裁决、
**不预测 G1 或 G2 的结果**。

最后在消息里汇报：结论、检查表简表、F1/F2/F3 各一两行的裁定、复算出的外推值、
pytest 原文行，以及——仅当仍成立时——

「P0 结果仅为记录，未接受；G1 未授权；next_gate 仍为 P0_PACKET_REVIEW。」

=====
