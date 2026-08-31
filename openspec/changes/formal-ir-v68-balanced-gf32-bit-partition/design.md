# OpenSpec Design: formal-ir-v68-balanced-gf32-bit-partition

**Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — **1024维符号 GF32两层验证冻结仅重划分10 bits，CAL-only 252枚举按升序唯一词典序 max→sum→abs→lex 选 S*，Phase A CAL-only Phase B VAL确认报告 natural 参照，V67三Session Stage2 复用，per-session 4分流 + 总体3态 + common审计，不跑decoder不构矩阵**

**Cycle**: `V68-BAL` (balanced-gf32-bit-partition), predecessor `V67-MAP (b7e3417f V67_FEASIBILITY_MAP_ACCEPTED 3× NEAR_FULL)` + `V64 22/24 PASS` + `V66 832e5394`, HEAD `b7e3417f` data `84d62779` 单点 `d1024 bw200 nearest legacy_v1`

**Feasibility**: `V67` 3 sessions 上 `natural 5+5 (s>>5 / s&31)` 均 `m1_raw≥1024 (1024–1199)` 且 `raw_disclosure 9589–11379` 证 `NEAR_FULL`，`λ` 未触边、`ΔNLL≤0.05`、`val_b 0` 证模型稳定但天然不均衡；`V68` 以均衡重划分纠正不均衡为假设，decoder-free 验证 `∃S: m1<1024&&m2<1024`。

**Key judgement**: **在 V67 三 session 的 `Stage2 CAL1024/VAL256` 上，仅重标记 10 bits 的 5-bit 子集 `S`（252 种），是否存在 CAL-only 选优的 `S*` 使 `VAL` 上 `m1_raw(S*)<1024 && m2_raw(S*)<1024`，若存在则 V67 imbalance 可被 bit-partition 均衡纠正，否则需更深表示。**

## 1. 科学问题与关键判断

> 在**完全冻结主体**（`n1024 q1024 GF32 poly37 H1-16 Lane C 184/190/192 H_inc Δ8 decoder 90/1.0 full-tag canonical 32*U1+U2 leak 5*(m1+m2)+64`，**不改1024维符号/q/GF/两层/验证**）下，**仅重划分 10-bit 符号的 5+5 比特分割**：对 `B={0..9}` 的全部 `S⊂B, |S|=5`（`C(10,5)=252`）定义 `U1'=bits_S(s), U2'=bits_{B\S}(s)`，每 `S` 在 `CAL1024` 上估 `P(U1'|B)/P(U2'|U1',B)`（`λ` 仅 CAL 4-fold），在 `VAL256` 上计量 `CE1/CE2 → m1_raw/m2_raw ceil不cap`，以升序唯一词典序 `max→sum→abs→lex` 选 `S*`，`Phase A CAL-only` 不读 VAL/TEST，`Phase B VAL` 确认并报告 `natural S_nat={5,6,7,8,9}` 参照，复用 V67 三 Session Stage2，每 session 4分流 `EVIDENCE_INCOMPLETE/MODEL_NOT_STABLE/BALANCED_FEASIBLE/STILL_HEAVY` + 总体3态 `BALANCED_COMMON_FEASIBLE / BALANCED_PER_SESSION_ONLY / STILL_HEAVY` + `common S*_common` 审计。全程 decoder-free，不构矩阵。

- **对照**：`V67 natural` `m1 1024–1178 / m2 881–1057 / raw 9589–11239` 为不均衡基线；`V68` 以 `ΔCE/Δm/Δmax` 显式对照。
- **不变量**：`dimension 1024 / bin200 / nearest legacy_v1 / channels A1/B5 / GF32 / Lane C / H_inc Δ8 / full-tag` 全冻结；**本变更仅 `S` 重标记**。
- **地图性质**：纯 decoder-free，252 枚举 + 唯一词典序选优 + CAL-only/VAL-confirm 两阶段，`TEST` 密封不读，V67 三 session 并列分流 + common 审计。

## 2. 冻结语义 — 主体与处理点零改（1024维符号 GF32两层验证，不重构）

| 项 | 冻结值 | 来源 |
|---|---|---|
| n/d | 1024 | V31/V54/V64 |
| q | 1024 (10-bit `s ∈[0,1023]`) | V25/V38 |
| GF | GF32 poly37 | GF2mField |
| U 自然 (参照) | `U1_nat=s>>5, U2_nat=s&31, F03 5+5` | V25/V67 |
| U 重划分 (本变更) | `U1'=bits_S(s), U2'=bits_{B\S}(s), S⊂{0..9}, |S|=5, C(10,5)=252` 仅重标记 | V68 |
| m1 base | 16 | V31 H1 |
| Lane C base m2 | `1M 184 / 1p5M 190 / 2M 192` | V54→V64 |
| H_total base | `200/206/208` | V64 |
| H_inc | `Δ8` 家族 nested | V54 |
| decoder (冻结禁用) | `90/1.0 poly37 early-stop` | V43 — 地图期禁用 |
| Verification | `full-symbol tag 32*U1+U2 canonical 64b` | V64 — 禁用期仍冻结 |
| Data SHA | `84d62779` `d1024 bw200 nearest legacy_v1` | V55 |
| 多 session 复用 | `V67 3 sessions Stage2 CAL1024+VAL256` 原样 | V67 `v67_data_registry.json` |
| 分阶段 | `Phase A CAL-only 选 S* → Phase B VAL256 确认` | V68 |

**禁令**：`SHALL NOT` 任何 `decode_* / construct_* / gf_rank / nested`；`SHALL NOT` 调 `m2/leak/decoder/prior/H1/Lane C/H_inc/verification`；`SHALL NOT` 引 `MET/protograph/SC/Gray`（除 `S` 纯比特重划分注释）；`SHALL NOT` 跨 acquisition 拼接；`SHALL NOT` 以 `VAL/TEST` 调 `S*`；`SHALL NOT` `min(1024,ceil)` cap；`SHALL NOT` 剪枝 252。

## 3. 数据角色 — V67 三预注册 Stage2 复用（每类≤3 机械已验）

### 3.1 复用与零重叠（键 `(source,session,frame)` + `(source_label, acquisition_id)`）

| 集合 | 每 session 规模 | 来源 | 说明 |
|---|---|---|---|
| Stage2 CAL (Phase A 用) | 1024 frames =262144 pairs | `v67_data_registry: stage2_CAL[1024]` | `C_ab → P_global → P(U1'|B)/P(U2'|U1'B) λ(CAL 4-fold)` per `S` |
| Stage2 VAL (Phase B 用) | 256 frames =65536 pairs | `v67_data_registry: stage2_VAL[256]` | `CE1/CE2/CE_full 链式 → m1_raw/m2_raw ceil → raw_disclosure` per `S` |
| TEST | 密封不读 | `V65 TEST 120 / V66 EVAL 24` | `used_test==False` |

- **复用**：`v68_data_registry.json` 由 `v67_data_registry.json` 的 3 sessions (`20260123_1M_600k_0dB 1M, 20260107_PPLN_1p5M 1p5M, 20260123_2M_1p2M_0dB 2M`) 的 `stage2_CAL[1024] + stage2_VAL[256]` 原样拷贝（`total 3, per_category 1,1,1, acquisition_dedup_verified, frozen, not_sorted_by_CE`），`zero_overlap_verified` 与 `V13..V67` 零重叠已验，禁止事后换 session 或按 `CE/m` 替换。
- **不重估计 V67**：V67 的 `natural` `CE/m` 仅引用对照，不在 V68 上重算 `natural` 的 `C_ab`（但 V68 的 `VAL` 计量会对 `S_nat` 同算法重算以保一致口径，报告 `Δ`）。
- **注册表**：`v68_data_registry.json` (`schema v68_data_v1, lifecycle PLAN_CANDIDATE, data_sha 84d62779, head b7e3417f, reused_from v67`) 含 `sessions[3] {session_id, acquisition_id, source_label, provenance, stage2_CAL[1024], stage2_VAL[256], zero_overlap_verified, acquisition_dedup_verified}`。

### 3.2 数据就绪门（decoder-free）

```
assert total_sessions==3 && per_category 1,1,1 && acquisition_dedup_verified
assert per session |CAL|==1024 && |VAL|==256 && CAL∩VAL==∅ (key=(source,session,frame))
assert CAL∪VAL ∩ (V13..V67) ==∅
assert frame 256 && s∈[0,1023] && natural U==32*U1+U2
```

## 4. 输入合同 — 严格复用 V56 权威算法（仅新增 S 重标记）

| 阶段 | 参数 | 冻结值 |
|---|---|---|
| 1 | dimension | 1024 |
| 2 | bin_width | 200 ps |
| 3 | pairing | `nearest`, double-pointer `bin//1024` |
| 4 | rule/mapping | `legacy_v1` |
| 5 | channels | `A:1 , B:5` |
| 6 | U 自然 | `s=32*u1+u2, U=32*U1+U2, F03 5+5` (参照) |
| 7 | U 重划分 | `S⊂{0..9}, |S|=5, U1'=bits_S(s), U2'=bits_{B\S}(s), 252种` |
| 8 | frame anchor | `frame_start_ps / period 204800ps / floor_div` |
| 9 | H1/Lane C | 只读冻结 |

## 5. 估计器 — 枚举252 × 层级先验 + 唯一词典序选优（Phase A CAL-only / Phase B VAL确认）

### 5.1 联合计数与全局先验 (CAL-only per S per session)

```
C_ab = bincount2d(a_cal, b_cal)  shape 1024×1024, sum N_cal=262144
N_b = Σ_a C_ab  shape 1024
P_global(a) = Σ_b C_ab / N_cal
Q=1024
# per S: 将 a 分解为 (u1'(S), u2'(S)) 查表，不改 C_ab，仅改 P(U1'|B) 汇总维度
```

### 5.2 分层条件分布与 λ 择优（仅 CAL 内 4-fold，不扩，TEST隔离）

```
P(a|b) = (C_ab + λ P_global(a)) / (N_b + λ) if N_b>0 else P_global(a)
# per S:
P(u1'|b) = Σ_{u2'} P( perm_S^{-1}(u1',u2') | b )   32×1024
P(u2'|u1',b) = P(a|b)/P(u1'|b) if >0 else 1/32
λ ∈ [1e-2, 1e4] log10 连续搜索，最小化 CAL 内 4-fold CV NLL (每 fold 256 frames 65536 pairs)
  边界最优 → MODEL_NOT_STABLE，不扩
```

### 5.3 VAL 交叉熵与 raw 冗余（VAL 确认，TEST隔离，链式，含 natural 参照）

```
CE_full(S) = -E_VAL[ log2 P( A | B ) ]  (与 S 无关，但每 S 的分解链式校验)
CE1(S) = -E_VAL[ log2 P( U1'(S) | B ) ]
CE2(S) = -E_VAL[ log2 P( U2'(S) | U1'(S), B ) ]
链式校验 |CE_full - CE1(S) - CE2(S)|<1e-9 else EVIDENCE_INCOMPLETE (per S)
m1_raw(S) = ceil(1.3*1024*CE1(S)/5)  ∈ [0,∞)  # 不 cap
m2_raw(S) = ceil(1.3*1024*CE2(S)/5)
raw_disclosure(S) = 5*(m1_raw+m2_raw)+64  # 不 cap
# natural S_nat={5,6,7,8,9} 同算法同 VAL 计量，恒报告 natural_vs_S* Δ
m1_nat = m1_raw(S_nat), m2_nat = m2_raw(S_nat)  # 对照 V67 已验 1024..1199
```

- **EVAL/TEST 禁用**：`S*` 选择不读 `VAL`/`TEST` 统计，Phase A 仅 CAL，违则 `EVIDENCE_INCOMPLETE`。
- **Phase B 独立**：`VAL` 上 `CE/m_raw` 仅度量，不重选 `S*`，`S*_common` 亦 CAL-only 选后 VAL 度量。

### 5.4 升序唯一词典序目标（max→sum→abs→lexicographic）

```
T(S) = ( max(m1_raw(S), m2_raw(S)),  m1_raw(S)+m2_raw(S),  abs(m1_raw(S)-m2_raw(S)),  S_lex )
其中 S_lex = tuple(sorted(S)) 的字典序，例如 (0,1,2,3,4) < (0,1,2,3,5) < ... < (5,6,7,8,9)
S*_per_session = argmin_{S ∈ 252} T(S) 升序（Python tuple 升序即唯一）
T_common(S) = ( max_{sess} max(m1,m2),  max_{sess} sum,  max_{sess} abs,  S_lex )  # 跨 3 sessions 的 worst 聚合
S*_common = argmin_{S} T_common(S) 升序
# m_raw 计算用 VAL 度量，但在 Phase A 选优时 VAL 未读，故 Phase A 以 CAL 上预估 CE？→ 本设计以 VAL 度量选优但 CAL-only 选 S* 的矛盾需调和：
# 实际：Phase A 枚举时对每个 S 以 CAL 4-fold 的 ValNLL 代理 CE 进行 T 排序选 S*，Phase B 再以真实 VAL 度量确认 report。
# 为保 CAL-only 且 VAL 确认两阶段正交，本设计采用：S* 排序键的 m_raw 来自 CAL 的 CV 估计（CAL-heldout 折内 NLL），VAL 上 m_raw 仅度量确认不重选。
```

简化实现（ponytail）：`S*` 的 `T` 排序键直接用 `VAL` 上 `m_raw` 但脚本内显式 `CAL-only` 标记为 `used_val_in_selection=False` 的变通是不自洽的。为真正 CAL-only，本设计冻结：**`S*` 的 `m1/m2` 排序键取自 `CAL` 内 4-fold 的 held-out `CE1_cv/CE2_cv` 导出的 `m1_cv/m2_cv`**（每 fold 的 held-out 均值），`VAL` 上仅报告 `m1_val/m2_val` 确认；若 `CAL_cv` 与 `VAL` 的 `S*` 不一致，报告 `cal_val_consistency` 但以 `CAL` 的 `S*` 为准，`VAL` 不重选。

## 6. 分流判定（per-session 4分流 + 总体3态 + common审计）

### 6.1 Per-session 4分流（优先级高→低，互斥）

```
if not materialization_ok or frame_256_violation or CE_chain_not_closed(S*) or provenance_fabricated:
    classification = V68_EVIDENCE_INCOMPLETE
elif λ_at_boundary(S*) or ΔNLL>0.50 or val_b_context_unseen>0.01 or not isfinite(ValNLL) or not isfinite(DeltaNLL):
    classification = V68_MODEL_NOT_STABLE   # q_mass/joint/H_cal 仅 descriptive，不入
elif m1_raw_val(S*) <1024 && m2_raw_val(S*) <1024 && raw_disclosure_val(S*) <5120:
    classification = V68_BALANCED_FEASIBLE  # 含 natural 参照 Δ 需显式
else: # m1≥1024 or m2≥1024 or raw≥5120
    classification = V68_STILL_HEAVY
```

- **阈值冻结**：`MODEL_NOT_STABLE` 的 `ΔNLL≤0.50` 且 `val_b_context_unseen≤1%` 且 `λ∈(1e-2,1e4)` 开区间；`BALANCED_FEASIBLE` 的 `<1024` 为单 plane 行数满秩阈，`5120≈10*1024/2` 为近半披露阈，仅描述不过 `MODEL` 门禁；`capacity_warning_m1/m2/disclosure`（`m1≥1024 / m2≥1024 / raw≥5120`）为正交旗标，仅描述不过门禁；`LaneC+8+8` 仅描述性，不入 `BALANCED` 门禁。
- **Successor**：`EVIDENCE_INCOMPLETE → recollect`，`MODEL_NOT_STABLE → recollect_or_new_prior`，`BALANCED_FEASIBLE → v68_balanced_code_design`，`STILL_HEAVY → v68_new_representation`。
- **Natural 参照**：每 session 表中恒含 `m1_nat/m2_nat/raw_nat` 与 `S*` 的 `ΔCE/Δmax/Δsum` 显式。

### 6.2 总体3态 + common审计

```
common_feasible = count_{sess} [ classification == BALANCED_FEASIBLE ]  # 0..3
per_session_feasible = common_feasible  # 同值，但总体 3 态按 common S*_common 的 VAL 度量二次确认
if common S*_common 在 3 sessions 上均 BALANCED_FEASIBLE (VAL) :
    overall = V68_OVERALL_BALANCED_COMMON_FEASIBLE
elif per_session_feasible ≥1 (存在 S*_per_session feasible 但 common 不 feasible):
    overall = V68_OVERALL_BALANCED_PER_SESSION_ONLY
else: # 0 feasible
    overall = V68_OVERALL_STILL_HEAVY
# 若有 EVIDENCE/MODEL 混入，则 overall 前缀 V68_OVERALL_EVIDENCE_INCOMPLETE / MODEL_NOT_STABLE 但主体 3 态仍计
audit = { S*_per_session[3], S*_common, T_per_session[3], T_common, natural_T[3], common_feasible_count, per_session_feasible_count, cal_val_consistency[3] }
```

- 总体不设 `FAIL`，即便全部 `STILL_HEAVY` 亦 `COMPLETE`（地图完成，结论为需新表示）；仅 `<3` session 视为 incomplete map（但 V68 固定 3）。
- 报告需附 `counts_per_classification (4分流)` 与 `common 审计表`。

## 7. 脚本与报告（decoder-free 守卫 + 252枚举回填）

- **脚本 `scripts/v68_spike.py`** (decoder-free):
  `python scripts/v68_spike.py [--registry v68_data_registry.json] [--out v68_results.json]`
   → 每 session `CAL1024 上 252×(C_ab/P/λ) → CV CE1/CE2 → m1_cv/m2_cv → T(S) 排序选 S*_per_session(CAL) → VAL256 上对 S* 与 S_nat 计 CE/m/raw`，`S*_common` 跨 session `T_common` 选，`rg "decode_|construct_|gf_rank|nested" 0 hits`，`rg -i "met|protograph|sc_coupling" 0 hits`，`py_compile PASS`；输出 `v68_results.json + v68_table.{csv,json} + 控制台摘要`；校验 `TEST 未参与`、`VAL 未参与选优`、`m_raw` 未 cap、`252 已枚举`。
- **报告 `V68_BALANCED_REPORT.md`**：`per session 252 选优表 + S*_per_session + S*_common + natural参照 + CAL/VAL 双组 CE/λ/ΔNLL/unseen/m/max/sum/abs/classification/successor/stage_consistency/cal_val_consistency + overall 3态 + common审计` 与 `json/csv` 一致，不扩大为 `FER/SKR`。
- **守卫**：地图期零 decoder、零矩阵构造、多 session 并列分流、**不创建 `run_01`**、不比较方法、不调 V68 以外码；**四工件+registry+spike 已单独提交推送，新 Plan SHA 已生成**。

## 8. 守卫 R68-01~10（decoder-free, 不构矩阵, 不创 run_01, V67复用）

| 守卫 | 检查 | 阈/断言 |
|---|---|---|
| R68-01 | 冻结主体 1024维 GF32两层验证不改 | `n1024 q1024 GF32 poly37 H1 16×1024 rank16 U=32*U1+U2 natural (仅 S 重标记) Lane C/H_inc Δ8 decoder 90/1.0 full-tag canonical git diff src==0` |
| R68-02 | 枚举252子集完整 | `C(10,5)==252 && itertools.combinations(range(10),5) 升序 252 行每 session && not剪枝` |
| R68-03 | 升序唯一词典序目标 max→sum→abs→lex | `T(S)=(max,sum,abs,S_lex) 升序唯一, T_common 同理, S* 确定性` |
| R68-04 | Phase A CAL-only 选 S* | `S* 排序键来自 CAL 4-fold m_cv, used_val_in_selection==False && used_test==False` |
| R68-05 | Phase B VAL确认 + natural参照 | `VAL256 上 S* 与 S_nat {5,6,7,8,9} 均 CE/m/chain 已计, |CE_full-CE1-CE2|<1e-9, natural Δ 已报告` |
| R68-06 | V67三Session Stage2 复用 | `v68 registry sessions==v67 Stage2 3 sessions, total 3 per_cat 1,1,1 acq_dedup_verified zero_overlap_verified` |
| R68-07 | per-session 4分流 + 总体3态 + common审计 | `classification 按 EVIDENCE>MODEL>BALANCED>STILL_HEAVY 互斥, overall 3态, S*_per_session+S*_common+common_feasible_count 已落盘` |
| R68-08 | 四工件 + test 完整 | `v68_data_registry + v68_results + v68_table.csv/json 行对等 + V68_BALANCED_REPORT + test_v68_spike_small.py py_compile+pytest PASS` |
| R68-09 | decoder-free 不构矩阵 | `rg "decode_|construct_|gf_rank|nested" 0 hits && rg -i "met|protograph" 0 hits && no H matrix built` |
| R68-10 | 不创 run_01 + 编译 + 小测试 + TEST隔离 | `ls .../v68_*/run_01 不存在 && py_compile PASS && pytest 小测试 PASS && used_test==False && m_raw 不 cap (grep "min(1024" 0 hits)` |

## 9. 与 V64/V66/V67/V68 衔接

- V64 `full-tag` 语义与 `H_total 200/206/208` 冻结构及 `22/24 PASS` 已固化；V67 3 sessions 均 `NEAR_FULL` 证 natural 5+5 不均衡；V68 为**同域比特级均衡性地图**，与 V67 正交复用 Stage2，不重估计 V67。
- 若 `V68_OVERALL_BALANCED_COMMON_FEASIBLE` 则 V67 imbalance 可被 `S*_common` 纠正，后续 `V69` 可直接复用该 `S*` 走平衡码设计；若 `BALANCED_PER_SESSION_ONLY` 则需 per-session 自适应；若 `STILL_HEAVY` 则需更深 `Gray/2+8` 等新表示（另起 OpenSpec）。
- 本变更不创建 `run_01`，任何 `V68` 后续码设计/decoder 需另起 `EXECUTE_AUTH`。

## 10. 自由裁量 D1-D7

- D1 完全冻结主体（`H1/Lane C/Δ8/decoder/full-tag`），V68 仅 `S` 重划分，不改码（多 session）。
- D2 单一层级估计器 `P(a|b)=(C_ab+λ P_global)/(N_b+λ)`，每 `S` 独立重估 `P(U1'|B)/P(U2'|U1'B)`。
- D3 泄漏 `raw_disclosure=5*(m1+m2)+64` 不 cap，`BALANCED_FEASIBLE` 限 `m1<1024&&m2<1024&&raw<5120`。
- D4 数据 `Stage2 CAL1024 VAL256` 确定性复用 V67，不搜索多划分，TEST隔离。
- D5 4分流 per-session + 3态 overall + common审计，不以平均替代。
- D6 不产生新矩阵/码参数，仅 `S*` 与 successor 建议，`BALANCED` 方可进入后续码设计。
- D7 本变更为 `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`，不产生 `run_01`，任何 decoder 需 `PLAN_ACCEPT + EXECUTE_AUTH` 后才允。
