# Design: formal-nonbinary-ldpc-v17-multibit-structured-de-gate

## 0. Status

PLANNING（2026-08-15）。独立 freeze review ACCEPT 前禁止任何执行。
冻结条款修改需 amendment + 主线程授权。

## 1. 立项依据（frozen context，非新结论）

- V14 门（2026-08-15，gate_state=fail）：符号级普通不规则系综在
  q=1024 结构化信道、rate 0.93–0.94 上 12/12 非收敛（熵停在 0.288–
  0.357 vs 阈值 0.01）；f 1.032–1.239 全 ≤1.3 但收敛绑定。机制经 T2
  等价（V9 1e-12）+ Stage 0 文献回归双背书，FAIL 非伪影。
- V13 D01 观测（frozen 数据事实）：bit-plane mismatch 单调 3.1e-5
  （MSB）→ 3.75e-2（LSB）；raw SER 0.077（bw200）；条件熵下限
  0.547 bits/symbol。
- 文献锚点（SciVerse 调研，见 docs/nonbinary-ldpc-efficiency-roadmap-survey.md）：
  Cohen-Raviv-Cassuto TIT 2019（位面分解）；Müller 2024 f=1.078–1.14
  （q=8）；Li-Fair-Krzymień TIT 2009（GA）。
- 排名（objective 冻结）：① 位面/边标签（本门）；② SC-LDPC（QSC 下
  负耦合增益、结构化信道未否定）；③ 多边/高维 λ（搜索空间大）。

## 2. Stage 0 — Cohen/多位信道机制复现门（frozen）

- 目标：在小 q 上证明"位面分解/多位信道 + 对应 DE 更新"机制与文献/
  解析锚点一致。
- 冻结锚点：q=4（2-bit 分解）：每平面二元 BSC(p_i) 且 p_1 ≠ p_2 时，
  符号级 QSC 等效 vs 位面分解 DE 的阈值差异；对照 Cohen 2019 数值或
  独立二元 DE 复现（复用 V8 q=2 DE 已对 BSC/BEC 发表向量验证的机制）。
- PASS 判据（冻结）：锚点差 ≤ 文献容差（如阈值差 ≤0.005）或机制
  结构一致性检查全过（T2 级测试）。
- FAIL：机制不可信 → 门冻结（不进入 Stage 1/2）。

## 3. Stage 1 — 冻结多位信道模型（frozen）

- 把 V13 D01 观测映射为冻结信道模型（characterization 帧只读重算，
  cross-fit 只用 characterization 角色；与 V14 信道模型同纪律）：
  - per-bit-plane 错误概率向量 {p_1..p_10}（MSB→LSB，单调）；以及
  - 位面联合结构（10 bit 平面的错误联合分布或保守独立近似，冻结时
    声明并验证）。
- 模型文件 schema `nbldpc_v17_multibit_channel_model_v1`，持久化于
  change 的 evidence/。

## 4. Stage 2 — 预注册候选与点评估（frozen）

- 候选族（预注册 3–5 个，不搜索、执行前冻结）：
  1. **位面分解（Cohen 式）**：10 个二元 LDPC 平面码（每个平面用
     V14 已验证的二元 DE 阈值），平面间由符号映射耦合；f 按总泄漏
     计；
  2. **多位边标签（符号级）**：q=1024 但边标签取位面模式（如 MSB 位
     面高可靠、LSB 位面低可靠的结构化先验 + 符号级 DE，复用 V14
     `nonbinary_v14_mcde.py` 的 structured 信道分支扩展）；
  3. **位面加权结构化先验**：V14 结构化 w' 上再按位面权重调制。
  - 每个候选冻结其 (λ, ρ) 或机制参数、评估点（m∈{15,16,17,18} 或
    冻结子集）。
- 判定（与 V14 同构，冻结）：PASS iff Stage 0 ∧ Stage 1 ∧ ∃候选点
  收敛（熵 ≤0.01 base-q 连续 20 迭代）∧ f≤1.3；否则 FAIL。

## 5. 预算与回放（frozen）

- 预算：peak RSS ≤ 3 GiB；wall ≤ 24 h；execute-once。
- 回放：strict replay 一次；科学文件字节一致、provenance 字段豁免
  （V10/V14 先例）。
- 降级链（预注册）：机制/模型/实现问题 → Li-Fair GA → Cohen 解析 →
  resource_blocked。

## 6. 产物与纪律（frozen）

- 产物全部 additive：change 的 `evidence/`（模型、各 stage 结果、
  gate_decision、gate_manifest、replay_evidence）。
- V8/V9/V11/V13/V14 源码零改动；新代码为新增模块
  `nonbinary_v17_*.py` + CLI。
- 禁止：有限码构造、调参、重跑、扩大搜索、V15/V16 重启、fresh
  acquisition 干扰。

## 7. Claim boundary（frozen）

- 最高状态：`gate_state=pass`（系综可行性）→ 另开有限码 candidate
  change；`gate_state=fail` → 路线冻结。
- 本门不产生任何 FER/资格/效率实测结论；f≤1.3 仅为 DE 层面目标。
