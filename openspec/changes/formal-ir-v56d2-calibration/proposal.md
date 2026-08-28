# OpenSpec Proposal: formal-ir-v56d2-calibration

**Status**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — **decoder-free 小规模零重叠物化校准，不运行 L1/L2 decoder，不改方法，不重跑原 90 块。**
**Domain**: Formal IR / V56D2 calibration (V56D1 唯一后继)
**Change ID**: `formal-ir-v56d2-calibration`
**Cycle ID**: `V56D2` calibration (predecessor `V56D1` `formal-ir-v56d1-raw-a2-diagnosis`)
**Predecessor**: `formal-ir-v56d1-raw-a2-diagnosis` (HEAD `73bb21669c1b76039a6981151d8cc0008dc778d0`, branch `formal-ir-mainline`, data SHA `84d62779603e62de50ded5182ed65b65d3dc6084` `84d62779` `200ps legacy_v1 nearest 1024` 单点, 结论 `MIXED_BY_SOURCE: 1M/2M PATH_A2 frac_B 36% + V55 无 delay/peak 记录 + timing_contract_verified全false / 1p5M INCONCLUSIVE`, 三源 raw peak `σ~127ps` 窄壂但 p2bg `708/629/378` <1000/ V55 gap, `A==B 27-41%` NLL `28-35` q_mass `57-71%`)
**Branch**: `formal-ir-mainline`
**HEAD**: `73bb21669c1b76039a6981151d8cc0008dc778d0` (2026-08-29 V56D1 固化后最新)
**Data SHA**: `84d62779603e62de50ded5182ed65b65d3dc6084` (200ps legacy_v1 nearest 1024) 单点不改
**Lifecycle**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — 仅 decoder-free 重算+物化落盘+只读验证，不产生 `run_01` decoder 执行，不改 `H1/Lane C/Δ8/decoder 90/1.0`
**Method frozen**: `V54二阶段 H1-16(80b) + L1-APP via H1 BP + Lane C m2 184/190/192 + H_inc1/2 Δ8+8 + decoder 90/1.0 poly37 + L2-only tag` 完全冻结

> ponytail lite: 本变更仅 6 文件 (`proposal/design/tasks/specs/spec.md` + `v56d2_calibration.py` decoder-free + `CALIBRATION_REPORT.md`) + 3×sidecar 落盘 + 零重叠 calibration frames 预注册；无 runner、无 decoder、无新矩阵，最短科学路径闭环。

## Goal

按最短科学路径启动 **V56D2 小规模零重叠物化校准**，在 V56D1 `MIXED_BY_SOURCE` 之上做 **唯一可修复处的显式落盘与 decoder-free 验证**，为后续是否另冻全新 TEST blocks 走 qualification 铺路：

1. **用 raw TTBin 重新显式计算并落盘每源 `channels/delay_used/peak/sigma/p2bg/gate/frame_start/mapping` 唯一真值**（不择优）：每源声明唯一 delay 符号（1M `-50ps`, 1p5M `+50ps`, 2M `-50ps` 与 V56D1 raw 实测 `peak_center ±50ps, σ127ps` 对齐），`delay_used == peak_center` 显式绑定 `|peak-delay|<50ps` 可机械校验，不在 `-50/+50` 间择优，不做多 delay 网格搜索；`channels {A:1,B:5}` + `gate 200ps` + `threshold 40000ps` + `frame_start/frame_period 204800ps/wrap_rule floor_div/mapping` 全部显式落盘 sidecar，FileReader 绑定可复现。
2. **每源预注册 8-16 个 calibration frames，与 V55 authoritative 90 块零重叠**（registry `selected_frame_ids` 共 90×4 frames, 1M `0..2129` 30 blocks / 1p5M `0..5124` / 2M `0..5512` deterministic；`need 30 gap≥4`，脚本机械校验 `set(calibration_frame_ids) ∩ set(V55_frame_ids) == ∅` + `frame_id ∈ [0, F-1]` + `pairs_per_frame 256` + 连续性/非重叠）
3. **仅 decoder-free 验证，满足双合同才算校准通过**：
   - **时间对齐合同**：`timing_contract_verified` — `peak` 健康（窄 `σ 50-150ps`）且 `|peak - delay_used|<50ps` 且 `sign一致` 且 `peak_to_bg` 兼容性已评估（见下）且 `gate/threshold/frame_start` 已显式落盘；
   - **通道路由合同**：`frac_B≥40% && frac_A≥40% && other<20% && unique_channels=={1,5}(+sync 1001/1002)` — 避免修 delay 后仍错 mapping；
   - **基础相关性**：`A==B >60%` 在 calibration 小批量上（8-16 frames）回升（从 V55 `27-41%`），`V25 prior (channel_counts.npz)` 下 `NLL` 从 `28-35 bits/block` 向 `V13 0.82 bits/symbol` 靠近、`q_mass_on_p_zero` 从 `57-71%` 向 `3%` 回落、`delta mass_0+mass_±1` 聚拢；
   - `p2bg>1000` 仅作**兼容性目标**先核查：当前 raw p2bg `708/629/378` 均 `<1000` 直接硬套必败，需分源评估是否应跨三采集强制共用阈值，报告 `per-source p2bg HEALTHY/PARTIAL/LOW` 与是否需分源阈值。
4. **三源全过后另冻全新 TEST blocks，再 qualification**；原 V55 90 块永不重跑，不在原块上做 corrected rerun（已揭盲 `0/90` 不得回注）。

## Non-Goals

- 不运行任何 `L1-APP / L2` decoder；不改 `H1-16 / Lane C / H_inc1/2 Δ8+8 / m2 184/190/192 / leak / tag / prior / decoder 90/1.0 poly37` 任一冻结量；不试新 `Δm/degree/seed`；不做 `bin_width/dimension/pairing` 网格搜索（`200ps legacy_v1 nearest 1024` 单点锚点）
- 不在原 V55 authoritative 90-block 上重跑任何 corrected pipeline / offset-corrected 重译（已揭盲 `0/90`，`base→Δ8→Δ16` 任一变体均禁）；不将校准择优值回注为新 pipeline
- 不宣称 LDPC 证伪 / FER / 阈值 / SKR / 晋升；本校准仅为 `DIAGNOSIS_PLAN_READY` 的物化验证，不直接进入 qualification
- 不创建正式 `.../v56d2_*/run_01` decoder 执行；校准帧冻结后 qualification 需另起 OpenSpec 与独立授权
- 不改写/覆盖 `V38–V56D1` 任何已有输出与终态（只读）；不直接修改 `AGENT_PROJECT_MEMORY.md / docs/decision-log.md`

## Scope

1. **冻结方法零改**：`n=1024, m2 184/190/192, GF32 poly37, H1-16 rank16 80b, L1-APP q via H1 BP (TRAIN channel_counts.npz), Lane C ordinal-2, H_inc1/2 Δ8+8, decoder 90/1.0 early-stop, L2-only tag 64b, TRAIN-only prior` 全只读，**零 decoder**
2. **Raw TTBin 显式重算与落盘**（decoder-free）：由 `v55_authoritative_registry.json:provenance` 解析三源双文件 `*.ttbin+*.1.ttbin`，调用 `read_ttbin_events` + `compute_cross_correlation_histogram(ch_a=1,ch_b=5,bin100/max_lag819200/n16384, lag=t_B-t_A)` 重算 `peak_center/σ/p2bg/delay_sign`，按源声明唯一 `delay_used -50/+50/-50`（不择优）落盘 `sidecar_meta.json: used_params={delay_used_ps, peak_center_ps, peak_sigma_ps, corr_argmax, corr_bins, peak_to_bg, peak_status, channels, gate_width_ps, pairing_threshold_ps, frame_start_ps, frame_anchor, mapping, wrap_rule, frame_period_ps, occupancy_filter}` + `provenance/sha256/merge_verified`
3. **Calibration frames 预注册**（零重叠，可机械校验）：每源 `8-16 frames` = `2-4 blocks×4` 连续帧，`pairs_per_frame 256`，`frame_id` 全部落在 `[0, F-1]` 且与 V55 `selected_frame_ids` 零交集；脚本校验 `gap≥4` 与 `set ∩ ==∅`，输出 `calibration_registry.json` + `calibration_manifest.json`
4. **Decoder-free 双合同验证**（timing + routing）：`timing_contract_verified (|peak-delay|<50 && sign && σ 50-150 && gate/threshold/frame_start 已落盘)` + `routing frac_B≥40% && frac_A≥40%` + `A==B>60%` + `NLL/q_mass` 向 V13 回落 + `p2bg>1000` 分源兼容性评估（`708/629/378` 现状下不得硬阈一刀切）
5. **三源全过 → 另冻全新 TEST blocks 再 qualification**；任一源不满足则停留在 `DIAGNOSIS_PLAN_READY` 修侧参数，不进入 qualification

## Impact Scope

- **新增/修订（本校准）**：`openspec/changes/formal-ir-v56d2-calibration/` 下 6 文件：`proposal.md/design.md/tasks.md/specs/spec.md` + `v56d2_calibration.py` (decoder-free) + `CALIBRATION_REPORT.md` (per-source 落盘/双合同/相关性/NLL/p2bg 分源评估，待填充实测值)；`specs/spec.md` 为增量（本校准仍 decoder-free，不改方法 spec 主体）
- **只读依赖**：`src/qkd_io/ttbin_pipeline.read_ttbin_events/compute_cross_correlation_histogram` + `v55_authoritative_registry.json` + `v55_intake_20260828/intake_report.json + pairs/*.parquet` + `workspace/v13r3fresh_20260816/sidecars/*/sidecar_meta.json + build_manifest.json` + `nbldpc_v25_20260818/run_04/channel_counts.npz`
- **不修改**：任何既有 `spec/代码/测试/输出`、`V38–V56D1` 输出、`outputs_comparison/workspace` 以外；不创建正式 TEST `run_01`；**零 decoder、零码参数**

## Acceptance Criteria

- [ ] `proposal/design/tasks/specs/spec.md` 齐全一致，lifecycle `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`，HEAD `73bb2166` + branch `formal-ir-mainline` + data SHA `84d62779` 已绑定，显式声明 decoder-free、零 decoder、禁重跑原 90、禁调 H1/Lane C/Δ8/decoder
- [ ] **显式落盘**可复现：每源 `sidecar_meta.json` 已落盘 `channels {A:1,B:5} / delay_used -50/+50/-50 / peak_center ±50 / σ~127 / p2bg 378-708 / gate 200 / threshold 40000 / frame_start / mapping / wrap_rule / frame_period 204800`，且 `|peak-delay|<50ps` `sign一致` 可机械校验，唯一 delay 符号不择优
- [ ] **零重叠预注册**可复现：每源 `8-16 frames` calibration 帧 `set ∩ V55 ==∅`、`frame_id∈[0,F-1]`、`gap≥4`、`pairs_per_frame 256` 已校验，`calibration_registry.json` 已生成
- [ ] **双合同验证**可复现：`timing_contract_verified` + `routing frac_B≥40%` 双门已逐源判定；`A==B>60%` 在 calibration 小批量上已核验（或未达即 `FAIL_NEED_FIX` 不进入 qualification）；`p2bg>1000` 已作分源兼容性评估（`708/629/378` 现状下不硬套共阈，报告 `per-source HEALTHY/PARTIAL/LOW` 与是否需分源阈值）
- [ ] `V25 prior` 下 `NLL` 从 `28-35` 向 `~0.82` 回落、`q_mass_on_p_zero` 从 `57-71%` 向 `3%` 回落已逐源报告
- [ ] `v56d2_calibration.py` 为 decoder-free 可运行脚本（`rg "decode_" 0 hits`），仅 `numpy/pandas/pyarrow + ttbin_pipeline(TimeTagger optional)`，输出 `v56d2_calibration.json` + 控制台摘要，`py_compile` PASS
- [ ] `CALIBRATION_REPORT.md` 已记录每源落盘值/双合同/相关性/NLL/p2bg 分源评估与总体结论，数据与 `v56d2_calibration.json` 一致，结论不扩大为 FER/阈值/SKR/晋升，明确原 90 已揭盲不可复用
- [ ] 已推送并停留在 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`，未创建任何 `.../v56d2_*/run_01` decoder 执行

## Tasks

见 `tasks.md`（Phase A 显式重算落盘；Phase B 8-16 零重叠预注册；Phase C 双合同解耦验证 + p2bg 分源评估；Phase D 相关性/NLL 回落；Phase E 脚本与报告交付）

## Lifecycle

V56D1 当前 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`（HEAD `73bb2166`, `MIXED_BY_SOURCE: 1M/2M PATH_A2 frac_B36% 2M p2bg378 / 1p5M INCONCLUSIVE`, 三源 `timing INCOMPLETE p2bg708/629/378<1000`）；V56D2 本校准 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`（仅物化落盘与 decoder-free 验证，不实现 runner，不执行 decoder，不创建 run_01）；三源 calibration 全 `PASS` 后**另起 successor** 冻全新 TEST blocks 再走 `QUALIFICATION_PLAN_READY`，本校准不直接进入 qualification。
