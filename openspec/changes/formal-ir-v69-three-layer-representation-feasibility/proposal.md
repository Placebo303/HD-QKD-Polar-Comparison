# OpenSpec Proposal: formal-ir-v69-three-layer-representation-feasibility

**Status**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — 仅计划四工件 + decoder-free 三层表示可行性地图，不改 1024 维符号 GF32 两层验证框架的底层码，不跑 decoder 不构矩阵，仅重划分 10 bits 为三层有序非空 `w∈[2,5]` partition 做 `3^10` 搜索，CAL-only λ 选优，链式 `CE1+CE2+CE3=CE_full`

**Domain**: Formal IR / NB-LDPC three-layer representation feasibility (V68 同域直接后继，V67 三预注册 Stage2 复用)

**Change ID**: `formal-ir-v69-three-layer-representation-feasibility`

**Cycle ID**: `V69-3L` (three-layer-representation-feasibility), predecessor `formal-ir-v68-balanced-gf32-bit-partition` (`d6f590ac6f30deaa8b0bf6cf5c419593fc037720` V68 `PLAN_CANDIDATE/DECODER_FREE`) + `formal-ir-v67-multisession-feasibility-map` (`V67_FEASIBILITY_MAP_ACCEPTED` 3 sessions 均 `NEAR_FULL` on natural 5+5) + `formal-ir-v64` (`22/24 PASS`)

**Branch**: `formal-ir-mainline`

**HEAD**: `d6f590ac6f30deaa8b0bf6cf5c419593fc037720` (V67/V68 清理后冻结 HEAD，本变更基于此；推送后以 `git rev-parse HEAD == origin/formal-ir-mainline` 40位重核)

**Data SHA**: `84d62779` (`84d62779603e62de50ded5182ed65b65d3dc6084`, `d=1024 bw=200ps pairing=nearest rule=legacy_v1` 单点；V69 复用 V67 三 session 的 `Stage2 CAL1024+VAL256`，不换点，不换 bin/mapping，不新增 acquisition)

**Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — 本轮止于计划四工件 + decoder-free 三层 partition 地图（registry 复用 + feasibility spike 枚举 `3^10`→`37170` valid + results + table + report + small test），零 decoder/矩阵/新依赖（`numpy/pandas/pyarrow` 已装），不创建 `run_01`，不比较方法，不转 qualification，不启动 V70，任何 decoder 执行需独立 `PLAN_ACCEPT + EXECUTE_AUTH`

> ponytail lite: 本变更仅 4 OpenSpec 工件 + 1 decoder-free spike（枚举 `3^10=59049` → 过滤 `2≤w≤5` 得 37170 有序非空三层 partition，`numpy` 直算 `C_ab` + `itertools.product`/`base-3`，不引 `scipy/sklearn`）+ 1 结果表 + 1 报告 + 1 小测试；零 decoder/矩阵/新依赖，最短科学路径。laziest alternative: `numpy` + `itertools` 穷举，不做启发式剪枝。

> **科学问题（冻结）**：于**完全冻结主体**（`n=1024, q=1024 (10-bit), GF32 poly37, H1 16×1024 rank16, Lane C 184/190/192, H_inc Δ8, decoder 90/1.0 poly37, full-tag canonical 32*U1+U2(+U3) 扩展, leak = Σ w_i·m_i +64` 全只读，**不改维度/符号/q/GF/两层验证**）下，**仅重划分 10 bits 为三层有序非空 `w_i∈[2,5]`**：对 10-bit 符号 `s∈[0,1023]` 的比特位置集合 `B={0..9}`，枚举全部 `3^10=59049` 个 `B→{1,2,3}` 分配，去重统计后过滤 `2≤|S_i|≤5` 且 `|S1|+|S2|+|S3|=10` 且 `S_i≠∅` 得 **37170** 个有效有序三层划分 `P=(S1,S2,S3)` 定义新分解 `U_i = bits_{S_i}(s)`（宽度 `w_i=|S_i|`, 值域 `0..2^{w_i}-1`），以 `CAL1024` 独立重估 `P(U1|B)/P(U2|U1,B)/P(U3|U1,U2,B)` 在 `VAL256` 上得 `m_i_raw=ceil(1.3*1024*CE_i/w_i)` **不 cap**，链式 `|CE_full-CE1-CE2-CE3|<1e-9`，**per-layer  `|CE_i^{VAL}-CE_i^{CAL-CV}|≤0.5` 且 `val_b_unseen≤1%` 且 `m_i_raw<1024`** 均满足才 `FEASIBLE`；证明是否存在**三 session 同 assignment 的 common** `P*_common` 使三层均可行（natural 5+5 `s>>5/s&31` 作为二层 looseness 参照，但不参与三层择优），并按**升序唯一词典序目标** `max_util → raw_disclosure → max_ΔNLL → lexicographic(P)` 选唯一 `P*`（`max_util=max_i(m_i/1024)` 主、`raw_disclosure=Σ w_i·m_i+64` 次、`max_ΔNLL` 三、`P` 升序字典序决胜），`Phase A CAL-only 选 P*`，`Phase B VAL 确认`，session 复用 V67 三预注册 Stage2，每 session 5分流 + 总体5态 + common 审计，产出四工件，不跑 decoder 不构矩阵。

## Goal

以最短 decoder-free 路径完成**三层表示可行性地图**，为 V67 `NEAR_FULL` / V68 仍待验证的均衡后是否需更深表示提供可验证证据：

### 1. 仅重划分 10 bits 为三层有序非空 `w∈[2,5]`，不改 1024 维符号 GF32 验证框架
- **冻结**：`n=1024, q=1024 (10-bit), GF32 poly37, H1 16×1024 rank16, Lane C 184/190/192, H_inc Δ8, decoder 90/1.0, full-tag canonical` 全只读（`git diff -- src/ ==0`），处理点 `84d62779 legacy_v1` 单点，`per frame 256, BLOCK 1024, period 204800` 等同 V67/V68。
- **唯一变量**：10-bit 符号 `s` 的三层有序比特分割 `B={0..9} → (S1,S2,S3)`，`|S_i|=w_i∈[2,5]`, `Σw_i=10`, `S_i≠∅` 有序，`U_i=bits_{S_i}(s)`，每种 `P` 纯重标记，不改 `s` 本身，不引 `Gray/MET/protograph/SC`。

### 2. 枚举 `3^10=59049` → 过滤 37170 有效三层划分，按升序唯一词典序 `max_util→disclosure→ΔNLL→lex` 选 `P*`，Phase A CAL-only Phase B VAL 确认
- **枚举**：`3^10=59049` 个 `B→{1,2,3}` 全分配（base-3 `0..59048` 或 `itertools.product([1,2,3], repeat=10)` 按升序生成），去重统计后过滤 `2≤w_i≤5` 且非空且和为 10 得 **37170** 有效有序三层 partition（`12` 种 `w` pattern 各 `2520/3150/4200` 详见 Design），每 `P` 在 `CAL1024` 上独立估计 `C_ab 1024×1024 → P_global → P(U1|B)/P(U2|U1,B)/P(U3|U1,U2,B)`（`λ` 仅 `CAL` 内 4-fold 择优 `[1e-2,1e4]` 不扩），在 `VAL256` 上计 `CE1/CE2/CE3/CE_full` 链式 `|CE_full-ΣCE_i|<1e-9` → `m_i_raw=ceil(1.3*1024*CE_i/w_i)` 不 cap，`raw_disclosure=Σ w_i·m_i+64`。
- **择优（升序唯一）**：对每 session 的有效集按元组 `T(P) = (max_i(m_i/1024), raw_disclosure(P), max_i(ΔNLL_i), P_lex)` 升序排序取最小 `P*_per_session`；`P_lex` 为 `P` 的扁平化 10 元分配向量（如 `tuple(assign[0..9])` 其中 `assign[j]∈{1,2,3}`）或等价 `(S1_tuple,S2_tuple,S3_tuple)` 升序字典序，保证唯一。`common P*_common` 按同样 `T` 但在 **3 sessions 汇聚的 worst** 上选：`T_common(P)= (max_{sess} max_util, max_{sess} raw_disclosure, max_{sess} max_ΔNLL, P_lex)` 升序最小；`Common` 需**三 session 同 assignment** 且每 session `m_i_raw<1024 ∀i` 才视为 `COMMON_FEASIBLE`。若无共同可行则仍报告但 `overall` 判 `NO_COMMON`。
- **Phase A CAL-only**：`P*` 选择仅用 `CAL1024` 的 `CV NLL/CE_cv` 择 `λ` 与 `CAL-CV H` 描述性，不读 `VAL`/`TEST`；脚本内 `assert used_val_in_selection==False && used_test==False`。
- **Phase B VAL 确认**：对 `P*` 在 `VAL256` 上独立计量 `CE_i/CE_full/λ/ΔNLL/val_b_unseen/m_raw/raw_disclosure` 并做 per-layer `|CE_i^{VAL}-CE_i^{CAL-CV}|≤0.5` 与 `val_b_unseen≤1%` 与 `m_i<1024` 门禁，落盘 `v69_results.json`。

### 3. Session 复用 V67 三预注册 Stage2
- **复用**：`v67_data_registry.json` 的 3 sessions（`20260123_1M_600k_0dB / 20260107_PPLN_1p5M / 20260123_2M_1p2M_0dB`）的 `stage2_CAL_frame_ids[1024] + stage2_VAL_frame_ids[256]` 原样复用（`v69_data_registry.json` 仅复引，不重新切帧，不扩 acquisition，`total=3, per_category 1,1,1, acquisition_dedup_verified`），`zero_overlap_verified` 与 `V13..V68` 零重叠键 `(source,session,frame)` 已验，禁止跨 acquisition 拼接或按 `CE/m` 换 session。
- **不重估计 V67**：V67 的二层 natural `CE/m` 不重算；V69 仅在新三层 `P` 上重估，V67/V68 结果零改。

### 4. 终态 per-session 5分流 + 总体5态 + common 审计（含 `max_util→disclosure→ΔNLL→lex` 词典序）
- **Per-session 5分流（优先级高→低，互斥）**：
  1. `V69_EVIDENCE_INCOMPLETE` — 物化/帧256/provenance/chain `|ΣCE_i - CE_full|≥1e-9` / `C_ab` 非有限 / 枚举不足 `37170`
  2. `V69_MODEL_NOT_STABLE` — `λ` 触边 `[1e-2,1e4]` 或任一层 `|CE_i^{VAL}-CE_i^{CAL-CV}|>0.50` 或 `ΔNLL_i>0.50` 或 `val_b_context_unseen>1%` 或 `ValNLL/H` 非有限（`q_mass/joint/H_cal` 仅描述性，不入稳定性门禁；`capacity_warning` 正交旗标）
  3. `V69_THREE_LAYER_FEASIBLE` — `∀i m_i_raw<1024 && raw_disclosure<10240` 且 `MODEL_NOT_STABLE` 未触发且链式已验（`m_raw` 不 cap 显式，`LaneC+8+8` 仅描述性不入此分流门禁）
  4. `V69_PARTIAL_FEASIBLE` — 存在 `1≤k<3` 层 `m_i<1024` 但非全三层可行（需 rate-adaptive / 混合披露，部分可行）
  5. `V69_STILL_HEAVY` — 否则（`∀i m_i≥1024` 或全 disclosure heavy，无任何层可行）
- **总体 5态（基于 common P*_common，需三 session 同 assignment）**：
  1. `V69_OVERALL_EVIDENCE_INCOMPLETE` — 任一 session `EVIDENCE_INCOMPLETE`
  2. `V69_OVERALL_MODEL_NOT_STABLE` — 无 `EVIDENCE` 但任一 session `MODEL_NOT_STABLE` 且无 common feasible
  3. `V69_OVERALL_THREE_LAYER_COMMON_FEASIBLE` — `common P*_common` 在 3 sessions 上均 `THREE_LAYER_FEASIBLE`（共识三层可行，需表示有效）
  4. `V69_OVERALL_THREE_LAYER_PER_SESSION_ONLY` — 存在 ≥1 session `THREE_LAYER_FEASIBLE` 或 `PARTIAL` 但 `common` 不可行（仅 per-session 可行，无共识）
  5. `V69_OVERALL_STILL_HEAVY` — 0 session `THREE_LAYER_FEASIBLE` 且 `PARTIAL==0`（即便三层重划分亦仍 heavy，需更深表示/非比特划分）
  （优先级 `EVIDENCE > MODEL > COMMON_FEASIBLE > PER_SESSION_ONLY > STILL_HEAVY`，互斥）
- **Common 审计**：报告 `P*_per_session[3] + P*_common + per_session_T(P) + common_T(P) + dedup_stats(59049→37170 per w pattern) + per_layer ΔCE/ΔNLL/unseen/m`，显式 `common_feasible_count / per_session_feasible_count / partial_count`。

### 5. 本轮交付边界（四工件 + 审计报告，decoder-free）
- 产出 `proposal/design/tasks/specs` 四工件 + `v69_data_registry.json`（复用 V67 三 session Stage2） + `scripts/v69_three_layer_feasibility.py`（枚举 59049→37170, `rg "decode_" 0 hits`） + `v69_results.json`（per session 过滤后全量或 Top-K + P* + dedup_stats） + `v69_table.csv/.json`（每行 `session / P / w1/w2/w3 / m1/m2/m3 / max_util / raw_disclosure / ΔNLL / classification + P* 高亮 + dedup_summary`） + `V69_THREE_LAYER_REPORT.md` + `test_v69_three_layer_small.py`（`py_compile PASS, pytest -p no:cacheprovider -q`） + 5分流控制台摘要；**禁** `decode_ / construct_H*` 调用、`run_01`、`H` 构造、跨方法比较、改 `src/` baseline、调 `TEST`、启动 V70。

## Non-Goals

- 不运行任何 `decode_row_layered_fftqspa / construct_H* / gf_rank / nested` decoder 或矩阵构造（脚本内 `rg "decode_|construct_|gf_rank|nested" 0 hits`）；不改 `H1/Lane C/m2/H_inc/decoder/full-tag` 任一冻结量；不引 `MET/protograph/SC` 新码族；不新增矩阵；**不以 `m_i/m` 是否 `<1024` 去构造验证 H**。
- 不读密封 `TEST` 的任何 `H/CE/NLL/MAP` 统计作 `P/m/阈值` 选择，`P*` 择优仅 `CAL`，`VAL` 仅确认度量，违则 `EVIDENCE_INCOMPLETE`。
- 不做 `bin_width/dimension/pairing/mapping/frame anchor` 网格搜索（单点 `84d62779`）；`λ` 仅 `[1e-2,1e4] log10` 仅 `CAL 4-fold`，不扩；`P` 枚举固定 `3^10=59049→37170`，不剪枝、不启发式、不按 `CE` 预过滤（除 `w∈[2,5]` 硬过滤）。
- 不宣称 `FER/阈值/SKR/晋升/安全证明`；本变更止于 `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`，不直接进入 qualification，不作跨方法 rank，不以 `THREE_LAYER_FEASIBLE` 宣称码可译。
- 不改写/覆盖 `V13/V48–V69` 任何已有输出与终态（只读）；V67 三 session 仅复用 Stage2，不重跑 Stage0/Stage1。
- 不以总体平均替代 per-session 分流；不以 `V25 H` 作新域门禁，门禁用 `VAL CE` + `m_raw` + per-layer `ΔCE≤0.5`。
- 不创建正式 `.../v69_*/run_01` decoder 执行；正式 decoder 需另起 `OpenSpec` + 独立 `EXECUTE_AUTH`。
- 不比较 Polar/Cascade/LDPC 方法；单表示内三层可行性探查，不作跨方法 rank。
- **不启动 V70**：任何 V70 `QUALIFICATION_PLAN_READY / run_01 / 阈/码族` 预冻结均禁止在本变更内声明或执行；V69 报告仅以 `successor ∈ {v69_three_layer_code_design, v69_new_representation, recollect}` 指向，不创建 V70 目录或产出。

## Scope

1. **冻结主体与处理点零改（1024维符号三层重标记扩展）**：`n1024, q1024 (10-bit s), GF32 poly37, H1 16×1024 rank16 80b U= (U1,U2,U3) 三层 F variable width (w1,w2,w3), Lane C ordinal-2 s38310x m2 184/190/192, H_inc Δ8, decoder 90/1.0 poly37 early-stop (禁用), full-tag canonical (32*U1+U2 扩展为多层 tag 仅描述性), leak Σ w_i·m_i+64` 全只读；`84d62779 legacy_v1` 单点；不引 V69 新码本以外的表示。
2. **枚举 `3^10=59049` → 过滤 37170 三层有序非空 `w∈[2,5]` 划分，按升序唯一词典序 `max_util→disclosure→ΔNLL→lex` 选 `P*`，Phase A CAL-only Phase B VAL确认**：`P∈{1,2,3}^{10}` 去重统计后 `w_i∈[2,5]` 过滤得 37170 有序三层 partition 升序生成 → 每 `P` 在 `CAL1024` 上 `C_ab/P_global/λ/CE_cv` → 在 `VAL256` 上 `CE1/CE2/CE3/CE_full chain→m_i_raw=ceil(1.3*1024*CE_i/w_i) raw_disclosure` 不 cap → `T(P)=(max_util, raw_disclosure, max_ΔNLL, P_lex)` 升序选 `P*_per_session`，`T_common(P)=(max_{sess} max_util, max_{sess} raw, max_{sess} ΔNLL, P_lex)` 选 `P*_common`（需三 session 同 assignment）；`Phase A CAL-only` 不读 VAL/TEST，`Phase B VAL` 确认 per-layer `VAL-CAL≤0.5` + `unseen≤1%` + `m<1024`。
3. **Session 复用 V67 三预注册 Stage2**：`v69_data_registry.json` 复用 `v67_data_registry.json: sessions[3]` 的 `stage2_CAL[1024] + stage2_VAL[256]` 帧集（`total 3, per_category 1,1,1, acquisition_dedup_verified, zero_overlap_verified`），与 `V13..V68` 零重叠键 `(source,session,frame)` 已验，不新增 acquisition，不按 `CE/m` 替换。
4. **终态 per-session 5分流 + 总体5态 + common 审计**：每 session `EVIDENCE_INCOMPLETE > MODEL_NOT_STABLE(per-layer ΔCE/ΔNLL/unseen) > THREE_LAYER_FEASIBLE(∀m_i<1024) > PARTIAL_FEASIBLE(∃m_i<1024) > STILL_HEAVY`；总体 `EVIDENCE_INCOMPLETE / MODEL_NOT_STABLE / COMMON_FEASIBLE / PER_SESSION_ONLY / STILL_HEAVY` + `common_feasible_count` + `P*_per_session+P*_common+dedup_stats` 审计；`capacity_warning` 三正交旗标仅描述不过门禁。
5. **四工件 + 审计报告交付（DECODER_FREE）**：`scripts/v69_three_layer_feasibility.py`（`rg "decode_" 0 hits`, `py_compile PASS`, 仅 `numpy/pandas/pyarrow+itertools`）输出 `v69_results.json + v69_table.{csv,json} + V69_THREE_LAYER_REPORT.md`（表含 `session/P/w/CE/lambda/ΔNLL/unseen/m/max_util/raw/classification/P*` 等 + `common + dedup_stats` 章节）+ 控制台摘要，未创建 `run_01`。
6. **守卫 R69-01~10**：见 Design §9 与 Spec §10，覆盖 `冻结主体 / 3^10→37170枚举去重 / 唯一词典序 max_util→disclosure→ΔNLL→lex / CAL-only选P* / VAL确认 per-layer ≤0.5 + unseen≤1% + chain 1e-9 + m<1024 / V67三Session复用 / per-session 5分流+总体5态+common审计 / 四工件+test / decoder-free不构矩阵 + 不读TEST + 不启V70 / 不创run_01+py_compile`。

## Impact Scope

- **新增（本变更）**：`openspec/changes/formal-ir-v69-three-layer-representation-feasibility/` 下 4 工件 `proposal.md/design.md/tasks.md/specs/spec.md` + `scripts/v69_three_layer_feasibility.py` (`rg "decode_" 0 hits`, `py_compile PASS`, 仅 `numpy/pandas/pyarrow+itertools`) + 冻结注册表 `v69_data_registry.json` (复用 V67 三 session Stage2) + `v69_results.json` (per session 过滤后 `37170` 行或 Top-K 浓缩 + `P*` + dedup_stats + per-layer VAL-CAL) + `v69_table.csv/.json` (每行 `session/P/w1/w2/w3/m1/m2/m3/max_util/raw/ΔNLL/classification` + P* 高亮 + common 汇总 + dedup_stats) + `V69_THREE_LAYER_REPORT.md` + `test_v69_three_layer_small.py` + 控制台摘要。
- **只读依赖**：`v67_data_registry.json / v67_feasibility_table.json`（V67 三 session Stage2 帧集复用） + `v55_intake_20260828/pairs/*` 3 sessions + `nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz` 仅对照。
- **不修改**：任何既有 `spec/代码/测试/输出`（除本目录 + `scripts/` 外）、`V38–V68` 输出、`outputs_comparison/workspace` 以外；**不改 `src/` 基线，不创建 `run_01`，零码参增量，不启动 decoder，不构矩阵，不重估计 V67/V68，不启动 V70**。

## Acceptance Criteria

- [ ] `proposal/design/tasks/specs/spec.md` 齐全一致，`lifecycle PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`，`branch formal-ir-mainline` + `HEAD d6f590ac6f30deaa8b0bf6cf5c419593fc037720` + `data 84d62779` + `predecessor V68 d6f590ac6f30deaa8b0bf6cf5c419593fc037720 / V67 FEASIBILITY_MAP_ACCEPTED / V64 22/24 PASS` 已绑定，显式声明 decoder-free、零 decoder/矩阵、1024维符号三层有序 `w∈[2,5]` 重划分、枚举 `3^10=59049→37170` 去重统计、升序唯一词典序 `max_util→disclosure→ΔNLL→lex` 选 `P*`、`Phase A CAL-only Phase B VAL确认` per-layer `VAL-CAL≤0.5` + `unseen≤1%` + `chain 1e-9` + `m<1024` + `raw disclosure` + common 三 session 同 assignment、四工件产出已声明，**V69 无独立 plan commit — provenance 待推送后生成**。
- [ ] **冻结主体零改已验**：`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0`，`n1024 q1024 GF32 poly37 H1 16×1024 rank16 80b U=(U1,U2,U3) 三层 (仅 S 重标记) Lane C 184/190/192 H_inc Δ8 decoder 90/1.0 full-tag canonical leak Σ w_i·m_i+64` 全只读，处理点 `84d62779 legacy_v1` 单点，`rg -i "gray|met|protograph|sc_coupling" scripts/v69_three_layer_feasibility.py` 0 hits（除 `P` 纯比特重划分注释），`rg "decode_|construct_|gf_rank|nested" 0 hits` 已验，`rg "TEST.*read|read.*TEST" 0 hits` 且 `used_test==False`。
- [ ] **枚举 `3^10→37170` 去重统计已验**：`3^10=59049` 个 `B→{1,2,3}` 分配由 `base-3` 或 `itertools.product([1,2,3], repeat=10)` 升序生成，去重后过滤 `w_i∈[2,5]` 且 `Σw_i=10` 且 `S_i≠∅` 得 `37170` 有序三层 partition（`12` 种 `w` pattern 各 `2520/3150/4200` 已分表统计），每 `P` 独立 `C_ab 1024×1024 → P_global → P(U1|B)/P(U2|U1,B)/P(U3|U1,U2,B) λ(CAL 4-fold [1e-2,1e4]) → VAL CE1/CE2/CE3/CE_full chain |CE_full-ΣCE_i|<1e-9 → m_i_raw=ceil(1.3*1024*CE_i/w_i) raw_disclosure Σ w_i·m_i+64` 不 cap，且 `T(P)=(max_util, raw, max_ΔNLL, P_lex)` 升序选 `P*_per_session`，`T_common(P)=(max_{sess} max_util, max_{sess} raw, max_{sess} ΔNLL, P_lex)` 选 `P*_common`（三 session 同 assignment），`dedup_stats` 已落盘且 `59049→37170` 已验，排序稳定唯一。
- [ ] **Phase A CAL-only Phase B VAL确认（含 per-layer ≤0.5 + unseen≤1% + chain + m<1024）已验**：`P*` 择优仅 `CAL1024` 内 `4-fold CV NLL/CE_cv` 最小 `λ`，脚本内 `used_val_in_selection==False && used_test==False` 已验；`VAL256` 上对 `P*` 计 `CE1/CE2/CE3/CE_full/λ/ΔNLL_i/val_b_unseen/chain_delta/H_cal`，`∀i |CE_i^{VAL}-CE_i^{CAL-CV}|≤0.5` 且 `ΔNLL_i≤0.5` 且 `val_b_context_unseen≤1%` 且 `|ΣCE_i-CE_full|<1e-9` 且 `m_i_raw<1024 ∀i` 均已链式校验，`H_cal/q_mass/joint` 仅描述性，不入稳定性门禁，`m_raw` 不 cap 显式，`raw_disclosure` 显式。
- [ ] **Session 复用 V67 三预注册 Stage2 已验**：`v69_data_registry.json` 复用 `v67_data_registry.json: sessions[3]` 的 `stage2_CAL[1024] (262144 pairs) + stage2_VAL[256] (65536 pairs)` 原样，`total 3 ∈[3,9] && per_category 1,1,1 && acquisition_dedup_verified && zero_overlap_verified && (Stage2_key ∩ (V13..V68)_key ==∅)` 已验，`P` 重划分不改帧集，不新增 acquisition，不按 `CE/m` 替换。
- [ ] **Per-session 5分流互斥已验**：每 session `classification ∈ {EVIDENCE_INCOMPLETE, MODEL_NOT_STABLE, THREE_LAYER_FEASIBLE, PARTIAL_FEASIBLE, STILL_HEAVY}` 按 `EVIDENCE_INCOMPLETE > MODEL_NOT_STABLE(λ触边/per-layer VAL-CAL>0.5/ΔNLL>0.5/val_b>1%/非有限) > THREE_LAYER_FEASIBLE(∀m_i<1024&&raw<10240) > PARTIAL_FEASIBLE(∃m_i<1024) > STILL_HEAVY` 已判定，`capacity_warning_m1/m2/m3/disclosure` 四正交旗标仅描述不过门禁，`per-layer` 阈已验。
- [ ] **总体5态 + common审计（含三 session 同 assignment + 词典序）已验**：`overall ∈ {EVIDENCE_INCOMPLETE, MODEL_NOT_STABLE, THREE_LAYER_COMMON_FEASIBLE, THREE_LAYER_PER_SESSION_ONLY, STILL_HEAVY}` 基于 `common P*_common` 在 3 sessions 上的 `THREE_LAYER_FEASIBLE` 计数（需三 session 同 assignment），落盘 `overall + common_feasible_count + per_session_feasible_count + partial_count + P*_per_session[3] + P*_common + common_T + dedup_stats(59049→37170 per w pattern)`，`T` 升序 `max_util→disclosure→max_ΔNLL→lex` 已验，`common` 需三 session 同 assignment 已验，报告 `common 审计` 章节与 `json/csv` 一致。
- [ ] **四工件 + 审计报告完整**：`v69_data_registry.json` + `v69_results.json` + `v69_table.csv/.json`（行对等，含 `session/P/w/CE/lambda/ΔNLL/unseen/m/max_util/raw/classification/P*_flag` + `dedup_stats` + `common` 汇总且与 json 一致，`capacity_warning` 正交 + `descriptive_diagnostics` 逐 session）+ `V69_THREE_LAYER_REPORT.md`（含 `per session 枚举去重 + 37170 选优 + P*_per_session + P*_common + dedup_stats + overall 5态 + common审计 + per-layer VAL-CAL + chain`）已齐。
- [ ] `scripts/v69_three_layer_feasibility.py` 为 decoder-free 可运行脚本（`rg "decode_" 0 hits`、`rg "construct_" 0 hits`、`rg "gf_rank" 0 hits`、`rg -i "met|protograph" 0 hits`，仅 `numpy/pandas/pyarrow+itertools`，`py_compile` PASS，`pytest -p no:cacheprovider -q test_v69_three_layer_small.py` PASS），输出 `results + table + report` + 控制台摘要，**未创建 run_01，未构矩阵，未读 TEST，λ 不扩搜索，m_raw 不 cap，`3^10→37170` 枚举去重 + 词典序 `max_util→disclosure→ΔNLL→lex` 唯一已验**。
- [ ] 已停留在 `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`，未创建任何 `.../v69_*/run_01`（`ls` 不存在已验），不比较，不碰 `V48-V68` 块外，未转 qualification，未启动 V70，**四工件+registry+spike+报告表已单独提交推送，返回新 Plan SHA + P*_per_session + P*_common + 各分流计数 + dedup_stats + common审计**，等待独立审核（`Pre-RESULT` 独立线程复核 `HEAD/ACCEPTED_PLAN_SHA/rg 0 hits/run_01不存在/py_compile/TEST 未读/m_raw 显式/59049→37170枚举去重/词典序唯一/5分流+5态/common同assignment/per-layer VAL-CAL≤0.5/unseen≤1%/chain 1e-9`）。

## Tasks

见 `tasks.md`（Phase A 枚举前置 `3^10→37170` 去重统计与注册表复用；Phase B 冻结主体 1024维三层仅重划分；Phase C Phase A CAL-only 选 P*（37170 枚举+词典序 `max_util→disclosure→ΔNLL→lex`）；Phase D Phase B VAL确认 per-layer `VAL-CAL≤0.5` + `unseen≤1%` + `chain 1e-9` + `m<1024`；Phase E per-session 5分流+总体5态+common三 session 同 assignment 审计；Phase F 四工件+审计报告；Phase G 守卫 R69-01~10 + 单独提交推送新 Plan SHA + 不启 V70）。

## Lifecycle

`V64` 已 `22/24 full-tag PASS`；`V65` new-session 对照；`V66` 单 session `72` 自适应 `RATE_NOT_FEASIBLE`；`V67-MAP` 已 `V67_FEASIBILITY_MAP_ACCEPTED` 3 sessions 均 `NEAR_FULL`（natural 5+5）；`V68-BAL` 为**均衡 5+5 均衡性地图** decoder-free 预冻结（`252` 枚举 `max→sum→abs→lex`）；`V69-3L` 为**三层表示可行性地图** decoder-free 预冻结，当前 `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`（仅重划分 10 bits 为三层有序 `w∈[2,5]` 找 CAL-only `P*` 使 `∀m_i<1024`，枚举 `3^10=59049→37170` 升序唯一词典序 `max_util→disclosure→ΔNLL→lex` 选 `P*`，Phase A CAL-only Phase B VAL确认 per-layer `VAL-CAL≤0.5/unseen≤1%/chain 1e-9/m<1024`，报告 dedup_stats，session 复用 V67 三预注册 Stage2，终态 per-session 5分流 + 总体5态 + common三 session 同 assignment 审计，不跑 decoder 不构矩阵，不启 V70）；`V69` 本身不直接进入 qualification；任何 decoder / 新表示需另起 `EXECUTE_AUTH`。
