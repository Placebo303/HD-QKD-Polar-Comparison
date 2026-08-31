# OpenSpec Spec: formal-ir-v68-balanced-gf32-bit-partition

**Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — 仅 plan 四工件 + decoder-free 均衡 bit-partition 地图，不改1024维符号 GF32两层验证，仅重划分10 bits，不跑decoder不构矩阵

**Change**: `formal-ir-v68-balanced-gf32-bit-partition` (`V68-BAL`, branch `formal-ir-mainline`, HEAD `b7e3417f`, data `84d62779`, 3 sessions 复用 V67 Stage2)

**Predecessor**: `formal-ir-v67-multisession-feasibility-map` (`b7e3417f` `V67_FEASIBILITY_MAP_ACCEPTED`) + `formal-ir-v64-full-symbol-verification-correction` (`22/24 PASS`) — V68 新增均衡 partition 地图，A-G 全约束，decoder-free

## 1. 变更类型与生命周期

- **Type**: `BALANCED_BIT_PARTITION_MAP` — 于 V67 三预注册 Session 的 `Stage2 CAL1024+VAL256` 上，对 `B={0..9}` 的全部 `C(10,5)=252` 个 5-bit 子集 `S` 定义 `U1'=bits_S(s), U2'=bits_{B\S}(s)`，每 `S` 在 `CAL` 上估 `P(U1'|B)/P(U2'|U1'B)`（`λ` 仅 CAL 4-fold），在 `VAL` 上计 `CE1/CE2/CE_full chain→m1_raw/m2_raw ceil不cap`，以升序唯一词典序 `max→sum→abs→lex` 选 `S*_per_session` 与 `S*_common`，报告 `natural S_nat={5,6,7,8,9}` 参照，`Phase A CAL-only` 不读 VAL/TEST，`Phase B VAL` 确认，per-session 4分流 + 总体3态 + common审计。
- **Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — 本轮止于 plan 四工件 + decoder-free 地图（`v68_data_registry.json + v68_spike.py + v68_results.json + v68_table.{csv,json} + V68_BALANCED_REPORT.md + test_v68_spike_small.py`），**不实现 runner，不执行 decoder，不构矩阵，不创建 `run_01`，不读 VAL/TEST 择优，不改1024维主体/V67/src**；正式 `run_01` 需独立 `PLAN_ACCEPT` + `EXECUTE_AUTH`；`DECODER_FREE` 表示零 `decode_* / construct_* / gf_rank / nested` 调用（`rg 0 hits`）。
- **Branch**: `formal-ir-mainline`；`HEAD` `b7e3417f` 重核，不一致阻塞；已与 `git rev-parse HEAD` 一致。`TBD` 0 hits，`f4040fc1` 0 hits 已验（V67 已清理）。
- **Data SHA**: `84d62779` (`d1024 bw200 nearest legacy_v1`) — V68 复用 V67 三 session Stage2 (`CAL1024+VAL256`)，不换点。
- **Session bound**: `total 3 (=V67 3)` 复用，`per_category 1,1,1`，不新增 acquisition。
- **Rate feasibility**: **m1_raw=ceil(1.3*1024*CE1/5), m2_raw=ceil(1.3*1024*CE2/5), raw_disclosure=5*(m1+m2)+64 不 cap**，择优键 `T=(max,sum,abs,S_lex)` 升序，分流阈 `m<1024 && raw<5120` 为 `BALANCED`。

## 2. 冻结方法（主体完全冻结，V68 零改，仅 S 重标记）

### 2.1 主体不变量（V64 完全冻结，V67 零改，V68 仅 S）

- `n=1024 symbols/block` (`4×256 frames`), `q=1024 (10-bit s)`, `GF32 poly37`, `tag=64 bits/block`。
- `H1 = V31-H1-QC 16×1024 rank16 80b` 母矩阵；`U_natural =32*U1+U2, F03 5+5` (`U1>>5, U2&31`) 参照；`U_permuted(S)=bits_S(s)/bits_{B\S}(s) 252种仅重标记`。
- `Lane C` ordinal-2 `s38310x`：`m2 base 1M 184 / 1p5M 190 / 2M 192` 全冻。
- `H_inc1 8×1024 + H_joint1 192×1024` nested；`H_inc2 8×1024 + H_total 200×1024` nested；`rank_total==m2+16` 等全冻，**本变更不构 H**。
- `decoder`: `decode_row_layered_fftqspa` `90/1.0 poly37 early-stop` (禁用至后续授权)；`rescue=verification-only`。
- `leak`: `leak=5*(m1+m2)+64`，`raw_disclosure` 不 cap。
- `verification`: `full-symbol tag s_hat=32*u1_hat+u2_hat compute_tag_64 canonical trunc64` (V64 22/24 PASS)，单64b。
- `budget 地图预冻结`: `V67 Stage2 CAL1024+VAL256` 每 session，`TEST` 密封，`m_raw` 由 `VAL CE` 得，择优键 `max→sum→abs→lex`。
- `V67 终态`: `3× NEAR_FULL_DISCLOSURE` natural 已固化，V68 以均衡重划分为纠正假设。

### 2.2 处理点与物化单点冻结

- `84d62779` 语义：`dimension 1024, bin_width 200ps, pairing nearest double-pointer bin//1024, rule legacy_v1, channels A1/B5, frame_len 256 pairs, BLOCK 1024, period 204800ps floor_div, threshold 40000ps, gate 200ps` — 单点，多 session provenance，各 session 单独物化后 `S` 重标记。
- `TEST` 密封：任何 `TEST/EVAL` 域不计 `CE/m/S*`；`C_ab/P/CE/m` 均 `CAL/VAL` 测，`TEST` 不读，`S*` 择优仅 `CAL`。
- **S 重标记**：`S∈C(10,5)=252` 升序枚举，`U1'=bits_S(s), U2'=bits_{B\S}(s)`，禁 `Gray/MET/protograph/SC` 外的重表示。

### 2.3 禁止

- 禁改任一冻结量、新增矩阵/标签/prior/阈值/decoder、试 `Δ8` 外 degree/seed 网格、跨 acquisition 拼接凑 `3`、将 `min(1024,ceil)` cap 伪装当通过、将 `VAL` 数据用于 `S*` 择优、将零重叠仅比 `frame_id`、引 `MET/protograph/SC/Gray`、改 `src/experiments/tools` 任何文件；禁读 `TEST` 统计；**m_raw 不 cap**；禁 `S` 剪枝至 `<252`；禁改 `T` 排序 `max→sum→abs→lex`；禁以平均替代 `max_{sess}` 选 `common`；禁构 `H/matrix/rank/nested`；未授 `EXECUTE_AUTH` 前禁 `decode_*`。

## 3. Phase A — 数据角色 (V67 Stage2 复用，252枚举前置)

### 3.1 角色与零重叠（键 `(source,session,frame)` 复用）

| 集合 | 每 session 规模 | 说明 |
|---|---|---|
| Stage2 CAL (Phase A) | 1024 frames (262144 pairs) | `C_ab → P` per `S` (252×) |
| Stage2 VAL (Phase B) | 256 frames (65536 pairs) | `CE → m_raw → raw_disclosure` per `S` (S*+S_nat) |
| TEST | 密封不读 | `used_test==False` |

- **复用**：`v68_data_registry.json` 由 `v67_data_registry.json` Stage2 原样复用 `sessions[3]`，`per_category 1,1,1`，`acquisition_dedup_verified:true`。
- **零重叠**：`CAL_key∩VAL_key==∅ && (CAL∪VAL)_key ∩ (V13..V67)_key ==∅`（键 `(source,session,frame)`），`not_cross_spliced:true`。
- **注册表**：`v68_data_registry.json` (`schema v68_data_v1`) 含 `sessions[3] {session_id, acquisition_id, source_label, provenance, stage2_CAL[1024], stage2_VAL[256], zero_overlap_verified, acquisition_dedup_verified, frozen, not_sorted_by_CE, reused_from v67}`，禁止事后换 session。
- **枚举**：`S_list = combinations(range(10),5)` 升序 252，`S_nat=(5,6,7,8,9)` 末位。

### 3.2 数据就绪门

- `total==3 && per_category 1,1,1 && acquisition_dedup_verified` 否则 `EVIDENCE_INCOMPLETE`。
- `|CAL|==1024 && |VAL|==256 && CAL∩VAL==∅ && (CAL∪VAL)∩(V13..V67)==∅` 否则 `EVIDENCE_INCOMPLETE`。
- `frame 256` + `s∈[0,1023]` 已验，否则 `EVIDENCE_INCOMPLETE`。

## 4. Phase B — 输入合同 strict V56 (仅 S 重标记)

- **合同项**：`dimension 1024, bin 200, pairing nearest bin//1024, legacy_v1, channels A1/B5, U_natural 32*U1+U2 5+5, U_permuted bits_S(S) 252种, frame_start_ps, period 204800, floor_div, mapping legacy_v1, 每帧256` 落 `v68_manifest.json`。
- **权威算法**：`_read_ttbin_timetags → _bin_indices_sorted_for_binwidth → _pairs_from_sorted_bins → 256分组 → legacy_v1 → U1U2 (natural) → bits_S 重标记` 原样复用，不重写。
- **不GE/MET**：`rg -i "met|protograph|sc_coupling" 0 hits` 已验（`S` 注释除外）。

## 5. Phase C/D — 枚举估计与两阶段选优 (252× CAL 4-fold + VAL确认，TEST不读)

### 5.1 C_ab 与 P_global (CAL-only per S per session)

```
C_ab[a,b] = bincount2d(a_cal, b_cal)  1024×1024, sum 262144 (CAL1024)
N_b[b] = Σ_a C_ab
P_global(a) = Σ_b C_ab / N_cal
Q=1024, n=1024
# per S: a 的 (u1',u2') 查表由 bits_S(s) 决定，C_ab 本身不按 S 重算，仅 P(U1'|B) 汇总按 S 变
```

### 5.2 层级先验与熵/CE (CAL 描述性 + VAL 门禁性，链式，TEST隔离，CAL-only 择优)

```
P(a|b) = (C_ab + λ P_global(a)) / (N_b + λ)  (N_b>0); P_global(a)  (N_b==0)
P(u1'|b) = Σ_{u2'} P( perm_S^{-1}(u1',u2') | b )  32×1024
CE1(S) = -E_{heldout/VAL} log2 P(U1'(S)|B)
CE2(S) = -E log2 P(U2'(S)|U1'(S),B)
CE_full = -E log2 P(A|B)
CE 链式: |CE_full - CE1(S) - CE2(S)| <1e-9 else EVIDENCE_INCOMPLETE
m1_raw(S) = ceil(1.3*1024*CE1/5), m2_raw(S) = ceil(1.3*1024*CE2/5)  (不 cap)
raw_disclosure(S) = 5*(m1_raw+m2_raw)+64
# S* 排序键来自 CAL held-out m_cv，VAL m_raw 仅度量确认
T(S) = (max(m1_cv,m2_cv), m1_cv+m2_cv, abs(m1_cv-m2_cv), S_lex)
S*_per_session = argmin_{S} T(S)  # 252升序唯一
T_common(S) = (max_{sess} max, max_{sess} sum, max_{sess} abs, S_lex)
S*_common = argmin_{S} T_common(S)
```

- **λ 择优**：`λ ∈[1e-2,1e4] log10` 仅 `CAL 内 4-fold` 最小 `CV NLL`，触界则 `MODEL_NOT_STABLE`，不扩网格。`VAL` 测时 `λ` 固定为 `CAL` 择优值，不重选。
- **阶段隔离**：`S*` 不读 `VAL`/`TEST`，`VAL` 仅对 `S*` 与 `S_nat` 度量；`used_val_in_selection==False && used_test==False` 已验。
- **Natural 参照**：`S_nat=(5,6,7,8,9)` 恒以同算法同 `VAL` 计量，报告 `ΔCE/Δmax/Δsum/Δraw`。

## 6. Phase E — 分流与总体 (per-session 4分流 + 总体3态 + common审计)

### 6.1 Per-session 4分流（优先级高→低，互斥）

```
if not materialization_ok or frame_256_violation or CE_chain_not_closed(S*) or provenance_fabricated:
    classification = V68_EVIDENCE_INCOMPLETE; successor = recollect
elif λ_at_boundary(S*) or ΔNLL>0.50 or val_b_context_unseen>0.01 or not isfinite(ValNLL) or not isfinite(DeltaNLL):
    classification = V68_MODEL_NOT_STABLE; successor = recollect_or_new_prior
elif m1_raw_val(S*) <1024 && m2_raw_val(S*) <1024 && raw_disclosure_val(S*) <5120:
    classification = V68_BALANCED_FEASIBLE; successor = balanced_code_design
else: # m1≥1024 or m2≥1024 or raw≥5120
    classification = V68_STILL_HEAVY; successor = new_representation
```

- `LaneC+8+8` 仅描述性，不入 `BALANCED` 门禁；`NEAR_FULL` 阈 `≥1024` / `raw≥5120`；`capacity_warning` 正交，仅描述不过门禁；旧三项 `ValNLL>H+1 / H+0.5 / joint>1%` 改归 `descriptive_diagnostics`。

### 6.2 总体3态 + common审计

```
common_feasible = #{sess | S*_common 在该 sess 上 BALANCED_FEASIBLE (VAL)}
per_session_feasible = #{sess | S*_per_session 在该 sess 上 BALANCED_FEASIBLE}
if common_feasible ==3:
    overall = V68_OVERALL_BALANCED_COMMON_FEASIBLE
elif per_session_feasible >=1:
    overall = V68_OVERALL_BALANCED_PER_SESSION_ONLY
else:
    overall = V68_OVERALL_STILL_HEAVY
# 若有 EVIDENCE/MODEL 混入，overall 前缀 EVIDENCE_INCOMPLETE / MODEL_NOT_STABLE 但主体 3 态仍按 feasible 计数
counts_per_classification = {EVIDENCE_INCOMPLETE, MODEL_NOT_STABLE, BALANCED_FEASIBLE, STILL_HEAVY}
audit = {S*_per_session[3], S*_common, T_per_session[3], T_common, natural_T[3], common_feasible_count, per_session_feasible_count, cal_val_consistency[3]}
```

## 7. Phase F — 报告与表 (per session 252 + S* + natural + overall 3态 + common审计)

- **表 schema** (`v68_table.csv/.json` 行对等, 3×252 + 汇总 + natural 行)：
```
session_id, acquisition_id, source_label, provenance,
S_tuple, S_lex_index, S_bits, # S=(a,b,c,d,e) 5元组
CAL: CAL_lambda, CAL_lambda_at_boundary, CAL_DeltaNLL, CAL_ValNLL, CAL_H_cal, CAL_val_b_context_unseen, CAL_joint_cell_unseen, CAL_q_mass_unseen (descriptive), CAL_descriptive×3, CAL_capacity_warning×3, CAL_effective_contexts,
VAL: CE1, CE2, CE_full, chain_delta, ValNLL, DeltaNLL, val_b_context_unseen, joint_cell_unseen, q_mass_unseen (descriptive), descriptive×3, capacity_warning×3, m1_raw, m2_raw, raw_disclosure, max_m, sum_m, abs_m,
is_S_star_per_session, is_S_star_common, is_S_nat,
per_session_classification (仅 S* 行有效), successor, cal_val_consistency
# 另汇总行: per_session S*, common S*, overall
```
- **报告** `V68_BALANCED_REPORT.md`：`per session 252 选优 + S*_per_session + S*_common + natural参照 + CAL/VAL 双组 CE/λ/ΔNLL/unseen/m/max/sum/abs/classification/successor/cal_val_consistency + overall 3态 + common审计 + map_sparse + TEST隔离 + 1024维冻结` 与 `json/csv` 一致，不扩大为 `FER/SKR`。

## 8. 守卫 R68-01~10

| 守卫 | 条件 | 阈值 |
|---|---|---|
| R68-01 | 冻结主体 1024维 GF32两层验证不改 | `n1024 q1024 GF32 poly37 H1 16×1024 rank16 U_natural 32*U1+U2 (仅 S 重标记) Lane C/H_inc Δ8 decoder 90/1.0 full-tag git diff src==0` |
| R68-02 | 枚举252子集完整 | `C(10,5)==252 && combinations(range(10),5) 升序 252 行每 session && not剪枝` |
| R68-03 | 升序唯一词典序 max→sum→abs→lex | `T(S)=(max,sum,abs,S_lex) 升序唯一, T_common 同理, S* 确定性` |
| R68-04 | Phase A CAL-only 选 S* | `S* 来自 CAL m_cv, used_val_in_selection==False && used_test==False` |
| R68-05 | Phase B VAL确认+natural参照 | `VAL256 上 S*与S_nat {5,6,7,8,9} 均 CE/m/chain 已计, |CE_full-CE1-CE2|<1e-9, natural Δ 已报告` |
| R68-06 | V67三Session Stage2 复用 | `v68 registry == v67 Stage2 3 sessions, total 3 per_cat 1,1,1 acq_dedup_verified zero_overlap_verified` |
| R68-07 | per-session 4分流+总体3态+common审计 | `classification 按 EVIDENCE>MODEL>BALANCED>STILL_HEAVY 互斥, overall 3态, S*_per_session+S*_common+common_feasible_count 已落盘` |
| R68-08 | 四工件+test 完整 | `v68_data_registry + v68_results + v68_table.csv/json 行对等 + V68_BALANCED_REPORT + test_v68_spike_small.py py_compile+pytest PASS` |
| R68-09 | decoder-free不构矩阵 | `rg "decode_|construct_|gf_rank|nested" 0 hits && rg -i "met|protograph" 0 hits && no H built` |
| R68-10 | 不创 run_01+编译+小测试+TEST隔离 | `run_01 不存在 && py_compile PASS && pytest 小测试 PASS && used_test==False && grep "min(1024" 0 hits && m_raw 不 cap` |

## 9. 脚本与证据写出 (预冻结，decoder-free，不构矩阵)

- **固定脚本**（本轮）：
  - `scripts/v68_spike.py`: `CAL1024 252×C_ab/P/λ→m_cv→T→S* → VAL256 S*/S_nat CE/m`，输出 `v68_data_registry.json + v68_results.json + v68_table.(csv|json) + v68_manifest.json + V68_BALANCED_REPORT.md`，`rg "decode_|construct_|gf_rank|nested" 0 hits`，`rg -i "met|protograph" 0 hits`，`py_compile PASS`，`m_raw` 未 cap，`VAL` 未参与选优，`CE 链式` 已验，`252` 已验。
- **证据**：
```
openspec/changes/formal-ir-v68-balanced-gf32-bit-partition/  # 本轮 plan 四工件
scripts/v68_spike.py  # decoder-free, 252枚举
v68_data_registry.json (复用 V67 Stage2 3 sessions)
v68_results.json (per session 252 CE/m + S*/natural + VAL确认)
v68_table.csv/.json (252×3 + 汇总, classification/successor)
V68_BALANCED_REPORT.md
v68_manifest.json (frozen_body + guards R68-01~10)
test_v68_spike_small.py
comparison_bench/outputs_comparison/formal_ir_methods/v68_balanced_partition/  # 未来 run_01 (本轮不建)
```
- **文件**：`v68_data_registry.json` (authoritative `3` 实表，复用 V67 Stage2) + `v68_results.json` + `v68_table` (行对等) + `v68_manifest.json` (frozen_body + guards) + `V68_BALANCED_REPORT.md` + 控制台摘要；本轮仅冻结计划，不创建正式 run_01，**已单独提交推送新 Plan SHA**。

## 10. 验收

- **本轮 plan 自检 gate（A-G 已闭合）**：`py_compile PASS` spike，`rg "decode_|construct_|gf_rank|nested" 0 hits`，`rg -i "met|protograph" 0 hits`，`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0 && git diff -- openspec/changes/formal-ir-v6[0-7]/ ==0` (除本变更+scripts 外零改)，`VAL` 未参与 `S*` 选优已验 (`used_val_in_selection==False`)，`TEST` 未读已验 (`used_test==False`)，`m_raw` 未 cap 伪装已验 (`grep "min(1024" 0 hits` 且 `m_raw` 显式)，`S 252` 枚举升序已验，`T max→sum→abs→lex` 唯一已验，`4分流优先级互斥` 已验，`overall 3态+common审计` 已验，`V67 Stage2 复用 3` 已验，`natural参照` 已验，`capacity_warning` 正交与 `descriptive` 已落盘，`run_01` 不存在已验，**报告表与 json 一致**，`TBD` 0 hits。
- **本轮仅 plan 四工件+registry+spike+报告表（CAL-only 252枚举）**，任何 `V68` 后的码设计/decoder 需 `Plan SHA` + `v68_data_registry.json` 实表 + `252选优+VAL确认+自然Δ` 已验后、且独立 `PLAN_ACCEPT` + `EXECUTE_AUTH` 后才允许创建正式实现并执行；`DECODER_FREE` 保持至授权。
