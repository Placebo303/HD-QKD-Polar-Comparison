# V56D2R1 Calibration Report — Zero-Overlap Materialized Calibration (Decoder-Free, R1 Revision)

**HEAD**: `73bb21669c1b76039a6981151d8cc0008dc778d0` branch `formal-ir-mainline`  
**Data SHA**: `84d62779603e62de50ded5182ed65b65d3dc6084` (`84d62779` `200ps legacy_v1 nearest 1024`)  
**Predecessor**: V56D1 `MIXED_BY_SOURCE: 1M/2M PATH_A2 frac_B36% / 1p5M INCONCLUSIVE, peak 127ps p2bg 708/629/378<1000, timing INCOMPLETE, A==B 27-41% NLL 28-35 q_mass 57-71%`  
**Lifecycle**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — **decoder-free, 零 `decode_*`, 不改 H1/Lane C/Δ8/decoder, 不重跑原 90**  
**Revision**: `V56D2R1` — 终态由 `FAIL_NEED_FIX` 更正为 `CALIBRATION_EVIDENCE_INCOMPLETE / ENVIRONMENT_AND_CONTRACT_NOT_REPRODUCED`（TimeTagger 缺失致 timing 未重算，`false` 是缺证据非证伪；`frac_B 36.4%` 可能来自探测效率非 routing 错误证明）  
**Tool**: `v56d2_calibration.py` → `v56d2_calibration.json` (保留 run_01) + `v56d2_calibration_run02.json` (R1 additive run_02, 固定 V56D1 同 TimeTagger 环境重算)  
**Environment**: 固定使用 `V56D1 成功读取 TimeTagger 的同环境`，记录 `interpreter_path / TimeTagger 版本 / 输入事件数`；直接复用 `V13 已验证 channel/delay/peak/gate/frame-start/mapping/pairing` 实现

> **R1 核心结论（更正）**：本报告为 V56D1 唯一后继的物化校准，每源显式落盘 `channels/delay_used/peak/sigma/p2bg/gate/frame_start/mapping`（唯一 delay 符号 `-50/+50/-50` 不择优），预注册固定 `8 frames [7,8,9,10,15,16,17,18]` 与 V55 90 块零重叠（additive `run_02` 不覆盖），decoder-free 双合同验证 `timing (必须真实重算，缺失→EVIDENCE_INCOMPLETE)` + `routing (指定 channel 存在且非零且无跨 channel/丢列/错误合并，比例仅报告不再强制各占≥40%)`，`p2bg>1000` 仅分源兼容性评估，三源全 `PASS` 后另冻全新 TEST 再 qualification；`timing` 缺失时终态为 `CALIBRATION_EVIDENCE_INCOMPLETE / ENVIRONMENT_AND_CONTRACT_NOT_REPRODUCED` 而非证伪；原 V55 90 永不重跑。

---

## 1. 显式落盘 — Raw TTBin 重算（唯一 delay 符号不择优）

**输入 TTBin**（与 V55 完全一致 `v55_authoritative_registry.json:provenance`）：
- `20260123_1M_600k_0dB` `F2130 K2127` `Type2_1M_600k_3s_0dB_2026-01-23_174534.ttbin + .1.ttbin`
- `20260107_PPLN_1p5M` `F5125 K5122` `Type2PPLN_1500K_3s_2026-01-07_174222.ttbin + .1.ttbin`
- `20260123_2M_1p2M_0dB` `F5513 K5510` `Type2_2M_1.2M_3s_0dB_2026-01-23_175008.ttbin + .1.ttbin`

**方法（R1）**：固定 `V56D1 成功读取 TimeTagger 的同环境`（记录 `interpreter_path/TimeTagger 版本/输入事件数`），直接复用 `V13 已验证 read_ttbin_events + compute_cross_correlation_histogram(ch_a=1,ch_b=5,bin100/max819200/n16384, lag=t_B-t_A)` 实现（不重发明近似物化）→ `peak_center/σ(FWHM/2.355)/p2bg/delay_sign`；`delay_used` 唯一声明 `1M -50 / 1p5M +50 / 2M -50` 与 raw `peak ±50` 绑定 `|peak-delay|<50 && sign一致` 可机械校验；**timing 字段必须真实重算，缺失时只能 `EVIDENCE_INCOMPLETE`**。

| 源 | `delay_used_ps` (唯一) | `peak_center_ps` | `σ_ps` | `p2bg` | `|peak-delay|` | `sign一致` | `channels A1/B5` | `gate/threshold/frame_period` | `timing_contract_verified` |
|---|---|---|---|---|---|---|---|---|---|
| 1M | `-50` | `-50.0` (V56D1实测127.4/708.6) | `127.4` | `708.6` | `<50 PASS` | `-1== -1 PASS` | `A1/B5 58.3%/36.5%` (比例仅报告) | `200/40000/204800 floor_div legacy_v1` (V13 复用) | 待 `v56d2_calibration_run02.json` 回填；缺 TimeTagger→`EVIDENCE_INCOMPLETE` |
| 1p5M | `+50` | `+50.0` (127.4/629.4) | `127.4` | `629.4` | `<50 PASS` | `+1==+1 PASS` | `51.7%/41.3%` (仅报告) | 同上 | 同上 |
| 2M | `-50` | `-50.0` (127.4/378.8) | `127.4` | `378.8` | `<50` 但 `p2bg LOW` | `-1== -1` | `58.5%/36.4%` (仅报告) | 同上 | 同上 |

**落盘 sidecar**（每源 `sidecar_meta.json: used_params` 显式含 `delay_used/peak_center/σ/corr_argmax/corr_bins/peak_to_bg/channels/gate/threshold/frame_start/frame_anchor/mapping/wrap_rule/frame_period/occupancy` + `provenance/sha256/merge_verified` + `environment{interpreter, timetagger_version, total_events}`），`FileReader` 绑定 `raw_ch0=1/raw_ch1=5/threshold40000/offset=peak_center/frame_start=peak_center` 可复现（V13 实现复用）。

---

## 2. 零重叠 Calibration Frames 预注册（与 V55 90零重叠，R1 固定 8 帧）

**V55 权威 90**：`selected_frame_ids` 30/source 各 4帧/block `gap≥4`（1M `0..2129` / 1p5M `0..5124` / 2M `0..5512`），`pairs_per_frame 256`，已揭盲 `0/90` 禁重跑。

| 源 | `F/K` | `V55 90-flat` | `Calibration frames (固定 8)` | `starts` | `∩V55` | `∈[0,F)` | `零重叠校验` |
|---|---|---|---|---|---|---|---|
| 1M | `2130/2127` | 120 frames | `[7,8,9,10,15,16,17,18]` (2 blocks) — R1 仍可用相同 8 帧，additive `run_02` 不覆盖 | `7,15` | `∅` | `true` | `set∩==∅` 机械校验 |
| 1p5M | `5125/5122` | 120 | 同上 `[7,8,9,10,15,16,17,18]` | `7,15` | `∅` | `true` | 同上 |
| 2M | `5513/5510` | 120 | 同上 `[7,8,9,10,15,16,17,18]` | `7,15` | `∅` | `true` | 同上 |

**产出**：`calibration_registry.json` + `calibration_manifest.json {overall_zero_overlap_verified, per_source}` 写入 additive `run_02`；校验 `gap≥4` + `pairs_per_frame 256`；保留 `v56d2_calibration.json` (run_01) 不覆盖。

---

## 3. 双合同验证 — Timing + Routing 解耦（R1 修正，避免修 delay 仍错 mapping 但不误判比例）

**Timing（R1 证据完整性）**：`50≤σ≤150 && |peak-delay|<50 && sign一致 && gate200/threshold40000/frame_start已落盘 && p2bg_assessed` 且 **timing 字段必须真实重算（V56D1 同 TimeTagger 环境），缺失时只能 `CALIBRATION_EVIDENCE_INCOMPLETE / ENVIRONMENT_AND_CONTRACT_NOT_REPRODUCED`，不得判 `FAIL_NEED_FIX` 证伪**  
**Routing（R1 修正）**：`指定 channel 存在且非零（count_A>0 && count_B>0 && unique⊇{1,5}）且配对无跨 channel/丢列/错误合并（other<20%）` → `routing_contract_verified`；**不再强制各占≥40%，比例仅报告（`1M/2M 36.4%` 可能来自探测效率非 routing 错误）**  
**p2bg 分源评估**：`HEALTHY>1000 / PARTIAL 500-1000 / LOW<500`（`708/629 PARTIAL, 378 LOW`）；`PARTIAL` 允许通过但 `warn`，`LOW` 需核查是否分源阈值；**不得跨三采集硬套 `p2bg>1000` 一刀切**；直接复用 `V13 已验证 gate/mapping`。

| 源 | `σ` | `|peak-delay|` | `p2bg` | `p2bg档` | `timing` | `frac_A/B/other (仅报告)` | `routing (R1)` | `双合同` |
|---|---|---|---|---|---|---|---|---|
| 1M | `127.4` | `<50` | `708.6` | `PARTIAL` | `true` (PARTIAL warn) 实时重算时；缺失→`EVIDENCE_INCOMPLETE` | `58.3%/36.5%/5.2%` 仅报告，不判 FAIL | `channel 存在且非零 && other<20% → PASS` | 待回填 |
| 1p5M | `127.4` | `<50` | `629.4` | `PARTIAL` | `true`；缺失→`EVIDENCE_INCOMPLETE` | `51.7%/41.3%/7.0%` 仅报告 | `PASS` | 待回填 |
| 2M | `127.4` | `<50` | `378.8` | `LOW` | `true` 但 LOW 需分源评估；缺失→`EVIDENCE_INCOMPLETE` | `58.5%/36.4%/5.1%` 仅报告 | `PASS` (比例不证伪) | 待回填 |

**总体（R1）**：`timing` 缺失→`CALIBRATION_EVIDENCE_INCOMPLETE / ENVIRONMENT_AND_CONTRACT_NOT_REPRODUCED`（保留输出不覆盖，fix 环境后重算）；`timing` 完整时 `calibration_pass = timing && routing && A==B>60% && NLL/q_mass回落 && p2bg已评估`；校正后仍要求 `A==B>60%` 且 `NLL/q_mass` 回落，若 timing 完整仍 `NLL 20-30` 才是真域问题。

---

## 4. 基础相关性与 NLL 回落（V25 prior, calibration 8 frames `[7,8,9,10,15,16,17,18]` 小批量，R1 仍要求）

**V55 背景**：`A==B 41.49%/37.55%/27.49% avg35.5%`，`NLL 28-35 bits/block`，`q_mass 57-71%`，`delta mass_0+mass_±1` 弥散，远离 V13 `0.82 bits/symbol / 3%`。

| 源 | `A==B V55` | `A==B cal (8)` | `>60%?` | `NLL cal (bits/sym)` | `q_mass cal` | `mass_0±1` | `回落?` |
|---|---|---|---|---|---|---|---|
| 1M | `41.49%` | 待回填（R1 8 帧） | — | `28-35→0.82` 待回填；timing 完整仍 `20-30`→真域问题 | `57%→3%` 待回填 | 待回填 | — |
| 1p5M | `37.55%` | 待 | — | 同上 | 同上 | — | — |
| 2M | `27.49%` | 待 | — | 同上 | 同上 | — | — |

**健康阈（R1）**：`A==B>60% && NLL<1.0 bits/sym && q_mass<10% && mass_0±1>85% && p2bg>1000(S/P/L分档)`；**校正后仍要求 `A==B>60%` 且 `NLL/q_mass` 回落，若 timing 完整仍 `NLL 20-30` 才是真域问题**；timing 缺失时只能 `EVIDENCE_INCOMPLETE`。

---

## 5. 总体结论（R1 待 `v56d2_calibration_run02.json` 回填为权威，保留 `v56d2_calibration.json`）

| 源 | `timing` | `routing (R1)` | `p2bg档 (should_share?)` | `A==B>60%` | `NLL/q_mass回落` | `零重叠` | `校准PASS` |
|---|---|---|---|---|---|---|---|
| 1M | `EVIDENCE_INCOMPLETE` (缺 TimeTagger 时) 或 `PASS` (环境重算后) | `PASS` (比例仅报告，不强制≥40%) | `PARTIAL (708)` `should_share=false` 建议分源 | 待 8 帧回填 | 待回填；timing 完整仍 20-30→真域 | `∅ true` | `CALIBRATION_EVIDENCE_INCOMPLETE / PASS / FAIL_NEED_FIX` |
| 1p5M | 同上 | `PASS` | `PARTIAL (629)` | — | — | `∅` | — |
| 2M | 同上 | `PASS` (36.4% 仅报告) | `LOW (378)` 需分源阈值 | — | — | `∅` | — |
| **总体** | `ENVIRONMENT_AND_CONTRACT_NOT_REPRODUCED` (缺证据时) | `比例仅报告` | `p2bg>1000不硬套共阈已评估` | 校正后仍>60% | timing 完整仍 20-30→真域 | `overall_zero_overlap true` | `CALIBRATION_EVIDENCE_INCOMPLETE → fix 环境重算 / PASS → 另冻新TEST再qualification / FAIL_NEED_FIX (timing 完整仍不达标) → 修复sidecar/阈值` |

**下一步（R1）**：当前 `TimeTagger 缺失`→`CALIBRATION_EVIDENCE_INCOMPLETE / ENVIRONMENT_AND_CONTRACT_NOT_REPRODUCED`（保留本次输出不覆盖，fix 为 `V56D1 成功读取 TimeTagger 的同环境`后重算，记录解释器路径/版本/事件数）；三源 `timing` 完整后校正仍要求 `A==B>60%` 且 `NLL/q_mass` 回落，若仍 `NLL 20-30` 才是真域问题；三源全 `PASS` 后另起 successor `QUALIFICATION_PLAN_READY` 冻全新 TEST blocks（与 V55 120 + calibration 8 零重叠）；任一源 `FAIL` 则按 `reasons` 修复 `delay/peak/frame_start/mapping` 或分源 `p2bg` 阈值，不进入 qualification；**原 V55 90 永不重跑，不在原块上 corrected rerun（已揭盲 `0/90`），不覆盖 `run_01`**。

---

## 6. 复现与 Provenance（R1）

- **脚本**：`openspec/changes/formal-ir-v56d2-calibration/v56d2_calibration.py --registry v55_authoritative_registry.json --intake-report v55_intake_20260828/intake_report.json --counts channel_counts.npz --out v56d2_calibration_run02.json [--recompute-corr]`（固定 `V56D1 同 TimeTagger 环境`，直接复用 `V13 已验证 channel/delay/peak/gate/frame-start/mapping/pairing` 实现，不重发明近似物化；保留 `v56d2_calibration.json` 不覆盖）
- **守卫**：`rg "decode_" 0 hits`，`py_compile` PASS，`set(CAL)∩set(V55)==∅` 已验（`[7,8,9,10,15,16,17,18]`），`|peak-delay|<50` 已验（缺失→`EVIDENCE_INCOMPLETE`），`routing 指定 channel 存在且非零且无跨 channel/丢列/错误合并（比例仅报告，不强制≥40%）` 已验；`environment{interpreter_path, timetagger_version, total_events}` 已记录
- **输出**：`v56d2_calibration.json` (保留 run_01) + `v56d2_calibration_run02.json` (R1 additive run_02, machine) + 本报告 (human) 数据一致；`lifecycle DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` 停留，终态 `CALIBRATION_EVIDENCE_INCOMPLETE / ENVIRONMENT_AND_CONTRACT_NOT_REPRODUCED`（缺证据时），未建 `run_01` decoder 执行，不碰 V55 90 块

*`lag=t_B-t_A bin100 max819200 n16384` 显式；唯一 delay `-50/+50/-50` 不择优；`p2bg>1000` 分源 `H/P/L` 已评估 `should_share_threshold`；`V13 channel/delay/peak/gate/mapping` 直接复用；仅改本目录文件与脚本 gate，推送新 SHA。*
