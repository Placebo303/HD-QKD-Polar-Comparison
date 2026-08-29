# Spec: aggressive-timing-calibration

*Affected capability*: `aggressive-timing-calibration` (新增) — 承载 C1 定时校准三步（C1a 固定锚、C1b 死时校准、C1c 窗口/帧锚寻优）在 `_aggressive_v1` 隔离命名空间内的行为契约。

## ADDED Requirements

### Requirement: Aggressive namespace isolation

系统 SHALL 将全部新增序列池、候选目录、重跑产物置于 `_aggressive_v1` 三目录隔离布局（`results/real_sequences_aggressive_v1/`、`results/authoritative_aggressive_v1/`、`results/paper_grade_aggressive_v1/`），且 SHALL 拒绝任何不含 `aggressive_v1` 子串的 `pool_root / out_root / candidate_dir` 写入（fail-closed 守卫）。

### Requirement: Fixed-anchor pilot C1a

C1a SHALL 在 `d=4096 × bw∈{40,200} × tier∈{6,10,16,20}dB` 的 8 格上以固定 `delay_override`（禁用 `pairing_v2` auto-peak 漂移重锚定）物化序列；每次物化 SHALL 在 `sidecar_meta.json` 记录 `delay_override` 与 `used_delay_ps` 且 `used_delay_ps` 在同格多次物化中 SHALL 字节一致（G_timing 锚定一致性）。

### Requirement: Deadtime calibration table C1b

系统 SHALL 提供 `calibration_table`（`results/real_sequences_aggressive_v1/calib/calibration_table_aggressive_v1.json`），其 key 为 `(src_tag, d, bw)`、值为显式单位的死时/堆积/游走参数（`deadtime_ps`, `pileup_coeff`, `walk_coeff` 等），并 SHALL 通过 `calibration_table` 透传参数应用于 `export_joint_sequence_sidecar` 的配对窗口与 singles 校正；`sidecar_meta.json` SHALL 记录 `calibration_table_sha256`；抽 12 格验证 SHALL 在启用校准表后执行 `G_timing` 与 `G_growth` 复筛。

### Requirement: Window and frame-anchor grid search C1c

C1c SHALL 在 12 格验证集上对 `effective_pairing_window_ps` 与 `frame_start_anchor` 做网格搜索（网格由 `explore_report.md` 冻结），以 `IAB_est` / `ser` 为目标选每点最优窗口/锚；结果 SHALL 落盘 `evidence/T3_window_anchor_sweep.csv` 与 `window_anchor_opt.json`，并 SHALL 参与 `G_growth` 终筛的增量增益分解。

### Requirement: Timing gates G_timing

`G_timing` SHALL 包含：(a) 跨档字节唯一性（同 (d,bw) 不同 src_tag 的 `a_eff/b_eff` sha256 零碰撞）；(b) 档均值 ser 严格有序 `6>10>16>20`；(c) 固定锚一致性（`used_delay_ps` 多次物化一致）。逐格 ser 倒置 SHALL 仅记入诊断清单，不作为门控条件（沿用 fix-candidate 终版 lesson）。

### Requirement: Calibration provenance

每个经 C1 路径物化的格 SHALL 在 `materialize_meta.json` / `MANIFEST.csv` 中记录 `source_ttbin` 路径+sha256、`processing_rule_version=pairing_v2`、`src_tag`、`pool_root` 指纹、`delay_override`、`calibration_table_sha256`，以满足 `G4` 溯源完整性校验。

### Requirement: Outlier annotation Q8

16dB `d=2048` 相关格 SHALL 被标注为离群（`evidence/*` 诊断表中单独章节），且 SHALL 不计入 `G_growth` 均值/中位数/正占比统计；其 `peak_sigma` 与 singles 遥测 SHALL 在 T5 old-vs-new 报告中单独分析。
