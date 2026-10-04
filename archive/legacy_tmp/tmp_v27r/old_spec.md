# Spec: formal-nonbinary-ldpc-v27-finite-leakage-margin-de-gate

> Status: DRAFT delta spec for V27 finite-leakage-margin DE gate. Freeze-review
> pending; nothing is executed until main-thread freeze ACCEPT.

## R1: Architecture & channel (frozen)
- 固定架构 F03 natural（MSB→LSB）：L1 GF(32) + L2 GF(32)，`width=log2(32)=5`。
- 每层从 V25 train `N_ab` / C04 source-delta 构建逐样本条件后验
  `P(U_i | B, source, delay, U_<i)`，true-symbol centering 注入 MC-DE；三 source
  独立；`SOURCE_METADATA` 显式记录 source↔delay（−50/+50/+50, n_pairs）。
- **Bob-full sequential decoding 语义**：下一层只使用 Bob 完整观测 + 公共
  source/delay + 已 Bob 解码并验证的前层；无 Alice-oracle。

## R2: Finite leakage budget (frozen)
- 总泄漏含 **64-bit 公开验证 tag**：`leak_total = (5·m_total + 64)/n` bits/symbol。
- `H_total = H1+H2 = 0.02566205 + 0.80690067 = 0.83256272` bits/symbol（worst-source）。
- 约束 `f = leak_total/H_total <= 1.3` ⇒
  `m_total = floor((1.3·n·H_total − 64)/5)`。
- 冻结预算表：n=1024→m_total=208；n=2048→430；n=4096→873；n=8192→1760。
- `m1_ep=round(m_total·H1/H_total)`、`m2=m_total−m1`；仅测
  `m1 ∈ {m1_ep−2, m1_ep−1, m1_ep, m1_ep+1, m1_ep+2}`。
- 可行性：`0<=m1,m2<=m_total` 且 `R_i=1−m_i/n ∈ (0,1)`；不可行拆分不参与判定。

## R3: Fixed ensemble (frozen)
- `lambda = {2: 1.0}`；每层码率 `R_i = 1 − m_i/n`，用 harmonic-exact concentrated
  check distribution 生成 `rho`。
- 禁止 λ/ρ 搜索、禁止 m1/m2 搜索（只测 ±2 带内）、禁止有限矩阵构造。

## R4: Screen & confirmation (frozen)
- Screen：n_samples=400, max_iter=100, seeds=[27001,27002], tol=0.01 bits, streak=20；
  覆盖 4 n × 5 m1 × 3 source × 2 layer。
- Confirmation：对每个 n 的最先通过拆分，n_samples=2000, max_iter=200,
  seeds=[27101..27105]；通过 = 3 source × 2 layer × 5 seeds 全收敛、无错误/非有限值、
  每层单独留证。

## R5: Terminal states (frozen, one of)
- `pass_finite_budget_ready`：至少一个 n 存在确认通过的 entropy-proportional 拆分。
- `de_pass_no_finite_headroom`：渐近 DE 通过（V26 30/30）但每个 n 的有限预算
  + 仅 ±2 带内均无可用头寸。
- `fixed_ensemble_margin_fail`：机制门失败、或系综在预算内 outright 不收敛、或资源门
  触发。

## R6: Prohibitions
- 不构造有限 parity-check 矩阵；不跑有限 FER/解码器；不做 MET；不做 degree/m1/m2
  搜索；不读 fresh/raw `.ttbin`；不改 factorization/labeling；不用 holdout 调参；
  不 push。**未获 freeze review ACCEPT 前不执行任何 DE。**
