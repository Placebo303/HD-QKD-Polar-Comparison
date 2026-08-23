# Spec Delta: formal-nonbinary-ldpc-v33-rate-aligned-empirical-channel-de-diagnostic

> **Status: DRAFT_PENDING_FREEZE_REVIEW** — SHALL 条款候选；判敛公式细节于
> freeze review 逐字定稿。

## Scope

ensemble/channel 层 DE diagnostic（V26 posterior-population full-vector MC-DE）：
在 V25 empirical joint P(A,B)（仅 train N_ab）、F03/A02 分配、V31 实际层率下，
判定三源两层 DE 是否全部收敛。非 fixed-packet / 非 QC matrix / 非 finite graph；
无码构造/decoder/FER/性能预测。DE 执行需冻结 + 显式授权。

## Definitions

### Binding Registry R1–R7（canonical——唯一规范表）

本表为全仓库唯一规范绑定表；proposal/design/tasks 只引用 SHALL-BIND1，
不得各自维护缩略副本或重新定义编号。

| # | 绑定 | 完整路径 / 精确 key | 用途与边界 |
|---|---|---|---|
| R1 | V25 train counts | `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz`；仅用三源键（见下） | DE channel construction 唯一数据源 |
| R2 | V25 summary | `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_summary.json`：raw_ser `0.239779296875` / `0.2544695292735815` / `0.2557409550754458`、pm1_mass | raw_ser 恒等校验 |
| R3 | V25 split manifest | `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/split_manifest.json` | train/holdout 边界声明 |
| R4 | V31 manifest | `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_20260820/run_01/RUN_MANIFEST.json`：`configs["1024"].sources[].{H.L1,H.L2,m1=16,m2,m_total,leak_total_bits∈{1064,1094,1104},f_total}` | 层率与分配恒等校验 |
| R5 | V31 matrix audits | `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_20260820/run_01/matrix_audits.json`：packet_id `m1_16_n1024_n1024\|QC-cyclic-projective`、L1 shape [16,1024] | **仅 allocation/packet identity 核对**；不是 V33 finite matrix、不是 QC packet、不是任何 DE 输入 |
| R6 | V31 registry | `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_20260820/run_01/m1_registry.json registered_calls`（allocation_id=`m1_16_n1024` 过滤） | **只允许读取 source ID、allocation ID、m1、m2、rate、H identity**；禁止继承 V31 seeds、f、n_samples、max_iter、tol、streak 或其他任何 DE 参数 |
| R7 | V26 DE kernel/code identity + historical gate | V26 run_02 工件（gate.json `pass_target_f13`、best_passing_f A01=1.6/A02=1.3）+ sampler/kernel 代码身份 | 只读方法身份对照，不可外推至 V31 层率 |

### Source ID ↔ NPZ key ↔ m2（逐项绑定；key 为盘上逐字字面量）

| label | source ID | NPZ key（R1 内） | m2 |
|---|---|---|---|
| 1M | `type2_1M_20260121_184040` | `type2_1M_20260121_184040_N_ab_train_N_ab_train` | 184 |
| 1p5M | `type2_1p5M_20260121_183806` | `type2_1p5M_20260121_183806_N_ab_train_N_ab_train` | 190 |
| 2M | `type2_2M_20260121_183657` | `type2_2M_20260121_183657_N_ab_train_N_ab_train` | 192 |

简称 1M/1p5M/2M 仅为标签。validation/holdout 禁入。

### 其他冻结定义

- Factorization：F03_natural_MSB_to_LSB_GF32_plus_GF32；A02=F03；L1 then L2；
  q=32/width=5；L2=true-predecessor-conditioned。
- GF(32) identity：GF2mField.create(32)；primitive polynomial = 37（0b100101）；
  polynomial basis；symbol encoding / field_id =
  `c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf`（与 V31
  manifest 一致）。
- Sampler semantics：每次抽取自 flatten 后的 P_s(A,B)；三源独立、永不合并；
  L1 使用 P(U1|B)；L2 使用同一真实 A 的真实 U1 构造 P(U2|B,U1)；后验按真实
  layer symbol 做 GF-XOR centering（真值位于 index 0）；PCG64 固定 draw order；
  非法条件分母直接 INCONCLUSIVE(reason=inconclusive_input_binding)，不进入任何
  one-hot fallback。
- Actual rate：n=1024；m1=16；m2 按上表逐项绑定；R_i=1−m_i/1024；
  ρ_i=make_rho(R_i, lambda={2:1})；禁止 f=1.3 反推。
- 调用矩阵（候选）：3 sources × 2 layers × seeds 33101–33105 = 30 calls；
  n_samples=2000；max_iter=200；entropy_tol=0.01 bits/symbol；streak=20；
  RNG=PCG64。
- **H_t（机械判敛量）** = mean_bits_entropy(c2v_t, q)
  = (1/M)·Σ_{j=1..M} H(p_{t,j})，其中 **M = c2v_t.shape[0] = n_samples = 2000**
  （MC-DE population rows）。**M 不是块分配长 n=1024。**
- Run root = `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v33_rate_aligned_empirical_de/run_01/`（完整路径，无省略号）。
- Terminal 恰三类：PASS / FAIL(`rate_allocation_or_ensemble_fail`) /
  INCONCLUSIVE(`de_diagnostic_inconclusive`，reason codes 含
  `inconclusive_input_binding`)；聚合优先级 INCONCLUSIVE > FAIL > PASS。
- Review IDs 唯一命名：FR1 freeze review / IR1 implementation candidate
  review / ER1 post-execution read-only evidence review。

## Requirements (SHALL)

### Bindings（canonical）
- **SHALL-BIND1**：全部输入 SHALL 经唯一 canonical Binding Registry R1–R7 引用；
  该表（含完整路径/精确 key/用途边界）为本变更唯一规范定义。proposal/design/tasks
  SHALL NOT 维护各自的缩略 registry 或重复表；实现与后续文档 SHALL 引用本表而
  非重新定义。冲突编号或以简称推断完整路径/source ID SHALL 被禁止。
- **SHALL-IN1**：DE channel construction SHALL 仅使用 R1 中三源 train 计数矩阵
  （逐字 key 见 Source ID 绑定表）；validation/holdout SHALL NOT 进入任何构造路径。
- **SHALL-R5B**：R5 SHALL 仅用于 allocation/packet identity 核对；SHALL NOT 作为
  V33 finite matrix、QC packet 或任何 DE 输入。
- **SHALL-R6B**：R6 读取 SHALL 仅限 source ID、allocation ID、m1、m2、rate、
  H identity 字段；V31 的 seeds/f/n_samples/max_iter/tol/streak 或其他 DE 参数
  SHALL NOT 被继承进本变更的任何计算或配置。

### Identity & Rates
- **SHALL-ID1**：DE SHALL 标识为 posterior-population full-vector MC-DE；
  `not_fixed_packet_de=true` SHALL 出现于输出；fixed-packet/QC-matrix/
  finite-graph 结论 SHALL NOT 出现。
- **SHALL-FAC1**：层映射 SHALL 为 F03(A02)、L1→L2、q=32/width=5、L2 true-
  predecessor-conditioned。
- **SHALL-RATE1**：m_i SHALL 按 Source ID ↔ m2 绑定表逐项取值；R_i 与 ρ_i SHALL
  分别按 R_i=1−m_i/1024 与 make_rho(R_i, lambda={2:1}) 构造；f=1.3 历史值
  SHALL NOT 参与任何 rate 推导或校验。
- **SHALL-FIELD1**：实现 SHALL 使用 GF2mField.create(32)、primitive polynomial
  = 37（0b100101）、polynomial basis，且 symbol encoding/field_id 与 V31 manifest
  一致；任何其他域表示 SHALL 触发 binding STOP。

### Convergence (mechanical)
- **SHALL-CONV1**：判敛 SHALL 仅采用机械判据
  **H_t = mean_bits_entropy(c2v_t, q) = (1/M)·Σ_j H(p_{t,j})，
  M = c2v_t.shape[0] = n_samples = 2000（population rows，非 n=1024）**：
  call PASS 当且仅当全程概率有效且连续 streak=20 次迭代满足
  H_t < entropy_tol(0.01 bits/symbol)；有效运行至 max_iter=200 未满足
  （含有限振荡）⇒ FAIL。"互信息增量"、"轨迹稳定"措辞与"按 n=1024 求均值"
  解释 SHALL NOT 出现于任何 v33 规格或输出。

### Stage-0 Failure（frozen）
- **SHALL-SF1**：stage-0 任一绑定校验失败时，系统 SHALL 保持 zero DE calls、
  SHALL NOT 进入 call/cell 聚合、overall SHALL 为 INCONCLUSIVE，reason SHALL 取
  固定枚举之一：missing_input / binding_drift / field_mismatch /
  allocation_mismatch / malformed_input；SHALL NOT 创建伪造的 30-call 记录。

### Call Matrix & Exact-Once
- **SHALL-MC1**：调用矩阵 SHALL 采用候选冻结值（seeds 33101–33105/n_samples=
  2000/max_iter=200/entropy_tol=0.01/streak=20/RNG=PCG64），ACCEPT_FREEZE 前
  为主控可修订候选，之后不可变。
- **SHALL-X1**：30 calls SHALL 按固定顺序 exact-once 执行；每 call 持久化后方
  进入下一 call；重复 call 或缺失序号 ⇒ evidence inconsistent STOP。
- **SHALL-X2**：official run lifecycle——execute 入口发现 run_01 已存在 ⇒
  collision STOP；否则创建 run_01 → 写 pre-execution manifest → 按固定顺序执行
  30 calls。同一次 execute 内后续阶段 SHALL NOT 重新触发 root collision。

### Terminals & Aggregation
- **SHALL-T1**：call 三态定义 SHALL 按 PASS(有效+streak)/FAIL(max_iter 未达
  streak 含有限振荡)/INCONCLUSIVE(NaN/Inf/负概率/归一化/异常/资源中断) 机械判定。
- **SHALL-ZD1**：正概率抽样点命中非法 L2 conditional denominator 时，该 call
  SHALL 终止为 INCONCLUSIVE(reason=inconclusive_input_binding)；one-hot fallback
  或静默跳过 SHALL 被实现禁止并有测试覆盖。
- **SHALL-AGG1**：cell=(source,layer) SHALL 由 5 seeds 聚合（任一 INCONCLUSIVE ⇒
  cell INCONCLUSIVE；全 PASS ⇒ cell PASS；否则 FAIL）；overall SHALL 由 cells
  按优先级 INCONCLUSIVE > FAIL > PASS 机械映射；未覆盖组合 ⇒ inconclusive with
  reasons；禁止事后发明终态。

### Claim Boundary
- **SHALL-CB1**：即使 overall PASS，本变更结论 SHALL 仅限 "exact-rate
  empirical-P ensemble DE 通过"；不得声称 finite code/decoder/FER/QKD
  qualification/promotion 可行。

### Write Roots & Path Guard
- **SHALL-PATH1**：存在最小显式路径守卫——拒绝 repo root、results root、
  diagnostics root（`…/nonbinary_diagnostics`）、`openspec/changes/archive`、
  五个 protected old roots（V31 run_01、closeout_v2 run_01/run_02、V32 bridge
  run_01、opaudit v1 run_01）及其任何子路径、workspace 根本身、sibling checkout；
  production execute 仅允许完整 official run_01；fake/test 仅允许 fresh
  workspace child root。
- **SHALL-WR1**：production execute SHALL 只写 official run_01；fake/test-only
  SHALL 只写 fresh workspace root；verify 子命令默认只读；ER1 在 official root
  内仅允许新增 readonly_review.json 一个文件。

### Execution Authorization（状态机）
- **SHALL-AU1**：在 IR1 review 与主控 implementation ACCEPT 之前，变更状态 SHALL
  为 `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`；真实 DE（含 smoke）
  SHALL NOT 执行；测试 SHALL 仅使用显式 fake DE runner。
- **SHALL-AU2**：IR1 通过且主控 implementation ACCEPT 之后，状态 SHALL 变为
  `IMPLEMENTATION_ACCEPTED / EXECUTE_NOT_AUTHORIZED`；真实 DE 仍 SHALL NOT 执行。
- **SHALL-AU3**：仅当主控另行授予 `EXECUTE_AUTH` 后，真实 DE 方可按冻结调用矩阵
  运行恰一次。

### Handoff
- **SHALL-H1**：closeout 交付 candidate_only=true / main_acceptance_pending=true /
  qualification=false / promotion=false；最终声明逐字：
  「candidate_only，等待 Codex 主控 ACCEPT/REJECT；未运行 DE，未运行 decoder，未启动 successor。」

## Acceptance Mapping

| AC 组 | SHALL | 验证 |
|---|---|---|
| 绑定 registry（canonical） | BIND1, IN1, R5B, R6B | 本表唯一性检查 + T1 五类 reason fixture |
| stage-0 failure 冻结语义 | SF1 | T1 五类 reason 全过 + 无伪造 call 记录断言 |
| 恒等/域身份/rate | ID1, FAC1, RATE1, FIELD1 | stage-0 + T0 断言 |
| 机械判敛（M≠n） | CONV1 | **T0 M≠n toy** + T1 措辞禁令 |
| sampler 语义 | SAMP1 | T2 三通道 fixture + centering 断言 |
| 调用矩阵/exact-once/lifecycle | MC1, X1, X2 | T2 fake 全流程 + 顺序/collision 断言 |
| 零分母 | ZD1 | T2 NaN/denominator fixture |
| 终态聚合 | T1, AGG1 | T2 三通道路由 + 重算 |
| 写根/路径守卫 | PATH1, WR1 | T1 守卫测试全套 |
| 授权状态机 | AU1–AU3 | 守卫测试 + FR1/IR1/ER1 报告链 |
| 输出/handoff | X2, H1 | 目录清单 + 标志断言 |
