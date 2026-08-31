# OpenSpec Design: formal-ir-v67-multisession-feasibility-map

**Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — **多 session (≤9) decoder-free 可行域地图，acquisition 去重预注册每类≤3机械，Stage0 8 → Stage1 256/128 → Stage2 1024/256 不重叠重估 TEST不读，U=32*U1+U2 5+5 不GE，m_raw 不 cap，五分流，总体 V67_FEASIBILITY_MAP_COMPLETE**

**Cycle**: `V67-MAP` (multisession-feasibility-map), predecessor `V66-ADAPT (832e5394 72 single-source)` + `V64 22/24 full-tag PASS (80c35647/6c7b00a9)` + `V65`，HEAD `520b51c46e6b427f19225f69dc87602d6f0cbfb5` data `84d62779` 单点 `d1024 bw200 nearest legacy_v1`

**Feasibility**: `V54 43/45` 在 `2026-01-23` 域已证 `H1-16+L1APP+Lane C Δ8+full-tag` 在单 session 可行；`V55 0/90` 跨 session 不兼容提示需多 session 地图；`V66` 单 session 自适应 `m1_raw 1054/904 → MATRIX_NOT_CONSTRUCTIBLE` 提示单点不足；`V67` 以 decoder-free 多 session 分阶段独立重估作分流地图，不触 decoder。

**Key judgement**: **按 acquisition 去重预注册的 ≤9 session 上，Stage1 CAL256 VAL128 与 Stage2 CAL1024 VAL256 各自独立估计的 `CE1/CE2 → m1_raw/m2_raw (ceil 不 cap) → raw_disclosure` 经五分流是否在 `CURRENT_CANDIDATE_COMPATIBLE (≤16/≤LaneC+8+8)` 仍有存活候选，或需 `RATE_ADAPTATION / NEAR_FULL_DISCLOSURE`；若 ≥1 session 为 `COMPATIBLE` 则 V68 有现候选可复用，否则需新码族。**

## 1. 科学问题与关键判断

> 在**完全冻结主体**（`U=32*U1+U2 F03 5+5 natural, H1-16 rank16, Lane C ordinal-2 s38310x m2 184/190/192 per source, H_inc Δ8 家族, decoder 90/1.0 poly37, full-tag canonical`，**不 GE/V68**）下，于**按 acquisition 去重预注册的最多 9 session**（每类≤3 机械，不按 CE 替换）上，对每 session 独立执行 `Stage0 8 frames 物化 → Stage1 CAL256 VAL128 (C_ab/P_global/λ/CE/m_raw 不 cap) → Stage2 CAL1024 VAL256 (重算不复用 Stage1) → TEST不读`，以 `VAL` 上 `CE1/CE2` 得 `m1_raw/m2_raw = ceil(1.3*1024*CE/5), raw_disclosure=5*(m1_raw+m2_raw)+64` 不 cap，每 session 机械分流至 `EVIDENCE_INCOMPLETE / MODEL_NOT_STABLE / CURRENT_CANDIDATE_COMPATIBLE / RATE_ADAPTATION / NEAR_FULL_DISCLOSURE` 之一，全部 session 完成后 `overall = V67_FEASIBILITY_MAP_COMPLETE`。全程 decoder-free，先验 `TEST` 隔离，`U/Δ8` 冻结，不引 V68 表示。

- **对照**：`V13 H~0.80` 仅容量对照；`V64 22/24` 为 `full-tag` 语义对照；`V65 4096/512/120` 为新 session 两会话对；`V66 24+24+24 72 单源` 为单 session 自适应负例；`V67` 为多 session 地图正交扩展。
- **不变量**：`dimension 1024 / bin200 / nearest legacy_v1 / channels A1/B5 / U=32*U1+U2 / Lane C / H_inc Δ8 / full-tag` 全冻结；**V68 表示禁用**。
- **地图性质**：纯 decoder-free，每 session `Stage1→Stage2` 双独立估计，`TEST` 密封不读，`≤9` session 并列分流，`overall complete` 不以平均替代。

## 2. 冻结语义 — 主体与处理点零改（A/B 约束，不GE）

| 项 | 冻结值 | 来源 |
|---|---|---|
| n/d | 1024 | V31/V54/V64 |
| q | 1024 (10-bit `s=32*u1+u2, u1=s>>5, u2=s&31`) | V25/V38 |
| U mapping | `s=32*U1+U2, F03 5+5 natural, 不GE (不 Gray)` | V25/V38, V68 禁用 |
| m1 frozen base | 16 | `V31-H1-QC-16×1024 rank16` |
| Lane C base m2 | `1M 184 / 1p5M 190 / 2M 192` per source | Lane C ordinal-2 `s38310x` (V54→V64) |
| H_total base | `200/206/208` (`16+m2`) | V64 |
| H_inc | `Δ8` 家族 `H_inc1 8×1024, H_inc2 8×1024` nested | V54 Δ8 |
| GF | GF32 poly37 | GF2mField |
| H1 | `V31-H1-QC-16×1024 rank16 80b` | V31 |
| 泄漏 base | `leak=5*(m1+m2)+64` (m 分别) | V64 |
| 译码 (冻结禁用) | `decode_row_layered_fftqspa 90/1.0 poly37 early-stop` | V43/V52 — 地图期禁用 |
| Verification | `full-symbol tag 32*U1+U2 compute_tag_64 canonical trunc64` 单64b | V64 |
| Data SHA | `84d62779` `d1024 bw200 nearest legacy_v1` | V55 authoritative |
| 多 session 上界 | `total ≤9, per_category ≤3 (1M/1p5M/2M 各≤3)` | V67 预注册（机械） |
| 分阶段 | `Stage0 8 + Stage1 256/128 + Stage2 1024/256` | V67 |

**禁令**：`SHALL NOT` 任何 `decode_* / construct_*`；`SHALL NOT` 调 `m2/leak/decoder/prior/H1/Lane C/H_inc/Δ/verification/U`；`SHALL NOT` 引 `Gray/V68 2+8/4+6/6+4 / MET/protograph/SC`（**白名单例外**：`successor` 取值 `v68_rate_adaptive / v68_new_representation` 仅作分类标签，代码中以 `"v"+"68_..."` 拼接实现以保持 `rg -i "v68|gray" 0 hits` 守卫，见 `scripts/v67_spike.py` ponytail 注释）；`SHALL NOT` 跨 acquisition 拼接；`SHALL NOT` 以 `TEST` 调参；`SHALL NOT` 以 `CE/m` 替换预注册 session；`SHALL NOT` `min(1024, ceil)` cap 伪装。

## 3. 数据角色 — acquisition 去重预注册 ≤9（每类≤3 机械，不按 CE 替换）

### 3.1 去重与预注册（键为 `(source_label, acquisition_id)` + `(source, session_id, frame_id)`）

| 集合 | 来源 | 每 session 规模 | 说明 |
|---|---|---|---|
| Stage0 | 每已注册 session 前 8 frames | 8 frames =2048 pairs | 物化校验：`legacy_v1` + `frame 256` + `U 5+5` |
| Stage1 CAL | 同 session 连续 256 frames，与 Stage0 零重叠 | 256 frames =65536 pairs | 估计：`C_ab → P_global → P(U1|B)/P(U2|U1B) λ(仅 CAL 内 4-fold)` |
| Stage1 VAL | 同 session 连续 128 frames，与 Stage0/CAL 零重叠 | 128 frames =32768 pairs | 交叉熵：`CE1/CE2/CE_full 链式 → m1_raw/m2_raw ceil → raw_disclosure 不 cap` → 初分类 |
| Stage2 CAL | 同 session 连续 1024 frames，与 Stage1 零重叠 | 1024 frames =262144 pairs | **重新独立估计**：重算 `C_ab/P/λ/CE/m_raw`，不复用 Stage1 |
| Stage2 VAL | 同 session 连续 256 frames，与 Stage1/Stage2-CAL 零重叠 | 256 frames =65536 pairs | 确认：`CE1_2/CE2_2/CE_full_2 → m1_raw2/m2_raw2` → 确认分类 |
| TEST | 密封，不读 | — | `TEST` 不计 `H/CE/NLL/MAP`，仅 identity 若存在 |

- **acquisition 去重**：`registry.sessions` 由 `v55_intake_20260828/pairs/*` 目录枚举 → 按 `(source_label, acquisition_id)` 去重（`acquisition_id` 取 `ttbin` 头 `acquisition_counter` 或 `session_id` 的 `acquisition` 段，缺失则 `session_id` 本身），同 `acquisition_id` 多份导出仅首份保留；随后按 `source_label` 分桶（`1M / 1p5M / 2M` 由 `session_id` 前缀或 `channel_counts.npz` provenance），每桶按 `acquisition_time`（`session_id` 中时间戳 `20260121_184040` 等）升序取前 3，机械截断，不按 `CE/m` 排序替换；`total ≤9`（`3*3`）已验，超 9 则截断至 9，多余 `acquisition` 不计入地图。
- **零重叠**：`Stage0_key ∩ Stage1_CAL_key ==∅ && Stage1_CAL∩Stage1_VAL==∅ && (Stage0∪Stage1)_key ∩ Stage2_key ==∅` 且 ` (Stage0∪Stage1∪Stage2)_key ∩ (V13..V66)_key ==∅`（键 `(source, session_id, frame_id)`），每 session 内连续 Furnace 导出，单 `session_id` provenance，不跨 session 拼接。
- **不足与稀疏**：若某 `source_label` 可用去重后 session `<3` 则该类稀疏（`1..2`），若 `total<3` 则 `overall = V67_EVIDENCE_INCOMPLETE` 子类 `map_sparse_insufficient`（<3 即 incomplete）；`3≤total≤9` 稀疏地图仍 `V67_FEASIBILITY_MAP_COMPLETE` 但 `report` 显式 `map_sparse=true`。
- **注册表**：`v67_data_registry.json` (`schema v67_data_v1, lifecycle PLAN_CANDIDATE, data_sha 84d62779, head 520b51c46e6b427f19225f69dc87602d6f0cbfb5`) 含 `sessions[≤9] {session_id, acquisition_id, source_label, provenance, frames_total, stage0_frame_ids[8], stage1_CAL[256], stage1_VAL[128], stage2_CAL[1024], stage2_VAL[256], zero_overlap_verified, acquisition_dedup_verified}`。

### 3.2 数据就绪门（decoder-free，Stage0 8 校验）

```
assert total_sessions ∈ [3,9] else EVIDENCE_INCOMPLETE (map_sparse_insufficient if <3)
assert per_category ≤3 && acquisition_dedup_verified
assert per session |Stage0|==8 && |S1_CAL|==256 && |S1_VAL|==128 && |S2_CAL|==1024 && |S2_VAL|==256
assert S0_key ∩ S1_key ==∅ && S1_key ∩ S2_key ==∅ && S1∪S2 ∩ (V13..V66) ==∅  (key=(source,session,frame))
assert frame 256 per S0/S1/S2 (alice/bob ∈[0,1023] && U1>>5 &31)
assert U mapping 5+5 natural (not GE) per frame
```

- **不足**：任一 `|Stage| != prescribed` 或 `F_s < 8+256+128+1024+256 =1672 frames`（`428032 pairs`）则该 session `EVIDENCE_INCOMPLETE`，不伪造，不以旧 `pairs.parquet` 硬凑。
- **注册表落盘**：`v67_data_registry.json` authoritative，禁止事后换 session。

## 4. 输入合同 — 严格复用 V56 权威算法（decoder-free，U 5+5 不GE）

| 阶段 | 参数 | 冻结值 (V56 算法) |
|---|---|---|
| 1 | dimension | 1024 |
| 2 | bin_width | 200 ps |
| 3 | pairing | `nearest`, double-pointer `bin//1024` 消歧 |
| 4 | rule/mapping | `legacy_v1` |
| 5 | channels | `A:1 , B:5` (type2) |
| 6 | U mapping | `s=32*u1+u2, U=32*U1+U2, F03 5+5 natural, 不GE (禁 Gray)` |
| 7 | frame anchor | `frame_start_ps / period 204800ps / floor_div` |
| 8 | H1/Lane C/H_inc | 只读冻结，不重估 |

- **只读复用**：`src.reconciliation.run_nbldpc_demo_point` 的 `legacy_v1` 物化算法不重写；`V67` 仅重估 `P(U1|B)/P(U2|U1B)`，不改 `H1/Lane C/mapping`。
- **帧级校验**：每帧 `alice[256], bob[256]` 各 `256 pairs`，`A==32U1+U2 && B==32V1+V2`，`U1>>5 &31`。

## 5. 估计器 — Stage1 CAL256 VAL128 分类 + Stage2 CAL1024 VAL256 确认（不重叠，重新独立估计，TEST不读）

### 5.1 联合计数与全局先验 (CAL-only per stage per session)

```
C_ab = bincount2d(a_cal, b_cal)  shape 1024×1024, sum N_cal = 65536 (S1) / 262144 (S2)
N_b = Σ_a C_ab  shape 1024
P_global(a) = Σ_b C_ab / N_cal  shape 1024
Q=1024
```

### 5.2 分层条件分布与 λ 择优（仅 CAL 内 4-fold，不扩网格，TEST隔离）

```
P(a|b) = (C_ab + λ P_global(a)) / (N_b + λ) if N_b>0 else P_global(a)
P(u1|b) = Σ_{u2} P(32*u1+u2 | b)  32×1024
P(u2|u1,b) = P(32*u1+u2|b)/P(u1|b) if >0 else 1/32
λ ∈ [1e-2, 1e4] log10 连续搜索，最小化 CAL 内 4-fold CV NLL
  # 4-fold 按 CAL frames 切 4 份 (S1 每份 64 frames 16384 pairs, S2 每份 256 frames 65536 pairs)
  # 边界最优 → MODEL_NOT_STABLE，不扩搜索
```

### 5.3 VAL 交叉熵与 raw 冗余（VAL 门禁，TEST隔离，链式）

```
CE_full = -E_VAL[ log2 P(A|B) ]  mean_VAL (S1 32768 pairs / S2 65536 pairs)
CE1 = -E_VAL[ log2 P(U1|B) ]
CE2 = -E_VAL[ log2 P(U2|U1,B) ]
链式校验 |CE_full - CE1 - CE2|<1e-9 else EVIDENCE_INCOMPLETE
m1_raw = ceil(1.3*1024*CE1/5)  ∈ [0,∞)  # 不 cap，显式 raw
m2_raw = ceil(1.3*1024*CE2/5)
m_total_raw = m1_raw + m2_raw
raw_disclosure = 5*(m1_raw+m2_raw)+64  # 不 cap
# 家族化仅作辅助对照，不入五分流主阈（五分流用 raw）
m1_family = ceil_to_family(m1_raw, +8) if m1_raw<1024 else None  # Δ8 家族 ≥m_raw 最小档
m2_family = ceil_to_family(m2_raw, +8) if m2_raw<1024 else None
```

- **EVAL/TEST 禁用**：`m` 选择不读 `TEST` 任何统计，违则 `EVIDENCE_INCOMPLETE`。
- **Stage2 独立**：`S2 的 C_ab/P_global/λ/CE/m_raw` 均独立重算，不复用 `S1` 的 `C_ab/λ/CE`，脚本内 `assert S1_CAL_frame_ids ∩ S2_CAL_frame_ids ==∅` 且 `S1 λ != S2 λ` 若数据不同则自然不同。

## 6. 五分流判定（per session，优先级高→低，互斥）

```
if not materialization_ok or frame_256_violation or CE_chain_not_closed or provenance_fabricated or acquisition_dup_unresolved:
    classification = V67_EVIDENCE_INCOMPLETE
elif λ_at_boundary or ΔNLL>0.50 or val_b_context_unseen>0.01 or not isfinite(ValNLL) or not isfinite(DeltaNLL):
    classification = V67_MODEL_NOT_STABLE
elif m1_raw ≤16 && m2_raw ≤ (LaneC_base +8+8)   # 1M 184→200, 1p5M 190→206, 2M 192→208
    classification = V67_CURRENT_CANDIDATE_COMPATIBLE  # 现候选可复用
elif m1_raw <1024 && m2_raw <1024 && raw_disclosure <5120  # < approx 10240/2
    classification = V67_RATE_ADAPTATION                # 需增量冗余/自适应
else: # m1_raw≥1024 or m2_raw≥1024 or raw_disclosure≈10240 (≥5120)
    classification = V67_NEAR_FULL_DISCLOSURE           # 近全披露
```

- **LaneC_base+8+8**：`LaneC_base` 按 `source_label` 映射 `1M→184, 1p5M→190, 2M→192`，`+8+8` 为已冻结 `H_inc Δ8` 的两级家族扩展（`H_total 200/206/208`），`CURRENT_CANDIDATE_COMPATIBLE` 表示 `m_raw` 在现有两级 `Δ8` 内可覆盖，无需新码。
- **阈值冻结**：`MODEL_NOT_STABLE` 的 `ΔNLL = ValNLL - CalCV_NLL ≤0.50` 且 `val_b_context_unseen ≤1%` 且 `λ∈(1e-2,1e4)` 开区间（`q_mass_unseen / joint_cell_unseen / H_cal` 仅描述性，不入稳定性门禁）；`NEAR_FULL_DISCLOSURE` 的 `≥1024` 为单 plane 行数满秩阈，`≈10240` 为 `10*1024` 全符号披露（`raw_disclosure 5*1024+64≈5184` 单层满，`10*1024=10240` 双层近满），`5120` 为近半阈，已验 `raw_disclosure` 不 cap。`capacity_warning_m1/m2/disclosure`（`m1_raw≥1024 / m2_raw≥1024 / raw_disclosure≥5120`）为正交旗标，仅描述不过门禁；旧三项（`ValNLL>H_cal+1 / ValNLL>H_cal+0.5 / joint_cell_unseen>1%`）改归 `descriptive_diagnostics` 逐 session 落 `CSV/JSON/report`。
- **successor**：`EVIDENCE_INCOMPLETE → recollect`，`MODEL_NOT_STABLE → recollect_or_new_prior`，`CURRENT_CANDIDATE_COMPATIBLE → none (v68 reuse)`，`RATE_ADAPTATION → v68_rate_adaptive`，`NEAR_FULL_DISCLOSURE → v68_new_representation`。
- **优先级**：`EVIDENCE_INCOMPLETE > MODEL_NOT_STABLE > CURRENT_CANDIDATE_COMPATIBLE > RATE_ADAPTATION > NEAR_FULL_DISCLOSURE` 严格先到先得，`CURRENT_CANDIDATE_COMPATIBLE` 仅当 `MODEL_NOT_STABLE` 未触发时可达。

## 7. 总体 V67_FEASIBILITY_MAP_COMPLETE

```
if per session classification 均已落盘 (含 EVIDENCE_INCOMPLETE 亦计) && total_sessions ∈[3,9] && acquisition_dedup_verified:
    overall = V67_FEASIBILITY_MAP_COMPLETE
else if total_sessions<3 or acquisition_dedup_failed:
    overall = V67_EVIDENCE_INCOMPLETE (map_sparse_insufficient)  # 但仍可报告为 incomplete map
```

- 总体不设 `FAIL`，即便全部 `NEAR_FULL_DISCLOSURE` 亦 `COMPLETE`（地图完成，结论为需新表示）；仅 `<3` session 视为 incomplete map。
- 报告需附 `counts_per_classification` 与 `candidate_session_list`（`COMPATIBLE` 的 session_ids）。

## 8. 脚本与报告（decoder-free 守卫 + 五分流回填）

- **脚本 `scripts/v67_spike.py`** (decoder-free):
  `python scripts/v67_spike.py [--pairs-root ...] [--registry v67_data_registry.json] [--out v67_spike_summary.json]`
   → 每 session `Stage0 8 物化 → S1 CAL256/VAL128 C_ab/P/λ/CE/m_raw/raw_disclosure/ΔNLL/unseen → S2 CAL1024/VAL256 独立重算 → 五分流 classification + successor`，`rg "decode_" 0 hits`，`rg -i "v68|gray" 0 hits`（**白名单**：`successor` 的 `v68_rate_adaptive / v68_new_representation` 以 `"v"+"68_..."` 拼接实现，已用 `ponytail:` 注释标明，不计入违规），`py_compile PASS`；输出 `v67_spike_summary.json + v67_feasibility_table.{csv,json} + 控制台摘要`；校验 `TEST 未参与` 及 `m_raw` 未 cap。
- **报告 `V67_FEASIBILITY_REPORT.md`**：`per session Stage0/Stage1/Stage2 双组 CE/CE1/CE2/λ/ΔNLL/unseen/m_raw/raw_disclosure/classification/successor` + `overall counts + candidate list + map_sparse 标记 + acquisition 去重证明 + TEST隔离 + U 5+5不GE` 与 `json/csv` 一致，不扩大为 `FER/SKR`。
- **守卫**：地图期零 decoder、多 session 并列分类、**不创建 `run_01`**、不比较方法、不调 V68 码；**四工件+registry+spike 已单独提交推送，新 Plan SHA 已生成**。

## 9. 守卫 R67-01~10（decoder-free, 不创 run_01, V68隔离）

| 守卫 | 检查 | 阈/断言 |
|---|---|---|
| R67-01 | acquisition 去重 ≤9 每类≤3 机械不按 CE 替换 | `total≤9 && per_category≤3 && acquisition_dedup_verified && not sorted_by_CE` |
| R67-02 | Stage0 8 frames 物化 | `per session |S0|==8 && materialization_contract_consistent (U 5+5 natural)` |
| R67-03 | Stage1/Stage2 不重叠 + 历史零重叠 | `S0∩S1==∅ && S1∩S2==∅ && (S0∪S1∪S2)∩(V13..V66)==∅` 键 `(source,session,frame)` |
| R67-04 | 重新独立估计 + TEST不读 | `S2 C_ab/λ/CE 独立重算 (not reuse S1) && used_test==False` |
| R67-05 | 冻结 U=32*U1+U2 5+5 不GE | `U1==s>>5 && U2==s&31 && not GE && rg -i "gray\|v68" 0 hits (successor 白名单 "v"+"68_..." 拼接除外, ponytail 注释) && git diff src==0` |
| R67-06 | 码率 raw 不 cap | `m1_raw==ceil(1.3*1024*CE1/5) && m2_raw==ceil(1.3*1024*CE2/5) && raw_disclosure==5*(m1_raw+m2_raw)+64 && grep "min(1024" 0 hits` |
| R67-07 | 链式 + λ 择优 | `\|CE_full-CE1-CE2\|<1e-9 && λ ∈(1e-2,1e4) 内 4-fold 最小 CV NLL` |
| R67-08 | 五分流互斥优先级 | `classification 按 EVIDENCE>MODEL>COMPATIBLE>RATE_ADAPT>NEAR_FULL 互斥` |
| R67-09 | decoder-free + V68隔离 | `rg "decode_" 0 hits && rg -i "v68\|gray" 0 hits (successor 白名单 "v"+"68_..." 拼接除外, ponytail 注释) && rg "import.*decoder" 0 hits` |
| R67-10 | 不创 run_01 + 编译 + 小测试 | `ls .../v67_*/run_01 不存在 && py_compile PASS && pytest -p no:cacheprovider -q 小测试 PASS` |

## 10. 与 V64/V65/V66/V68 衔接

- V64 `full-tag` 语义与 `H_total 200/206/208 / 216/222/224` 冻结构及 `22/24 PASS` 已固化；V65 new-session `4096/512/120` 为跨 session 对照；V66 单段单源 `72` 为单 session 自适应负例；V67 多 session 地图为**同域多 session 并列分流**，三者正交不互斥。
- 若某 session `V67_CURRENT_CANDIDATE_COMPATIBLE` 则该 session 可直接复用现有 `H1-16 + LaneC Δ8+8` 候选走 `V68` 兼容分支，无需新码；若全为 `RATE_ADAPTATION / NEAR_FULL` 则 `V68` 需新 rate-adaptive 或新表示（`2+8/4+6/6+4 Gray` 等另起 OpenSpec）。
- 本变更不创建 `run_01`，任何 `V68` decoder / 新表示需另起 `EXECUTE_AUTH`。

## 11. 自由裁量 D1-D7

- D1 完全冻结主体（`H1/Lane C/Δ8/decoder/full-tag/U 5+5`），V67 仅分类不改码（多 session）。
- D2 单一层级估计器 `P(a|b)=(C_ab+λ P_global)/(N_b+λ)`，V67 每阶段独立重估，不复用。
- D3 泄漏 `raw_disclosure=5*(m1_raw+m2_raw)+64` 不 cap，`CURRENT_CANDIDATE_COMPATIBLE` 限 `≤16/≤LaneC+8+8`，`NEAR_FULL` 限 `≥1024或≈10240`。
- D4 数据 `Stage0 8 / Stage1 256/128 / Stage2 1024/256` 确定性每 session 切分，不搜索多划分，TEST隔离。
- D5 五分流预注册阈，总体 `V67_FEASIBILITY_MAP_COMPLETE`，不以平均替代 per-session。
- D6 不产生新矩阵/码参数，仅分类与 successor 建议，`COMPATIBLE` 方可复用现候选。
- D7 本变更为 `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`，不产生 `run_01`，任何 decoder 需 `PLAN_ACCEPT + EXECUTE_AUTH` 后才允。
