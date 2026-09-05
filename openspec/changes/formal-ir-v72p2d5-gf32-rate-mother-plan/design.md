# D5 设计：F 模型两层 prior 合同、行数表、嵌套 mother 与 synthetic 门控

状态：`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`。只设计不实现；所有公式与阈值在本轮冻结，
apply 阶段不得回写放宽。`N=1024 symbols/block`，`q=32`，`GF(32)` poly `37`（`0b100101`），
映射 `symbol = low + 32*high`（`U1=high/MSB`，`U2=low/LSB`，`bit0=LSB`），无 Gray、无置换。

## 1. F 模型到两层 prior 的数学合同（无歧义冻结）

记 `A ∈ 0..1023`，`B ∈ 0..1023`，`A = 32*U1 + U2`，`U1,U2 ∈ 0..31`。
F 模型输出全符号条件表 `P_F(A|B)`，形状 `(1024,1024)`，列归一（`axis1=Bob` 列和为 1），
D4R2 冻结平滑 `lambda*=137.3823795883264`（单系数 Laplace/收缩，作用于 counts 列方向，见 §1.5）。

```text
P1(U1|B)    = Σ_{u2=0..31} P_F(32*U1 + u2 | B)          # 求和轴 = U2（Alice 符号的低 5 bit）
P2(U2|U1,B) = P_F(32*U1 + U2 | B) / P1(U1|B)            # 逐 (U1,B) 行归一
chain check : CE_joint == CE_L1 + CE_L2_oracle  (容差 <1e-10, float64, log2)
```

### 1.1 求和轴（与 V54 reshape 同口径）

- canonical counts `counts[a,b]=count(Alice=a,Bob=b)`，`axis0=Alice/axis1=Bob`
 （`v72p2d3_gf32_contrast.build_canonical_counts`，转置输入恒拒绝）。
- Alice 索引 `a = U1*32 + U2`（行主序 `reshape(32,32,1024)=(U1,U2,Bob)`，
  与 `v54.get_l1_prior_p_u1_given_b` 第 413 行 `reshape` 语义逐字一致）。
- `P1` = 对 `reshape` 的 `axis=1`（U2 轴）求和后列归一；
  `P2` = 同一 `reshape` 下固定 `(U1,B)` 切片的行归一。
  任何转置/反轴实现必须被不对称手算分布反例捕获（spec S-PRIOR-02）。

### 1.2 归一化时机

1. counts → 加 `lambda*` 平滑 → 列归一得 `P_F(A|B)`；
2. `P_F` → 按 U2 求和 → 列归一得 `P1(U1|B)`（形状 `(32,1024)`，列和 1）；
3. `P2(U2|U1,B) = P_F / P1` 逐 `(U1,B)` 归一（形状 `(32,1024,32)` 逻辑，`(U1,B,U2)`，行和 1）。
- 禁止先取 log 再归一；禁止在未归一表上做 `q@P`。

### 1.3 概率域 vs log 域

- 存储与传递一律概率域；decoder 入口一律概率域 `(N,32)`（`decode_row_layered_fftqspa`
  内部自行转 log-belief）。
- CE 与审计一律 `log2`（`CE=-mean(log2 P)`）；decoder 内部自然 log 转换显式且不进入本审计口径。
- `P1` 表形状 `(32,1024)`（U1×B），decoder prior 形状 `(N,32)`（每行一 symbol 的 32 元分布）。

### 1.4 数值下溢

- 双 floor 并存，语义分离冻结：审计/CE 用 `PROB_FLOOR=1e-300`（先正常归一再 `max(P,1e-300)` 后取 log，只保护 log）；
  decoder 通路用 `1e-15`（V54/v35 历史路径：`maximum(...,1e-15)` 后重归一，保护 FFT-QSPA 迭代）。
- 两 floor 均不得改变归一性（floor 后必须重归一）；`P1(U1|B)=0` 的 `(U1,B)` 切片回退均匀 `1/32`
 （V54 第 419–420 行语义），不得删样本。

### 1.5 L2 oracle prior vs 实际条件 prior（关键区分）

- `CE_L2_oracle`（预算诊断用）：`P2(U2 | U1_true, B)`，用真实 `U1` 查表
 （`v35.get_conditional_posterior_l2(counts,bob,u1)` 语义：`rows=arr[u*32+0..31, b]` 行归一）。
  仅作分层预算诊断，非生产性能。
- 生产 L2 prior：`prior_l2 = q @ P`，其中 `q=softmax(L1 final_beliefs)`（`(N,32)`），
  `P=P(U2|U1,B)` 为 `(32,32,1024)→(N,32,32)` 切片（`v54.get_l1_app_prior_l2` 语义）。
  L1 失败仍恒进 L2（V54/D3 历史语义：L2 恒用 `q`，无门控；L2 base-ok 短路 joint/total）。
- D4R2 的 `CE_L2_oracle=3.347605` 是 oracle 上界口径；生产 `q@P` 只会更差，不得把 oracle CE
  当作生产可达性能引用。

### 1.6 decoder 输入形状与接口映射

| D5 prior | 形状 | 现有接口（精确复用） |
|---|---|---|
| `P1(U1\|B)` 查表 → L1 prior | `(N,32)` | `v54.get_l1_prior_p_u1_given_b(counts(1024,1024), bob(N,))`（D3 包装：`get_l1_prior_production`） |
| `q=softmax(L1 beliefs)` | `(N,32)` | `v54.softmax_beliefs`（D3 包装：`softmax_beliefs_history`） |
| `prior_l2=q@P` | `(N,32)` | `v54.get_l1_app_prior_l2(counts, bob, q)`（D3 包装：`build_l2_prior_from_l1`；签名禁 Alice/oracle） |
| oracle L2（仅诊断/门控） | `(N,32)` | `v35.get_conditional_posterior_l2(counts, bob, u1_true)` |
| decoder 调用 | `H(m,n) uint8, priors(N,32), syndromes(m,)` | `v35.decode_row_layered_fftqspa(..., max_iter=90, damping_alpha=1.0, warm_beliefs=None, field=GF(32))` → `DecoderResult(x_hat, syndrome_ok, iterations 0..max, final_beliefs)` |

**对齐结论：对齐，需且仅需一个 frozen adapter delta**（不实现，只声明）：
V54 现有 prior 路径用原始 counts + `1e-15` floor，无 Laplace `lambda*` 平滑；
D5 F 模型要求先对 counts 施加 `lambda*=137.3823795883264` 平滑再列归一。
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
| (参1.3) | 5078.18 | 1016 | 4456.23 | 892 | 1908 | 9534.52 | 1907* | 同上（D4R2：1907 vs 216, margin −1691） |

`*` joint-ceil 与 m1+m2 差 1 行是 ceil 伪影（`f=1.1/1.3`），权威口径取 `m1+m2`。
worst joint `7.178766` → `7351.06` bits → `1471` 行（均值 1467 + 4 行）；
std `0.0158` ≈ `16.2` bits ≈ 4 行；range `0.0423` ≈ `43.3` bits ≈ 9 行。
`M_max=1000` 每层覆盖 `f≤1.2`（L1 938 ≤ 1000 margin 62 行；L2 823 ≤ 1000 margin 177 行），
覆盖 `f=1.0`（margin 218/314 行）。

### 2.2 为何旧 216 行在 f=1.0 不足（bit 对比，不重复 D4 证明）

- L1：需要 `3906.30` bits，旧给 `16*5=80` bits → 缺 `3826.30` bits（766 行，48.9 倍不足）。
- L2：需要 `3427.95` bits，旧给 `200*5=1000` bits → 缺 `2427.95` bits（486 行，3.43 倍不足）。
- Total：需要 `7334.24` bits，旧给 `1080` bits（`1.0546875` bit/symbol）→ 缺 `6254.24` bits（1251 行，6.79 倍不足）。
- 结论只记 `MODEL_BUDGET_MISMATCH`（D4R2 route C）；禁止写成信息论极限/GF32 失败/LDPC 不可能；
  L1 不足禁止只加 L2。

### 2.3 “约 700–1000 行”目标的构成（冻结解释）

- 本计划把任务书的“约 700–1000 行”冻结为**每层独立 mother 的 `M_max=1000` 行级**：
  L1 mother `1000×1024`（`f=1.0` 披露前 782 行，`f=1.2` 披露前 938 行），
  L2 mother `1000×1024`（`f=1.0` 披露前 686 行，`f=1.2` 披露前 823 行）。
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

### 3.1 选型：V31 QC-cyclic-projective `build_layer` 为扩展基线

`nonbinary_v31.build_layer(m, n=1024, family="qc_cyclic_projective", field=GF(32))`
（支撑：`build_supports_qc_cyclic` + `select_projective_ratio_v31` + `projective_column_audit`）。
选中理由（一行）：它是仓库唯一同时满足“任意 m（含 1000）、n=1024 已验证、确定性可重放、
`occupancy≤31` 硬门、`projective_safe + full_row_rank` 双审计”的 GF32 构造器，
且列重恒为 2 使 700–1000 行仍极稀疏。

- 稀疏性：列重恒 2；行重均值 `2n/M`：`M=1000` 时 ≈2.05，`M=782` 时 ≈2.62——天然适配大 m。
- rank 保证：audit 含 `rank / full_row_rank / projective_safe`；`construction_ok` 要求三者全过。
- 可扩展性：`build_supports_qc_cyclic(m,n)` 对任意 `m≥2` 枚举 `(a,(a+s)%m)` 至 n 列，
  `m=1000` 时候选对 `499500 ≫ 1024`，occupancy 自然 ≤2，无容量墙。
- 嵌套适配：单 mother 一次性按 `M_max=1000` 构建，披露取行前缀 `H[:k]`
  （一行 reinterpretation，无需改构造器；前缀秩逐个验证，见 §4）。

### 3.2 备选与否决（冻结）

- 备选：V38 `construct_lane_c_prototype`（SC-inspired banded，`L=8,w=2,dv=2`，4-cycle 回避）。
  仅当 V31-QC 在 G2 生死实验 FAIL 且根因为图结构（非 prior/decoder）时，才允许另立 change 评估；
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
一次构建、行前缀嵌套披露、每前缀秩证明。**禁止直接假设适用于 GF32**，四点边界冻结：
(a) 域不同（GF2 vs GF32，FFT-QSPA 卷积代价不同）；
(b) 维度不同（10240-bit vs 1024-symbol，行重 regime 不同）；
(c) 码率 regime 不同（`f=1.3 NOT_MEASURED` vs F 联合 `7.16` bit/symbol 实测需求）；
(d) decoder 不同（binary BP vs layered FFT-QSPA）。D5 的稀疏/rank 结论需独立验证。

## 4. nested prefix / 稀疏 / 满秩 / 披露 API（冻结定义）

- 一句话定义：每层 GF32 mother 是一次性构建的单个 `M_max×1024` 矩阵（`M_max=1000`），
  披露是行前缀 `H[:k]`，`k` 取自冻结披露集合，对一切已披露 `k` 要求 GF(32) 满行秩，
  后增行只追加、不改动前缀行。
- nested prefix 语义：`H_mother` 形状 `(1000,1024)` uint8（值域 `0..31`）；
  披露集合 `K={m1/m2(f=1.0/1.05/1.1/1.2)}`（§2.1：L1 `{782,821,860,938}`，L2 `{686,720,755,823}`）；
  对任意 `k∈K`，`H[:k]` 满行秩（rank `=k`）；`H[:k1]` 是 `H[:k2]`（`k1<k2`）的精确行前缀。
- 稀疏度目标：V31-QC 基线下列重恒 2；行重目标 `2–4`（均值 `2n/M_max≈2.05`，允许 `±1` 波动带）；
  零行/零列数为 0；`support occupancy ≤31`（构造器硬门）。
- 满秩验证方法（只定义步骤，不执行大矩阵验证）：
  `nonbinary_codebook.gf_rank(H[:k], GF2mField.create(32)) == k` 逐 `k∈K` 断言
  （pinned 多项式基高斯消元）；tiny 规模（`m≤8,n≤16`）附手算可验示例；
  `M_max=1000` 全量验证是 `O(m²n)` 量级 field 运算，列为 apply 阶段实现任务并配预算，
  本轮不执行。
- 增量披露 API 形状（最小列表/指针，禁通用框架）：
  `m_max: int`（=1000）+ `prefix_rows: int`（=k）+ `extra_rows: list[int] | None`
 （默认 `None` = 前缀 `0..k-1`；非 None 时为显式行索引表，用于诊断重排实验，生产恒 None）。
  mother 存单个 `np.ndarray`，披露即视图 `H[:k]`；L1 披露先行，L1 syndrome-ok（或 90 轮耗尽）后再开 L2 前缀。

## 5. 三级 matched synthetic 门控（tiny / n=64 / n=256）

通用冻结：synthetic 生成必须 matched to F（由 `P_F` 采样或按 CE 标定噪声）；
**禁止用 AWGN/BSC/QSC 替代**；prior 一律用真 `P_F` 表（无估计误差，隔离 prior 错）；
Bob 边际用 CAL TRAIN 经验 `P(B)`（CAL-only，不碰 VAL）；种子冻结列表制；`max_iter=90`，
`damping=1.0`，cold start（`warm_beliefs=None`），tag 不生成不计费。

| 级 | n | 目的 | 生成（matched） | prior | 披露行数 | 通过阈值 | 失败三分法 |
|---|---|---|---|---|---|---|---|
| G0 tiny | ≤9（手算 2×2×2 或 `k=2/3,n=6/9` 穷举） | 数学正确性 | 穷举/手算联合分布；`P_F` 精确已知 | 真表 | tiny mother 2–4 行（`gf_rank` 全秩） | 边际/条件与暴力误差 `<1e-12`；链式 `<1e-10`；无噪精确恢复 100%；`iterations≤max` | 边际/链式错→数学错；无噪 syndrome 错→图/field 错；真 prior+足行仍不收敛→decoder 错 |
| G1 | 64 | 集成/ scale 趋势（非杀门） | `B∼P_CAL(B)`，`A∼P_F(·\|B)`，≥100 blocks | 真表 | §2 scaled：f=1.0 `m1=49/m2=43`；f=1.2 `m1=59/m2=52` | 单调 `FER(1.2)≤FER(1.0)`；oracle-L2 exact ≥ APP-fed exact（分层有效）；零 crash/非有限 | crash/非有限→实现错；单调反转→图/scale 错；oracle≈APP→分层语义错 |
| G2 | 256 | 性能趋势 + **唯一生死实验**（见 §6） | 同上，≥200 blocks | 真表 | f∈{1.0,1.1,1.2}：`m1={196,215,235}`，`m2={172,189,206}` | §6 PASS/FAIL | 同 §6 分支 |

- G0/G1 失败判据只做三分归因（数学错 vs 图错 vs prior/decoder 错），不直接杀路线；
  G1 的 prior 错项恒 excluded（真 prior 构造），若 G1  fail 而 G0 pass → 图/scale 错。
- n=1024 真实执行前置条件（冻结）：G0+G1+G2 全过 + Pre-EXECUTE review（`HEAD==origin==实现SHA`、
  `ACCEPTED_PLAN_SHA` 重推导、`run_01` 不存在、预算与授权一致、`py_compile`+关键测试 PASS）。

## 6. 最小生死实验（go/no-go，唯一杀实验 = G2）

- 实验：`n=256` matched synthetic（`B∼P_CAL(B)`，`A∼P_F(·|B)`，`lambda*` 真值表），真 prior，
  V31-QC `1000×256`？否——注意：G2 的 mother 列数随 n 缩放（`M_max` 按同码率缩放？
  冻结：G2 mother 按 `n=256` 独立构建 `M_max=500`？不——保持行数与 §5 表一致：
  mother 构建为 `(500,256)`（覆盖 f=1.2 的 441 行 total-equivalent per-layer 上界 235/206，
  余量作实现冻结值 500），披露取 §5 的 `m1/m2` 前缀；`f∈{1.0,1.1,1.2}` 三点扫描，
  ≥200 blocks，冻结种子，`max90/damping1.0/cold`，L1-then-L2。
  （列数缩放依据：`rows=ceil(n*CE*f/5)` 同公式，`n=256` 行数见 §5 表。）
- PASS（继续 GF32，允许起草 n=1024 实现计划）：`f=1.2` 端到端精确恢复率 ≥90%
  且 `FER(1.2)≤FER(1.1)≤FER(1.0)` 且 oracle-L2 ≥ APP-fed。
- FAIL（放弃 GF32 当前域真实路线）：`f=1.2` 精确恢复率 <90% 即 FAIL，其中：
  `<50%` = 路由死（`GF32_ROUTE_DEAD`），后继仅 `d=256,[4,4]` backlog；
  `50–90%` = 图有改善信号但预算内不足（`GF32_INSUFFICIENT_AT_BUDGET`），同样放弃 n=1024 真实，
  允许的后继只有 backlog 降维，不调参、不加行、不重跑。
- 禁止多实验铺开：本节是 D5 唯一的性能杀实验；G0/G1 是正确性/集成门，无杀权。

## 7. 风险与 open questions（冻结记录，实现不得自行消解）

- R1（科学）：生产 `q@P` 相对 oracle 有 L1 误差传播税，D5 行数表基于 oracle CE，
  真实所需行数只会更多；G2 用真 prior + oracle 对照显式度量该税。
- R2（工程）：700–1000 行 FFT-QSPA 运行时未实测（每轮每 check `q=32` FWHT 卷积，
  `1000×1024` 稀疏图 ×90 轮）；G2 在 `n=256/500行` 级先暴露趋势，n=1024 预算另批。
- R3（构造）：V31-QC 前缀秩在 `k∈K` 需逐个验证；若某前缀秩亏，允许的唯一修复是同种子族内换 `family` 参数
  （另立修订，不现场调参）。
- R4（语义）：`lambda*` 是 D4R2 outer-mean 单值；G2 synthetic 真值表直接采用它，
  不重做 inner 选择（synthetic 无估计问题）；n=1024 真实阶段的 λ 重拟合程序沿用 D4 口径，另批授权。
- OQ1（需 main thread 单点决策，见 tasks D5-T8）：§2.3 的 per-layer `M_max=1000` 解读是否接受？
  若坚持统一 total 700–1000，则 D5 直接维持 route C，无后续实现。
- OQ2：G2 的 90% PASS 线是否接受？备选 80%（更松）/ 95%（更严）一行记录，默认 90%，改线需重审。
