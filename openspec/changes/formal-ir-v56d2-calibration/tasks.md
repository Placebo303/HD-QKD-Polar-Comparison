# OpenSpec Tasks: formal-ir-v56d2-calibration — V56D2R1 minimal revision

**Lifecycle**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — **decoder-free 零重叠物化校准，不运行 L1/L2 decoder**
**HEAD**: `73bb21669c1b76039a6981151d8cc0008dc778d0` (branch `formal-ir-mainline`, V56D1 固化后) + data SHA `84d62779603e62de50ded5182ed65b65d3dc6084`
**Predecessor**: `formal-ir-v56d1-raw-a2-diagnosis` (MIXED_BY_SOURCE: 1M/2M PATH_A2 frac_B36% / 1p5M INCONCLUSIVE, peak 127ps p2bg708/629/378<1000 raw, timing INCOMPLETE)
**Revision V56D2R1**: 终态 `FAIL_NEED_FIX` → `CALIBRATION_EVIDENCE_INCOMPLETE / ENVIRONMENT_AND_CONTRACT_NOT_REPRODUCED`；环境锁定 `V56D1 同 TimeTagger` + 记录解释器/版本/事件数；复用 V13 实现；routing 去除≥40% 硬门（比例仅报告）；timing 缺失→`EVIDENCE_INCOMPLETE`；固定 8 帧 `[7,8,9,10,15,16,17,18]` additive `run_02` 不覆盖；仅改本目录文件与脚本 gate，不运行 decoder，不碰 V55 90 块

## Phase A — Raw TTBin 显式重算与落盘（decoder-free, 唯一 delay 符号 -50/+50 不择优，R1 环境锁定 + V13 复用）

- [ ] **A1** 固定使用 `V56D1 成功读取 TimeTagger 的同环境`（记录 `interpreter_path、TimeTagger 版本、输入事件数`），读 `v55_authoritative_registry.json: strata[].provenance[].path+sha256` 三源双文件 `*.ttbin+*.1.ttbin`，直接复用 `V13 已验证 read_ttbin_events + compute_cross_correlation_histogram(ch_a=1,ch_b=5,bin100/max_lag819200/n16384, lag=t_B-t_A)` 实现统计 `channel_hist {unique, count_A1/count_B5/other, frac_A/B/other, total_events, acquisition_duration_s, ttbin_merge {main_size,chunk_size,merge_verified}}` 并得 `peak_center/σ(FWHM/2.355)/peak_count/p2bg/delay_sign`（不重发明近似物化）；`timing` 字段必须真实重算，缺失时只能 `EVIDENCE_INCOMPLETE / ENVIRONMENT_AND_CONTRACT_NOT_REPRODUCED`，不得判 `FAIL_NEED_FIX`
- [ ] **A2** 声明唯一 `delay_used -50/+50/-50` (1M `-50`, 1p5M `+50`, 2M `-50` 与 raw `peak ±50` 对齐) 不择优，落盘每源 `sidecar_meta.json: used_params={delay_used_ps, peak_center_ps, peak_sigma_ps, corr_argmax, corr_bins, peak_to_bg, peak_status, channels {A:1,B:5}, gate_width_ps 200, pairing_threshold_ps 40000, frame_start_ps, frame_anchor, mapping, wrap_rule floor_div, frame_period_ps 204800, occupancy_filter}` + `provenance/sha256` + `environment{interpreter, timetagger_version, total_events}`，机械校验 `|peak - delay|<50ps` 且 `sign一致`
- [ ] **A3** 直接复用 `workspace/v13r3fresh_20260816/sidecars/*/sidecar_meta.json` 的 `V13 已验证 channel/delay/peak/gate/frame-start/mapping/pairing` 实现（`delay -50/+50 σ74/88/103 p2bg3300-3800 gate200 threshold40000`）不重发明，仅作对照，不硬编码判定

## Phase B — 8 帧零重叠 calibration frames 预注册（与 V55 90块零重叠，R1 固定）

- [ ] **B1** 解析 `v55_authoritative_registry.json: strata[].F/K/selected_frame_ids` (1M F2130 / 1p5M 5125 / 2M 5513, 各 30 blocks, gap≥4)，为每源固定预注册 `8 frames [7,8,9,10,15,16,17,18] = 2 blocks×4` 连续帧（仍可用相同 8 帧），`pairs_per_frame 256`，`frame_id ∈ [0,F-1]`，写入 additive `run_02` 或修订轮目录不覆盖 `v56d2_calibration.json`
- [ ] **B2** 机械校验 `set(calibration_frame_ids) ∩ set(V55_frame_ids) == ∅` 且 `gap≥4`，输出 `calibration_registry.json + calibration_manifest.json {overall_zero_overlap_verified, per_source_zero_overlap}`
- [ ] **B3** 失败则 `CALIBRATION_EVIDENCE_INCOMPLETE` 或 `FAIL_NEED_FIX` 停留，不进 qualification；保留 `run_01` 不覆盖

## Phase C — 双合同解耦验证（timing + routing, decoder-free, R1 修正）

- [ ] **C1** Timing 合同时刻（R1）：`peak_shape_ok (50≤σ≤150)` + `timing_ok (|peak-delay|<50 && sign一致)` + `gate_ok (gate200/threshold40000/frame_start已落盘)` + `p2bg_assessed` → `timing_contract_verified`；**timing 字段必须真实重算（V56D1 同 TimeTagger 环境），缺失时只能 `CALIBRATION_EVIDENCE_INCOMPLETE / ENVIRONMENT_AND_CONTRACT_NOT_REPRODUCED`，不得判 `FAIL_NEED_FIX` 证伪**
- [ ] **C2** 通道路由（R1）：`指定 channel 存在且非零（count_A>0 && count_B>0 && unique⊇{1,5}）且配对无跨 channel/丢列/错误合并（other<20%）` → `routing_contract_verified`；**不再强制各占≥40%，`1M/2M 36.4%` 比例仅报告（可能来自探测效率非 routing 错误证明）**
- [ ] **C3** p2bg>1000 兼容性分源评估：`HEALTHY>1000 / PARTIAL 500-1000 / LOW<500` 三档，`708/629` 为 PARTIAL、`378` 为 LOW；评估 `should_share_threshold_across_acquisitions` 是否跨三采集强制共用，报告 `recommended_per_source_threshold`；`PARTIAL` 允许通过但 `p2bg_partial_warn`，`LOW` 需核查；不得直接硬套共阈一刀切
- [ ] **C4** `timing` 缺失→`CALIBRATION_EVIDENCE_INCOMPLETE`；`timing` 完整且双合同均 `true` 且 `A==B>60%` 且 `NLL/q_mass` 回落才校准通过，否则 `FAIL_NEED_FIX`；**校正后仍要求 `A==B>60%` 且 `NLL/q_mass` 回落，若 timing 完整仍 `NLL 20-30` 才是真域问题**

## Phase D — 基础相关性与 NLL 回落验证（decoder-free, V25 prior, R1）

- [ ] **D1** 在 calibration 小批量 `8 frames [7,8,9,10,15,16,17,18]` 上统计 `A==B_rate` (从 V55 27-41% 向 >60% 回升)、`U1/U2` (F03 5+5)、`delta mass_0+mass_±1`
- [ ] **D2** V25 `channel_counts.npz` column-norm `P(A|B)` 算 `NLL bits/block` 从 `28-35` 向 `V13 0.82*1024` 靠近，`q_mass_on_p_zero` 从 `57-71%` 向 `3%` 回落；**timing 缺失时只能 `EVIDENCE_INCOMPLETE`**；`timing` 完整仍 `NLL 20-30` 才是真域问题，未达即 `FAIL_NEED_FIX` 不进 qualification
- [ ] **D3** 三源全 `calibration_pass` 标志 `overall PASS`，`timing` 缺失时 `CALIBRATION_EVIDENCE_INCOMPLETE / ENVIRONMENT_AND_CONTRACT_NOT_REPRODUCED`，否则 `MIXED/FAIL` 按源分别修 sidecar/重审阈值，分源阈值另行记录；保留 `run_01` 不覆盖

## Phase E — 脚本与报告交付（DIAGNOSIS_PLAN_READY, R1）

- [ ] **E1** 修订 `v56d2_calibration.py` (decoder-free, 本变更目录下): `python v56d2_calibration.py [--registry ...] [--intake-report ...] [--v13-root ...] [--counts ...] [--out v56d2_calibration_run02.json] [--recompute-corr]` → 固定 `V56D1 同 TimeTagger 环境`（记录解释器/版本/事件数）重算 peak/channel + 落盘 sidecar + 零重叠 `8 frames [7,8,9,10,15,16,17,18]` + 双合同（routing 去≥40% 硬门，timing 缺失→`EVIDENCE_INCOMPLETE`）+ 相关性/NLL/p2bg分源评估；直接复用 `V13 channel/delay/peak/gate/frame-start/mapping/pairing` 实现；守卫 `rg "decode_" 0 hits` 仅 `numpy/pandas/pyarrow + ttbin_pipeline`，`py_compile` PASS；保留 `v56d2_calibration.json` 不覆盖
- [ ] **E2** 修订 `CALIBRATION_REPORT.md` (R1): 每源 `落盘值/通道 frac_A/B/other（比例仅报告）/ timing+routing 双门 / A==B/NLL/q_mass / p2bg三档分源评估` + 总体 `PASS / CALIBRATION_EVIDENCE_INCOMPLETE / FAIL_NEED_FIX` 与 `should_share_p2bg_threshold` 结论，终态更正为 `EVIDENCE_INCOMPLETE`（缺 TimeTagger 时），数据与 `v56d2_calibration_run02.json` 一致，不扩大为 FER/阈值/SKR/晋升，显式原 90 已揭盲不可复用
- [ ] **E3** 自检：`py_compile` PASS, `rg "decode_" 0 hits`, `set(CAL)∩set(V55)==∅` 已验, `|peak-delay|<50` 已验（缺失→`EVIDENCE_INCOMPLETE`）, `routing 指定 channel 存在且非零且无跨 channel/丢列（比例仅报告）` 已验, `CALIBRATION_REPORT` 与 json 一致, `environment{interpreter, timetagger_version, total_events}` 已记录
- [ ] **E4** 推送新 SHA 并停留 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`，未创建任何 `.../v56d2_*/run_01` decoder 执行，不碰 V55 90 块，不运行 decoder，仅改本目录文件与脚本 gate；三源全 PASS 后另起 successor 冻全新 TEST blocks 再 qualification

## 本校准显式禁止（R1 仍适用）

decoder 调用 (`decode_*` / `construct_*` / `sample_uniform_gf32` 等)；在原 V55 90-block 上重跑任何 corrected pipeline（含 peak-corrected 重译）；调 `H1/Lane C/Δ8/decoder 90/1.0/m2/leak/prior` 任一冻结参数；宣称 LDPC 证伪或 FER/阈值/SKR/晋升；创建正式 `.../v56d2_*/run_01` decoder 执行；跨三采集硬套 `p2bg>1000` 一刀切而不做分源评估；择优多 delay 符号；**重发明 V13 已验证 channel/delay/peak/gate/frame-start/mapping/pairing 近似物化**；**强制各占≥40% 硬门**；**伪造 timing 值**（缺失时必须 `EVIDENCE_INCOMPLETE`）；覆盖 `v56d2_calibration.json` 或 V55 90 块。

## 验收（R1）

- proposal/design/tasks/specs 一致 HEAD 73bb2166 84d62779 lifecycle DIAGNOSIS_PLAN_READY DECODE_FORBIDDEN 终态 `CALIBRATION_EVIDENCE_INCOMPLETE / ENVIRONMENT_AND_CONTRACT_NOT_REPRODUCED`（缺证据时）明确
- 每源 sidecar 已显式落盘 `delay -50/+50/-50` + `peak ±50 σ127 p2bg 708/629/378`（真实重算或 `EVIDENCE_INCOMPLETE`）+ `|peak-delay|<50` 可机械校验（缺失→`EVIDENCE_INCOMPLETE`），唯一符号不择优；环境 `interpreter/TimeTagger版本/事件数` 已记录
- 每源 8 frames `[7,8,9,10,15,16,17,18]` 零重叠已预注册且 `set∩==∅` 已验，additive `run_02` 不覆盖
- 双合同 `timing(缺失→EVIDENCE_INCOMPLETE)+routing(指定 channel 存在且非零且无跨 channel/丢列，比例仅报告)` 逐源判定 + `p2bg>1000` 分源三档评估已报告；直接复用 V13 实现，无近似物化
- 校正后仍要求 `A==B>60%` + `NLL 28-35→0.82` + `q_mass 57-71%→3%` 回落；timing 完整仍 `NLL 20-30` 才是真域问题，否则 `EVIDENCE_INCOMPLETE`
- 脚本 `rg 0 hits` `py_compile` PASS 报告与 `run02` json 一致 未建 `run_01` 已推新 SHA DIAGNOSIS_PLAN_READY 仅改本目录
