# Proposal: formal-nonbinary-ldpc-v17-multibit-structured-de-gate

> 状态：PLANNING —— 2026-08-15 按用户更新后的目标（P2：独立效率研究，
> 位面/边标签门先行）立项。

## What

一个**纯可行性门**：用密度演化（DE）判定——把 V13 已观测的
**MSB→LSB 单调失配**（bit-plane mismatch 3.1e-5 → 3.75e-2，D01
characterization）映射为冻结的**多位结构化信道模型**之后，是否存在
**边标签/位面级**的非二元 LDPC 系综能在 rate ≥ 0.90 上达到 f ≤ 1.3。

本 change **不构造任何有限码**（无 codebook、无 decoder、无 canary/
development/qualification）。

## Why

- V14 门已证明：普通不规则系综（符号级、含 degree-2 的 λ）在
  q=1024 结构化信道上 rate 0.93–0.94 无 BP 收敛点（12/12 非收敛）。
- 该数据的核心结构是**位面不均匀**：错误概率从 MSB 到 LSB 单调上升
  近 3 个数量级。符号级 QSC/结构化先验都抹平了这一结构；**位面分解
  （Cohen-Raviv-Cassuto TIT 2019）或多位边标签**直接利用它，是有物理
  依据的下一候选族。
- 选择它作为第一效率路线的理由（objective 明确）：直接对应当前数据
  的位面不均匀性；V11 三个 SC-LDPC 几何在 QSC 下均为负耦合增益（SC
  在结构化信道下尚未被否定，排第二）；多边/高维 λ 搜索空间更大，
  排第三。
- 门优先纪律（V9A/V10/V11/V14 教训）：先证明系综层面可行，再构造
  有限码，避免浪费性构造。

## Scope

只做可行性门，分阶段（详见 design.md）：

1. **Cohen/多位信道机制复现门**：在小 q（q=4/16）上复现位面分解信道的
   DE 机制（对照文献解析/数值锚点），验证机制可信。
2. **MSB→LSB 单调失配映射**：把 V13 D01 观测冻结为多位信道模型
   （per-bit-plane 错误概率向量 / 位面相关结构）。
3. **预注册少量边标签/位面候选**：3–5 个（不搜索；候选集冻结于执行
   前）。
4. **执行前冻结**收敛、效率（f≤1.3）、预算（3 GiB / 24 h）、
   execute-once + strict replay 标准。
5. **一次执行**：PASS → 另开新的有限码 candidate change；FAIL →
   冻结，不启动 V15/V16，不扩大搜索。

## Out of scope

- 有限码构造（codebook/decoder/资格）；SC-LDPC 门（第二候选，本 change
  不覆盖）；多边/高维 λ 搜索；V15/V16 重启（仍为 aborted drafts）；
  fresh acquisition（P1 独立 change）。

## Success criteria

- 机制复现门 PASS 且存在 ≥1 个预注册候选点收敛且 f≤1.3 →
  `gate_state=pass` → 另开有限码 candidate change。
- 否则 `gate_state=fail` → 冻结、不启动 V15/V16、不扩大搜索。
