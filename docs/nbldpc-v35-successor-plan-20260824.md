# NB-LDPC 后继计划（V35 系列）— 基于 V34 bounded FAIL 的性能优先路线 — 2026-08-24

前置状态：V34 已按 `docs/v34-formal-execution-er1-closeout-20260824.md` 以
ER1 ACCEPT 关闭（0/60，三源各自 0/20，无 fatal/false accept）。本文档不修改
任何历史终态，只给出下一个算法中心变更的执行队列，供用户选择与授权。

## 0. 新增定量事实（本轮只读计算，可复核）

对 V25 train `P(A,B)` 直接重算两层条件熵（1024-bin 联合表，F03 因子化）：

| source | H(U2 \| U1,B) bits | L2 泄漏 m2×5 bits | L2 名义盈余 |
|---|---:|---:|---:|
| 1M | 795.46 | 920 | +124.54 |
| 1p5M | 819.50 | 950 | +130.50 |
| 2M | 826.52 | 960 | +133.48 |

与路线图 §3 的"+179.7/+184.6/+187.5 总预算余量"口径不同但结论一致：
**信息论预算不是第一矛盾，正盈余约 125–190 bits**。结合 V33 ensemble DE
六格全 PASS（L2 收敛需 37–44 迭代，max_iter=200），失败被压缩到且仅压缩到：

> **有限图实现 + 解码器转换层**（V31 0/300、V30R、V32 B3/B4
> improve-but-no-syndrome ≈250→≈179、V34 0/60 四代证据一致）。

V34 内部再细分：23/60 `max_iter_reached`（与 DE 所需 37–44 迭代相比存在
**迭代饥饿嫌疑**，因 V34 冻结 max_iter=30 是为了与 V32 可比而非收敛需要）；
37/60 `converged_no_syndrome`（BP 到达错误固定点：trapping 结构 /
posterior-conversion 失配嫌疑）。这两类需要不同的对策。

## 1. 决策答案：改当前算法还是换算法

- **方法论不改**：empirical-P matched control、source-specific 建模、
  train-only 设计、一次执行 + 独立 ER1 的生命周期全部继承。
- **码家族更换**：关闭对 V31 全 degree-2 QC packet 及其 seed/girth 微调的
  一切继续投入（V34 FAIL 分支已触发此禁令）；主线转向
  **informed protograph/MET 系综设计 + rate-adaptive 母码**。
- **解码内核先审计再复用**：V28R FFT-QSPA 的 oracle-L1 posterior 转换先用
  小规模黄金用例（m,n≤64，暴力 log-BP 对照）审计，排除 V30R 式转换 bug；
  damping / shuffled / layered scheduling 作为解码变体进入系综门（文献支持，
  不是对失败 packet 的调参）。

## 2. 执行队列（每步独立可停）

### S0 残差拓扑解剖（只读，零解码调用，立即可做）
输入：`run_01/block_records.json` 持久化的完整 `x2_hat` ×60 + V25 表 +
QC packet。输出：残差符号跨块重合模式、Tanner 短环参与度、未满足校验邻域、
prior 秩分布、b/delay 聚集。产物直接变成 S2 的设计禁令/目标清单，并能提前
暴露 conversion 病理（如残差集中于低信息位置）。

### S1 有界高迭代归因实验（唯一合法的"提高迭代"，需新 OpenSpec + 用户 EXECUTE_AUTH）
fresh seeds 新实验（非 V34 重跑）：同 packet、同经验 P 抽样语义、20 blocks/
source、max_iter=80、逐块记录 syndrome 首达迭代。成本 ≤25 min。
判读：若 max_iter 类消失且出现合法 PASS → 饥饿是主因之一，调度类改进入
S2 门；若 converged_no_sydrome 仍主导 → 结构定罪加强，S3 优先。

### S2 系综设计门（不构图，纯 DE/熵计算）
合并 roadmap R2.1+R2.3：F02–F05 × 层序 × L1/L2 泄漏分配的链式熵扫描；
empirical-P 非对称 MC-DE（Bennantan–Burshtein / Wang et al. 口径）筛选
protograph/MET λ-ρ 与解码变体（含 damping/layered）。判据升级为
block-error 结构代理 + 预估净 key-rate，不再单看 bit-entropy threshold。

### S3 单一有限实现 gate
系综通过后，恰两个候选比较：一个 protograph lifting vs 一个 Block-MDS/QC
（Tauz ITW 2024 方向）；禁止 seed 搜索；黄金转换测试先行。

### S4 rate-adaptive 母码（并行设计轨）
乘性重复 NB-LDPC（EPJ QT 2025）、puncture/shorten、raptor-like 增量冗余
（Access 2024；Tarable rateless protograph）。目标：三源共享单一母结构、
按帧实测 SER 只交易必要额外泄漏，直接服务净 key-rate 目标函数。

### 并行锚点（低预算）
R3 binary MLC/Polar P0（10 个 bit-plane 链式熵，纯计算）；R4 HD-Cascade
系统基线（独立冻结数据）。若 R4 净 key 已领先，NB-LDPC 后继必须指明收益
来自更低 leakage / 更少交互 / 更高吞吐中的哪一项。

## 3. 统一度量与停止规则

`accepted_fraction × (raw_secret_budget − actual_leakage) / acquisition_time`
为主排序量；同时记录 exact-FER、总泄漏、runtime/内存。任一候选在 S2 失败
即关闭；S3 第一次冻结 gate 失败后不得在同一 confirmation 数据上调参。

## 4. 建议顺序与请求授权项

默认顺序：S0 →(并行) S1-proposal + S2 → S3/S4 按 S0/S1 证据定向。
需要用户动作的两处：① S1 的新 OpenSpec freeze + EXECUTE_AUTH；
② S2/S4 的预算分配确认。S0 无需授权，可在下一轮直接开始。

## 5. 文献锚点（增量检索未发现反证）

- [Müller et al., HD-QKD NB-LDPC/HD-Cascade, QiP 2024](https://doi.org/10.1007/s11128-024-04395-w)
- [Martínez-Mateo & Elkouss, multiplicatively repeated NB-LDPC, EPJ QT 2025](https://doi.org/10.1140/epjqt/s40507-025-00376-9)（[arXiv:2501.11009](https://arxiv.org/abs/2501.11009)）
- [Karimi & Banihashemi, elementary trapping sets, IEEE TIT 2014](https://doi.org/10.1109/TIT.2014.2334657)；[degree-2 variable nodes 与 BP 失败](https://mathoverflow.net/questions/215424/effects-of-many-degree-2-variable-nodes-in-the-tanner-graph-during-the-decoding/215429#215429)
- [Informed shuffled/damped BP 解码变体](https://ietresearch.onelibrary.wiley.com/doi/10.1049/iet-com.2014.1169)
- [Rate-compatible Polar/LDPC hybrid-ARQ 反向协调](https://eprints.soton.ac.uk/511406/)
- 其余沿用路线图 §10 书目（MC-DE、非对称 DE、finite-length scaling、
  protograph girth、Block-MDS ITW 2024、short-block raptor-like 等）。
