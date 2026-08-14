# Design: formal-nonbinary-ldpc-v15-high-rate-candidate

> 状态：DRAFT SKELETON —— 立项前置：V14 gate_state = pass。选中点
> （λ/m）、构造算法细节与资格门数值在 V14 门结果 + freeze review 后定稿；
> 本文件先把与门结果无关的骨架冻结。

## 1. 候选契约（骨架）

- 身份：`nbldpc_v15_hr_v1`；n=256、q=1024、m ∈ 门通过的冻结集
  （[PENDING V14 GATE]）；rate = 1 − m/256。
- 图：连通、无平行边、Tanner girth ≥ 8、变量度分布 = 门通过的冻结 λ
  （[PENDING]）、校验度 = 该点冻结 ρ；rank(H)=m 逐码验证。
- 构造：[PENDING —— 候选：QC 代数构造（Arabaci 2009 / Song 2006 族）或
  确定性 PEG + 消短环；冻结种子搜索同 V13 R3 先例]。
- 解码器：结构化先验 w'（V14 信道模型）替换 QSC 先验；flooding
  FFT-QSPA 镜像循环（复用 V13 D03 等价性证据）；max_iter=100；
  hook 等价性测试逐字段断言。
- 泄漏：m·10/256 bits/symbol；f = (m·10/256)/H(w')。

## 2. 合成资格（骨架，数值 [PENDING]）

- 合成信道：按 w' 采样（结构化模拟，含冻结种子）；预注册
  canary/development/confirmation 三集（新合成根，与 V7-V13 全部根
  不相交）；baseline（V13 R3 码 + QSC 先验）与候选各一次；事后 exact
  check；禁止词与六文件/verify 纪律沿用 V13。
- 门：[PENDING —— 候选 development ≥ 冻结阈值 + zero forbidden；
  baseline 仅对照]。

## 3. fresh 实数据确认（明确不自动执行）

- 需要用户决定新采集（新帧身份）；本 change 只准备 prepare/review/
  execute/verify 管线与预注册合同，不触发采集。

## 4. 输出与测试

- 证据：`comparison_bench/outputs_comparison/formal_ir_methods/` 新根
  （[PENDING 命名]）；测试 T0-T3 同 V13 纪律；IT0-IT3 候选实现测试。

## 5. Claim boundary

- 合成资格 ≠ promotion/qualification/fresh correction；fresh 确认需
  独立 change + 采集。
