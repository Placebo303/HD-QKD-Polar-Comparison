# OpenSpec Proposal: formal-ir-v68-balanced-gf32-bit-partition

**Status**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — 仅计划四工件 + decoder-free 只读 bit-partition 地图，不改1024维符号 GF32两层验证框架，仅重划分10 bits 找 CAL-only 均衡 5-bit U1 子集，不跑 decoder 不构矩阵

**Domain**: Formal IR / NB-LDPC balanced bit-partition (V67 同域直接后继，V67 三预注册 Stage2 复用)

**Change ID**: `formal-ir-v68-balanced-gf32-bit-partition`

**Cycle ID**: `V68-BAL` (balanced-gf32-bit-partition), predecessor `formal-ir-v67-multisession-feasibility-map` (`b7e3417f` `V67_FEASIBILITY_MAP_ACCEPTED` 3 sessions 均 `NEAR_FULL_DISCLOSURE`) + `formal-ir-v66-single-segment-adaptive-nbldpc` (`832e5394`) + `formal-ir-v64` (`22/24 PASS`)

**Branch**: `formal-ir-mainline`

**HEAD**: `b7e3417f` (V67 清理后冻结 HEAD，本变更基于此；推送后以 `git rev-parse HEAD == origin/formal-ir-mainline` 40位重核)

**Data SHA**: `84d62779` (`84d62779603e62de50ded5182ed65b65d3dc6084`, `d=1024 bw=200ps pairing=nearest rule=legacy_v1` 单点；V68 复用 V67 三 session 的 `Stage2 CAL1024+VAL256`，不换点，不换 bin/mapping，不新增 acquisition)

**Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — 本轮止于计划四工件 + decoder-free 均衡 partition 地图（registry 复用 + spike枚举252 + results + table + report + small test），零 decoder/矩阵/新依赖（`numpy/pandas/pyarrow` 已装），不创建 `run_01`，不比较方法，不转 qualification，任何 decoder 执行需独立 `PLAN_ACCEPT + EXECUTE_AUTH`

> ponytail lite: 本变更仅 4 OpenSpec 工件 + 1 decoder-free spike (枚举252子集，`numpy` 直算 `C_ab` + `itertools.combinations`，不引 `scipy/sklearn`) + 1 结果表 + 1 报告 + 1 小测试；零 decoder/矩阵/新依赖，最短科学路径。laziest alternative: `numpy` + `itertools` 穷举，不做启发式剪枝。

> **科学问题（冻结）**：于**完全冻结主体**（`n=1024, q=1024 (10-bit), GF32 poly37, H1 16×1024 rank16, Lane C 184/190/192, H_inc Δ8, decoder 90/1.0 poly37, full-tag canonical 32*U1+U2, leak 5*(m1+m2)+64` 全只读，**不改维度/符号/q/GF/两层/验证**）下，**仅重划分 10 bits 的 5+5 均衡性**：对 10-bit 符号 `s∈[0,1023]` 的比特位置集合 `B={0..9}`，枚举全部 `C(10,5)=252` 个 5-bit 子集 `S⊂B, |S|=5` 定义新分解 `U1' = bits_S(s) (5-bit, 0..31), U2' = bits_{B\S}(s) (5-bit)`，以 `CAL1024` 独立重估的 `P(U1'|B)/P(U2'|U1',B)` 在 `VAL256` 上得 `m1_raw=ceil(1.3*1024*CE1/5), m2_raw=ceil(1.3*1024*CE2/5)` **不 cap**，证明是否存在 `S*` 使 `m1_raw<1024 && m2_raw<1024`（即 natural 5+5 `s>>5 / s&31` 不均衡可被均衡重划分纠正），并按**升序唯一词典序目标** `max(m1,m2) → sum(m1+m2) → abs(m1-m2) → lexicographic(S)` 选唯一 `S*`（`max` 主、`sum` 次、`abs` 三、`S` 升序字典序决胜），`Phase A CAL-only 选 S*`，`Phase B VAL 确认`报告 `natural` 参照，session 复用 V67 三预注册 Stage2，每 session 4分流 + 总体3态 + common 审计，产出四工件，不跑 decoder 不构矩阵。

## Goal

以最短 decoder-free 路径完成**GF32 bit-partition 均衡性地图**，为 V67 `NEAR_FULL` 后的新表示必要性提供可验证证据：

### 1. 仅重划分 10 bits，不改 1024 维符号 GF32 两层验证
- **冻结**：`n=1024, q=1024 (10-bit), GF32 poly37, H1 16×1024 rank16, Lane C 184/190/192, H_inc Δ8, decoder 90/1.0, full-tag canonical` 全只读（`git diff -- src/ ==0`），处理点 `84d62779 legacy_v1` 单点，`per frame 256, BLOCK 1024, period 204800` 等同 V67。
- **唯一变量**：10-bit 符号 `s` 的 5+5 比特分割 `B={0..9} → S vs B\S`，`U1'=permute_S(s), U2'=permute_{B\S}(s)`，每种 `S` 纯重标记，不改 `s` 本身，不引 `Gray/MET/protograph/SC`。

### 2. 枚举 252 子集按升序唯一词典序目标 max→sum→abs→lexicographic 选 S*，Phase A CAL-only Phase B VAL确认，报告 natural 参照
- **枚举**：`C(10,5)=252` 子集 `S`（`itertools.combinations(0..9,5)` 按升序生成），每 `S` 在 `CAL1024` 上独立估计 `C_ab 1024×1024 → P_global → P(U1'|B)/P(U2'|U1',B)`（`λ` 仅 `CAL` 内 4-fold 择优 `[1e-2,1e4]` 不扩），在 `VAL256` 上计 `CE1(S), CE2(S), CE_full` 链式 `|CE_full-CE1-CE2|<1e-9` → `m1_raw(S), m2_raw(S)` 不 cap，`raw_disclosure(S)`。**natural `S_nat={5,6,7,8,9}` (s>>5)** 恒作为参照同表报告，**不参与择优**。
- **择优（升序唯一）**：对每 session 的 252 行按元组 `T(S) = (max(m1,m2), m1+m2, abs(m1-m2), S_lex)` 升序排序，取最小 `S*` 为该 session 最优；`S_lex` 为 `S` 的 5 元组升序字典序（如 `(0,1,2,3,4) < (0,1,2,3,5) < ...`），保证唯一。`common S*_common` 按同样 `T` 但在 **3 sessions 汇聚的 max** 上选：`T_common(S)= (max_{sess} max(m1,m2), max_{sess} sum, max_{sess} abs, S_lex)` 升序最小；若无共同可行则仍报告但 `overall` 判 `NO_COMMON`。
- **Phase A CAL-only**：`S*` 选择仅用 `CAL1024` 的 `CV NLL` 择 `λ` 与 `CAL` 上 `H` 描述性，不读 `VAL`/`TEST`；脚本内 `assert used_val_in_selection==False && used_test==False`。
- **Phase B VAL 确认**：对 `S*` 与 `S_nat` 在 `VAL256` 上独立计量 `CE1/CE2/CE_full/λ/ΔNLL/val_b_unseen/m_raw/raw_disclosure`，落盘双组 `natural vs balanced`，`stage_consistency` 与 `natural_delta` 显式。

### 3. Session 复用 V67 三预注册 Stage2
- **复用**：`v67_data_registry.json` 的 3 sessions（`20260123_1M_600k_0dB / 20260107_PPLN_1p5M / 20260123_2M_1p2M_0dB`）的 `stage2_CAL_frame_ids[1024] + stage2_VAL_frame_ids[256]` 原样复用（`v68_data_registry.json` 仅复引，不重新切帧，不扩 acquisition，`total=3, per_category 1,1,1, acquisition_dedup_verified`），`zero_overlap_verified` 与 `V13..V67` 零重叠键 `(source,session,frame)` 已验，禁止跨 acquisition 拼接或按 `CE/m` 换 session。
- **不重估计 V67**：V67 的 `natural` `CE/m` 不重算（报告内引用），V68 仅在新 `S` 上重估 `P(U1'|B)/P(U2'|U1',B)`，V67 结果零改。

### 4. 终态 per-session 4分流 + 总体3态 + common 审计
- **Per-session 4分流（优先级高→低，互斥）**：
  1. `V68_EVIDENCE_INCOMPLETE` — 物化/帧256/provenance/chain `|CE_full-CE1-CE2|≥1e-9` / `C_ab` 非有限
  2. `V68_MODEL_NOT_STABLE` — `λ` 触边 `[1e-2,1e4]` 或 `ΔNLL>0.50` 或 `val_b_context_unseen>1%` 或 `ValNLL/H` 非有限（`q_mass/joint/H_cal` 仅描述性，不入稳定性门禁；`capacity_warning` 正交旗标）
  3. `V68_BALANCED_FEASIBLE` — `m1_raw(S*)<1024 && m2_raw(S*)<1024 && raw_disclosure<5120` 且 `MODEL_NOT_STABLE` 未触发（`m_raw` 不 cap 显式，`LaneC+8+8` 仅描述性，不入此分流门禁）
  4. `V68_STILL_HEAVY` — 否则（`m1_raw≥1024 || m2_raw≥1024 || raw_disclosure≥5120`）
- **总体 3态（基于 common S*_common）**：
  1. `V68_OVERALL_BALANCED_COMMON_FEASIBLE` — `common S*_common` 在 3 sessions 上均 `BALANCED_FEASIBLE`（共识均衡可行，V67 imbalance 被纠正）
  2. `V68_OVERALL_BALANCED_PER_SESSION_ONLY` — 存在 ≥1 session `BALANCED_FEASIBLE` 但 `common` 不可行（仅 per-session 可均衡，无共识）
  3. `V68_OVERALL_STILL_HEAVY` — 0 session `BALANCED_FEASIBLE`（即便均衡重划分亦仍 heavy，需更深表示）
  （若有 `EVIDENCE_INCOMPLETE/MODEL_NOT_STABLE` 混入，则总体前缀 `V68_OVERALL_EVIDENCE_INCOMPLETE` / `..._MODEL_NOT_STABLE` 并计入审计，但 3态主体仍按 feasible 计数）
- **Common 审计**：报告 `S*_per_session[3] + S*_common + per_session_T(S) + common_T(S) + natural_T`，显式 `common_feasible_count / per_session_feasible_count` 与 `natural_vs_balanced delta (ΔCE1/ΔCE2/Δmax/Δsum)`。

### 5. 本轮交付边界（四工件 + 审计报告，decoder-free）
- 产出 `proposal/design/tasks/specs` 四工件 + `v68_data_registry.json`（复用 V67 三 session Stage2） + `scripts/v68_spike.py`（枚举252, `rg "decode_" 0 hits`） + `v68_results.json`（per session 252 行 + S* + natural） + `v68_table.csv/.json`（每行 `session / S / m1/m2/max/sum/abs / classification + S* 行高亮`） + `V68_BALANCED_REPORT.md` + `test_v68_spike_small.py`（`py_compile PASS, pytest -p no:cacheprovider -q`） + 控制台摘要；**禁** `decode_ / construct_H*` 调用、`run_01`、`H` 构造、跨方法比较、改 `src/` baseline、调 `TEST`。

## Non-Goals

- 不运行任何 `decode_row_layered_fftqspa / construct_H* / gf_rank / nested` decoder 或矩阵构造（脚本内 `rg "decode_|construct_|gf_rank|nested" 0 hits`）；不改 `H1/Lane C/m2/H_inc/decoder/full-tag` 任一冻结量；不引 `MET/protograph/SC` 新码族；不新增矩阵；**不以 `m1/m2` 是否 `<1024` 去构造验证 H**。
- 不读密封 `TEST` 的任何 `H/CE/NLL/MAP` 统计作 `P/m/阈值` 选择，`S*` 择优仅 `CAL`，`VAL` 仅确认度量，违则 `EVIDENCE_INCOMPLETE`。
- 不做 `bin_width/dimension/pairing/mapping/frame anchor` 网格搜索（单点 `84d62779`）；`λ` 仅 `[1e-2,1e4] log10` 仅 `CAL 4-fold`，不扩；`S` 枚举固定 252，不剪枝、不启发式、不按 `CE` 预过滤。
- 不宣称 `FER/阈值/SKR/晋升/安全证明`；本变更止于 `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`，不直接进入 qualification，不作跨方法 rank，不以 `BALANCED_FEASIBLE` 宣称码可译。
- 不改写/覆盖 `V13/V48–V68` 任何已有输出与终态（只读）；V67 三 session 仅复用 Stage2，不重跑 Stage0/Stage1。
- 不以总体平均替代 per-session 分流；不以 `V25 H` 作新域门禁，门禁用 `VAL CE` + `m_raw`。
- 不创建正式 `.../v68_*/run_01` decoder 执行；正式 decoder 需另起 `OpenSpec` + 独立 `EXECUTE_AUTH`。
- 不比较 Polar/Cascade/LDPC 方法；单表示内均衡性探查，不作跨方法 rank。

## Scope

1. **冻结主体与处理点零改（1024维符号 GF32两层验证）**：`n1024, q1024 (10-bit s), GF32 poly37, H1 16×1024 rank16 80b U=32*U1+U2 F03 5+5 natural（仅本变更内新增 permuted U1'/U2' 重标记，不改 s）, Lane C ordinal-2 s38310x m2 184/190/192, H_inc Δ8, decoder 90/1.0 poly37 early-stop (禁用), full-tag canonical, leak 5*(m1+m2)+64` 全只读；`84d62779 legacy_v1` 单点；不引 V68 新码本以外的表示。
2. **枚举 252 子集按升序唯一词典序目标 max→sum→abs→lexicographic 选 S*，Phase A CAL-only Phase B VAL确认，报告 natural 参照**：`S∈C(10,5)=252` 升序生成 → 每 `S` 在 `CAL1024` 上 `C_ab/P_global/λ/CE` → 在 `VAL256` 上 `CE1/CE2/CE_full chain→m1_raw/m2_raw` 不 cap → `T(S)=(max,sum,abs,S_lex)` 升序选 `S*_per_session`，`T_common(S)=(max_{sess} max, max_{sess} sum, max_{sess} abs, S_lex)` 选 `S*_common`；`Phase A CAL-only` 不读 VAL/TEST，`Phase B VAL` 确认 natural vs balanced 双报告。
3. **Session 复用 V67 三预注册 Stage2**：`v68_data_registry.json` 复用 `v67_data_registry.json: sessions[3]` 的 `stage2_CAL[1024] + stage2_VAL[256]` 帧集（`total 3, per_category 1,1,1, acquisition_dedup_verified, zero_overlap_verified`），与 `V13..V67` 零重叠键 `(source,session,frame)` 已验，不新增 acquisition，不按 `CE/m` 替换。
4. **终态 per-session 4分流 + 总体3态 + common 审计**：每 session `EVIDENCE_INCOMPLETE > MODEL_NOT_STABLE > BALANCED_FEASIBLE(m1<1024&&m2<1024&&raw<5120) > STILL_HEAVY`；总体 `BALANCED_COMMON_FEASIBLE / BALANCED_PER_SESSION_ONLY / STILL_HEAVY` + `common_feasible_count` + `S*` 审计；`capacity_warning_m1/m2/disclosure` 三正交旗标仅描述不过门禁。
5. **四工件 + 审计报告交付（DECODER_FREE）**：`scripts/v68_spike.py`（`rg "decode_" 0 hits`, `py_compile PASS`, 仅 `numpy/pandas/pyarrow + itertools`）输出 `v68_results.json + v68_table.{csv,json} + V68_BALANCED_REPORT.md`（表含 `session/S/CE/lambda/ΔNLL/m/max/sum/abs/classification/S*` 等 + `common` 章节）+ 控制台摘要，未创建 `run_01`。
6. **守卫 R68-01~10**：见 Design §9 与 Spec §10，覆盖 `冻结主体 / 252枚举 / 唯一词典序目标 / CAL-only选S* / VAL确认+natural参照 / V67三Session复用 / per-session 4分流+总体3态+common审计 / 四工件+test / decoder-free不构矩阵 / 不创run_01+TEST隔离+py_compile`。

## Impact Scope

- **新增（本变更）**：`openspec/changes/formal-ir-v68-balanced-gf32-bit-partition/` 下 4 工件 `proposal.md/design.md/tasks.md/specs/spec.md` + `scripts/v68_spike.py` (`rg "decode_" 0 hits`, `py_compile PASS`, 仅 `numpy/pandas/pyarrow+itertools`) + 冻结注册表 `v68_data_registry.json` (复用 V67 三 session Stage2) + `v68_results.json` (每 session 252 行 CE/m + S*/natural) + `v68_table.csv/.json` (每行 `session/S/m1/m2/max/sum/abs/classification` + S* 高亮 + common 汇总) + `V68_BALANCED_REPORT.md` + `test_v68_spike_small.py` + 控制台摘要。
- **只读依赖**：`v67_data_registry.json / v67_feasibility_table.json`（V67 三 session Stage2 帧集复用） + `v55_intake_20260828/pairs/*` 3 sessions + `nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz` 仅对照。
- **不修改**：任何既有 `spec/代码/测试/输出`（除本目录 + `scripts/` 外）、`V38–V67` 输出、`outputs_comparison/workspace` 以外；**不改 `src/` 基线，不创建 `run_01`，零码参增量，不启动 decoder，不构矩阵，不重估计 V67**。

## Acceptance Criteria

- [ ] `proposal/design/tasks/specs/spec.md` 齐全一致，`lifecycle PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`，`branch formal-ir-mainline` + `HEAD b7e3417f` + `data 84d62779` + `predecessor V67 b7e3417f V67_FEASIBILITY_MAP_ACCEPTED / V64 22/24 PASS` 已绑定，显式声明 decoder-free、零 decoder/矩阵、1024维符号 GF32两层验证冻结仅重划分10 bits、枚举252子集升序唯一词典序 `max→sum→abs→lex` 选 `S*`、`Phase A CAL-only Phase B VAL确认` 报告 natural 参照、session 复用 V67 三预注册 Stage2、per-session 4分流 + 总体3态 + common审计、四工件产出已声明，**新 Plan SHA 已推送**。
- [ ] **冻结主体零改已验**：`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0`，`n1024 q1024 GF32 poly37 H1 16×1024 rank16 80b U=32*U1+U2 F03 5+5 natural（仅新增 permuted U1'/U2' 重标记） Lane C 184/190/192 H_inc Δ8 decoder 90/1.0 full-tag canonical leak 5*(m1+m2)+64` 全只读，处理点 `84d62779 legacy_v1` 单点，`rg -i "gray|met|protograph|sc_coupling" scripts/v68_spike.py` 0 hits（除 `S` 纯比特重划分注释），`rg "decode_|construct_|gf_rank|nested" 0 hits` 已验。
- [ ] **枚举252按升序唯一词典序目标已验**：`C(10,5)=252` 子集 `S` 由 `itertools.combinations(range(10),5)` 升序生成，每 `S` 独立 `C_ab 1024×1024 → P_global → P(U1'|B)/P(U2'|U1',B) λ(CAL 4-fold [1e-2,1e4]) → VAL CE1/CE2/CE_full chain |CE_full-CE1-CE2|<1e-9 → m1_raw=ceil(1.3*1024*CE1/5), m2_raw=ceil(1.3*1024*CE2/5) raw_disclosure 5*(m1+m2)+64 不 cap`，`T(S)=(max,sum,abs,S_lex)` 升序选 `S*_per_session`，`T_common(S)=(max_{sess} max, max_{sess} sum, max_{sess} abs, S_lex)` 选 `S*_common`，`natural S_nat={5,6,7,8,9}` 恒参照，三者均落盘且唯一性已验（`252` 行每 session，排序稳定）。
- [ ] **Phase A CAL-only Phase B VAL确认已验**：`S*` 择优仅 `CAL1024` 内 `4-fold CV NLL` 最小 `λ`，脚本内 `used_val_in_selection==False && used_test==False` 已验；`VAL256` 上对 `S*` 与 `S_nat` 双计 `CE1/CE2/CE_full/λ/ΔNLL/val_b_unseen/m_raw/raw_disclosure/chain_delta/H_cal`，报告 `natural_vs_balanced ΔCE/Δm/Δmax` 已披露，不以 `VAL`/`TEST` 重选 `S*`。
- [ ] **Session 复用 V67 三预注册 Stage2 已验**：`v68_data_registry.json` 复用 `v67_data_registry.json: sessions[3]` 的 `stage2_CAL[1024] (262144 pairs) + stage2_VAL[256] (65536 pairs)` 原样，`total 3 ∈[3,9] && per_category 1,1,1 && acquisition_dedup_verified && zero_overlap_verified && (Stage2_key ∩ (V13..V67)_key ==∅)` 已验，`S` 重划分不改帧集，不新增 acquisition，不按 `CE/m` 替换。
- [ ] **Per-session 4分流互斥已验**：每 session `classification ∈ {EVIDENCE_INCOMPLETE, MODEL_NOT_STABLE, BALANCED_FEASIBLE, STILL_HEAVY}` 按 `EVIDENCE_INCOMPLETE > MODEL_NOT_STABLE(λ触边/ΔNLL>0.5/val_b>1%/非有限) > BALANCED_FEASIBLE(m1<1024&&m2<1024&&raw<5120) > STILL_HEAVY(≥1024或≥5120)` 已判定，`capacity_warning_m1/m2/disclosure` 三正交旗标仅描述不过门禁，`q_mass/joint/H_cal` 仅描述性，不入稳定性门禁。
- [ ] **总体3态 + common审计已验**：`overall ∈ {BALANCED_COMMON_FEASIBLE, BALANCED_PER_SESSION_ONLY, STILL_HEAVY}` 基于 `common S*_common` 在 3 sessions 上的 `BALANCED_FEASIBLE` 计数，落盘 `overall + common_feasible_count + per_session_feasible_count + S*_per_session[3] + S*_common + common_T + natural_T`，报告 `common 审计` 章节与 `json/csv` 一致。
- [ ] **四工件 + 审计报告完整**：`v68_data_registry.json` + `v68_results.json` + `v68_table.csv/.json`（行对等，252×3 + 汇总行，含 `session/S/CE/lambda/ΔNLL/unseen/m/max/sum/abs/classification/S*_flag` 且与 json 一致，`capacity_warning` 正交 + `descriptive_diagnostics` 逐 session）+ `V68_BALANCED_REPORT.md`（含 `per session 252 选优 + S* + natural参照 + overall 3态 + common审计`）已齐，`natural` 参照每 session 已披露。
- [ ] `scripts/v68_spike.py` 为 decoder-free 可运行脚本（`rg "decode_" 0 hits`、`rg "construct_" 0 hits`、`rg "gf_rank" 0 hits`、`rg -i "met|protograph" 0 hits`，仅 `numpy/pandas/pyarrow+itertools`，`py_compile` PASS，`pytest -p no:cacheprovider -q test_v68_spike_small.py` PASS），输出 `results + table + report` + 控制台摘要，**未创建 run_01，未构矩阵，未读 TEST，λ 不扩搜索，m_raw 不 cap，252 枚举已验**。
- [ ] 已停留在 `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`，未创建任何 `.../v68_*/run_01`（`ls` 不存在已验），不比较，不碰 `V48-V67` 块外，未转 qualification，**四工件+registry+spike+报告表已单独提交推送，返回新 Plan SHA + S*_per_session + S*_common + 各分流计数 + common审计**，等待独立审核（`Pre-RESULT` 独立线程复核 `HEAD/ACCEPTED_PLAN_SHA/rg 0 hits/run_01不存在/py_compile/TEST 未读/m_raw 显式/252 枚举/词典序唯一/4分流+3态`）。

## Tasks

见 `tasks.md`（Phase A 枚举前置与注册表复用；Phase B 冻结主体 1024维 GF32两层验证仅重划分；Phase C Phase A CAL-only 选 S*（252 枚举+词典序）；Phase D Phase B VAL确认+natural参照；Phase E per-session 4分流+总体3态+common审计；Phase F 四工件+审计报告；Phase G 守卫 R68-01~10 + 单独提交推送新 Plan SHA）。

## Lifecycle

`V64` 已 `22/24 full-tag PASS`；`V65` new-session 对照；`V66` 单 session `72` 自适应 `RATE_NOT_FEASIBLE`；`V67-MAP` 已 `V67_FEASIBILITY_MAP_ACCEPTED` 3 sessions 均 `NEAR_FULL_DISCLOSURE`（natural 5+5）；`V68-BAL` 为**均衡 bit-partition 地图** decoder-free 预冻结，当前 `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`（仅重划分 10 bits 找 CAL-only 5-bit U1 子集使 `m1/m2<1024`，枚举252升序唯一词典序 `max→sum→abs→lex` 选 `S*`，Phase A CAL-only Phase B VAL确认，报告 natural 参照，session 复用 V67 三预注册 Stage2，终态 per-session 4分流 + 总体3态 + common审计，不跑 decoder 不构矩阵）；`V68` 本身不直接进入 qualification；任何 decoder / 新表示需另起 `EXECUTE_AUTH`。
