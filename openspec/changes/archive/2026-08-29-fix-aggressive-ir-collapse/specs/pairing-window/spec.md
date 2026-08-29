# Spec: pairing-window

*Affected capability*: `pairing-window`（新增）— 承载 P2 `max_pairs` 动态化与 P3 `map_ser/peak_sigma` 归一化在 `_aggressive_v1` 增量修复中的行为契约；关联诊断 `workspace/diag_6dB_collapse_20260828.md §C0.2–C0.3, C0.1, C1.1`。

## ADDED Requirements

### Requirement: max_pairs shall be dynamic per d×bw, not fixed 687388

`src/workflow/export_joint_sequence_sidecar.py` 的 `max_pairs` SHALL NOT 固定为 `687388` 全 `d` 恒定；其 SHALL 支持 `0`（解固定截断，按真实 TTbin candidate pairs 全量）与 `auto`（按 `d×bw` 等比 `max_pairs = base_pairs * (d*bw)/(d0*bw0)`，`base_pairs` 取 `d=4,bw=20` 实测值）两档策略，且 SHALL 经 `experiments/run_e2e_pipeline.py --max-pairs {0,auto,<int>}` 透传；不传参且旧默认保留时 SHALL 与旧 `687388` 逐字符一致（等价断言），修复后冻结值 SHALL 写入 `evidence/gates_frozen.json: max_pairs_strategy`。

- **校验（G_pairing）**：同 `bw` 下 `seq_pair_stats.json` 的 `n_pairs/n_pairs_actual` SHALL 随 `d` 单调分叉（例 `bw180: d4≈224k vs d4096≈687k` 量级回归 lossfix），且 `_tmp_grid_table.csv` / `polar_diag_summary.csv` 的 `coincidence_rate_hz` 在每 `bw` 下 `uniq>1`（去均匀化），否则 `G_pairing` FAIL → 回退至 `auto`（design §8.3）。

### Requirement: Pairing window shall remain bw_fallback with explicit trace

`effective_pairing_window_ps` SHALL 保持 `bw_fallback` 语义（`effective == bw`，`pairing_window_source_tag=bw_fallback`，`threshold_ratio_to_bw=1.0`，`pairing_mode=nearest`），诊断已证 `bw_fallback` 非均匀化根因（diag §C0.3）；系统 SHALL 在 `sidecar_meta.json` 显式记录 `effective_pairing_window_ps / pairing_window_source_tag / frame_period_ps (=d*bw) / max_pairs_strategy / max_pairs_actual` 供 `G_pairing` 溯源。

### Requirement: map_ser and peak_sigma shall be normalized per d

`map_ser` 与 `peak_sigma_ps` 的计算 SHALL 按 `d` 归一化校正，使同 `(d,bw)` 点的 `map_ser` 系统性偏高 `+0.02`（`d4/bw180 0.0886 vs lossfix 0.0694`，`d4/bw150 0.105 vs 0.080`）消除；校正后同点差值 SHALL ≤0.01。`map_ser`/`sidecar_verdict` SHALL 仅作诊断列，不参与 `status` 的 PASS/FAIL 判定（高维在高 SER 仍成钥，算出来的即真实结果）。

- `polar_diag_summary.csv` 的 `peak_sigma_ps / peak_center_ps / peak_to_bg` 随 `d` 递增单调性 SHALL 可复现（`d4 53.7 vs d4096 150.24` 量级），`near_neighbor_frac==1.0` 时 100% ±1 邻 bin 错误语义（AGENT_PROJECT_MEMORY 2026-08-26）保持不变。
- `status` SHALL 仅由 `k_best>0` / `rescue_success` / `layers_success_best>0` 等真实译码成功判定（有 k 则 PASS，否则 FAIL）；`sidecar_verdict` 不参与 `status`。

### Requirement: SER shall decrease monotonically with d per bw

修复后每 `bw` 下 `raw_ser / map_ser` 随 `d` 增大 SHALL 单调递降且分叉（`11d` 不再同值），且档均值 `ser` SHALL 严格有序 `6dB > 10dB > 16dB > 20dB`（`G3` 硬条件，逐格倒置仅诊断清单，不门控，沿用 fix-candidate 终版 lesson）。

### Requirement: Per-block vs summary alignment shall hold (P4)

`actual_ir_block_table.csv` 明细 SHALL 从 121 行汇总恢复为 per-block `≈130k` 行（`121点×层×300帧`，容差 ±5%），列 SHALL 含 `point_id/d/bw/layer_idx/block_index/decoder_mode_used/k_used/rate_used/total_leak_ec_bits/block_success_flag/fer_upper`（对齐 lossfix 130253 行 schema）；汇总视图 `actual_ir_block_summary.csv`（121 行，`mean beta/PIE`）SHALL 与明细的 `Σk/Σleak` 推导一致（容差 `1e-9`），且 `beta_eff_empirical` SHALL 由明细推导可复现。

### Requirement: Provenance shall include pairing and FER fingerprints

每个经本 spec 路径物化的格 SHALL 在 `materialize_meta.json / MANIFEST.csv / sidecar_meta.json` 记录 `source_ttbin/sha256 / processing_rule_version=pairing_v2 / src_tag / pool_root（含 aggressive_v1）/ max_pairs_strategy / max_pairs_actual / fer_threshold / fer_rule / decoder_mode_best`，以满足 `G4` 溯源完整性与 `G1` 双跑字节一致校验。

## MODIFIED Requirements

（无既有 spec 原地修改）

## REMOVED Requirements

（无）
