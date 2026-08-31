# OpenSpec Tasks: formal-ir-v69-three-layer-representation-feasibility — 三层表示可行性地图 (PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED)

**Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — **1024维符号三层有序 `w∈[2,5]` 重划分，枚举 `3^10=59049→37170` 去重统计，按升序唯一词典序 `max_util→disclosure→ΔNLL→lex` 选 `P*`，Phase A CAL-only 选 P* Phase B VAL确认 per-layer `VAL-CAL≤0.5` + `unseen≤1%` + `chain 1e-9` + `m<1024`，session 复用 V67 三预注册 Stage2，per-session 5分流 + 总体5态 + common三 session 同 assignment 审计，四工件 spike/results/table/report+test，守卫 R69-01~10，不跑decoder不构矩阵不读TEST不启V70**

**HEAD**: `fcf3e457ecf45c58e23f91d750acd5267d541795` + data `84d62779` (复用 V67/V68 清理后 HEAD)

**Predecessor**: `formal-ir-v68-balanced-gf32-bit-partition` `fcf3e457ecf45c58e23f91d750acd5267d541795` + `formal-ir-v67-multisession-feasibility-map` `V67_FEASIBILITY_MAP_ACCEPTED` (3 sessions 均 `NEAR_FULL` natural 5+5) → `V69-3L`

**Method frozen**: `n1024 q1024 GF32 poly37 H1 16×1024 rank16 80b U 二层 natural 5+5 参照 + U 三层 (S1,S2,S3) w∈[2,5] Σw=10 有序非空 37170种仅重标记 Lane C ordinal-2 s38310x m2 184/190/192 H_inc Δ8 decoder 90/1.0 full-tag canonical leak Σw_i·m_i+64` 零改；处理点 `84d62779` 单点；`P` `3^10→37170` 枚举去重

**Boundary**: 仅 `P` 三层重划分，不改主体；`3^10=59049→37170` 升序枚举按 `T=(max_util, raw, max_ΔNLL, P_lex)` 选 `P*`（`max_util=max_i(m_i/1024)` 主、`raw=Σw_i·m_i+64` 次、`max_ΔNLL` 三、`P_lex` 字典序决胜，其中 `P_lex=tuple(assign[0..9])`），`Phase A CAL-only` 不读 VAL/TEST，`Phase B VAL` 确认 per-layer `VAL-CAL≤0.5` + `unseen≤1%` + `chain 1e-9` + `∀m_i<1024`，V67 三 session Stage2 复用 `CAL1024+VAL256` 不重估计；per-session 5分流 `EVIDENCE_INCOMPLETE > MODEL_NOT_STABLE > THREE_LAYER_FEASIBLE(∀m_i<1024) > PARTIAL_FEASIBLE(∃m_i<1024) > STILL_HEAVY` + 总体5态 `EVIDENCE/MODEL/COMMON_FEASIBLE/PER_SESSION_ONLY/STILL_HEAVY` + common 三 session 同 assignment 审计；DECODER_FREE 四工件已验后推送新 SHA，不构矩阵不跑 decoder不启V70

## Phase A — 注册表复用与枚举前置（V67 Stage2 复用，`3^10→37170` 去重统计，不重估计）

- [ ] **A1 复用 `v67_data_registry.json` 的 Stage2 帧集（机械，不按 CE 替换，不启 V70）**：读取 `openspec/changes/formal-ir-v67-multisession-feasibility-map/v67_data_registry.json` 的 `sessions[3]`（`20260123_1M_600k_0dB 1M / 20260107_PPLN_1p5M 1p5M / 20260123_2M_1p2M_0dB 2M`）的 `stage2_CAL_frame_ids[1024] (262144 pairs) + stage2_VAL_frame_ids[256] (65536 pairs)` 原样拷贝至 `v69_data_registry.json`（`schema v69_data_v1, lifecycle PLAN_CANDIDATE, head fcf3e457ecf45c58e23f91d750acd5267d541795, data_sha 84d62779, reused_from v67, successor_v70_not_started true, sessions[3], per_session {session_id, acquisition_id, source_label, provenance, stage2_CAL[1024], stage2_VAL[256], zero_overlap_verified, acquisition_dedup_verified, frozen, not_sorted_by_CE}`），校验 `total 3 && per_category 1,1,1 && acquisition_dedup_verified && zero_overlap_verified && Stage2_key ∩ (V13..V68)_key ==∅` 键 `(source,session,frame)`，禁止事后换 session，且 `successor_v70_not_started==true`。

- [ ] **A2 枚举 `3^10=59049` → 过滤 `37170` 有效三层有序非空 `w∈[2,5]` 划分（ponytail: `itertools.product`/`base-3`）**：生成 `assign_list = list(itertools.product([1,2,3], repeat=10))` 或等价 `base-3 0..59048` 升序 `59049` 行，校验 `len(raw)==59049==3**10`，对每 `assign` 计 `w_i = count(assign==i)`，过滤 `2≤w_i≤5 ∀i && Σw_i==10 && S_i≠∅` 得 `valid_list` 校验 `len(valid)==37170` 且 `12` 种 `w pattern` 各计数 `2520/3150/4200` 分表一致（见 Design §5.4），`dedup_stats={raw 59049, valid 37170, per_pattern[12], empty_filtered, width_filtered}` 落盘 `v69_manifest.json:enum`，`P_lex = tuple(assign)` 字典序保证唯一。

- [ ] **A3 冻结 U 三层重标记函数（纯比特置换，不改 s，不启 V70）**：实现 `bits_P(s, P) -> (u1,u2,u3)` 其中 `u_i = Σ_{k=0..w_i-1} ((s>>S_i[k])&1)<<k` with `S_i = {j | assign[j]==i} sorted`，每帧校验 `∀s s == perm_P^{-1}(u1,u2,u3)` 双射且 `chain 10 bits` 无丢，每 `P` 的 `w_i` 与 `U` 值域 `0..2^{w_i}-1` 已验，`rg -i "gray|met|protograph|sc_coupling|v70" 0 hits`（除 `P` 纯比特三层重划分注释），`src/` 零改，`V70_not_started` 已显式。

## Phase B — 冻结主体 1024维三层验证仅重划分（decoder-free，不构矩阵，不启 V70）

- [ ] **B1 主体明文化（逐项显式，冻结零改，不启 V70）**：写入 `v69_manifest.json:frozen_body {n1024, q1024, GF32 poly37, H1 16×1024 rank16, U_natural 32*U1+U2 F03 5+5 参照, U_three_layer bits_P(P) 37170种仅重标记 w∈[2,5] Σw=10 有序非空, per_frame 256, Lane C 184/190/192, H_inc Δ8, decoder 90/1.0 poly37 disabled, full-tag canonical, leak Σw_i·m_i+64, materialization legacy_v1, successor_v70_not_started true}`，显式 `not Gray/not MET/protograph/SC/not H construction/not V70`，`git diff -- src/ ==0` 已验。

- [ ] **B2 权威算法只读复用**：直接复用 `src.reconciliation.run_nbldpc_demo_point` 的 `legacy_v1` 物化算法不重写；`Stage2 CAL/VAL` 均按该链物化后 `frame_id=row//256` 切片，`U` 三层重标记仅在 `a_cal/b_cal` 的 `s` 上比特置换，不改 `pairs.parquet` 帧边界，不读 TEST，不启 V70。

- [ ] **B3 不构矩阵守卫 + 不启 V70 守卫**：`rg "decode_|construct_|gf_rank|nested" scripts/v69_three_layer_feasibility.py 0 hits` 且不调用任何 `H` 构造、`rank`、`nested` 函数，且 `rg -i "v70|qualification" scripts/v69_three_layer_feasibility.py 0 hits`（除 successor 注释 `V70_not_started`），`py_compile` 校验；脚注 `ponytail:` 标明 ceiling（若需后续三层码构造/V70，需另起 OpenSpec）。

## Phase C — Phase A CAL-only 选 P*（`37170` 枚举 × CAL 4-fold，不读 VAL/TEST，不启 V70）

- [ ] **C1 每 session CAL1024 上 `37170×(C_ab/P/λ)` 估计（CAL-only，去重统计）**：按 `CAL1024 (262144 pairs)` 先算一次 `C_ab 1024×1024 int32 sum 262144 → N_b/P_global`，对每 `P` 由 `C_ab` 重汇总得 `P(U1|B) 2^{w1}×1024 + P(U2|U1,B) + P(U3|U1,U2,B)`（不重算 `C_ab`），`λ∈[1e-2,1e4] log10` 仅 `CAL 内 4-fold`（每 fold 256 frames 65536 pairs）最小 `CV NLL` 择优，生成 `per_P CAL {w1/w2/w3, λ, λ_at_boundary, H_cal_cv_i, CV_NLL_i, ΔCE_cv, effective_contexts}`，落盘 `per_P CAL`，校验 `used_val_in_selection==False && used_test==False && dedup_stats.valid==37170`，`S=37170` 行每 session（或 Top-K 浓缩但 `P*` 选优需全量）。

- [ ] **C2 CAL-heldout `CE→m_cv` 排序键（升序唯一词典序 `max_util→disclosure→ΔNLL→lex`）**：对每 `P` 以 `CAL` 的 held-out 折均值计 `CE1_cv=-E_{heldout} log P(U1|B), CE2_cv, CE3_cv` → `m1_cv=ceil(1.3*1024*CE1_cv/w1), m2_cv, m3_cv`，`max_util_cv = max_i(m_i_cv/1024)`，`raw_cv = Σ w_i·m_i_cv+64`，`max_ΔNLL_cv = max_i(ΔNLL_i_cv)`，`P_lex=tuple(assign)`，`T(P)=(max_util_cv, raw_cv, max_ΔNLL_cv, P_lex)`，按 `T` 升序选 `P*_per_session(CAL)`，`P*_common(CAL)` 按 `T_common(P)=(max_{sess} max_util_cv, max_{sess} raw_cv, max_{sess} max_ΔNLL_cv, P_lex)` 升序选（需三 session 同 assignment 的 worst 聚合），落盘 `P*_per_session[3] + P*_common + T_sorted 37170 + dedup_stats per_pattern`，校验 `37170` 行排序稳定且 `P*` 唯一且 `common` 同 assignment。

- [ ] **C3 去重统计审计**：落盘 `dedup_stats {raw 59049, valid 37170, per_pattern: {(2,3,5):2520,...}, filtered_empty, filtered_width_violation}` 供 Phase F 报告 12-pattern 分表。

## Phase D — Phase B VAL确认 + per-layer 门禁（VAL256 独立度量，不重选 P*，per-layer `VAL-CAL≤0.5` + `unseen≤1%` + `chain 1e-9` + `m<1024`）

- [ ] **D1 VAL256 上 P* 双计量（VAL 确认，TEST隔离，per-layer 门禁，chain 1e-9）**：对 `P*_per_session(CAL)` 与 `P*_common(CAL)` 在 `VAL256 (65536 pairs)` 上以 `P_λ*` 计 `CE_full=-E_VAL log P(A|B), CE1/CE2/CE3`，校验 `|CE_full-CE1-CE2-CE3|<1e-9` 否则 `EVIDENCE_INCOMPLETE`，落盘 `VAL {CE1,CE2,CE3,CE_full,chain_delta, H_cal_i, ValNLL_i, ΔNLL_i, ΔCE_i=|CE_i^{VAL}-CE_i^{CV}|, val_b_context_unseen, joint_cell_unseen, q_mass_unseen (descriptive), descriptive_diagnostics×3, capacity_warning_m1/m2/m3/disclosure, m1_raw,m2_raw,m3_raw, raw_disclosure, max_util, max_ΔNLL}` per `P*`，`m_i_raw=ceil(1.3*1024*CE_i/w_i)` 不 cap，`raw=Σw_i·m_i+64`，校验 `∀i ΔCE_i≤0.5 && ΔNLL_i≤0.5 && val_b_unseen≤1% && chain<1e-9` 否则 `MODEL_NOT_STABLE`。

- [ ] **D2 per-layer Δ 审计**：落盘 `per_layer_diagnostics {ΔCE1,ΔCE2,ΔCE3, ΔNLL1,ΔNLL2,ΔNLL3, val_b_unseen, joint_unseen, q_mass (descriptive)}` 三层各显式，报告 `max_util` vs `raw` vs `max_ΔNLL` 三元组。

- [ ] **D3 一致性字段 + m<1024 门禁**：落盘 `cal_val_consistency = (P*_per_session(CAL) == argmin_{P} T_val(P))` 其中 `T_val` 为同 `T` 但用 `VAL` 上 `m_raw` 排序，若不一致以 `CAL` 为准，报告 `cal_val_consistency` 与 `VAL` 上 `P*_val` 备选；同时落盘 `∀i m_i<1024` 布尔与 `raw<10240` 供 5分流。

## Phase E — per-session 5分流 + 总体5态 + common三 session 同 assignment 审计（优先级互斥，不启 V70）

- [ ] **E1 Per-session 5分流（优先级互斥，per-layer ≤0.5 + unseen≤1%）**：取 `VAL` 上 `P*_per_session(CAL)` 的 `m_i_raw_val/raw_val/ΔCE_i/ΔNLL_i/unseen` 按 `EVIDENCE_INCOMPLETE(CE_chain/非有限/dedup 不足37170) > MODEL_NOT_STABLE(λ触边/∃i ΔCE>0.5/∃i ΔNLL>0.5/val_b>1%/非有限) > THREE_LAYER_FEASIBLE(∀m_i<1024&&raw<10240&&∀ΔCE≤0.5&&unseen≤1%) > PARTIAL_FEASIBLE(∃m_i<1024) > STILL_HEAVY` 互斥已验，`capacity_warning` 正交，`q_mass/joint/H_cal` 仅描述性，落盘 `classification + successor {three_layer_code_design, rate_adaptive_or_new_representation, new_representation, recollect}` per session，且 `V70_not_started`。

- [ ] **E2 总体5态（基于 common P*_common 的 VAL 度量，需三 session 同 assignment）**：对 `P*_common(CAL)` 在 3 sessions 上的 `VAL` 度量得 `common_feasible_count = #{sess | THREE_LAYER_FEASIBLE}`，`per_session_feasible_count = #{sess | per_session P* THREE_LAYER_FEASIBLE}`，`partial_count = #{sess | PARTIAL_FEASIBLE}`，判定 `overall = EVIDENCE_INCOMPLETE if any EVIDENCE else MODEL_NOT_STABLE if any MODEL and common==0 else THREE_LAYER_COMMON_FEASIBLE if common_feasible==3 (同 assignment) else THREE_LAYER_PER_SESSION_ONLY if per_session_feasible≥1 or partial≥1 else STILL_HEAVY`，落盘 `overall + common_feasible_count + per_session_feasible_count + partial_count + P*_per_session[3] + P*_common + T_common_sorted + dedup_stats`。

- [ ] **E3 Common 同 assignment 审计表**：落盘 `audit {P*_per_session, P*_common, T_per_session, T_common, dedup_stats{raw 59049, valid37170, per_pattern12}, max_util/disclosure/ΔNLL per P, common_feasible_count, per_session_feasible_count, partial_count, cal_val_consistency[3], per_session_classification[3], per_layer ΔCE/ΔNLL/unseen}`，报告 `common 同 assignment` 审计章节显式三 session 是否同 `P*_common`。

## Phase F — 四工件 + 审计报告交付（PLAN_CANDIDATE / DECODER_FREE，不启 V70）

- [ ] **F1 编写 `scripts/v69_three_layer_feasibility.py`** (decoder-free, 本变更目录下): `python scripts/v69_three_layer_feasibility.py [--registry v69_data_registry.json] [--out v69_results.json]` → `CAL1024 37170×C_ab/P/λ→m_cv→T→P* → VAL256 P* CE/m + per-layer VAL-CAL + chain + dedup_stats + common同 assignment`，`rg "decode_|construct_|gf_rank|nested" 0 hits` `rg -i "met|protograph" 0 hits` `rg -i "v70|qualification" 0 hits`（除 successor V70_not_started 注释）仅 `numpy/pandas/pyarrow+itertools`，`py_compile PASS`，输出 `v69_results.json + v69_table.(csv|json) + dedup_stats` + 控制台摘要。

- [ ] **F2 执行 decoder-free 枚举回填（含去重统计）**：运行 `scripts/v69_three_layer_feasibility.py` 得每 session `37170` 行 `CE_i/CE_full/λ/ΔNLL/unseen/m/max_util/raw`（或 Top-K 浓缩 + 全量 dedup_stats）与 `P*_per_session/P*_common`，落盘 `v69_results.json` 与 `v69_table.csv/.json`（CSV 行对等，含 `capacity_warning` 正交 + `per-layer ΔCE`），`dedup_stats {59049→37170 per_pattern}` 已验。

- [ ] **F3 撰写 `V69_THREE_LAYER_REPORT.md`**：`per session 3^10→37170 去重统计 12-pattern 分表 + P*_per_session + P*_common + CAL/VAL 双组 CE_i/λ/ΔNLL/unseen/m/max_util/raw/classification/successor/cal_val_consistency/per-layer VAL-CAL + overall 5态 + common同 assignment审计 + map_sparse 标记 + TEST隔离 + 1024维冻结 + V70_not_started` 与 `json/csv` 一致，不扩大为 `FER/SKR`，显式 `37170 枚举去重 + 词典序 `max_util→disclosure→ΔNLL→lex` 唯一 + Phase A CAL-only + Phase B VAL确认 per-layer ≤0.5`。

- [ ] **F4 自检（5分流+5态+守卫+R69-01~10，不启 V70）**：`py_compile` spike PASS, `rg "decode_|construct_|gf_rank|nested" 0 hits`, `rg -i "met|protograph" 0 hits`, `rg -i "v70" 0 hits`（除 V70_not_started 注释），`git diff -- src/ ==0` 未改码, V67 Stage2 复用 `3` 已验, `P 3^10→37170` 去重枚举已验, `|CE_full-ΣCE_i|<1e-9` 已验, `T max_util→disclosure→ΔNLL→lex` 唯一 + common同 assignment 已验, `Phase A CAL-only` 已验, `m_raw ceil` 不 cap `raw_disclosure Σw_i·m_i+64` 显式已验, `per-layer VAL-CAL≤0.5 && unseen≤1% && m<1024` 已验, `5分流优先级互斥` 已验, `overall 5态+common` 已验, `TEST 未读` 已验, `V70_not_started` 已验, 报告与 json/csv 一致 **无 TBD**, **A-E 已闭合**。

- [ ] **F5 小测试**：`pytest -p no:cacheprovider -q` 小测试（`test_v69_three_layer_small.py`）验证 `bits_P / permute / w∈[2,5]过滤 / dedup_stats 59049→37170 / T排序唯一性 + common同 assignment / CAL-only + per-layer VAL-CAL` 纯函数与 `TEST隔离` + `V70_not_started`，`py_compile` 双 PASS。
  - ponytail: `bits_P` 为 10-bit 纯移位/掩码，不引 `numba`；`T` 排序为 `tuple` 升序最小，`O(37170 log 37170)` 足够，Phase B VAL 仅对 `P*` 详计以控成本。

## Phase G — 守卫 R69-01~10 + 单独提交推送新 Plan SHA + 不启 V70

- [ ] **G1 守卫 R69-01~10 落盘验证**：在 `v69_manifest.json:guards {R69-01..R69-10}` 逐项 `true`，见 Design §8 / Spec §10。
  - R69-01 冻结主体 1024维三层验证不改 + 不启 V70
  - R69-02 枚举 `3^10=59049→37170` 去重统计完整（12-pattern 分表）
  - R69-03 升序唯一词典序 `max_util→disclosure→ΔNLL→lex` + common 同 assignment
  - R69-04 Phase A CAL-only 选 P*
  - R69-05 Phase B VAL确认 per-layer `VAL-CAL≤0.5` + `unseen≤1%` + `chain 1e-9` + `m<1024`
  - R69-06 V67三Session Stage2 复用 + 不启 V70
  - R69-07 per-session 5分流+总体5态+common同 assignment审计
  - R69-08 四工件+test 完整（含 dedup_stats）
  - R69-09 decoder-free不构矩阵 + 不读 TEST
  - R69-10 不创run_01+编译+小测试+TEST隔离+不启V70
- [ ] **G2 单独提交推送四工件+registry+spike+报告表（V69 provenance — 新 Plan SHA）**：`git add openspec/changes/formal-ir-v69-three-layer-representation-feasibility/ scripts/v69_three_layer_feasibility.py v69_data_registry.json v69_results.json v69_table.csv v69_table.json V69_THREE_LAYER_REPORT.md test_v69_three_layer_small.py && git commit -m "formal-ir-v69: three-layer 3^10→37170 w∈[2,5] CAL-only max_util→disclosure→ΔNLL→lex P* VAL per-layer ≤0.5 common同assignment V67 Stage2 reuse" && git push origin formal-ir-mainline`，返回新 `Plan SHA`（40位），记录于 `proposal/design/tasks` HEAD 占位替换，**不创建 run_01，不启 V70**。
- [ ] **G3 停留 `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` + `V70_NOT_STARTED`**，未创建任何 `.../v69_*/run_01` 且未创建 `.../v70_*/run_01`，未构矩阵，不比较，不碰 `V48-V68` 块外，未转 qualification，未启动 V70，仅改本目录 + `scripts/`，**推送后等待独立审核**（`Pre-RESULT` 独立线程复核 `HEAD/ACCEPTED_PLAN_SHA/rg 0 hits/run_01不存在/py_compile/TEST 未读/m_raw 显式/59049→37170枚举去重词典序唯一/5分流+5态/common同assignment/per-layer VAL-CAL≤0.5/unseen≤1%/chain 1e-9/V70_not_started`），返回 `Plan SHA / P*_per_session[3] / P*_common / 各分流计数 / dedup_stats + common审计` 等待 `PLAN_ACCEPT`。

## 本变更显式禁止

decoder/矩阵构造 (`decode_*` / `construct_*` / `gf_rank` / `nested` 等)；读密封 `TEST` 的 `H/CE/NLL/MAP` 统计或将其用于 `P/m/P*` 选择；读 `VAL` 参与 `P*` 择优（`P*` 仅 `CAL`）；在原 `V55 90-block` 或 `V48-V68` 已用 `(source,session,frame)` 上重跑先验估计而不零重叠；调 `H1/Lane C/Δ8/decoder/m2/m_total/leak/prior/H_inc/H_total/verification` 任一冻结参数或新增矩阵；**跨 acquisition 拼接凑 3**；**将 floor/round 当 ceil**；**将 `min(1024, ceil(...))` cap 伪装当通过**（`m_raw` 必须显式 Σw_i·m_i+64）；**将 `+8` 外 degree/seed 网格当自适应**；**用 `VAL/TEST` 择优 `P*`**（`P*` 仅 `CAL`）；**将不足 3 伪判为 complete**（应 `EVIDENCE_INCOMPLETE`）；**将 `acquisition` 未去重多计**（必须 V67 复用）；**将 `P` 剪枝至 <37170**（除 `w∈[2,5]` 硬过滤必须 `37170`）；**将 `T` 换 `disclosure→max_util` 等非 max_util 主**（必须 `max_util→disclosure→ΔNLL→lex`）；**将 `P*_common` 按平均而非 worst max_{sess}**（必须 `max_{sess} max_util` + 同 assignment）；**引 MET/protograph/SC/Gray**（仅 `P` 纯重划分）；**改 `src/` 基线**；宣称 LDPC 证伪或 `FER/阈值/SKR/晋升`；创建正式 `.../v69_*/run_01`；任意 `bin_width/dimension/pairing/mapping` 网格或阈网格（处理点单点）；用第二 estimator 作门禁；覆盖已有输出；`V55 90 / V48-V68` 永久禁用違反；**主观“显著可行”替代硬阈 `∀m_i<1024 && per-layer ≤0.5 && unseen≤1%`**；**擅自调 V69 以外码**（仅 `P` 三层重划分）；**保留 TBD 占位不回填**；**启动 V70**（任何 `V70_*/run_01`、`QUALIFICATION_PLAN_READY`、`V70` OpenSpec 预冻结均禁止）。

## 验收

- proposal/design/tasks/specs 一致 `fcf3e457ecf45c58e23f91d750acd5267d541795→新 Plan SHA` `84d62779` lifecycle `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` + `V70_NOT_STARTED` 5分流+5态按优先级互斥明确，显式 1024维冻结仅重划分10 bits 三层有序 `w∈[2,5]`、枚举 `3^10=59049→37170` 去重统计升序唯一词典序 `max_util→disclosure→ΔNLL→lex` 选 `P*` + common同 assignment、`Phase A CAL-only` 不读 VAL/TEST `Phase B VAL确认 per-layer ≤0.5 + unseen≤1% + chain 1e-9 + m<1024`、V67三Session Stage2 复用、per-session 5分流 + 总体5态 + common审计、四工件产出已声明，严格复用 V56 权威算法，冻结分段/熵-CE 与 m 公式/分流阈 + V70_not_started
- 1024维冻结仅重划分已验，`P 3^10→37170` 去重枚举升序唯一词典序 `T max_util→disclosure→ΔNLL→lex` + common同 assignment 已验，`Phase A CAL-only` 不读 VAL/TEST 且 `P*` 以 `CAL m_cv` 选已验，`Phase B VAL` 上 `P*` 双计 `CE/m` 链式 `|CE_full-ΣCE_i|<1e-9` 且 per-layer `VAL-CAL≤0.5 && unseen≤1% && m<1024` 已验，`m_raw ceil` 不 cap，`TEST` 未读已验，3 sessions 复用已验，**新 Plan SHA 已推送，V70 未启动**
- 合同 `dimension 1024 / bin200 / nearest legacy_v1 / channels/frame anchor/mapping 每帧256` 算法一致已验，`U` 三层重标记 `bits_P` 每帧已验，偏则 `EVIDENCE_INCOMPLETE` 已验，`37170` 去重 + `59049` raw 已验
- 每 session `CAL 37170×C_ab → P(U1|B)/P(U2|U1,B)/P(U3|U1,U2,B) λ(CAL 4-fold) → VAL CE1/CE2/CE3/CE_full 链式 → m_i_raw ceil → T max_util→disclosure→ΔNLL→lex 选 P*` 已算且 `CAL-only` 已验，`VAL` 上 `P*` 计 `m_raw/raw` 且 per-layer `ΔCE/ΔNLL/unseen` 已报告，不扩，禁第二 estimator 已验，`cal_val_consistency` 已报告，`dedup_stats 12-pattern` 已落盘
- 每 session `5分流 final_classification + successor` 已落盘，`overall 5态 + common审计 P*_per_session/P*_common/common_feasible_count/partial_count/dedup_stats` 已统计
- `37170行(或Top-K+ dedup_stats)/ P*/ CAL/VAL 双组 CE/λ/ΔNLL/unseen/m/max_util/raw/classification/successor/capacity_warning/descriptive` 已回填，`报告表 CSV行对等 JSON` 已验，`overall 5态` 已验，`V70_not_started` 已验
- 守卫 `R69-01~10` 已验（`59049→37170` 去重枚举/唯一词典序+common同 assignment/CAL-only/VAL确认 per-layer ≤0.5 + unseen≤1% + chain/m<1024/V67复用/5分流+5态+common/四工件+test/decoder-free不构矩阵不读TEST/不创run_01/py_compile/小测试+V70_not_started）
- 双脚本 `rg "decode_|construct_|gf_rank|nested" 0 hits` `rg -i "met|protograph" 0 hits` `rg -i "v70" 0 hits`（除 V70_not_started 注释） `py_compile` PASS `pytest 小测试` PASS `m_raw` 未 cap `VAL 未参与选优` `TEST 未读` `37170 去重` 已验 `common同 assignment` 已验 `capacity_warning` 正交与 `descriptive` 已落盘 报告与 json/csv 一致 未建 `run_01` 未启 `V70` 已停留 `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` 仅改本目录 + `scripts/`（`src/` 零改），未启动 decoder/矩阵，**四工件+registry+spike+报告表已单独提交推送，新 Plan SHA + P*_per_session + P*_common + 各分流数 + dedup_stats + common审计已返回**，推送后等待独立审核
