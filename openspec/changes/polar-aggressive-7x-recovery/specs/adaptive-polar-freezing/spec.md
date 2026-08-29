# Spec: adaptive-polar-freezing

*Affected capability*: `adaptive-polar-freezing` (新增) — 承载 C2 解码器升级（Tal-Vardy 轻版 → 全 GA 信道自适应冻结序、SCL16、块长、层丢弃）在 `_aggressive_v1` 隔离命名空间内的行为契约。

## ADDED Requirements

### Requirement: Adaptive freeze order — Tal-Vardy lite first

C2 SHALL 分步实施：先交付 Tal-Vardy 轻版自适应冻结序（per-layer BER 估计 + 极化权重构冻结序，`--freeze-order tal_vardy_lite`），在 T3 最优配置的 12 格上对比 PW 固定序的 `ΔPIE`；轻版验证通过后 SHALL 再推进全 GA 冻结序（`--freeze-order ga_full`），否则 SHALL 保留轻版为 C2 终态。

### Requirement: Adaptive freeze order — full GA

全 GA 冻结序 SHALL 基于密度演进（density evolution / Gaussian approximation）为每层独立构造最优冻结序；每层的 `k_best` SHALL 与冻结序一一对应且可复现；高噪声层（`BER≥3.8%`）的码率 gap 回收 SHALL 在 `evidence/T4_ga_full_report.md` 中以逐层 `ΔPIE` 表举证。

### Requirement: SCL16 with layer drop L10/11

SCL 解码器 SHALL 支持 `--scl-list-size 16`（Q4：从 4 升至 16），并 SHALL 在 `d=4096` 时丢弃净负层 `L10/11`（最高两层，`net_layer < 0`），重算 `leak_EC_actual_bits` 与 `accepted_frame_fraction` 分摊；`beta_eff_empirical` SHALL 仍由泄漏与错误推导，不手填（AGENTS.md §5.5）；结果 SHALL 落 `evidence/T4_scl16_drop_report.md`。

### Requirement: Block length evaluation

块长评估 SHALL 在 12 格子集（4 格抽样）上对比 `n=4096` vs `n=8192` 的 `ΔPIE` 与解码成本（`--block-length`），产出成本-增益对照表 `evidence/T4_block_length_report.md`；是否将 `n=8192` 推广至全量 121 格 SHALL 由主线在 T4.6 review 中裁决，未裁决前不得进入 T5 全量 8192。

### Requirement: Layer-drop accounting

层丢弃记账 SHALL 复用 `results/diagnostics/leak_negative_layer_accounting_20260814/run_accounting.py` 的 `net_layer < 0` 丢弃语义（含验证位分摊重算），在 12 格最优配置上搜索最优丢弃掩码，落盘 `evidence/T3_layer_drop_mask.json`；92 点转正逻辑 SHALL 可复现。

### Requirement: C2 growth gate and decomposition

C2 各子项（Tal-Vardy / GA / SCL16 / 块长）的增量 `ΔPIE` SHALL 在 `evidence/T4_gain_decomposition.csv` 中分层分解，且 C1 与 C2 增益 SHALL 分表对照以避免混淆；`G_growth` 终筛（阈值来自 `evidence/gates_frozen.json`）PASS 后 SHALL 进入 T5，否则 SHALL 仅 C1 产物进入审计。

### Requirement: Frozen baseline touch boundary

C2 涉及的冻结基线触碰 SHALL 仅限 `design.md §3` 清单（`pool_root / delay_override / calibration_table` 透传 + `--freeze-order / --scl-list-size / --block-length` 新增 CLI 旗标），默认行为 SHALL 与旧调用逐字节兼容；任何超出清单的 `src/reconciliation/*` 内核改动 SHALL 另起独立 OpenSpec 并重走 review-go 三阶（Q7）。
