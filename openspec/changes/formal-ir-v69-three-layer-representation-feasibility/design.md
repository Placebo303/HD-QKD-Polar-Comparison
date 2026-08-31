# OpenSpec Design: formal-ir-v69-three-layer-representation-feasibility

**Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — **1024维符号三层有序 `w∈[2,5]` 重划分，`3^10=59049→37170` 枚举去重，按升序唯一词典序 `max_util→disclosure→ΔNLL→lex` 选 `P*`，Phase A CAL-only Phase B VAL确认 per-layer `VAL-CAL≤0.5` + `unseen≤1%` + `chain 1e-9` + `m<1024`，V67三Session Stage2 复用，per-session 5分流 + 总体5态 + common三 session 同 assignment 审计，不跑decoder不构矩阵不启V70**

**Cycle**: `V69-3L` (three-layer-representation-feasibility), predecessor `V68-BAL (fcf3e457ecf45c58e23f91d750acd5267d541795)` + `V67-MAP (V67_FEASIBILITY_MAP_ACCEPTED 3× NEAR_FULL)` + `V64 22/24 PASS`, HEAD `fcf3e457ecf45c58e23f91d750acd5267d541795` data `84d62779` 单点 `d1024 bw200 nearest legacy_v1`

**Feasibility**: `V67` 3 sessions 上 `natural 5+5` 均 `m1_raw≥1024` 证 `NEAR_FULL`，`V68` 252 均衡 `5+5` 地图待验证，`V69` 假设**三层 `w∈[2,5]` 有序非空划分**可在 `CE` 维度拆散 `H(U1|B)+H(U2|U1,B)+H(U3|U1,U2,B)` 使每层 `m_i<1024` 的概率高于二层，需 decoder-free 验证 `∃P: ∀i m_i<1024` 且 `common` 三 session 同 assignment。

**Key judgement**: **在 V67 三 session 的 `Stage2 CAL1024/VAL256` 上，仅重标记 10 bits 的三层有序 partition `P=(S1,S2,S3)`（`59049→37170` 种，`w_i∈[2,5]`），是否存在 CAL-only 选优的 `P*` 使 `VAL` 上 `∀i m_i_raw(P*)<1024` 且 per-layer `|CE_i^{VAL}-CE_i^{CAL-CV}|≤0.5` 且 `unseen≤1%` 且链式 `<1e-9`，且 common `P*_common` 三 session 同 assignment 均可行；若存在则 V67 imbalance 可被三层表示纠正，否则需更深非比特划分。**

## 1. 科学问题与关键判断

> 在**完全冻结主体**（`n1024 q1024 GF32 poly37 H1-16 Lane C 184/190/192 H_inc Δ8 decoder 90/1.0 full-tag canonical, leak Σ w_i·m_i+64`，**不改1024维符号/q/GF/两层验证码**）下，**仅重划分 10-bit 符号为三层有序非空 `w_i∈[2,5]`**：对 `B={0..9}` 的全部 `3^10=59049` 个分配 `assign: B→{1,2,3}` 去重统计后过滤 `w_i=|{j:assign[j]=i}|∈[2,5]` 且 `Σw_i=10` 且 `S_i≠∅` 得 **37170** 有效有序三层划分 `P=(S1,S2,S3)` 定义 `U_i=bits_{S_i}(s)`（`w_i` bits, `0..2^{w_i}-1`），每 `P` 在 `CAL1024` 上估 `P(U1|B)/P(U2|U1,B)/P(U3|U1,U2,B)`（`λ` 仅 CAL 4-fold），在 `VAL256` 上计量 `CE1/CE2/CE3 → m_i_raw ceil不cap`，链式 `|CE_full-ΣCE_i|<1e-9`，per-layer `|CE_i^{VAL}-CE_i^{CAL-CV}|≤0.5` + `unseen≤1%` + `m_i<1024` 门禁，以升序唯一词典序 `max_util→disclosure→ΔNLL→lex` 选 `P*`，`Phase A CAL-only` 不读 VAL/TEST，`Phase B VAL` 确认，复用 V67 三 Session Stage2，每 session 5分流 `EVIDENCE_INCOMPLETE/MODEL_NOT_STABLE/THREE_LAYER_FEASIBLE/PARTIAL_FEASIBLE/STILL_HEAVY` + 总体5态 + `common P*_common 三 session 同 assignment` 审计。全程 decoder-free，不构矩阵，不启 V70。

- **对照**：`V67 natural` + `V68 5+5 均衡` 的 `m1/m2` 不均衡基线；`V69` 以 `ΔCE/Δm/Δmax_util` 与 dedup_stats 显式对照。
- **不变量**：`dimension 1024 / bin200 / nearest legacy_v1 / channels A1/B5 / GF32 / Lane C / H_inc Δ8 / full-tag` 全冻结；**本变更仅 `P` 重标记**。
- **地图性质**：纯 decoder-free，`3^10→37170` 枚举 + 去重统计 + 唯一词典序选优 + CAL-only/VAL-confirm 两阶段，`TEST` 密封不读，V67 三 session 并列分流 + common 同 assignment 审计，不启 V70。

## 2. 冻结语义 — 主体与处理点零改（1024维三层重标记，不重构）

| 项 | 冻结值 | 来源 |
|---|---|---|
| n/d | 1024 | V31/V54/V64 |
| q | 1024 (10-bit `s ∈[0,1023]`) | V25/V38 |
| GF | GF32 poly37 | GF2mField |
| U 自然 (二层参照) | `U1_nat=s>>5, U2_nat=s&31, F03 5+5` | V25/V67 |
| U 三层重划分 (本变更) | `P=(S1,S2,S3), B={0..9}=S1⊔S2⊔S3, w_i=|S_i|∈[2,5], Σw_i=10, S_i≠∅, 有序, C=37170 ⊂ 3^10=59049` 仅重标记 | V69 |
| m1 base | 16 | V31 H1 |
| Lane C base m2 | `1M 184 / 1p5M 190 / 2M 192` | V54→V64 |
| H_total base | `200/206/208` | V64 |
| H_inc | `Δ8` 家族 nested | V54 |
| decoder (冻结禁用) | `90/1.0 poly37 early-stop` | V43 — 地图期禁用 |
| Verification | `full-symbol tag 32*U1+U2 canonical 64b` (三层 tag 仅描述性) | V64 — 禁用期仍冻结 |
| Data SHA | `84d62779` `d1024 bw200 nearest legacy_v1` | V55 |
| 多 session 复用 | `V67 3 sessions Stage2 CAL1024+VAL256` 原样 | V67 `v67_data_registry.json` |
| 分阶段 | `Phase A CAL-only 选 P* → Phase B VAL256 确认 per-layer ≤0.5 + unseen≤1% + chain 1e-9` | V69 |
| V70 | **禁止启动** — 任何 V70 预冻结/run_01 禁止 | V69 |

**禁令**：`SHALL NOT` 任何 `decode_* / construct_* / gf_rank / nested`；`SHALL NOT` 调 `m2/leak/decoder/prior/H1/Lane C/H_inc/verification`；`SHALL NOT` 引 `MET/protograph/SC/Gray`（除 `P` 纯比特三层重划分注释）；`SHALL NOT` 跨 acquisition 拼接；`SHALL NOT` 以 `VAL/TEST` 调 `P*`；`SHALL NOT` `min(1024,ceil)` cap；`SHALL NOT` 剪枝至 `<37170`（除 `w∈[2,5]` 硬过滤）；`SHALL NOT` 启动 V70；`SHALL NOT` 读 TEST。

## 3. 数据角色 — V67 三预注册 Stage2 复用（每类≤3 机械已验）

### 3.1 复用与零重叠（键 `(source,session,frame)` + `(source_label, acquisition_id)`）

| 集合 | 每 session 规模 | 来源 | 说明 |
|---|---|---|---|
| Stage2 CAL (Phase A 用) | 1024 frames =262144 pairs | `v67_data_registry: stage2_CAL[1024]` | `C_ab → P_global → P(U1|B)/P(U2|U1,B)/P(U3|U1,U2,B) λ(CAL 4-fold)` per `P` |
| Stage2 VAL (Phase B 用) | 256 frames =65536 pairs | `v67_data_registry: stage2_VAL[256]` | `CE1/CE2/CE3/CE_full 链式 → m_i_raw ceil → raw_disclosure + per-layer VAL-CAL + unseen` per `P` |
| TEST | 密封不读 | `V65 TEST 120 / V66 EVAL 24` | `used_test==False`，V69 不读，V70 亦不启 |

- **复用**：`v69_data_registry.json` 由 `v67_data_registry.json` 的 3 sessions (`20260123_1M_600k_0dB 1M, 20260107_PPLN_1p5M 1p5M, 20260123_2M_1p2M_0dB 2M`) 的 `stage2_CAL[1024] + stage2_VAL[256]` 原样拷贝（`total 3, per_category 1,1,1, acquisition_dedup_verified, frozen, not_sorted_by_CE`），`zero_overlap_verified` 与 `V13..V68` 零重叠已验，禁止事后换 session 或按 `CE/m` 替换。
- **不重估计 V67/V68**：V67/V68 的 `CE/m` 仅引用对照，不在 V69 上重算；V69 仅在新三层 `P` 上重估。
- **注册表**：`v69_data_registry.json` (`schema v69_data_v1, lifecycle PLAN_CANDIDATE, data_sha 84d62779, head fcf3e457ecf45c58e23f91d750acd5267d541795, reused_from v67, successor V70_not_started`) 含 `sessions[3] {session_id, acquisition_id, source_label, provenance, stage2_CAL[1024], stage2_VAL[256], zero_overlap_verified, acquisition_dedup_verified}`。

### 3.2 数据就绪门（decoder-free）

```
assert total_sessions==3 && per_category 1,1,1 && acquisition_dedup_verified
assert per session |CAL|==1024 && |VAL|==256 && CAL∩VAL==∅ (key=(source,session,frame))
assert CAL∪VAL ∩ (V13..V68) ==∅
assert frame 256 && s∈[0,1023] && natural U check 32*U1+U2 (二层) 仍成立
assert successor_v70_not_started == true
```

## 4. 输入合同 — 严格复用 V56 权威算法（仅新增 P 三层重标记）

| 阶段 | 参数 | 冻结值 |
|---|---|---|
| 1 | dimension | 1024 |
| 2 | bin_width | 200 ps |
| 3 | pairing | `nearest`, double-pointer `bin//1024` |
| 4 | rule/mapping | `legacy_v1` |
| 5 | channels | `A:1 , B:5` |
| 6 | U 自然 (参照) | `s=32*u1+u2, U=32*U1+U2, F03 5+5` (参照) |
| 7 | U 三层重划分 | `P=(S1,S2,S3), B={0..9}→{1,2,3}, w_i∈[2,5], Σw_i=10, S_i≠∅, 37170种, U_i=bits_{S_i}(s)` |
| 8 | frame anchor | `frame_start_ps / period 204800ps / floor_div` |
| 9 | H1/Lane C | 只读冻结 |

## 5. 估计器 — 枚举 `3^10→37170` × 层级先验 + 唯一词典序选优（Phase A CAL-only / Phase B VAL确认 per-layer ≤0.5）

### 5.1 联合计数与全局先验 (CAL-only per P per session)

```
C_ab = bincount2d(a_cal, b_cal)  shape 1024×1024, sum N_cal=262144
N_b = Σ_a C_ab  shape 1024
P_global(a) = Σ_b C_ab / N_cal
Q=1024
# per P: 将 a 分解为 (u1,u2,u3) 查表，w_i=|S_i|，不改 C_ab，仅改 P(U_i|…) 汇总维度
# dedup_stats: 3^10=59049 全枚举按 w pattern 12类计数，过滤后 37170 有效（见 §5.4 表）
```

### 5.2 分层条件分布与 λ 择优（仅 CAL 内 4-fold，不扩，TEST隔离，三层）

```
P(a|b) = (C_ab + λ P_global(a)) / (N_b + λ) if N_b>0 else P_global(a)
# per P=(S1,S2,S3), w1,w2,w3:
P(u1|b) = Σ_{u2,u3} P( perm_P^{-1}(u1,u2,u3) | b )   # 2^{w1} ×1024
P(u2|u1,b) = Σ_{u3} P(u2,u3|u1,b)  # 2^{w2} × …
P(u3|u1,u2,b) = P(a|b)/P(u1|b)/P(u2|u1,b) if >0 else 1/2^{w3}
λ ∈ [1e-2, 1e4] log10 连续搜索，最小化 CAL 内 4-fold CV NLL (每 fold 256 frames 65536 pairs)
  边界最优 → MODEL_NOT_STABLE，不扩
```

### 5.3 VAL 交叉熵与 raw 冗余（三层，VAL 确认，TEST隔离，链式，per-layer VAL-CAL 门禁）

```
CE_full(P) = -E_VAL[ log2 P( A | B ) ]  (与 P 无关，恒值，但每 P 的分解链式校验)
CE1(P) = -E_VAL[ log2 P( U1(P) | B ) ]
CE2(P) = -E_VAL[ log2 P( U2(P) | U1(P), B ) ]
CE3(P) = -E_VAL[ log2 P( U3(P) | U1(P),U2(P), B ) ]
链式校验 |CE_full - CE1(P) - CE2(P) - CE3(P)|<1e-9 else EVIDENCE_INCOMPLETE (per P)
m1_raw(P) = ceil(1.3*1024*CE1(P)/w1)  ∈ [0,∞)  # 不 cap
m2_raw(P) = ceil(1.3*1024*CE2(P)/w2)
m3_raw(P) = ceil(1.3*1024*CE3(P)/w3)
raw_disclosure(P) = w1*m1_raw + w2*m2_raw + w3*m3_raw + 64  # 不 cap, +64 tag

# CAL-CV 上同算法得 CE1_cv/CE2_cv/CE3_cv 供 per-layer VAL-CAL 门禁：
ΔCE_i = |CE_i^{VAL} - CE_i^{CAL-CV}|
ΔNLL_i = ValNLL_i - CV_NLL_i  (per-layer NLL)
门禁：∀i ΔCE_i ≤0.5 且 ΔNLL_i ≤0.50 且 val_b_context_unseen ≤1%
```

- **EVAL/TEST 禁用**：`P*` 选择不读 `VAL`/`TEST` 统计，Phase A 仅 CAL，违则 `EVIDENCE_INCOMPLETE`。
- **Phase B 独立**：`VAL` 上 `CE/m_raw` 仅度量，不重选 `P*`，`P*_common` 亦 CAL-only 选后 VAL 度量 per-layer 门禁。
- **V70 隔离**：任何 V70 `QUALIFICATION_PLAN_READY` 禁止在本 Phase 启动。

### 5.4 去重统计与 `w∈[2,5]` 过滤（`3^10` 全搜索 → `37170` 有效）

```
raw_space = 3^10 = 59049  # B→{1,2,3} 全分配，含空层或 w∉[2,5]
# 过滤：w_i = #{j: assign[j]=i} 需 2≤w_i≤5 且 Σw_i=10 且 S_i≠∅
valid = 37170
# 12种 w pattern 去重分表：
# (2,3,5):2520  (2,4,4):3150  (2,5,3):2520
# (3,2,5):2520  (3,3,4):4200  (3,4,3):4200  (3,5,2):2520
# (4,2,4):3150  (4,3,3):4200  (4,4,2):3150
# (5,2,3):2520  (5,3,2):2520  → sum 37170
# 落盘 dedup_stats: {raw 59049, valid 37170, per_pattern[12], empty_filtered, width_filtered}
```

### 5.5 升序唯一词典序目标（`max_util→disclosure→ΔNLL→lexicographic`，含 common 三 session 同 assignment）

```
max_util(P) = max_i( m_i_raw(P)/1024 )  # 或等价 max_i(m_i)，∈[0,∞)
raw_disp(P) = Σ w_i·m_i +64
max_ΔNLL(P) = max_i( ΔNLL_i(P) )  # 或 max ΔCE_i
P_lex = tuple(assign[0..9])  # assign[j]∈{1,2,3} 10元组字典序，升序唯一
  # 等价 (S1_tuple,S2_tuple,S3_tuple) 各升序后的扁平 10 元

T(P) = ( max_util(P), raw_disp(P), max_ΔNLL(P), P_lex )
P*_per_session = argmin_{P ∈ 37170} T(P) 升序（Python tuple 升序即唯一，需三 session 各自）

T_common(P) = ( max_{sess} max_util(P), max_{sess} raw_disp(P), max_{sess} max_ΔNLL(P), P_lex )
  # 跨 3 sessions 的 worst 聚合，需同 assignment P 在三 session 上均评估
P*_common = argmin_{P ∈ 37170} T_common(P) 升序
  # Common 需 ∀sess ∀i m_i^{sess}(P)<1024 且 per-layer 门禁全过才 THREE_LAYER_COMMON_FEASIBLE

# m_raw 排序键来自 CAL 的 held-out CE_cv：T_cv 用 m_i_cv，VAL 上仅度量确认不重选
# CAL-only：P* 的 T 排序键取自 CAL 内 4-fold 的 held-out CE_i_cv 导出的 m_i_cv
# VAL 上仅报告 m_i_val 确认；若 CAL_cv 与 VAL 的 P* 不一致，报告 cal_val_consistency 但以 CAL 的 P* 为准
```

简化实现（ponytail）：若 `37170×3 sessions×CAL 4-fold` 全量 `C_ab` 重算过重，可对每 session `CAL` 上仅枚举一次 `C_ab` (1024×1024) 后每 `P` 的 `P(U_i|…)` 仅为 `C_ab` 的 `bits` 重汇总（O(1024) per P），不重算 `C_ab`；`VAL` 确认仅对 Top-K（如 `T_cv` 前 100）或 `P*` + `dedup_stats` 全量统计做分层：Phase A 需全量 37170 的 `T_cv` 排序以保 `Common` worst 聚合正确，Phase B VAL 仅对 `P*_per_session`/`P*_common` 做全 per-layer `ΔCE/unseen/chain` 详计，其余 37169 行仅 `m_cv/raw_cv` 落盘或聚合摘要，报告 `dedup_stats` 已足。

## 6. 分流判定（per-session 5分流 + 总体5态 + common审计，三 session 同 assignment）

### 6.1 Per-session 5分流（优先级高→低，互斥）

```
if not materialization_ok or frame_256_violation or CE_chain_not_closed(P*) or dedup_stats invalid or provenance_fabricated:
    classification = V69_EVIDENCE_INCOMPLETE
elif λ_at_boundary(P*) or ∃i ΔCE_i>0.50 or ∃i ΔNLL_i>0.50 or val_b_context_unseen>0.01 or not isfinite(ValNLL) or not isfinite(ΔNLL):
    classification = V69_MODEL_NOT_STABLE   # q_mass/joint/H_cal 仅 descriptive，不入
elif ∀i m_i_raw_val(P*) <1024 && raw_disclosure_val(P*) <10240 && ∀i ΔCE_i≤0.5 && unseen≤1%:
    classification = V69_THREE_LAYER_FEASIBLE  # 含 dedup_stats 显式
elif ∃i m_i_raw_val(P*) <1024:  # 1或2层可行但非全三层
    classification = V69_PARTIAL_FEASIBLE
else: # ∀i m_i≥1024 或 raw≥10240 且无层可行
    classification = V69_STILL_HEAVY
```

- **阈值冻结**：`MODEL_NOT_STABLE` 的 `ΔCE/ΔNLL≤0.50` 且 `val_b_context_unseen≤1%` 且 `λ∈(1e-2,1e4)` 开区间；`THREE_LAYER_FEASIBLE` 的 `∀m_i<1024` 为单 plane 行数满秩阈，`raw<10240≈10*1024` 为 disclosure 阈，仅描述不过 `MODEL` 门禁；`capacity_warning_m1/m2/m3/disclosure`（`m_i≥1024 / raw≥10240`）为正交旗标，仅描述不过门禁；`LaneC+8+8` 仅描述性，不入 `THREE_LAYER` 门禁。
- **Successor**：`EVIDENCE_INCOMPLETE → recollect`，`MODEL_NOT_STABLE → recollect_or_new_prior`，`THREE_LAYER_FEASIBLE → v69_three_layer_code_design`，`PARTIAL_FEASIBLE → v69_rate_adaptive_or_new_representation`，`STILL_HEAVY → v69_new_representation`。
- **Dedup 审计**：每 session 表中恒含 `dedup_stats {raw 59049, valid 37170, per_pattern[12]}`。

### 6.2 总体5态 + common审计（三 session 同 assignment）

```
common_feasible = count_{sess} [ P*_common 在该 sess 上 THREE_LAYER_FEASIBLE ]  # 0..3, 需同 P
per_session_feasible = #{sess | P*_per_session 在该 sess 上 THREE_LAYER_FEASIBLE}  # 0..3
partial_count = #{sess | classification == PARTIAL_FEASIBLE}
if any EVIDENCE_INCOMPLETE:
    overall = V69_OVERALL_EVIDENCE_INCOMPLETE
elif any MODEL_NOT_STABLE and common_feasible==0:
    overall = V69_OVERALL_MODEL_NOT_STABLE
elif common_feasible ==3:  # common P*_common 在 3 sessions 上均 THREE_LAYER_FEASIBLE (同 assignment)
    overall = V69_OVERALL_THREE_LAYER_COMMON_FEASIBLE
elif per_session_feasible >=1 or partial_count>=1:
    overall = V69_OVERALL_THREE_LAYER_PER_SESSION_ONLY  # 存在 P* feasible 但 common 不 feasible
else: # 0 feasible 且 0 partial
    overall = V69_OVERALL_STILL_HEAVY
# audit = { P*_per_session[3], P*_common, T_per_session[3], T_common, dedup_stats, common_feasible_count, per_session_feasible_count, partial_count, cal_val_consistency[3], max_util/disclosure/ΔNLL per P }
```

- 总体不设 `FAIL`，即便全部 `STILL_HEAVY` 亦 `COMPLETE`（地图完成，结论为需新表示）；仅 `<3` session 视为 incomplete map（但 V69 固定 3）。
- 报告需附 `counts_per_classification (5分流)` 与 `common 审计表` + `dedup_stats 12-pattern 分表` + `per-layer ΔCE/ΔNLL/unseen`。

## 7. 脚本与报告（decoder-free 守卫 + `3^10→37170` 枚举去重回填，不启 V70）

- **脚本 `scripts/v69_three_layer_feasibility.py`** (decoder-free):
  `python scripts/v69_three_layer_feasibility.py [--registry v69_data_registry.json] [--out v69_results.json]`
   → 每 session `CAL1024 上 37170×(C_ab/P/λ) → CV CE_i → m_i_cv → T(P) 排序选 P*_per_session(CAL) → VAL256 上对 P* 计 CE/m/raw + per-layer VAL-CAL + chain + dedup_stats`，`P*_common` 跨 session `T_common` 选（同 assignment），`rg "decode_|construct_|gf_rank|nested" 0 hits`，`rg -i "met|protograph|sc_coupling" 0 hits`，`rg "V70|v70|QUALIFICATION" 0 hits`（除 successor 注释），`py_compile PASS`；输出 `v69_results.json + v69_table.{csv,json} + 控制台摘要`；校验 `TEST 未参与`、`VAL 未参与选优`、`m_raw` 未 cap、`37170 去重`已验、`common 同 assignment`。
- **报告 `V69_THREE_LAYER_REPORT.md`**：`per session 3^10→37170 去重统计 + 12-pattern 分表 + P*_per_session + P*_common + CAL/VAL 双组 CE_i/λ/ΔNLL/unseen/m/max_util/raw/classification/successor/stage_consistency/cal_val_consistency/per-layer ΔCE + overall 5态 + common 同 assignment 审计` 与 `json/csv` 一致，不扩大为 `FER/SKR`，显式 `V70_not_started`。
- **守卫**：地图期零 decoder、零矩阵构造、多 session 并列分流、**不创建 `run_01`**、不比较方法、不调 V69 以外码、**不启 V70**；**四工件+registry+spike 已单独提交推送，新 Plan SHA 已生成**。

## 8. 守卫 R69-01~10（decoder-free, 不构矩阵, 不创 run_01, 不启 V70, V67复用, `3^10→37170` 去重, per-layer ≤0.5）

| 守卫 | 检查 | 阈/断言 |
|---|---|---|
| R69-01 | 冻结主体 1024维三层验证不改 + 不启 V70 | `n1024 q1024 GF32 poly37 H1 16×1024 rank16 U 三层 (仅 P 重标记) Lane C/H_inc Δ8 decoder 90/1.0 full-tag git diff src==0 && successor_v70_not_started && rg "V70" 0 hits` |
| R69-02 | 枚举 `3^10=59049→37170` 去重统计完整 | `3^10==59049 && valid C(10:w_i∈[2,5])==37170 && product([1,2,3],repeat=10) 升序过滤 37170 行每 session && per_pattern 12类计数 2520/3150/4200 已验 && not剪枝` |
| R69-03 | 升序唯一词典序 `max_util→disclosure→ΔNLL→lex` | `T(P)=(max_util, raw, max_ΔNLL, P_lex) 升序唯一, T_common 同理 (max_{sess} 聚合), P* 确定性, Common 同 assignment` |
| R69-04 | Phase A CAL-only 选 P* | `P* 排序键来自 CAL 4-fold m_cv/CE_cv, used_val_in_selection==False && used_test==False` |
| R69-05 | Phase B VAL确认 per-layer `VAL-CAL≤0.5` + `unseen≤1%` + `chain 1e-9` + `m<1024` | `VAL256 上 P* 计 CE1/CE2/CE3/CE_full chain |ΣCE_i-CE_full|<1e-9, ∀i |CE_i^{VAL}-CE_i^{CV}|≤0.5 && ΔNLL_i≤0.5, val_b_context_unseen≤1%, ∀i m_i<1024 阈已验` |
| R69-06 | V67三Session Stage2 复用 | `v69 registry sessions==v67 Stage2 3 sessions, total 3 per_cat 1,1,1 acq_dedup_verified zero_overlap_verified, successor_v70_not_started` |
| R69-07 | per-session 5分流 + 总体5态 + common同 assignment 审计 | `classification 按 EVIDENCE>MODEL>THREE_LAYER>PARTIAL>STILL_HEAVY 互斥, overall 5态 (含 COMMON_FEASIBLE 需三 session 同 P), P*_per_session+P*_common+common_feasible_count+dedup_stats 已落盘` |
| R69-08 | 四工件 + test 完整 | `v69_data_registry + v69_results + v69_table.csv/json 行对等 + V69_THREE_LAYER_REPORT + test_v69_three_layer_small.py py_compile+pytest PASS + dedup_stats 12-pattern` |
| R69-09 | decoder-free 不构矩阵 + 不读 TEST | `rg "decode_|construct_|gf_rank|nested" 0 hits && rg -i "met|protograph" 0 hits && rg "TEST" read 0 hits && used_test==False && no H matrix built` |
| R69-10 | 不创 run_01 + 编译 + 小测试 + TEST隔离 + 不启 V70 | `ls .../v69_*/run_01 不存在 && py_compile PASS && pytest 小测试 PASS && used_test==False && grep "min(1024" 0 hits && m_raw 不 cap && V70_not_started` |

## 9. 与 V64/V67/V68/V69/V70 衔接

- V64 `full-tag` 语义与 `H_total 200/206/208` 冻结构及 `22/24 PASS` 已固化；V67 3 sessions 均 `NEAR_FULL` 证 natural 5+5 不均衡；V68 为**二层比特级均衡性地图**（252）；V69 为**三层表示可行性地图**（`3^10→37170`），与 V67/V68 正交复用 Stage2，不重估计。
- 若 `V69_OVERALL_THREE_LAYER_COMMON_FEASIBLE` 则三层表示可被 `P*_common` 纠正，后续 `V69` 可直接复用该 `P*` 走三层码设计；若 `PER_SESSION_ONLY` 则需 per-session 自适应；若 `PARTIAL` 则需 rate-adaptive；若 `STILL_HEAVY` 则需更深非比特划分（另起 OpenSpec，但非 V70 本轮）。
- 本变更不创建 `run_01`，**不启动 V70**，任何 `V69` 后续码设计/decoder 需另起 `EXECUTE_AUTH`，V70 需独立 `OpenSpec` 且显式用户授权。

## 10. 自由裁量 D1-D7

- D1 完全冻结主体（`H1/Lane C/Δ8/decoder/full-tag`），V69 仅 `P` 三层重划分，不改码（多 session），不启 V70。
- D2 单一层级估计器 `P(a|b)=(C_ab+λ P_global)/(N_b+λ)`，每 `P` 独立重估 `P(U1|B)/P(U2|U1,B)/P(U3|U1,U2,B)`，`λ` 单一全局。
- D3 泄漏 `raw_disclosure=Σ w_i·m_i+64` 不 cap，`THREE_LAYER_FEASIBLE` 限 `∀m_i<1024 && raw<10240` + per-layer `VAL-CAL≤0.5` + `unseen≤1%`。
- D4 数据 `Stage2 CAL1024 VAL256` 确定性复用 V67，不搜索多划分，TEST隔离，V70 不启。
- D5 5分流 per-session + 5态 overall + common 同 assignment 审计，不以平均替代。
- D6 不产生新矩阵/码参数，仅 `P*` 与 successor 建议，`THREE_LAYER` 方可进入后续三层码设计。
- D7 本变更为 `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`，不产生 `run_01`，任何 decoder/V70 需 `PLAN_ACCEPT + EXECUTE_AUTH` 后才允。
