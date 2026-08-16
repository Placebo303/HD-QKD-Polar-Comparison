# Route A 诊断结论 — V13-R3 legacy 失败帧非“迭代不足” (2026-08-16)

Status: COMPLETE (diagnostic_only)

## 数据
- 全量 legacy audit 中 128 个 `decode_failed` 帧（均为 iteration_limit@100）。
- Route A 重解码：
  - `max_iter=200`：**128/128 仍 decode_failed，0 exact_correct**
  - `max_iter=500`：抽样 **8/8 代表性失败帧仍 decode_failed，0 exact_correct**

## 结论
失败帧不能通过单纯提高迭代次数救回。因此这些失败更可能来自：
1. 固定 QSC 先验 p=.20 与实际信道 SER≈0.24–0.26 不匹配；
2. R3 图结构/码率在当前漂移信道上存在收敛限制；
3. 需要结构化信道模型（位面相关）而不是 q-ary symmetric 假设。

## 证据
- `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3_legacy_route_a_20260816/`
  - `max_iter_200_diagnostic.csv`
  - `max_iter_500_sample_diagnostic.csv`
  - `route_a_sample_summary.json`
  - `route_a_conclusion.json`

## 后续建议
- Route B 效率改进必须先引入结构化信道/先验适配；
- 若继续用当前 R3 候选，需考虑按帧估计 SER 或增加码率/图结构自由度；
- 这些仅为 diagnostic_only，不改变 frozen failure 或 legacy_drift_audit 边界。

## 先验校准探针（A3b）结果

- Oracle 先验（p=每帧 raw_ser，max_iter=100）：128/128 仍 decode_failed，0 exact_correct。
- p 网格（p∈{0.16,0.20,0.24,0.28,0.32}，8 个代表性失败帧，max_iter=100）：40/40 仍 decode_failed，0 exact_correct。
- 结论强化：**QSC 类先验失配不是失败主因**；失败更可能来自结构化信道假设不足或 R3 图/码率限制。

证据：
- `prior_probe_oracle_diagnostic.csv`
- `prior_grid_sample_diagnostic.csv`
- `route_a_prior_probe_summary.json`
