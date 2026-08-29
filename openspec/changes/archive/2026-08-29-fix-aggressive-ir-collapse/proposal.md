# Proposal: fix-aggressive-ir-collapse

> **关联诊断：`workspace/diag_6dB_collapse_20260828.md`（分支 `polar-aggressive-7x-recovery`，HEAD `847b768` 上 6dB 缺陷只读取证）**
> 本文为该诊断的修复变更提案；未读诊断不得评审本提案。

## 1. Goal

修复 `polar-aggressive-7x-recovery` 在 `results/paper_grade_aggressive_v1/four_loss_parts_frames300_aggressive_v1/` 上已证实的系统性 IR 坍缩，使**四档 6/10/16/20dB 各 121 格**均产出**可归因的正确合理结果**：

- **正 PIE 占比**：每档 `PIE_reconciled_net > 0` 格数从当前 `6dB: 2/121`（仅 `d=4096/bw=180` 0.025 与 `4096/200` 0.005，其余 119 点 `PIE=0, beta=0`）恢复至**合理正值分布**（预期 100+/121，具体阈值由 T1 实测冻结；历史 lossfix 同网格约 27 点 PASS 不可直接对标，但 2/121 为明确异常）。
- **β 经验值**：成功点 `beta_eff_empirical ≈ 0.7–0.8`（由泄漏与错误推导，不手填；AGENTS.md §5.5）。
- **SER 物理性**：同 `bw` 下 `SER` 随 `d` 增大**单调递降且分叉**，消除当前 `coincidence_rate` 跨 `d` 均匀化（`11d` 同值）假象；`raw_ser ≈ map_ser` 去均匀化后回归 lossfix 分布（例 `d=4/bw180` 0.088→0.069 量级）。

全程增量命名 `_aggressive_v1` 不覆盖已落盘结果；冻结基线 `src/experiments/tools` 仅最小透传；从小点 `--only-points 4,180 --debug-layer` 验证到全 `121×4` 全量。

## 2. Why — 问题陈述

诊断 `diag_6dB_collapse_20260828.md` 已定位分叉链路（T0 首现、T1 引爆、T2 透传）：

| 阶段 | 现象 | 证据 |
|---|---|---|
| **T0 配对** | `max_pairs=687388` 固定截断致 `n_pairs/n_pairs_actual` 跨 `d` 恒定 → `coincidence_rate` 同 `bw` 下 11d 完全一致（例 bw20: 168550.33 全d一致） | `seq_pair_stats.json: d4/bw180==d4096/bw180==687388, raw_ser==0.08863`；`_tmp_grid_table.csv` aggressive uniq=1 vs lossfix uniq=3；10dB 同样均匀化（系统性缺陷非 6dB 特有） |
| **T0b map_ser** | 同点 `map_ser` 系统性偏高 ~0.02（`d4/bw180` 0.0886 vs lossfix 0.0694；`d4/bw150` 0.105 vs 0.080 致阈值穿越） | `_tmp_src_table.csv` 22/121 PASS vs lossfix 27/121 |
| **T1 Polar** | `fer_acceptance: one_sided_wilson_upper < 0.05` 过严 + SCL 未尝试：847 层中仅 2 层 `rescue_success=1`（均为 `d4096/Ber<1e-4` 的 `fer_upper=0.042<0.05`），其余 `k_best=0, frozen=4096, decoder_mode=""` | `polar_layer_metrics.csv: 119点 layers_success_best=0, 2点=1`；`d4/bw180 L0 BER0.044 cap0.739 k0 vs lossfix cap0.78 k629` — cap 足够但 Wilson 上界判失败 |
| **T2 IR** | 119 行 `beta_eff_empirical=0.0, leak≈1226` 完全对应 T1 的 `k=0`，非独立根因，仅透传 | `actual_ir_block_table.csv: 119×0 vs 2×>0`；security 表 `cpp_scl_hard_PIE=0` 同步 0 |

已落盘：`loss_6dB 121/121` 但 119 点无效；`10/16dB` 已终止未产废数据；`loss_20dB` 参照干净（AGENT_PROJECT_MEMORY 2026-08-25）。

## 3. What — 交付物

本变更在 `_aggressive_v1` 增量命名空间内交付（不新增 `_v2` 后缀，避免与下游归档混淆）：

- **P0 fer 策略**：`one_sided_wilson_upper<0.05` → `0.10`（或点估计对照）可配置化，4028 行可复现。
- **P1 解码回退**：SC 失败自动 fallback 到 SCL（`scl-16` 默认，不引入 GPU/FPGA），确保非极低 BER 层亦尝试 SCL 并记录 `fer_*`。
- **P2 配对截断**：解除 `max_pairs=687388` 全 `d` 固定截断，改为 `max_pairs` 按 `d×bw` 动态（与 `frame_period_ps=d*bw` 等比）或直接解固定截断（`max_pairs=0` 按真实 TTbin 对数），使 `n_pairs` 随 `d` 递减、`coincidence_rate` 去均匀化。
- **P3 归一化校正**：`map_ser / peak_sigma` 随 `d`/`bw` 的归一化不一致校正，消除小 `d` 高估 `SER 0.088 vs 0.069`。
- **P4 产物对齐**：`actual_ir_block_table.csv` 从 121 行汇总恢复为 `per-block 130k` 行明细（`~121点×`层×300帧，对标 lossfix 130253 行），含 `k_used/rate/leak/block_success` 可细粒度复盘 FER/β。
- **门与验证**：复用 `G0–G4` 并冻结更新 `G_growth`；小点试点 `--only-points 4,180 --debug-layer` 到全量 `121×4` 分阶段验证。

## 4. Non-Goals

- 不承诺固定倍数 PIE 数值；以实测分布与审计表为准（沿用 `polar-aggressive-7x-recovery` §5 语义）。
- **不引入 GPU/FPGA** 硬件加速；SCL 仍为 CPU 实现（用户约束）。
- 不触 `comparison_bench/` Polar 语义；comparison 仅只读桥接。
- 不覆盖 `results/` 既有产物与 `results/paper_grade_aggressive_v1/` 已落盘 121 行（追加 `_aggressive_v1` 同根重跑，旧表保留作对比基线）。
- 不改 `results/paper_grade_v3` / `authoritative` / `authoritative_nsfix` / `paper_grade_v4_rate_search_fix` 只读历史。
- 不引入 SHA-256 清单/原子写/备份回滚等重型防御（AGENTS.md §5.7）；以 Git 基线 + 字节比对为准。
- 不在 T0.5 小点试点通过前启动全量 `121×4` 重跑。
- 不将 `beta_eff_empirical` 手填；仍由泄漏/错误推导。

## 5. Scope

**In scope**

- `src/workflow/export_joint_sequence_sidecar.py`：`max_pairs` 动态化或解固定截断；`map_ser/peak_sigma` 归一化校正；仅新增可选透传参数（默认行为不变）。
- `experiments/run_e2e_pipeline.py` / `experiments/run_real_polar_max_pie.py`：`--fer-threshold`、`--fer-rule {wilson,point}`、`--decoder-modes {sc,scl,auto-fallback}`、`--max-pairs {0,auto}` 的最小 CLI 透传。
- `src/reconciliation/real_polar_sc_rescue.py`：P0 阈值与 P1 fallback 策略参数化（阈值外置，不改内核公式）。
- 新/改工具（仅 `tools/`）：`verify_aggressive_gates.py` 扩展 `G_growth` 门；可选 `sweep_max_pairs_map_ser.py` 小点对比脚本（复用，不新增框架）。
- 输出：`results/real_sequences_aggressive_v1/` 新池（按需重物化）与 `results/paper_grade_aggressive_v1/four_loss_parts_frames300_aggressive_v1/<loss_XXdB>/` 增量重跑（不覆盖旧 121 行，落盘前校验旧表存在）。
- 文档：`docs/decision-log.md` / `AGENT_PROJECT_MEMORY.md` / `docs/troubleshooting.md` 条目。

**Out of scope**

- 冻结基线其余逻辑（Polar SC/SCL 内核、安全有限长公式、finite-key 审计表生成）除 §5 清单外不动。
- `formal IR / binary-LDPC-v4+ / nonbinary-LDPC` 研究线（AGENTS.md §0，归属 sibling 仓库）。
- 任何对 `src/reconciliation/cpp_polar/` 编译产物的改动（除非 P1 需暴露 SCL list-size 参数，已有则复用）。
- 新序列池命名空间 `_aggressive_v2` 等新后缀 — 本变更复用 `_aggressive_v1` 原地修复。
- `wsl-env.sh` / `PROJECT_DATA_ROOT` / 20dB 干净档重建。

## 6. Impact Scope

| 域 | 文件/模块 | 影响 |
|---|---|---|
| 冻结基线透传 | `src/workflow/export_joint_sequence_sidecar.py` | `max_pairs` 动态化（`auto`/`0` 解截断）+ `map_ser` 归一化校正；新增可选参数，`None/0` 时与旧硬编码逐字符一致 |
| 冻结基线透传 | `experiments/run_e2e_pipeline.py` | 新增 `--fer-threshold/--fer-rule/--decoder-modes/--max-pairs` 透传至 worker |
| 冻结基线透传 | `src/reconciliation/real_polar_sc_rescue.py` | `fer_acceptance` 阈值参数化 + SC→SCL fallback 分支（默认 `auto-fallback`） |
| 验证工具 | `tools/verify_aggressive_gates.py` | 扩展 `G_growth` 判定 + `coincidence_rate` 去均匀化校验 |
| 新池（按需） | `results/real_sequences_aggressive_v1/` | 若 P2/P3 需重物化则增量覆盖该池（旧池字节保留作对比） |
| 重跑产物 | `results/paper_grade_aggressive_v1/four_loss_parts_frames300_aggressive_v1/` | 原地重跑覆盖（旧 121 行失真表保留备份 `*.bak_20260828/` 再覆盖） |
| 文档 | `docs/decision-log.md`, `AGENT_PROJECT_MEMORY.md` | T3 收尾追加条目 |

## 7. Affected Specs

- **Delta spec 新增**：`ir-policy`（P0 阈值 + P1 fallback 策略、G_growth 门定义）
- **Delta spec 新增**：`pairing-window`（P2 `max_pairs` 动态化 + `coincidence_rate` 去均匀化 + P3 `map_ser/peak_sigma` 归一化）
- （可选）`output-alignment`（P4 per-block 130k 行对齐）
- 无既有 `openspec/specs/` 需原地修改（增量修复语义）

## 8. Acceptance Criteria（分阶段门，冻结于 design.md §8）

- **T0.5 小点试点**：`4,180` 与 `4096,180` 双点 `--debug-layer` 对比；`n_pairs` 随 `d` 分叉（4096 倍差异回归），`map_ser` 偏高消除，`fer_upper` 在 `0.10` 或点估计下 `k>0`；`beta≠0` 初现；产物落 `evidence/T0_5_pilot_report.md`。
- **T1 全量 6dB 重跑**：`loss_6dB` 121/121 且 `validator 121/121 eps≤1e-10`；`coincidence_rate uniq>1 per bw`；`layers_success_best>0` 显著多于 2；`PIE_reconciled_net>0` 显著多于 2 且 `beta_eff_empirical` 分布 `0.6–0.9`；`SER` 随 `d` 单调递降（档均值有序）。
- **T2 全档 10/16/20dB**：各档 121/121；`coincidence_rate` 全档去均匀化；`map_ser` 校正后跨档 `6>10>16>20` 有序（诊断不门控）；`G0–G4` 全 PASS。
- **T3 门校验**：`G1` 每档 ≥3 格双跑字节一致、`G2` 跨档零碰撞（~574 组）、`G3` 档均值 `ser` 有序 `6>10>16>20` 硬条件、`G4` 溯源完整；`G_growth` 按冻结阈值 PASS（新 vs 失真旧 6dB 的 `ΔPIE` 均值/中位数/正占比）；`old_vs_new` 484 行对比表完成。

## 9. 风险与回滚

- P2 若 `max_pairs=0` 致大 `d` 内存溢出 → 回退至 `max_pairs=auto (∝ d×bw)` 等比截断（design §8）。
- P0 阈值放宽若致 FER 膨胀 → 切 `fer-rule=point` 对照分支，以 `evidence` 择优冻结（design §3）。
- 任一门 FAIL 且非脚本 bug → STOP 不得调参绕过（AGENTS.md §10.1）。

## 10. 约束回声

- 冻结基线仅最小透传（proposal §5 清单），超出需另起 OpenSpec + review-go 三阶（沿用 `polar-aggressive-7x-recovery` Q7）。
- 增量命名 `_aggressive_v1` 不覆盖旧证据（旧 121 行备份后覆盖）。
- 留 2 核（`jobs=18` on 20-logical-core 主机，`workers=12/metric-jobs=12/shards=16` 基准见 `fix-candidate-loss-namespace/evidence/phase4_launch_config.md`）；frames300/seed20260228/tag_bits64 不变。
- 验证路径：小点 `--only-points 4,180 --debug-layer` → 6dB 全量 → 四档全量；G 校验贯穿。

## Appendix — Diagnostics Traceability

| 诊断章节 | 修复优先级 |
|---|---|
| C0.2–C0.3 `max_pairs=687388` 均匀化 | P2 |
| C1.2 `wilson<0.05` 过严 `k=0` | P0 |
| C1.3 SCL 未尝试 | P1 |
| C1.1 `map_ser +0.02` | P3 |
| C2.1 `beta=0` 透传 / 121 vs 130k | P4 |
