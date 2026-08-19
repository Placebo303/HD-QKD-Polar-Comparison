# Proposal: formal-nonbinary-ldpc-v27-finite-leakage-margin-de-gate  (V27R revision)

> Status: **V27R DRAFT — source-adaptive 修订版，PENDING_FREEZE_REVIEW（2026-08-19；只创建
> OpenSpec，不执行）**。本文档由 2026-08-19 V27R revision 取代本 change 内先前
> worst-source 草案；在 Luna worker 独立 freeze review ACCEPT 且主线程记录 P102 ACCEPT
> 前**不实现、不执行任何 DE**。
> 上游：V26 `pass_target_f13`（A02 / F03 GF32+GF32 在 f=1.3 下 30/30 全收敛，独立只读
> verifier 复核通过，V26 已归档，仅作为 archived reference——**禁止重跑 V26 DE**）。

## What

把 V26 已证明的 A02 渐近多级 DE 结论推进到**有限块长、整数码率预算、且计入 64-bit
公开验证 tag** 的 **source-adaptive finite-leakage-margin** 门：

1. **source-adaptive 预算**：每个 source（1M / 1p5M / 2M）使用自己完整的 H1/H2
   （full-precision，来自 V25 `channel_counts.npz`），对每个冻结块长
   `block_len ∈ {1024, 2048, 4096, 8192}` 解整数 `m_total`：
   `m_total = floor((1.3·block_len·H_source − 64)/5)`（H_source=该 source 的 H1+H2，
   full-precision，不共享 worst-source 常数）。
2. **m1_ep + ±2 带**：对每个 (source, block_len)，按冻结明确 rounding 规则
   `m1_ep = round(m_total·H1/H_total)`（Python `round`，round-half-to-even）取
   entropy-proportional 拆分；只测 `m1 ∈ {m1_ep−2, m1_ep−1, m1_ep, m1_ep+1, m1_ep+2}`，
   `m2 = m_total − m1`。**五个候选全部有晋级资格**（不做任何 m1/m2 搜索）。
3. **asymptotic true-predecessor-conditioned multistage DE**：V27 是渐近 DE，L1 正确
   时条件于 L1 计算 L2（true-predecessor-conditioned）；**不模拟有限码错误传播**。
   单个 64-bit tag 只计入整块总泄漏，**不在层间使用/只作用在块级总账**。
4. **source/delay 语义**：source/delay 只是公开 acquisition selector，仅用于选择
   后验 population 与 syndrome 预算；**不是逐符号公开 side information，不额外重复
   计费**。
5. **pass 定义**：存在同一个 `block_len`，使三个 source（1M/1p5M/2M）在该
   block_len 下**均**有确认通过的候选 → `pass_finite_budget_ready`。
6. 终态仅允许：`pass_finite_budget_ready` / `de_pass_no_finite_headroom` /
   `implementation_blocked` / `resource_blocked`。

## Why

- 前版（worst-source 单一预算）用 2M 的 H_total 给所有 source 配预算，低估了 1M/1p5M
  的真实 headroom；V27R 改为 **source-adaptive**，每个 source 用自己的全精度熵，能对
  每个 source 公平回答"在该块长、整数码率、64-bit 验证开销下的有限泄漏头寸"。
- 需在真正有限块长 + 整数码字数 + 64-bit 公开验证 tag 下检验固定系综还剩多少收敛
  头寸，再决定能否提出有限构造 change。
- 若某 block_len 三 source 全有确认通过候选 → `pass_finite_budget_ready`，允许下一步
  提有限构造（仍无 FER/qualification/promotion）。
- 若渐近 DE 机制有效（继承 V26 30/30）但每个 block_len 三 source 都无法同时获得确认
  通过候选（预算太紧/±2 带内无可用头寸）→ `de_pass_no_finite_headroom`。
- 若实现/资源层面被阻塞 → `implementation_blocked` / `resource_blocked`（24h 全局
  completed-call 资源门）。

## Scope

- 只复用 V26 的 A02（F03 natural，GF32+GF32）channel-informed posterior 注入与 MC-DE
  内核；**不复制/重写 V26 内核**，实现最小 budget planner + V26 MC-DE adapter
  wrapper。
- **source-adaptive 有限整数预算平面**：
  `m_total = floor((1.3·block_len·H_source − 64)/5)`，其中 `H_source = H1+H2` 为该
  source 的 full-precision 条件熵；只测 entropy-proportional 拆分 `m1 ∈ {m1_ep−2 …
  m1_ep+2}`。
- 冻结预算表（full-precision H1/H2 复算，见 design §2）：

  | source | block_len | m_total |
  |:------:|----------:|--------:|
  | 1M     | 1024/2048/4096/8192 | 200/413/840/1693 |
  | 1p5M   | 1024/2048/4096/8192 | 206/426/866/1745 |
  | 2M     | 1024/2048/4096/8192 | 208/430/873/1760 |

- Bob-full sequential decoding 语义：下一层只依赖 Bob 已解码并验证的前层，DE 端无
  Alice-oracle（渐近 true-predecessor 条件化，不模拟有限码错误传播）。
- 每层 syndrome + 块级公开 tag 进入总泄漏。

## Out of scope（V27 不应做什么）

- 不执行：本 change 在 freeze review ACCEPT 前只写文档，不运行任何 DE；ACCEPT 后按
  Phase B 顺序一次执行 screen/confirmation。
- 不做 degree 搜索 / 撞库；不做有限 parity-check 矩阵构造；不做有限 FER/解码器；
  不做 MET；不做 fresh/raw 或 V26 重跑；不改 factorization/labeling；不用 holdout
  调参；不 push。
- 不再使用 worst-source 单一预算常数（被 source-adaptive 取代）。

## Decision states (终态，仅允许以下之一)

- `pass_finite_budget_ready`：存在同一个 `block_len`，三 source 均有确认通过的候选。
- `de_pass_no_finite_headroom`：渐近机制有效（继承 V26），但每个 block_len 三 source
  无法同时获得确认通过候选（有限预算太紧 / ±2 带内无头寸）。
- `implementation_blocked`：budget planner / wrapper / 资源实现被阻塞。
- `resource_blocked`：24h 全局 completed-call 累计资源门触发。
