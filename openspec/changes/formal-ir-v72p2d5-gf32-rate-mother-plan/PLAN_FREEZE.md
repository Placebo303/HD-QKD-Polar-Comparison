# V72P2D5 计划冻结报告（PLAN_FREEZE，只读 survey + 冻结结论）

- Change：`formal-ir-v72p2d5-gf32-rate-mother-plan`，Cycle `V72P2D5-GF32-RATE-MOTHER`
- 状态：`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`；`REAL_EXECUTION_AUTHORIZED=false`，
  `DECODER_EXECUTED=false`，`VAL_LOADER_CALLS=0`
- Frozen input：`d=1024, U1/U2=[5,5], GF(32), N=1024`；模型 F；
  `CE_L1=3.814742 / CE_L2_oracle=3.347605 / CE_joint=7.162347`（worst `7.178766`，
  std `0.0158`，range `0.0423`，`lambda*=137.3823795883264`，D4R2 R2 审计）；
  旧 `16/200/216` 行禁真实。
- 本报告是 D5-T7 产出；实现任务未启动；阈值冻结后不得回写。

## 1. 可复用能力表（只读 grep + 签名确认，无执行）

列：函数/文件 | 输入 | 输出 | 任意 m | nested prefix | rank 保证 | 行/列重 | n=1024 绑定 | 700–1000 适配 | 已有测试 | 复用风险

| 函数/文件 | 输入 | 输出 | 任意 m | nested | rank | 行/列重 | n 绑定 | 700–1000 | 测试 | 风险 |
|---|---|---|---|---|---|---|---|---|---|---|
| `nonbinary_field.GF2mField.create(32)`（poly `0b100101=37`）+ `add/mul/inv` | `q=32` | field（exp/log 表） | N/A（与 m 无关） | N/A | N/A | N/A | 否（q-only） | 是（O(1) ops） | `_check_field` 自检 + V35 系 | 低 |
| V31 `build_layer(m,n,family=qc,field)`（`nonbinary_v31.py:624`；支撑 `build_supports_qc_cyclic:394` + `select_projective_ratio_v31` + 审计） | `m,n,family` | `(matrix, audit{rank,full_row_rank,projective_safe,occupancy≤31})` | 是（含 1000；候选对 `m(m-1)/2≫1024`） | 否（per-m 重建；D5 用 `M_max=1000` 单构建+`H[:k]` reinterpretation 实现嵌套） | 是（`full_row_rank+projective_safe` 双审计） | 列重恒 2；行重均 `2n/M`（M=1000→2.05） | 默认 1024，`n` 参数化 | **是（选中基线）** | V31 gate/closeout 审计测试 | 低 |
| V31 `build_matrix_packet(m1,m2_by_source,n)`（`:710`） | `m1, {1M,1p5M,2M}:m2` | L1 + per-source L2 packet | 是 | 否（独立层） | 逐层审计 | 同上 | 同上 | 是（分层独立母矩阵语义与 D5 一致） | 同上 | 低 |
| V28 `build_matrices(config)` + `_build_pair_matrix`（`nonbinary_v28.py:124`）| config(`q,n,m1,m2`) | `h1(6×1024), h2{src}(202×1024)`（历史小 m 值） | 是（参数化） | 否（独立构建；row-prefix 输入被拒） | 小 m 全秩（identity parity half） | degree-2 pairs | 是（config n） | 未验证（仅小 m 实证）→ H1 小矩阵参考 | V28/V29 系 | 中 |
| D3 冻结几何 `nested_geometry()`（`v72p2d3:414`：`H1=16,H_base=184,joint=192,total=200`，leak `1064/1104/1144`） | 无 | 形状/泄漏常量 | 否（冻结 16/184/200） | 是（`184/192/200` 前缀） | rank-16 H1（R5 门要求；全零拒绝） | QC 小矩阵 | 是（N=1024） | 否（即被替代的旧预算） | `test_v72p2d3`（~1800 断言级） | 低（历史对照保留，不扩展） |
| V38 `construct_lane_c_prototype(source,seed,field)`（`:745`，L=8,w=2 banded, dv=2, 4-cycle 回避） | `source,seed` | `(H, metrics{position_permutations})` | 否（`SOURCE_CHECKS`/allocations 小 m 冻结） | 否（单发构建） | 弱（structural metrics，无 V31 级双审计） | dv=2 banded，行重 `≈2n/m` | 是（`BLOCK_LENGTH`） | 否（需重设计分配向量）→ **备份** | V38/V39/V40/V41 系 | 中 |
| V54 `construct_h_inc(source,det_id,delta_m,n)`（`:477`，PEG-like det，行度 cap 16）+ `construct_h_joint1` | `source,delta_m` | `(H_inc,H_support,nnz,row_deg)` | 是（`delta_m` 参数） | 是（`[H_base;H_inc]` + S0..S3 切片） | 无审计（gap） | 行度 ≤16，稀疏 | 是（`BLOCK_LENGTH`） | 待验证（小 Δ 实证，大 m 无审计） | V54 系 | 中 |
| V36 `build_v36_incremental_matrix(H_base,source)`（`:874`，+32 行，行重 10–14） | `H_base` | `(H_mother, {S0..S3})` | 否（固定 +32） | 是（vstack+切片） | 无 | 行重 10–14（700 行下过密，D5 否决） | 是 | 否 | V36 系 | 高（D5 不用） |
| V35 `build_v35_incremental_mother_matrix(base_H)`（`:823`，192→224） | `base_H` | `H_mother(224×1024)` | 否（硬编码 224） | 是（vstack） | 无 | protograph QC | 是 | 否 | V35 系 | 高（D5 不用） |
| `nonbinary_codebook.gf_rank(matrix,field)`（`:56`，pinned 基高斯消元） | 任意矩阵 | `rank: int` | 是 | N/A（验证工具） | 本身即秩判定 | N/A | 否 | 是（`O(m²n)`，配预算执行） | codebook 系 | 低 |
| v35 `decode_row_layered_fftqspa(H(m,n),priors(N,32),syndromes(m,),max_iter,damping,warm_beliefs,field)`（`:483`）→ `DecoderResult(x_hat,syndrome_ok,iterations 0..max,final_beliefs)` | 任意 `m×n` + `(N,32)` | 解码结果（syndrome 等式停止，无 residual tolerance） | 是 | N/A（调用方切片） | N/A | 任意（每 check `q=32` FWHT） | 否（任意 n） | 是（计算可行，700+ 行 runtime 未实测→R2 风险） | V28/V31/V35/D3 系广泛覆盖 | 低-中 |
| V54 `get_l1_prior_p_u1_given_b(counts(1024,1024),bob)`（`:408`，`reshape(32,32,1024)` 求和） | counts+bob | `(N,32)` | N/A | N/A | N/A | N/A | 否（任意 N） | 是 | V54/D3/D4 系（含转置反例） | 低 |
| V54 `get_l1_app_prior_l2(counts,bob,q(N,32))`（`:432`，`q@P`）+ `softmax_beliefs`（`:453`） | counts+bob+q | `(N,32)` | N/A | N/A | N/A | N/A | 否 | 是 | 同上 | 低；delta 见下 |
| v35 `get_conditional_posterior_l2(counts,bob,u1_true)`（`:279`，oracle） | counts+bob+u1 | `(N,32)` | N/A | N/A | N/A | N/A | 否 | 是（诊断用） | V35/V38 系 | 低 |
| D3 `build_canonical_counts / symbols_to_layers / layers_to_symbols / build_stage1_P / build_stage2_P / ce_*_log2`（`v72p2d3:298–604`）+ 生产包装 `get_l1_prior_production / build_l2_prior_from_l1`（V54 精确复用） | CAL symbols / counts | counts+ prior 表 + CE | N/A | N/A | N/A | N/A | N=1024（R5 系；synthetic 小 n 另行缩放） | 是 | `test_v72p2d3/v72p2d4*` | 低 |
| CLI/test 入口：`scripts/v72p2d3_gf32_contrast.py`，`scripts/v72p2d4*_audit.py`，`comparison_bench/tests/test_v72p2d3*.py/test_v72p2d4*.py`，`cli/run_v35*/run_v37*/run_nonbinary_v31_gate.py` 等 | — | — | — | — | — | — | — | D5 新增 CLI+test 各一（deferred） | — | 低 |

**关键结论**：选中基线 = V31 QC-cyclic-projective `build_layer`（唯一“任意 m + n=1024 已验证 +
确定性可重放 + occupancy 硬门 + 双秩审计”且大 m 更稀疏的构造器）；
700–1000 行适配方式 = 单层 `M_max=1000` 一次构建 + 行前缀披露（ reinterpretation，无需改构造器）。

## 2. 行数表（权威：分层独立 ceil）

`rows=ceil(N*CE*f/5)`，F 均值 `L1 3.814742 / L2 3.347605 / joint 7.162347`。

### n=1024（真实目标）

| f | m1 (L1) | m2 (L2) | m1+m2 | joint-ceil（对照） | 旧预算缺口 |
|---|---|---|---|---|---|
| 1.0 | 782 | 686 | 1468 | 1467 | L1 −766 / L2 −486 / Tot −1251 行 |
| 1.05 | 821 | 720 | 1541 | 1541 | 同上口径 |
| 1.1 | 860 | 755 | 1615 | 1614* | 同上口径 |
| 1.2 | 938 | 823 | 1761 | 1761 | 同上口径 |
| (参1.3) | 1016 | 892 | 1908 | 1907* | Tot −1691 行（D4R2 一致） |

`*` 差 1 行为 ceil 伪影，权威取 `m1+m2`。worst joint → 1471 行（+4）；std ≈ 4 行；range ≈ 9 行。
bit 对比：L1 需 3906 vs 旧 80；L2 需 3428 vs 旧 1000；Total 需 7334 vs 旧 1080（6.79 倍不足）。

### scaled 门控行数（同公式）

- n=64：f=1.0 `m1=49/m2=43/joint-ceil=92`；f=1.2 `m1=59/m2=52/joint=111`。
- n=256：f=1.0 `m1=196/m2=172/joint=367`；f=1.1 `215/189/404`；f=1.2 `235/206/441`。

## 3. prior 对齐结论

对齐 + 单 delta：下游（`reshape` 求和 / `q@P` / `(N,32)` / `max90/damping1.0/cold`）逐字复用 V54/v35；
delta 仅为 `counts → P_F` 前插入 frozen `lambda*=137.3823795883264` 平滑（D3 `_smooth_counts` 语义）。
floor 双轨（审计 `1e-300` / decoder `1e-15`，均重归一）与 oracle-vs-生产区分（§1.5）已冻结。

## 4. 嵌套 mother（一句话）

每层一次性构建单个 `(1000,1024)` GF32 矩阵并按冻结披露集取行前缀 `H[:k]`，
一切已披露前缀满行秩、稀疏（列重 2 / 行重 2–4 / occupancy≤31）、后增行不改前缀、
L1 先收敛再开 L2、披露 API 为 `m_max + prefix_rows + extra_rows|None` 最小三元组。

## 5. 门控与生死实验摘要

- G0 tiny：数学正确性（`<1e-12` 边际/条件，`<1e-10` 链式，无噪 100%）。
- G1 n=64：集成趋势门（单调 + oracle≥APP + 零 crash），无杀权。
- G2 = 唯一生死实验：n=256 matched synthetic，真 prior，V31-QC 按 n=256 构建、
  `f∈{1.0,1.1,1.2}` 三点（`m1={196,215,235}`，`m2={172,189,206}`），≥200 blocks；
  PASS = `f=1.2` 端到端精确恢复 ≥90% 且单调且 oracle≥APP；FAIL 即放弃（`<50%` 路由死 /
  `50–90%` 预算内不足），后继仅 `d=256` backlog。
- n=1024 真实前置：G0+G1+G2 全过 + Pre-EXECUTE review。

## 6. 修改文件清单（仅 openspec，无生产代码）

新增（5 文件，均在本 change 目录）：

1. `openspec/changes/formal-ir-v72p2d5-gf32-rate-mother-plan/proposal.md`
2. `openspec/changes/formal-ir-v72p2d5-gf32-rate-mother-plan/design.md`
3. `openspec/changes/formal-ir-v72p2d5-gf32-rate-mother-plan/tasks.md`
4. `openspec/changes/formal-ir-v72p2d5-gf32-rate-mother-plan/specs/spec.md`
5. `openspec/changes/formal-ir-v72p2d5-gf32-rate-mother-plan/PLAN_FREEZE.md`（本文件）

修改：零（无既有文件改动）。删除：零。
git 状态/提交：本环境无 shell 执行工具，无法运行 `git status/commit`；
请 main thread 代为执行 `git status --short` 核对仅上述 5 个新增文件后提交
（建议信息 `docs(v72p2d5): freeze GF32 rate-mother plan, no code, no execution`）。
`docs/` 下无新增（报告已按任务书允许置于 change 目录）。

## 7. 剩余风险 / open questions

- R1 生产 `q@P` 相对 oracle 的 L1 传播税（行数表基于 oracle，只会更紧）。
- R2：700–1000 行 FFT-QSPA runtime 未实测。
- R3：V31 前缀秩需逐 `k∈K` 验证；亏秩的唯一修复是换 family 参数（另立修订）。
- R4：`lambda*` 为 outer-mean 单值；synthetic 真值直接采用，真实阶段重拟合沿 D4 口径另批。
- OQ1（单点决策）：per-layer `M_max=1000` 解读是否接受？若否→维持 route C，无实现。
- OQ2：G2 的 90% PASS 线是否接受（备选 80%/95%，改线需重审）？

## 8. 是否可进入 apply

否——条件：D5-T8 独立 Plan Review ACCEPT（含 OQ1/OQ2 决策）后，方可按 tasks.md deferred
的 D5-I1..I5 逐项另批启动；任何 decoder/VAL/n=1024 真实执行仍需独立 EXECUTE_AUTH。
