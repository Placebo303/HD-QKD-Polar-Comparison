# OpenSpec Tasks: formal-ir-v56d1-raw-a2-diagnosis

**Lifecycle**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — **decoder-free raw-A2 诊断，不运行 L1/L2 decoder，不改方法，不重跑原 90 块。**
**Execution status**: 本轮仅完成 `proposal/design/tasks` + `diagnosis_raw_a2.py` (decoder-free) + `REPORT.md` (per-source peak/channel/contract/B判定) 的诊断交付；不创建 `run_01`，不冻新 registry。
**HEAD**: `4914b56d8d353e7445a621fb142f340c37245f12` (branch `formal-ir-mainline`, V56 固化后最新) + data SHA `84d62779603e62de50ded5182ed65b65d3dc6084` (84d62779 200ps legacy_v1 nearest 1024)
**Predecessor**: `formal-ir-v56-input-domain-diagnosis` (V56D0, `4914b56d...` 固化, `INCONCLUSIVE_METADATA_INCOMPLETE`, A1 已排除 `k*=0`)
**Method frozen**: `H1-16/Lane C m2 184/190/192/H_inc1/2 Δ8+8/decoder 90/1.0 poly37/L2-only tag/TRAIN prior` 零改，诊断期间禁止调任一参数，**零 decoder、零码参数**

## Phase A — Raw TTBin channel 校验与 cross-correlation 重算（decoder-free，读原始 TTBin）

- [ ] **A1** 从三个原始 TTBin 读取真实 channel IDs（A1/B5 声明校验）：由 `comparison_bench/outputs_comparison/v55_intake_20260828/intake_report.json:provenance[].path` 解析三源双文件路径（`20260123_1M_600k_0dB` / `20260107_PPLN_1p5M` / `20260123_2M_1p2M_0dB` 各 `.ttbin` + `.1.ttbin`），调用 `src/qkd_io/ttbin_pipeline.read_ttbin_events` 读取 `channel / time_ps / event_type`，统计 `channel_hist`（`unique_channels`, `count_A(1)`, `count_B(5)`, `other_channels`, `frac_A/B/other`），校验声明 `materialize_params.channels {A:1,B:5}` 的 `PASS/MISMATCH/INCOMPLETE`（若 TimeTagger 不可用则 `INCOMPLETE_TTBin_UNAVAILABLE` 降级，不伪造）
- [ ] **A2** 重算 timestamp cross-correlation：对每源调用 `compute_cross_correlation_histogram(ch_a=1,ch_b=5,bin_width_ps=100,max_lag_ps=819200)`（`n_bins 16384`, `lag = t_B - t_A`），得 `lag_center_ps[16384]` + `counts[16384]`；找 `peak_idx = argmax counts`，输出 `peak_center_ps = lag_center[peak_idx]`、`peak_count`、`peak_width_ps`（FWHM→σ, `σ≈FWHM/2.355`）、`peak_to_bg = peak_count / bg_median`（`bg = median(counts where |lag-peak|>5σ or >2000ps)`）、`delay_sign = sign(peak_center)`、`total_pairs_in_window`、`acquisition_duration_s`；报告每源三值与直方图摘要，注明 `bin_width 100 / max_lag 819200 / n_bins 16384` 固定口径
- [ ] **A3** 失败降级与可复现：若 `TimeTagger.FileReader` 不可用或文件缺失，输出 `INCOMPLETE_TTBin_UNAVAILABLE` 并记录 `TimeTagger available=false`，不伪造 peak；可用时 deterministic（`numpy` 固定、TTBin 排序、`lag = t_B - t_A` 显式），输出含 `HEAD 4914b56d / data SHA 84d62779 / run_at / input SHAs`

## Phase B — 契约字段审计 vs V13 实时读（decoder-free，不硬编码）

- [ ] **B1** 只读核对 V13 2026-01-21 三源元数据：**读取实际** `workspace/v13r3fresh_20260816/sidecars/*/sidecar_meta.json` 的 `used_params`（`delay_used_ps / peak_center_ps / peak_sigma_ps / corr_argmax / corr_bins / corr_max / peak_to_bg / pairing_threshold_ps / gate_width_ps / pairing_mode / frame_start_ps / frame_anchor / mapping / wrap_rule / occupancy_filter / frame_period_ps`）+ `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/build_manifest.json` 的 `provenance/source_ttbin_paths` + `nbldpc_v25_20260818/run_04/data_inventory.json/channel_summary.json` 的 `delta_by_source`，**不硬编码 `-50/+50/8191`** 等值，缺失如实 `INCOMPLETE`，有值才记 `PASS` 并记录 `_value`
- [ ] **B2** 只读核对 V55 三候选 2026.1.23/2026.1.07 三源契约：读取实际 `v55_intake_20260828/intake_report.json` + `sidecars/*/sidecar_meta.json` 的实际 `materialize_params/used_params` 字段 + `v55_authoritative_registry.json`，逐项标记 `PASS/MISMATCH/INCOMPLETE` 按实际文件内容；对 `nearest_threshold_ps / pairing_direction / frame_start_ps / bin_origin / wrap_rule / gate_width_ps / delay_used_ps / peak_center` 等与 **A 相 raw 实测峰** 比对（`|peak_center - delay_used|<50ps` 则 PASS，否则 MISMATCH），V55 缺则 `INCOMPLETE`，不自动判 A2
- [ ] **B3** 生成契约对比矩阵（`V13 实时读 vs V55 raw实测+sidecar声明`，见 design §2.2），输出逐字段 `PASS/MISMATCH/INCOMPLETE` 表，重点标记 `delay_used_ps / peak_center / peak_sigma / corr_argmax / frame_start_ps / bin_origin / wrap_rule / pairing_threshold / pairing_direction` 的缺失或不一致；结论写入 `REPORT.md §2-3` 且与 `diagnosis_raw_a2.json:contract_matrix` 一致；该矩阵为后续 A2 判定的先验证据

## Phase C — 逐源 A2 判定与总体四态（decoder-free，三源逐源 + 总体四态）

- [ ] **C1** 逐源 A2 判定（raw 证据驱动）：
  - `INCOMPLETE_TTBin_UNAVAILABLE`：若 TimeTagger 不可用或文件缺失 → 该源 `INCONCLUSIVE_NEED_CALIBRATION`（INCOMPLETE_TTBin_UNAVAILABLE）
  - `PATH_A2_RAW_CONTRACT_ERROR`：若 `peak_missing`（`p2bg<10` 或无单峰）或 `|peak_center - delay_used|>50ps`（delay 已知时）或 `σ>150ps` 弥散或 `channel_mismatch`（`count_A/B` 非主导 `<40%`）或 `nearest_threshold !=40000ps` / `pairing_direction` 反向 / `frame_start` 错位且 raw 证据确凿 → 该源 `PATH_A2`（可修复）
  - `PATH_B_DOMAIN_SHIFT`：若 `peak_healthy`（`|peak-delay|<50ps && p2bg>1000 && σ 50-150ps`）但 `A==B 27-41%`、`NLL>>1.0`、`q_mass_on_p_zero 57-71%` 仍低（沿用 V56D0 parquet 统计作背景）→ 该源 `PATH_B`（需重估熵/泄漏）
  - 否则 `INCONCLUSIVE` / `INCONCLUSIVE_METADATA_INCOMPLETE`
- [ ] **C2** 总体四态聚合（三源逐源 → 总体）：
  - `PATH_A2_ALL`（三源全 A2） / `PATH_B_ALL`（三源全 B） / `MIXED_BY_SOURCE`（源间 A2/B/INCONCLUSIVE 混合） / `INCONCLUSIVE`（含 `INCONCLUSIVE_METADATA_INCOMPLETE`、`INCOMPLETE_TTBin_UNAVAILABLE`）
  - 显式声明 `A1` 已由 V56D0 排除（`k*=0`），本诊断不再判 A1；`B` 为排除 A2 后物理域迁移
- [ ] **C3** 守卫：判定以 raw 实测峰为准，不以 `V25 P(A|B)` 重估；不对 parquet 做 offset 扫描重判；不将 `peak` 择优回注为新 pipeline；注明 `lag = t_B - t_A` 显式

## Phase D — 逐源分流后的修复/重估建议与校准优先（A2/B 分支）

- [ ] **D1** 若某源 `PATH_A2`，输出 **A2 修复建议**（sidecar 必填 `channels/delay_used/peak_center/σ/corr_argmax/frame_start/bin_origin/wrap_rule/pairing_threshold/gate_width` + FileReader 显式绑定 `raw_ch0_id=1/raw_ch1_id=5/threshold 40000/offset=peak_center/frame_start=peak_center` 校验 `|delay-peak|<50ps` + per-source G1'-G3' 门 `peak_status ok && p2bg>1000 && σ 50-150ps`），声明原 90 已揭盲不可复用，**可修复后用 0 重叠 calibration frames 验证**（与原 90 零重叠、未揭盲、每源 8-16 frames 小批量，`A==B>60%` HEALTHY）
- [ ] **D2** 若某源 `PATH_B`，输出 **重估清单**（`N_ab → H(A|B) → F03 H(U1|B),H(U2|U1,B) → m_total/f` source-adaptive 重算 `m_total=floor((1.3*1024*H-64)/5)`，见 design §3.2），并声明当前 `m2/leak` 预算缺口；`MIXED_BY_SOURCE` 时按源分别给建议
- [ ] **D3** 无论何种总体终态，均冻结**校准优先原则**：必须先用**独立 calibration frames**（与原 90 零重叠、未揭盲、每源 8-16 frames 小批量）验证基础相关性（健康参考 `A==B>60% NLL<1.0 p2bg>1000` 仅作描述），通过后再另冻新 blocks 进入 qualification；本诊断不直接冻结新 blocks
- [ ] **D4** 原 90 已揭盲保护：显式禁止在 `v55_authoritative_registry.json` 90-block 上重跑任何 corrected pipeline（含 peak-corrected 重译），违者诊断作废

## Phase E — 诊断脚本与报告交付（DIAGNOSIS_PLAN_READY）

- [ ] **E1** 实现 `diagnosis_raw_a2.py` (decoder-free, 本变更目录下)：
  - 接口 `python diagnosis_raw_a2.py [--intake-report ...] [--v13-sidecar-root ...] [--counts ...] [--registry ...] [--out ...] [--recompute-corr]`，默认由 `intake_report.json:provenance` 解析三源双文件 + `workspace/v13r3fresh_20260816/sidecars` 实时读 V13 + `channel_counts.npz` 仅作背景
  - 产出 `diagnosis_raw_a2.json` (含 `head 4914b56d / data SHA 84d62779 / per_source {channel_hist, peak_center/width/p2bg/delay_sign, contract_row, per_source_decision} / overall_shunt / metadata_matrix`) + 控制台摘要
  - 守卫：`rg "decode_" 0 hits`, `rg "import.*decoder" 0`, 仅 `numpy/pandas/pyarrow + ttbin_pipeline(TimeTagger optional)`，零 `construct_*` 调用；TTBin 不可用时 `INCOMPLETE_TTBin_UNAVAILABLE` 不伪造；`py_compile` PASS
- [ ] **E2** 撰写 `REPORT.md`（待填充 → 回填实测值）：记录每源 `channel 校验 / peak_center/width/p2bg/delay_sign / total_pairs`、V13 实时读值 vs V55 raw 实测对比矩阵、逐源 A2/B 判定与总体四态、修复/重估建议与校准优先清单；数据与 `diagnosis_raw_a2.json` 一致，显式声明不扩大为 FER/阈值/SKR/晋升、不宣称 LDPC 证伪
- [ ] **E3** 自检与交付：`python diagnosis_raw_a2.py --help` 可运行，`rg` 守卫 0 命中，`REPORT.md` 与 json 数值一致（或 `INCOMPLETE_TTBin_UNAVAILABLE` 降级一致），`proposal/design/tasks` 与报告结论一致，已达 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`，`HEAD 4914b56d` 已绑定
- [ ] **E4** 推送并停留 `DIAGNOSIS_PLAN_READY`，未创建任何 `.../v56d1_*/run_01` 或新 registry，等待 successor `calibration` / `contract-fix` / `entropy-reestimation` 的独立授权

## 本诊断期间显式禁止

decoder 调用（任何 `decode_*` / `construct_lane_c_prototype` / `sample_uniform_gf32_nonzero` 等）；在原 V55 authoritative 90-block 上重跑任何 corrected pipeline（含 peak-corrected 重译）；调 `H1/Lane C/Δ8/decoder 90/1.0/m2/leak/prior` 任一冻结参数；宣称 LDPC/NB-LDPC 证伪或 FER/阈值/SKR/晋升结论；创建正式 `.../v56d1_*/run_01` 或新 registry/新校准 blocks（校准需 successor）；以 peak/offset 扫描择优值回注为新 pipeline；将 `0/90` 记为算法失败；自授 `EXECUTE_AUTH` 或伪造 `DIAGNOSIS_PLAN_READY`；**零 decoder、零码参数**。

## 验收（本诊断）

- `proposal.md/design.md/tasks.md` 与 `diagnosis_raw_a2.py` + `REPORT.md` 5 文件齐全一致，`HEAD 4914b56d` + `84d62779` 已绑定，lifecycle `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` 明确，`rg "decode_" 0 hits`
- Raw channel 校验与 cross-correlation 重算（`bin100 / max_lag819200 / 16384 bins`）已生成每源 `peak_center/width/p2bg/delay_sign`（或 `INCOMPLETE_TTBin_UNAVAILABLE` 降级），并与 V13 实时读值对比
- 契约审计矩阵 `PASS/MISMATCH/INCOMPLETE` 已生成且指出 `nearest_threshold / pairing_direction / frame_start / bin_origin` 等字段状态
- 逐源 A2 判定与总体四态 `PATH_A2_ALL / PATH_B_ALL / MIXED / INCONCLUSIVE` 已互斥给出且与 raw 证据链闭合，含修复（0重叠 calibration 验证）/重估建议与已揭盲保护、校准优先硬约束
- 脚本 `rg` 守卫 0 命中、`py_compile` PASS、`REPORT.md` 与 json 一致、未创建新 registry/run_01，已推至 `DIAGNOSIS_PLAN_READY`
