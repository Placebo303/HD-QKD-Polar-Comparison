# Proposal: formal-nonbinary-ldpc-v15-high-rate-candidate

> 状态：DRAFT —— 本提案在 V14 门结果出来前起草；**立项前置条件是 V14
> gate_state = pass**。门为 FAIL 时本 change 不立项（路线冻结声明见
> V14-C01）。设计细节（选中的 λ/m 点、构造算法、资格门数值）在门结果
> 与 freeze review 后定稿。

## What

把 V14 门通过的"系综可行性"落实为**第一个高码率有限码候选**：
- 在冻结的 (λ, m) 点上构造 n=256、q=1024、rate ≈ 0.93–0.94 的
  nonbinary QC/PEG 有限码（girth ≥ 8、无平行边、连通、rank = m），
  新身份 `nbldpc_v15_hr_v1`；
- 解码器：冻结的结构化先验 w'（V14 信道模型）+ flooding FFT-QSPA
  （复用 V13 D03 已验证的镜像循环；结构化先验只替换 QSC 先验矩阵）；
- **合成资格**：新合成根、预注册 canary/development/confirmation 集、
  baseline（V13 R3）与候选各一次、事后 exact check；通过后进入
  fresh 实数据确认（**需要用户决定新采集**——新帧身份，复用 V12 的
  source_partition 纪律）。

## Why

- V14 门 PASS 只证明系综层面可行；有限码 + 短块（n=256）的 FER/效率
  需要实证。
- 结构化先验是把模型熵从 2.72 压到 0.57 的关键（V13 已证明其为
  co-factor）；V15 是它第一次进入有限码解码。
- 文献：高码率 NB-QC 构造（Arabaci 2009）、puncture/shorten 速率适配
  （Klinc 2008）、EMS 备选（Lacruz 2016）；调研报告
  docs/nonbinary-ldpc-efficiency-roadmap-survey.md。

## Scope

- 新增 OpenSpec change、码本模块、结构化先验解码路径、合成资格通道、
  IT0-IT3 测试；`comparison_bench/` 内；V8/V9/V11/V13 源码与冻结基线
  不动。
- 明确不做：真实数据解码（fresh 采集前）、promotion/qualification
  声明、对 V13 证据的改写。

## Affected specs

- 新 spec：`formal-nonbinary-ldpc-v15-high-rate-candidate`。
