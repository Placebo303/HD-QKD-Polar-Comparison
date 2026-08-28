# OpenSpec Design: formal-ir-v56d2-calibration

**Lifecycle**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — **decoder-free 零重叠物化校准**
**Cycle**: `V56D2` calibration, predecessor `V56D1` `73bb2166`
**Branch**: `formal-ir-mainline` HEAD `73bb21669c1b76039a6981151d8cc0008dc778d0` data SHA `84d62779603e62de50ded5182ed65b65d3dc6084` (200ps legacy_v1 nearest 1024)
**Feasibility**: V56D1 已用 raw TTBin 实测 `peak_center ±50ps σ127ps` 但 `p2bg 708/629/378<1000` 且 V55 sidecar 缺 `delay_used/peak/frame_start/mapping` 10+ 字段致 `timing_contract_verified全false` + `frac_B 36.5%/36.4%<40%` 通道告警，`A==B 27-41%` NLL `28-35` q_mass `57-71%` 远离 V13 `0.82/3%`；**A2 未排除不得判 B**；最短路径为先做小批量零重叠校准显式落盘+双合同验证，再定是否冻新 TEST。

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

## 3. 显式落盘 — raw TTBin 重算（decoder-free）

- 输入：`v55_authoritative_registry.json: strata[].provenance[].path+sha256` 双文件 `*.ttbin + *.1.ttbin`，`FileReader` 读 `main` 自动合并 `.1.ttbin`
- 方法：`read_ttbin_events(main)` → `channel_hist {unique, count_A(1), count_B(5), other, frac_A/B/other, total_events, acquisition_duration_s, ttbin_merge {main_size,chunk_size,merge_verified}}` + `compute_cross_correlation_histogram(ch_a=1,ch_b=5,bin100/max_lag819200/n16384, lag=t_B-t_A) → peak_center/σ(FWHM/2.355)/peak_count/p2bg=peak/bg_median/bg_median|5σ/delay_sign`
- 声明：每源唯一 `delay_used -50/+50/-50`（1M -50, 1p5M +50, 2M -50）与 raw `peak_center` 绑定 `|peak-delay|<50 && sign一致`；落盘 `sidecar_meta.json: used_params={delay_used_ps, peak_center_ps, peak_sigma_ps, corr_argmax, corr_bins, peak_to_bg, peak_status, channels {A:1,B:5}, gate_width_ps 200, pairing_threshold_ps 40000, frame_start_ps, frame_anchor, mapping, wrap_rule floor_div, frame_period_ps 204800, occupancy_filter}` + `provenance/sha256`
- V13 对照：实时读 `workspace/v13r3fresh_20260816/sidecars/*/sidecar_meta.json: used_params` 实际 `delay -50/+50, σ74/88/103, p2bg3300-3800` 仅作参考，不硬编码判定

## 4. 零重叠 calibration frames 预注册

- 定义：每源 `8-16 frames` = `2-4 blocks ×4` 连续帧，`pairs_per_frame 256`，与 V55 `selected_frame_ids` **零重叠** `set(CAL) ∩ set(V55)==∅` 可机械校验
- 约束：`frame_id ∈ [0, F-1]` (`F 2130/5125/5513`), `gap≥4` 同 V55，`need 8-16` 预注册，deterministic 不重叠区间（选 gaps 中最早可用连续段）
- 产出：`calibration_registry.json {per_source: {F,K,selected_frame_ids,blocks,provenance,processing_rule}}` + `calibration_manifest.json {overall_zero_overlap_verified: true, per_source_zero_overlap: true}`

## 5. 双合同验证 — timing + routing 解耦

**timing_contract_verified** (时间对齐):
```
peak_shape_ok = 50 <= σ <=150
timing_ok = |peak_center - delay_used|<50 && sign(peak)==sign(delay)
gate_ok = gate_width==200 && threshold==40000 && frame_start已落盘
p2bg_assessed = per-source p2bg已评估 (见 §6)
timing_contract_verified = peak_shape_ok && timing_ok && gate_ok && p2bg_assessed
```

**routing_contract_verified** (通道路由):
```
channel_ok = frac_A>=0.40 && frac_B>=0.40 && frac_other<0.20
unique_ok = set(unique_channels) ⊇ {1,5}
routing_contract_verified = channel_ok && unique_ok
# V56D1实测 1M frac_B36.5% 2M36.4% 为习题，需校准后≥40%才过
```

**总体校准通过**:
```
calibration_pass = timing_contract_verified && routing_contract_verified
                 && A==B_cal >0.60 && NLL_cal回落 && q_mass回落 && p2bg分源评估非硬败
# 任一合同失败 -> FAIL_NEED_FIX 停留 DIAGNOSIS_PLAN_READY，不进 qualification
```

## 6. p2bg>1000 兼容性分源评估（关键）

- 现状：raw 重算 `708(1M)/629(1p5M)/378(2M)` 均 `<1000`，若跨三采集强制共用 `p2bg>1000` 必全败，需先核查是否应分源
- 策略：`per-source HEALTHY (>1000) / PARTIAL (500-1000) / LOW (<500)` 三档；`PARTIAL` 允许 calibration 通过但标记 `p2bg_partial_warn`，`LOW` 需核查光路/阈值是否应分源阈值；报告 `should_share_threshold_across_acquisitions: bool` 与 `recommended_per_source_threshold`
- 校准不因 `p2bg` 单项 `<1000` 而一刀切失败，但必须显式评估并记录 `p2bg_assessed=true`

## 7. 相关性/NLL/q_mass 回落验证

- 输入：calibration 小批量 `8-16 frames` 的 `pairs.parquet` 预生成（由落盘后的 `frame_id` 从已物化 `pairs/*.parquet` 切片或按 `sidecar` 重建）的 `alice_symbol/bob_symbol` 统计
- 指标：`A==B_rate`, `U1/U2_rate`(F03 5+5 split), `NLL_bits_per_block = -sum log2 P(A|B)` via `channel_counts.npz` column-norm, `q_mass_on_p_zero = sum_{N_ab==0} P>0`, `delta_hist mass_0+mass_±1`
- 健康参考：`A==B>60%` (从 27-41% 回升), `NLL` 从 `28-35` 向 `V13 0.82*1024≈839 bits/block` 靠近, `q_mass 57-71%→3%`, `mass_0+mass_±1>85%`；未达即 `FAIL_NEED_FIX` 不进 qualification

## 8. 校准脚本与报告（decoder-free 守卫）

- 脚本 `v56d2_calibration.py` (本变更目录下, decoder-free): `--registry v55_authoritative_registry.json --intake-report --v13-root --counts --out v56d2_calibration.json [--recompute-corr]` → 重算 peak/channel + 落盘 sidecar + 预注册零重叠帧 + 双合同判定 + 相关性/NLL，`rg "decode_" 0 hits` 仅 `numpy/pandas/pyarrow + ttbin_pipeline(TimeTagger optional)`，`py_compile` PASS
- 报告 `CALIBRATION_REPORT.md`: 每源 `落盘值/通道/双合同/相关性/NLL/p2bg分源评估` 与总体 `PASS/FAIL_NEED_FIX`，数据与 json 一致，不扩大为 FER/阈值/SKR/晋升
- 守卫：校准期 **零 decoder**、原 90 已揭盲保护、三源全 `PASS` 才允许另起 successor 冻新 TEST

## 9. 与 V55/V56D1 衔接

- V55 `QUALIFICATION_RESULT_ACCEPTED_FAIL 0/90` 已固化，不重跑；V56D1 `MIXED_BY_SOURCE 2×A2+1×INCONCLUSIVE` 已固化，需本校准显式落盘补齐 `timing_contract` + 通道 `frac_B`；V56D2 不改变前两终态，仅 append 显式落盘与小批量验证；qualification 需全新 successor。

## 10. 自由裁量 D1-D6

- D1 raw 重算固定 `ch1/5 bin100 max819200 n16384 lag=t_B-t_A` 不扩展多通道
- D2 delay 唯一符号 `-50/+50/-50` 不择优，候选阈固定 40000/gate200 不网格
- D3 calibration 固定 `8-16 frames gap≥4 零重叠` 不扩至多配置
- D4 p2bg 分源三档 `>1000/500-1000/<500` 已达最简，不做高斯拟合
- D5 双合同阈 `σ50-150 |peak-delay|<50 frac≥40%` 启发仅证据描述，非 decoder 门禁
- D6 不产生新矩阵/码参数，仅落盘与验证，最简闭环
