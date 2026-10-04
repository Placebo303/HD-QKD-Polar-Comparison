# Spec: formal-nonbinary-ldpc-v27-finite-leakage-margin-de-gate  (V27R revision)

> Status: V27R delta spec（source-adaptive 修订）。独立 freeze review 已 ACCEPT（2026-08-20），
> 主线程已记录 P102 ACCEPT。/ V27 是 asymptotic true-predecessor-conditioned
> multistage DE (L2 conditioned on correct L1); 单个 64-bit tag 只计入整块总泄漏，
> 不在层间使用。

## R1: Architecture & channel (frozen)
- 固定架构 F03 natural（MSB→LSB）：L1 GF(32) + L2 GF(32)，`width=log2(32)=5`。
- 每层从 V25 train `N_ab` / C04 source-delta 构建逐样本条件后验
  `P(U_i | B, source, delay, U_<i)`，true-symbol centering 注入 MC-DE；三 source
  独立；`SOURCE_METADATA` 显式记录 source↔delay（−50/+50/+50, n_pairs）。
- **asymptotic true-predecessor-conditioned multistage DE**：L2 条件于**已正确解码的
  L1**（true-predecessor-conditioned）；不模拟有限码错误传播；无 Alice-oracle。
  单个 **64-bit 公开验证 tag** 只计入整块总泄漏，**不在层间使用**。
- **source/delay 语义**：source/delay 是公开 acquisition selector，只用于选择后验
  population 与 syndrome 预算；**不是逐符号公开 side information，不额外重复计费**。

## R2: Finite leakage budget (frozen, source-adaptive)
- 总泄漏含 **64-bit 块级公开验证 tag**：`leak_total = (5·m_total + 64)/block_len`
  bits/symbol。tag 计入整块总泄漏，不在层间使用。
- **source-adaptive**：每 source 用自己的 full-precision `H_source = H1+H2`；
  `m_total = floor((1.3·block_len·H_source − 64)/5)`。
- 冻结预算表（block_len=1024/2048/4096/8192 → m_total）：
  - 1M: 200 / 413 / 840 / 1693
  - 1p5M: 206 / 426 / 866 / 1745
  - 2M: 208 / 430 / 873 / 1760
- `m1_ep = round(m_total·H1/H_source)`（Python `round`，round-half-to-even，冻结明确
  规则）；只测 `m1 ∈ {m1_ep−2, m1_ep−1, m1_ep, m1_ep+1, m1_ep+2}`，`m2 = m_total−m1`；
  **五个候选全部有晋级资格**。
- 合法性：`0<=m1,m2<=m_total` 且 `R_i=1−m_i/block_len ∈ (0,1)`；非法候选不参与排序/
  确认。冻结表所有候选合法。
- `block_len` 与 `mc_samples` 是两个不同字段（不混用）。

## R3: Fixed ensemble (frozen)
- `lambda = {2: 1.0}`；每层码率 `R_i = 1 − m_i/block_len`，用 harmonic-exact
  concentrated check distribution 生成 `rho`（GF32 域，DEGREE_MAX 内，由 planner
  校验）。
- 禁止 λ/ρ 搜索、禁止 m1/m2 搜索（只测 ±2 带内）、禁止有限矩阵构造。

## R4: Screen & confirmation (frozen)
- Screen：mc_samples=400, max_iter=100, screen_seeds=[27001,27002], local tol=0.01
  bits, streak=20；覆盖 4 block_len × 3 source × 5 候选 × 2 层。**screen 完整执行
  全部候选后再进入 confirmation。**
- candidate_id=`(block_len, source, m1)`；去重（同 id 合并）；排序 keys 升序：
  1) worst_final_entropy, 2) mean_final_entropy, 3) abs(offset), 4) m1。
- Confirmation：对每个 (block_len, source) 按排序**从第 1 名依次确认**；失败继续
  下一个直到通过或 5 个全失败。单候选通过 = 2 层 × confirm_seeds
  [27101..27105]（mc_samples=2000, max_iter=200, tol=0.01, streak=20）全收敛且无
  错误/非有限值。
- **pass**：存在同一 block_len 使 1M/1p5M/2M 三 source 均有确认通过候选；多块长满足
  取最小 block_len。

## R5: Terminal states (frozen, only-one-of)
- `pass_finite_budget_ready`：存在同一 block_len，三 source 均有确认通过候选。
- `de_pass_no_finite_headroom`：渐近机制有效（继承 V26 30/30）但每个 block_len 三
  source 无法同时获得确认通过候选（有限预算太紧 / ±2 带内无头寸）。
- `implementation_blocked`：budget planner / wrapper / 资源实现被阻塞。
- `resource_blocked`：24h 全局 completed-call 累计资源门触发。
- 优先级：先查实现/资源阻塞，再无阻塞时找 passing block_len。

## R6: Resource gate & V26 relation (frozen)
- **24h 全局 completed-call 累计资源门**：`RESOURCE_LIMIT_SECONDS`，按已完成 DE 调用
  累计耗时计；超限 → `resource_blocked`，dir 记录 blocked=true。
- checkpoint 必须绑定完整 frozen configuration（预算表、rounding、候选、参数、排序、
  终态、资源门），可完整重建，禁止"换配置重跑"。
- V26 仅作 archived reference；**禁止重跑 V26 DE**；V27 只做最小 budget planner +
  V26 MC-DE adapter wrapper，不复制/重写 V26 内核。

## R7: Prohibitions
- 不构造有限 parity-check 矩阵；不跑有限 FER/解码器；不做 MET；不做 degree/m1/m2
  搜索；不重跑 V26；不读 fresh/raw `.ttbin`；不改 factorization/labeling；不用
  holdout 调参；不 push。**未获主线程 P102 ACCEPT 前不执行任何 DE；ACCEPT 后一次
  执行、独立只读 verifier、不调参不重跑、不覆盖现有 output root。**
