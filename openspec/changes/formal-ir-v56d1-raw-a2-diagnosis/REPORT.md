# V56D1 Raw-A2 TTBin Diagnosis — V55 0/90 A2 Root Cause (Decoder-Free)

**HEAD**: `4914b56d8d353e7445a621fb142f340c37245f12` (branch `formal-ir-mainline`, 2026-08-29, V56 `DIAGNOSIS_PLAN_READY` 固化后)  
**Data SHA**: `84d62779603e62de50ded5182ed65b65d3dc6084` (`84d62779`, `d=1024 bw=200ps pairing=nearest rule=legacy_v1`, 单点)  
**Registry**: `v55_authoritative_registry.json` (30/source 共90, `F 2130/5125/5513`, `K 2127/5122/5510`, `gap≥4`, 已揭盲 `0/90`)  
**Lifecycle**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — **全程 decoder-free，零 `decode_*` 调用，零码参数，不改方法，不重跑原 90**  
**Predecessor**: `formal-ir-v56-input-domain-diagnosis` (V56D0, `INCONCLUSIVE_METADATA_INCOMPLETE`, A1 已排除 `k*=0 Δrate=0`) → V56D1 唯一后继补 A2 actual raw 证据  
**Date**: 2026-08-29 (待回填实测)  
**Tool**: `diagnosis_raw_a2.py` (decoder-free) → `diagnosis_raw_a2.json`

> **核心结论（待回填，执行后固化）**：本诊断从三个原始 TTBin 重读 `channel IDs` 与 `timestamp cross-correlation` 实测 `peak_center / σ / p2bg / delay_sign`，与 V13 实际 sidecar 实时读值对比，逐源判定 `PATH_A2_RAW_CONTRACT_ERROR`（明确契约错误，可修复，0重叠 calibration 验证）或 `PATH_B_DOMAIN_SHIFT`（完整正确但 `A==B 27-41%` 仍低，需重估 `H(U1|B), H(U2|U1,B)` 与 `m1/m2/f`）。**禁止在原 90 块上重跑 corrected pipeline**，**零 decoder、零码参数**。

---

## 1. 触发与边界

- **V54 基线**：`H1-16 (80-bit) + L1-APP via H1 BP + Lane C m2 184/190/192 + H_inc1/2 Δ8+8 + decoder 90/1.0 poly37 + L2-only tag + TRAIN prior` 于 held-out `45块` 上 `18 base → 38 stage1 → 43/45 final`，证明方法在 `2026-01-21` 域可行。
- **V55 观测**：同方法同点 `1024/200/nearest/legacy_v1` 于新 intake `90块` 上 `0/90 exact_full`，`A==B 76%→27-41%`，`U1/U2` 同步跌落。
- **V56D0 已证**：parquet 层 `A1 = b'=(b+k)%1024` 已排除（三源 `k*=0 Δrate=0 NLL*=NLL0 single_peak false`），但 V55 sidecar 缺 `delay_used/peak_center/σ/corr_argmax/frame_start/mapping/pairing_threshold` 等 10+ 字段 → `INCONCLUSIVE_METADATA_INCOMPLETE`，**A2 需 actual raw peak 证据**。
- **V56D1 诊断边界**：仅只读 raw TTBin + sidecar/manifest 实时读，重算 `lag = t_B - t_A` 直方图（`100ps / 819200ps / 16384 bins` 与 V13 一致），不调 `H1/Lane C/Δ8/decoder`，不宣称 LDPC 证伪/阈值/SKR/晋升。

---

## 2. Raw Channel 校验与 Cross-Correlation 重算（decoder-free，读原始 TTBin）

**输入 TTBin（与 V55 intake 完全一致，provenance 实时读）**：
- `20260123_1M_600k_0dB` (`F2130`): `D:\Data\Raw Data\2026.1.23\Type2_1M_600k_3s_0dB_2026-01-23_174534.ttbin` (+ `.1.ttbin` `d478322...`)
- `20260107_PPLN_1p5M` (`F5125`): `D:\Data\Raw Data\2026.1.7\Type2PPLN_1500K_3s_2026-01-07_174222.ttbin` (+ `.1.ttbin` `576a299...`)
- `20260123_2M_1p2M_0dB` (`F5513`): `D:\Data\Raw Data\2026.1.23\Type2_2M_1.2M_3s_0dB_2026-01-23_175008.ttbin` (+ `.1.ttbin` `e007963...`)
- 亦可由 `comparison_bench/outputs_comparison/v55_intake_20260828/intake_report.json:provenance[].path+sha256` 实时解析，不硬编码 hash，仅作绑定校验。

**方法**：`read_ttbin_events(main_ttbin)` → `channel` 直方图 + `compute_cross_correlation_histogram(ch_a=1,ch_b=5,bin_width 100,max_lag 819200, lag=t_B-t_A)` → `peak_center = lag_center[argmax]`、`peak_count`、`FWHM→σ`、`p2bg = peak_count / bg_median(|lag-peak|>5σ)`、`delay_sign = sign(peak_center)`、`total_pairs_in_window`。若 `TimeTagger` 不可用则 `INCOMPLETE_TTBin_UNAVAILABLE` 降级，不伪造峰。

> **待回填表**：`python diagnosis_raw_a2.py --recompute-corr --out diagnosis_raw_a2.json` 后回填（或降级 `INCOMPLETE`）。

| 源 | `channel` 真实分布 (`count_A1 / count_B5 / other / frac`) | `unique_channels` | `peak_center_ps` | `σ_ps (FWHM)` | `peak_count` | `p2bg` | `delay_sign` | `total_pairs_in_window` | 声明校验 |
|---|---|---|---|---|---|---|---|---|---|
| **1M** (`20260123_1M_600k_0dB`) | `count_A= — / count_B= — / other= — / frac_A — / frac_B —` | `—` | `—` | `—` | `—` | `—` | `—` | `—` | `PASS/MISMATCH/INCOMPLETE` vs 声明 `{A:1,B:5}` |
| **1p5M** (`20260107_PPLN_1p5M`) | `—` | `—` | `—` | `—` | `—` | `—` | `—` | `—` | `—` |
| **2M** (`20260123_2M_1p2M_0dB`) | `—` | `—` | `—` | `—` | `—` | `—` | `—` | `—` | `—` |

**V13 实时读对照**（不硬编码，仅读 `workspace/v13r3fresh_20260816/sidecars/*/sidecar_meta.json:used_params` 实际值）：
- `type2_1M_20260121_184040`: `delay_used -50ps / peak_center -50ps / σ 74.68ps / corr_argmax 8191 / corr_bins 16384 / p2bg 3808.6 / threshold 40000ps / gate 200ps` (实时读)
- `type2_1p5M_20260121_183806`: `delay +50 / peak +50 / σ 87.97 / argmax 8192 / p2bg 3366.1 / threshold 40000` (实时读)
- `type2_2M_20260121_183657`: `delay +50 / peak +50 / σ 103.11 / argmax 8192 / p2bg 3699.4 / threshold 40000` (实时读)
- `frame_period 204800ps / wrap_rule floor_div / pairing nearest` (实时读)

*注：上表 V13 数值在报告中仅作“实时读示例”，脚本实际以文件读取为准，不硬编码判定阈。*

**健康参考（非门禁）**：`p2bg >1000` 且 `σ 50-150ps` 且 `peak_count` 显著高于 `bg_median*1000` 视为 HEALTHY（V13 实测 `3300-3800`）；`p2bg<10` 或 `σ>150ps` 弥散或无单峰视为 `peak_missing`。

*执行命令*：`python openspec/changes/formal-ir-v56d1-raw-a2-diagnosis/diagnosis_raw_a2.py --intake-report comparison_bench/outputs_comparison/v55_intake_20260828/intake_report.json --out diagnosis_raw_a2.json`（`rg "decode_" 0 hits` 可验）

---

## 3. 契约字段审计：V13 实时读 vs V55 raw 实测 + 声明（`PASS / MISMATCH / INCOMPLETE`）

**输入（实际读取，不硬编码）**：
- V13: 直接读取 `workspace/v13r3fresh_20260816/sidecars/*/sidecar_meta.json` 的 `used_params` 与 `build_manifest.json:processing/pairing_mode/processing_rule_version`；缺失如实 `INCOMPLETE`
- V55: 直接读取 `comparison_bench/outputs_comparison/v55_intake_20260828/sidecars/*/sidecar_meta.json` 的 `materialize_params/used_params` + `intake_report.json:provenance` + `v55_authoritative_registry.json`；缺失如实 `INCOMPLETE`；并与 §2 raw 实测 `peak_center/σ/p2bg` 比对（`|peak_center - delay_used|<50ps` 则 PASS）

| 维度 | V13 实际 sidecar 实时读 | V55 raw 实测重算 + sidecar 声明 | 结论（按实际文件 + raw 实测） |
|---|---|---|---|
| acquisition date / `.ttbin`+`.1.ttbin` | `build_manifest.json:sources[].main_ttbin/chunk_ttbin` sha256/size 实时读 | `intake_report.json:provenance[]` 双文件 sha256/size 实时读 + `read_ttbin_events:total_events` | `PASS` 或 `INCOMPLETE` 按实际 |
| channels A/B 真实分布 | 读 `used_params.channels` 或隐式 `A1/B5`（若 INCOMPLETE） | **raw 实测** `channel_hist` `count_A1/count_B5/other` 占比 + 声明 `channels {A:1,B:5}` | `PASS` 如 raw `1/5` 主导且声明一致，否则 `MISMATCH` |
| `delay_used_ps` / `peak_center_ps` | 读 `used_params.delay_used_ps / peak_center_ps` 实际值 | **raw 实测** `peak_center_ps` vs 声明 `delay_used_ps`（V55 侧缺则 INCOMPLETE） | `PASS` 如 `|peak-delay|<50ps`，否则 `MISMATCH` |
| `peak_sigma_ps` / width | 读 `used_params.peak_sigma_ps` 实际 `74/88/103ps` | **raw 实测** `σ ≈FWHM/2.355` | `PASS` 如 `50-150ps` 同量级，否则弥散 `MISMATCH` |
| `peak_to_bg` | 读 `used_params.peak_to_bg` `3300-3800` | **raw 实测** `p2bg` | `PASS` 如 `>1000` |
| `corr_argmax / corr_bins` | 读 `used_params.corr_argmax 8191/8192 / corr_bins 16384` | **raw 实测** `argmax = peak_idx` / `n_bins 16384` | `PASS` 如中心附近 |
| `delay_sign` | 由 `delay_used_ps` 符号 | **raw 实测** `sign(peak_center)` `t_B-t_A` | `PASS` 如符号一致 |
| `nearest_threshold_ps` | 读 `nearest_threshold_ps 40000` | 声明 `pairing_threshold_ps`（V55 缺则 INCOMPLETE）+ raw 间隔统计 | `PASS` 或 `INCOMPLETE/MISMATCH` |
| `pairing_direction / pairing_mode` | 读 `pairing_mode nearest` + `pairing_mode_requested` | `pairing_mode nearest` + `nearest_unique greedy` 方向（`t_B-t_A`） | `PASS` 或 `INCOMPLETE` |
| `frame_start_ps / bin origin / wrap_rule` | 读 `frame_start_ps / frame_anchor / wrap_rule floor_div` / `frame_period 204800` | 声明 `frame_start_ps / frame_anchor / wrap_rule`（V55 缺则 INCOMPLETE） | `PASS` 或 `INCOMPLETE` |
| `gate_width_ps / coinc_window` | 读 `gate_width_ps 200` | 声明 `gate_width_ps / coinc_window_ps` | `PASS` 或 `INCOMPLETE` |
| `occupancy_filter` | 读 `occupancy_filter` | 声明 `occupancy_filter` | `PASS` 或 `INCOMPLETE` |

**审计结论**（待回填）：按实际 sidecars 读取 + raw 实测，缺 `delay_used/peak_center/frame_start/mapping/pairing_threshold` 等字段时仅记 `INCONCLUSIVE_METADATA_INCOMPLETE`，不自动判 `PATH_A2`；需 actual raw peak 证据才可判 `A2`；若 raw 峰健康但 `A==B 27-41%` 仍低则判 `PATH_B`。

*注：V55 `intake_report.json` 与 `v55_authoritative_registry.json` 的实际字段以文件为准，缺失如实 `INCOMPLETE`。TimeTagger 不可用时 `INCOMPLETE_TTBin_UNAVAILABLE`。*

---

## 4. 逐源 A2 判定与总体四态（A2 专用，四态互斥，待回填）

**域拆分**：`A2 = raw TTBin delay/peak/pairing contract`（需 actual raw peak/delay/channel 证据），`B = 排除 A2 后物理域迁移`；`A1` 已由 V56D0 排除（`k*=0`），本诊断不再判 A1。`B` 为排除 A2 后物理域迁移。

**判定逻辑**（见 design §3，逐源，阈启发仅证据描述，非门禁）：

- `peak_missing (p2bg<10 / no clear peak) || |peak_center - delay_used|>50ps (when delay known) || σ>150ps broad || channel_mismatch (A/B<40% or other>20%) || threshold MISMATCH || pairing reversed || frame_start offset` 且 raw 证据确凿 → `PATH_A2_RAW_CONTRACT_ERROR`（可修复，0重叠 calibration 验证）
- `peak_healthy (|peak-delay|<50ps && p2bg>1000 && σ 50-150ps) && still_low (A==B<45% && NLL>>1.0)` → `PATH_B_DOMAIN_SHIFT`（raw 正确但相关率仍低，需重估熵/泄漏）
- `TimeTagger missing / file missing` → `INCONCLUSIVE_NEED_CALIBRATION` (`INCOMPLETE_TTBin_UNAVAILABLE`)
- 缺 metadata 无 actual 证据 → `INCONCLUSIVE_METADATA_INCOMPLETE`

**总体四态**：`PATH_A2_ALL`（全 A2） / `PATH_B_ALL`（全 B） / `MIXED_BY_SOURCE`（源间不一致） / `INCONCLUSIVE`（含 `INCOMPLETE_TTBin_UNAVAILABLE`）

> **待回填**：执行 `diagnosis_raw_a2.py` 后回填 `diagnosis_raw_a2.json: per_source_decisions / overall_shunt / shunt_evidence` 为权威结论。

| 源 | raw `peak_center/σ/p2bg/delay_sign` | Channel 校验 | 契约 `PASS/MISMATCH/INCOMPLETE` 关键项 | Parquet 背景 `A==B` | 逐源判定 | 含义 |
|---|---|---|---|---|---|---|
| 1M | `center — / σ — / p2bg — / sign —` | `A1/B5 —` | `delay — / threshold — / frame_start —` | `—` (V56D0 `41.49%`) | `待回填 PATH_A2 / PATH_B / INCONCLUSIVE` | — |
| 1p5M | `—` | `—` | `—` | `—` (`37.55%`) | `待回填` | — |
| 2M | `—` | `—` | `—` | `—` (`27.49%`) | `待回填` | — |
| **总体** | — | — | — | `avg —` | `待回填 PATH_A2_ALL / PATH_B_ALL / MIXED / INCONCLUSIVE` | — |

**无论 Path A2/B，均禁止在原 V55 authoritative 90-block 上重跑任何 corrected pipeline**（已揭盲，`base→Δ8→Δ16` 任一变体均禁，含 `peak-corrected` 重译）；**禁止调 `H1/Lane C/Δ8/decoder 90/1.0`**；**不得宣称 LDPC 证伪**。

#### 若 PATH_A2 — 修复建议（materialization contract, 可修复后 0 重叠 calibration 验证）

1. **Sidecar 必填字段**：`channels {A,B}`, `delay_used_ps`, `delay_override_ps`, `peak_center_ps`, `peak_sigma_ps`, `corr_argmax`, `frame_start_ps`, `frame_anchor`, `bin_origin_ps`, `mapping`, `wrap_rule`, `pairing_mode`, `nearest_threshold_ps`, `gate_width_ps`, `occupancy_filter` 全部显式落盘，缺一则 `DATA_NOT_READY`。
2. **FileReader 显式绑定**：`_read_ttbin_timetags(raw_ch0_id=1, raw_ch1_id=5)` + `_bin_indices_sorted_for_binwidth(200)` + `_pairs_from_sorted_bins(1024, nearest, threshold=40000)` 参数显式化，`relative_delay_ps` 与 `frame_start_override_ps` 必须与 `peak_center` 绑定校验 (`|delay_used - peak_center|<50ps`)。
3. **Per-source 校验门**：新增 `G1' peak_status==ok && peak_to_bg>1000`, `G2' |delay_used - peak_center|<50ps && σ 50-150ps`, `G3' channel frac_A/B>40% other<20%`，失败则拒绝进入 registry。
4. **已揭盲保护**：原 V55 90-block 已揭盲（`0/90` 已观测），**禁止**在其上应用修复后重跑；修复后需**另采/另冻新 calibration + 新 TEST blocks**（与原 90 零重叠，`frame_ids` 零重叠可机械校验，**0重叠 calibration frames 8-16 frames 小批量** 验证 `A==B>60%` 且 `p2bg>1000` 健康后，再冻新 blocks）。

#### 若 PATH_B — 重估清单（物理域迁移，完整正确但相关率仍低）

1. 用新 session 全量 intake 重算 `N_ab → H(A|B) → F03 H(U1|B), H(U2|U1,B)` (`layer_conditional_entropy_bits`，`nbldpc_v25_gate.py` 定义)，报告 per-source `H` 与 V13 差值（V13 `≈0.80 bits/symbol` 基线）。
2. 重算 `m_total = floor((1.3*1024*H_source -64)/5)` 与 `m1_ep = round(m_total*H1/H_total)` 的 source-adaptive 预算，评估当前 `m2/leak` 的 `f` 缺口（若 `H` 从 `0.80` 升至 `>1.2`，`f` 将 `>>1.3`）。
3. 若 `H` 显著升高，需重新设计 `H1` 冗余或 `Lane C` 码族，而非仅增 `Δ8`。
4. 同样需**独立 calibration frames** 先验（0重叠），再冻新 blocks（与原 90 零重叠）。

---

## 5. 校准优先的下一步（Calibration-first，硬约束，待回填）

- **Calibration frames 定义**：与 V55 authoritative 90-block **零重叠**、未揭盲、每源建议 `8-16` 连续 frames（`2-4` blocks）的小批量，仅用于验证基础相关性，不进入正式 TEST 统计。
- **健康参考**（诊断描述，非门禁）：`A==B>60%` 且 `U1/U2>55%` 且 `Bob-conditioned NLL<1.0 bits/symbol` 且 `raw p2bg>1000 && σ 50-150ps` 视为信道健康；低于则继续诊断，不直接调码。
- **冻结新 blocks 条件**：仅当 calibration 健康且 sidecar 契约补齐（Path A2）或熵重估完成（Path B）后，才允许另起 OpenSpec 冻结新 TEST registry（与原 90 零重叠、与 calibration 零重叠），并走独立 `QUALIFICATION_PLAN_READY` 流程。
- **本诊断不直接冻结**新 registry/blocks/correction；successor 需独立授权；**若发现明确契约错误则可修复后用 0 重叠 calibration frames 验证**，若完整正确而相关率仍低则判 Path B。

---

## 6. 禁止项（硬约束，重申）

- `SHALL NOT` 运行任何 `L1-APP / L2` decoder（`decode_row_layered_fftqspa` 等零调用，`rg "decode_" 0 hits` 可验）；**零 decoder、零码参数**
- `SHALL NOT` 在原 V55 authoritative 90-block (`v55_authoritative_registry.json` 30/source) 上重跑任何 corrected pipeline（含 `peak-corrected` 重译）
- `SHALL NOT` 调 `H1/Lane C/Δ8/decoder 90/1.0/m2/leak/prior` 任一冻结参数以拟合 V55
- `SHALL NOT` 宣称 LDPC/NB-LDPC 证伪 / FER / 阈值 / SKR / 晋升；`0/90` 仅为域失配信号
- `SHALL NOT` 创建正式 `.../v56d1_*/run_01` 或新 registry（本诊断仅只读）；`SHALL` 先用独立 calibration 验证后才能另冻新 blocks

---

## 7. 复现与 Provenance（待回填）

- **脚本**：`openspec/changes/formal-ir-v56d1-raw-a2-diagnosis/diagnosis_raw_a2.py`
  - 输入：`--intake-report` (默认 `v55_intake_20260828/intake_report.json:provenance`) + `--v13-sidecar-root` (默认 `workspace/v13r3fresh_20260816/sidecars`) + `--counts` (`channel_counts.npz` 仅背景) + `--out` (`diagnosis_raw_a2.json`)
  - 输出：`diagnosis_raw_a2.json` (含 `head/branch/data_sha/metadata_audit/per_source/shunt_evidence/overall_shunt`) + 控制台摘要
  - 守卫：仅 `numpy/pandas/pyarrow + ttbin_pipeline(TimeTagger optional)`，`rg "decode_" 0 hits`，`py_compile` PASS；TTBin 不可用时 `INCOMPLETE_TTBin_UNAVAILABLE` 不伪造
- **输入 SHAs**：V55 三源 `.ttbin/.1.ttbin` hash 见 `intake_report.json:provenance[].sha256`（`ee79c5b.../5e6fcb8.../e8c6f67...`）实时读；V13 三源 hash 见 `build_manifest.json:sources[].main_ttbin/chunk_ttbin.sha256` 实时读；`channel_hist` 由 raw `channel` 直方图实测
- **输出**：`diagnosis_raw_a2.json` (machine-readable) + 本报告 (human-readable)，数据一致；不写 `run_01`

---

## 8. 结论（待回填，执行后固化为权威）

- **状态**：`DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — 脚本待执行，`REPORT.md` 待填充 `diagnosis_raw_a2.json: shunt_evidence / per_source_decisions / overall_shunt` 为权威结论；`rg "decode_" 0 hits` 可验；未运行 decoder，未宣称 LDPC 证伪。
- **分流占位**：
  - 若 `PATH_A2_RAW_CONTRACT_ERROR`（某源 `|peak-delay|>50ps` 或 `p2bg<10` 或 `channel_mismatch` 等 explicit）→ `PATH_A2_ALL` 或 `MIXED_BY_SOURCE`，输出 contract 修复 + **0重叠 calibration 验证**后另冻新 blocks，原 90 禁止重跑。
  - 若 `PATH_B_DOMAIN_SHIFT`（三源 peak 健康 `p2bg>1000 σ 50-150ps |peak-delay|<50ps` 但 `A==B 27-41%` 仍低）→ `PATH_B_ALL`，需重估 `H(U1|B), H(U2|U1,B), m_total/f`，同样校准优先。
  - 否则 `INCONCLUSIVE`（含 `INCOMPLETE_TTBin_UNAVAILABLE`）→ 补 TimeTagger/raw 后再判，不自动判 A2/B。
- **Claim 边界**：本诊断仅为 `decoder-free` raw-A2 根因诊断，不产生 `FER/阈值/SKR/资格/晋升` 证据；`V54` 二阶段在 `2026-01-21` 域上的 `43/45` 仍为有效开发确认，`V55 0/90` 不推翻，需 calibration 后再定。

---

*本报告由 `diagnosis_raw_a2.py` (decoder-free) 生成，需与 `diagnosis_raw_a2.json` 数值一致；`rg "decode_" 0 hits` 可验；未运行 decoder，未宣称 LDPC 证伪；`lag = t_B - t_A` 显式，`TimeTagger` 不可用时 `INCOMPLETE_TTBin_UNAVAILABLE`。*
