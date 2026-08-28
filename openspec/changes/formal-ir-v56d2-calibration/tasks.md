# OpenSpec Tasks: formal-ir-v56d2-calibration

**Lifecycle**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — **decoder-free 零重叠物化校准，不运行 L1/L2 decoder**
**HEAD**: `73bb21669c1b76039a6981151d8cc0008dc778d0` (branch `formal-ir-mainline`, V56D1 固化后) + data SHA `84d62779603e62de50ded5182ed65b65d3dc6084`
**Predecessor**: `formal-ir-v56d1-raw-a2-diagnosis` (MIXED_BY_SOURCE: 1M/2M PATH_A2 frac_B36% / 1p5M INCONCLUSIVE, peak 127ps p2bg708/629/378<1000 raw, timing INCOMPLETE)

## Phase A — Raw TTBin 显式重算与落盘（decoder-free, 唯一 delay 符号 -50/+50 不择优）

- [ ] **A1** 读 `v55_authoritative_registry.json: strata[].provenance[].path+sha256` 三源双文件 `*.ttbin+*.1.ttbin`，调用 `read_ttbin_events(main)` 统计 `channel_hist {unique, count_A1/count_B5/other, frac_A/B/other, total_events, acquisition_duration_s, ttbin_merge {main_size,chunk_size,merge_verified}}`，并 `compute_cross_correlation_histogram(ch_a=1,ch_b=5,bin100/max_lag819200/n16384, lag=t_B-t_A)` 得 `peak_center/σ(FWHM/2.355)/peak_count/p2bg=peak/bg_median/delay_sign`；若 TimeTagger 缺失则 `INCOMPLETE_TTBin_UNAVAILABLE` 不伪造
- [ ] **A2** 声明唯一 `delay_used -50/+50/-50` (1M `-50`, 1p5M `+50`, 2M `-50` 与 raw `peak ±50` 对齐) 不择优，落盘每源 `sidecar_meta.json: used_params={delay_used_ps, peak_center_ps, peak_sigma_ps, corr_argmax, corr_bins, peak_to_bg, peak_status, channels {A:1,B:5}, gate_width_ps 200, pairing_threshold_ps 40000, frame_start_ps, frame_anchor, mapping, wrap_rule floor_div, frame_period_ps 204800, occupancy_filter}` + `provenance/sha256`，机械校验 `|peak - delay|<50ps` 且 `sign一致`
- [ ] **A3** 实时读 `workspace/v13r3fresh_20260816/sidecars/*/sidecar_meta.json` 的 `delay -50/+50 σ74/88/103 p2bg3300-3800` 仅作对照，不硬编码判定

## Phase B — 8-16 零重叠 calibration frames 预注册（与 V55 90块零重叠）

- [ ] **B1** 解析 `v55_authoritative_registry.json: strata[].F/K/selected_frame_ids` (1M F2130 / 1p5M 5125 / 2M 5513, 各 30 blocks, gap≥4)，为每源预注册 `8-16 frames = 2-4 blocks×4` 连续帧，`pairs_per_frame 256`，`frame_id ∈ [0,F-1]`
- [ ] **B2** 机械校验 `set(calibration_frame_ids) ∩ set(V55_frame_ids) == ∅` 且 `gap≥4`，输出 `calibration_registry.json + calibration_manifest.json {overall_zero_overlap_verified, per_source_zero_overlap}`
- [ ] **B3** 失败则 `FAIL_NEED_FIX` 停留，不进 qualification

## Phase C — 双合同解耦验证（timing + routing, decoder-free）

- [ ] **C1** Timing 合同时刻：`peak_shape_ok (50≤σ≤150)` + `timing_ok (|peak-delay|<50 && sign一致)` + `gate_ok (gate200/threshold40000/frame_start已落盘)` + `p2bg_assessed` → `timing_contract_verified`；单项失败即 `timing FAIL`
- [ ] **C2** 通道路由：`frac_A≥40% && frac_B≥40% && other<20% && unique⊇{1,5}` → `routing_contract_verified`；V56D1 `frac_B36.5%/36.4%` 习题需校准后≥40%才过
- [ ] **C3** p2bg>1000 兼容性分源评估：`HEALTHY>1000 / PARTIAL 500-1000 / LOW<500` 三档，`708/629` 为 PARTIAL、`378` 为 LOW；评估 `should_share_threshold_across_acquisitions` 是否跨三采集强制共用，报告 `recommended_per_source_threshold`；`PARTIAL` 允许通过但 `p2bg_partial_warn`，`LOW` 需核查；不得直接硬套共阈一刀切
- [ ] **C4** 双合同均 `true` 才校准通过，否则 `CALIBRATION_FAIL_NEED_FIX`

## Phase D — 基础相关性与 NLL 回落验证（decoder-free, V25 prior）

- [ ] **D1** 在 calibration 小批量 `8-16 frames` 上统计 `A==B_rate` (从 V55 27-41% 向 >60% 回升)、`U1/U2` (F03 5+5)、`delta mass_0+mass_±1`
- [ ] **D2** V25 `channel_counts.npz` column-norm `P(A|B)` 算 `NLL bits/block` 从 `28-35` 向 `V13 0.82*1024` 靠近，`q_mass_on_p_zero` 从 `57-71%` 向 `3%` 回落；未达即 `FAIL_NEED_FIX` 不进 qualification
- [ ] **D3** 三源全 `calibration_pass` 标志 `overall PASS`，否则 `MIXED/FAIL` 按源分别修sidecar/重审阈值，分源阈值另行记录

## Phase E — 脚本与报告交付（DIAGNOSIS_PLAN_READY）

- [ ] **E1** 实现 `v56d2_calibration.py` (decoder-free, 本变更目录下): `python v56d2_calibration.py [--registry ...] [--intake-report ...] [--v13-root ...] [--counts ...] [--out v56d2_calibration.json] [--recompute-corr]` → 重算 peak/channel + 落盘 sidecar + 零重叠预注册 + 双合同 + 相关性/NLL/p2bg分源评估；守卫 `rg "decode_" 0 hits` 仅 `numpy/pandas/pyarrow + ttbin_pipeline`，`py_compile` PASS
- [ ] **E2** 撰写 `CALIBRATION_REPORT.md` (待填充→回填实测值): 每源 `落盘值/通道 frac_A/B/other / timing+routing 双门 / A==B/NLL/q_mass / p2bg三档分源评估` + 总体 `PASS/FAIL_NEED_FIX` 与 `should_share_p2bg_threshold` 结论，数据与 `v56d2_calibration.json` 一致，不扩大为 FER/阈值/SKR/晋升，显式原 90 已揭盲不可复用
- [ ] **E3** 自检：`py_compile` PASS, `rg "decode_" 0 hits`, `set(CAL)∩set(V55)==∅` 已验, `|peak-delay|<50` 已验, `frac_B≥40%` 已验, `CALIBRATION_REPORT` 与 json 一致
- [ ] **E4** 推送并停留 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`，未创建任何 `.../v56d2_*/run_01` decoder 执行；三源全 PASS 后另起 successor 冻全新 TEST blocks 再 qualification

## 本校准显式禁止

decoder 调用 (`decode_*` / `construct_*` / `sample_uniform_gf32` 等)；在原 V55 90-block 上重跑任何 corrected pipeline（含 peak-corrected 重译）；调 `H1/Lane C/Δ8/decoder 90/1.0/m2/leak/prior` 任一冻结参数；宣称 LDPC 证伪或 FER/阈值/SKR/晋升；创建正式 `.../v56d2_*/run_01` decoder 执行；跨三采集硬套 `p2bg>1000` 一刀切而不做分源评估；择优多 delay 符号。

## 验收

- proposal/design/tasks/specs 一致 HEAD 73bb2166 84d62779 lifecycle DIAGNOSIS_PLAN_READY DECODE_FORBIDDEN 明确
- 每源 sidecar 已显式落盘 `delay -50/+50/-50` + `peak ±50 σ127 p2bg 708/629/378` + `|peak-delay|<50` 可机械校验，唯一符号不择优
- 每源 8-16 frames 零重叠已预注册且 `set∩==∅` 已验
- 双合同 `timing+routing` 逐源判定 + `p2bg>1000` 分源三档评估已报告
- `A==B>60%` + `NLL 28-35→0.82` + `q_mass 57-71%→3%` 回落已核验或 `FAIL_NEED_FIX`
- 脚本 `rg 0 hits` `py_compile` PASS 报告与 json 一致 未建 run_01 已推 DIAGNOSIS_PLAN_READY
