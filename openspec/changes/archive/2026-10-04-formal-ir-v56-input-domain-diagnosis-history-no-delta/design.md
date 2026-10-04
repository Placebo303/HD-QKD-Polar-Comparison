# OpenSpec Design: formal-ir-v56-input-domain-diagnosis

**Lifecycle**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — **decoder-free 输入域失配根因诊断，不运行 L1/L2 decoder。**
**Cycle**: `V56D0`
**Predecessor**: `formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation` (plan SHA `3d7c63eefe655c9f25d199af3f7f4ea311ac454b`, branch `formal-ir-mainline`), **HEAD** `cf8b098047cf64aa1e0426e2ea2e62b680430bd6` (2026-08-29, V55 固化后), data SHA `84d62779603e62de50ded5182ed65b65d3dc6084` (200ps legacy_v1 nearest 1024, 单点 `84d62779`)
**Feasibility**: V54 二阶段在 V55 intake 之前于 held-out `45块`上曾 `18 base → 38 stage1 → 43/45 final` (`V54_DELTA8_ALREADY_SUFFICIENT`，非 `42→43`)，证明方法在 `2026-01-21` 域上构造与泄漏 `1064/1094/1104` 等价可行；V55 同方法在新 intake `90块`上 `0/90` 且 `U1/U2 76%→27-41%`，信号指向**输入域系统性失配**而非算法本身，需先完成 decoder-free 诊断再决定 materialization 修复或域重估。
**Key judgement**: **`0/90` 不是 LDPC 证伪，是 200ps + legacy_v1 + channel/routing/offset/mapping 跨 session 不兼容的域失配信号；禁止在已揭盲原 90 块上择优重跑，必须先以独立 calibration frames 验证基础相关性。**

## 1. 科学问题与关键判断

> 在**完全冻结 V54 二阶段完整方法**（`H1-16 + L1-APP via H1 BP + Lane C m2 184/190/192 + H_inc1/2 Δ8+8 + decoder 90/1.0 poly37 + L2-only tag + TRAIN prior channel_counts.npz`）与**相同处理点**（`d=1024 bw=200ps pairing=nearest rule=legacy_v1`）下，为何 **V55 独立跨 session TEST 的 authoritative 90-block** 会从 `V54 43/45` 跌至 `0/90`，且 `A==B` 与 `U1/U2` 一致率从 `~76%` 跌至 `27-41%`？该跌落是否可由**显式 metadata/offset/channel 错误**（可修复）解释，或即使处理无误仍属**不同物理域**（需重估 `H(U1|B), H(U2|U1,B)` 与泄漏）？

- **对照**：`V13 2026-01-21` 三源 (`type2_1M_20260121_184040 / type2_1p5M_20260121_183806 / type2_2M_20260121_183657`, `200ps legacy_v1`, `nearest`, `delay -50/+50/+50`, `peak_center -50/+50`, `corr_argmax 8191`, `channels A1/B5 隐式`) 作为参考域；`V55` 三源 (`20260123_1M_600k_0dB F2130 / 20260107_PPLN_1p5M F5125 / 20260123_2M_1p2M_0dB F5513`, 同 `200ps legacy_v1 nearest 1024` 但 sidecar 缺 `delay/peak/mapping` 字段) 作为待诊域。
- **不变量**：`dimension 1024 / bin_width 200ps / pairing nearest / legacy_v1 / frame_period 204800 / BLOCK 1024 (4×256)` 为名义不变量；但 `TimeTagger channels A/B、delay、bin origin、peak 位置、mapping、pairing 方向` 为跨 session 可变且未被 V55 sidecar 完整记录，是首要怀疑点。
- **诊断性质**：纯 **decoder-free**（零 `decode_*` 调用），仅读 `pairs.parquet` 与 `sidecar_meta.json` + `channel_counts.npz`，做**统计对比**与**固定 offset 扫描**（不择优），最终给出**唯一分流判定**（Path A 可修复 vs Path B 域迁移）。

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

- **诊断禁令**：诊断期间 `SHALL NOT` 调用任何 `decode_*` / `construct_*` 构造新矩阵 / 调 `m2/leak/decoder` 参数；违者诊断无效。
- **已揭盲保护**：V55 authoritative 90-block 的 `frame_ids/ordinal` 已在 `v55_authoritative_registry.json` 冻结且已执行一次 `0/90` 揭盲观测，**禁止**在其上重跑任何 corrected pipeline（即使发现 offset 错误）。

### 2.2 V13 vs V55 元数据对比矩阵（只读审计维度，读取实际 sidecars/metrics，不硬编码）

> **读取方式**：脚本 `audit_metadata()` 直接读取 `workspace/v13r3fresh_20260816/sidecars/*/sidecar_meta.json` 与 `comparison_bench/outputs_comparison/v55_intake_20260828/sidecars/*/sidecar_meta.json` 及 `build_manifest.json` 的 `used_params`/`materialize_params` 字段；缺失如实报告为 `INCOMPLETE`（含缺失文件本身），不硬编码 `delay -50/+50` 等权威值；仅当文件存在且字段非空才记 `PASS` 并记录 `_value`。

| 维度 | V13 (2026-01-21) 实际 sidecars | V55 (2026.1.23/2026.1.07) 实际 sidecars | 审计结论 |
|---|---|---|---|
| acquisition date | 读 `sidecar_meta.json` / `build_manifest.json` 的 `source_ttbin_paths` | 读 `sidecars/*/sidecar_meta.json` 的 `provenance` | `MISMATCH` (预期，non-iid) 如文件可读 |
| raw `.ttbin` + `.1.ttbin` | 双文件同 acquisition，hash 见 `build_manifest.json` | 双文件同 acquisition，hash 见 `intake_report.json` | `PASS` 如双文件存在 |
| channels A/B | 读 `used_params` 实际 `A1/B5` 或缺失 | 读 `materialize_params.channels` | `PASS` 或 `INCOMPLETE` 按实际 |
| delay_used_ps | 读 `used_params.delay_used_ps` 实际值 | 读 `used_params.delay_used_ps` 实际值 | `PASS` 或 `INCOMPLETE` 按实际 |
| delay_override_ps | 读 `used_params.delay_override_ps` | 读 `used_params.delay_override_ps` | `PASS` 或 `INCOMPLETE` 按实际 |
| peak_center_ps | 读 `used_params.peak_center_ps` | 读 `used_params.peak_center_ps` | `PASS` 或 `INCOMPLETE` 按实际 |
| peak_sigma_ps | 读 `used_params.peak_sigma_ps` | 读 `used_params.peak_sigma_ps` | `PASS` 或 `INCOMPLETE` 按实际 |
| corr_argmax / corr_bins | 读 `used_params.corr_argmax/corr_bins` | 读 `used_params.corr_argmax/corr_bins` | `PASS` 或 `INCOMPLETE` 按实际 |
| frame_start_ps / frame_anchor | 读 `used_params.frame_start_ps/frame_anchor` | 读 `used_params.frame_start_ps/frame_anchor` | `PASS` 或 `INCOMPLETE` 按实际 |
| bin origin / wrap_rule | 读 `mapping/wrap_rule` | 读 `mapping/wrap_rule` | `PASS` 或 `INCOMPLETE` 按实际 |
| pairing_mode / direction | 读 `pairing_mode` + `nearest_threshold_ps` | 读 `pairing_mode` + `nearest_threshold_ps` | `PASS` 或 `INCOMPLETE` 按实际 |
| gate_width_ps / coinc_window | 读 `gate_width_ps` | 读 `gate_width_ps` | `PASS` 或 `INCOMPLETE` 按实际 |
| occupancy_filter | 读 `occupancy_filter/frame_diag` | 读 `occupancy_filter` | `PASS` 或 `INCOMPLETE` 按实际 |
| processing_rule | 读 `processing_rule_version` | 读 `processing_rule_version` | `PASS` 或 `INCOMPLETE` 按实际 |
| dimension / bin_width | 读 `dimension/bin_width_ps` | 读 `dimension/bin_width_ps` | `PASS` 或 `INCOMPLETE` 按实际 |
| frame_period_ps | 读 `frame_period_ps` | 读 `frame_period_ps` | `PASS` 或 `INCOMPLETE` 按实际 |

> **设计结论**：缺 `delay_used_ps/peak_center/peak_sigma/corr_argmax/frame_start/mapping/pairing_window` 等字段时仅记 `INCONCLUSIVE_METADATA_INCOMPLETE`，不自动判 Path A/A2；需 `actual raw peak/delay/channel` 证据才可判 `A2`；诊断以统计与 `A1-only` offset 扫描补足。

### 2.3 诊断统计量定义（decoder-free，基于 parquet + V25 counts，脚本一致）

- **A==B 率 / SER**：`rate_eq = mean(a == b)`, `SER = 1 - rate_eq`，per source 与 per frame 分布。
- **U1/U2 一致率**：F03 `5+5` split (`FACTORIZATIONS["F03"]` `L1 [9..5] L2 [4..0]`)，`split_label(a, "F03", "L01_natural")` 得 `u1 = a >>5`, `u2 = a & 31` (natural)，同理 `b`；`U1_eq = mean(u1_a == u1_b)`, `U2_eq = mean(u2_a == u2_b)`，已观测 `V13 ~76% → V55 27-41%`，本诊断复算并分层报告。
- **Bob-conditioned NLL**：基于 V25 TRAIN `channel_counts.npz` 的 `P(A|B)=N_ab / colsum`，`NLL_bits = mean(-log2 P(a|b))` (add `1e-15` 平滑)，报告 `bits/symbol` 与 `bits/block (×1024)`；同时报告 `q_mass_on_p_zero = sum_{a,b: N_ab_train=0} P_empirical(a,b)` 与 `zero_prob_count`。
- **边缘分布**：`P(A), P(B)` 1024-bin 直方图与 `top_a/b_frac`、`marginal_entropy`（KL/rare-bin 等未实现指标已删除以与脚本一致）。
- **Frame 级相关率**：per-frame `rate_eq` 直方图、`±1` 邻bin质量 (`delta=(a-b) mod 1024` 直方图峰于 `0/±1` 的质量、`direction_asymmetry = frac[+1]-frac[-1]`)。
- **Modular delta**：`delta_ab = (a - b) mod 1024` 与 `delta_ba = (b - a) mod 1024` 双直方图，`mass_0/mass_±1/other`。

### 2.4 Offset 扫描诊断（固定相对 offset，仅作证据，A1-only）

```
for each source in {1M,1p5M,2M}:
  load pairs (a,b) from parquet (authoritative 90-block 或全量 intake，全量优先)
  delta = (a - b) mod 1024; hist = bincount(delta, minlength=1024) / n  // 1024-bin modular-delta histogram
  for k in [-8..+8]:  // 直接由 hist 得全 k 的 rate_eq(k)=hist[k mod 1024]，不逐 k 扫描 (b+k)
    rate_eq(k) = hist[k mod 1024]
  仅对 k=0 与 k*=argmax rate_eq(k) 算 NLL(k)=mean(-log2 P(a|b_k)) // P 来自 V25 TRAIN，其余 k 不算 NLL
  报告曲线、峰值 k*、Δrate、NLL(0) vs NLL(k*)
  注：b'=(b+k)%1024 仅为 parquet symbol/mapping shift (A1)，不等价 raw TTBin time-delay 扫描；A2 需 actual raw peak/delay/channel 证据
```

- **仅诊断**：`k*` 不用于修正原 90 块，不用于新 pipeline，不用于调参；仅作为 `A1 parquet symbol/mapping` 错误的**似然证据**，与 `A2 raw TTBin delay/peak/pairing contract` 分离。
- **判定启发**：若某 `k* ≠0` 且 `Δrate > 20pp` 且 `NLL(k*)` 回落至 `~0.8-1.0 bits/symbol` 且 `hist[k*]` 峰回 `0`，则支持 Path A1（parquet symbol shift）；若 `k` 曲线平坦或多峰弥散、峰值仍 `<50%`、NLL 仍 `>1.5 bits/symbol`，则排除 A1，进入 A2/B 判定。

## 3. 逐源分流与总体终态（A1/A2/B 拆分，总体四态）

> **域拆分**：`A1 = b'=(b+k)%1024 parquet symbol/mapping shift`（仅 offset 扫描可证），`A2 = raw TTBin delay/peak/pairing contract`（需 actual raw peak/delay/channel 证据，缺 metadata 本身仅 INCONCLUSIVE_METADATA_INCOMPLETE 不自动判 Path A），`B = 排除 A1/A2 后物理域迁移`。

```
per_source in {1M,1p5M,2M}:
  if single_peak_significant (k*≠0, Δrate>20pp, gap>0.05, NLL(k*)<1.0):
    → PATH_A1_PARQUET_SYMBOL_SHIFT
  elif missing_raw_fields (delay/peak/frame_start/mapping 等 INCOMPLETE) without actual raw evidence:
    → INCONCLUSIVE_METADATA_INCOMPLETE  // 需 actual raw peak/delay/channel 证据才可判 A2
  elif still_low (rate<45% 且 peak<50% 且无单峰 且 NLL>>1.0):
    → PATH_B_DOMAIN_SHIFT
  else:
    → INCONCLUSIVE
overall in {PATH_A_ALL, PATH_B_ALL, MIXED_BY_SOURCE, INCONCLUSIVE, INCONCLUSIVE_METADATA_INCOMPLETE}:
  if all per_source == PATH_A1 (or mix A1/A2 with actual evidence): → PATH_A_ALL
  elif all per_source == PATH_B: → PATH_B_ALL
  elif any INCONCLUSIVE_METADATA_INCOMPLETE with uniform: → INCONCLUSIVE_METADATA_INCOMPLETE 或 MIXED_BY_SOURCE
  elif decisions differ: → MIXED_BY_SOURCE
  else: → INCONCLUSIVE
```

### 3.1 Path A1 — parquet symbol/mapping shift（A1）可修复

- **证据**：`A1-only` offset 单峰回升 (`k*≠0, Δrate>20pp, gap>0.05, NLL(k*)<1.0, hist[k*]`显著)，与 `A2` 分离
- **根因假设**：`mapping/bin_origin` 或 parquet 符号域循环偏移，非 raw time-delay；`FileReader` 符号化链路错配
- **修复建议**：同原 contract 级（sidecar 必填 `mapping/bin_origin/wrap_rule` 等、FileReader 符号化显式化、G1'-G3' 门），原 90 已揭盲禁止重跑

### 3.1.2 Path A2 — raw TTBin delay/peak/pairing contract（需 actual raw 证据）

- **证据**：需 `actual raw peak/delay/channel` 证据（`peak_center/peak_sigma/corr_argmax/delay_used_ps/channels` 的实测值及跨 session 对比），**缺 metadata 本身仅 INCONCLUSIVE_METADATA_INCOMPLETE，不自动判 Path A/A2**
- **根因假设**：`FileReader` 未显式绑定 `delay_override_ps / peak_gate_sigma / frame_start_override_ps / coinc_window_override_ps`，跨 session `TimeTagger` 漂移；需补实际测量验证
- **修复建议**：同原 contract 级 Sidecar 必填与 FileReader 显式绑定；补 `actual raw` 证据后才可确认 A2

### 3.2 Path B — 不同物理域，需重估条件熵/泄漏（排除 A1/A2 后）

- **证据**：排除 `A1` 单峰后仍 `27-45%` 相关、`offset` 无单峰或峰值仍 `<50%`、`NLL` 仍 `>1.5 bits/symbol`、`q_mass_on_p_zero` 高、`U1/U2` 仍低、且无 `A2` raw 证据支持
- **根因假设**：`2026-01-23 / 2026-01-07` 的 `device/channel_params/power/delay` 与 `2026-01-21` 非同分布，真实信道 `P(A|B)` 已迁移，`H(U1|B)≈0.025 bits` 与 `H(U2|U1,B)≈0.78 bits` 的 V25 估计不再适用，`m2 184/190/192` 与 `f≈1.3` 的泄漏预算根本不适配新域
- **重估清单**：
  1. 用新 session 的 **全量 intake** 重算 `N_ab` → `H(A|B)` → `F03` 链式 `H(U1|B), H(U2|U1,B)`（`layer_conditional_entropy_bits`），报告 `per-source H` 与 `V13` 差值。
  2. 重算 `m_total = floor((1.3*1024*H_source -64)/5)` 与 `m1_ep = round(m_total*H1/H_total)` 的 source-adaptive 预算，评估当前 `m2/leak` 的 `f` 缺口。
  3. 若 `H` 显著升高（如 `>1.2 bits`），则需重新设计 `H1` 冗余或 `Lane C` 码族，而非仅增 `Δ8`。
  4. 同样需**独立 calibration frames** 先验，再冻新 blocks。

## 4. 校准优先的下一步（Calibration-first）

- **Calibration frames 定义**：与 V55 authoritative 90-block **零重叠**、未揭盲、每源建议 `8-16` 连续 frames（`2-4` blocks）的小批量，仅用于验证基础相关性，不进入正式 TEST 统计。
- **健康阈（诊断参考，非门禁）**：`A==B>60%` 且 `U1/U2>55%` 且 `Bob-conditioned NLL<1.0 bits/symbol` 且 `delta mass_0+mass_±1>85%` 视为信道健康；低于则继续诊断，不直接调码。
- **冻结新 blocks 条件**：仅当 calibration 健康且 sidecar 契约补齐（Path A）或熵重估完成（Path B）后，才允许另起 OpenSpec 冻结新 TEST registry（与原 90 零重叠、与 calibration 零重叠），并走独立 `QUALIFICATION_PLAN_READY` 流程。

## 5. 诊断脚本与报告（decoder-free 守卫）

- **脚本** `diagnosis_v55_domain.py`（本变更目录下，decoder-free）：
  - 输入：`--pairs-root` (默认 `comparison_bench/outputs_comparison/v55_intake_20260828/pairs` + `v13r3fresh_pairs_20260816`), `--sidecar-root`, `--counts` (`channel_counts.npz`), `--registry` (`v55_authoritative_registry.json`), `--out`
  - 输出：`diagnosis_v55_domain.json` (per-source 统计、NLL、edge、offset 曲线、分流判定) + 控制台摘要
  - 守卫：`rg "decode_" 0 hits`、`rg "import.*decoder"` 0、仅 `numpy/pandas/pyarrow`，零 `compute_tag_64` 以外 tag 调用
- **报告** `DIAGNOSIS_REPORT.md`：记录每源 `A==B/U1/U2/NLL/edge/zero-bins/frame相关率`、V13 vs V55 差值、offset 扫描表与曲线、分流结论（Path A/B）与下一步校准清单；结论不扩大为 FER/阈值/SKR/晋升

## 6. 守卫与禁止项（decoder-free 硬约束）

1. **Decoder 禁止**：脚本与报告生成期间 `SHALL NOT` 出现 `decode_row_layered_fftqspa / decode_* / construct_lane_c_prototype` 调用；`grep` 守卫 `0 hits`。
2. **原 90 已揭盲保护**：`SHALL NOT` 在 `v55_authoritative_registry.json` 的 `90 blocks (30/source)` 上重跑任何 corrected pipeline（含 offset-corrected），违者诊断作废。
3. **参数冻结**：`SHALL NOT` 调 `H1/Lane C/Δ8/decoder 90/1.0/m2/leak/prior` 任一参数以拟合 V55 数据。
4. **LDPC 证伪禁止**：`SHALL NOT` 将 `0/90` 记为 LDPC/NB-LDPC 证伪证据；报告必须显式声明 `0/90` 为域失配信号。
5. **校准优先**：`SHALL` 先用独立 calibration frames 验证基础相关性后，才能另冻新 blocks 进入 qualification；本诊断不直接冻结新 blocks。

## 7. 记录、聚合、输出（本诊断）

- **输入根**（只读）：`v55_intake_20260828`, `v13r3fresh_pairs_20260816`, `nbldpc_v25_20260818/run_04`, `v55_authoritative_registry.json`
- **输出**（本变更目录 additive）：`diagnosis_v55_domain.json` (machine-readable), `DIAGNOSIS_REPORT.md` (human-readable), 控制台 `stdout` 摘要；不写 `run_01`，不写新 registry
- **可重现性**：脚本确定性（`numpy` 固定、parquet 读取排序 `frame_id/pair_idx`），输出含 `HEAD cf8b09... / data SHA 84d62779 / run_at / input SHAs`

## 8. 与 V55 的衔接

- V55 保持 `QUALIFICATION_PLAN_READY / EXECUTE_NOT_AUTHORIZED` 且 authoritative 90-block 已冻但 `0/90` 已揭盲；V56D0 诊断不改变 V55 终态，仅追加**输入域失配的只读证据**。
- 诊断结论为 successor change 的**唯一入口**：`Path A` → `materialization-contract-fix` change；`Path B` → `entropy-reestimation` change；`INCONCLUSIVE` → `calibration-only` change；三者均需独立授权。

## 9. 自由裁量 D1–D8（本诊断）

- D1 元数据审计维度固定为 `delay/peak/bin_origin/mapping/pairing/occupancy` 等 15 项，不扩展至光路物理参数
- D2 统计量固定为 `A==B/U1/U2/NLL/edge/zero/frame/delta` 7 类，不引入新熵估计器
- D3 Offset 扫描固定 `±8`（可扩 `±16` 仅作诊断），不做二维 `A/B` 联合偏移
- D4 分流阈启发固定为 `Δrate 20pp / NLL 1.0 / 相关率 60%` 仅作证据描述，不作门禁
- D5 修复建议固定为 sidecar 必填 + FileReader 显式绑定 + per-source 校验门，已达最简
- D6 重估清单固定为 `H(U1|B)/H(U2|U1,B)/m_total/f` 四项，不重设计码族
- D7 校准帧固定为 `8-16` frames 小批量，不进入正式 TEST
- D8 本诊断为 decoder-free 只读，不产生新 registry/blocks，等待 successor
