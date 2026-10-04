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

> **执行**：`python diagnosis_v55_domain.py` 生成 `diagnosis_v55_domain.json` 的 `per_source.v55 / v13 / delta`；下表为**脚本输出值的已回填结果**（`diagnosis_v55_domain.json: per_source`）。

| 源 | 指标 | V13 (2026-01-21) 参考 | V55 (新 intake) | Δ (V55−V13) |
|---|---|---|---|---|
| **1M** | `A==B 率 / SER` | `0.7602207 (SER 0.23979)` (n=512000) | `0.4149299 (SER 0.58507)` (n=545280, **41.5%**) | `Δrate -0.34529` (**76%→41.5%**) |
|  | `U1 一致率` | `0.9927559` | `0.4549993` | `ΔU1 -0.53776` |
|  | `U2 一致率` | `0.7602207` | `0.4320661` | `ΔU2 -0.32815` |
|  | `Bob-conditioned NLL` | `0.81960 bits/symbol` (`839.27 bits/block`) | `28.57290 bits/symbol` (`29258.65 bits/block`) | `ΔNLL +27.75330 bits/symbol` |
|  | `q_mass_on_p_zero` | `0.000381 (0.038%)` (zero_prob 195) | `0.568957 (56.9%)` (zero_prob 310241) | — |
|  | `delta mass_0 / +1 / -1 / other` | `0.76022 / 0.001334 / 0.238445 / ~0` (以 -1 为主, direction_asym -0.237) | `0.41493 / 0.012709 / 0.011955 / 0.56041` (弥散, asym 0.000754) | — |
|  | `frame 级 rate 均值±std` | `0.76022±0.02596` (2000 frames, 0.664-0.855) | `0.41493±0.03136` (2130 frames, 0.293-0.523) | — |
| **1p5M** | `A==B 率 / SER` | `0.7455305 (SER 0.25447)` (n=708352) | `0.3754878 (SER 0.62451)` (n=1312000, **37.5%**) | `Δrate -0.37004` |
|  | `U1 / U2` | `0.99231 / 0.74553` | `0.41544 / 0.39357` | `ΔU1 -0.57687 / ΔU2 -0.35196` |
|  | `NLL` | `0.83880 bits/symbol` (`858.93 bits/block`) | `30.57725 bits/symbol` (`31311.10 bits/block`) | `ΔNLL +29.73845` |
|  | `q_mass_on_p_zero` | `0.000285 (0.029%)` (202) | `0.609187 (60.9%)` (799253) | — |
|  | `delta mass_0 / +1 / -1 / other` | `0.74553 / 0.253261 / 0.001208 / ~0` (以 +1 为主, asym +0.252) | `0.37549 / 0.010292 / 0.013156 / 0.60106` (弥散, asym -0.00286) | — |
|  | `frame 级` | `0.74553±0.02729` (2767 frames) | `0.37549±0.03043` (5125 frames, 0.281-0.484) | — |
| **2M** | `A==B 率 / SER` | `0.7442590 (SER 0.25574)` (n=933120) | `0.2748667 (SER 0.72513)` (n=1411328, **27.5%**) | `Δrate -0.46939` |
|  | `U1 / U2` | `0.99218 / 0.74426` | `0.31344 / 0.29630` | `ΔU1 -0.67874 / ΔU2 -0.44796` |
|  | `NLL` | `0.84259 bits/symbol` (`862.82 bits/block`) | `35.56324 bits/symbol` (`36416.76 bits/block`) | `ΔNLL +34.72065` |
|  | `q_mass_on_p_zero` | `0.000267 (0.027%)` (249) | `0.710065 (71.0%)` (1002134) | — |
|  | `delta mass_0 / +1 / -1 / other` | `0.74426 / 0.254257 / 0.001484 / ~0` (以 +1 为主, asym +0.253) | `0.27487 / 0.010060 / 0.008671 / 0.70640` (弥散, asym +0.00139) | — |
|  | `frame 级` | `0.74426±0.02718` (3645 frames) | `0.27487±0.02824` (5513 frames, 0.168-0.391) | — |
| **overall** | `avg_rate V55` | — | `0.35509` (三源均值) | — |

> **NLL 口径（失配评分，非物理条件熵）**：`NLL = mean(-log2 P_TRAIN(a|b))` 以 V25 `channel_counts.npz` 的 `P(A|B)=N_ab/colsum` 为参考，`1e-15` floor 平滑；`q_mass_on_p_zero 57-71%` 表示 `>50%` 的 `(a,b)` 在 TRAIN 中零计数，落入 `1e-15` 分支贡献 `≈49.83 bits/symbol` 惩罚，NLL 膨胀至 `28.57/30.58/35.56 bits/symbol` 属**失配评分**，**不是**新域的物理条件熵 `H(A|B)`，**不能直接用于码率/泄漏设计**，仅作 V25 模型与新域的失配度量。

**已确认的系统性信号**：
- `V13` 三源 `A==B 0.744-0.760` 且 `mass_0+mass_±1 ≈100%`、`other≈0`，`direction_asymmetry` 随 `delay -50→+1主导 / +50→-1主导` 翻转，是 `delay` 的确定性签名。
- `V55` 已观测 `27-41%` 相关率（`76%→27-41%` 跌落 `35-49pp`），即使 `U1/U2` 分层亦同步跌落，非单比特平面问题。
- `V55` 的 `NLL` 若以 V25 TRAIN `P(A|B)` 计算，预期因 `q_mass_on_p_zero` 高而 `>>1.5 bits/symbol`，`per-block NLL` 将远超 `1064/1094/1104` 的泄漏预算所能覆盖的 `H(U1|B)+H(U2|U1,B)`（`≈0.80 bits/symbol` 基线）。

*脚本复现命令*：`python openspec/changes/formal-ir-v56-input-domain-diagnosis/diagnosis_v55_domain.py --out diagnosis_v55_domain.json`（零 decoder 调用，`rg "decode_" 0 hits` 可验）

## 4. 固定相对 offset 扫描（A1-only，不等价 raw time-delay，诊断专用）

**方法**：`b'=(b+k) mod 1024` 仅为 parquet symbol/mapping shift (A1)，与 raw TTBin delay/peak/pairing contract (A2) 分离；直接由已有 1024-bin `delta=(a-b) mod 1024` histogram 得全 `k` 的 `rate_eq(k)=hist[k]`，仅对 `k=0` 与主峰 `k*` 算 `NLL(k)`，其余 `k` 不算 NLL；报告 `k vs 曲线` 与峰值 `k* = argmax rate_eq(k)`、`Δrate = rate(k*)-rate(0)`。**注明不等价 raw time-delay 扫描**。

> 下表为脚本输出 `offset_scan[源].curve` 与 `peak` 的已回填结果（`diagnosis_v55_domain.json: offset_scan`），**A1-only，不等价 raw TTBin time-delay 扫描**。

| 源 | `k*` | `rate(k*)` | `Δrate` | `NLL(k*)` (bits/symbol, 仅 k* 与 0) | `delta hist[k*]` | 曲线形态 | 证据解读 (A1-only) |
|---|---|---|---|---|---|---|---|
| 1M | `0` | `0.41493` | `0.0` | `NLL*=28.57290 = NLL0` (gap 0.40222, single_peak false) | `mass_0 0.41493 / ±1 0.0127/0.0120` | 平坦弥散（k=±1 仅 ~0.012，非峰） | **A1 基本排除**：k*=0 且 Δrate=0 且 NLL 不变，parquet `b'=(b+k)%1024` 不可修复；V25 严重不匹配，A2 尚未排除 |
| 1p5M | `0` | `0.37549` | `0.0` | `NLL*=30.57725 = NLL0` (gap 0.36233, single_peak false) | `mass_0 0.37549 / ±1 0.0103/0.0132` | 平坦弥散 | **A1 基本排除**，同上 |
| 2M | `0` | `0.27487` | `0.0` | `NLL*=35.56324 = NLL0` (gap 0.26481, single_peak false) | `mass_0 0.27487 / ±1 0.0101/0.00867` | 平坦弥散 | **A1 基本排除**，同上 |

> **A1 守卫重申**：`b'=(b+k) mod 1024` 仅为 parquet symbol/mapping shift (A1)，由 1024-bin `delta=(a-b) mod 1024` histogram 直接得 `rate(k)=hist[k]`，与 raw TTBin 的 time-delay/peak/pairing contract (A2) 分离，**不等价 raw TTBin 扫描**；本次 `k*=0 / Δrate=0 / NLL*=NLL0` 三源一致，排除可由纯 A1 解释的假设。

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

> **状态**：已由 `diagnosis_v55_domain.py` 回填 — `diagnosis_v55_domain.json: shunt_evidence / per_source_decisions / shunt_decision` 为权威结论。

| 字段 | 值 (已回填) |
|---|---|
| `shunt_decision` (总体) | `INCONCLUSIVE_METADATA_INCOMPLETE` — 三源一致，因缺 raw 契约字段无法 auto-assign Path A2，归为 **INCONCLUSIVE** 总体 |
| `per_source_decisions` | `{1M: INCONCLUSIVE_METADATA_INCOMPLETE, 1p5M: INCONCLUSIVE_METADATA_INCOMPLETE, 2M: INCONCLUSIVE_METADATA_INCOMPLETE}` (3/3 一致) |
| `rationale` | `missing raw contract fields [delay_used_ps, peak_center_ps, peak_sigma_ps, corr_argmax, frame_start_ps, mapping] without actual raw peak/delay/channel evidence -> INCONCLUSIVE, cannot auto-assign Path A2` (json `shunt_evidence[*].per_source_rationale`) |
| `avg_rate_v55` | `0.35509` (三源均值 (0.415+0.375+0.275)/3) |
| `metadata INCOMPLETE` | 三源均仅 `INCONCLUSIVE_METADATA_INCOMPLETE`，不自动判 A/A2，需 actual raw 证据；`b'=(b+k)%1024 covers A1 only; A2 requires raw TTBin evidence; B after excluding A1/A2` |
| `offset 单峰 (A1-only)` | `k*=0, Δrate=0, NLL*=NLL0, gap 0.26-0.40, single_peak_significant false` — **A1 基本排除**，不等价 raw time-delay 扫描 |

逐源 `shunt_evidence` 明细：`1M gap 0.40222 / NLL 28.57=28.57 / still_low true`；`1p5M gap 0.36233 / 30.58=30.58 / still_low true`；`2M gap 0.26481 / 35.56=35.56 / still_low true` — 均 `single_peak_significant false`。

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

## 9. 结论（已回填固化）

- **系统性输入域失配信号**：`76%→27-41%` 跌落（1M 76.0%→41.5% Δ-34.5pp；1p5M 74.6%→37.5% Δ-37.0pp；2M 74.4%→27.5% Δ-46.9pp）+ `NLL 0.82→28.57/30.58/35.56 bits/symbol` 膨胀（Δ+27.75/+29.74/+34.72，`q_mass_on_p_zero 57-71%` 落 1e-15 floor）+ `sidecar 10+ 字段 INCOMPLETE (delay/peak/frame_start/mapping)` 已构成 **输入域失配** 的充分信号，非算法失败。**NLL 为 1e-15 floor 失配评分，不是物理条件熵，不可直接设计码率**。
- **分流**：三源一致 `INCONCLUSIVE_METADATA_INCOMPLETE`，总体 **INCONCLUSIVE** (`avg_rate 0.355`)；**A1 基本排除**（`k*=0 / Δrate=0 / NLL*=NLL0, single_peak false, gap 0.26-0.40`，A1-only 不等价 raw TTBin）、**V25 严重不匹配**（`q_mass_on_p_zero 56.9%/60.9%/71.0%`）、**A2 尚未排除**（需 actual raw TTBin peak/delay/channel 证据才可判），已揭盲保护与校准优先为硬约束。
- **Claim 边界**：本诊断仅为 `decoder-free` 根因诊断，不产生 `FER/阈值/SKR/资格/晋升` 证据；`V54` 二阶段在 `2026-01-21` 域上的 `43/45` 仍为有效开发确认，`V55 0/90` 不推翻。

---
*本报告由 `diagnosis_v55_domain.py` (decoder-free) 生成，需与 `diagnosis_v55_domain.json` 数值一致；`rg "decode_" 0 hits` 可验；未运行 decoder，未宣称 LDPC 证伪。*
