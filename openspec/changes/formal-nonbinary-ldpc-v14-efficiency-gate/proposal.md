# Proposal: formal-nonbinary-ldpc-v14-efficiency-gate

## What

V14 是"效率可行性门"：在构造任何高码率码之前，用密度演化（DE）回答一个
可判定问题——**在冻结的结构化信道模型（V13 修正后 D01 聚合导出的经验符号
差分分布）上，是否存在 rate ≥ 0.90（m ≤ 25 校验、n=256、q=1024）的
nonbinary LDPC 度分布，其 BP 解码可收敛（熵趋零），从而把协商效率压到
f ≤ 1.3？**

门的结果只有两个：**PASS**（冻结的候选度分布集合中存在收敛点 → V15 高码
率候选立项）或 **FAIL**（不存在 → 路线冻结为"仅 fresh 确认 V13 R3 现状"，
不做 V15/V16 码构造）。

## Why

- V13 已证明：图结构正确时，非二元 LDPC 在该数据域可 448/448 精确纠错，
  但 V13 R3 是 rate 0.336 的诊断载体，泄漏 6.64 bits/symbol，f≈12.1（对
  经验条件熵 0.547 bits/symbol）。
- 文献锚点（`docs/nonbinary-ldpc-efficiency-roadmap-survey.md`）：Müller
  et al. 2024 在 dimension 8、QBER 3–15% 达到 f = 1.078–1.14；本仓库 V8
  已复现其 q=4 参考点。f ≤ 1.3 在低维是实证可达的。
- 历史教训：V9A（GF(1024) 全向量 MC-DE 零候选、66 分钟预算）、V10
  （DE-PEG-FFT-QSPA ensemble 门 failed）、V11（SC-DE 门 failed）三次失败
  都发生在"没有先行可行性门就构造码"。V14 把门放在最前面，且门不过就
  冻结，不允许"最接近"式续行。
- 我们的信道是**结构化**的（99.3% 非零差分 < 128，经验熵 0.547 ≪ QSC
  模型 2.722），QSC 的 1-参数门限族不适用；V14 用经验分布 w[d] 作为冻结
  信道模型直接做收敛判定。

## Scope

- 新增：V14 OpenSpec change、结构化信道模型文件、DE 门机制（扩展 V8/V9
  的 MC-DE）、门执行一次、独立 freeze review 与 gate review。
- 明确不做：任何有限码构造、解码器资格、真实数据解码、fresh 采集、
  V13 证据的任何改写。
- Claim boundary：DE 门是**渐近系综**陈述（BP 收敛性与码率），不是 FER、
  不是有限长性能、不是 promotion/qualification。

## Affected specs

- 新 spec：`formal-nonbinary-ldpc-v14-efficiency-gate`（本 change 的
  specs/ 增量）。
- 不修改任何既有 spec；`comparison_bench/` 内新增模块，冻结基线
  `src/`、`experiments/`、`tools/`、`results/` 不变。
