## Historical implemented scope — formal-ir-v68-balanced-gf32-bit-partition

This section preserves only the archived, reviewed scope named below. It does not change the archived source. Current repository AGENTS.md and reboot handoff R1–R9 take precedence. This historical merge grants no new execution, acceptance, qualification, promotion, publication, decoder work, or probe restart.

<!-- Source: openspec/changes/archive/2026-10-04-formal-ir-v68-balanced-gf32-bit-partition-completed/specs/spec.md -->

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

<!-- Source: openspec/changes/archive/2026-10-04-formal-ir-v68-balanced-gf32-bit-partition-completed/specs/spec.md -->

## 5. Phase C/D — 枚举估计与两阶段选优 (252× CAL 4-fold + VAL确认，TEST不读)

### 5.1 C_ab 与 P_global (CAL-only per S per session)

```
C_ab[a,b] = bincount2d(a_cal, b_cal)  1024×1024, sum 262144 (CAL1024)
N_b[b] = Σ_a C_ab
P_global(a) = Σ_b C_ab / N_cal
Q=1024, n=1024

<!-- Source: openspec/changes/archive/2026-10-04-formal-ir-v68-balanced-gf32-bit-partition-completed/specs/spec.md -->

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

<!-- Source: openspec/changes/archive/2026-10-04-formal-ir-v68-balanced-gf32-bit-partition-completed/specs/spec.md -->

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

<!-- Source: openspec/changes/archive/2026-10-04-formal-ir-v68-balanced-gf32-bit-partition-completed/specs/spec.md -->

## 7. Phase F — 报告与表 (per session 252 + S* + natural + overall 3态 + common审计)

- **表 schema** (`v68_table.csv/.json` 行对等, 3×252 + 汇总 + natural 行)：
```
session_id, acquisition_id, source_label, provenance,
S_tuple, S_lex_index, S_bits, # S=(a,b,c,d,e) 5元组
CAL: CAL_lambda, CAL_lambda_at_boundary, CAL_DeltaNLL, CAL_ValNLL, CAL_H_cal, CAL_val_b_context_unseen, CAL_joint_cell_unseen, CAL_q_mass_unseen (descriptive), CAL_descriptive×3, CAL_capacity_warning×3, CAL_effective_contexts,
VAL: CE1, CE2, CE_full, chain_delta, ValNLL, DeltaNLL, val_b_context_unseen, joint_cell_unseen, q_mass_unseen (descriptive), descriptive×3, capacity_warning×3, m1_raw, m2_raw, raw_disclosure, max_m, sum_m, abs_m,
is_S_star_per_session, is_S_star_common, is_S_nat,
per_session_classification (仅 S* 行有效), successor, cal_val_consistency

<!-- Source: openspec/changes/archive/2026-10-04-formal-ir-v68-balanced-gf32-bit-partition-completed/specs/spec.md -->

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
