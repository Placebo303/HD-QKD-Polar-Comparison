# OpenSpec Spec: formal-ir-v67-multisession-feasibility-map

**Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — 仅 plan 四工件 + decoder-free 多 session 可行域地图，不改主体/V64/src，不启动 decoder，不创 run_01，U=32*U1+U2 5+5 不GE，acquisition 去重 ≤9 每类≤3，五分流，总体 V67_FEASIBILITY_MAP_COMPLETE

**Change**: `formal-ir-v67-multisession-feasibility-map` (`V67-MAP`, branch `formal-ir-mainline`, HEAD `520b51c46e6b427f19225f69dc87602d6f0cbfb5`, data `84d62779`, ≤9 sessions)

**Predecessor**: `formal-ir-v64-full-symbol-verification-correction` (`22/24 PASS`) + `formal-ir-v65-new-session-channel-compatibility` + `formal-ir-v66-single-segment-adaptive-nbldpc (832e5394)` — V67 新增多 session 解耦地图，A-H 全约束，decoder-free

## 1. 变更类型与生命周期

- **Type**: `MULTISESSION_FEASIBILITY_MAP` — 按 acquisition 去重预注册 ≤9 session（每类≤3 机械不按 CE 替换）上，每 session `Stage0 8 物化 → Stage1 CAL256 VAL128 分类 (C_ab/P/λ/CE/m_raw 不 cap) → Stage2 CAL1024 VAL256 confirmation (重算不复用) → TEST不读` → 五分流 `EVIDENCE_INCOMPLETE / MODEL_NOT_STABLE / CURRENT_CANDIDATE_COMPATIBLE(≤16/≤LaneC+8+8) / RATE_ADAPTATION / NEAR_FULL_DISCLOSURE(≥1024或≈10240)` 之一，全部 session 完成后 `overall = V67_FEASIBILITY_MAP_COMPLETE`，为 V68 提供 `candidate_session_list` 与 `counts_per_classification`。
- **Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — 本轮止于 plan 四工件 + decoder-free 地图（`v67_data_registry.json + v67_spike.py + v67_spike_summary.json + v67_feasibility_table.(csv|json) + V67_FEASIBILITY_REPORT.md`），**不实现 runner，不执行 decoder，不创建 `run_01`，不读 TEST 统计，不改主体/V64/src，不调 V68 码**；正式 `run_01` 或 `V68` decoder 需独立 `PLAN_ACCEPT` + `EXECUTE_AUTH`；`DECODER_FREE` 表示零 `decode_*` 调用（`rg 0 hits`）。
- **Branch**: `formal-ir-mainline`；`HEAD` `520b51c46e6b427f19225f69dc87602d6f0cbfb5` 重核，不一致阻塞；已与 `git rev-parse HEAD` 一致。
- **Data SHA**: `84d62779` (`d1024 bw200 nearest legacy_v1`) — 多 session 复用该处理点；每 session `Stage0 8 + Stage1 256/128 + Stage2 1024/256`，`acquisition 去重`。
- **Session bound**: `total ≤9`, `per_category ≤3`（`1M / 1p5M / 2M` 各≤3，机械 `acquisition_time` 前 3，不按 `CE/m` 替换）。
- **Rate feasibility**: **m1_raw=ceil(1.3*1024*CE1/5), m2_raw=ceil(1.3*1024*CE2/5), raw_disclosure=5*(m1_raw+m2_raw)+64 不 cap**，五分流阈 `≤16 / ≤LaneC+8+8 / <1024 / ≥1024或≈10240`。

## 2. 冻结方法（主体完全冻结，V67 零改，多 session）

### 2.1 主体不变量（V64 完全冻结，V67 零改，22/24 PASS）

- `n=1024 symbols/block` (`4×256 frames`), `q=1024 (10-bit s=32*u1+u2, u1=s>>5 0..31, u2=s&31 low)`, `log2 q per plane 5`, `GF32 poly37`, `tag=64 bits/block 仍单 tag 仅 total 计一次`。
- `H1 = V31-H1-QC 16×1024 rank16 80b` 母矩阵；`U =32*U1+U2, F03 5+5 natural, 不GE (禁 Gray/V68)` (`U1>>5, U2&31`)。
- `Lane C` ordinal-2 `s38310x`：`m2 base 1M 184 / 1p5M 190 / 2M 192`，`support/标签/置换/MET图` 全冻，**不引 MET/protograph/SC/Gray/V68**。
- `H_inc1 8×1024 + H_joint1 192×1024` nested；`H_inc2 8×1024 + H_total 200×1024` nested；`H_total_full 216/222/224` (`16+m2`)；`rank_total==m2+16, independence_2==8, row≤16, col_inc≤1`。
- `decoder`: `decode_row_layered_fftqspa` `max_iter=90, damping 1.0, early-stop` (禁用至 V68 授权)；`rescue=verification-only`。
- `leak`: `leak=5*(m1+m2)+64` 其中 `m1,m2` 分别 adapted，`tag` 已含，不重复，V67 不变，**raw_disclosure 不 cap**。
- `verification`: `full-symbol tag s_hat=32*u1_hat+u2_hat compute_tag_64 canonical trunc64` (V64 22/24 PASS)，单64b。
- `budget 地图预冻结`: `≤9 session` 各 `Stage0 8 + S1 256/128 + S2 1024/256`，`TEST` 密封，`m_raw` 由 `VAL CE` 得，但五分流用 raw，不 cap。
- `V64 终态`: `22/24 full-tag PASS 双口径无 discordance`，`H_total 200/206/208 → leak 1144/1174/1184` 单源已固化，多 session 复用。

### 2.2 处理点与物化单点冻结

- `84d62779` 语义：`dimension 1024, bin_width 200ps, pairing nearest double-pointer bin//1024, rule legacy_v1, channels A1/B5, frame_len 256 pairs, BLOCK 1024, period 204800ps floor_div, threshold 40000ps, gate 200ps` — 单点，多 session provenance，各 session 单独物化。
- `TEST` 密封：任何 `TEST/EVAL` 域不计 `CE/m`；`C_ab/P/CE/m` 均 `CAL/VAL` 测，`TEST` 不读。
- **U 5+5 不GE**：`U=32*U1+U2` 自然 5+5，禁 `Gray / V68 2+8/4+6`。

### 2.3 禁止

- 禁改任一冻结量、新增矩阵/标签/prior/阈值/decoder、试 `Δ8` 外 degree/seed 网格、跨 acquisition 拼接凑 `9`、将 `min(1024,ceil)` cap 伪装当通过、将 `+8` 外家族当自适应、将 `TEST` 数据用于 `P/m`、将零重叠仅比 `frame_id`、引 `Gray/V68/MET/protograph/SC`、改 `src/experiments/tools` 任何文件；禁读 `TEST` 统计；**m_raw 不 cap**；禁 `acquisition` 未去重多计；禁按 `CE` 替换预注册；禁 `V68` 码调用；未授 `EXECUTE_AUTH` 前禁 `decode_*`。

## 3. Phase A — 数据角色 (acquisition 去重 ≤9，每类≤3 机械)

### 3.1 角色与零重叠（键为 `(source,session,frame)` + `(source_label, acquisition_id)` 去重）

| 集合 | 每 session 规模 | 说明 |
|---|---|---|
| Stage0 | 8 frames (2048 pairs) | `legacy_v1 物化校验` |
| Stage1 CAL | 256 frames (65536 pairs) | `C_ab → P` |
| Stage1 VAL | 128 frames (32768 pairs) | `CE → m_raw → raw_disclosure → 初分类` |
| Stage2 CAL | 1024 frames (262144 pairs) | `重新独立估计 C_ab/P/λ/CE/m_raw` |
| Stage2 VAL | 256 frames (65536 pairs) | `确认 CE/m_raw → 确认分类` |
| TEST | 密封不读 | `used_test==False` |

- **acquisition 去重**：`v67_data_registry.json` 由 `v55_intake_20260828/pairs/*` 去重得 `sessions[≤9]`，`per_category ≤3` 机械 `acquisition_time` 前 3，不按 `CE/m` 替换，`acquisition_dedup_verified:true`。
- **零重叠**：`Stage0_key∩Stage1_key==∅ && Stage1_key∩Stage2_key==∅ && (Stage0∪Stage1∪Stage2)_key ∩ (V13..V66)_key ==∅`（键 `(source,session,frame)`），`not_cross_spliced:true`。
- **注册表**：`v67_data_registry.json` (`schema v67_data_v1`) 含 `sessions[≤9] {session_id, acquisition_id, source_label, provenance, frames_total, stage0[8], s1_cal[256], s1_val[128], s2_cal[1024], s2_val[256], zero_overlap_verified, acquisition_dedup_verified, frozen, not_sorted_by_CE}`，禁止事后换 session。
- **稀疏**：`total<3` → `EVIDENCE_INCOMPLETE map_sparse_insufficient`；`3≤total≤9` 稀疏地图仍 `COMPLETE` 但 `map_sparse:true`。

### 3.2 数据就绪门

- `total ∈[3,9] && per_category≤3 && acquisition_dedup_verified` 否则 `EVIDENCE_INCOMPLETE`。
- `|Stage0|==8 && |S1_CAL|==256 && |S1_VAL|==128 && |S2_CAL|==1024 && |S2_VAL|==256` 否则 `EVIDENCE_INCOMPLETE`。
- `frame 256` + `U 5+5` 已验，否则 `EVIDENCE_INCOMPLETE`。

## 4. Phase B — 输入合同 strict V56 (U=32*U1+U2 5+5 不GE)

- **合同项**：`dimension 1024, bin 200, pairing nearest bin//1024, legacy_v1, channels A1/B5, U=32*U1+U2 5+5 natural 不GE, frame_start_ps, period 204800, floor_div, mapping legacy_v1, 每帧256` 落 `v67_manifest.json`。
- **权威算法**：`_read_ttbin_timetags → _bin_indices_sorted_for_binwidth → _pairs_from_sorted_bins → 256分组 → legacy_v1 → U1U2` 原样复用，不重写。
- **不GE**：`rg -i "gray|v68" 0 hits` 已验。

## 5. Phase C/D/E — 分阶段估计 (Stage0 8 + Stage1 256/128 + Stage2 1024/256 不重叠重新独立估计，TEST不读)

### 5.1 C_ab 与 P_global (CAL-only per stage per session)

```
C_ab[a,b] = bincount2d(a_cal, b_cal)  1024×1024, sum 65536 (S1) / 262144 (S2)
N_b[b] = Σ_a C_ab
P_global(a) = Σ_b C_ab / N_cal
Q=1024, n=1024
```

### 5.2 层级先验与熵/CE (CAL 描述性 + VAL 门禁性，链式，TEST隔离)

```
P(a|b) = (C_ab + λ P_global(a)) / (N_b + λ)  (N_b>0); P_global(a)  (N_b==0)
P(u1|b) = Σ_{u2} P(32*u1+u2 | b)  32×1024
CE1 = -E_VAL log2 P(U1|B)  (VAL 上 per session)
CE2 = -E_VAL log2 P(U2|U1,B)
CE_full = -E_VAL log2 P(A|B)
CE 链式: |CE_full - CE1 - CE2| <1e-9 else EVIDENCE_INCOMPLETE
m1_raw = ceil(1.3*1024*CE1/5), m2_raw = ceil(1.3*1024*CE2/5)  (不 cap, 显式 raw)
m_total_raw = m1_raw + m2_raw
raw_disclosure = 5*(m1_raw+m2_raw)+64  # 不 cap
```

- **λ 择优**：`λ ∈[1e-2,1e4] log10 连续` 仅 `CAL 内 4-fold` 最小 `CV NLL`，触界则 `MODEL_NOT_STABLE`，不扩网格。
- **Stage2 独立**：`C_ab/P/λ/CE/m_raw` 均独立重算，不复用 S1；`used_test==False` 已验。

## 6. Phase F — 五分流与总体 (per session + overall)

### 6.1 五分流（per session，优先级高→低，互斥）

```
if not materialization_ok or frame_256_violation or CE_chain_not_closed or provenance_fabricated or acquisition_dup_unresolved:
    classification = V67_EVIDENCE_INCOMPLETE; successor = recollect
elif λ_at_boundary or ΔNLL>0.50 or val_b_context_unseen>0.01 or not isfinite(ValNLL) or not isfinite(DeltaNLL):
    classification = V67_MODEL_NOT_STABLE; successor = recollect_or_new_prior
elif m1_raw ≤16 && m2_raw ≤ (LaneC_base +8+8)  # 184→200,190→206,192→208
    classification = V67_CURRENT_CANDIDATE_COMPATIBLE; successor = none
elif m1_raw <1024 && m2_raw <1024 && raw_disclosure <5120
    classification = V67_RATE_ADAPTATION; successor = v68_rate_adaptive
else: # m1_raw≥1024 or m2_raw≥1024 or raw_disclosure≥5120 (≈10240)
    classification = V67_NEAR_FULL_DISCLOSURE; successor = v68_new_representation
```

- `LaneC_base` 按 `source_label`：`1M 184, 1p5M 190, 2M 192`，`+8+8 = +16 → 200/206/208`，`NEAR_FULL` 阈 `≥1024` 单 plane 或 `raw_disclosure≥5120 (10240/2)`。

### 6.2 总体

```
if per session classification 均已落盘 (含 EVIDENCE_INCOMPLETE) && total∈[3,9] && acquisition_dedup_verified:
    overall = V67_FEASIBILITY_MAP_COMPLETE
counts_per_classification = {EVIDENCE_INCOMPLETE, MODEL_NOT_STABLE, CURRENT_CANDIDATE_COMPATIBLE, RATE_ADAPTATION, NEAR_FULL_DISCLOSURE}
candidate_session_list = [session_id for session_id where classification==CURRENT_CANDIDATE_COMPATIBLE]
```

## 7. Phase G — 报告与表 (per session 表含 session/CE/lambda/gap/unseen/m/raw/classification/successor)

- **表 schema** (`v67_feasibility_table.csv/.json` 行对等)：
```
session_id, acquisition_id, source_label, provenance,
S1_CE1, S1_CE2, S1_CE_full, S1_chain_delta, S1_lambda, S1_lambda_at_boundary, S1_DeltaNLL, S1_ValNLL, S1_H_cal, S1_val_b_context_unseen, S1_joint_cell_unseen, S1_q_mass_unseen, S1_descriptive_diagnostics×3 (ValNLL_gt_Hcal_plus_1/0_5/joint_cell_unseen_gt_1pct), S1_capacity_warning_m1/m2/disclosure (m1_raw≥1024/m2_raw≥1024/raw_disclosure≥5120 正交), S1_effective_contexts, S1_m1_raw, S1_m2_raw, S1_raw_disclosure, S1_m1_family, S1_m2_family,
S2_CE1, S2_CE2, S2_CE_full, S2_chain_delta, S2_lambda, S2_lambda_at_boundary, S2_DeltaNLL, S2_ValNLL, S2_H_cal, S2_val_b_context_unseen, S2_joint_cell_unseen, S2_q_mass_unseen, S2_descriptive_diagnostics×3, S2_capacity_warning_m1/m2/disclosure, S2_m1_raw, S2_m2_raw, S2_raw_disclosure, S2_m1_family, S2_m2_family,
final_m1_raw, final_m2_raw, final_raw_disclosure, stage_consistency,
final_classification, successor
```
- **报告** `V67_FEASIBILITY_REPORT.md`：`per session Stage0/Stage1/Stage2 双组 CE/λ/gap/unseen/m/raw/classification/successor/stage_consistency + overall counts + candidate list + map_sparse + acquisition 去重证明 + TEST隔离 + U 5+5不GE + 五分流阈` 与 `json/csv` 一致，不扩大为 `FER/SKR`。

## 8. 守卫 R67-01~10

| 守卫 | 条件 | 阈值 |
|---|---|---|
| R67-01 | acquisition 去重 ≤9 每类≤3 机械不按 CE 替换 | `total≤9 && per_category≤3 && acquisition_dedup_verified && not_sorted_by_CE` |
| R67-02 | Stage0 8 frames 物化 | `\|S0\|==8 && materialization_contract_consistent` |
| R67-03 | Stage1/Stage2 不重叠 + 历史零重叠 | `S0∩S1==∅ && S1∩S2==∅ && (S∪V13..V66)==∅` 键 `(source,session,frame)` |
| R67-04 | 重新独立估计 + TEST不读 | `S2 重算 not reuse S1 && used_test==False` |
| R67-05 | U=32*U1+U2 5+5 不GE V68隔离 | `U1==>>5 && U2==&31 && rg -i "gray\|v68" 0 hits && git diff src==0` |
| R67-06 | 码率 raw 不 cap | `m_raw==ceil(1.3*1024*CE/5) && raw_disclosure==5*(m_raw)+64 && grep "min(1024" 0 hits` |
| R67-07 | 链式 + λ 择优 | `\|CE_full-CE1-CE2\|<1e-9 && λ∈(1e-2,1e4) 4-fold 最小` |
| R67-08 | 五分流互斥优先级 | `classification 按 EVIDENCE>MODEL>COMPATIBLE>RATE>NEAR_FULL 互斥` |
| R67-09 | decoder-free + V68隔离 | `rg "decode_" 0 hits && rg -i "v68\|gray" 0 hits` |
| R67-10 | 不创 run_01 + 编译 + 小测试 | `run_01 不存在 && py_compile PASS && pytest 小测试 PASS` |

## 9. 脚本与证据写出 (预冻结，decoder-free)

- **固定脚本**（本轮）：
  - `scripts/v67_spike.py`: 每 session `Stage0 8 → S1 CAL256/VAL128 → S2 CAL1024/VAL256 独立重算`，输出 `v67_data_registry.json + v67_spike_summary.json + v67_feasibility_table.(csv|json) + v67_manifest.json + V67_FEASIBILITY_REPORT.md`，`rg "decode_" 0 hits`，`rg -i "v68|gray" 0 hits`，`py_compile PASS`，`m_raw` 未 cap，`TEST` 未用，`CE 链式` 已验。
- **证据**：
```
openspec/changes/formal-ir-v67-multisession-feasibility-map/  # 本轮 plan 四工件
scripts/v67_spike.py  # decoder-free
v67_data_registry.json (acquisition 去重 ≤9, 每类≤3)
v67_spike_summary.json (per session S1/S2 CE/λ/m_raw/raw_disclosure)
v67_feasibility_table.csv/.json (per session classification/successor)
V67_FEASIBILITY_REPORT.md
v67_manifest.json (guards R67-01~10)
comparison_bench/outputs_comparison/formal_ir_methods/v67_feasibility_map/  # 未来 run_01 (本轮不建)
```
- **文件**：`v67_data_registry.json` (authoritative `≤9` 实表，`acquisition_dedup_verified`) + `v67_spike_summary.json` + `v67_feasibility_table` (行对等) + `v67_manifest.json` (frozen_body + guards) + `V67_FEASIBILITY_REPORT.md` + 控制台摘要；本轮仅冻结计划，不创建正式 run_01。

## 10. 验收

- **本轮 plan 自检 gate（A-H 已闭合）**：`py_compile PASS` spike，`rg "decode_" 0 hits`，`rg -i "v68|gray" 0 hits`，`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0 && git diff -- openspec/changes/formal-ir-v6[0-6]/ ==0` (除本变更+scripts 外零改)，`TEST` 未读统计已验 (`used_test==False`)，`m_raw` 未 cap 伪装已验 (`grep "min(1024" 0 hits` 且 `m_family +8` 辅助显式)，`acquisition 去重 ≤9 每类≤3 机械不按 CE` 已验，`Stage0 8 / S1 256/128 / S2 1024/256 不重叠重估` 已验，`U 5+5不GE` 已验，`CE 链式 <1e-9` 已验，`五分流优先级互斥` 已验，`capacity_warning_m1/m2/disclosure` 正交旗标与 `descriptive_diagnostics` 已落盘，`overall V67_FEASIBILITY_MAP_COMPLETE` 已验，`run_01` 不存在已验，**报告表与 json 一致**。
- **本轮仅 plan 四工件+registry+spike+报告表**，任何 `V68` 实度量需 `Plan SHA` + `v67_data_registry.json` 实表 + 五分流已验后、且独立 `PLAN_ACCEPT` + `EXECUTE_AUTH` 后才允许创建正式实现并执行；`DECODER_FREE` 保持至授权。
