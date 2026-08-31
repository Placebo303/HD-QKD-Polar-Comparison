# OpenSpec Spec: formal-ir-v69-three-layer-representation-feasibility

**Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — 仅 plan 四工件 + decoder-free 三层表示可行性地图，不改1024维符号 GF32两层验证，仅重划分10 bits 为三层有序 `w∈[2,5]`，不跑decoder不构矩阵不读TEST不启V70

**Change**: `formal-ir-v69-three-layer-representation-feasibility` (`V69-3L`, branch `formal-ir-mainline`, HEAD `fcf3e457ecf45c58e23f91d750acd5267d541795`, data `84d62779`, 3 sessions 复用 V67 Stage2, `3^10=59049→37170`)

**Predecessor**: `formal-ir-v68-balanced-gf32-bit-partition` (`fcf3e457ecf45c58e23f91d750acd5267d541795` `PLAN_CANDIDATE`) + `formal-ir-v67-multisession-feasibility-map` (`V67_FEASIBILITY_MAP_ACCEPTED`) + `formal-ir-v64-full-symbol-verification-correction` (`22/24 PASS`) — V69 新增三层表示可行性地图，A-G 全约束，decoder-free，不启 V70

## 1. 变更类型与生命周期

- **Type**: `THREE_LAYER_REPRESENTATION_FEASIBILITY_MAP` — 于 V67 三预注册 Session 的 `Stage2 CAL1024+VAL256` 上，对 `B={0..9}` 的全部 `3^10=59049` 个分配 `assign: B→{1,2,3}` 去重统计后过滤 `w_i=|{j:assign[j]=i}|∈[2,5]` 且 `Σw_i=10` 且 `S_i≠∅` 得 **37170** 个有效有序三层划分 `P=(S1,S2,S3)` 定义 `U_i=bits_{S_i}(s)`（宽度 `w_i`, 值域 `0..2^{w_i}-1`），每 `P` 在 `CAL` 上估 `P(U1|B)/P(U2|U1,B)/P(U3|U1,U2,B)`（`λ` 仅 CAL 4-fold），在 `VAL` 上计 `CE1/CE2/CE3/CE_full chain→m_i_raw=ceil(1.3*1024*CE_i/w_i) raw_disclosure=Σw_i·m_i+64` 不 cap，链式 `|ΣCE_i-CE_full|<1e-9`，per-layer `|CE_i^{VAL}-CE_i^{CAL-CV}|≤0.5` 且 `val_b_unseen≤1%` 且 `∀m_i<1024` 门禁，以升序唯一词典序 `max_util→disclosure→max_ΔNLL→lex` 选 `P*_per_session` 与 `P*_common`（需三 session 同 assignment），`Phase A CAL-only` 不读 VAL/TEST，`Phase B VAL` 确认 per-layer 门禁。
- **Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — 本轮止于 plan 四工件 + decoder-free 地图（`v69_data_registry.json + v69_three_layer_feasibility.py + v69_results.json + v69_table.{csv,json} + V69_THREE_LAYER_REPORT.md + test_v69_three_layer_small.py + dedup_stats`），**不实现 runner，不执行 decoder，不构矩阵，不创建 `run_01`，不读 VAL/TEST 择优，不改1024维主体/V67/V68/src，不启动 V70**；正式 `run_01` 需独立 `PLAN_ACCEPT` + `EXECUTE_AUTH`；`DECODER_FREE` 表示零 `decode_* / construct_* / gf_rank / nested` 调用（`rg 0 hits`），`V70_NOT_STARTED` 表示零 `V70_*/run_01` 且 `rg -i "v70|qualification" 0 hits`（除 successor 注释）。
- **Branch**: `formal-ir-mainline`；`HEAD` `fcf3e457ecf45c58e23f91d750acd5267d541795` 重核，不一致阻塞；已与 `git rev-parse HEAD` 一致。`TBD` 0 hits。
- **Data SHA**: `84d62779` (`d1024 bw200 nearest legacy_v1`) — V69 复用 V67 三 session Stage2 (`CAL1024+VAL256`)，不换点，不启 V70。
- **Session bound**: `total 3 (=V67 3)` 复用，`per_category 1,1,1`，不新增 acquisition。
- **Rate feasibility**: **m_i_raw=ceil(1.3*1024*CE_i/w_i), raw_disclosure=Σw_i·m_i+64 不 cap**，择优键 `T=(max_util, raw, max_ΔNLL, P_lex)` 升序，分流阈 `∀m_i<1024 && raw<10240 && ∀ΔCE_i≤0.5 && unseen≤1%` 为 `THREE_LAYER_FEASIBLE`，`common` 需三 session 同 assignment。
- **Search space**: `raw 3^10=59049` 全分配，`w∈[2,5]` 过滤后 `valid 37170`（12 pattern 各 `2520/3150/4200`），`dedup_stats` 已落盘。
- **V70**: **NOT_STARTED** — 本变更内禁止任何 `V70` `QUALIFICATION_PLAN_READY / run_01 / 阈/码族` 预冻结或产出。

## 2. 冻结方法（主体完全冻结，V69 零改，仅 P 三层重标记，不启 V70）

### 2.1 主体不变量（V64 完全冻结，V67/V68 零改，V69 仅 P）

- `n=1024 symbols/block` (`4×256 frames`), `q=1024 (10-bit s)`, `GF32 poly37`, `tag=64 bits/block`。
- `H1 = V31-H1-QC 16×1024 rank16 80b` 母矩阵；`U_natural =32*U1+U2, F03 5+5` (`U1>>5, U2&31`) 二层参照；`U_three_layer(P)= (bits_{S1}(s), bits_{S2}(s), bits_{S3}(s))` 37170种仅重标记（`w_i∈[2,5] Σw_i=10 有序非空`）。
- `Lane C` ordinal-2 `s38310x`：`m2 base 1M 184 / 1p5M 190 / 2M 192` 全冻。
- `H_inc1 8×1024 + H_joint1 192×1024` nested；`H_inc2 8×1024 + H_total 200×1024` nested；`rank_total==m2+16` 等全冻，**本变更不构 H**。
- `decoder`: `decode_row_layered_fftqspa` `90/1.0 poly37 early-stop` (禁用至后续授权)；`rescue=verification-only`。
- `leak`: `leak_three = Σ w_i·m_i +64`（三层），`raw_disclosure` 不 cap；二层 `5*(m1+m2)+64` 仅参照。
- `verification`: `full-symbol tag s_hat=perm_P^{-1}(u1_hat,u2_hat,u3_hat) compute_tag_64 canonical trunc64` (V64 22/24 PASS)，单64b。
- `budget 地图预冻结`: `V67 Stage2 CAL1024+VAL256` 每 session，`TEST` 密封，`m_raw` 由 `VAL CE_i/w_i` 得，择优键 `max_util→disclosure→max_ΔNLL→lex`（common 三 session 同 assignment）。
- `V67 终态`: `3× NEAR_FULL` 二层 natural 已固化，V69 以三层重划分为纠正假设；`V68` 252 均衡二层地图正交。
- `V70`: **NOT_STARTED** — 禁止本变更内任何 V70 预冻结。

### 2.2 处理点与物化单点冻结

- `84d62779` 语义：`dimension 1024, bin_width 200ps, pairing nearest double-pointer bin//1024, rule legacy_v1, channels A1/B5, frame_len 256 pairs, BLOCK 1024, period 204800ps floor_div, threshold 40000ps, gate 200ps` — 单点，多 session provenance，各 session 单独物化后 `P` 重标记。
- `TEST` 密封：任何 `TEST/EVAL` 域不计 `CE/m/P*/ΔCE/unseen`；`C_ab/P/CE/m` 均 `CAL/VAL` 测，`TEST` 不读，`P*` 择优仅 `CAL`，`V70` 不启。
- **P 三层重标记**：`P∈ {1,2,3}^{10} 59049→37170 有序三层 w∈[2,5] Σw=10 S_i≠∅` 升序枚举，禁 `Gray/MET/protograph/SC` 外的重表示。

### 2.3 禁止

- 禁改任一冻结量、新增矩阵/标签/prior/阈值/decoder、试 `Δ8` 外 degree/seed 网格、跨 acquisition 拼接凑 `3`、将 `min(1024,ceil)` cap 伪装当通过、将 `VAL` 数据用于 `P*` 择优、将零重叠仅比 `frame_id`、引 `MET/protograph/SC/Gray`、改 `src/experiments/tools` 任何文件；禁读 `TEST` 统计；**m_raw 不 cap**；禁 `P` 剪枝至 `<37170`（除 `w∈[2,5]` 硬过滤）；禁改 `T` 排序 `max_util→disclosure→ΔNLL→lex`；禁以平均替代 `max_{sess}` 选 `common`；禁不满足同 assignment 的 `common`；禁构 `H/matrix/rank/nested`；未授 `EXECUTE_AUTH` 前禁 `decode_*`；**禁启 V70**。

## 3. Phase A — 数据角色 (V67 Stage2 复用，`3^10→37170` 枚举去重前置，不启 V70)

### 3.1 角色与零重叠（键 `(source,session,frame)` 复用）

| 集合 | 每 session 规模 | 说明 |
|---|---|---|
| Stage2 CAL (Phase A) | 1024 frames (262144 pairs) | `C_ab → P` per `P` (37170×) 去重统计 |
| Stage2 VAL (Phase B) | 256 frames (65536 pairs) | `CE_i → m_i_raw → raw + per-layer VAL-CAL + unseen + chain + m<1024` per `P*` |
| TEST | 密封不读 | `used_test==False`，V70 不启 |

- **复用**：`v69_data_registry.json` 由 `v67_data_registry.json` Stage2 原样复用 `sessions[3]`，`per_category 1,1,1`，`acquisition_dedup_verified:true`，`successor_v70_not_started:true`。
- **零重叠**：`CAL_key∩VAL_key==∅ && (CAL∪VAL)_key ∩ (V13..V68)_key ==∅`（键 `(source,session,frame)`），`not_cross_spliced:true`。
- **注册表**：`v69_data_registry.json` (`schema v69_data_v1`) 含 `sessions[3] {session_id, acquisition_id, source_label, provenance, stage2_CAL[1024], stage2_VAL[256], zero_overlap_verified, acquisition_dedup_verified, frozen, not_sorted_by_CE, reused_from v67, successor_v70_not_started}`，禁止事后换 session。
- **枚举去重**：`assign_list = product([1,2,3], repeat=10)` 升序 `59049`，过滤 `w_i∈[2,5]` 得 `37170`，`per_pattern 12类` 已分表统计，`dedup_stats` 落盘。

### 3.2 数据就绪门

- `total==3 && per_category 1,1,1 && acquisition_dedup_verified && successor_v70_not_started` 否则 `EVIDENCE_INCOMPLETE`。
- `|CAL|==1024 && |VAL|==256 && CAL∩VAL==∅ && (CAL∪VAL)∩(V13..V68)==∅` 否则 `EVIDENCE_INCOMPLETE`。
- `frame 256` + `s∈[0,1023]` 已验，否则 `EVIDENCE_INCOMPLETE`。
- `raw 59049 && valid 37170 && per_pattern sum 37170` 已验，否则 `EVIDENCE_INCOMPLETE`。

## 4. Phase B — 输入合同 strict V56 (仅 P 三层重标记)

- **合同项**：`dimension 1024, bin 200, pairing nearest bin//1024, legacy_v1, channels A1/B5, U_natural 32*U1+U2 5+5 参照, U_three_layer bits_P(P) 37170种 w∈[2,5] Σw=10 有序非空, frame_start_ps, period 204800, floor_div, mapping legacy_v1, 每帧256` 落 `v69_manifest.json`。
- **权威算法**：`_read_ttbin_timetags → _bin_indices_sorted_for_binwidth → _pairs_from_sorted_bins → 256分组 → legacy_v1 → U (natural) → bits_P 三层重标记` 原样复用，不重写。
- **不GE/MET/V70**：`rg -i "met|protograph|sc_coupling|v70|qualification" 0 hits` 已验（`P` 注释 + `V70_not_started` 除外），`V70_not_started` 已显式。

## 5. Phase C/D — 枚举估计与两阶段选优 (`37170` CAL 4-fold + VAL确认 per-layer ≤0.5，不启 V70)

### 5.1 C_ab 与 P_global (CAL-only per P per session, 去重)

```
C_ab[a,b] = bincount2d(a_cal, b_cal)  1024×1024, sum 262144 (CAL1024)
N_b[b] = Σ_a C_ab
P_global(a) = Σ_b C_ab / N_cal
Q=1024, n=1024
# per P: a 的 (u1,u2,u3) 查表由 bits_P(s) 决定，C_ab 本身不按 P 重算，仅 P(U_i|…) 汇总按 P 变
# dedup: raw 59049 → valid 37170 去重统计已验
```

### 5.2 层级先验与熵/CE (CAL 描述性 + VAL 门禁性，三层，链式，TEST隔离，CAL-only 择优，per-layer ≤0.5)

```
P(a|b) = (C_ab + λ P_global(a)) / (N_b + λ)  (N_b>0); P_global(a)  (N_b==0)
P(u1|b) = Σ_{u2,u3} P( perm_P^{-1}(u1,u2,u3) | b )  # 2^{w1}×1024
P(u2|u1,b) = Σ_{u3} P(u2,u3|u1,b)
P(u3|u1,u2,b) = P(a|b)/P(u1|b)/P(u2|u1,b)
CE1(P) = -E_{heldout/VAL} log2 P(U1(P)|B)
CE2(P) = -E log2 P(U2(P)|U1(P),B)
CE3(P) = -E log2 P(U3(P)|U1,U2,B)
CE_full = -E log2 P(A|B)
CE 链式: |CE_full - CE1(P) - CE2(P) - CE3(P)| <1e-9 else EVIDENCE_INCOMPLETE
m1_raw(P) = ceil(1.3*1024*CE1/w1), m2_raw=ceil(1.3*1024*CE2/w2), m3_raw=ceil(1.3*1024*CE3/w3)  (不 cap)
raw_disclosure(P) = w1*m1_raw + w2*m2_raw + w3*m3_raw +64
max_util(P)= max_i(m_i/1024), max_ΔNLL(P)=max_i(ΔNLL_i)
# P* 排序键来自 CAL held-out m_cv，VAL m_raw 仅度量确认
T(P) = (max_util, raw_disclosure, max_ΔNLL, P_lex)
P*_per_session = argmin_{P} T(P)  # 37170升序唯一
T_common(P) = (max_{sess} max_util, max_{sess} raw, max_{sess} max_ΔNLL, P_lex)
P*_common = argmin_{P} T_common(P)  # 需三 session 同 assignment
# per-layer VAL-CAL 门禁：ΔCE_i=|CE_i^{VAL}-CE_i^{CV}|≤0.5, ΔNLL_i≤0.5, unseen≤1%
```

- **λ 择优**：`λ ∈[1e-2,1e4] log10` 仅 `CAL 内 4-fold` 最小 `CV NLL`，触界则 `MODEL_NOT_STABLE`，不扩网格。`VAL` 测时 `λ` 固定为 `CAL` 择优值，不重选。
- **阶段隔离**：`P*` 不读 `VAL`/`TEST`，`VAL` 仅对 `P*` 度量 per-layer `ΔCE/ΔNLL/unseen/chain/m<1024`；`used_val_in_selection==False && used_test==False` 已验。
- **Dedup**：`dedup_stats {raw 59049, valid 37170, per_pattern[12]}` 已落盘。
- **V70 隔离**：任何 V70 预冻结禁止。

## 6. Phase E — 分流与总体 (per-session 5分流 + 总体5态 + common同 assignment审计)

### 6.1 Per-session 5分流（优先级高→低，互斥）

```
if not materialization_ok or frame_256_violation or CE_chain_not_closed(P*) or dedup_invalid or provenance_fabricated:
    classification = V69_EVIDENCE_INCOMPLETE; successor = recollect
elif λ_at_boundary(P*) or ∃i ΔCE_i>0.50 or ∃i ΔNLL_i>0.50 or val_b_context_unseen>0.01 or not isfinite(ValNLL) or not isfinite(ΔNLL):
    classification = V69_MODEL_NOT_STABLE; successor = recollect_or_new_prior
elif ∀i m_i_raw_val(P*) <1024 && raw_disclosure_val(P*) <10240 && ∀i ΔCE_i≤0.5 && unseen≤1%:
    classification = V69_THREE_LAYER_FEASIBLE; successor = three_layer_code_design
elif ∃i m_i_raw_val(P*) <1024:  # 1或2层可行
    classification = V69_PARTIAL_FEASIBLE; successor = rate_adaptive_or_new_representation
else: # ∀m_i≥1024 或 raw≥10240 且无层可行
    classification = V69_STILL_HEAVY; successor = new_representation
```

- `LaneC+8+8` 仅描述性，不入 `THREE_LAYER` 门禁；`capacity_warning_m1/m2/m3/disclosure` 正交，仅描述不过门禁；旧三项 `ValNLL>H+1 / H+0.5 / joint>1%` 改归 `descriptive_diagnostics`。

### 6.2 总体5态 + common同 assignment审计

```
common_feasible = #{sess | P*_common 在该 sess 上 THREE_LAYER_FEASIBLE (同 assignment, ∀m_i<1024 && per-layer ≤0.5 && unseen≤1%)}  # 0..3
per_session_feasible = #{sess | P*_per_session 在该 sess 上 THREE_LAYER_FEASIBLE}  # 0..3
partial_count = #{sess | classification == PARTIAL_FEASIBLE}
if any EVIDENCE_INCOMPLETE:
    overall = V69_OVERALL_EVIDENCE_INCOMPLETE
elif any MODEL_NOT_STABLE and common_feasible==0:
    overall = V69_OVERALL_MODEL_NOT_STABLE
elif common_feasible ==3:  # common P*_common 在 3 sessions 上均 THREE_LAYER_FEASIBLE 同 assignment
    overall = V69_OVERALL_THREE_LAYER_COMMON_FEASIBLE
elif per_session_feasible >=1 or partial_count>=1:
    overall = V69_OVERALL_THREE_LAYER_PER_SESSION_ONLY
else:
    overall = V69_OVERALL_STILL_HEAVY
counts_per_classification = {EVIDENCE, MODEL, THREE_LAYER, PARTIAL, STILL_HEAVY}
audit = {P*_per_session[3], P*_common, T_per_session[3], T_common, dedup_stats{raw,valid,per_pattern12}, common_feasible_count, per_session_feasible_count, partial_count, cal_val_consistency[3], max_util/disclosure/ΔNLL per P, per_layer ΔCE/ΔNLL/unseen}
```

## 7. Phase F — 报告与表 (per session 去重统计 + P* + dedup + overall 5态 + common同 assignment)

- **表 schema** (`v69_table.csv/.json` 行对等, 过滤后全量或 Top-K + P* + dedup_summary + common 汇总)：
```
session_id, acquisition_id, source_label, provenance,
P_assign (tuple 10), P_S1_tuple, P_S2_tuple, P_S3_tuple, w1,w2,w3, P_lex_index,
dedup_stats: raw_59049, valid_37170, per_pattern_counts[12],
CAL: CAL_lambda, CAL_lambda_at_boundary, CAL_DeltaNLL_i[3], CAL_ValNLL_i[3], CAL_H_cal_i[3], CAL_val_b_context_unseen, CAL_joint_cell_unseen, CAL_q_mass_unseen (descriptive), CAL_descriptive×3, CAL_capacity_warning×4, CAL_effective_contexts,
VAL: CE1, CE2, CE3, CE_full, chain_delta, ValNLL_i[3], DeltaNLL_i[3], DeltaCE_i[3]=|CE_i^{VAL}-CE_i^{CV}|, val_b_context_unseen, joint_cell_unseen, q_mass_unseen (descriptive), descriptive×3, capacity_warning×4, m1_raw, m2_raw, m3_raw, raw_disclosure, max_util, max_DeltaNLL, max_DeltaCE,
is_P_star_per_session, is_P_star_common,
per_session_classification (仅 P* 行有效), successor, cal_val_consistency, successor_v70_not_started
# 另汇总行: per_session P*, common P*, dedup_stats 12-pattern 分表, overall 5态
```
- **报告** `V69_THREE_LAYER_REPORT.md`：`per session 59049→37170 去重统计 12-pattern 分表 + P*_per_session + P*_common + CAL/VAL 双组 CE_i/λ/ΔNLL/unseen/m/max_util/raw/classification/successor/cal_val_consistency/per-layer ΔCE + overall 5态 + common同 assignment审计 + map_sparse + TEST隔离 + 1024维冻结 + V70_not_started` 与 `json/csv` 一致，不扩大为 `FER/SKR`。

## 8. 守卫 R69-01~10

| 守卫 | 条件 | 阈值 |
|---|---|---|
| R69-01 | 冻结主体 1024维三层验证不改 + 不启 V70 | `n1024 q1024 GF32 poly37 H1 16×1024 rank16 U 三层 (仅 P 重标记) Lane C/H_inc Δ8 decoder 90/1.0 full-tag git diff src==0 && successor_v70_not_started && rg -i "v70|qualification" 0 hits` |
| R69-02 | 枚举 `3^10=59049→37170` 去重统计完整 | `3^10==59049 && valid==37170 && product([1,2,3],repeat=10) 升序过滤 37170 行每 session && per_pattern 12类 2520/3150/4200 已验 && not剪枝` |
| R69-03 | 升序唯一词典序 `max_util→disclosure→ΔNLL→lex` + common 同 assignment | `T(P)=(max_util, raw, max_ΔNLL, P_lex) 升序唯一, T_common 同理 (max_{sess} 聚合), P* 确定性, Common 同 assignment` |
| R69-04 | Phase A CAL-only 选 P* | `P* 来自 CAL m_cv/CE_cv, used_val_in_selection==False && used_test==False` |
| R69-05 | Phase B VAL确认 per-layer `VAL-CAL≤0.5` + `unseen≤1%` + `chain 1e-9` + `m<1024` | `VAL256 上 P* 均 |ΣCE_i-CE_full|<1e-9, ∀i |CE_i^{VAL}-CE_i^{CV}|≤0.5 && ΔNLL_i≤0.5, val_b_context_unseen≤1%, ∀i m_i<1024` |
| R69-06 | V67三Session Stage2 复用 + 不启 V70 | `v69 registry == v67 Stage2 3 sessions, total 3 per_cat 1,1,1 acq_dedup_verified zero_overlap_verified && V70_not_started` |
| R69-07 | per-session 5分流+总体5态+common同 assignment审计 | `classification 按 EVIDENCE>MODEL>THREE_LAYER>PARTIAL>STILL_HEAVY 互斥, overall 5态 (含 COMMON_FEASIBLE 需三 session 同 P), P*_per_session+P*_common+common_feasible_count+partial_count+dedup_stats 已落盘` |
| R69-08 | 四工件+test 完整（含 dedup_stats） | `v69_data_registry + v69_results + v69_table.csv/json 行对等 + V69_THREE_LAYER_REPORT + test_v69_three_layer_small.py py_compile+pytest PASS + dedup_stats 12-pattern` |
| R69-09 | decoder-free不构矩阵 + 不读 TEST | `rg "decode_|construct_|gf_rank|nested" 0 hits && rg -i "met|protograph" 0 hits && used_test==False && no H built` |
| R69-10 | 不创 run_01+编译+小测试+TEST隔离+不启V70 | `run_01 不存在 && py_compile PASS && pytest 小测试 PASS && used_test==False && grep "min(1024" 0 hits && m_raw 不 cap && V70_not_started` |

## 9. 脚本与证据写出 (预冻结，decoder-free，不构矩阵，不启 V70)

- **固定脚本**（本轮）：
  - `scripts/v69_three_layer_feasibility.py`: `CAL1024 37170×C_ab/P/λ→m_cv→T→P* → VAL256 P* CE/m + per-layer VAL-CAL + chain + dedup_stats + common同 assignment`，输出 `v69_data_registry.json + v69_results.json + v69_table.(csv|json) + v69_manifest.json + V69_THREE_LAYER_REPORT.md`，`rg "decode_|construct_|gf_rank|nested" 0 hits`，`rg -i "met|protograph|v70" 0 hits`（除 V70_not_started 注释），`py_compile PASS`，`m_raw` 未 cap，`VAL` 未参与选优，`CE 链式` 已验，`59049→37170` 已验。
- **证据**：
```
openspec/changes/formal-ir-v69-three-layer-representation-feasibility/  # 本轮 plan 四工件
scripts/v69_three_layer_feasibility.py  # decoder-free, 37170枚举去重
v69_data_registry.json (复用 V67 Stage2 3 sessions, V70_not_started)
v69_results.json (per session 去重统计 + CE/m + P* + per-layer VAL-CAL + common同 assignment)
v69_table.csv/.json (过滤后全量或 Top-K + P* 汇总, classification/successor + dedup_stats)
V69_THREE_LAYER_REPORT.md
v69_manifest.json (frozen_body + guards R69-01~10 + dedup_stats 12-pattern)
test_v69_three_layer_small.py
comparison_bench/outputs_comparison/formal_ir_methods/v69_three_layer/  # 未来 run_01 (本轮不建, V70 亦不建)
```
- **文件**：`v69_data_registry.json` (authoritative `3` 实表，复用 V67 Stage2) + `v69_results.json` + `v69_table` (行对等) + `v69_manifest.json` (frozen_body + guards + dedup_stats) + `V69_THREE_LAYER_REPORT.md` + 控制台摘要；本轮仅冻结计划，不创建正式 run_01，**已单独提交推送新 Plan SHA**，**V70_NOT_STARTED**。

## 10. 验收

- **本轮 plan 自检 gate（A-G 已闭合，不启 V70）**：`py_compile PASS` spike，`rg "decode_|construct_|gf_rank|nested" 0 hits`，`rg -i "met|protograph" 0 hits`，`rg -i "v70|qualification" 0 hits`（除 V70_not_started 注释），`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0 && git diff -- openspec/changes/formal-ir-v6[0-8]/ ==0` (除本变更+scripts 外零改)，`VAL` 未参与 `P*` 选优已验 (`used_val_in_selection==False`)，`TEST` 未读已验 (`used_test==False`)，`m_raw` 未 cap 伪装已验 (`grep "min(1024" 0 hits` 且 `m_raw` 显式 Σw_i·m_i+64)，`P 59049→37170` 去重枚举升序已验，`T max_util→disclosure→ΔNLL→lex` 唯一 + common同 assignment 已验，`5分流优先级互斥` 已验，`overall 5态+common审计+dedup_stats` 已验，`V67 Stage2 复用 3` 已验，`per-layer VAL-CAL≤0.5 && unseen≤1% && chain 1e-9 && ∀m_i<1024` 已验，`capacity_warning` 正交与 `descriptive` 已落盘，`run_01` 不存在已验，`V70_not_started` 已验，**报告表与 json 一致**，`TBD` 0 hits。
- **本轮仅 plan 四工件+registry+spike+报告表（CAL-only 37170枚举去重，common同 assignment）**，任何 `V69` 后的三层码设计/decoder 需 `Plan SHA` + `v69_data_registry.json` 实表 + `37170选优+VAL确认+per-layer门禁+dedup_stats` 已验后、且独立 `PLAN_ACCEPT` + `EXECUTE_AUTH` 后才允许创建正式实现并执行；`DECODER_FREE` 保持至授权，**V70 保持 NOT_STARTED**。
