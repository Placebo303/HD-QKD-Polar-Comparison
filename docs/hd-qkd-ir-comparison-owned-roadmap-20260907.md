# HD-QKD IR Comparison 主实施路线图（2026-09-07）

## 1. 所有权边界

`HD-QKD_Polar_Comparison` 是后续 NB-LDPC 科研主线的实施仓库，负责：

- Model-F/CAL 输入合同；
- D5 P0/G1/G2 与目标 `n_IR=1024` 验证；
- 真实单点 NB-IR；
- 逐块接受、错误接受、泄漏、保留率和运行成本；
- 固定 `d` 的 `tau` 扫描与后续 `d x tau` 泛化；
- 安全模型需要的标准化实际 IR 输出。

`HD-QKD_Polar_Release` 近期仅作只读参考：复用其 ttbin、物理分帧、Polar
基线和报告语义，不修改其 Polar 逻辑，不在那里维护第二套 NB-LDPC 或扫描器。
只有 Comparison 已形成稳定输出合同并完成真实单点验收后，才能通过新的独立
change 考虑 Release 侧薄读取适配层。

## 2. 当前状态

- D4R2 已量化新域模型预算：两层 CE `3.814742 + 3.347605 = 7.162347`
  bit/symbol；旧 `16/200/216` 行预算不适用。
- D5 DV3 mother 的八个冻结前缀通过结构门，四环风险保留。
- G0 recovery 为 8/8 exact/syndrome-ok/finite，八次历史 decoder call；仅为
  tiny synthetic plumbing 证据，不是 FER、真实数据、资格或推广结果。
- P0/G1/G2 候选实现存在，但需先完成独立验收和最小返工。
- P0/G1/G2 正式执行、目标块长、真实数据、扫描、安全选点均未授权。
- 当前 Model-F preparation 缺少冻结 CAL-TRAIN canonical `counts_ab
  (1024,1024)` 与 `P(B)`；不得用 G0 toy、uniform 或随机分布替代。

## 3. 有序里程碑

### M1 — 新域合成可行性

1. 独立验收 P0/G1/G2 候选实现；
2. 补齐 canonical Model-F CAL-TRAIN 输入；
3. 分别授权并执行 P0 成本预检、G1 `n_IR=64` 趋势门、G2 `n_IR=256`
   生死门；
4. 仅 G2 合格后验证目标 `n_IR=1024`。

M1 输出是匹配新域模型与码率的真实 decoder 合成结果，不是实际 FER。

### M2 — 新域真实单点

冻结一个 `(d,tau,n_IR)`，CAL/选择数据与独立确认数据隔离。报告 attempted、
exact、protocol accepted、accepted-wrong/undetected、实际 syndrome/
verification/control disclosure、保留符号及运行资源。

### M3 — Comparison 内的端到端公开开销闭环

在 Comparison 中复用既有符号/中间数据边界，接入 NB-LDPC，并输出稳定的
逐块实际 IR 合同。安全观测量不足时只报告 reconciled/public-EC 结果，不冒充
secure key。Release 仍不承载算法实现。

### M4 — 扫描

先固定 `d,n_IR` 扫描 `tau`，逐点重建数据、prior、码率并核算保留率、实际
leakage、接受率和耗时；用独立数据确认所选点。随后只增加一个新 `d` 验证拆层、
有限域、矩阵和校准泛化，最后才扩展完整 `d x tau`。

### M5 — 安全资格与最终选点

安全测量/模型可并行准备，但 measured、assumed、projected、qualified 必须分开。
先选择 reconciled-net 最佳点；协议观测量、有限长度参数和 epsilon budget 全部
合格后，才选择 secure-key-rate 最佳点，并使用独立数据确认。

## 4. 最近目标

当前最近 gate 是：完成 P0/G1/G2 候选的独立验收与最小返工，再单独解决
Model-F CAL-TRAIN 输入，之后才决定是否授权 P0。

第一个端到端里程碑是：在 Comparison 内，对一个真实 ttbin 会话和固定 `d`
生成由实际 NB-LDPC 译码支撑的 `tau` 扫描表。它必须经过 M1、真实单点和公开
开销合同，不能从 G0 或 P0 直接跳到扫描。

