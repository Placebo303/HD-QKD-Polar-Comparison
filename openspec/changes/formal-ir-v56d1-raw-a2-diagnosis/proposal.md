# OpenSpec Proposal: formal-ir-v56d1-raw-a2-diagnosis

**Status**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — **decoder-free raw TTBin A2 诊断，不运行 L1/L2 decoder，不改方法，不重跑原 90 块。**
**Domain**: Formal IR / V56D1 raw-A2 原始 TTBin channel / peak / delay / pairing 诊断（V56 D0 的唯一后继）
**Change ID**: `formal-ir-v56d1-raw-a2-diagnosis`
**Cycle ID**: `V56D1` (raw-A2 diagnosis), predecessor `V56D0` `formal-ir-v56-input-domain-diagnosis`
**Predecessor**: `formal-ir-v56-input-domain-diagnosis` (lifecycle `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`, HEAD `cf8b098047cf64aa1e0426e2ea2e62b680430bd6`, data SHA `84d62779603e62de50ded5182ed65b65d3dc6084`) 固化于 `4914b56d8d353e7445a621fb142f340c37245f12` (branch `formal-ir-mainline`, 2026-08-29); V56D0 逐源 `INCONCLUSIVE_METADATA_INCOMPLETE` — 缺 raw 契约字段，需 actual raw 证据才可判 A2
**Branch**: `formal-ir-mainline`
**HEAD**: `4914b56d8d353e7445a621fb142f340c37245f12` (V56 诊断固化后最新, branch `formal-ir-mainline`)
**Data SHA**: `84d62779603e62de50ded5182ed65b65d3dc6084` (`84d62779`, `d=1024 bw=200ps pairing=nearest rule=legacy_v1` 单点, 200ps legacy_v1 nearest 1024)
**Lifecycle**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — 仅只读 raw TTBin + sidecar 审计与重算 cross-correlation，不产生 `run_01`，不产生新 TEST blocks，不调码
**Method frozen**: `V54二阶段 H1-16(80-bit) + L1-APP via H1 BP + Lane C m2 184/190/192 + H_inc1/2 Δ8+8 + decoder 90/1.0 poly37 + L2-only tag` 完全冻结，诊断期间禁止调任一参数

> ponytail lite: 本变更仅 5 文件 (`proposal/design/tasks` + `diagnosis_raw_a2.py` (decoder-free) + `REPORT.md`) + 只读 TTBin/sidecar 审计；无 runner、无 decoder、无新 registry、无新矩阵，最简闭环。

## Goal

在 V56D0 `INCONCLUSIVE_METADATA_INCOMPLETE` 之上，以 **decoder-free 只读 raw TTBin 手段**补齐 **A2 = raw TTBin delay/peak/pairing contract** 的 actual 证据，完成 V56 唯一后继的 **逐源 A2 判定**（三源逐源 + 总体四态）：

1. **从三个原始 TTBin 读取真实 channel IDs 并校验 A1/B5 声明** + **重算 timestamp cross-correlation**（`t_B - t_A` 滞后直方图，`bin_width 100ps / max_lag 819200ps / 16384 bins` 与 V13 一致口径），**输出每源 peak center（ps）、peak width（σ/FWHM, ps）、peak-to-background、delay sign**（lag  convention `t_B - t_A`）；与 V55 intake sidecar 声明的 `channels {A:1,B:5}` 逐源比对，统计 `channel=1/5` 事件数、占比、sync 通道占比，校验是否存在 channel 错配/反接/额外通道。

2. **核对 nearest threshold、pairing direction、frame start / bin origin**：读取实际 TTBin `pairing_threshold_ps / gate_width_ps / pairing_mode`、pairing 方向（`nearest_unique` greedy 单调 1-1）、`frame_start_ps / frame_anchor / bin_origin / wrap_rule / frame_period` 等，**对比 V13 实际 metrics（不硬编码 `delay -50/+50` 等，从 `workspace/v13r3fresh_20260816/sidecars/*/sidecar_meta.json` + `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/build_manifest.json` + `nbldpc_v25_20260818/run_04/*` 实时读）**，输出逐字段 `PASS / MISMATCH / INCOMPLETE` 矩阵（缺失如实 `INCOMPLETE`，有值才比对）。

3. **逐源 A2 判定，仍保持三源逐源 + 总体四态**（与 V56D0 一致，非单一 Path A/B）：
   - 逐源：`PATH_A2_RAW_CONTRACT_ERROR`（明确契约错误，可修复） / `PATH_B_DOMAIN_SHIFT`（仅当 `timing_contract_verified` 才允许） / `INCONCLUSIVE_A2_NOT_EXCLUDED`（peak 健康但 delay/pairing 不可追溯，不得判 B） / `INCONCLUSIVE` / `INCONCLUSIVE_NEED_CALIBRATION`；
   - 总体：`PATH_A2_ALL / PATH_B_ALL / MIXED_BY_SOURCE / INCONCLUSIVE`（含 `INCONCLUSIVE_METADATA_INCOMPLETE`、`INCONCLUSIVE_A2_NOT_EXCLUDED` 子态）；
   - **timing_contract_verified** 单独定义：只有恢复出 V55 实际使用的 `delay_used_ps` + `pairing_threshold_ps` 并确认与 raw peak 符号和数值 `|peak-delay|<50ps` 匹配，才允许进 Path B；已用 delay 与 raw peak 明确不匹配→ Path A2；健康峰但不可追溯→ `INCONCLUSIVE_A2_NOT_EXCLUDED`
   - 若发现**明确契约错误**（peak 中心与 `delay_used_ps` 不一致/符号反、peak 丢失/弥散、pairing 阈值/方向/frame_start 错误、channel 错配等），则**可修复后用 0 重叠 calibration frames 验证**（与原 90 零重叠、未揭盲、每源 8-16 frames 小批量，仅验基础相关性 `A==B>60%` 等价健康）；加载后记录 `total_events/acquisition_duration_s/ttbin_merge {main_size,chunk_size,merge_verified}` 并与 intake sidecar 核对，避免静默漏读 `.1.ttbin`；
   - 若**完整正确且契约已验证而相关率仍低**（`timing_contract_verified` + peak 正确对准但 `A==B 27-41%`、NLL 仍高、`delta mass_0+mass_±1` 弥散），则判 **Path B 需重估 `H(U1|B), H(U2|U1,B)` 与 `m1/m2/f` 泄漏**（source-adaptive 重算 `m_total = floor((1.3*1024*H -64)/5)`）。

4. **禁止项**（硬约束）：**禁止在原 V55 90 块上重跑 corrected pipeline**（已揭盲，`base→Δ8→Δ16` 任何变体均禁，含 offset-corrected 重译）；**禁止调 `H1 / Lane C / Δ8 / decoder 90/1.0` 任一参数以拟合 V55**；**零 decoder、零码参数**（`rg "decode_" 0 hits` 可验）。

## Non-Goals

- 不运行任何 `L1-APP / L2` decoder（`decode_row_layered_fftqspa` 等零调用）；不改 `H1-16 / Lane C / H_inc1/2 / m2 / leak / tag / prior` 任一冻结量；不试新 `Δm / degree / seed`；不做 `bin_width / dimension / pairing` 网格搜索（`200ps legacy_v1 nearest 1024` 单点为锚点，cross-correlation 仅为 `100ps` 校准口径）。
- 不在原 V55 authoritative 90-block (`v55_authoritative_registry.json` 30/source) 上重跑任何 corrected pipeline / offset-corrected 重译；不将 peak/offset 择优值回注为新 pipeline。
- 不宣称 LDPC 证伪 / FER 结论 / 阈值 / SKR / 晋升；不将 `0/90` 记为算法失败证据。
- 不做 `FER / 阈值 / SKR / 安全 / 资格 / 晋升` 的扩大陈述；tag 仍 L2-only `≈2^-64` 工程近似仅作记账背景，不作诊断门禁。
- 不改写/覆盖 `V38–V56D0` 任何已有输出与终态（只读）；本诊断不直接修改 `AGENT_PROJECT_MEMORY.md / docs/decision-log.md`（仅预留 V56D1 条目占位）。
- 不创建正式 `.../v56d1_*/run_01` / 新 authoritative registry / 新校准 blocks（校准块冻结需另起 OpenSpec，待 Path A2/B 判定后）。
- 不做 `FER / 阈值 / SKR / 晋升` 的扩大陈述；本诊断仅补 A2 actual 证据，不直接进入 qualification。

## Scope

1. **冻结方法（零改）**：`n=1024, m2 184/190/192, GF32 poly37, H1-16 rank16 80b, L1-APP q via H1 BP (TRAIN channel_counts.npz), Lane C ordinal-2, H_inc1/2 Δ8+8, decoder 90/1.0 early-stop, L2-only tag 64b, TRAIN-only prior, verification-only, leak 1064/1094/1104 +40+40`，`90块 180-360 calls` 预算——诊断期间以上全部只读，**零 decoder**。

2. **Raw TTBin 只读审计与重算**（decoder-free）：
   - 输入 TTBin（与 V55 intake 完全一致）：
     - `D:\Data\Raw Data\2026.1.23\Type2_1M_600k_3s_0dB_2026-01-23_174534.ttbin` (+ `.1.ttbin` `d47832223...`) `channel_counts: A1/B5` 待验
     - `D:\Data\Raw Data\2026.1.23\Type2_2M_1.2M_3s_0dB_2026-01-23_175008.ttbin` (+ `.1.ttbin` `e00796306...`)
     - `D:\Data\Raw Data\2026.1.7\Type2PPLN_1500K_3s_2026-01-07_174222.ttbin` (+ `.1.ttbin` `576a299cf...`) `PPLN 1p5M`
     - 亦可由 `comparison_bench/outputs_comparison/v55_intake_20260828/intake_report.json` 的 `provenance.path + sha256` 实时读（不硬编码 hash，仅作 provenance 绑定校验）
   - 调用 `src/qkd_io/ttbin_pipeline.read_ttbin_events` 读取 `time_ps/channel/event_type`，统计每通道事件数、占比，校验 `channels A1/B5` 声明；
   - 调用 `compute_cross_correlation_histogram(ch_a=1,ch_b=5,bin_width_ps=100,max_lag_ps=819200)` 重算 `lag = t_B - t_A` 直方图（16384 bins），拟合峰：`peak_center = lag_center[argmax]`、`peak_count`、`peak_width`（FWHM→σ）、`peak_to_bg = peak_count / bg_median`（bg 取 `|lag - peak| > 5σ` 区间中位）、`delay_sign = sign(peak_center)`；报告三源 `peak_center / σ / p2bg / delay_sign / total_pairs_in_window`；
   - 失败降级：若 `TimeTagger` 不可用，仅报告 `INCOMPLETE_TTBin_UNAVAILABLE` 并回退到 sidecar 审计，不伪造 peak。

3. **契约字段审计**（decoder-free，实时读 V13 实际 sidecars，不硬编码）：
   - 读取 V13 侧 `workspace/v13r3fresh_20260816/sidecars/*/sidecar_meta.json` 的 `used_params`（`delay_used_ps / peak_center_ps / peak_sigma_ps / corr_argmax / corr_bins / corr_max / peak_to_bg / pairing_threshold_ps / gate_width_ps / pairing_mode / frame_start_ps / frame_anchor / mapping / wrap_rule / occupancy_filter / frame_period_ps`）与 `build_manifest.json` 的 `provenance/source_ttbin_paths`；
   - 读取 V55 侧 `comparison_bench/outputs_comparison/v55_intake_20260828/sidecars/*/sidecar_meta.json` 同字段 + `intake_report.json` + `v55_authoritative_registry.json`；
   - 亦实时读取 `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/data_inventory.json / channel_summary.json` 的 `delta_by_source` 作 `mass_0 / mass_±1` 基线；
   - 输出逐字段 `PASS / MISMATCH / INCOMPLETE` 矩阵，重点标记 `nearest_threshold_ps / pairing_direction / frame_start_ps / bin_origin / wrap_rule / delay_used_ps / peak_center` 在 V55 侧的缺失或不一致。

4. **逐源 A2 判定与总体四态**（与 V56D0 一致的四态扩展，A2 专用）：
   - **逐源三判定 + 总体四态**：`PATH_A2_RAW_CONTRACT_ERROR`（明确 raw 契约错误，可修复） / `PATH_B_DOMAIN_SHIFT`（完整正确但相关率仍低，需重估熵/泄漏） / `MIXED_BY_SOURCE`（源间不一致） / `INCONCLUSIVE`（含 `INCONCLUSIVE_METADATA_INCOMPLETE`、`INCOMPLETE_TTBin_UNAVAILABLE`）；
   - **PATH_A2 可修复**：若某源 `peak_center` 与 `delay_used_ps` 偏差 `>50ps` 或 `peak_missing/low p2bg<10 / σ>150ps弥散 / channel 错配 / pairing 阈值/方向错误 / frame_start 错位` 且 raw 证据确凿 ⇒ 该源 `A2`，输出 contract 修复（sidecar 必填 + FileReader 显式绑定 `delay_override / peak_gate_sigma / frame_start_override / coinc_window`）并声明原 90 已揭盲不可复用，**修复后用 0 重叠 calibration frames 验证**（8-16 frames, 0 overlap with 90）；
   - **PATH_B 域迁移**：若某源 peak 正确对准（`|peak_center - delay_used|<50ps`, p2bg>1000, σ~70-110ps HEALTHY）但 `A==B 27-41%`、`NLL>>1.5`、`q_mass_on_p_zero 57-71%` 仍低 ⇒ 该源 `B`，需重估 `H(U1|B), H(U2|U1,B)` 与 `m1/m2/f`；
   - **MIXED_BY_SOURCE**：源间判定不一致时逐源分别给建议；
   - **INCONCLUSIVE**：TTBin 不可用或证据不足时，仅 `INCONCLUSIVE` 不自动判 A2/B，需补 calibration。

5. **校准优先的下一步**（冻结原则）：无论 Path A2/B，均**先用独立 calibration frames**（与原 90 零重叠、未揭盲、每源 `8-16` frames 小批量）验证基础相关性（`A==B>60%` 且 `NLL<1.0 bits/symbol` 等价量为健康阈，诊断阈非门禁），通过后再另冻新 blocks 进入 qualification；校准块冻结需新 OpenSpec 与独立执行授权；本诊断不直接冻结新 blocks。

## Impact Scope

- **新增/修订（本诊断）**：`openspec/changes/formal-ir-v56d1-raw-a2-diagnosis/` 下 5 文件：`proposal.md / design.md / tasks.md / diagnosis_raw_a2.py (decoder-free) / REPORT.md (待填充，含 per-source peak/channel/contract/B判定)`；`specs/spec.md` 可选增量（本诊断为只读分析，不改方法 spec，主 spec 保持 V55/V56D0 冻结）
- **只读依赖**：`src/qkd_io/ttbin_pipeline.py` (`read_ttbin_events`, `compute_cross_correlation_histogram`, `compute_ttbin_metrics`)、`comparison_bench/outputs_comparison/v55_intake_20260828/intake_report.json + sidecars/*/sidecar_meta.json + pairs/*.parquet`、`workspace/v13r3fresh_20260816/sidecars/*/sidecar_meta.json + build_manifest.json`、`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz + data_inventory.json + channel_summary.json + delta_by_source.csv`、`v55_authoritative_registry.json`、`nonbinary_v25_gate.py` (P(A|B)/NLL 仅作背景，不调用 decoder)
- **不修改**：任何既有 `spec/代码/测试/输出`、`V38–V56D0` 输出、`outputs_comparison`/`workspace`/`AGENT_PROJECT_MEMORY.md`/`docs/decision-log.md` 以外；不创建正式 TEST `run_01`；不 import 任何 `v50/v51/v52/v53/v54/v55` 模块作生产解码；**零 decoder、零码参数**
- **不产生**：新 authoritative registry、新校准 blocks、新矩阵、新泄漏公式——以上需 Path 判定后的 successor change；本诊断仅补 A2 actual 证据

## Acceptance Criteria

- [ ] `proposal.md / design.md / tasks.md` 齐全一致，lifecycle 为 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`，HEAD 绑定 `4914b56d8d353e7445a621fb142f340c37245f12` + branch `formal-ir-mainline` + data SHA `84d62779` (200ps legacy_v1) 已记录，显式声明 decoder-free、零 decoder、禁重跑原 90、禁调 H1/Lane C/Δ8/decoder
- [ ] **Raw channel 校验**可复现：从三个原始 TTBin 读取 `channel` 分布，报告每源 `count_A(1)/count_B(5)/other_channels` 及占比，校验 `A1/B5` 声明 `PASS/MISMATCH/INCOMPLETE`，`delay_sign` 与 `peak_center` 一致性
- [ ] **Timestamp cross-correlation 重算**可复现：每源 `bin_width 100ps / max_lag 819200ps / 16384 bins` 直方图已重算，输出 `peak_center_ps、peak_width_ps (σ/FWHM)、peak_count、peak_to_bg、delay_sign、total_pairs_in_window`，并与 V13 实际 `peak_center -50/+50`、`peak_sigma 74/88/103ps`、`peak_to_bg 3300-3800`、`corr_argmax 8191/8192` 实时读值对比（不硬编码，仅读 sidecar 时比对）
- [ ] **契约审计**可复现：逐项对比 `nearest_threshold_ps / pairing_direction / frame_start_ps / bin_origin / wrap_rule / gate_width_ps / delay_used_ps / peak_center` 等 `PASS/MISMATCH/INCOMPLETE` 矩阵已生成（V13 从 sidecar/manifest 实时读，不硬编码 `delay -50/+50`），明确指出 V55 sidecar 缺失的关键字段及 raw 实测对比结论，写入 `REPORT.md §2-3` 且与 `diagnosis_raw_a2.json` 一致
- [ ] **逐源 A2 判定**可复现：每源 `PATH_A2_RAW_CONTRACT_ERROR / PATH_B_DOMAIN_SHIFT / INCONCLUSIVE` 已按 raw 证据判定，总体四态 `PATH_A2_ALL / PATH_B_ALL / MIXED_BY_SOURCE / INCONCLUSIVE` 互斥给出，判定依据与前述 raw peak/channel/contract 证据链闭合，报告含对应**修复建议**（0重叠 calibration 验证）或**重估清单**（`H(U1|B), H(U2|U1,B), m_total/f`），且含原 90 已揭盲不可复用硬约束
- [ ] **禁止项**已冻结：报告与 tasks 显式禁止“原 90 块 corrected 重跑”“调 H1/Lane C/Δ8/decoder 90/1.0”“宣称 LDPC 证伪”，并要求校准帧验证后再冻新 blocks；**零 decoder、零码参数**（`rg "decode_" 0 hits`、`rg "import.*decoder" 0 hits`）
- [ ] `diagnosis_raw_a2.py` 为 decoder-free 可运行脚本（`python diagnosis_raw_a2.py [--ttbin-root ...] [--out ...] [--recompute-corr]`），`rg "decode_" 0 hits`、`rg "import.*decoder" 0 hits`，仅依赖 `numpy/pandas/pyarrow/TimeTagger(optional)`，输出 `diagnosis_raw_a2.json` 与控制台摘要，TTBin 不可用时降级 `INCOMPLETE_TTBin_UNAVAILABLE` 不伪造 peak
- [ ] `REPORT.md` 已记录每源 peak/channel/契约审计、分流结论（A2/B），数据与 `diagnosis_raw_a2.json` 一致，结论不扩大为 FER/阈值/SKR/晋升
- [ ] 已推送并停留在 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`，未创建任何 `.../v56d1_*/run_01` 或新 registry，等待 successor

## Tasks

见 `tasks.md`（Phase A raw channel/peak 重算；Phase B 契约字段审计 vs V13 实时读；Phase C 逐源 A2 判定与总体四态；Phase D 修复/重估建议与校准优先；Phase E 诊断脚本与报告交付至 DIAGNOSIS_PLAN_READY；显式禁止清单与 decoder-free 守卫）。

## Lifecycle

V56D0 当前 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`（HEAD `4914b56d8...`, branch `formal-ir-mainline`, data SHA `84d62779` 200ps legacy_v1，三源 `INCONCLUSIVE_METADATA_INCOMPLETE` — 缺 raw 契约字段）；V56D1 本诊断 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`（仅补 raw TTBin actual 证据的重算与审计，不实现 runner，不执行 decoder，不创建 run_01）；诊断结论 `PATH_A2` 或 `PATH_B` 后，**校准帧验证**与**新 blocks 冻结**需另起 successor OpenSpec（独立授权），本诊断不直接进入 qualification。
