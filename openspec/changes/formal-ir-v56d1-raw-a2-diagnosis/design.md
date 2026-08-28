# OpenSpec Design: formal-ir-v56d1-raw-a2-diagnosis

**Lifecycle**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — **decoder-free raw TTBin A2 诊断，不运行 L1/L2 decoder。**
**Cycle**: `V56D1` (raw-A2), predecessor `V56D0` diag `4914b56d8d353e7445a621fb142f340c37245f12`
**Predecessor**: `formal-ir-v56-input-domain-diagnosis` (V56D0, `cf8b098...` →固化 `4914b56d...`, branch `formal-ir-mainline`), **HEAD** `4914b56d8d353e7445a621fb142f340c37245f12` (2026-08-29, V56 固化后), data SHA `84d62779603e62de50ded5182ed65b65d3dc6084` (200ps legacy_v1 nearest 1024, 单点 `84d62779`)
**Feasibility**: V54 二阶段在 `2026-01-21` 域 `43/45`，V55 同方法 `0/90` 且 `A==B 76%→27-41%`，V56D0 仅 parquet `A1` 排除 (`k*=0 Δrate=0 NLL*=NLL0, single_peak false`) 但因 V55 sidecar 缺 `delay/peak/corr/frame_start/mapping` 等 10+ 字段而 `INCONCLUSIVE_METADATA_INCOMPLETE`，**A2 = raw TTBin delay/peak/pairing contract 需 actual raw 证据**；本诊断唯一后继补齐该证据。
**Key judgement**: **缺 metadata 本身不自动判 A2**；必须从原始 TTBin 重读 `channel IDs` 与 `timestamp cross-correlation` 实测 `peak_center/width/p2bg/delay_sign` 后，才可判 `PATH_A2_RAW_CONTRACT_ERROR`（可修复，0重叠 calibration 验证）或 `PATH_B_DOMAIN_SHIFT`（完整正确但相关率仍低，需重估条件熵/泄漏）。

## 1. 科学问题与关键判断

> 在**完全冻结 V54 二阶段完整方法**与**相同处理点**（`d=1024 bw=200ps pairing=nearest rule=legacy_v1`）下，V56D0 已排除 `A1 = b'=(b+k)%1024 parquet symbol shift`（三源 `k*=0` 无回升），但 **`A2 = raw TTBin delay/peak/pairing contract`** 尚未有 actual 证据：`TimeTagger channels A/B、delay、bin origin、peak 位置、nearest threshold、pairing 方向` 在 V55 sidecar 中 `INCOMPLETE`，无法判断是 **显式契约错误**（可修复）还是 **不同物理域**（需重估 `H(U1|B), H(U2|U1,B)`）。

- **对照**：`V13 2026-01-21` 三源 (`type2_1M_20260121_184040 / type2_1p5M_20260121_183806 / type2_2M_20260121_183657`, `200ps legacy_v1`, `nearest`, `delay -50/+50/+50`, `peak_center -50/+50`, `peak_sigma 74/88/103ps`, `peak_to_bg 3808/3366/3699`, `corr_argmax 8191/8192`, `corr_bins 16384`, `gate 200ps`, `threshold 40000ps`, `channels 隐式 A1/B5`) 作为参考域，**不硬编码，仅从 `sidecar_meta.json`+`build_manifest.json` 实时读**；`V55` 三源 (`20260123_1M_600k_0dB F2130 / 20260107_PPLN_1p5M F5125 / 20260123_2M_1p2M_0dB F5513`, 同 `200ps legacy_v1 nearest 1024` 但 sidecar 缺 `delay/peak/mapping` 字段) 作为待诊域，**从原始 TTBin 重算 actual 值**。
- **不变量**：`dimension 1024 / bin_width 200ps / pairing nearest / legacy_v1 / frame_period 204800ps / BLOCK 1024 (4×256)` 为名义不变量；但 `TTBin channels、分bin 原点、peak 中心/宽度、nearest threshold、pairing 方向` 为跨 session 可变且未被 V55 sidecar 完整记录，是首要怀疑点。
- **诊断性质**：纯 **decoder-free**（零 `decode_*` 调用，零码参数），仅读 raw TTBin + `sidecar_meta.json` + `channel_counts.npz` 作背景，做**channel 校验**与**cross-correlation 重算**与**固定契约审计**，最终给出**逐源 A2 判定与总体四态**。

## 2. 冻结语义 — V54 方法与 V55 intake 零改

### 2.1 固定不变项（诊断期间零改）

| 项 | 冻结值 | 来源 |
|---|---|---|
| n / d | 1024 | V31/V55 |
| m2 per source | 184 (1M), 190 (1p5M), 192 (2M) | Lane C `SOURCE_CHECKS` ordinal-2 `38310x` |
| GF | GF32 `poly=37` (`0b100101`) | `GF2mField.create(32)` |
| H1 | `V31-H1-QC-16×1024 rank16 80b` | V31 权威 |
| 泄漏 base/stage1/stage2 | `1064/1094/1104 → 1104/1134/1144 (+40) → 1144/1174/1184 (+80)` | `m1=16` + 64b tag |
| 译码 (冻结但诊断禁用) | `decode_row_layered_fftqspa 90/1.0 poly37 early-stop` | V43/V52 |
| L1-APP | `p_i(u1)=P(U1\|B_i)→BP_i→q_i→P_i(U2)` | TRAIN `channel_counts.npz` |
| Verification | `tag_scope=l2_only compute_tag_64(empty,x2) trunc64, syndrome_ok && tag_ok` | V35 |
| Intake 处理点 | `d1024 bw200 pairing nearest rule legacy_v1 channels A1/B5` 单点 `84d62779` | V55 authoritative |
| Intake 三源 | `20260123_1M_600k_0dB F2130 / 20260107_PPLN_1p5M F5125 / 20260123_2M_1p2M_0dB F5513` 非同分布 2026-01-21 | V55 intake |

- **诊断禁令**：诊断期间 `SHALL NOT` 调用任何 `decode_*` / `construct_*` 构造新矩阵 / 调 `m2/leak/decoder` 参数；**零 decoder、零码参数**；违者诊断无效。
- **已揭盲保护**：V55 authoritative 90-block 的 `frame_ids/ordinal` 已在 `v55_authoritative_registry.json` 冻结且已执行一次 `0/90` 揭盲观测，**禁止**在其上重跑任何 corrected pipeline（含 peak-corrected 重译）。
- **V56D0 衔接**：V56D0 的 `A1-only` offset 扫描已排除 `b'=(b+k)%1024` parquet shift（`k*=0`），本诊断**不再重复 parquet 层**，仅补 raw 层 A2。

### 2.2 Raw 重算与 V13 实时读对比矩阵（只读审计，不硬编码）

> **读取方式**：脚本 `diagnosis_raw_a2.py` (decoder-free) 直接：
> - 对 V55 三源：由 `intake_report.json:provenance[].path` 找到 `*.ttbin + *.1.ttbin` 双文件，调用 `ttbin_pipeline.read_ttbin_events` + `compute_cross_correlation_histogram(ch_a=1,ch_b=5,bin_width_ps=100,max_lag_ps=819200)` 重算 `peak_center/σ/p2bg/delay_sign/count_A/B`；
> - 对 V13 侧：**实时读取** `workspace/v13r3fresh_20260816/sidecars/*/sidecar_meta.json` 的 `used_params`（`delay_used_ps/peak_center_ps/peak_sigma_ps/corr_argmax/corr_bins/peak_to_bg/pairing_threshold_ps/gate_width_ps/pairing_mode/frame_start_ps/frame_anchor/mapping/wrap_rule/occupancy_filter`）与 `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/build_manifest.json` 的 `processing/pairing_mode/processing_rule_version`，**不硬编码 `-50/+50/8191` 等值**，仅当字段存在才记 `PASS` 并记录 `_value` 做比对；缺失记 `INCOMPLETE`。

| 维度 | V13 实际 sidecar 实时读 | V55 raw 实测重算 + sidecar 声明 | 审计结论 |
|---|---|---|---|
| raw `.ttbin` + `.1.ttbin` | `build_manifest.json: sources[].main_ttbin/chunk_ttbin` sha256/size 实时读 | `intake_report.json: provenance[]` 双文件 sha256/size 实时读 + FileReader 统计 `total_events` | `PASS` 如双文件存在且 sha 一致 |
| channels A/B 真实分布 | 读 `used_params.channels` 或隐式 `A1/B5`（若 INCOMPLETE 则记 INCOMPLETE） | **raw 重算**：`channel` 直方图 `count_A(1)/count_B(5)/other` 占比 + 声明 `materialize_params.channels {A:1,B:5}` | `PASS` 如 raw 实测 `1/5` 为主导且声明一致，否则 `MISMATCH` |
| delay_used_ps / peak_center_ps | 读 `used_params.delay_used_ps / peak_center_ps` 实际值（V13 已有 `-50/+50` 但不硬编码） | **raw 重算** `peak_center_ps` vs sidecar `delay_used_ps`（V55 侧缺则 INCOMPLETE） | `PASS` 如 `|peak_center - delay_used|<50ps`，否则 `MISMATCH` |
| peak_sigma_ps / peak_width | 读 `used_params.peak_sigma_ps` 实际 `74/88/103ps` | **raw 重算** `peak_sigma_ps ≈ FWHM/2.355` | `PASS` 如同量级 `50-150ps`，否则 `MISMATCH` 弥散 |
| peak_to_bg | 读 `used_params.peak_to_bg` `3300-3800` | **raw 重算** `p2bg = peak_count / bg_median` | `PASS` 如 `>1000` HEALTHY |
| corr_argmax / corr_bins | 读 `used_params.corr_argmax 8191/8192 / corr_bins 16384` | **raw 重算** `corr_argmax = argmax counts` / `n_bins 16384` | `PASS` 如中心附近，否则 `MISMATCH` |
| delay_sign | 由 `delay_used_ps` 符号 | **raw 重算** `sign(peak_center)` lag=`t_B-t_A` | `PASS` 如符号一致 |
| nearest_threshold_ps | 读 `nearest_threshold_ps 40000` | 读 `materialize_params.used_params.nearest_threshold_ps` 或 `pairing_threshold_ps`（V55 缺则 INCOMPLETE）+ raw 间隔统计 | `PASS` 或 `INCOMPLETE` 按实际 |
| pairing direction/mode | 读 `pairing_mode nearest` + `pairing_mode_requested` | `pairing_mode nearest` + `nearest_unique greedy monotonic 1-1` 方向 | `PASS` 或 `INCOMPLETE` |
| frame_start_ps / bin origin / wrap_rule | 读 `frame_start_ps / frame_anchor / wrap_rule floor_div` / `frame_period_ps 204800` | 读 `frame_start_ps / frame_anchor / wrap_rule`（V55 缺则 INCOMPLETE）+ `ttbin_metrics.symbolization_snapshot.wrap_rule` | `PASS` 或 `INCOMPLETE` |
| gate_width_ps / coinc_window | 读 `gate_width_ps 200` | 读 `gate_width_ps / coinc_window_ps`（V55 缺则 INCOMPLETE） | `PASS` 或 `INCOMPLETE` |
| occupancy_filter | 读 `occupancy_filter` | 读 `occupancy_filter`（V55 缺则 INCOMPLETE） | `PASS` 或 `INCOMPLETE` |

> **设计结论**：缺 `delay_used_ps/peak_center/frame_start/mapping` 等字段时仅记 `INCONCLUSIVE_METADATA_INCOMPLETE`，不自动判 `PATH_A2`；需 actual raw peak 证据才可判 `A2`；若 raw 实测峰正确但 NLL/相关率仍低则判 `PATH_B`。

### 2.3 诊断统计量定义（decoder-free，raw 重算 + parquet 仅作背景）

 - **Channel 真实分布**：`channel_hist = bincount(channel)`, `count_A = hist[1]`, `count_B = hist[5]`, `other_channels = total - count_A - count_B`, `frac_A/B/other`，`unique_channels` 列表；校验声明 `A1/B5`。同时记录 `total_events` 与 `acquisition_duration_s`（`tmax-tmin`），并验证 `.1.ttbin` 自动合并：`main_size` + `chunk_size` 需与 `intake sidecar provenance` 一致且 `total_events>50000` 否则 `merge_verified=false` 标记静默漏读风险，与 intake `diagnostics/n_pairs` 交叉核对。
 - **timing_contract_verified**：单独布尔，仅当恢复出 V55 实际使用的 `delay_used_ps`（以及 `pairing_threshold_ps ==40000`）且与 raw `peak_center` 符号一致、数值 `|peak-delay|<50ps` 时为 true；只有该值为 true 且 `peak_shape_healthy` 时才允许进 `PATH_B`；健康峰但未验证→ `INCONCLUSIVE_A2_NOT_EXCLUDED`；明确不匹配→ `PATH_A2`。
- **Cross-correlation histogram**：`lag = t_B - t_A`, `bin_width 100ps`, `max_lag 819200ps`, `n_bins 16384`, `counts[16384]` 由 `compute_cross_correlation_histogram` Chunked 统计；`peak_idx = argmax counts`, `peak_center = lag_center[peak_idx]`, `peak_count = counts[peak_idx]`。
- **Peak width**：FWHM 估计：从 `peak_idx` 向两侧找 `counts < peak_count/2` 的最近 bin，`FWHM = (right-left)*100ps`，`σ ≈ FWHM/2.355`；若峰过窄（单 bin 尖）则 `σ` 取半高宽近似，报告 `peak_width_ps (σ)` 与 `FWHM`。
- **Peak-to-background**：`bg = median(counts where |lag - peak_center| > 5σ)`（或 `>2000ps` 若 σ 未定），`p2bg = peak_count / max(bg,1)`；`p2bg_health >1000` 为 HEALTHY（V13 实测 `3300-3800`）。
- **Delay sign**：`sign(peak_center)`，`t_B - t_A >0` 表示 B 滞后 A；与 `delay_used_ps` 符号一致性校验（V13 `delay -50→peak -50` / `+50→+50`）。
- **Total pairs in window / acquisition**：`summary.count_A/B`, `total_pairs_in_window`, `acquisition_duration_s`。
- **契约审计**：逐字段 `PASS/MISMATCH/INCOMPLETE` 矩阵（含 `nearest_threshold 40000ps / pairing_mode nearest / frame_period 204800ps / wrap_rule floor_div` 等），V13 值从 sidecar 实时读作参考，不硬编码。
- **背景 NLL/相关率**（仅作 Path B 判定背景，不重算码率）：沿用 V56D0 的 `A==B 率 / U1/U2 / Bob-conditioned NLL(q_mass)` 作为 `still_low` 判断的辅助，若 raw 峰正确但 NLL 仍 `>>1.5` 则 B。

## 3. 逐源分流与总体终态（A2 专用，四态互斥）

> **域拆分**：`A2 = raw TTBin delay/peak/pairing contract`（需 actual raw peak/delay/channel 证据），`B = 排除 A2 后物理域迁移`；`A1` 已由 V56D0 排除 (`k*=0`)，本诊断不再判 A1。
> **四态**：`PATH_A2_ALL / PATH_B_ALL / MIXED_BY_SOURCE / INCONCLUSIVE`（含 `INCONCLUSIVE_METADATA_INCOMPLETE`、`INCOMPLETE_TTBin_UNAVAILABLE`）。

```
per_source in {1M,1p5M,2M}:
  if raw_unavailable (TimeTagger missing / file missing):
    → INCONCLUSIVE_NEED_CALIBRATION (INCOMPLETE_TTBin_UNAVAILABLE)
  elif explicit_contract_error:
    // peak_missing (p2bg<10) OR |peak_center - delay_used|>50ps when delay known OR sign mismatch
    // OR σ>150ps broad / channel_mismatch / nearest_threshold !=40000 / pairing reversed / frame_start offset
    → PATH_A2_RAW_CONTRACT_ERROR (可修复，需 0重叠 calibration 验证)
  elif peak_shape_healthy (p2bg>1000 && σ 50-150ps) && timing_contract_verified (|peak-delay|<50 && sign match && delay+pairing recovered) && still_low (A==B<45% && NLL>>1.0):
    → PATH_B_DOMAIN_SHIFT (raw 正确且契约已验证但相关率仍低，需重估熵/泄漏)
  elif peak_shape_healthy (p2bg>1000 && σ 50-150ps) && !timing_contract_verified && still_low:
    → INCONCLUSIVE_A2_NOT_EXCLUDED (peak 健康但 V55 delay/pairing 不可追溯，不得判 B，A2 未排除)
  elif missing_raw_fields without actual raw evidence:
    → INCONCLUSIVE_METADATA_INCOMPLETE
  else:
    → INCONCLUSIVE

overall in {PATH_A2_ALL, PATH_B_ALL, MIXED_BY_SOURCE, INCONCLUSIVE}:
  if all per_source == PATH_A2: → PATH_A2_ALL
  elif all per_source == PATH_B: → PATH_B_ALL
  elif any INCONCLUSIVE* without uniform: → INCONCLUSIVE or MIXED_BY_SOURCE
  elif decisions differ: → MIXED_BY_SOURCE
  else: → INCONCLUSIVE
```

### 3.1 PATH_A2 — raw TTBin 契约错误（需 actual raw 证据，可修复）

- **证据**：`actual raw peak/delay/channel` 实测与声明不一致
  - `|peak_center - delay_used_ps| >50ps`（若 `delay_used_ps` 已知；V55 侧缺则由 `peak_center` 偏差 + `p2bg` 综合判）
  - `peak_missing`：`p2bg<10` 或 `counts` 无明显单峰（`peak_count` 不显著高于 `bg_median*10`）
  - `σ>150ps` 弥散或 `FWHM>350ps`
  - `channel 错配`：`count_A(1)` 或 `count_B(5)` 非主导（`<40%` of time-tag events）或 `other_channels` 显著
  - `nearest_threshold` 非 `40000ps` 预期或 `pairing_direction` 反向（`t_B - t_A` 符号与 `delay_sign` 预期相反）
  - `frame_start_ps / bin_origin / wrap_rule` 错位（`frame_start_ps` 缺或 `wrap_rule != floor_div`）
- **根因假设**：`FileReader` 未显式绑定 `delay_override_ps / peak_gate_sigma / frame_start_override_ps / coinc_window_override_ps`，跨 session `TimeTagger` 漂移；或 `channels A/B` 配置错误；或 `threshold/pairing` 契约丢失。
- **修复建议**：Sidecar 必填（`channels/delay_used/peak_center/σ/corr_argmax/frame_start/mapping/wrap_rule/pairing_threshold/gate_width`）+ FileReader 显式绑定（`raw_ch0_id=1, raw_ch1_id=5, threshold 40000, offset=peak_center, frame_start=peak_center` 校验 `|delay-peak|<50ps`）+ per-source G1'-G3' 门（`peak_status ok && p2bg>1000 && σ 50-150ps && |delay-peak|<50ps`）；**原 90 已揭盲禁止重跑，修复后用 0 重叠 calibration frames 验证**（8-16 frames, 0 overlap with 90, `A==B>60%` HEALTHY）。

### 3.2 PATH_B — 不同物理域，需重估条件熵/泄漏（排除 A2 后）

- **证据**：raw 实测 `peak_center` 正确对准（`|peak-delay|<50ps`, `p2bg>1000`, `σ 70-110ps` HEALTHY）但 `A==B 27-41%`、`NLL>>1.5 bits/symbol`、`q_mass_on_p_zero 57-71%` 仍低、`delta mass_0+mass_±1` 弥散（V56D0 已证 `other 56-71%`），且无 A2 契约错误。
- **根因假设**：`2026-01-23 / 2026-01-07` 的 `device/channel_params/power/delay` 与 `2026-01-21` 非同分布，真实信道 `P(A|B)` 已迁移，`H(U1|B)≈0.025 bits` 与 `H(U2|U1,B)≈0.78 bits` 的 V25 估计不再适用，`m2 184/190/192` 与 `f≈1.3` 的泄漏预算根本不适配新域。
- **重估清单**：
  1. 用新 session 的 **全量 intake** 重算 `N_ab` → `H(A|B)` → `F03` 链式 `H(U1|B), H(U2|U1,B)`（`layer_conditional_entropy_bits`），报告 `per-source H` 与 `V13` 差值。
  2. 重算 `m_total = floor((1.3*1024*H_source -64)/5)` 与 `m1_ep = round(m_total*H1/H_total)` 的 source-adaptive 预算，评估当前 `m2/leak` 的 `f` 缺口。
  3. 若 `H` 显著升高（如 `>1.2 bits`），则需重新设计 `H1` 冗余或 `Lane C` 码族，而非仅增 `Δ8`。
  4. 同样需**独立 calibration frames** 先验，再冻新 blocks。

## 4. 校准优先的下一步（Calibration-first）

- **Calibration frames 定义**：与 V55 authoritative 90-block **零重叠**、未揭盲、每源建议 `8-16` 连续 frames（`2-4` blocks）的小批量，仅用于验证基础相关性，不进入正式 TEST 统计。
- **健康阈（诊断参考，非门禁）**：`A==B>60%` 且 `U1/U2>55%` 且 `Bob-conditioned NLL<1.0 bits/symbol` 且 `delta mass_0+mass_±1>85%` 且 `raw p2bg>1000 && σ 50-150ps` 视为信道健康；低于则继续诊断，不直接调码。
- **冻结新 blocks 条件**：仅当 calibration 健康且 sidecar 契约补齐（Path A2）或熵重估完成（Path B）后，才允许另起 OpenSpec 冻结新 TEST registry（与原 90 零重叠、与 calibration 零重叠），并走独立 `QUALIFICATION_PLAN_READY` 流程。
- **本诊断不直接冻结**新 registry/blocks/correction；successor 需独立授权；**若发现明确契约错误则可修复后用 0 重叠 calibration frames 验证**（不重跑原 90），否则 Path B 走熵重估。

## 5. 诊断脚本与报告（decoder-free 守卫）

- **脚本** `diagnosis_raw_a2.py`（本变更目录下，decoder-free）：
  - 输入：`--ttbin-root` (默认 `D:\Data\Raw Data\2026.1.23|2026.1.7` 三源双文件) 或 `--intake-report` (`v55_intake_20260828/intake_report.json`) 自动解析 `provenance`；`--v13-sidecar-root` (`workspace/v13r3fresh_20260816/sidecars`)；`--counts` (`channel_counts.npz` 仅作背景 NLL)；`--registry` (`v55_authoritative_registry.json`)；`--out` (`diagnosis_raw_a2.json`)；`--recompute-corr` 开关（默认 true if TimeTagger 可用）
  - 输出：`diagnosis_raw_a2.json` (per-source `channel_hist / peak_center/width/p2bg/delay_sign / contract_matrix / per_source_decision / overall`) + 控制台摘要
  - 守卫：`rg "decode_" 0 hits`、`rg "import.*decoder"` 0、仅 `numpy/pandas/pyarrow + ttbin_pipeline(TimeTagger optional)`，零 `compute_tag_64` 以外 tag 调用；TTBin 不可用时 `INCOMPLETE_TTBin_UNAVAILABLE` 不伪造
  - 可重现：`bin_width 100 / max_lag 819200 / n_bins 16384` 固定，`lag = t_B - t_A` 显式，输出含 `HEAD 4914b56d / data SHA 84d62779 / run_at / input SHAs`
- **报告** `REPORT.md`：记录每源 `channel 校验 / peak_center/width/p2bg/delay_sign / total_pairs`、契约 `PASS/MISMATCH/INCOMPLETE` 矩阵（V13 实时读值）、`V13 vs V55` 差值、逐源 A2/B 判定与修复/重估建议、校准优先清单；结论不扩大为 FER/阈值/SKR/晋升

## 6. 守卫与禁止项（decoder-free 硬约束）

1. **Decoder 禁止**：脚本与报告生成期间 `SHALL NOT` 出现 `decode_row_layered_fftqspa / decode_* / construct_lane_c_prototype` 调用；`grep` 守卫 `0 hits`；**零 decoder、零码参数**。
2. **原 90 已揭盲保护**：`SHALL NOT` 在 `v55_authoritative_registry.json` 的 `90 blocks (30/source)` 上重跑任何 corrected pipeline（含 peak-corrected 重译），违者诊断作废。
3. **参数冻结**：`SHALL NOT` 调 `H1/Lane C/Δ8/decoder 90/1.0/m2/leak/prior` 任一参数以拟合 V55 数据。
4. **LDPC 证伪禁止**：`SHALL NOT` 将 `0/90` 记为 LDPC/NB-LDPC 证伪证据；报告必须显式声明 `0/90` 为域失配信号。
5. **校准优先**：`SHALL` 先用独立 calibration frames（0重叠）验证基础相关性后，才能另冻新 blocks 进入 qualification；本诊断不直接冻结新 blocks。若发现明确契约错误，可修复后用 calibration 验证（不重跑原 90）。

## 7. 记录、聚合、输出（本诊断）

- **输入根**（只读）：`D:\Data\Raw Data\2026.1.23|2026.1.7` 三源双文件、`v55_intake_20260828/intake_report.json + sidecars/*/sidecar_meta.json + pairs/*.parquet`、`workspace/v13r3fresh_20260816/sidecars/*/sidecar_meta.json + build_manifest.json`、`nbldpc_v25_20260818/run_04/*`、`v55_authoritative_registry.json`
- **输出**（本变更目录 additive）：`diagnosis_raw_a2.json` (machine-readable), `REPORT.md` (human-readable, 待填充), 控制台 `stdout` 摘要；不写 `run_01`，不写新 registry
- **可重现性**：脚本确定性（`numpy` 固定、TTBin 读取排序、直方图 `bin_width 100 / max_lag 819200` 固定、`lag = t_B - t_A` 显式），输出含 `HEAD 4914b56d... / data SHA 84d62779 / run_at / input SHAs / TimeTagger available`

## 8. 与 V55/V56D0 的衔接

- V55 保持 `QUALIFICATION_PLAN_READY / EXECUTE_NOT_AUTHORIZED` 且 authoritative 90-block 已冻但 `0/90` 已揭盲；V56D0 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` 已固化 `INCONCLUSIVE_METADATA_INCOMPLETE`（A1 已排除 `k*=0`，A2 缺 actual 证据）；V56D1 本诊断**补齐 A2 actual raw 证据**，不改变 V55/V56D0 终态，仅追加**raw 输入域的只读证据**。
- 诊断结论为 successor change 的**唯一入口**：`PATH_A2` → `materialization-contract-fix + calibration` change；`PATH_B` → `entropy-reestimation + calibration` change；`INCONCLUSIVE` → `calibration-only` change；三者均需独立授权；**若发现明确契约错误则可修复后用 0重叠 calibration frames 验证**（不重跑原 90），若完整正确而相关率仍低则判 Path B。

## 9. 自由裁量 D1–D8（本诊断）

- D1 Raw 重算固定为 `ch_a=1/ch_b=5, bin_width 100ps, max_lag 819200ps, n_bins 16384, lag=t_B-t_A`，不扩展至多通道/可变 bin
- D2 契约审计维度固定为 `channels/delay/peak/σ/corr/frame_start/bin_origin/wrap_rule/pairing_threshold/gate/occupancy` 等，不扩展至光路物理参数
- D3 Peak 拟合固定为 `argmax + FWHM→σ + median bg p2bg`，不做高斯/洛伦兹拟合网格
- D4 分流阈启发固定为 `|peak-delay|>50ps / p2bg 1000/10 / σ 50-150ps / rate 60%/45% / NLL 1.0` 仅作证据描述，不作门禁
- D5 修复建议固定为 sidecar 必填 + FileReader 显式绑定 + per-source G1'-G3'，已达最简
- D6 重估清单固定为 `H(U1|B)/H(U2|U1,B)/m_total/f` 四项，不重设计码族
- D7 校准帧固定为 `8-16` frames 小批量，不进入正式 TEST，0重叠可机械校验
- D8 本诊断为 decoder-free 只读，不产生新 registry/blocks，等待 successor
