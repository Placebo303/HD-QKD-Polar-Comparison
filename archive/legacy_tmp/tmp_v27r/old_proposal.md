# Proposal: formal-nonbinary-ldpc-v27-finite-leakage-margin-de-gate

> Status: **DRAFT_PENDING_FREEZE_REVIEW（2026-08-19；只创建 OpenSpec，不执行）**。
> 上游：V26 `pass_target_f13`（A02 / F03 GF32+GF32 在 f=1.3 下 30/30 全收敛，
> 独立只读 verifier 复核通过，V26 已归档）。
> 本 change 是 V26 的**有限泄漏头寸（finite-leakage-margin）**门：在真正有限块长、
> 整数码率预算、且计入 64-bit 公开验证 tag 的前提下，检验固定系综在 A02 上还剩多少
> 收敛头寸，再决定能否提出有限构造 change。**V27 只写 OpenSpec，不实现、不执行。**

## What

把 V26 已证明的 A02 渐近 DE 结论推进到**有限块长整数预算**：
1. 对每个冻结块长 `n ∈ {1024, 2048, 4096, 8192}`，按总效率上限 `f <= 1.3`（含
   每块 64 bit 公开验证 tag 计入总泄漏）解出**整数**总码字数 `m_total`。
2. 只按 **entropy-proportional** 拆分 `m1/m2`（以及 `m1±1、m1±2`，`m2=m_total-m1`）
   测试 DE；不做任何 m1/m2 搜索。
3. 每个 n 上测试：固定 `lambda={2:1}` + harmonic-exact concentrated checks、
   Bob-full sequential decoding 语义、source/delay-conditioned 经验后验、
   screen seeds 27001–27002、confirmation seeds 27101–27105。
4. 输出每个 n / 每个 m1 拆分的收敛信息与总 f（含 tag），收敛 → 终态之一：
   `pass_finite_budget_ready` / `de_pass_no_finite_headroom` / `fixed_ensemble_margin_fail`。

效率定义与 V26 一致（单位 bits/symbol；`width = log2(q) = 5` 对 GF32 层）：

\[
f=\frac{\mathrm{leak}_{\mathrm{total}}}{H_{\mathrm{total}}},\qquad
\mathrm{leak}_{\mathrm{total}}=\frac{5\,m_{\mathrm{total}}+64}{n},\qquad
H_{\mathrm{total}}=H_1+H_2
\]

（`5 m_total` = 两个 GF32 层的 syndrome bits，`64` = 公开验证 tag bits；`n` = 块长
符号数。）

## Why

- V26 `pass_target_f13` 授权**提出** A02 有限码/构造 change，但提出前必须先回答：
  "有限块长 + 整数码字数 + 64-bit 验证开销"下是否还有正泄漏头寸（margin）。
- 若某 n 与某 entropy-proportional 拆分能收敛 → `pass_finite_budget_ready`，
  允许下一步提有限构造（仍无 FER/qualification/promotion）。
- 若渐近 DE 没问题（V26 30/30）但有限预算下每个 n 的头寸都不足/不可行 →
  `de_pass_no_finite_headroom`（机制有效、预算太紧）。
- 若固定系综在预算内直接不收敛 → `fixed_ensemble_margin_fail`。

## Scope

- 只复用 V26 的 A02（F03 natural，GF32+GF32）channel-informed posterior 注入与
  MC-DE 内核；不加新内核。
- 有限整数预算平面：`m_total = floor((1.3·n·H_total − 64)/5)`（worst-source
  `H_total`）；只测 entropy-proportional 拆分 `m1 ∈ {m1_ep−2 … m1_ep+2}`。
- `H_total` 取 A02 最差 source 的两层条件熵之和（`H1+H2`
  = 0.02566205 + 0.80690067 = 0.83256272 bits/symbol）。
- Bob-full sequential decoding 语义：下一层只依赖 Bob 已解码并验证的前层，DE 端
  无 Alice-oracle。

## Out of scope（V27 不应做什么）

- **不执行**：本 change 在 freeze review ACCEPT 前只写文档，不运行任何 DE。
- 不做 degree 搜索 / 撞库；不做有限 parity-check 矩阵构造；不做有限 FER/解码器；
  不做 MET；不做 fresh/raw `.ttbin` 读取；不改 factorization/labeling；不用
  holdout 调参；不 push。

## Decision states (终态，仅允许以下之一)

- `pass_finite_budget_ready`
- `de_pass_no_finite_headroom`
- `fixed_ensemble_margin_fail`
