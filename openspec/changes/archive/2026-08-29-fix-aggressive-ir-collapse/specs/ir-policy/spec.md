# Spec: ir-policy

*Affected capability*: `ir-policy`（新增）— 承载 P0 fer 策略与 P1 SC→SCL 回退在 `_aggressive_v1` 增量修复中的行为契约；关联诊断 `workspace/diag_6dB_collapse_20260828.md §C1.2–C1.3`。

## ADDED Requirements

### Requirement: FER acceptance threshold shall be configurable and frozen

系统 SHALL 将 `fer_acceptance` 判定外置为参数 `fer_threshold: float` 与 `fer_rule: {one_sided_wilson_upper_lt_threshold, point_estimate_lt_threshold}`，且 SHALL 在 `experiments/run_e2e_pipeline.py` 以 `--fer-threshold` / `--fer-rule` 透传至 `src/reconciliation/real_polar_sc_rescue.py` 的码率搜索；默认行为 SHALL 与旧 `wilson<0.05` 逐字符一致（不传参等价断言覆盖），修复后冻结值 SHALL 写入 `evidence/gates_frozen.json: G_fer.threshold/rule` 且后续 T1–T3 SHALL NOT 漂移。

- **修复值**：`G_fer.threshold` SHALL 为 `0.10`（或点估计对照分支胜者），由 T0.5 小点 `4,180 vs 4096,180 --debug-layer` 8 组对照择优冻结。
- **校验**：`d=4/bw=180 L0 (BER≈0.044 cap≈0.739)` 在冻结阈值下 SHALL 使 `k_best>0`（对标 lossfix `k≈629`），且 `d=4096/bw=180 (BER<1e-4)` SHALL 保持 `k≈2021 fer_upper≈0.042` 不退化；`polar_layer_metrics.csv` 的 `fer_errors/fer_trials/fer_upper_bound` SHALL 非空可审计。

### Requirement: Decoder shall auto-fallback from SC to SCL

当 `decoder_modes=auto-fallback` 时，系统 SHALL 先以 SC 搜索 `k`，若 `fer_upper ≥ G_fer.threshold` 则 SHALL 自动以 SCL-16 重搜同一 `k` 候选（复用 `src/reconciliation/cpp_scl_wrapper.py`，不引入 GPU/FPGA）；`polar_layer_metrics.csv` 每层 SHALL 记录 `decoder_mode_best ∈ {sc,scl}` 非空，`fer_*` 非空，且 `polar_e2e_results.csv` 的 `layers_success_scl` SHALL 显著多于失真旧表的 2（T1 验收）。

- 不传参或显式 `--decoder-modes sc` 时 SHALL 与旧 SC 单路径逐字符一致（默认行为等价断言）。

### Requirement: Beta shall remain derived, not hand-filled

`beta_eff_empirical` SHALL 始终由 `actual_ir_block_table.csv` 明细的 `Σk_best / Σleak_EC_actual_bits` 与 `capacity` 推导，MUST NOT 手填或硬编码；`leak_EC_actual_bits` SHALL 随 `decoder_mode` 与 `k` 联动重算（AGENTS.md §5.5）。

### Requirement: G_growth gate shall be frozen and evaluated

`G_growth` SHALL 定义为新修复表 vs 失真旧表（`*.bak_20260828`）在同 `121` 格上的 `ΔPIE = PIE_new - PIE_old` 的三阈值判定：`mean ΔPIE ≥ G_growth.mean_delta_PIE` 或 `median ΔPIE ≥ G_growth.median_delta_PIE` 或 `positive_frac ≥ G_growth.positive_frac`；阈值 SHALL 由 T0.5 小点择优冻结于 `gates_frozen.json`，T1 对 6dB 121 格初筛、T3 对 484 格终筛，任一阈值 PASS 即门 PASS，否则 SHALL STOP 不得调参绕过。

### Requirement: Per-block IR table shall be auditable

`actual_ir_block_table.csv` 明细 SHALL 满足 `G1` 每档 ≥3 格双跑字节一致与 `G4` 溯源完整（`source_ttbin/sha256/processing_rule_version/pairing_path/fer_threshold/decoder_mode`）；`security_calibrated_master_table.csv` 的 `cpp_scl_hard_PIE` 零值点 SHALL 与明细推导的 `PIE_reconciled_net` 零值点一致（T2 透传一致性，diag §C2.2）。

### Requirement: Status shall not gate on map_ser

`polar_e2e_results.csv` 的 `status` 列 SHALL NOT 依赖 `map_ser` 或 `sidecar_verdict` 的 `0.1` 门限；`sidecar_verdict`/`map_ser` SHALL 仅作诊断列保留（`polar_diag_summary.csv` 同列）。`status` SHALL 仅由真实译码结果判定：`layers_success_best>0`（或 `k_best>0`/`rescue_success==1`）则 `PASS`，否则 `FAIL`；无译码产出（如 `missing_sidecar`、`k==0` 全层失败）则 `FAIL`，若无任何真实失败则全 `PASS`。高维在高 SER 仍成钥，算出来的即真实结果。

## MODIFIED Requirements

（无既有 spec 原地修改；本 delta 为增量修复语义，冻结期外不溯及 `polar-aggressive-7x-recovery` 已落盘失真表。）

## REMOVED Requirements

（无）
