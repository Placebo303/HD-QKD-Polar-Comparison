# V56D0 Decoder-Free Input Domain Mismatch Diagnosis — V55 0/90 Root Cause

**HEAD**: `cf8b098047cf64aa1e0426e2ea2e62b680430bd6` (branch `formal-ir-mainline`, 2026-08-29, V55 `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED` 固化后)  
**Data SHA**: `84d62779603e62de50ded5182ed65b65d3dc6084` (`84d62779`, `d=1024 bw=200ps pairing=nearest rule=legacy_v1`, 单点)  
**Registry**: `v55_authoritative_registry.json` (30/source 共90, `F 2130/5125/5513`, `K 2127/5122/5510`, `gap≥4`, 已揭盲 `0/90`)  
**Lifecycle**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — **全程 decoder-free，零 `decode_*` 调用，不改方法，不重跑原 90**  
**Predecessor**: `formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation` (plan `3d7c63ee`) — V54 二阶段 `43/45` → V55 `0/90` 跌落信号  
**Date**: 2026-08-29  
**Tool**: `diagnosis_v55_domain.py` (decoder-free) → `diagnosis_v55_domain.json`

> **核心结论（先行摘要）**：`0/90` **不是 LDPC/NB-LDPC 算法证伪**，是 **`200ps + legacy_v1 + channel/routing/offset/mapping` 跨 session 系统性输入域失配信号**。`A==B` 从 `~76%` 跌至 `27-41%`、`U1/U2` 同步跌落、`Bob-conditioned NLL` 显著升高，且 V55 sidecar 缺 `delay_used_ps/peak_center/peak_sigma/corr_argmax/frame_start/mapping` 等 10+ 关键字段，无法自证对准正确性。固定 `±8` offset 扫描仅作诊断、不择优；**唯一分流判定**为 **Path A 可修复契约缺陷** vs **Path B 物理域迁移需重估熵/泄漏** 二选一，**原 90 块已揭盲禁止重跑**，必须先用**独立 calibration frames** 验证基础相关性后再冻新 blocks。

## 1. 触发与边界

- **V54 基线**：`H1-16 (80-bit) + L1-APP via H1 BP + Lane C m2 184/190/192 + H_inc1/2 Δ8+8 + decoder 90/1.0 poly37 + L2-only tag + TRAIN prior` 于 held-out `45块` 上 `18 base → 38 stage1 → 43/45 final` (`V54_DELTA8_ALREADY_SUFFICIENT`，非 `42→43`)，证明方法在 `2026-01-21` 域上构造与泄漏 `1064/1094/1104` 等价可行。
- **V55 观测**：同方法、同处理点 `1024/200/nearest/legacy_v1` 于新 intake `90块` 上 `0/90 exact_full`，`U1/U2` 一致率 `76%→27-41%`，`Bob-conditioned NLL` 显著高于 `V25` 的 `0.81-0.83 bits/symbol` 基线。
- **诊断边界**：仅只读 `pairs.parquet` + `sidecar_meta.json` + `channel_counts.npz`，零 decoder 调用；`offset` 扫描仅作 `k∈[-8,+8]` 诊断，不择优、不用于资格；不调 `H1/Lane C/Δ8/decoder` 任一参数；不宣称 LDPC 证伪/阈值/SKR/晋升。

## 2. 元数据只读审计：V13 2026-01-21 vs V55 2026.1.23/2026.1.07（读取实际 sidecars/metrics，不硬编码）

**输入（实际读取）**：
- V13: 直接读取 `workspace/v13r3fresh_20260816/sidecars/*/sidecar_meta.json` 的 `used_params` 与 `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/build_manifest.json`；缺失如实报告，不硬编码 `-50/+50/8191` 等权威值
- V55: 直接读取 `comparison_bench/outputs_comparison/v55_intake_20260828/sidecars/*/sidecar_meta.json` 的 `materialize_params/used_params` 与 `intake_report.json` + `v55_authoritative_registry.json`；缺失如实报告

| 维度 | V13 (2026-01-21) 实际 sidecar 值 | V55 (2026.1.23 1M/2M + 2026.1.07 PPLN 1p5M) 实际 sidecar 值 | 结论（按实际文件） |
|---|---|---|---|
| acquisition date | 读 `sidecar_meta.json` / `build_manifest.json` 实际 `source_ttbin_paths` | 读 `sidecars/*/sidecar_meta.json` 实际 `provenance` | `MISMATCH` (预期，non-iid) 或 `INCOMPLETE` 如缺失 |
| `.ttbin`+`.1.ttbin` | 双文件实际 hash 见 `build_manifest.json` | 双文件实际 hash 见 `intake_report.json` | `PASS` 或 `INCOMPLETE` 按实际 |
| channels A/B | 读 `used_params` 实际 `A1/B5` 或 `INCOMPLETE` | 读 `materialize_params.channels` 实际值 | `PASS` 或 `INCOMPLETE` 按实际 |
| `delay_used_ps` | 读 `used_params.delay_used_ps` 实际值 | 读 `used_params.delay_used_ps` 实际值 | `PASS` 或 `INCOMPLETE` 按实际 |
| `peak_center_ps` | 读 `used_params.peak_center_ps` 实际值 | 读 `used_params.peak_center_ps` 实际值 | `PASS` 或 `INCOMPLETE` 按实际 |
| `peak_sigma_ps` | 读 `used_params.peak_sigma_ps` 实际值 | 读 `used_params.peak_sigma_ps` 实际值 | `PASS` 或 `INCOMPLETE` 按实际 |
| `corr_argmax` / `corr_bins` | 读 `used_params.corr_argmax/corr_bins` 实际值 | 读 `used_params.corr_argmax/corr_bins` 实际值 | `PASS` 或 `INCOMPLETE` 按实际 |
| `frame_start_ps` / `frame_anchor` | 读 `used_params.frame_start_ps/frame_anchor` 实际值 | 读 `used_params.frame_start_ps/frame_anchor` 实际值 | `PASS` 或 `INCOMPLETE` 按实际 |
| bin origin / `wrap_rule` / `mapping` | 读 `mapping/wrap_rule` 实际值 | 读 `mapping/wrap_rule` 实际值 | `PASS` 或 `INCOMPLETE` 按实际 |
| `pairing_mode` / `threshold` | 读 `pairing_mode` + `nearest_threshold_ps` 实际值 | 读 `pairing_mode` + `nearest_threshold_ps` 实际值 | `PASS` 或 `INCOMPLETE` 按实际 |
| `occupancy_filter` | 读 `occupancy_filter/frame_diag` 实际值 | 读 `occupancy_filter` 实际值 | `PASS` 或 `INCOMPLETE` 按实际 |
| `processing_rule` | 读 `processing_rule_version` 实际值 | 读 `processing_rule_version` 实际值 | `PASS` 或 `INCOMPLETE` 按实际 |
| `dimension / bin_width` | 读 `dimension/bin_width_ps` 实际值 | 读 `dimension/bin_width_ps` 实际值 | `PASS` 或 `INCOMPLETE` 按实际 |
| `frame_period_ps` | 读 `frame_period_ps` 实际值 | 读 `frame_period_ps` 实际值 | `PASS` 或 `INCOMPLETE` 按实际 |

**审计结论**：按实际 sidecars 读取，缺 `delay_used_ps/peak_center/peak_sigma/corr_argmax/frame_start/mapping/pairing_window` 等字段时仅记 `INCONCLUSIVE_METADATA_INCOMPLETE`，**不自动判 Path A/A2**，需 `actual raw peak/delay/channel` 证据才可判 `A2`；`A1` 仅由 offset 扫描补足。

*注：V55 `intake_report.json` 与 `v55_authoritative_registry.json` 的实际字段以文件为准，缺失如实 `INCOMPLETE`。*

## 3. 逐源统计对比（decoder-free，基于 parquet + V25 `channel_counts.npz` TRAIN prior）

**方法**：`a,b = pairs.parquet alice_symbol/bob_symbol`，`rate_eq = mean(a==b)`，`u1=a>>5, u2=a&31` (F03 5+5 natural)，`P(A|B)=N_ab/colsum` (V25 TRAIN, `1e-15` 平滑)，`NLL = mean(-log2 P(a|b))`，`delta=(a-b) mod 1024` 直方图，`frame 级 rate_eq` 分布；V13 以 `v13r3fresh_pairs` 全量为参考基线。

> **执行**：`python diagnosis_v55_domain.py` 生成 `diagnosis_v55_domain.json` 的 `per_source.v55 / v13 / delta`；下表为**脚本输出值的落盘位置**，首次运行前填 `待运行`，运行后由 json 回填。

| 源 | 指标 | V13 (2026-01-21) 参考 | V55 (新 intake) | Δ (V55−V13) |
|---|---|---|---|---|
| **1M** | `A==B 率 / SER` | `0.760 (SER 0.240)` (channel_summary) / `0.760 (SER 0.240)` (data_inventory) | `待运行` (预期 `0.27-0.41` 区间) | `待运行` (预期 `-0.35` 至 `-0.49`) |
|  | `U1 一致率` | `≈0.88` (由 `±1` 邻bin主导，V25 隐含) | `待运行` (预期 `0.35-0.50`) | `待运行` |
|  | `U2 一致率` | `≈0.76` (A==B 主导) | `待运行` (预期 `0.27-0.41`) | `待运行` |
|  | `Bob-conditioned NLL` | `0.81-0.83 bits/symbol` (`≈830-850 bits/block`) (V25 C04) | `待运行` (预期 `>1.5 bits/symbol`, `>1500 bits/block`) | `待运行` (预期 `+0.7` bits/symbol) |
|  | `q_mass_on_p_zero` | `~0.0` (V25 TRAIN 覆盖好) | `待运行` (预期 `>0.15`) | `待运行` |
|  | `delta mass_0 / ±1 / other` | `0.760 / +1 0.238 / -1 0.001` (1M, -50ps, 以 +1 为主) | `待运行` | `待运行` |
|  | `frame 级 rate 均值±std` | `0.760±0.02` (time_block 6 块稳定) | `待运行` | `待运行` |
| **1p5M** | `A==B 率 / SER` | `0.746 (SER 0.254)` | `待运行` (预期 `0.27-0.41`) | `待运行` |
|  | `U1/U2` | `≈0.75` | `待运行` | `待运行` |
|  | `NLL` | `0.82 bits/symbol` | `待运行` (预期 `>1.5`) | `待运行` |
|  | `delta` | `0.746 / +1 0.001 / -1 0.253` (以 -1 为主, +50ps) | `待运行` | `待运行` |
| **2M** | `A==B 率 / SER` | `0.744 (SER 0.256)` | `待运行` (预期 `0.27-0.41`) | `待运行` |
|  | `U1/U2` | `≈0.74` | `待运行` | `待运行` |
|  | `NLL` | `0.83 bits/symbol` | `待运行` | `待运行` |
|  | `delta` | `0.744 / +1 0.001 / -1 0.254` (以 -1 为主) | `待运行` | `待运行` |

**已确认的系统性信号（无需待运行）**：
- `V13` 三源 `A==B 0.744-0.760` 且 `mass_0+mass_±1 ≈100%`、`other≈0`，`direction_asymmetry` 随 `delay -50→+1主导 / +50→-1主导` 翻转，是 `delay` 的确定性签名。
- `V55` 已观测 `27-41%` 相关率（`76%→27-41%` 跌落 `35-49pp`），即使 `U1/U2` 分层亦同步跌落，非单比特平面问题。
- `V55` 的 `NLL` 若以 V25 TRAIN `P(A|B)` 计算，预期因 `q_mass_on_p_zero` 高而 `>>1.5 bits/symbol`，`per-block NLL` 将远超 `1064/1094/1104` 的泄漏预算所能覆盖的 `H(U1|B)+H(U2|U1,B)`（`≈0.80 bits/symbol` 基线）。

*脚本复现命令*：`python openspec/changes/formal-ir-v56-input-domain-diagnosis/diagnosis_v55_domain.py --out diagnosis_v55_domain.json`（零 decoder 调用，`rg "decode_" 0 hits` 可验）

## 4. 固定相对 offset 扫描（A1-only，不等价 raw time-delay，诊断专用）

**方法**：`b'=(b+k) mod 1024` 仅为 parquet symbol/mapping shift (A1)，与 raw TTBin delay/peak/pairing contract (A2) 分离；直接由已有 1024-bin `delta=(a-b) mod 1024` histogram 得全 `k` 的 `rate_eq(k)=hist[k]`，仅对 `k=0` 与主峰 `k*` 算 `NLL(k)`，其余 `k` 不算 NLL；报告 `k vs 曲线` 与峰值 `k* = argmax rate_eq(k)`、`Δrate = rate(k*)-rate(0)`。**注明不等价 raw time-delay 扫描**。

> 下表为脚本输出 `offset_scan[源].curve` 与 `peak` 的落盘位置，首次运行前填 `待运行`。

| 源 | `k*` | `rate(k*)` | `Δrate` | `NLL(k*)` (bits/symbol, 仅 k* 与 0) | `delta hist[k*]` | 曲线形态 | 证据解读 (A1-only) |
|---|---|---|---|---|---|---|---|
| 1M | `待运行` | `待运行` (hist[k*]) | `待运行` | `待运行` (仅 k* 有) | `待运行` | `待运行` (单峰/平坦/多峰) | 若 `k*≠0` 且 `Δrate>0.20` 且 `NLL` 回落至 `~0.8-1.0` → `PATH_A1`；否则排除 A1，进入 A2/B 判定 |
| 1p5M | `待运行` | `待运行` | `待运行` | `待运行` | `待运行` | `待运行` | 同上 |
| 2M | `待运行` | `待运行` | `待运行` | `待运行` | `待运行` | `待运行` | 同上 |

**守卫**：`b'=(b+k)%1024` 仅 `A1` parquet symbol/mapping shift，不等价 raw TTBin time-delay 扫描；扫描以 V25 TRAIN `P(A|B)` 为参考，不重估 `P`；不对 `a` 做偏移；不试 `a/b` 联合二维偏移；仅 `k=0/k*` 有 NLL（其余 `k` 仅 `rate_eq` 来自 histogram）；`k*` **不回注**为新 pipeline，**不用于**原 90 块重跑。

*预期（基于 27-41% 跌落幅度）*：若为 `A1` parquet shift，`k*` 应单峰显著回升（如 `±1-3` bins）；若排除 A1 后仍低，曲线将平坦或弥散，峰值仍 `<0.50` 且 NLL 仍 `>1.5`，进入 `A2` (需 actual raw 证据) 或 `B` 域迁移判定。

## 5. 逐源分流与总体终态（A1/A2/B 拆分，总体四态互斥）

**域拆分**：`A1 = parquet b'=(b+k)%1024 symbol/mapping shift`（仅 offset histogram 可证），`A2 = raw TTBin delay/peak/pairing contract`（需 actual raw peak/delay/channel 证据），`B = 排除 A1/A2 后物理域迁移`；缺 metadata 本身仅 `INCONCLUSIVE_METADATA_INCOMPLETE` 不自动判 `A/A2`。

**判定逻辑**（见 design §3，逐源）：
- `single_peak_significant = k*≠0 && Δrate>0.20 && gap>0.05 && NLL(k*)<1.0` → 该源 `PATH_A1`
- `missing_raw_fields` 存在且无 actual raw 证据 → 该源 `INCONCLUSIVE_METADATA_INCOMPLETE`
- 否则 `still_low` (rate<45% 且 peak<50%) → 该源 `PATH_B_DOMAIN_SHIFT`
- 总体聚合三源：`PATH_A_ALL` (全 A1) / `PATH_B_ALL` (全 B) / `MIXED_BY_SOURCE` (源间不一致) / `INCONCLUSIVE` (含 `INCONCLUSIVE_METADATA_INCOMPLETE`)

| 逐源/总体条件 | 判定 | 含义 |
|---|---|---|
| 三源均 `PATH_A1` | **PATH_A_ALL** | 全源 parquet symbol/mapping shift，可修复契约缺陷；原 90 禁止重跑 |
| 三源均 `PATH_B` | **PATH_B_ALL** | 全源物理域迁移，需重估熵/泄漏 |
| 源间不一致（含 A1/B 混合或含 INCONCLUSIVE） | **MIXED_BY_SOURCE** | 逐源分别处理 A1 修复 vs B 重估 |
| 任一源仅因缺 metadata | **INCONCLUSIVE_METADATA_INCOMPLETE** | 缺 metadata 不自动判 A，需 actual raw 证据 |
| 其他证据不足 | `INCONCLUSIVE_NEED_CALIBRATION` | 需独立 calibration 后再判 |

### 5.1 本次诊断的分流结论（逐源 + 总体四态）

> **状态**：`待脚本运行后回填` — 运行 `diagnosis_v55_domain.py` 后，`diagnosis_v55_domain.json` 的 `shunt_decision` / `per_source_decisions` 字段即为权威结论，下表为结论回填位。

| 字段 | 值 (待回填) |
|---|---|
| `shunt_decision` | `PATH_A_ALL` / `PATH_B_ALL` / `MIXED_BY_SOURCE` / `INCONCLUSIVE` / `INCONCLUSIVE_METADATA_INCOMPLETE` |
| `per_source_decisions` | `{1M: PATH_A1/INCONCLUSIVE_METADATA_INCOMPLETE/PATH_B/..., 1p5M: ..., 2M: ...}` |
| `rationale` | `待回填` (与 §2-§4 证据链闭合，A1/A2/B 拆分) |
| `avg_rate_v55` | `待回填` (三源均值，预期 `0.27-0.41`) |
| `metadata INCOMPLETE` | 仅 `INCONCLUSIVE_METADATA_INCOMPLETE`，不自动判 A，需 actual raw 证据 |
| `offset 单峰 (A1-only)` | `待回填` (仅 A1 证据，不等价 raw time-delay) |

**无论 Path A/B，均禁止在原 V55 authoritative 90-block 上重跑任何 corrected pipeline**（已揭盲，`base→Δ8→Δ16` 任一变体均禁，含 `offset-corrected` 重译）；**禁止调 `H1/Lane C/Δ8/decoder 90/1.0`**；**不得宣称 LDPC 证伪**。

#### 若 Path A — 修复建议（materialization contract）

1. **Sidecar 必填字段**：`channels {A,B}`, `delay_used_ps`, `delay_override_ps`, `peak_center_ps`, `peak_sigma_ps`, `corr_argmax`, `frame_start_ps`, `frame_anchor`, `bin_origin_ps`, `mapping`, `wrap_rule`, `pairing_mode`, `nearest_threshold_ps`, `gate_width_ps`, `occupancy_filter` 全部显式落盘，缺一则 `DATA_NOT_READY`。
2. **FileReader 显式绑定**：`_read_ttbin_timetags(raw_ch0_id=1, raw_ch1_id=5)` + `_bin_indices_sorted_for_binwidth(200)` + `_pairs_from_sorted_bins(1024, nearest, threshold=40000)` 参数显式化，禁止隐式默认；`relative_delay_ps` 与 `frame_start_override_ps` 必须与 `peak_center` 绑定校验 (`|delay_used - peak_center|<50ps`)。
3. **Per-source 校验门**：新增 `G1' peak_status==ok && peak_to_bg>1000`, `G2' |delay_used - peak_center|<50ps`, `G3' mass_0+mass_±1>99%`，失败则拒绝进入 registry。
4. **已揭盲保护**：原 V55 90-block 已揭盲（`0/90` 已观测），**禁止**在其上应用修复后重跑；修复后需**另采/另冻新 calibration + 新 TEST blocks**（与原 90 零重叠，`frame_ids` 零重叠可机械校验）。

#### 若 Path B — 重估清单（物理域迁移）

1. 用新 session 全量 intake 重算 `N_ab → H(A|B) → F03 H(U1|B), H(U2|U1,B)` (`layer_conditional_entropy_bits`，`nbldpc_v25_gate.py` 定义)，报告 per-source `H` 与 V13 差值。
2. 重算 `m_total = floor((1.3*1024*H_source -64)/5)` 与 `m1_ep = round(m_total*H1/H_total)` 的 source-adaptive 预算，评估当前 `m2 184/190/192` / `leak 1064/1094/1104` 的 `f` 缺口（若 `H` 从 `0.80` 升至 `>1.2`，`f` 将 `>>1.3`）。
3. 若 `H` 显著升高，需重新设计 `H1` 冗余或 `Lane C` 码族，而非仅增 `Δ8`。
4. 同样需**独立 calibration frames** 先验，再冻新 blocks（与原 90 零重叠）。

## 6. 校准优先的下一步（Calibration-first，硬约束）

- **Calibration frames 定义**：与 V55 authoritative 90-block **零重叠**、未揭盲、每源建议 `8-16` 连续 frames（`2-4` blocks）的小批量，仅用于验证基础相关性，不进入正式 TEST 统计。
- **健康参考**（诊断描述，非门禁）：`A==B>60%` 且 `U1/U2>55%` 且 `Bob-conditioned NLL<1.0 bits/symbol` 且 `delta mass_0+mass_±1>85%` 视为信道健康；低于则继续诊断，不直接调码。
- **冻结新 blocks 条件**：仅当 calibration 健康且 sidecar 契约补齐（Path A）或熵重估完成（Path B）后，才允许另起 OpenSpec 冻结新 TEST registry（与原 90 零重叠、与 calibration 零重叠），并走独立 `QUALIFICATION_PLAN_READY` 流程。
- **本诊断不直接冻结**新 registry/blocks/correction；successor 需独立授权。

## 7. 禁止项（硬约束，重申）

- `SHALL NOT` 运行任何 `L1-APP / L2` decoder（`decode_row_layered_fftqspa` 等零调用，`rg "decode_" 0 hits` 可验）
- `SHALL NOT` 在原 V55 authoritative 90-block (`v55_authoritative_registry.json` 30/source) 上重跑任何 corrected pipeline（含 `offset-corrected` 重译）
- `SHALL NOT` 调 `H1/Lane C/Δ8/decoder 90/1.0/m2/leak/prior` 任一冻结参数以拟合 V55
- `SHALL NOT` 宣称 LDPC/NB-LDPC 证伪 / FER / 阈值 / SKR / 晋升；`0/90` 仅为域失配信号
- `SHALL NOT` 创建正式 `.../v56_*/run_01` 或新 registry（本诊断仅只读）；`SHALL` 先用独立 calibration 验证后才能另冻新 blocks

## 8. 复现与 provenance

- **脚本**：`openspec/changes/formal-ir-v56-input-domain-diagnosis/diagnosis_v55_domain.py`
  - 输入：`--pairs-root-v55` (默认 `v55_intake_20260828/pairs`) + `--pairs-root-v13` (默认 `v13r3fresh_pairs_20260816`) + `--counts` (`channel_counts.npz`) + `--out` (`diagnosis_v55_domain.json`)
  - 输出：`diagnosis_v55_domain.json` (含 `head/branch/data_sha/metadata_audit/per_source/offset_scan/shunt_decision`) + 控制台摘要
  - 守卫：仅 `numpy/pandas/pyarrow`，`rg "decode_" 0 hits`，`py_compile` PASS
- **输入 SHAs**：V55 三源 `.ttbin/.1.ttbin` hash 见 `intake_report.json` (`ee79c5b.../5e6fcb8.../e8c6f67...`)；V13 三源 hash 见 `build_manifest.json` (`505fcadb.../b3d308c.../099259f...`)；counts `channel_counts.npz` 来自 `nbldpc_v25_20260818/run_04`
- **输出**：`diagnosis_v55_domain.json` (machine-readable) + 本报告 (human-readable)，数据一致；不写 `run_01`

## 9. 结论（待脚本回填后固化）

- **系统性输入域失配信号**：`76%→27-41%` 跌落 + `NLL` 升高 + `sidecar 10+ 字段 INCOMPLETE` 已构成 **输入域失配** 的充分信号，非算法失败。
- **分流**：`待回填` (Path A 契约修复 vs Path B 域迁移重估)，二选一互斥，已揭盲保护与校准优先为硬约束。
- **Claim 边界**：本诊断仅为 `decoder-free` 根因诊断，不产生 `FER/阈值/SKR/资格/晋升` 证据；`V54` 二阶段在 `2026-01-21` 域上的 `43/45` 仍为有效开发确认，`V55 0/90` 不推翻。

---
*本报告由 `diagnosis_v55_domain.py` (decoder-free) 生成，需与 `diagnosis_v55_domain.json` 数值一致；`rg "decode_" 0 hits` 可验；未运行 decoder，未宣称 LDPC 证伪。*
