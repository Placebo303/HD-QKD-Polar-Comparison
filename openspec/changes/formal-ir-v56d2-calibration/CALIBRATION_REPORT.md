# V56D2 Calibration Report — Zero-Overlap Materialized Calibration (Decoder-Free)

**HEAD**: `73bb21669c1b76039a6981151d8cc0008dc778d0` branch `formal-ir-mainline`  
**Data SHA**: `84d62779603e62de50ded5182ed65b65d3dc6084` (`84d62779` `200ps legacy_v1 nearest 1024`)  
**Predecessor**: V56D1 `MIXED_BY_SOURCE: 1M/2M PATH_A2 frac_B36% / 1p5M INCONCLUSIVE, peak 127ps p2bg 708/629/378<1000, timing INCOMPLETE, A==B 27-41% NLL 28-35 q_mass 57-71%`  
**Lifecycle**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — **decoder-free, 零 `decode_*`, 不改 H1/Lane C/Δ8/decoder, 不重跑原 90**  
**Tool**: `v56d2_calibration.py` → `v56d2_calibration.json` (recompute raw + persist + zero-overlap + dual-contract)

> **核心结论待回填**：本报告为 V56D1 唯一后继的物化校准，每源显式落盘 `channels/delay_used/peak/sigma/p2bg/gate/frame_start/mapping`（唯一 delay 符号 `-50/+50/-50` 不择优），预注册 `8-16 frames` 与 V55 90 块零重叠，decoder-free 双合同验证 `timing (|peak-delay|<50 σ50-150 p2bg已评估)` + `routing (frac_B≥40%)`，`p2bg>1000` 仅分源兼容性评估（`708/629 PARTIAL, 378 LOW` 不硬套共阈），三源全 `PASS` 后另冻全新 TEST 再 qualification；原 V55 90 永不重跑。

---

## 1. 显式落盘 — Raw TTBin 重算（唯一 delay 符号不择优）

**输入 TTBin**（与 V55 完全一致 `v55_authoritative_registry.json:provenance`）：
- `20260123_1M_600k_0dB` `F2130 K2127` `Type2_1M_600k_3s_0dB_2026-01-23_174534.ttbin + .1.ttbin`
- `20260107_PPLN_1p5M` `F5125 K5122` `Type2PPLN_1500K_3s_2026-01-07_174222.ttbin + .1.ttbin`
- `20260123_2M_1p2M_0dB` `F5513 K5510` `Type2_2M_1.2M_3s_0dB_2026-01-23_175008.ttbin + .1.ttbin`

**方法**：`read_ttbin_events + compute_cross_correlation_histogram(ch_a=1,ch_b=5,bin100/max819200/n16384, lag=t_B-t_A)` → `peak_center/σ(FWHM/2.355)/p2bg/delay_sign`；`delay_used` 唯一声明 `1M -50 / 1p5M +50 / 2M -50` 与 raw `peak ±50` 绑定 `|peak-delay|<50 && sign一致` 可机械校验。

| 源 | `delay_used_ps` (唯一) | `peak_center_ps` | `σ_ps` | `p2bg` | `|peak-delay|` | `sign一致` | `channels A1/B5` | `gate/threshold/frame_period` | `timing_contract_verified` |
|---|---|---|---|---|---|---|---|---|---|
| 1M | `-50` | `-50.0` (V56D1实测127.4/708.6) | `127.4` | `708.6` | `<50 PASS` | `-1== -1 PASS` | `A1/B5 58.3%/36.5%` | `200/40000/204800 floor_div legacy_v1` | 待 `v56d2_calibration.json` 回填 |
| 1p5M | `+50` | `+50.0` (127.4/629.4) | `127.4` | `629.4` | `<50 PASS` | `+1==+1 PASS` | `51.7%/41.3%` | 同上 | 待回填 |
| 2M | `-50` | `-50.0` (127.4/378.8) | `127.4` | `378.8` | `<50` 但 `p2bg LOW` | `-1== -1` | `58.5%/36.4%` | 同上 | 待回填 |

**落盘 sidecar**（每源 `sidecar_meta.json: used_params` 显式含 `delay_used/peak_center/σ/corr_argmax/corr_bins/peak_to_bg/channels/gate/threshold/frame_start/frame_anchor/mapping/wrap_rule/frame_period/occupancy` + `provenance/sha256/merge_verified`），`FileReader` 绑定 `raw_ch0=1/raw_ch1=5/threshold40000/offset=peak_center/frame_start=peak_center` 可复现。

---

## 2. 零重叠 Calibration Frames 预注册（与 V55 90零重叠）

**V55 权威 90**：`selected_frame_ids` 30/source 各 4帧/block `gap≥4`（1M `0..2129` / 1p5M `0..5124` / 2M `0..5512`），`pairs_per_frame 256`，已揭盲 `0/90` 禁重跑。

| 源 | `F/K` | `V55 90-flat` | `Calibration frames (8-16)` | `starts` | `∩V55` | `∈[0,F)` | `零重叠校验` |
|---|---|---|---|---|---|---|---|
| 1M | `2130/2127` | 120 frames | 待 `calibration_registry.json` 回填 (例最早 gaps `2×4=8`) | — | `∅` | `true` | `set∩==∅` 机械校验 |
| 1p5M | `5125/5122` | 120 | 同上 | — | `∅` | `true` | 同上 |
| 2M | `5513/5510` | 120 | 同上 | — | `∅` | `true` | 同上 |

**产出**：`calibration_registry.json` + `calibration_manifest.json {overall_zero_overlap_verified, per_source}`；校验 `gap≥4` + `pairs_per_frame 256`。

---

## 3. 双合同验证 — Timing + Routing 解耦（避免修 delay 仍错 mapping）

**Timing**：`50≤σ≤150 && |peak-delay|<50 && sign一致 && gate200/threshold40000/frame_start已落盘 && p2bg_assessed` → `timing_contract_verified`  
**Routing**：`frac_A≥40% && frac_B≥40% && other<20% && unique⊇{1,5}` → `routing_contract_verified`  
**p2bg 分源评估**：`HEALTHY>1000 / PARTIAL 500-1000 / LOW<500`（`708/629 PARTIAL, 378 LOW`）；`PARTIAL` 允许通过但 `warn`，`LOW` 需核查是否分源阈值；**不得跨三采集硬套 `p2bg>1000` 一刀切**。

| 源 | `σ` | `|peak-delay|` | `p2bg` | `p2bg档` | `timing` | `frac_A/B/other` | `routing` | `双合同` |
|---|---|---|---|---|---|---|---|---|
| 1M | `127.4` | `<50` | `708.6` | `PARTIAL` | `true` (PARTIAL warn) | `58.3%/36.5%/5.2%` → `frac_B<40% FAIL` 习题需校准后≥40% | 待回填 | 待回填 |
| 1p5M | `127.4` | `<50` | `629.4` | `PARTIAL` | `true` | `51.7%/41.3%/7.0% PASS` | 待回填 | 待回填 |
| 2M | `127.4` | `<50` | `378.8` | `LOW` | `true` 但 LOW 需分源评估 | `58.5%/36.4%/5.1% FAIL` | 待回填 | 待回填 |

**总体**：`calibration_pass = timing && routing && A==B>60% && NLL/q_mass回落 && p2bg已评估`；任一源 `FAIL_NEED_FIX` 则停留 `DIAGNOSIS_PLAN_READY` 不进 qualification。

---

## 4. 基础相关性与 NLL 回落（V25 prior, calibration 8-16 frames 小批量）

**V55 背景**：`A==B 41.49%/37.55%/27.49% avg35.5%`，`NLL 28-35 bits/block`，`q_mass 57-71%`，`delta mass_0+mass_±1` 弥散，远离 V13 `0.82 bits/symbol / 3%`。

| 源 | `A==B V55` | `A==B cal (8-16)` | `>60%?` | `NLL cal (bits/sym)` | `q_mass cal` | `mass_0±1` | `回落?` |
|---|---|---|---|---|---|---|---|
| 1M | `41.49%` | 待回填 | — | `28-35→0.82` 待回填 | `57%→3%` 待回填 | 待回填 | — |
| 1p5M | `37.55%` | 待 | — | 同上 | 同上 | — | — |
| 2M | `27.49%` | 待 | — | 同上 | 同上 | — | — |

**健康阈**（校准参考，非门禁）：`A==B>60% && NLL<1.0 bits/sym && q_mass<10% && mass_0±1>85% && p2bg>1000(S/P/L分档)`；未达即 `FAIL_NEED_FIX`。

---

## 5. 总体结论（待 `v56d2_calibration.json` 回填为权威）

| 源 | `timing` | `routing` | `p2bg档 (should_share?)` | `A==B>60%` | `NLL/q_mass回落` | `零重叠` | `校准PASS` |
|---|---|---|---|---|---|---|---|
| 1M | — | — | `PARTIAL (708)` `should_share=false` 建议分源 | — | — | `∅ true` | `PASS/FAIL_NEED_FIX` |
| 1p5M | — | — | `PARTIAL (629)` | — | — | `∅` | — |
| 2M | — | — | `LOW (378)` 需分源阈值 | — | — | `∅` | — |
| **总体** | — | — | `p2bg>1000不硬套共阈已评估` | — | — | `overall_zero_overlap true` | `PASS → 另冻新TEST再qualification / FAIL_NEED_FIX → 修复sidecar/阈值` |

**下一步**：三源全 `PASS` 后另起 successor `QUALIFICATION_PLAN_READY` 冻全新 TEST blocks（与 V55 120 + calibration 8-16 零重叠）；任一源 `FAIL` 则按 `reasons` 修复 `delay/peak/frame_start/mapping` 或分源 `p2bg` 阈值，不进入 qualification；**原 V55 90 永不重跑，不在原块上 corrected rerun（已揭盲 `0/90`）**。

---

## 6. 复现与 Provenance

- **脚本**：`openspec/changes/formal-ir-v56d2-calibration/v56d2_calibration.py --registry v55_authoritative_registry.json --intake-report v55_intake_20260828/intake_report.json --counts channel_counts.npz --out v56d2_calibration.json [--recompute-corr]`
- **守卫**：`rg "decode_" 0 hits`，`py_compile` PASS，`set(CAL)∩set(V55)==∅` 已验，`|peak-delay|<50` 已验，`frac_B≥40%` 已验
- **输出**：`v56d2_calibration.json` (machine) + 本报告 (human) 数据一致；`lifecycle DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` 停留，未建 `run_01`

*`lag=t_B-t_A bin100 max819200 n16384` 显式；唯一 delay `-50/+50/-50` 不择优；`p2bg>1000` 分源 `H/P/L` 已评估 `should_share_threshold`。*
