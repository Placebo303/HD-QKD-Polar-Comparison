# Design: formal-nonbinary-ldpc-v27-finite-leakage-margin-de-gate

> Status: DRAFT_PENDING_FREEZE_REVIEW（2026-08-19；只写文档，不执行）。
> 继承：V26 channel-informed multilevel DE gate（A02 F03 GF32+GF32 渐近 f=1.3 收敛 30/30）
> 与 V25 经验信道 `P(A|B, source, delay)` / `channel_counts.npz`。

## 1. 架构与信道（冻结，继承 V26 A02）

- 架构：**F03 natural（MSB→LSB），L1 GF(32) + L2 GF(32)**，`width = log2(32) = 5`
  bit/symbol/层。
- 信道：从 V25 train `N_ab`（`channel_counts.npz`）构造每层逐样本
  `P(U_i | B, source, delay, U_<i)` 的条件后验，true-symbol centering 注入
  MC-DE；三 source（1M/1p5M/2M）独立，`SOURCE_METADATA` 显式记录
  `delay_used_ps = -50/+50/+50`、`n_pairs`。不重估亚 bin delay。
- **Bob-full sequential decoding 语义**：第 i 层只使用完整 Bob 观测 B + 公共 Z
  （source/delay）+ 已被 Bob 解码并通过验证的前层；该语义是 DE/率账的建模前提，
  **不是** Alice-oracle（与 V26 design §1 一致）。每层 syndrome + 公共 tag 进入
  总泄漏。

## 2. 有限泄漏预算（冻结公式）

总泄漏（bits/symbol，含 64-bit 公开验证 tag）：

\[
\mathrm{leak}_{\mathrm{total}}=\frac{5\,m_{\mathrm{total}}+64}{n}
\]

- `m_total = m1 + m2`：两个 GF32 层**整数** syndrome 行数之和（每行 5 bit）。
- `64`：**每块**公开验证 tag 的 bit 数，计入总泄漏。
- `n`：块长（GF32 符号数）。

总效率 `f = leak_total / H_total`，用 **worst-source** 条件熵
`H_total = H1 + H2 = 0.02566205 + 0.80690067 = 0.83256272` bits/symbol。
约束 `f <= 1.3` ⇒

\[
5\,m_{\mathrm{total}} \le 1.3\,n\,H_{\mathrm{total}} - 64 \quad\Rightarrow\quad
m_{\mathrm{total}} = \left\lfloor \frac{1.3\,n\,H_{\mathrm{total}} - 64}{5} \right\rfloor
\]

冻结预算表（worst-source `H_total`）：

| n    | m_total | m1_ep (entropy-proportional) | m2_ep = m_total − m1_ep | R1 = 1−m1/n | R2 = 1−m2/n | 实现总 f (含 64-bit tag) |
|-----:|--------:|----------------------------:|------------------------:|------------:|------------:|-------------------------:|
| 1024 | 208     | 6                           | 202                     | 0.99414     | 0.80273     | ≈1.29495 |
| 2048 | 430     | 13                          | 417                     | 0.99365     | 0.79639     | ≈1.29847 |
| 4096 | 873     | 27                          | 846                     | 0.99341     | 0.79346     | ≈1.29876 |
| 8192 | 1760    | 54                          | 1706                    | 0.99341     | 0.79175     | ≈1.29964 |

实现总 f 均 < 1.3（正但很小的 margin）：这是 64-bit tag 占掉部分预算后的真实头寸。
`m1_ep = round(m_total · H1/H_total)`，`m2_ep = m_total − m1_ep`。

约束：任意拆分必须满足 `0 <= m1, m2 <= m_total` 且 `R1, R2 ∈ (0,1)`（即
`m1, m2 < n`）；不满足的 n/拆分记为不可行，进入 no-headroom / fail 判定。

## 3. 固定系综（冻结）

- 变量度分布冻结 `lambda = {2: 1.0}`。
- 每层码率由拆分决定：`R_i = 1 − m_i / n`（GF32 每行 5 bit，`R = 1 − leak/width`
  与 V26 `target_rate_layer` 同源）。用 harmonic-exact concentrated check
  distribution 生成对应 `rho`（GF32 域；`R1≈0.9934–0.9941` 时 dc≈303–342，
  `R2≈0.79–0.80` 时 dc≈9–10，均在 DEGREE_MAX 内）。
- **只测 entropy-proportional 拆分及其 ±1、±2**：
  `m1 ∈ {m1_ep−2, m1_ep−1, m1_ep, m1_ep+1, m1_ep+2}`，`m2 = m_total − m1`；
  不做任何 m1/m2 搜索。总 f 与拆分无关（`m_total` 固定），拆分只改变每层 `f_i` 与
  各层收敛性。

## 4. Screen（M2 / 每个 n × 每个 m1 拆分）

```
n_samples   = 400
max_iter    = 100
seeds       = [27001, 27002]
entropy_tol_bits = 0.01
streak      = 20
```

覆盖：4 n × {5 种 m1} × 3 source × 2 层 × 2 seeds。判定通过 = 某 (n, m1) 下所有
source、所有层、两个 seed 都收敛（final mean entropy ≤ 0.01 bits/symbol 连续 20 轮）。

## 5. Confirmation（M3 / 每个 n 上一名通过拆分）

```
n_samples   = 2000
max_iter    = 200
seeds       = [27101, 27102, 27103, 27104, 27105]
```

对每个 n，取 screen 中最先通过（按 m1 升序）的拆分做 5-seed confirmation；通过 =
3 source × 2 层 × 5 seeds 全收敛且无错误/非有限值。若无任何 screen 通过点，该 n
不运行 confirmation。

完成调用的累计资源上限沿用 24h 门（`RESOURCE_LIMIT_SECONDS`），超限 →
`fixed_ensemble_margin_fail` 前的资源阻塞分支（与 V26 `resource_blocked` 语义一致，
但 V27 终态集合不含独立 `resource_blocked`，资源阻塞并入 `fixed_ensemble_margin_fail`
并在 dir 中记录 blocked=true）。

## 6. 终态（M4）

- `pass_finite_budget_ready`：至少一个 n 存在确认通过的 entropy-proportional
  拆分（3 source × 2 层 × 5 confirm seeds 全收敛），此时该 n 的
  `(m_total, m1, m2, R1, R2, f_realized)` 为该 n 的可提出有限构造预算。
- `de_pass_no_finite_headroom`：V26 渐近每层 f=1.3 DE 仍全收敛（机制有效），但每个 n
  在有限整数预算 + 64-bit tag + 仅 ±2 拆分带内都无可用头寸：或预算表无可行拆分
  （m_i≥n / R_i≤0），或 screen/confirmation 全部不收敛（预算太紧）。给出结论：渐近
  通过但有限块头寸不足，有限构造 change 暂不提出。
- `fixed_ensemble_margin_fail`：任一机制门（M0/M1）不过，或固定系综在预算内 outright
  不收敛（非头寸不足而是系综本身失败），或资源门触发。报告失败拆分数与最小熵值。

判定优先级：机制门失败 → `fixed_ensemble_margin_fail`；某 n 确认通过 →
`pass_finite_budget_ready`（任一 n 命中即成功）；否则若渐近 DE（V26 复测）通过 →
`de_pass_no_finite_headroom`；否则 → `fixed_ensemble_margin_fail`。

## 7. 禁止项

不实现有限 parity-check 矩阵、不跑有限 FER/解码器、不做 MET、不做 λ/ρ 或 m1/m2
degree 搜索、不读 fresh/raw `.ttbin`、不改 factorization/labeling、不用 holdout
调参、不 push。**本 change 在 freeze review ACCEPT 前不执行任何 DE。**
