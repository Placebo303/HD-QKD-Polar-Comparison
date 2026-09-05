# V72P2D5 计划冻结报告 R2（PLAN_FREEZE；PLAN_REVISE_REQUIRED，只读 + 冻结结论）

- Change：`formal-ir-v72p2d5-gf32-rate-mother-plan`，Cycle `V72P2D5-GF32-RATE-MOTHER`
- 状态：`PLAN_REVISE_REQUIRED`（R2；R1 `PLAN_ACCEPTED` 已被 `PLAN_CORRIGENDUM_R2.md` 宣告 superseded，仅作历史保留）；
  `REAL_EXECUTION_AUTHORIZED=false`，`DECODER_EXECUTED=false`，`FULL_MOTHER_BUILT=false`，`VAL_LOADER_CALLS=0`
- R2 CAUSE：`DEGREE2_PREFIX_CONNECTIVITY_IMPOSSIBLE`（strict 证明见 corrigendum §2：full `E=2N=2048, V=2024, need 2023` 可行，纠正 2000→2048；
  L2 `k=686: E_prefix<=2048-628=1420 vs need 1709`、L1 `k=782: <=2048-436=1612 vs need 1805`，任意排序不可修复；
  非 V31 bug，非 decoder 结果，仅证列重 2 + 1000 非零 + 前缀单连通三者联合不可满足；natural-prefix 与 row-ordering 路线关闭；T0/T1 代码未提交未接受）
- R2 冻结单新 mother：`G2_MINIMAL_NESTED_DV3_GF32`（每层 `1000x1024`，列重 3，GF32 非零 `1..31`；无并行家族；
  必要条件：`E=3072`，L2 `2444>=1709`、L1 `2636>=1805`，仅记必要条件可满足，不预断结构 PASS）
- 目标状态（R2 Review ACCEPT 后仅可变为）：`PLAN_ACCEPTED + implementation_authorized:false + synthetic_execution_authorized:false + real_execution_authorized:false`；
  Review PASS 不自动授权实现；后续分开 `R2 implementation packet→review→M0/G0 auth→G0 review→P0/G1 auth→G1 review→G2 auth→G2 Pre-RESULT`，不一次授权 G0/G1/G2。
- Frozen input：`d=1024, U1/U2=[5,5], GF(32), N=1024`；模型 F；
- 目标状态（Review ACCEPT 后仅可变为）：`PLAN_ACCEPTED + implementation_authorized:false + synthetic_execution_authorized:false + real_execution_authorized:false`；
  Review PASS 不自动授权实现；后续分开 `implementation packet→review→M0/G0 auth→G0 review→P0/G1 auth→G1 review→G2 auth→G2 Pre-RESULT`，不一次授权 G0/G1/G2。
- Frozen input：`d=1024, U1/U2=[5,5], GF(32), N=1024`；模型 F；
  `CE_L1=3.814742 / CE_L2_oracle=3.347605 / CE_joint=7.162347`（worst `7.178766`，
  std `0.0158`，range `0.0423`，`lambda*=137.3823795883264`，D4R2 R2 审计）；
  旧 `16/200/216` 行禁真实。
- `M_max=1000 is a D5 synthetic construction cap, not a production sufficiency claim.`
  不代表生产充分/传播税覆盖/worst-fold 或 finite-size margin 充分，不授权 `n=1024` 真实，不允许 `f=1.3`（L1 1016 超 cap）。
- 本报告是 D5-T7 产出；实现任务未启动；阈值/种子/门禁/预算/调用数冻结后不得回写。
- 本轮不 push 不 commit，留给后续 operator 统一 commit+push。

## 1. 可复用能力表（只读 grep + 签名确认，无执行）

列：函数/文件 | 输入 | 输出 | 任意 m | nested prefix | rank 保证 | 行/列重 | n=1024 绑定 | 700–1000 适配 | 已有测试 | 复用风险

| 函数/文件 | 输入 | 输出 | 任意 m | nested | rank | 行/列重 | n 绑定 | 700–1000 | 测试 | 风险 |
|---|---|---|---|---|---|---|---|---|---|---|
| `nonbinary_field.GF2mField.create(32)`（poly `0b100101=37`）+ `add/mul/inv` | `q=32` | field（exp/log 表） | N/A（与 m 无关） | N/A | N/A | N/A | 否（q-only） | 是（O(1) ops） | `_check_field` 自检 + V35 系 | 低 |
| V31 `build_layer(m,n=1024,*,family,field,require_full_rank)`（`nonbinary_v31.py:624`；历史能力记录保留） | `m,n,family` | `(supports, audit{rank,full_row_rank,projective_safe,occupancy≤31})` | 是（含 1000） | 否（per-m 重建；R2 已 EXIT 作 D5 嵌套 mother） | 是（`full_row_rank+projective_safe` 方法复用，仅 full 矩阵） | 历史列重 2（R2 不可能性证明后不再作 live 目标） | 默认 1024，`n` 参数化 | **否（R2 状态 `EXIT_PREFIX_CONNECTIVITY_IMPOSSIBLE`；仅保留 field/rank/decoder 复用）** | V31 gate/closeout 审计测试 | 低（历史保留，不改历史文件） |
| R2 新 mother `G2_MINIMAL_NESTED_DV3_GF32`（本计划冻结，无实现） | `N=1024, M_max=1000, seed L1 2026090501 / L2 2026090502` | 每层 `1000x1024` GF32（列重 3：2 base + 1 expansion；系数 `1..31` 冻结 seed PRNG 一次） | 是（单构建 + 构造序前缀 `H[:k]`） | 是（`H[:k1]` 为 `H[:k2]` 精确行前缀；自然序 = 构造序；无 row ordering） | 逐 `k in K` 验证（`gf_rank==k`；不足 => `G2_PREFIX_RANK_BLOCKED`；无重播种/追 rank） | 列重恰 3；行重均 `≈3.07`；每行度 >=2；无重复边/三元组 | 是（N=1024；`n=64/256` 同合同缩放） | **是（R2 唯一冻结 mother；仅必要条件可满足，不预断 PASS）** | 待新 R2 packet（本轮不建） | 低（最小贪心，无 PEG 库/框架） |
| V31 `build_matrix_packet(m1,m2_by_source,n)` | `m1, {1M,1p5M,2M}:m2` | L1 + per-source L2 packet | 是 | 否（独立层） | 逐层审计 | 同上 | 同上 | 同上 | 是（分层独立母矩阵语义与 D5 一致） | 低 |
| V28 `build_matrices(config)` + `_build_pair_matrix` | config(`q,n,m1,m2`) | `h1(6×1024), h2{src}(202×1024)`（历史小 m 值） | 是（参数化） | 否（独立构建；row-prefix 输入被拒） | 小 m 全秩 | degree-2 pairs | 是（config n） | 未验证（仅小 m 实证）→ H1 小矩阵参考 | V28/V29 系 | 中 |
| D3 冻结几何 `nested_geometry()`（`H1=16,H_base=184,joint=192,total=200`，leak `1064/1104/1144`） | 无 | 形状/泄漏常量 | 否（冻结 16/184/200） | 是（`184/192/200` 前缀） | rank-16 H1 | QC 小矩阵 | 是（N=1024） | 否（即被替代的旧预算） | `test_v72p2d3` | 低（历史对照保留，不扩展） |
| V38 `construct_lane_c_prototype(source,seed,field)`（L=8,w=2 banded, dv=2, 4-cycle 回避） | `source,seed` | `(H, metrics)` | 否（小 m 冻结） | 否（单发构建） | 弱 | dv=2 banded | 是 | 否（需重设计分配向量）→ **备份** | V38/V39/V40/V41 系 | 中 |
| V36 `build_v36_incremental_matrix(H_base,source)`（+32 行，行重 10–14） | `H_base` | `(H_mother, {S0..S3})` | 否（固定 +32） | 是（vstack+切片） | 无 | 行重 10–14（700 行下过密，D5 否决） | 是 | 否 | V36 系 | 高（D5 不用） |
| V35 `build_v35_incremental_mother_matrix(base_H)`（192→224） | `base_H` | `H_mother(224×1024)` | 否（硬编码 224） | 是（vstack） | 无 | protograph QC | 是 | 否 | V35 系 | 高（D5 不用） |
| `nonbinary_codebook.gf_rank(matrix,field)`（pinned 基高斯消元） | 任意矩阵 | `rank: int` | 是 | N/A（验证工具） | 本身即秩判定 | N/A | 否 | 是（`O(m²n)`，配预算执行） | codebook 系 | 低 |
| v35 `decode_row_layered_fftqspa(H(m,n),priors(N,32),syndromes(m,),max_iter,damping,warm_beliefs,field)` → `DecoderResult(x_hat,syndrome_ok,iterations 0..max,final_beliefs)` | 任意 `m×n` + `(N,32)` | 解码结果 | 是 | N/A（调用方切片） | N/A | 任意（每 check `q=32` FWHT） | 否（任意 n） | 是（700+ 行 runtime 未实测→R2 风险，P0 预检） | V28/V31/V35/D3 系 | 低-中 |
| V54 `get_l1_prior_p_u1_given_b(counts(1024,1024),bob)`（`reshape(32,32,1024)` 求和） | counts+bob | `(N,32)` | N/A | N/A | N/A | N/A | 否（任意 N） | 是 | V54/D3/D4 系（含转置反例） | 低 |
| V54 `get_l1_app_prior_l2(counts,bob,q(N,32))` + `softmax_beliefs` | counts+bob+q | `(N,32)` | N/A | N/A | N/A | N/A | 否 | 是 | 同上 | 低；delta 见下 |
| v35 `get_conditional_posterior_l2(counts,bob,u1_true)`（oracle，仅诊断） | counts+bob+u1 | `(N,32)` | N/A | N/A | N/A | N/A | 否 | 是（诊断用） | V35/V38 系 | 低 |
| D3 `build_canonical_counts / symbols_to_layers / layers_to_symbols / build_stage1_P / build_stage2_P / ce_*_log2` + 生产包装 `get_l1_prior_production / build_l2_prior_from_l1` | CAL symbols / counts | counts+ prior 表 + CE | N/A | N/A | N/A | N/A | N=1024 | 是 | `test_v72p2d3/v72p2d4*` | 低 |
| CLI/test 入口 | — | — | — | — | — | — | — | D5 新增 CLI+test 各一（deferred） | — | 低 |

**关键结论（R2）**：V31 degree-2 路径状态 = `EXIT_PREFIX_CONNECTIVITY_IMPOSSIBLE`（仅保留 field/rank/decoder 复用，不改历史文件，不是 GF32 路线失败）；
冻结单新 mother `G2_MINIMAL_NESTED_DV3_GF32` = 每层 `M_max=1000` 一次构建 + 构造序行前缀披露（无 row ordering，需 M0 逐 `k` 验证，不预断 PASS）。

## 2. 行数表（权威：分层独立 ceil）+ 轴合同 + 种子 + 预算 + 调用数

`rows=ceil(N*CE*f/5)`，F 均值 `L1 3.814742 / L2 3.347605 / joint 7.162347`。
轴合同：`counts.shape=(Alice,Bob)`，`P_F.shape=(Alice,Bob)`，`axis0=Alice, axis1=Bob`，
`assert_allclose(P_F.sum(axis=0),1.0)`；`P_reshaped=P_F.reshape(32,32,1024)`，
`P1=P_reshaped.sum(axis=1)`，`assert_allclose(P1.sum(axis=0),1)`；
`P2[u1,b,u2]` 固定 `(u1,b)` 沿 `u2` 和为 1。无“axis1 列归一”表述。

### n=1024（真实目标，synthetic cap 内仅 f≤1.2）

| f | m1 (L1) | m2 (L2) | m1+m2 | joint-ceil（对照） | 旧预算缺口 |
|---|---|---|---|---|---|
| 1.0 | 782 | 686 | 1468 | 1467 | L1 −766 / L2 −486 / Tot −1251 行 |
| 1.05 | 821 | 720 | 1541 | 1541 | 同上口径 |
| 1.1 | 860 | 755 | 1615 | 1614* | 同上口径 |
| 1.2 | 938 | 823 | 1761 | 1761 | 同上口径 |
| (参1.3禁入) | 1016 | 892 | 1908 | 1907* | Tot −1691 行（D4R2 一致；L1 1016 超 1000 cap，禁入） |

`*` 差 1 行为 ceil 伪影，权威取 `m1+m2`。worst joint → 1471 行（+4）；std ≈ 4 行；range ≈ 9 行。
bit 对比：L1 需 3906 vs 旧 80；L2 需 3428 vs 旧 1000；Total 需 7334 vs 旧 1080（6.79 倍不足）。

### scaled 门控行数（同公式）

- n=64：f=1.0 `m1=49/m2=43/joint-ceil=92`；f=1.2 `m1=59/m2=52/joint=111`。
- n=256：f=1.0 `m1=196/m2=172/joint=367`；f=1.1 `215/189/404`；f=1.2 `235/206/441`。

### 冻结种子

graph L1 `2026090501`、L2 `2026090502`；G0 `2026090510..2026090517`（8）；
G1 `2026090600..2026090699`（100）；G2 `2026091000..2026091199`（200）。禁 seed search，运行后禁换 seed。

### P0 与预算

P0 COST-PREFLIGHT：`n=64` 2 blocks `f=1.0,1.2` APP+oracle，记录 wall/iterations/RSS，不计入 G1；外推 G1/G2 projected wall。
单 call `120s`，G1 总 `≤900s`，G2 总 `≤3600s`，peak RSS `<2GiB`；G2 projected>3600s 则 `RESOURCE_PROJECTION_BLOCKED`。

### 调用数

G1 APP-fed `100 blocks x 2 rates` + oracle 前 20 同 seed `x 2 rates` 仅诊断；
G2 APP-fed `200 x 3 rates` + oracle 前 40 同 seed `x 3 rates` 仅诊断。

## 3. prior 对齐结论

对齐 + 单 delta：下游（`reshape` 求和 / `q@P` / `(N,32)` / `max90/damping1.0/cold`）逐字复用 V54/v35；
delta 仅为 `counts → P_F` 前插入 frozen `lambda*=137.3823795883264` 平滑（D3 `_smooth_counts` 语义）。
floor 双轨（审计 `1e-300` / decoder `1e-15`，均重归一）与 oracle-vs-生产区分已冻结；oracle 仅诊断（9 项同报），删除硬门。

## 4. 嵌套 mother（一句话；R2）+ M0 + 13 项门禁（无 row ordering）

每层一次性构建单个 `(1000,1024)` GF32 矩阵（列重 3，系数 `1..31`）并按冻结披露集 `L1 {782,821,860,938} / L2 {686,720,755,823}` 取构造序行前缀 `H[:k]`，
一切已披露前缀满行秩、每变量前缀内度 >=2（新增硬门，非递减）、每行度 >=2、无重复边/三元组、后增行不改前缀、
L1 先收敛再开 L2、披露 API 为 `m_max + prefix_rows + extra_rows|None` 最小三元组。
`M_max=1000 is a D5 synthetic construction cap, not a production sufficiency claim.`
M0（单构建 → 全 prefix PASS 才进 G0；无 seed 搜索；无独立矩阵冒充；无 support 追 rank；无 decoder 引导）+
13 项门禁（rank/zero_rows/zero_cols/列 degree min-med-max/deg1/deg2/deg3/CC 数/largest 分数/isolated/row-degree 直方图/4-cycle/dup-投影等价/GF32 非零）+
最低 PASS（`zero_columns==0, isolated==0, largest_fraction==1.0, rank==k, duplicate==0, variable_degree_min>=2`；degree-1 只披露）+
4-cycle 只计数（base-only 目标 0；非零则 `STRUCTURE_PASS_WITH_CYCLE_RISK`；G1/G2 裁判，不回头调图）+
系数分离（冻结 seed PRNG 一次；零 forbidden；秩不足 => `G2_PREFIX_RANK_BLOCKED` 返回 planner）；
无 row-ordering live 路径（自然序 = 构造序）。

## 5. 门控与分级实验摘要

- G0 tiny：数学正确性（边际/条件 `<1e-12`，链式 `<1e-10`，syndrome 重算一致，tree/tiny exhaustive 一致，无噪 100%；失败 BLOCKED）。
- P0：成本预检（不计入 G1，外推后超门则 `RESOURCE_PROJECTION_BLOCKED`）。
- G1 n=64：集成趋势门（APP-fed 100 paired f={1.0,1.2}，单调 `exact_rate(1.2)>=exact_rate(1.0)` + 零 crash/nonfinite + 结构趋势；无杀权；命名 `exact_failure_fraction`）。
- G2 = 唯一分级实验：n=256 matched synthetic，真 prior，dv3 mother 按 n=256 同合同构建、
  `f∈{1.0,1.1,1.2}` 三点（`m1={196,215,235}`，`m2={172,189,206}`），200 blocks；
  四态：`>=90%@1.2` 且单调 `G2_SYNTHETIC_QUALIFIED` / `50-90% G2_INCONCLUSIVE` /
  `<50% G2_CURRENT_CONFIGURATION_FAILED` / crash-非有限-数学不一致 `IMPLEMENTATION_OR_NUMERICAL_BLOCKED`；
  PASS 只用 APP-fed 端到端 exact；单调 raw inequality + Wilson 并报；无论结果不自动进 `n=1024`。
- n=1024 真实前置：G0+G1+G2 全过 + Pre-EXECUTE review。

## 6. 修改文件清单（R2：恰 7 docs，无生产代码）

修订（5 文件，均在本 change 目录）：

1. `openspec/changes/formal-ir-v72p2d5-gf32-rate-mother-plan/proposal.md`
2. `openspec/changes/formal-ir-v72p2d5-gf32-rate-mother-plan/design.md`
3. `openspec/changes/formal-ir-v72p2d5-gf32-rate-mother-plan/tasks.md`
4. `openspec/changes/formal-ir-v72p2d5-gf32-rate-mother-plan/specs/spec.md`
5. `openspec/changes/formal-ir-v72p2d5-gf32-rate-mother-plan/PLAN_FREEZE.md`（本文件）

新增（1 文件）：

6. `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/PLAN_CORRIGENDUM_R2.md`

修改（1 文件）：

7. `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/cycle_state.yaml`（状态 `PLAN_REVISE_REQUIRED`，全部执行授权 false，`decoder_executed=false`，`full_mother_built=false`，`next_gate=INDEPENDENT_R2_PLAN_REVIEW`）

R2 修订内容：degree-2 不可能性冻结（full `E=2048` 纠正；L2 `1420<1709`、L1 `1612<1805`；任意排序不可修复）；
V31-degree-2 EXIT（保留 field/rank/decoder 复用）；单新 dv3 mother（`E=3072` 必要条件 L2 `2444>=1709`、L1 `2636>=1805`，不预断 PASS）；
最小确定性贪心 support + 系数分离；新增 `variable_degree_min>=2`；4-cycle 只计数（`STRUCTURE_PASS_WITH_CYCLE_RISK`）；
删除 row-ordering live 路径。历史删除注记保留；旧 verdict/packet 不动（仅 corrigendum 宣告 superseded）。
git 状态/提交：本轮不 push 不 commit，留给后续 operator 统一 commit+push；staged manifest 必须恰为上述 7 docs。

## 7. 剩余风险 / open questions（R2 已决策，残留实现风险）

- R1 生产 `q@P` 相对 oracle 的 L1 传播税（行数表基于 oracle，只会更紧；G1/G2 诊断度量，非硬门）。
- R2：700–1000 行 FFT-QSPA runtime 未实测（P0 预检 + 外推 + RESOURCE 门）。
- R3：dv3 前缀秩/连通/度门禁需 M0 逐 `k in K` 验证；无 seed 搜索；无独立矩阵冒充；无 support 追 rank；秩不足则 `G2_PREFIX_RANK_BLOCKED`。
- R4：`lambda*` 为 outer-mean 单值；synthetic 真值直接采用，真实阶段重拟合沿 D4 口径另批。
- OQ1（R1 已决策，R2 保留）：per-layer `M_max=1000` synthetic cap 接受但限定（见 §2）。
- OQ2（R1 已决策，R2 保留）：90% 改四态分级，非死亡线。
- R5（R2 新增）：dv3 仅必要条件可满足；4-cycle 非零风险经 `STRUCTURE_PASS_WITH_CYCLE_RISK` 记录，G1/G2 裁判，不回头调图。

## 8. 独立 R2 Plan Review 前自查清单（逐项，R2；18 checks）

- [ ] R2 corrigendum 存在：`PLAN_CORRIGENDUM_R2.md` 记录 `PLAN_REVISE_REQUIRED` / `DEGREE2_PREFIX_CONNECTIVITY_IMPOSSIBLE` /
  `UNCOMMITTED_NOT_ACCEPTED` / `decoder_executed:false` / `full_mother_built:false`；旧 verdict/packet 未动（仅宣告 superseded）。
- [ ] 不可能性证明数全：full `E=2N=2048`（纠正 2000→2048）、`V=2024`、`need 2023` 可行；前缀界 `E_prefix<=2N-2(M-k)`；
  L2 `k=686: 1420<1709`、L1 `k=782: 1612<1805`；任意排序不可修复；非 V31 bug / 非 decoder 结果 / 不关闭 GF32 路线。
- [ ] G1 状态：V31 degree-2 `EXIT_PREFIX_CONNECTIVITY_IMPOSSIBLE`；保留 field/rank/decoder 复用；不改 V31 历史。
- [ ] G2 冻结单 mother：`G2_MINIMAL_NESTED_DV3_GF32`（`N=1024, M_max=1000, 列重 3, GF32 1..31`；无并行家族）；
  论证仅必要边数（`E=3072`；L2 `2444>=1709`、L1 `2636>=1805`）；不预断结构 PASS。
- [ ] support 构造全：2 base（`[0,k_min)` 不同 check；最早前缀内每变量度 >=2）+ 1 expansion（覆盖全部 suffix 行；允许必要 spill）；
  每行度 >=2；无重复边；无重复三元组；全确定性；seed L1 `2026090501` / L2 `2026090502`；无 seed search；
  最小确定性贪心（edge1 最小度；edge2 不重复对→异分支→最小度→最小索引；edge3 先覆盖 suffix；收尾确定性交换）；无 PEG 库/框架；无 decoder/syndrome/Alice/Bob 视图。
- [ ] 系数合同全：support/coeff 分离；`1..31` 冻结 seed PRNG 一次；零 forbidden；无重播种；无 decoder 引导；无 support 追 rank；
  秩不足 => `G2_PREFIX_RANK_BLOCKED`，不自动重抽。
- [ ] prefix 门全：L1/L2 每个 `k` 13 项 + 最低 PASS 含新增 `variable_degree_min>=2`（非递减）；M0 全 PASS 才进 G0。
- [ ] 4-cycle 合同全：变量对共享 check 对机械计数；base-only 目标 0；expansion 如实计数（总数/incidence/最大）；
  无绝对阈值；非零则 `STRUCTURE_PASS_WITH_CYCLE_RISK`，不回头调图。
- [ ] row ordering 已删：自然序 = 构造序；无 `order_rows_for_prefix_coverage` live 实现/调用；无后构造/decoder 重排。
- [ ] 未来 delta 在 tasks.md：删 degree-2 V31 生产候选、删 row-ordering 实现、加 dv3 构建器；保留 prior/生成器/审计/隔离；未提交码仅部分候选；新 packet 接受前不动码。
- [ ] OQ1 synthetic cap：四工件统一 `M_max=1000 is a D5 synthetic construction cap, not a production sufficiency claim.`；无生产充分断言；无 `n=1024` 真实授权；无 `f=1.3`。
- [ ] OQ2 非死亡：四态命名齐全；无 live `GF32_ROUTE_DEAD`/backlog 唯一后继/放弃 GF32；G2 不否定 GF32。
- [ ] 轴无歧义：`counts.shape=(Alice,Bob)`，`P_F.shape=(Alice,Bob)`，`axis0=Alice, axis1=Bob`，`P_F.sum(axis=0)==1`，`P1.sum(axis=0)==1`，`P2[u1,b,u2]` 沿 `u2` 和为 1；无“axis1 列归一”。
- [ ] seed 全冻结：graph/G0/G1/G2 与 §2 一致；禁 seed search；运行后禁换 seed。
- [ ] oracle 非硬门：9 项同报；`ORACLE_APP_NONMONOTONIC_DIAGNOSTIC`；G2 PASS 只用 APP-fed。
- [ ] 预算完整：P0 + 单 120s + G1 ≤900s + G2 ≤3600s + RSS<2GiB + `RESOURCE_PROJECTION_BLOCKED`；不降点/不并行/不改 max90。
- [ ] 调用数明确：G1 APP 100x2 + oracle 前 20x2；G2 APP 200x3 + oracle 前 40x3；oracle 仅诊断。
- [ ] 文件纪律：恰 7 docs（5 计划 + corrigendum + cycle_state）；3 `.py`、旧 verdict/packet、memory/decision-log、其它代码输出未动；无 hash/checksum/tag 新增。

## 9. 是否可进入 apply

否——条件：D5 R2 独立 Plan Review ACCEPT（含 §8 R2 18 checks 全过）后，
方可按 tasks.md deferred 的 R2 delta（D5-I2-R2 等）逐项另批启动，但仍需新 R2 implementation packet 接受后才动代码；
Review PASS 只变为 `PLAN_ACCEPTED + implementation_authorized:false + synthetic_execution_authorized:false + real_execution_authorized:false`，
不自动授权实现；任何 decoder/VAL/n=1024 真实执行仍需独立授权；禁止一次授权 G0/G1/G2。
`NEXT_GATE: INDEPENDENT_R2_PLAN_REVIEW`（cycle_state.yaml 已同步；旧 verdict/packet 保留不动）。
