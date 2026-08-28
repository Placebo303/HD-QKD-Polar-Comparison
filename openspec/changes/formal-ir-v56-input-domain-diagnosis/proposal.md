# OpenSpec Proposal: formal-ir-v56-input-domain-diagnosis

**Status**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — **decoder-free 根因诊断，不运行 L1/L2 decoder，不改方法，不重跑原 90 块。**
**Domain**: Formal IR / V55R1-V56 decoder-free 输入域失配根因诊断
**Change ID**: `formal-ir-v56-input-domain-diagnosis`
**Cycle ID**: `V56D0` (diagnosis), predecessor `V55P0` two-stage rescue independent TEST
**Predecessor**: `formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation` (authoritative 90-block, branch `formal-ir-mainline`, plan SHA `3d7c63eefe655c9f25d199af3f7f4ea311ac454b`, data SHA `84d62779603e62de50ded5182ed65b65d3dc6084` legacy_v1 200ps, implementation HEAD `cf8b098047cf64aa1e0426e2ea2e62b680430bd6`)
**Branch**: `formal-ir-mainline`
**HEAD**: `cf8b098047cf64aa1e0426e2ea2e62b680430bd6` (2026-08-29, V55 `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED` 固化后最新)
**Lifecycle**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — 仅只读核对与统计对比，不产生 `run_01`，不产生新 TEST blocks
**Method frozen**: `V54二阶段 H1-16(80-bit) + L1-APP via H1 BP + Lane C m2 184/190/192 + H_inc1/2 Δ8+8 + decoder 90/1.0 poly37 + L2-only tag` 完全冻结，诊断期间禁止调任一参数

> ponytail lite: 本变更仅 5 文件 (`proposal/design/tasks` + `diagnosis_v55_domain.py` + `DIAGNOSIS_REPORT.md`) + 只读 parquet/sidecar 审计；无 runner、无 decoder、无新 registry、无新矩阵，最简闭环。

## Goal

V55 在 authoritative 90-block 上出现 `0/90 exact_full`（V54 held-out 曾 `43/45`）且 `27-41%` 相关率远低于 V13 的 `76%`，本诊断**唯一目标**是以 **decoder-free 只读手段**判定该信号是**系统性输入域失配**而非算法证伪，并给出唯一分流结论：

1. **只读核对新旧 session 元数据**（TimeTagger channels A/B、delay、bin origin、coincidence peak 位置、mapping、pairing 方向等）：逐项对比 **V13 2026-01-21** (`type2_1M_20260121_184040 / type2_1p5M_20260121_183806 / type2_2M_20260121_183657`, delay `-50/+50/+50`, `bin_width 200ps`, `legacy_v1`, `nearest`, `corr_argmax 8191`, `peak_center -50/+50`, `channels 隐式 A1/B5`) 与 **V55 三候选** (`2026.1.23 1M_600k_0dB F2130` / `2026.1.23 2M_1.2M_0dB F5513` / `2026.1.07 PPLN 1p5M F5125`, `200ps legacy_v1 nearest A1/B5` 但 sidecar 缺 `delay_used_ps/peak_center/peak_sigma/corr_argmax/frame_start/mapping` 等字段)，以 intake sidecar/meta 与 `v55_authoritative_registry.json`/`build_manifest.json`/`data_inventory.json` 为权威输入，记录每项 `PASS/INCOMPLETE/MISMATCH`。

 2. **逐源统计对比**（decoder-free，仅读 parquet/sidecar）：
   - `A==B 率` (raw SER `1 - A==B`)、**U1/U2 一致率**（已观测 `76% → 27-41%`）、**Bob-conditioned NLL** (基于 V25 `channel_counts.npz` TRAIN prior 的 `E[-log2 P(A|B)]`，单位 bits/symbol 与 bits/block 双报)、**边缘分布** (`P(A), P(B)` 直方图)、**零/罕见 bins** (joint `N_ab=0` 占比与 `P>0` mass 落于零格的 `q_mass_on_p_zero`)、**frame 级相关率** (per-frame `A==B` 分布与 `±1` 邻bin质量)；
   - 允许**固定相对 offset 扫描仅作 A1 诊断**（`b'=(b+k)%1024` 仅为 parquet symbol/mapping shift (A1)，与 raw TTBin delay/peak/pairing contract (A2) 分离；直接由 1024-bin `delta=(a-b) mod 1024` histogram 得全 k 的 `rate_eq(k)`，仅对 `k=0` 与主峰 `k*` 算 NLL，并注明不等价 raw time-delay 扫描）：报告每 `k` 的 `A==B+k` 率与 NLL 曲线（仅 `k=0/k*` 有 NLL），**不择优、不重跑资格、不用于修正原 90 块**，仅作为 `A1` 假设的证据。

 3. **逐源分流与总体终态**（A1/A2/B 拆分，逐源判定，总体四态互斥）：
    - **逐源**：`PATH_A1_PARQUET_SYMBOL_SHIFT` (A1, offset 单峰) / `INCONCLUSIVE_METADATA_INCOMPLETE` (缺 metadata 仅 INCONCLUSIVE，需 actual raw 证据才可判 A2) / `PATH_B_DOMAIN_SHIFT` (排除 A1/A2 后物理域迁移) / `INCONCLUSIVE`。
    - **总体**：至少 `PATH_A_ALL / PATH_B_ALL / MIXED_BY_SOURCE / INCONCLUSIVE`（含 `INCONCLUSIVE_METADATA_INCOMPLETE` 子态），非单一 Path A/B；`Path A` 细分 `A1` (parquet shift) 与 `A2` (raw delay/peak/pairing, 需 actual 证据)；`Path B` 为排除 `A1/A2` 后物理域迁移。
    - **Path A1 — parquet shift**：若某源 offset 出现单峰显著回升（`k*≠0` 且 `>60%` 且 NLL 回落至 `~0.8 bits/symbol`），判该源 `A1`，需修复 `mapping/bin_origin` 契约。
    - **A2 — raw contract**：缺 metadata 本身仅 `INCONCLUSIVE_METADATA_INCOMPLETE`，不能自动判 `A2`，需 `actual raw peak/delay/channel` 证据。
    - **Path B — 域迁移**：排除 `A1/A2` 后仍 `27-45%` 且 NLL `>>1.5`，则该源 `B`，需重估 `H(U1|B), H(U2|U1,B)` 与 `m1/m2/f`。

4. **禁止项**（硬约束）：禁止在原 90 块上重跑任何 corrected pipeline（已揭盲，`base→Δ8→Δ16` 任何变体均禁）；禁止调 `H1/Lane C/Δ8/decoder 90/1.0` 任一参数以拟合 V55；必须先用**独立 calibration frames**（与原 90 零重叠、未揭盲的新块）验证基础相关性后，才能另冻新 blocks 进入 qualification。

## Non-Goals

- 不运行任何 `L1-APP / L2` decoder（`decode_row_layered_fftqspa` 等零调用）；不改 `H1-16/Lane C/H_inc1/H_inc2/m2/leak/tag/prior` 任一冻结量；不试新 `Δm/degree/seed`。
- 不在原 V55 authoritative 90-block (`v55_authoritative_registry.json` 30/source) 上重跑任何 corrected pipeline / offset-corrected 重译；不将 offset 扫描择优值回注为新 pipeline。
- 不宣称 LDPC 证伪 / FER 结论 / 阈值 / SKR / 晋升；不将 `0/90` 记为算法失败证据。
- 不做 `FER/阈值/SKR/安全/资格/晋升` 的扩大陈述；tag 仍 L2-only `≈2^-64` 工程近似仅作记账背景，不作诊断门禁。
- 不改写/覆盖 `V38–V55` 任何已有输出与终态（只读）；本诊断不修改 `AGENT_PROJECT_MEMORY.md / docs/decision-log.md`（仅预留 V56 条目占位）。
- 不创建正式 `.../v56_*/run_01` / 新 authoritative registry / 新校准 blocks（校准块冻结需另起 OpenSpec，待 Path A/B 判定后）。
- 不做多 `bin_width / dimension / pairing` 网格搜索；`200ps legacy_v1 nearest 1024` 单点为诊断锚点。

## Scope

1. **冻结方法（零改）**：`n=1024, m2 184/190/192, GF32 poly37, H1-16 rank16 80b, L1-APP q via H1 BP (TRAIN `channel_counts.npz`), Lane C ordinal-2, H_inc1/2 Δ8+8, decoder 90/1.0 early-stop, L2-only tag 64b, TRAIN-only prior, verification-only, leak 1064/1094/1104 +40+40`, `90块 180-360 calls` 预算——诊断期间以上全部只读。

2. **元数据只读审计**（decoder-free）：
   - 输入：`V13` 侧 `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/build_manifest.json` + `workspace/v13r3fresh_20260816/sidecars/*/sidecar_meta.json` (含 `delay_used_ps -50/+50`, `peak_center -50/+50`, `peak_sigma 74ps`, `corr_argmax 8191`, `frame_period 204800`, `mapping/wrap_rule`, `occupancy_filter`, `delta_hist` 等) + `nbldpc_v25_20260818/run_04/data_inventory.json/channel_summary.json`；
   - 对比：`V55` 侧 `comparison_bench/outputs_comparison/v55_intake_20260828/intake_report.json` + `sidecars/*/sidecar_meta.json` (仅 `dimension/bin_width/pairing/legacy_v1/channels A1/B5`) + `v55_authoritative_registry.json` + `pairs.parquet` 结构统计；
   - 输出：逐字段 `PASS/MISMATCH/INCOMPLETE` 矩阵，重点标记 `delay_used_ps / peak_center / peak_sigma / corr_argmax / frame_start_ps / mapping / pairing_window / delay_override_ps / occupancy_filter` 在 V55 侧的缺失。

3. **逐源统计对比**（decoder-free，仅 parquet + V25 counts）：
   - 每源计算 `A==B 率 / SER`, `U1==U1' 与 U2==U2' 一致率` (F03 `5+5` split via `split_label`), `Bob-conditioned NLL` (`P(A|B)` from `channel_counts.npz` column-normalized, 见 `nonbinary_v25_gate.P_A_given_B`), `边缘分布` (1024-bin 直方图), `零/罕见 bins` (`N_ab=0` 格数与 `q_mass_on_p_zero`), `frame 级相关率` (per-frame `A==B` 直方图与 `±1` 质量), `modular delta` (`(a-b) mod 1024` 直方图与 `direction_asymmetry`)；
   - 以 `V13 TRAIN` 为参考基线，输出 `V55 - V13` 差值与 `NLL` 增量（bits/symbol & bits/block）。

 4. **Offset 扫描诊断**（A1-only，仅作证据，不等价 raw time-delay）：
   - 对每源由已有 1024-bin `delta=(a-b) mod 1024` histogram 直接得全 `k` 的 `rate_eq(k)=hist[k]`（`b'=(b+k)%1024` 仅 parquet symbol/mapping shift (A1)），仅对 `k=0` 与主峰 `k*` 算 `Bob-conditioned NLL` / `delta`，其余 `k` 不算 NLL；
   - 报告 `k vs 相关率/NLL` 曲线与峰值 `k*`，**不择优重跑**，注明不等价 raw time-delay 扫描，仅用于判断 A1 单峰 vs 域迁移弥散。

 5. **逐源分流与总体终态**（四态互斥）：
   - **逐源三判定** + **总体** `PATH_A_ALL / PATH_B_ALL / MIXED_BY_SOURCE / INCONCLUSIVE`（含 `INCONCLUSIVE_METADATA_INCOMPLETE`），非单一 Path A/B；`A1` 与 `A2` (raw contract) 分离，缺 metadata 仅 `INCONCLUSIVE` 不自动判 `A`；`B` 为排除 `A1/A2` 后物理域迁移。
   - **Path A1 可修复**：某源 offset 单峰显著 ⇒ 该源 `A1`，输出 mapping 契约修复并声明原 90 已揭盲不可复用。
   - **A2 需 actual 证据**：缺 `delay/peak/mapping` 仅 `INCONCLUSIVE_METADATA_INCOMPLETE`，需 actual raw peak/delay/channel 证据才可判 `A2`。
   - **Path B 域迁移**：某源排除 `A1/A2` 后仍 `27-45%` 相关、NLL 仍高 ⇒ 该源 `B`，需重估 `H(U1|B), H(U2|U1,B)` 与 `m1/m2/f`。

6. **校准优先的下一步**（冻结原则）：无论 Path A/B，均**先用独立 calibration frames**（与原 90 零重叠、未揭盲、每源建议 `≥8-16` frames 小批量）验证基础相关性（`A==B>60%` 且 `NLL<1.0 bits/symbol` 等价量为健康阈，诊断阈非门禁），通过后再另冻新 blocks 进入 qualification；校准块冻结需新 OpenSpec 与独立执行授权。

## Impact Scope

- **新增/修订（本诊断）**：`openspec/changes/formal-ir-v56-input-domain-diagnosis/` 下 5 文件：`proposal.md / design.md / tasks.md / diagnosis_v55_domain.py (decoder-free) / DIAGNOSIS_REPORT.md`；`specs/spec.md` 可选增量（本诊断为只读分析，不改方法 spec，主 spec 保持 V55 冻结）
- **只读依赖**：`v55_authoritative_registry.json`, `v55_intake_20260828/intake_report.json + sidecars/*/sidecar_meta.json + pairs/*.parquet`, `v13r3fresh_pairs_20260816/build_manifest.json + sidecars/*/sidecar_meta.json`, `nbldpc_v25_20260818/run_04/channel_counts.npz + data_inventory.json + channel_summary.json + delta_by_source.csv`, `nonbinary_v25_gate.py` (P(A|B)/NLL/熵定义), `v38_architecture_triage.py` (Lane C 常量仅作背景，不调用 decoder)
- **不修改**：任何既有 `spec/代码/测试/输出`、`V38–V55` 输出、`outputs_comparison`/`workspace`/`AGENT_PROJECT_MEMORY.md`/`docs/decision-log.md` 以外；不创建正式 TEST `run_01`；不 import 任何 `v50/v51/v52/v53/v54/v55` 模块作生产解码
- **不产生**：新 authoritative registry、新校准 blocks、新矩阵、新泄漏公式——以上需 Path 判定后的 successor change

## Acceptance Criteria

- [ ] `proposal.md / design.md / tasks.md` 齐全一致，lifecycle 为 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`，HEAD 绑定 `cf8b098047cf64aa1e0426e2ea2e62b680430bd6` + branch `formal-ir-mainline` + data SHA `84d62779` (200ps legacy_v1) 已记录，显式声明 decoder-free、禁重跑原 90、无 LDPC 证伪
- [ ] **元数据审计**可复现：逐项对比 `V13 (2026-01-21)` vs `V55 (2026.1.23/2026.1.07)` 的 `channels A1/B5, delay_used_ps, bin_origin, frame_start_ps, peak_center, peak_sigma, corr_argmax, mapping, wrap_rule, pairing_mode/direction, occupancy_filter` 等，输出 `PASS/MISMATCH/INCOMPLETE` 矩阵，明确指出 V55 sidecar 缺失的关键字段（`delay_used_ps/peak_center/corr_argmax/frame_start/mapping` 等），结论与 `DIAGNOSIS_REPORT.md` 一致
- [ ] **逐源统计**可复现：每源 `A==B 率 / SER, U1/U2 一致率 (76%→27-41% 复现), Bob-conditioned NLL (bits/symbol & bits/block), 边缘分布, 零/罕见 bins (N_ab=0 占比与 q_mass_on_p_zero), frame 级相关率, modular delta 直方图与 direction_asymmetry` 均基于 `pairs.parquet` + `channel_counts.npz` 只读计算，零 `decode_*` 调用，报告含 `V13 vs V55` 差值与 per-source 明细
- [ ] **Offset 扫描**可复现：固定 `k∈[-8,+8]`（或 `[-16,+16]`）`b'=(b+k) mod 1024` 扫描的 `相关率/NLL/delta` 曲线已生成，峰值 `k*` 与回升幅度已记录，显式标注“仅诊断、不择优、不用于资格”
- [ ] **唯一分流判定**已给出且互斥：`Path A 可修复 materialization contract` vs `Path B 域迁移需重估熵/泄漏` 二选一，判定依据与前述元数据/统计/offset 证据链闭合，报告含对应**修复建议**或**重估清单**，且含**原 90 块已揭盲不可复用**与**需独立 calibration frames 先验**的硬约束
- [ ] **禁止项**已冻结：报告与 tasks 显式禁止“原 90 块 corrected 重跑”“调 H1/Lane C/Δ8/decoder 90/1.0”“宣称 LDPC 证伪”，并要求校准帧验证后再冻新 blocks
- [ ] `diagnosis_v55_domain.py` 为 decoder-free 可运行脚本（`python diagnosis_v55_domain.py [--pairs-root ...] [--out ...]`），`rg "decode_" 0 hits`、`rg "import.*decoder" 0 hits`，仅依赖 `numpy/pandas/pyarrow`，输出 `diagnosis_v55_domain.json` 与控制台摘要
- [ ] `DIAGNOSIS_REPORT.md` 已记录每源统计、NLL、offset 扫描结果与分流结论，数据与 `diagnosis_v55_domain.json` 一致，结论不扩大为 FER/阈值/SKR/晋升
- [ ] 已推送并停留在 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`，未创建任何 `.../v56_*/run_01` 或新 registry

## Tasks

见 `tasks.md`（Phase A 元数据只读审计；Phase B 逐源统计对比；Phase C 固定 offset 扫描诊断；Phase D 唯一分流判定与修复/重估建议；Phase E 诊断脚本与报告交付至 DIAGNOSIS_PLAN_READY；显式禁止清单与 decoder-free 守卫）。

## Lifecycle

V55 当前 `QUALIFICATION_PLAN_READY / EXECUTE_NOT_AUTHORIZED`（HEAD `cf8b098...`, branch `formal-ir-mainline`, data SHA `84d62779` 200ps legacy_v1，authoritative 90-block 已冻但 `0/90` 揭示域失配信号）；V56D0 本诊断 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`（仅只读诊断，不实现 runner，不执行 decoder，不创建 run_01）；诊断结论 `Path A` 或 `Path B` 后，**校准帧验证**与**新 blocks 冻结**需另起 successor OpenSpec（独立授权），本诊断不直接进入 qualification。
