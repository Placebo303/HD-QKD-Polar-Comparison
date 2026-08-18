# Tasks: formal-nonbinary-ldpc-v25-empirical-timestamp-channel-and-multilevel-factorization-gate

Status: **FROZEN_ACCEPTED — P102 ACCEPT（主线程 2026-08-18）；五项 minor spec edits 已应用；M0–M4 实现已授权**

## P0 — read-only state/input audit

- [ ] **P001** 读取 AGENTS.md、AGENT_PROJECT_MEMORY.md、CURRENT_TASK.md、
  AGENT_HANDOFF.md、docs/decision-log.md。
- [ ] **P002** 只读审查 V17–V24 evidence/report/archive；确认 V24 只排除 bounded
  single-edge、不排除 GF512/256/multilevel/source-conditioned/MET。
- [x] **P003** 定位 pairs build manifest、sidecar metadata、数据源 provenance、
  D01/V17 证据、legacy pairs；产出 `data_inventory.json`（路径/source ID/时间/
  frame 数/symbol 数/bin width/frame period/delay/pairing/provenance/角色/可否
  train-holdout-qualification）。
- [x] **P004** 本阶段不修改代码、不运行 DE、不读取重型原始数据。

## P1 — OpenSpec freeze

- [x] **P101** proposal/design/tasks/spec 冻结定义、输入清单、切分、factorization、
  labeling、输出 schema、gate、禁止事项、失败终态。
- [ ] **P102** 独立 freeze review ACCEPT 前不得开始实现。

## I — engineering (engineering pass only)

- [ ] **I01** labeling L01/L02 实现与可逆性（T01）。
- [ ] **I02** factorization F01–F05 实现与可逆重构（T02/T03）。
- [ ] **I03** 数据切分器（60/20/20 时间序、frame 不重叠、T04）+ split_manifest。
- [ ] **I04** delta 诊断（signed/modular 分离 T05；run 不跨边界 T06）。
- [ ] **I05** conditional count 表 N[A,B,Z(+labels)] 与 chain-rule 计算（T07）。
- [ ] **I06** 模型家族 C01–C06 实现（预测 NLL、条件熵、calibration、zero-prob、
  per-source）。
- [ ] **I07** delay/alignment 门（source-dependent，锁 delay）。
- [ ] **I08** factorization gate（顺序规则、H_i、R_i_ref、复杂度代理）。
- [ ] **I09** 输出层：channel_summary/delta_by_source/gray_joint_masks/
  channel_counts.npz/model_holdout_scores/factorization_layers/chain_rule_check/
  alignment_report/gate_summary/readonly_verify + 说明。
- [ ] **I10** Alice-oracle 访问检测（T10）、holdout 不回写（T11）、verifier 重算
  terminal state（T12）。

## T — tests (T01–T12)

- [ ] **T01** natural/Gray labeling 可逆。
- [ ] **T02** F01–F05 分层可逆。
- [ ] **T03** 所有分层重构回原始 0–1023。
- [ ] **T04** train/validation/holdout 无 frame 重叠。
- [ ] **T05** signed delta 与 modular delta 不混淆。
- [ ] **T06** run 不跨文件/frame。
- [ ] **T07** chain rule 在 tiny synthetic joint table 上闭合。
- [ ] **T08** 公开 residual 会增加 leakage 的负例。
- [ ] **T09** Bob-full 与 Bob-coarse 条件信道不可混用。
- [ ] **T10** Alice oracle 访问检测。
- [ ] **T11** holdout 参数不可回写 train model。
- [ ] **T12** 输出 verifier 从原始统计重算 terminal gate。

## M — scientific stages (authorized only after P0/P1 ACCEPT)

- [ ] **M001** 生成 data_inventory.json。
- [ ] **M0** 时间戳误差图谱（16 项指标，按 source/file/time block）。
- [ ] **M1** 模型比较 C01–C06（validation + sealed holdout；per-source + pooled 补充）。
- [x] **M2** ±1 结构 / 方向 / 时间稳定性分析（既有 delay 配置，不重估 delay、不读
  .ttbin）；方向随 source/delay_used_ps 变化视为待建模 channel 特征。
- [ ] **M3** multilevel factorization gate（F01–F05 × L01–L02；chain rule 闭合；
  R_i_ref；复杂度代理）。
- [ ] **M4** 产出供 V26 的信道候选：**高域候选 GF(512)/GF(256)** + **中域对照
  GF(32)/GF(16)/GF(8)**；同时给出总状态（pass_ready_for_de_change /
  fail_no_stable_factorization / blocked_insufficient_joint_data /
  blocked_alignment_unresolved）。M4 不选唯一方案。

## V — verification / closeout

- [ ] **V001** 独立只读 verifier：从 counts+frozen config 重算主要指标与 terminal
  state；ok=true/false + 问题列表。
- [ ] **V002** 决策写入 decision-log；更新 CURRENT_TASK/AGENT_HANDOFF/
  AGENT_PROJECT_MEMORY。
- [ ] **V003** PASS 仅允许提出 V26（不得自动启动）；FAIL/BLOCKED 停止并保留全部证据。
- [ ] **V004** 本地提交，不 push。

## Stop rules

- P0/P1 未 ACCEPT → 不得实现/执行。
- 出现 blocked_insufficient_joint_data / blocked_alignment_unresolved → 停止并保留
  证据（不是科学 FAIL）。
- fail_no_stable_factorization → 现有数据无稳定可迁移分层结构，停止。
- 任何禁止事项（MET/有限码/FER/oracle/holdout-selected-mapping/raw pipeline）→ 立即
  停止并请求授权。
