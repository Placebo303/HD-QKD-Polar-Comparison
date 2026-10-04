# V25 Empirical Timestamp Channel + Multilevel Factorization Gate — Report

Status: COMPLETE — `pass_ready_for_de_change`（2026-08-18；P102 ACCEPT；M0–M4 实现并运行）

## 1. Scope & frozen conventions

- q=1024 原始符号保持 1024-bin；编码分层（F01–F05 × L01 natural / L02 Gray，
  MSB→LSB 切分）与物理 bin 合并严格区分。
- 解码信道方向（冻结）：`P(A|B)`，`N_ab[a,b]=count(A=a,B=b)`（列归一化）；
  sidecar chan_ll_table 冻结为该方向。
- 主线程决策：±1 相邻 bin 偏移 + 方向随 source/delay_used_ps 变化 =
  **source/delay-conditioned channel**（非 alignment blocker）；V25 不重读
  .ttbin、不重估亚 bin delay。
- 数据：3 个 fresh Type2 source（bw 200 ps / frame 204800 ps），pairs.parquet
  行数 512000 / 708352 / 933120；按 frame 时间序 60/20/20 切分。

## 2. M0 — timestamp error map

| source | SER | mass0 | mass +1 | mass −1 | gray0 frac |
|---|---|---|---|---|---|
| type2_1M (delay −50) | 0.2398 | 0.7602 | 0.2384 | 0.0013 | 0.7602 |
| type2_1p5M (delay +50) | 0.2545 | 0.7455 | 0.0012 | 0.2533 | 0.7455 |
| type2_2M (delay +50) | 0.2557 | 0.7443 | 0.0015 | 0.2543 | 0.7443 |

- 误差几乎全部为 {−1, 0, +1} 相邻 bin；中间/大偏移 ≈ 0。‖Δ‖ 集中 0–1。
- Gray popcount 几乎全为 0 或 1 位翻转。

## 3. M1 — channel-model comparison（holdout NLL, bits/symbol）

| source | C01 QSC | C02 V17 product | C03 pooled δ | C04 source δ | C05 δ+parity | C06 jitter+bg |
|---|---|---|---|---|---|---|
| 1M | 3.196 | 3.321 | 0.807 | 0.807 | 0.807 | 0.880 |
| 1p5M | 3.347 | 3.497 | 0.827 | 0.827 | 0.827 | 0.901 |
| 2M | 3.335 | 3.478 | 0.828 | 0.828 | 0.828 | 0.902 |

- 经验 delta 条件模型（C03/C04/C05）holdout NLL ≈ H(A|B) ≈ 0.80–0.83，**远优于
  QSC（3.2）与 V17 independent-plane product（3.3–3.5）**。
- 说明：旧聚合模型丢失了时间戳信道“±1 近邻”结构；`structured_model_beats=
  true`（per-source，全部 holdout）。

## 4. M2 — ±1 structure / direction / time stability（既有 delay 配置）

- 方向稳定：delay −50 → 主 +1（23.8%）；delay +50 → 主 −1（25.3–25.4%）。
- 时间稳定：首/尾 time block 的 ±1 mass 几乎不变（如 2M：+0.148%/−25.8% →
  +0.139%/−25.1%），方向在 frame 序上稳定。
- 结论：方向是 source/delay_used_ps 的稳定条件特征，**不是 alignment blocker**
  （按主线程决策建模，不重读 .ttbin、不重估亚 bin delay）。

## 5. M3 — factorization gate（train，三源均值；chain-rule 闭合 err≤5e-9）

| (F, L) | per-layer H (bits) | 合计 | R_i_ref 示例（f=1.3） |
|---|---|---|---|
| F01 GF512+GF2 | L1=0.410, L2=0.410 | 0.820 | L1 0.941, L2 0.467 |
| F02 GF256+GF4 | L1=0.205, L2=0.615 | 0.820 | L1 0.967, L2 0.600 |
| F03 GF32+GF32 | L1=0.025, L2=0.795 | 0.820 | L1 0.994, L2 0.793 |
| F04 GF16+GF16+GF4 | 0.012/0.192/0.615 | 0.820 | — |
| F05 GF8×3+GF2 | 0.006/0.045/0.359/0.410 | 0.820 | — |

- natural 与 Gray 在该信道上 per-layer H 相同（±1 单 bin 翻转在 MSB→LSB 位切分中
  落入同层）。
- `H(A|B) ≈ 0.80 bits`；分层总和闭合（最坏绝对误差 5e-9）。
- 参考码率：`R_i_ref = 1 − 1.3·H_i/a_i` 仅信息论参考，不代表 DE 可达。

## 6. M4 — V26 candidates

- **高域候选**：`F01 / L01_natural`（GF(512) + GF(2)）
- **中域对照**：`F03 / L01_natural`（GF(32) + GF(32)）
- 选择规则：层数最少 → 平均总条件熵最低（确定性）。
- 总状态：**`pass_ready_for_de_change`**（chain-rule 闭合、结构化模型逐 source holdout
  优于 QSC/V17、分层稳定、无 oracle/holdout 调参）。

## 7. Evidence

- Run root：`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/`
  （data_inventory / split_manifest / channel_summary / delta_by_source.csv /
  gray_joint_masks.csv / channel_counts.npz / model_holdout_scores.csv /
  factorization_layers.csv / chain_rule_check.json / alignment_report.json /
  gate_summary.json / readonly_verify.json）
- 只读 verifier：`ok=true`。
- OpenSpec：`openspec/changes/formal-nonbinary-ldpc-v25-...`（FROZEN_ACCEPTED）。

## 8. Claim boundary

- 渐近/信息论层面：经验信道 + 分层可行；未实现有限码/解码器/FER，未达 f≤1.3 证明，
  未做 qualification/promotion，未用 Alice-oracle/holdout 调参。
- V25 PASS 只“提出”V26（小规模 channel-informed DE），不自动启动；不 push。
