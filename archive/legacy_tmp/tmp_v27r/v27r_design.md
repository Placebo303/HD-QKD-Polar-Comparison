# Design: formal-nonbinary-ldpc-v27-finite-leakage-margin-de-gate  (V27R revision)

> Status: **V27R DRAFT — source-adaptive 修订版，PENDING_FREEZE_REVIEW（2026-08-19；
> 只写文档，不执行）**。本修订取代 change 内先前 worst-source 草案。
> 继承：V26 channel-informed multilevel DE gate（A02 F03 GF32+GF32 渐近 f=1.3 收敛
> 30/30）与 V25 经验信道 `P(A|B, source, delay)` / `channel_counts.npz`。
> V26 仅作 archived reference；**禁止重跑 V26 DE**。

## 1. 架构与信道（冻结，继承 V26 A02）

- 架构：**F03 natural（MSB→LSB），L1 GF(32) + L2 GF(32)**，`width = log2(32) = 5`
  bit/symbol/层。
- 信道：从 V25 train `N_ab`（`channel_counts.npz`）构造每层逐样本条件后验
  `P(U_i | B, source, delay, U_<i)`，true-symbol centering 注入 MC-DE；三 source
  （1M/1p5M/2M）独立，`SOURCE_METADATA` 显式记录 `delay_used_ps = -50/+50/+50`、
  `n_pairs`。不重估亚 bin delay。
- **asymptotic true-predecessor-conditioned multistage DE**：V27 是渐近**多级** DE，
  语义为 L1 先于 L2、且 L2 条件于**已正确解码的 L1**（true-predecessor-conditioned）。
  这是渐近建模前提，**不模拟有限码错误传播**——不引入 Alice-oracle，也不在层间传递
  有限码纠错后的残余错误。每层 syndrome + **块级** 64-bit 公开验证 tag 进入整块总
  泄漏。
- **source/delay 语义**：source/delay 是**公开 acquisition selector**，仅用于：
  (a) 选择后验 population（%source 独立的 P(A|B)）；(b) 选择 syndrome 预算
  （source-adaptive m_total）。它们**不是逐符号公开 side information**，不额外重复
  计费——后验与预算已计入总泄漏，source/delay 本身不作为逐符号信息再次计入。

## 2. 有限泄漏预算（冻结，source-adaptive）

总泄漏（bits/symbol，含 64-bit 公开验证 tag）：

\[
\mathrm{leak}_{\mathrm{total}}=\frac{5\,m_{\mathrm{total}}+64}{n}
\]

- `m_total = m1 + m2`：两个 GF32 层**整数** syndrome 行数之和（每行 5 bit）。
- `64`：**每块**公开验证 tag 的 bit 数，计入总泄漏（块级，不在层间使用）。
- `n = block_len`：块长（GF32 符号数）。

每个 source 用自己的 full-precision 条件熵 `H_source = H1 + H2`（从 `channel_counts.npz`
复算，见下表）。总效率约束 `f = leak_total / H_source <= 1.3` ⇒

\[
m_{\mathrm{total}} = \left\lfloor \frac{1.3\,\cdot\,block\_len\,\cdot\,H_{source} - 64}{5} \right\rfloor
\]

### 2.1 Full-precision 每-source 条件熵（冻结来源：`channel_counts.npz` run_04）

| source | H1 (bits/sym) | H2 (bits/sym) | H_total (bits/sym) |
|:------:|--------------:|--------------:|-------------------:|
| 1M     | 0.024280547   | 0.776757278   | 0.801037825        |
| 1p5M   | 0.025199497   | 0.800366555   | 0.825566052        |
| 2M     | 0.025662049   | 0.806900673   | 0.832562722        |

（与 V26 worst-source 常数 0.02566205/0.80690067 一致；此处保留每-source full-precision，
不取 worst 共享。）

### 2.2 冻结 source-adaptive 预算表（复算确认）

> `m_total = floor((1.3·block_len·H_source − 64)/5)`，full-precision H_source。

| source | block_len=1024 | 2048 | 4096 | 8192 |
|:------:|---------------:|-----:|-----:|-----:|
| 1M     | 200            | 413  | 840  | 1693 |
| 1p5M   | 206            | 426  | 866  | 1745 |
| 2M     | 208            | 430  | 873  | 1760 |

### 2.3 拆分 m1/m2（冻结）

对每个 (source, block_len)：

- **m1_ep rounding 规则（冻结，明确）**：`m1_ep = round(m_total · H1 / H_source)`，
  使用 Python `round`（float·float，banker's rounding / round-half-to-even），结果
  cast 为 int。此为可复现的明确规则，不作任何人工调整。
- 候选：`m1 ∈ {m1_ep − 2, m1_ep − 1, m1_ep, m1_ep + 1, m1_ep + 2}`，
  `m2 = m_total − m1`。**五个候选均有晋级资格**。
- 合法性 `0 <= m1, m2 <= m_total` 且 `R_i = 1 − m_i/n ∈ (0,1)`（即 `m1,m2 < n`）。
  冻结表中所有候选均合法（m1 ∈ [4..56]，m2 ∈ [194..1720]，均 ≪ n）。
- 每层码率：`R_i = 1 − m_i/n`（GF32 每行 5 bit，`R = 1 − leak/width` 与 V26
  `target_rate_layer` 同源）。总 f 与拆分无关（`m_total` 固定），拆分只改变每层
  `f_i` 与各层收敛性。

### 2.4 每 (source, block_len) 的 m1_ep 与实现总 f（复算）

| source | n | m_total | m1_ep | m2(m1_ep) | 实现总 f |
|:------:|--:|--------:|------:|----------:|---------:|
| 1M     | 1024 | 200 |  6 | 194 | 1.29715 |
| 1M     | 2048 | 413 | 13 | 400 | 1.29775 |
| 1M     | 4096 | 840 | 25 | 815 | 1.29958 |
| 1M     | 8192 | 1693| 51 | 1642| 1.29974 |
| 1p5M   | 1024 | 206 |  6 | 200 | 1.29409 |
| 1p5M   | 2048 | 426 | 13 | 413 | 1.29764 |
| 1p5M   | 4096 | 866 | 26 | 840 | 1.29942 |
| 1p5M   | 8192 | 1745| 53 | 1692| 1.29956 |
| 2M     | 1024 | 208 |  6 | 202 | 1.29495 |
| 2M     | 2048 | 430 | 13 | 417 | 1.29847 |
| 2M     | 4096 | 873 | 27 | 846 | 1.29876 |
| 2M     | 8192 | 1760| 54 | 1706| 1.29964 |

实现总 f 均 < 1.3（正但很小）：这是 64-bit tag 占掉部分预算后的真实有限头寸。

## 3. 固定系综（冻结）

- 变量度分布冻结 `lambda = {2: 1.0}`。
- 每层码率由拆分决定：`R_i = 1 − m_i / n`（GF32 每行 5 bit）。用 harmonic-exact
  concentrated check distribution 生成对应 `rho`（GF32 域，与 V26 同源；
  `R1≈0.993–0.996`、`R2≈0.79–0.81`，所得 check degree 须在 DEGREE_MAX 内，由
  budget planner 校验）。
- **只测 entropy-proportional 拆分及其 ±1、±2**（见 §2.3）；不做任何 m1/m2 搜索、
  不做 λ/ρ 搜索、不做有限矩阵构造。

## 4. Screen（每个 (block_len, source) × 5 候选）

```
mc_samples  = 400          # 与 block_len 是两个不同字段（不混用）
max_iter    = 100
screen_seeds = [27001, 27002]
local_entropy_tol_bits = 0.01
streak      = 20
```

- 覆盖：4 block_len × 3 source × 5 候选（m1） × 2 层 × 2 screen seeds。
- 每个 (block_len, source) 的**每个候选**独立打分；对候选计算的 screen 指标（均只
  针对该单一 (block_len, source, candidate)）：
  - `worst_final_entropy`：该 (block_len, source, candidate) 下 2 层 × 2 screen
    seeds 的 final mean entropy 最大值；
  - `mean_final_entropy`：2 层 × 2 screen seeds 的 final mean entropy 平均。
- **screen 完整执行**全部候选后再进入 confirmation（不做边 screen 边 confirm 的
  提前截断；screen 必须先跑完）。

### candidate_id / 去重 / 排序（冻结）

- `candidate_id`：`(block_len, source, m1)` 三元组（`source`=1M/1p5M/2M label，
  `m1` 为整数；`(block_len, source, m1)` 唯一）。一个 `(block_len, source)` 下正好
  5 个候选 id。
- **去重**：`(block_len, source, m1)` 相同者视为同一候选（同 m1 → 同 m2、同
  层码率），任何重复出现的同一 id 合并；screen 后每 (block_len,source) 恰好 5 个
  唯一候选。
- **合法性**：`0 <= m1 <= m_total`、`0 <= m2 <= m_total`、`m1 < n`、`m2 < n`（即
  `R1,R2 ∈ (0,1)`）。不满足者标记 `illegal`，不参与排序与 confirmation。
- **排序 keys（升序，依次）**：
  1. `worst_final_entropy`（最小优先）；
  2. `mean_final_entropy`（最小优先）；
  3. `abs(offset)`（|m1 − m1_ep| 最小优先；越贴近 entropy-proportional 越好）；
  4. `m1`（最小优先，打破平局，确定性）。
  用这组 keys 对每个 (block_len, source) 的 5 个合法候选排序，得到确认顺序。

## 5. Confirmation（每个 (block_len, source)，按排序依次）

- 对每个 (block_len, source)，按 §4 排序从**第 1 名**开始依次确认：
  `mc_samples = 2000`、`max_iter = 200`、`confirm_seeds = [27101, 27102, 27103, 27104, 27105]`。
- **confirmed-pass 定义（单候选）**：该 (block_len, source, candidate) 的 **2 层 ×
  5 confirm seeds** 全部收敛（final mean entropy ≤ 0.01 bits/symbol 连续 20 轮）且
  无错误/非有限值。V27 是渐近 true-predecessor 条件化多层 DE（L2 条件于正确 L1），
  不模拟有限码错误传播。
- **候选失败后继续下一个**：若第 k 名候选确认未通过，转到 k+1 名；直到某候选通过
  （该 (block_len, source) 记 `confirmed candidate`）或 5 个候选全部失败（该
  (block_len, source) 无通过候选）。
- **pass（块长级）**：存在同一个 `block_len`，使 1M、1p5M、2M 三个 source 在该
  block_len 下**均有**通过确认的候选（各自可不同 m1）→ 该 block_len 为
  `passing_block_len`。若多个 block_len 满足，取**最小** block_len 为最终
  `pass_finite_budget_ready` 的通过块长。

## 6. 终态（冻结，仅允许以下之一）

- `pass_finite_budget_ready`：存在一个 `block_len` 使三 source 均确认通过候选；输出
  该 block_len 及三 source 的 (m_total, m1, m2, R1, R2, f_realized)。
- `de_pass_no_finite_headroom`：渐近机制有效（继承 V26 30/30），但**每个** block_len
  三 source 都无法同时获得确认通过候选（有限预算太紧 / ±2 带内无头寸）。给出每
  block_len 的失败候选数与最小熵值；结论：渐近通过但有限块头寸不足，有限构造 change
  暂不提出。
- `implementation_blocked`：budget planner / V26 wrapper / 资源实现被阻塞（如冻结
  source 数据缺失、channel adapter 无法复用），返回具体阻塞点。
- `resource_blocked`：24h **全局 completed-call 累计资源门**触发（见 §7）。

判定优先级：先查 `implementation_blocked`/`resource_blocked`（实现/资源层）→ 再无
阻塞时按 §5 找 passing block_len → 有 → `pass_finite_budget_ready`；无 → 
`de_pass_no_finite_headroom`。

## 7. 资源门与 checkpoint（冻结）

- **24h 全局 completed-call 累计资源门**：`RESOURCE_LIMIT_SECONDS = 24h`，按**已完成
  DE 调用的累计计算耗时**计（不是墙钟），与 V26 一致但沿用"completed-call 累计"语义。
- 超限 → 停止新调用，终态 `resource_blocked`，dir 内记录 `blocked=true` 与已累计耗时。
- **checkpoint 必须绑定完整 frozen configuration**：每个 checkpoint/run root 记录
  source-adaptive 预算表、m1_ep rounding 规则、五个候选、screen/confirm 参数、排序
  keys、终态集合、资源门——保证从任何 checkpoint 可完整重建，且禁止"换配置重跑"。

## 8. V26 关系

- V26 只作为 **archived reference**：继承其 A02 后验注入与 MC-DE 内核结论
  （f=1.3 渐近 30/30、H 常数来源）。**禁止重跑 V26 DE**；V27 实现只做最小 budget
  planner + V26 MC-DE 的 adapter wrapper，不复制/重写 V26 内核。

## 9. 禁止项

不实现有限 parity-check 矩阵、不跑有限 FER/解码器、不做 MET、不做 λ/ρ 或 m1/m2
degree 搜索、不重跑 V26、不读 fresh/raw `.ttbin`、不改 factorization/labeling、
不用 holdout 调参、不 push。**本 change 在 freeze review ACCEPT 前不执行任何 DE；
ACCEPT 后按 Phase B 顺序一次执行 screen/confirmation，不调参不重跑。**
