# Paste-ready prompt — D5-P0-PREEXECUTE-R1 independent Pre-EXECUTE review

Copy everything between the two `=====` lines into a FRESH session opened in
`D:/Code/HD-QKD_Polar_Comparison`. Do not reuse any session that wrote the P0
packet or executed an earlier D5 task packet — this review must be independent.

=====

你是本次的**独立只读评审**。你没有写这份 P0 执行包，也没有参与之前任何一次 D5
任务包的执行；不要采信任何既有结论，一切从源码重新核实。

任务包全文在：
`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_P0_PREEXECUTE_R1_REVIEW_PACKET.md`

先完整读完，再按 §2 → §9 执行。

被评审对象：
`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/P0_EXECUTION_PACKET.md`
（状态 `P0_PACKET_FROZEN / EXECUTE_NOT_AUTHORIZED`，HEAD `b27f31da`）

你要裁两件事：

1. **这份冻结包是否忠实于源码与既定计划**——P03 参数表逐行对照代码核实，
   不许拿包里自己的数字当自己的证据。任何科研输入上的 `DISAGREE` 都是阻塞发现。
2. **它留下的五个 open question（OQ-P0-1 .. OQ-P0-5）的答案**——逐条给
   `DECIDED`（写明决定、理由、以及执行时必须因此改变什么）或 `REVISE_REQUIRED`
   （写明缺什么、包里要改什么）。**这五条是你来裁的，不许再往下推。**

你的 PASS **不等于授权**。它只表示这份包够格被授权；真正翻
`p0_cost_execution_authorized` 的动作只有用户能做。

必须自己核的重点（不许略过）：

- 块宽、`f` 集合、`m1`/`m2` 前缀值是否确实等于 `ceil(n*CE*f/5)`、builder `k_min`、
  图种子、块种子、12 次调用的算法、decoder 配置、先验来源与 `LAMBDA_STAR`、
  输出根与四文件不可覆盖、外推公式与 `projection_blocked` 阈值、单次预算、
  指标命名。逐行给 `AGREE`/`DISAGREE`/`NOT_VERIFIABLE` 并附源码位置。
- **缺陷修复本身**：这个 change 存在的全部理由，就是以前每个 `f` 都用同一套完整
  矩阵解码。去代码里确认现在每个 `f` 确实用自己的 `H1_mother[:m1(f)]` /
  `H2_mother[:m2(f)]`，且切片发生在该 `f` 的任何解码调用之前、按构造顺序、无行
  重排。同时确认 L1→L2 顺序、L1 失败时 L2 仍尝试、oracle 仅诊断且从不决定判定。
- **授权链**：`is_phase_authorized` 是否唯一收口、`p0-cost` 是否映射到
  `p0_cost_execution_authorized`、CLI 在 false 时是否在任何构造/加载/解码/写入
  之前就 exit 3；并写明 `run_p0_cost_synthetic(authorized=True)` 在**不传任何参数**
  时到底绑定哪个 decoder、写到哪个根——这就是残余风险 `R-R1`，判断包里是否
  如实描述了它。

硬约束：

- 授权状态 false。不许运行 decoder；不许执行 P0/G1/G2。**唯一允许的 `--phase`
  调用**是 §5 那个有防护的拒绝性验证，且必须按它写的四步走（先确认两个正式根
  缺席且授权位为 false，再跑，跑完立刻重新 stat）。整个 §5 也可以直接跳过，标
  `NOT_ATTEMPTED`，跳过不算失败。
- **一旦 `workspace/v72p2d5_p0_cost/20260906_r1` 或 `.../v72p2d5_g2/20260906_r1`
  在任何时刻出现，立刻 STOP 并作为严重发现上报。**
- 不许运行 `v72p2d5_prepare_model_f_input.py`（授权已消耗，禁止重放）；不许
  `pandas.read_parquet` 或读 CAL/VAL/原始行；pyarrow 只读元数据可以。
- `workspace/` 下除了 §6 你自己新建的 pytest basetemp 之外，不许新建/删/移/改名/
  复制/写入。
- 不许改任何 `.py`、任何既有 `.md`、OpenSpec、decision-log、
  AGENT_PROJECT_MEMORY，**不许改 `cycle_state.yaml` 的任何值**——授权不是你的活。
- 不许 `git add/commit/push/reset/stash/checkout --/clean/rebase/revert`。
- 不许写 `RESULT_SUMMARY` / `OPERATOR_RETURN` / `run_01`。
- **发现问题只报告，不修复。** 查不动的项标 `NOT_VERIFIABLE` 并写明原因，不要猜，
  也不要悄悄换成更弱的检查。

产出：**只允许新建 1 个文件**
`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/P0_PRE_EXECUTE_REVIEW_R1.md`，
内容按任务包 §8（编号检查 + P03 逐行核实表 + 缺陷修复结论 + 授权链结论 +
拒绝验证结果或 NOT_ATTEMPTED + 编译与测试证据 + 前后 stat 快照 + 五条 OQ 裁决 +
执行了什么/没执行什么 + 结论块）。结论只能二选一：

- `PRE_EXECUTE_REVIEW_PASS`（五条 OQ 全部 `DECIDED`；并写明这不是授权，
  `p0_cost_execution_authorized` 仍为 false，只有用户能翻）
- `PRE_EXECUTE_REVIEW_FAIL`（点名阻塞发现 + 重审前必须做的那一组修改）

无论哪个结论，都要写出证据支持的最强论断，以及明确不主张的清单（不主张 FER、
泄漏、密钥率、资格、方法结论，也不预测 P0 会通过）。

最后在消息里（不是文件里）汇报：结论、检查表简表、五条 OQ 各一行的裁决、
pytest 原文行、所有 `DISAGREE` 行，以及——仅当它仍然成立时——这一句：

「P0 未授权、未执行；正式根仍不存在；next_gate 仍为 P0_PACKET_REVIEW。」

=====
