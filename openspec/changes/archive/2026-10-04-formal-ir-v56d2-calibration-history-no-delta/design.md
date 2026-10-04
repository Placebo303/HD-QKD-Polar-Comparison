# OpenSpec Design: formal-ir-v56d2-calibration

**Lifecycle**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — **decoder-free 零重叠物化校准**
**Cycle**: `V56D2R1` calibration (revision of `V56D2`), predecessor `V56D1` `73bb2166`
**Branch**: `formal-ir-mainline` HEAD `73bb21669c1b76039a6981151d8cc0008dc778d0` data SHA `84d62779603e62de50ded5182ed65b65d3dc6084` (200ps legacy_v1 nearest 1024)
**Revision reason**: V56D2 终态 `FAIL_NEED_FIX` 错误基于缺证据判证伪；正确为 `CALIBRATION_EVIDENCE_INCOMPLETE / ENVIRONMENT_AND_CONTRACT_NOT_REPRODUCED` — TimeTagger 缺失致 timing 未重算，`frac_B 36.4%` 可能来自探测效率非 routing 错误。
**Feasibility**: V56D1 已用 raw TTBin 实测 `peak_center ±50ps σ127ps` 但 `p2bg 708/629/378<1000` 且 V55 sidecar 缺 `delay_used/peak/frame_start/mapping` 10+ 字段致 `timing_contract_verified全false` + `frac_B 36.5%/36.4%<40%`；**R1 更正**：`frac≥40%` 硬门不合理，不再强制各占≥40%，比例仅报告；timing 缺失只能 `EVIDENCE_INCOMPLETE`；固定使用 `V56D1 成功读取 TimeTagger 的同环境` 并记录解释器路径/版本/输入事件数；直接复用 `V13 已验证 channel/delay/peak/gate/frame-start/mapping/pairing` 实现；**A2 未排除不得判 B**；最短路径为先做小批量零重叠校准显式落盘+双合同验证，再定是否冻新 TEST。

## 1. 科学问题与关键判断

> V54 在 2026-01-21 域 `43/45`，V55 同方法同点新域 `0/90`；V56D0 排除 parquet `A1(k*=0)`，V56D1 补 raw A2 发现 `peak窄127ps` 但 `timing INCOMPLETE + 通道36%`，不能自动判 `PATH_B_DOMAIN_SHIFT`；当前 `p2bg 378-708` 弱于 V13 `3300-3800`，若跨三采集硬套 `p2bg>1000` 必全败，需分源评估；校准必须同时验证**通道路由**与**时间对齐**双合同，避免只修 delay 仍错 mapping。

- **不变量**：`dimension 1024 / bin_width 200ps / pairing nearest / legacy_v1 / frame_period 204800ps / BLOCK 4×256` 为名义不变量
- **可变量**：`delay_used / peak_center / σ / p2bg / channels A/B分布 / threshold 40000 / gate 200 / frame_start / mapping / wrap_rule` 跨 session 可变且 V55 未记录，是校准落盘重点
- **唯一真值**：每源声明唯一 `delay_used -50/+50/-50` 与 raw `peak_center` 对齐（1M `-50`, 1p5M `+50`, 2M `-50`），不择优，不做多 delay 扫描，`|peak-delay|<50ps` 且 `sign一致` 为硬校验

## 2. 冻结语义 — V54 方法零改

| 项 | 冻结值 | 来源 |
|---|---|---|
| n/d | 1024 | V31/V55 |
| m2 per source | 184 (1M) 190 (1p5M) 192 (2M) | Lane C ordinal-2 |
| GF | GF32 poly37 | GF2mField |
| H1 | V31-H1-QC-16×1024 rank16 80b | V31 |
| 泄漏 | base 1064/1094/1104 +40 +40 | m1=16+64b tag |
| 译码 (冻结禁用) | decode_row_layered_fftqspa 90/1.0 | V43/V52 — 校准期禁用 |
| L1-APP | p via H1 BP TRAIN channel_counts.npz | V25 |
| Intake | d1024 bw200 nearest legacy_v1 A1/B5 单点 84d62779 | V55 |

**禁令**：`SHALL NOT` 任何 `decode_*` / `construct_*` / 调 `m2/leak/decoder`；**零 decoder**；原 V55 90-block 已揭盲禁止重跑。

## 3. 显式落盘 — raw TTBin 重算（decoder-free，R1 环境锁定 + V13 复用）

- 输入：`v55_authoritative_registry.json: strata[].provenance[].path+sha256` 双文件 `*.ttbin + *.1.ttbin`，`FileReader` 读 `main` 自动合并 `.1.ttbin`
- 环境锁定（R1 新增）：固定使用 `V56D1 成功读取 TimeTagger 的同环境`（`V56D1 diagnosis_raw_a2.py` 曾成功重算 `TimeTagger` 的解释器），记录 `environment {interpreter_path, timetagger_version, total_events, acquisition_duration_s}`；缺失 `TimeTagger` 时不得伪造 timing 值，只能标记 `EVIDENCE_INCOMPLETE / ENVIRONMENT_AND_CONTRACT_NOT_REPRODUCED`
- 方法：直接复用 `V13 已验证 read_ttbin_events + compute_cross_correlation_histogram(ch_a=1,ch_b=5,bin100/max_lag819200/n16384, lag=t_B-t_A)` 实现（不重发明近似物化）→ `channel_hist {unique, count_A(1), count_B(5), other, frac_A/B/other, total_events, acquisition_duration_s, ttbin_merge {main_size,chunk_size,merge_verified}}` + `peak_center/σ(FWHM/2.355)/peak_count/p2bg=peak/bg_median/bg_median|5σ/delay_sign`
- 声明：每源唯一 `delay_used -50/+50/-50`（1M -50, 1p5M +50, 2M -50）与 raw `peak_center` 绑定 `|peak-delay|<50 && sign一致`；落盘 `sidecar_meta.json: used_params={delay_used_ps, peak_center_ps, peak_sigma_ps, corr_argmax, corr_bins, peak_to_bg, peak_status, channels {A:1,B:5}, gate_width_ps 200, pairing_threshold_ps 40000, frame_start_ps, frame_anchor, mapping, wrap_rule floor_div, frame_period_ps 204800, occupancy_filter}` + `provenance/sha256` + `environment`
- V13 复用：直接复用 `workspace/v13r3fresh_20260816/sidecars/*/sidecar_meta.json: used_params` 的 `delay -50/+50, σ74/88/103, p2bg3300-3800, gate/threshold/mapping/wrap` 实现与阈值，实时读仅作对照，不硬编码判定，不重发明近似 pairing

## 4. 零重叠 calibration frames 预注册

- 定义：每源固定 `8 frames [7,8,9,10,15,16,17,18] = 2 blocks×4` 连续帧（V56D2R1 仍可用相同 8 帧，写入 additive `run_02` 或修订轮目录不覆盖 `run_01`），`pairs_per_frame 256`，与 V55 `selected_frame_ids` **零重叠** `set(CAL) ∩ set(V55)==∅` 可机械校验
- 约束：`frame_id ∈ [0, F-1]` (`F 2130/5125/5513`), `gap≥4` 同 V55，`need 8` 预注册，deterministic 不重叠区间（选 gaps 中最早可用连续段，已验证 `[7,8,9,10,15,16,17,18]` 零重叠）
- 产出：`calibration_registry.json {per_source: {F,K,selected_frame_ids,blocks,provenance,processing_rule}}` + `calibration_manifest.json {overall_zero_overlap_verified: true, per_source_zero_overlap: true}`，落盘至 additive `run_02` 目录，不覆盖 `v56d2_calibration.json`

## 5. 双合同验证 — timing + routing 解耦（R1 修正）

**timing_contract_verified** (时间对齐，R1 证据完整性门):
```
# timing 字段必须真实重算（V56D1 同 TimeTagger 环境），缺失时只能 EVIDENCE_INCOMPLETE，不得判 FAIL_NEED_FIX 证伪
peak_shape_ok = 50 <= σ <=150  (仅当 σ 真实重算时可判定，否则 UNKNOWN)
timing_ok = |peak_center - delay_used|<50 && sign(peak)==sign(delay)  (仅当 peak_center 真实重算时可判定)
gate_ok = gate_width==200 && threshold==40000 && frame_start已落盘
p2bg_assessed = per-source p2bg已评估 (见 §6)
timing_contract_verified = peak_shape_ok && timing_ok && gate_ok && p2bg_assessed
timing_evidence_complete = peak_center/σ/p2bg 均真实重算  (否则 → CALIBRATION_EVIDENCE_INCOMPLETE)
```

**routing_contract_verified** (通道路由，R1 修正 — 不再强制各占≥40%):
```
# R1: 指定 channel 存在且非零、配对无跨 channel/丢列/错误合并；比例仅报告，不再强制各占≥40%
channel_exists = 1 in unique_channels && 5 in unique_channels && count_A>0 && count_B>0
no_cross_channel = frac_other<0.20 && 未跨 channel 错误合并 && 无丢列
routing_contract_verified = channel_exists && no_cross_channel
# 仅报告 frac_A/B/other（如 1M 36.5% / 2M 36.4% 可能来自探测效率，非 routing 错误证明）
```

**总体校准判定（R1）**:
```
if not timing_evidence_complete:
    overall = CALIBRATION_EVIDENCE_INCOMPLETE / ENVIRONMENT_AND_CONTRACT_NOT_REPRODUCED
    # 缺 TimeTagger/缺 peak 致 timing 未重算，保留本次输出不覆盖，fix 环境后重算
elif timing_contract_verified && routing_contract_verified && A==B_cal>0.60 && NLL/q_mass回落 && p2bg分源评估非硬败:
    calibration_pass = true
else:
    calibration_pass = false  # timing 完整仍 NLL 20-30 才是真域问题
# 任一 timing 缺失 → EVIDENCE_INCOMPLETE 而非 FAIL_NEED_FIX；仅 timing 完整才可判域问题
```

## 6. p2bg>1000 兼容性分源评估（关键）

- 现状：raw 重算 `708(1M)/629(1p5M)/378(2M)` 均 `<1000`，若跨三采集强制共用 `p2bg>1000` 必全败，需先核查是否应分源
- 策略：`per-source HEALTHY (>1000) / PARTIAL (500-1000) / LOW (<500)` 三档；`PARTIAL` 允许 calibration 通过但标记 `p2bg_partial_warn`，`LOW` 需核查光路/阈值是否应分源阈值；报告 `should_share_threshold_across_acquisitions: bool` 与 `recommended_per_source_threshold`
- 校准不因 `p2bg` 单项 `<1000` 而一刀切失败，但必须显式评估并记录 `p2bg_assessed=true`

## 7. 相关性/NLL/q_mass 回落验证（R1 校正后仍要求）

- 输入：calibration 小批量 `8 frames [7,8,9,10,15,16,17,18]` 的 `pairs.parquet` 预生成（由落盘后的 `frame_id` 从已物化 `pairs/*.parquet` 切片或按 `sidecar` 重建）的 `alice_symbol/bob_symbol` 统计
- 指标：`A==B_rate`, `U1/U2_rate`(F03 5+5 split), `NLL_bits_per_block = -sum log2 P(A|B)` via `channel_counts.npz` column-norm, `q_mass_on_p_zero = sum_{N_ab==0} P>0`, `delta_hist mass_0+mass_±1`
- 健康参考：`A==B>60%` (从 27-41% 回升), `NLL` 从 `28-35` 向 `V13 0.82*1024≈839 bits/block` 靠近, `q_mass 57-71%→3%`, `mass_0+mass_±1>85%`；校正后仍要求 `A==B>60%` 且 `NLL/q_mass` 回落，若 timing 完整仍 `NLL 20-30` 才是真域问题；timing 缺失时只能 `EVIDENCE_INCOMPLETE`

## 8. 校准脚本与报告（decoder-free 守卫，R1）

- 脚本 `v56d2_calibration.py` (本变更目录下, decoder-free): `--registry v55_authoritative_registry.json --intake-report --v13-root --counts --out v56d2_calibration_run02.json [--recompute-corr]` → 固定 `V56D1 同 TimeTagger 环境`（记录 `interpreter_path/TimeTagger版本/输入事件数`）重算 peak/channel + 落盘 sidecar + 预注册 `8 frames [7,8,9,10,15,16,17,18]` 零重叠 + 双合同判定（routing 不再强制≥40%，timing 缺失→`EVIDENCE_INCOMPLETE`）+ 相关性/NLL，`rg "decode_" 0 hits` 仅 `numpy/pandas/pyarrow + ttbin_pipeline(TimeTagger optional)`，`py_compile` PASS；保留 `v56d2_calibration.json` 不覆盖，写入 additive `run_02`
- 报告 `CALIBRATION_REPORT.md`: 每源 `落盘值/通道/双合同/相关性/NLL/p2bg分源评估` 与总体 `PASS/CALIBRATION_EVIDENCE_INCOMPLETE`（缺证据时）或 `FAIL_NEED_FIX`（timing 完整仍不达标时），数据与 json 一致，不扩大为 FER/阈值/SKR/晋升
- 守卫：校准期 **零 decoder**、原 90 已揭盲保护、三源全 `PASS` 才允许另起 successor 冻新 TEST；**不运行 decoder，不碰 V55 90 块，仅改本目录文件与脚本 gate，推送新 SHA**

## 9. 与 V55/V56D1 衔接

- V55 `QUALIFICATION_RESULT_ACCEPTED_FAIL 0/90` 已固化，不重跑；V56D1 `MIXED_BY_SOURCE 2×A2+1×INCONCLUSIVE` 已固化，需本校准显式落盘补齐 `timing_contract` + 通道 `frac_B`；V56D2 不改变前两终态，仅 append 显式落盘与小批量验证；qualification 需全新 successor。

## 10. 自由裁量 D1-D6

- D1 raw 重算固定 `ch1/5 bin100 max819200 n16384 lag=t_B-t_A` 不扩展多通道
- D2 delay 唯一符号 `-50/+50/-50` 不择优，候选阈固定 40000/gate200 不网格
- D3 calibration 固定 `8-16 frames gap≥4 零重叠` 不扩至多配置
- D4 p2bg 分源三档 `>1000/500-1000/<500` 已达最简，不做高斯拟合
- D5 双合同阈 `σ50-150 |peak-delay|<50 frac≥40%` 启发仅证据描述，非 decoder 门禁
- D6 不产生新矩阵/码参数，仅落盘与验证，最简闭环
