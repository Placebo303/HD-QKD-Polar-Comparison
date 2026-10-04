# 跨仓流程审计：NB-LDPC（本仓）vs NB-Polar（../HD-QKD_Polar_Comparison-nbpolar）— 2026-09-28

- **来源与授权**：本文件由 NB-Polar 项目会话（`HD-QKD_Polar_Comparison-nbpolar`，分支 `codex/nbpolar-phase0`）写入。
  PI 于 2026-09-28 在该会话中明确授权："同时也调研隔壁 comparison 是否有相同问题，特别是他们也在做 NBLDPC
  相关任务，有这样问题的话也帮他们一并修改并给出说明是我在这个项目同意你修改的，以及修改原因"。
- **性质**：只读审计记录（新增文件）。**未修改本仓任何既有文件**，未改任何历史结论、状态串或 OpenSpec change；
  未提交（本仓当前分支 `formal-ir-v72p1-addendum-clean` 有另一会话的未提交改动，为避免冲突，提交留给本仓会话/PI）。

## 为什么做这次审计

NB-Polar 项目 2026-09-28 诊断出一组流程问题，导致其 agent 反复要求"新采集数据"，而二元基线在同等 3 s 采集规模下
能正常评估大量块：

- **P1** "解码过的帧永不回流为确认样本"被当作硬规则，常冠以"污染/consumed/须新采集"。其真实理由只是统计选择偏差；
  安全上公开披露已计入 β/f_eff/leak_EC，重复解码不增加泄漏。
- **P2** 为研究比较设置过多分段（CAL/CHAR/HELDOUT/EVAL/RESERVE，且为已淘汰方法保留 1024 帧 CAL），
  一次 3 s 采集只剩 14 个可评估块（二元基线约 65 块）。
- **P3** "数据已耗尽"被反复引用，无统一数据账本，两批不同数据的"耗尽"被混为一谈。
- **P4** 样本量 n 按早期参照值冻结，方法改进后未重推，且有规则禁止由 n 反推数据需求。
- **P5** 规则靠模板/delta-successor 继承传递，从未重新推导理由。

NB-Polar 侧的修正在 `../HD-QKD_Polar_Comparison-nbpolar/openspec/changes/nbpolar-data-use-rules-revision/`。

## 本仓审计结论（只读，证据见各行）

| 问题 | 本仓是否存在 | 证据 |
|---|---|---|
| P1 | 部分存在但范围窄、理由正确（B 类统计选择偏差），仅用于正式 TEST/qualification 声明，不阻塞诊断 | `openspec/changes/formal-ir-v55-*/design.md:47`；`docs/nonbinary-ldpc-v13-existing-data-diagnostic-plan.md:300-313`（"重新采集不是 V13 诊断的前置条件"）；`docs/decision-log.md:2617` |
| 泄漏记账 | 无"重复解码增加泄漏"谬误；多阶段 rescue 的逐阶段泄漏是真实新增披露，正确计入 | `openspec/changes/formal-ir-v55-*/design.md` §2.1 |
| P2 | 分段存在但跨方法等量（同一批切分供 NB/HD-Cascade/Layered-Binary 共用），无与二元基线不对等 | `docs/research_cycles/M2-REALCOMP/RESULT.md:28-53` |
| P3 | 不存在：有统一原始数据清单；"ladder_exhausted" 指码率阶梯而非数据耗尽，未混用 | `docs/DATA_INVENTORY_20260921.md`；`docs/decision-log.md:2094,2108` |
| P4 | 不存在：N_req/阈值持续重推 | `docs/research_cycles/V80-NBLDPC-JAN21/X1_BATCH_END_REVIEW.md:25`；`docs/decision-log.md:4743` |
| P5 | 有苗头（`AGENTS.md` §10.1 item 5 delta-successor 继承），但有批末/会话审计主动纠偏 | `AGENTS.md:360-363`；`docs/research_cycles/SESSION-AUDIT-20260928/` |

## 结论与建议（供本仓 PI/会话裁决，未执行）

1. 本仓**无需**做与 NB-Polar 同等的规则改写；现有分段、数据清单、阈值重推机制健康。
2. 可选的唯一加固（P5）：在 `AGENTS.md` §10.1 item 5 追加一句——继承前代常量或规则时，须写明其理由来源
   （哪次实测/推导，以及理由类型：安全 / 统计选择偏差 / 审计完整性）。按本仓规则，此改动应走 OpenSpec，
   由本仓会话执行。
3. 措辞建议：本仓 v55 等处用"HOLD 已污染"描述统计选择偏差；如后续新文档引用，建议写成"HOLD 已用于开发（选择偏差）"，
   避免被误读为安全/泄漏理由（NB-Polar 正是因此类措辞漂移产生了误导）。
