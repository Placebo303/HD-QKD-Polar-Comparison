# Design: formal-nonbinary-ldpc-v14-efficiency-gate

> 状态：FROZEN CANDIDATE — 第 5 节依据 DE 调研子代理报告定稿；提交独立
> freeze review（V14-P06）后，review ACCEPT 前禁止任何执行。

## 1. 冻结信道模型（本 design 中先冻结，不依赖 DE 机制调研）

- **来源**：V13 修正后 D01 聚合（128 个 bw200 characterization 帧、
  32768 符号；bursts_runs 修正值见 decision-log 2026-08-14 条目）。
- **形式**：GF(1024) 上经验符号差分分布 `w[d] = P(alice XOR bob = d)`，
  由 characterization 帧**只读重算**全 1024-bin 直方图得到（D01 包只存
  32-bin 分桶，全 bin 需重算；重算属 D01 邻近聚合，不触发解码器）。
- **光滑化（冻结规则）**：`w' = (1-λ)·w_emp + λ·u`，其中 `u` 为 GF(1024)
  均匀分布，`λ = 1e-3`（floor 目的；λ 冻结，不允许按结果调整）。
- **Cross-fit 纪律**：仅用 characterization 帧拟合；development/audit 帧
  与 audit truth 永不参与；拟合产物是公开全局聚合（1024 个数 + λ +
  SHA-free 描述），持久化为 `structured_channel_model.json`（schema
  `nbldpc_v14_channel_model_v1`）。
- **对照**（门内证据，非拟合）：经验条件熵 H(w') ≈ 0.547 bits/symbol；
  QSC p=.20 模型熵 2.722；两者差值即"结构化先验的理论收益上限"。

## 2. 门的判定目标（冻结）

- **码率点（冻结）**：m ∈ {15, 16, 17, 18}（n=256、q=1024，码率
  R = 1 − m/256 ∈ {0.9414, 0.9375, 0.9336, 0.9297}；对应
  f = (m·10/256)/H(w') ∈ {1.071, 1.143, 1.214, 1.286}，全部 ≤ 1.3 的
  目标）。m=14 恰在 SW 边界（f=1.0），冻结排除。
- **候选度分布（冻结，共 3 个 λ，边视角、低度）**：
  ① `λ = {2:0.25, 3:0.30, 4:0.45}`（均值 d_v≈3.2）；
  ② `λ = {2:0.20, 3:0.25, 5:0.55}`；
  ③ `λ = {3:0.3, 4:0.7}`（近正则）。
  校验侧 ρ 由 `concentrated_check_distribution`（V9-common 谐波精确解）
  在每个码率点精确锁定。合计 ≤ 12 个**点评估**（3 λ × 4 码率），不做
  profile 搜索。
- **判定式（规则先冻结，数值由测量决定）**：对每个 (λ, m) 点运行 DE；
  **PASS** 当且仅当：Stage 0 机制回归通过（§3）**且** 存在一个点满足
  (a) 平均 base-q 校验消息熵 ≤ 0.01 并连续 20 次迭代维持（max_iter ≤
  150）——收敛判据照搬 V9A 冻结预算；(b) 其 f_achieved ≤ 1.3。
  **FAIL**：全部 12 点不收敛。禁止"最接近"、禁止测量后改规则/加候选、
  禁止重跑换种子。
- **历史教训的规避**：不预承诺不可达的门限数值（V10 的 .22/.32 之误）；
  不零候选搜索（V9A 之误）——候选集小而冻结、且以 Stage 0 回归先行；
  不继承其他 change 的门（V11 之误）。

## 3. 验证门 Stage 0（机制回归，先于 Stage 2 执行）

- 用扩展后的 DE 机制在 **QSC 模式**下复现 V8-60 已接受的参考点（Müller
  et al. 2024 Table 1 行 0.75：q=4、R=0.75、**发表门限 0.069**；V8-60 修正
  运行的计算 proxy 为 0.06242、|δ| = 0.00658 ≤ 0.012）。Stage 0 的判定：
  本机制的计算 proxy 与发表值 0.069 的 |δ| ≤ 0.012。
  复现失败 = 机制未验证 → Stage 2 不得执行，
  `gate_state=mechanism_unverified`（或 `failed_reference`）冻结。

## 4. 输出、路径与测试

- 门证据（加法，沿 V9/V10/V11 先例放 change 的 evidence 目录）：
  `openspec/changes/formal-nonbinary-ldpc-v14-efficiency-gate/evidence/` 下：
  `v14_structured_channel_model.json`（w'、H、折叠规则 φ）、
  `v14_stage0_q4_qsc_regression.json`、`v14_stage1_structured_smallq.json`、
  `v14_stage2_q1024_threshold.json`（12 点逐一结果）、
  `v14_gate_decision.json`（schema `nbldpc_v14_gate_decision_v1`，镜像
  v10_gate_decision 的机械计算风格：gate_state ∈ {pass, fail,
  mechanism_unverified} + 每点数值）、`v14_gate_manifest.json`（命令、
  git commit、预算消耗）、`v14_replay_evidence.json`（严格字节比对回放）。
  证据目录内不使用 <run_id> 子目录（本 change 内单次执行 + 单次回放）。
- 不写 `formal_ir_methods/` 官方资格根；不覆盖任何既有输出；V13 产物
  不动。
- 测试：`workspace/nbldpc_v14_<uuid>/` + `pytest -p no:cacheprovider`；
  T0 编译/导入/结构；T1 信道模型（光滑化、归一化、cross-fit 断言、
  折叠 φ 的 QSC 极限）；T2 机制回归（小 q 玩具信道 DE vs 暴力/闭式
  对照、QSC 模式与 V8 常数一致）；T3 fake gate lifecycle（fake DE 注入，
  证明测试不进真实长计算）。
- 研究代码策略：无 hash DAG/签名/锁；预算与停止规则见第 5 节。

## 5. DE 机制与预算（依据 DE 调研子代理报告定稿）

- **实现形态（不修改已归档 V9/V8/V11 源码）**：新增模块
  `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v14_mcde.py`，
  以 import 复用 V9 的更新核（`variable_update_mcde` /
  `belief_update_mcde` / `entropy_base_q`，已接受任意 (N,q) 先验矩阵），
  在新模块内实现与 `nonbinary_v9_mcde.run_mcde`（`:414`）同构的循环，
  其信道生成块（对应 V9 `:446-457`，QSC-only）改为 `channel_mode` 分支：
  `"qsc"` 保持原文语义；`"structured"` 时 `diffs = rng.choice(q,
  size=n_samples, p=w)`，样本 i 的先验行 `channel[i,j] = w[j XOR diff_i]`
  （误差域居中）。**T2 等价性测试**证明 QSC 模式下新循环与 V9
  `run_mcde` 输出一致（同种子、逐字段），保证结构化分支的机制可信且
  V9 归档证据字节不受影响。
- **Stage 0（S1，机制回归）**：QSC 模式复现 V8-60 已接受参考点
  （`REPRODUCTION_Q=4`、`REPRODUCTION_RATE=0.75`、n_samples=100000、
  max_iter=150；门限 0.069 ± 0.012）。失败 → `failed_reference` 停止，
  S2 禁止。
- **Stage 1（结构化小 q 验证，非外推）**：折叠同态 φ_m(d) = d mod 2^m
  （m ∈ {2,3,4}，XOR 位序保持），`w_small[d'] = Σ_{a: φ(a)=d'} w[a]`；
  验证归一化、QSC 极限（均匀非零 → QSC）、熵比单调。目的：廉价验证
  结构化机制与折叠配方，**不用小 q 外推 q=1024 门限**。
- **Stage 2（q=1024 点评估）**：12 点（3 λ × 4 码率）结构化先验 DE；
  n_samples=1e4、max_iter=150、收敛判据 熵≤0.01 连续 20 迭代（V9A
  预算同源）。成本：单点 ≈118 s（numba 基准 1.181 s/500样本×30迭代
  ×20×5 外推，dc≈53 高校验度预计再 ×10 → 单点 ~20 min，12 点 ~4 h）。
- **预算与停止（冻结数字）**：单运行峰值 RSS ≤ 3 GiB（V9_RSS_CAP_BYTES）；
  wall ≤ 24 h；execute exactly-once + 一次严格字节回放（V9/V10/V11
  先例）；测量后禁止调参/加候选/改规则。
- **预注册降级链（仅预算超限触发，按序）**：① Li-Fair-Krzymień TIT 2009
  单参数高斯近似 DE；② Cohen-Raviv-Cassuto TIT 2019 位面分解（与本数据
  MSB→LSB 单调失配同构）；③ 否则 `resource_blocked`（门值不变，原因
  记录）。绝不在未触发时使用，绝不静默外推。

## 6. Claim boundary

- DE 收敛 ≠ 有限码可解码；PASS 只授权 **V15 立项**（高码率候选的
  合成资格研究），不授权任何 fresh/real/promotion 声明。
- `promoted`、`qualified`、`observed_fresh_correction` 在本 change 禁止。
- 门失败是**不可变**结果：证据保留，结论记录进 decision-log 与记忆。
