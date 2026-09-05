# D5 设计 R1：F 模型两层 prior 合同、行数表、嵌套 mother 与 synthetic 门控

状态：`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`。只设计不实现；所有公式、阈值、种子、门禁在本轮冻结，
apply 阶段不得回写放宽。`N=1024 symbols/block`，`q=32`，`GF(32)` poly `37`（`0b100101`），
映射 `symbol = low + 32*high`（`U1=high/MSB`，`U2=low/LSB`，`bit0=LSB`），无 Gray、无置换。

`M_max=1000 is a D5 synthetic construction cap, not a production sufficiency claim.`
不代表生产充分 / 传播税覆盖 / worst-fold 或 finite-size margin 充分，不授权 `n=1024` 真实。

## 1. F 模型到两层 prior 的数学合同（无歧义冻结）

记 `A in 0..1023`，`B in 0..1023`，`A = 32*U1 + U2`，`U1,U2 in 0..31`。
F 模型输出全符号条件表 `P_F`，冻结合同：

- `counts.shape=(Alice,Bob)`，`P_F.shape=(Alice,Bob)`，`axis0=Alice`，`axis1=Bob`。
- 对 every `b` 有 `sum_a P_F[a,b]=1`，即 `assert_allclose(P_F.sum(axis=0),1.0)`。
- D4R2 冻结平滑 `lambda*=137.3823795883264`（单系数 Laplace/收缩，作用于 counts 列方向，见 §1.5）。

```text
P_reshaped = P_F.reshape(32,32,1024)   # (U1,U2,Bob); Alice a = U1*32+U2 行主序
P1(U1|B)    = P_reshaped.sum(axis=1)   # 对 U2 轴求和，形状 (32,1024)=(U1,Bob)
assert_allclose(P1.sum(axis=0),1.0)    # 对 every b 沿 U1 求和为 1
P2[u1,b,u2] = P_reshaped[u1,u2,b] / P1[u1,b]   # 固定 (u1,b) 后沿 u2 和为 1
chain check : CE_joint == CE_L1 + CE_L2_oracle  (容差 <1e-10, float64, log2)
```

禁止“axis1 列归一”歧义表述；一律用 `axis0=Alice 求和归一` 表述。

### 1.1 求和轴（与 V54 reshape 同口径）

- canonical counts `counts[a,b]=count(Alice=a,Bob=b)`，`axis0=Alice/axis1=Bob`
  （`v72p2d3_gf32_contrast.build_canonical_counts`，转置输入恒拒绝）。
- Alice 索引 `a = U1*32 + U2`（行主序 `reshape(32,32,1024)=(U1,U2,Bob)`，
  与 `v54.get_l1_prior_p_u1_given_b` 第 413 行 `reshape` 语义逐字一致）。
- `P1` = 对 `reshape` 的 `axis=1`（U2 轴）求和后沿 `axis=0`（U1 轴）归一；
  `P2` = 同一 `reshape` 下固定 `(U1,B)` 切片沿 U2 归一。
  任何转置/反轴实现必须被不对称手算分布反例捕获（spec S-PRIOR-02）。

### 1.2 归一化时机

1. counts → 加 `lambda*` 平滑 → 沿 `axis=0`（Alice 轴）归一得 `P_F(A|B)`；
2. `P_F` → 按 U2 求和 → 沿 `axis=0`（U1 轴）归一得 `P1(U1|B)`（形状 `(32,1024)`，`P1.sum(axis=0)==1`）；
3. `P2[u1,b,u2] = P_reshaped[u1,u2,b] / P1[u1,b]`，固定 `(u1,b)` 沿 `u2` 归一（逻辑形状 `(32,1024,32)=(U1,B,U2)`）。
- 禁止先取 log 再归一；禁止在未归一表上做 `q@P`。

### 1.3 概率域 vs log 域

- 存储与传递一律概率域；decoder 入口一律概率域 `(N,32)`（`decode_row_layered_fftqspa`
  内部自行转 log-belief）。
- CE 与审计一律 `log2`（`CE=-mean(log2 P)`）；decoder 内部自然 log 转换显式且不进入本审计口径。
- `P1` 表形状 `(32,1024)`（U1xB），decoder prior 形状 `(N,32)`（每行一 symbol 的 32 元分布）。

### 1.4 数值下溢

- 双 floor 并存，语义分离冻结：审计/CE 用 `PROB_FLOOR=1e-300`（先正常归一再 `max(P,1e-300)` 后取 log，只保护 log）；
  decoder 通路用 `1e-15`（V54/v35 历史路径：`maximum(...,1e-15)` 后重归一，保护 FFT-QSPA 迭代）。
- 两 floor 均不得改变归一性（floor 后必须重归一）；`P1(U1|B)=0` 的 `(U1,B)` 切片回退均匀 `1/32`
  （V54 第 419–420 行语义），不得删样本。

### 1.5 L2 oracle prior vs 实际条件 prior（关键区分）

- `CE_L2_oracle`（预算诊断用）：`P2(U2 | U1_true, B)`，用真实 `U1` 查表
  （`v35.get_conditional_posterior_l2(counts,bob,u1)` 语义：`rows=arr[u*32+0..31, b]` 沿 Alice 行归一）。
  仅作分层预算诊断，非生产性能。
- 生产 L2 prior：`prior_l2 = q @ P`，其中 `q=softmax(L1 final_beliefs)`（`(N,32)`），
  `P=P(U2|U1,B)` 为 `(32,32,1024)->(N,32,32)` 切片（`v54.get_l1_app_prior_l2` 语义）。
  L1 失败仍恒进 L2（V54/D3 历史语义：L2 恒用 `q`，无门控；L2 base-ok 短路 joint/total）。
- D4R2 的 `CE_L2_oracle=3.347605` 是 oracle 上界口径；生产 `q@P` 只会更差，不得把 oracle CE
  当作生产可达性能引用。

### 1.6 decoder 输入形状与接口映射

| D5 prior | 形状 | 现有接口（精确复用） |
|---|---|---|
| `P1(U1\|B)` 查表 → L1 prior | `(N,32)` | `v54.get_l1_prior_p_u1_given_b(counts(1024,1024), bob(N,))`（D3 包装：`get_l1_prior_production`） |
| `q=softmax(L1 beliefs)` | `(N,32)` | `v54.softmax_beliefs`（D3 包装：`softmax_beliefs_history`） |
| `prior_l2=q@P` | `(N,32)` | `v54.get_l1_app_prior_l2(counts, bob, q)`（D3 包装：`build_l2_prior_from_l1`；签名禁 Alice/oracle） |
| oracle L2（仅诊断） | `(N,32)` | `v35.get_conditional_posterior_l2(counts, bob, u1_true)` |
| decoder 调用 | `H(m,n) uint8, priors(N,32), syndromes(m,)` | `v35.decode_row_layered_fftqspa(..., max_iter=90, damping_alpha=1.0, warm_beliefs=None, field=GF(32))` → `DecoderResult(x_hat, syndrome_ok, iterations 0..max, final_beliefs)` |

**对齐结论：对齐，需且仅需一个 frozen adapter delta**（不实现，只声明）：
V54 现有 prior 路径用原始 counts + `1e-15` floor，无 Laplace `lambda*` 平滑；
D5 F 模型要求先对 counts 施加 `lambda*=137.3823795883264` 平滑再沿 `axis=0` 归一。
Delta = 在 `counts → P_F` 这一步插入 frozen `lambda*` 平滑（`v72p2d3.build_stage1_P/build_stage2_P`
的 `_smooth_counts` 语义），下游 `reshape` 求和 / `q@P` / decoder 调用逐字复用 V54，
不得改动历史 kernel。若未来发现接口形状不一致，状态为 `BLOCKED` 并报 main thread，
不得猜测绕过。

## 2. 码率/行数表（GF32 每行 5 bit）

冻结公式：`required_bits(layer) = N * CE_layer * f`，`rows_required(layer) = ceil(required_bits / 5)`。
**分层独立 ceil 为权威口径**；`m_total = m1 + m2`（分层独立披露）。
joint-ceil（`ceil(N*CE_joint*f/5)`）仅作对照，两者差 0–1 行为 ceil 取整伪影，计划中显式记录而非调平。

### 2.1 n=1024 行数表（D4R2 F 均值：L1 3.814742 / L2 3.347605 / joint 7.162347）

| f | L1 bits | m1 | L2 bits | m2 | m1+m2 | joint bits | joint-ceil | 对照旧预算 |
|---|---|---|---|---|---|---|---|---|
| 1.0 | 3906.30 | **782** | 3427.95 | **686** | **1468** | 7334.24 | 1467 | L1 16 / L2 200 / Tot 216 |
| 1.05 | 4101.61 | **821** | 3599.34 | **720** | **1541** | 7700.96 | 1541 | 同上 |
| 1.1 | 4296.93 | **860** | 3770.74 | **755** | **1615** | 8067.67 | 1614* | 同上 |
| 1.2 | 4687.55 | **938** | 4113.54 | **823** | **1761** | 8801.09 | 1761 | 同上 |
| (参1.3禁入) | 5078.18 | 1016 | 4456.23 | 892 | 1908 | 9534.52 | 1907* | 同上（D4R2：1907 vs 216, margin −1691；仅参照） |

`*` joint-ceil 与 m1+m2 差 1 行是 ceil 伪影（`f=1.1/1.3`），权威口径取 `m1+m2`。
worst joint `7.178766` → `7351.06` bits → `1471` 行（均值 1467 + 4 行）；
std `0.0158` ≈ `16.2` bits ≈ 4 行；range `0.0423` ≈ `43.3` bits ≈ 9 行。
`M_max=1000` 每层覆盖 `f≤1.2`（L1 938 ≤ 1000 margin 62 行；L2 823 ≤ 1000 margin 177 行），
覆盖 `f=1.0`（margin 218/314 行）。
`M_max=1000 is a D5 synthetic construction cap, not a production sufficiency claim.`
`f=1.3` L1 需 1016 行超 cap，本轮 synthetic 禁止 `f=1.3`。

### 2.2 为何旧 216 行在 f=1.0 不足（bit 对比，不重复 D4 证明）

- L1：需要 `3906.30` bits，旧给 `16*5=80` bits → 缺 `3826.30` bits（766 行，48.9 倍不足）。
- L2：需要 `3427.95` bits，旧给 `200*5=1000` bits → 缺 `2427.95` bits（486 行，3.43 倍不足）。
- Total：需要 `7334.24` bits，旧给 `1080` bits（`1.0546875` bit/symbol）→ 缺 `6254.24` bits（1251 行，6.79 倍不足）。
- 结论只记 `MODEL_BUDGET_MISMATCH`（D4R2 route C）；禁止写成信息论极限/GF32 失败/LDPC 不可能；
  L1 不足禁止只加 L2。

### 2.3 “约 700–1000 行”目标的构成（冻结解释）

- 本计划把任务书的“约 700–1000 行”冻结为**每层独立 mother 的 `M_max=1000` 行级 synthetic 构造 cap**：
  L1 mother `1000×1024`（`f=1.0` 披露前 782 行，`f=1.2` 披露前 938 行），
  L2 mother `1000×1024`（`f=1.0` 披露前 686 行，`f=1.2` 披露前 823 行）。
  `M_max=1000 is a D5 synthetic construction cap, not a production sufficiency claim.`
- 若按“统一 total 700–1000 行”理解：`700` 行 = `3500` bits = `3.42` bit/symbol，
  `1000` 行 = `5000` bits = `4.88` bit/symbol，均 `< 7.162347` 联合需求，
  在 `f=1.0` 仍失配 467–767 行——该解读下直接维持 route C，不进入真实实验。
  两种解读的判定已在本节冻结，实现阶段不得重新解释。
- L1/L2 是**独立 mother**（不同 GF32 字母表：U1 vs U2；V31 packet 本就是 L1 + per-source L2 独立矩阵），
  不是统一 mother 切片。增量披露顺序冻结为 **L1 先收敛再开 L2**（V54/D3 历史语义：
  L1 APP `q` 恒喂 L2，L2 内 base→joint→total 短路；联合同时披露变体明确 deferred，不在 D5）。
- Laziest alternative（一行）：统一 `1761×1024` mother 同时约束 U1/U2——否决，
  因为 L1/L2 活在不同 GF32 字母表上且历史 packet 全是分层独立矩阵，统一 mother 无复用基础。

## 3. 嵌套 mother 设计（只设计不实现）

### 3.1 选型：V31 `build_layer` 为扩展基线

`nonbinary_v31.build_layer(m, n=1024, *, family, field=GF(32), require_full_rank=True)`
（支撑：`build_supports` + `select_projective_ratio_v31` + `projective_column_audit`；family 必须显式传参，不依赖默认）。
选中理由（一行）：它是仓库唯一同时满足“任意 m（含 1000）、n=1024 已验证、确定性可重放、
`occupancy≤31` 硬门、`projective_safe + full_row_rank` 双审计”的 GF32 构造器，
且列重恒为 2 使 700–1000 行仍极稀疏。

- 稀疏性：列重恒 2；行重均值 `2n/M`：`M=1000` 时 ≈2.05，`M=782` 时 ≈2.62——天然适配大 m。
- rank 保证：audit 含 `rank / full_row_rank / projective_safe`；`construction_ok` 要求三者全过。
- 可扩展性：`build_supports(m,n)` 对任意 `m≥2` 枚举候选对至 n 列，
  `m=1000` 时候选对 `499500 ≫ 1024`，occupancy 自然 ≤2，无容量墙。
- 嵌套注意：单 mother 一次性按 `M_max=1000` 构建后取行前缀 `H[:k]` 是 reinterpretation，
  前缀秩未经构造器保证，必须经 §4 M0-STRUCTURE 逐个验证（见 §4；禁止假设自然行序合格）。

### 3.2 备选与否决（冻结）

- 备选：V38 `construct_lane_c_prototype`（SC-inspired banded，`L=8,w=2,dv=2`，4-cycle 回避）。
  仅当 M0 结论为 `V31_PREFIX_FAMILY_UNSUITABLE` 且根因为图结构（非 prior/decoder）时，才允许另立 change 评估；
  D5 内不并行推进。理由：其 `SOURCE_CHECKS`/allocations 为小 m 冻结值，700+ 需重设计分配向量，
  且 rank 审计弱于 V31。
- 否决（D5 内不候选）：V36 `build_v36_incremental_matrix`（行重 10–14，700 行下平均列重 ≈8.2，
  对 FFT-QSPA 过密）；V35 `build_v35_incremental_mother_matrix`（硬编码 192→224，不支持任意 m）；
  `nonbinary_codebook` 家族（`32×64` 级小母矩阵，非 1024 列 regime）；
  V28 `_build_pair_matrix`（小 m 验证过，700+ 未验证，留作 H1 小矩阵参考）；
  V54 `construct_h_inc`（Δ8–32 小增量语义已由 D3 前缀 `(184,192,200)` 覆盖，大 m 未审计）。

### 3.3 V72P0 边界（结构参考，非复用）

V72P0 mother（binary `9036×10240` IRA，`H_p` dual-diagonal `det=1 ⇒ rank=9036`，
`nnz≈5.5/行`，`prefix_nested`，`C1–C6` 全 PASS）只借三条结构模式：
一次性构建、行前缀嵌套披露、每前缀秩证明。**禁止直接假设适用于 GF32**，四点边界冻结：
(a) 域不同（GF2 vs GF32，FFT-QSPA 卷积代价不同）；
(b) 维度不同（10240-bit vs 1024-symbol，行重 regime 不同）；
(c) 码率 regime 不同（`f=1.3 NOT_MEASURED` vs F 联合 `7.16` bit/symbol 实测需求）；
(d) decoder 不同（binary BP vs layered FFT-QSPA）。D5 的稀疏/rank 结论需独立验证。

## 4. M0-STRUCTURE / prefix 门禁 / row ordering / 披露 API（冻结定义）

- 一句话定义：每层 GF32 mother 是一次性构建的单个 `M_max×1024` 矩阵（`M_max=1000`），
  披露是行前缀 `H[:k]`，`k` 取自冻结披露集合，对一切已披露 `k` 要求 GF(32) 满行秩，
  后增行只追加、不改动前缀行。
- 披露集合 `K` 冻结：L1 `{782,821,860,938}`，L2 `{686,720,755,823}`（§2.1）；`H[:k1]` 是 `H[:k2]`（`k1<k2`）的精确行前缀。
- 修正 V31 前缀假设：`build_layer(1000,1024)` 任意前缀视为 nested mother 是未验证假设。
  改为 M0-STRUCTURE 两阶段：只构建一次 `1000x1024` 候选 → 检查所有冻结 prefix → 全 PASS 才进 G0；
  full `(1000,1024)` PASS 但某 prefix FAIL 时，不允许换 seed 搜索、不允许每 `k` 独立矩阵冒充 nested，
  只允许一个预注册确定性 rank/coverage-aware row ordering 候选，一次完成冻结，后续 prefix 来自同一排序 mother；
  排序后仍 FAIL 则 `V31_PREFIX_FAMILY_UNSUITABLE` 停止返回 planner，不进 decoder。
  不要把换 family 写成唯一修复。

### 4.1 每个 prefix 必须报告并冻结的 13 项结构门禁

对 L1 每个 `k in {782,821,860,938}` 与 L2 每个 `k in {686,720,755,823}` 的 `H[:k]` 报告：

1. `rank==k`；2. `zero_rows==0`；3. `zero_columns==0`；4. 每列 active degree `min/median/max`；
5. `degree-1 count`；6. `degree-2 count`；7. `connected_component count`；
8. `largest_component fraction`；9. `isolated==0`；10. check `row-degree histogram`；
11. `4-cycle count`；12. `duplicate/projective-equivalent col count==0`；13. GF32 系数非零。

最低 PASS（五项全过才算该 prefix PASS）：
`zero_columns==0`，`isolated==0`，`largest_fraction==1.0`，`rank==k`，`duplicate==0`。
`degree-1` 只披露不发明阈值；若大量 `degree-1` 则 G1 前标注结构风险，不自动 FAIL。

### 4.2 行排序合同（row ordering，预注册一次）

- 输入完整 1000 行 mother → 输出一个行置换，不改行内容/系数。
- 优先级：新覆盖变量数 → rank 增量 → component 连接；tie-break 确定性。
- 不得查看 decoder 结果 / Alice block / synthetic exact；一次排序用于 L1/L2 各自所有 prefix。
- L1/L2 不同固定构造 seed 但算法相同。
- 若实现前评估排序过复杂，可把 prefix 实测作实现前独立 feasibility gate，但不能假设自然行序合格。

### 4.3 稀疏度目标与披露 API

- 稀疏度目标：V31 基线下列重恒 2；行重目标 `2–4`（均值 `2n/M_max≈2.05`，允许 `±1` 波动带）；
  零行/零列数为 0；`support occupancy ≤31`（构造器硬门）。
- 满秩验证方法（只定义步骤，不执行大矩阵验证）：
  `nonbinary_codebook.gf_rank(H[:k], GF2mField.create(32)) == k` 逐 `k in K` 断言
  （pinned 多项式基高斯消元）；tiny 规模（`m≤8,n≤16`）附手算可验示例；
  `M_max=1000` 全量验证是 `O(m²n)` 量级 field 运算，列为 apply 阶段实现任务并配预算，
  本轮不执行。
- 增量披露 API 形状（最小列表/指针，禁通用框架）：
  `m_max: int`（=1000）+ `prefix_rows: int`（=k）+ `extra_rows: list[int] | None`
  （默认 `None` = 前缀 `0..k-1`；非 None 时为显式行索引表，用于诊断重排实验，生产恒 None）。
  mother 存单个 `np.ndarray`，披露即视图 `H[:k]`；L1 披露先行，L1 syndrome-ok（或 90 轮耗尽）后再开 L2 前缀。

## 5. 三级 matched synthetic 门控（tiny / n=64 / n=256）+ P0 + 种子 + 计数

通用冻结：synthetic 生成必须 matched to F（由 `P_F` 采样或按 CE 标定噪声）；
**禁止用 AWGN/BSC/QSC 替代**；prior 一律用真 `P_F` 表（无估计误差，隔离 prior 错）；
Bob 边际用 CAL TRAIN 经验 `P(B)`（CAL-only，不碰 VAL）；`max_iter=90`，
`damping=1.0`，cold start（`warm_beliefs=None`），tag 不生成不计费。
命名统一 `exact_failure_fraction=1-exact_count/attempted_blocks`，可注 synthetic block error fraction，
不得称真实 FER 或外推真实。

### 5.1 冻结种子

- graph seed：L1 `2026090501`，L2 `2026090502`（L1/L2 不同固定构造 seed，row ordering 算法相同）。
- G0：`2026090510..2026090517`（8）。
- G1：`2026090600..2026090699`（100 blocks）。
- G2：`2026091000..2026091199`（200 blocks）。
- 若与 API 范围不兼容则改为兼容明确整数但实现前固定，运行后禁换 seed。禁止 seed search，失败按停止规则返回。

### 5.2 P0 COST-PREFLIGHT（冻结，不计入 G1）

- `n=64`，2 blocks，`f=1.0` 和 `1.2`，APP 与 oracle 都跑，记录 `wall/iterations/RSS`，不计入 G1。
- 基于 P0 外推 G1/G2 projected wall。
- 资源门：单 call timeout `120s`，G1 总 `≤900s`，G2 总 `≤3600s`，peak RSS `<2GiB`；
  G2 `projected>3600s` 则 `RESOURCE_PROJECTION_BLOCKED` 不启动；
  不降 block/rate 点绕过、不自动并行、不改 `max_iter=90`。

### 5.3 调用数（冻结计数）

- G1：APP-fed `100 blocks x 2 rates` + oracle 前 20 同 seed `x 2 rates` 仅诊断。
- G2：APP-fed `200 x 3 rates` + oracle 前 40 同 seed `x 3 rates` 仅诊断。
- oracle 均为同 seed 配对子集，仅诊断，不计入 PASS 判定。

### 5.4 oracle 与 APP 判据合同

删除 oracle-L2 exact>=APP-fed exact 硬门。改为同时报告：
`oracle_L2_exact / app_fed_exact / oracle_minus_app / oracle_syndrome_ok / app_syndrome_ok /`
`L1 exact / L1 syndrome_ok / L1 posterior NLL / q entropy mean/p95`。
解释：oracle 为诊断上界、APP-fed 为生产语义、有限 BP 可非单调、oracle<APP 不自动判错、
异常标 `ORACLE_APP_NONMONOTONIC_DIAGNOSTIC` 并查合同/seed 配对/syndrome 重算，
仅数学/输入不一致才 `BLOCKED`。G2 PASS 只用 APP-fed 端到端 exact。

| 级 | n | 目的 | 生成（matched） | prior | 披露行数 | 通过阈值 | 失败归因 |
|---|---|---|---|---|---|---|---|
| G0 tiny | ≤9（手算 2×2×2 或 `k=2/3,n=6/9` 穷举） | 数学正确性 | 穷举/手算联合分布；`P_F` 精确已知 | 真表 | tiny mother 2–4 行（`gf_rank` 全秩） | 边际/条件与暴力误差 `<1e-12`；链式 `<1e-10`；syndrome 重算一致；tree/tiny exhaustive 一致；无噪精确恢复 100% | 任一失败即 `BLOCKED`（数学错/图-field 错/decoder 错三分记录） |
| P0 | 64（2 blocks） | 成本预检 | `B∼P_CAL(B)`，`A∼P_F(·\|B)` | 真表 | f=1.0 `m1=49/m2=43`；f=1.2 `m1=59/m2=52` | 只记录 wall/iterations/RSS 并外推，不计入 G1 | 超门则 `RESOURCE_PROJECTION_BLOCKED` |
| G1 | 64 | 集成/scale 趋势（非杀门，无路线死亡权） | `B∼P_CAL(B)`，`A∼P_F(·\|B)`，100 blocks（§5.1 种子） | 真表 | §2 scaled：f=1.0 `m1=49/m2=43`；f=1.2 `m1=59/m2=52` | 单调 `exact_rate(1.2)>=exact_rate(1.0)`（即 `exact_failure_fraction(1.2)<=exact_failure_fraction(1.0)`）；零 crash/非有限；结构趋势检查 | crash/非有限→实现错；单调反转→图/scale 错并进诊断；不杀路线 |
| G2 | 256 | 性能趋势 + **唯一分级实验**（见 §6） | 同上，200 blocks（§5.1 种子） | 真表 | f∈{1.0,1.1,1.2}：`m1={196,215,235}`，`m2={172,189,206}` | §6 四态 | 同 §6 分支 |

- G0/G1 失败判据只做归因，不直接杀路线；
  G1 的 prior 错项恒 excluded（真 prior 构造），若 G1 fail 而 G0 pass → 图/scale 错。
- n=1024 真实执行前置条件（冻结）：G0+G1+G2 全过 + Pre-EXECUTE review（`HEAD==origin==实现SHA`、
  `ACCEPTED_PLAN_SHA` 重推导、`run_01` 不存在、预算与授权一致、`py_compile`+关键测试 PASS）。
  无论 G2 结果均不自动进 `n=1024`。

## 6. 最小分级实验（四态，唯一分级实验 = G2）

- 实验：`n=256` matched synthetic（`B∼P_CAL(B)`，`A∼P_F(·|B)`，`lambda*` 真值表），真 prior，
  V31 按 `n=256` 独立构建（行数与 §5 表一致：披露 §5 的 `m1/m2` 前缀；mother 行数实现冻结值覆盖 `f=1.2` 上界 235/206），
  `f∈{1.0,1.1,1.2}` 三点扫描，200 blocks，冻结种子（§5.1），`max90/damping1.0/cold`，L1-then-L2。
  （列数缩放依据：`rows=ceil(n*CE*f/5)` 同公式，`n=256` 行数见 §5 表。）
- 四态（PASS 只用 APP-fed 端到端 exact；oracle 仅诊断）：
  `>=90%@1.2` 且单调 `exact_rate(1.2)>=exact_rate(1.1)>=exact_rate(1.0)` → `G2_SYNTHETIC_QUALIFIED`
  （允许起草 `n=1024` synthetic 计划，不授权执行）；
  `50-90%` → `G2_INCONCLUSIVE`（保留路线，停止本轮，仅按预注册诊断判断图/APP 传播税/迭代不足，不自动调参）；
  `<50%` → `G2_CURRENT_CONFIGURATION_FAILED`（只否定当前 F prior+mother+decoder+预算组合）；
  crash/非有限/数学不一致 → `IMPLEMENTATION_OR_NUMERICAL_BLOCKED`。
- 单调按预注册 raw inequality 判定；1–2 block 反转报告 Wilson 区间与 raw counts，仍按 raw inequality 决定 qualified。
- 禁止多实验铺开：本节是 D5 唯一的分级实验；G0/G1 是正确性/集成门，无杀权。
- G2 不否定 GF32；无论结果不自动进 `n=1024`。

## 7. 风险与 open questions（冻结记录，实现不得自行消解）

- R1（科学）：生产 `q@P` 相对 oracle 有 L1 误差传播税，D5 行数表基于 oracle CE，
  真实所需行数只会更多；G1/G2 用真 prior + oracle 对照显式度量该税（诊断口径，非硬门）。
- R2（工程）：700–1000 行 FFT-QSPA 运行时未实测（每轮每 check `q=32` FWHT 卷积，
  `1000×1024` 稀疏图 ×90 轮）；P0 在 `n=64/2 blocks` 级先暴露趋势并外推，`n=1024` 预算另批。
- R3（构造）：V31 前缀秩在 `k in K` 需逐个验证；M0 FAIL 后只允许一次预注册 row ordering，不换 seed 搜索，
  不以每 `k` 独立矩阵冒充 nested；仍 FAIL 则 `V31_PREFIX_FAMILY_UNSUITABLE` 返回 planner。
- R4（语义）：`lambda*` 是 D4R2 outer-mean 单值；G2 synthetic 真值表直接采用它，
  不重做 inner 选择（synthetic 无估计问题）；n=1024 真实阶段的 λ 重拟合程序沿用 D4 口径，另批授权。
- OQ1（R1 已决策）：per-layer `M_max=1000` 接受但限定为 synthetic 构造 cap（见 §2.3），不代表生产充分。
- OQ2（R1 已决策）：90% 不作路线死亡线，改为 §6 四态；删除死亡线与 backlog 唯一后继表述。
