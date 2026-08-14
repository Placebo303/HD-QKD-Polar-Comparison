# Proposal: formal-nonbinary-ldpc-v16-rate-adaptive-deployment

> 状态：DRAFT —— 立项前置条件：V14 gate = pass 且 V15 候选完成合成资格。
> 本 change 是部署适配层，不引入新码。

## What

为 V15 候选族加**部署适配层**（对照文献样板
Treeviriyanupab & Zhang, Entropy 2024；Gao et al., Opt. Express 2019）：
1. **syndrome 估计**：用单个/多个冻结码的 syndrome 权重估计当前 SER，
   替代随机采样估计（冻结估计器公式与偏差校准）；
2. **rate-adaptive 协商**：按估计 SER 从冻结候选族（V15 码 + 预注册的
   puncture/shorten 变体）中选择码率，模拟信道漂移下的端到端效率；
3. **子块确认**：分块多项式哈希确认（冻结 hash 参数），错误子块只
   重协商一次。

证据：合成信道漂移仿真（SER 按冻结时间剖面从 0.05 漂到 0.12），
输出每块选中码率、泄漏、f、确认轮数、端到端 secret-key 吞吐对照
Slepian-Wolf 界。

## Why

- 真实 QKD 中 SER 随损耗/环境漂移；固定码率会损失效率或失败。
- 文献样板已证明该组合能把吞吐推到理论极限（BB84 场景）。
- 复用 V13 的六文件/预注册/只读 verify 纪律。

## Scope

- `comparison_bench/` 内新增：估计器模块、码率选择器、子块确认协议、
  仿真通道、CLI、IT 测试；不改 V14/V15 码本与 V13 基线。
- 明确不做：真实数据、安全证明、硬件实现。

## Affected specs

- 新 spec：`formal-nonbinary-ldpc-v16-rate-adaptive-deployment`。
