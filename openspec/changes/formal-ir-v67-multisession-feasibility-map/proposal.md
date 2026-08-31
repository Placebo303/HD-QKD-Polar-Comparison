# OpenSpec Proposal: formal-ir-v67-multisession-feasibility-map

**Status**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — 本轮仅交付计划四工件 + decoder-free 只读多 session 可行域地图（≤9 session acquisition 去重预注册，每类≤3 机械预注册不按 CE 替换），分阶段 Stage0 8frames 物化 → Stage1 CAL256 VAL128 分类 → Stage2 CAL1024 VAL256 confirmation 不重叠重新独立估计，TEST 不读，冻结 U=32*U1+U2 5+5 不GE，码率 m_raw 不 cap，五分流判定，总体 V67_FEASIBILITY_MAP_COMPLETE，不实现/不执行 decoder，不创建 run_01，不调 V68 码

**Domain**: Formal IR / NB-LDPC multisession feasibility map (V64/V65/V66 同域多 session 扩展，V68 前置)

**Change ID**: `formal-ir-v67-multisession-feasibility-map`

**Cycle ID**: `V67-MAP` (multisession-feasibility-map), predecessor `formal-ir-v66-single-segment-adaptive-nbldpc` (`832e5394bb → f4040fc1 24+24+24 single-source RATE_NOT_FEASIBLE`) + `formal-ir-v65-new-session-channel-compatibility` + `formal-ir-v64-full-symbol-verification-correction (22/24 PASS)`

**Branch**: `formal-ir-mainline`

**HEAD**: `b9f29173 (本次 proposal/design/tasks/specs 四工件 + registry + spike + report 落盘后单独提交推送产生的新 40 位 Plan SHA，实施前 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline` 40 位重核，不一致阻塞；归档前重核)`

**Data SHA**: `84d62779` (`84d62779603e62de50ded5182ed65b65d3dc6084`, `d=1024 bw=200ps pairing=nearest rule=legacy_v1` 单点；V67 多 session 复用该处理点，不换点，不换 bin/mapping)

**Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — 本轮止于计划四工件 + decoder-free 地图（registry + spike.py + report + feasibility table），零 decoder/矩阵/依赖（`numpy/pandas/pyarrow` 已装），不创建 `run_01`，不比较，不转 qualification，任何 decoder 执行需独立 `PLAN_ACCEPT + EXECUTE_AUTH`

> ponytail lite: 本变更仅 4 OpenSpec 工件 + 1 decoder-free spike 脚本 + 1 注册表 + 1 报告 + 1 可行域表（CSV/JSON 双写）；零 decoder/矩阵/新依赖（`numpy/pandas/pyarrow` 已装），最短科学路径。laziest alternative: `numpy` 直算 `C_ab/bincount2d` + 链式 CE，不引 `scipy/sklearn`；`m` 校验纯代数 `ceil(1.3*1024*CE/5)`，不调 decoder。

> **科学问题（冻结）**：于**按 acquisition 去重预注册的最多 9 session**（每类≤3 机械预注册，不按 CE 替换，上界 9）上，对每 session 独立执行 **Stage0 8 frames 物化校验 → Stage1 CAL256 + VAL128 初分类 → Stage2 CAL1024 + VAL256 独立重估确认**（Stage1/Stage2 不重叠且与历史零重叠，TEST 不读，U=32*U1+U2 5+5 冻结不 GE），以 `CAL` 重估层级先验 `P(U1|B)/P(U2|U1,B)`，以 `VAL` 上 `CE1/CE2` 得 `m1_raw=ceil(1.3*1024*CE1/5), m2_raw=ceil(1.3*1024*CE2/5), raw_disclosure=5*(m1_raw+m2_raw)+64` **不 cap**，每 session 按阈机械分流至五类 `V67_EVIDENCE_INCOMPLETE / MODEL_NOT_STABLE / CURRENT_CANDIDATE_COMPATIBLE(≤16/≤LaneC+8+8) / RATE_ADAPTATION / NEAR_FULL_DISCLOSURE(≥1024 或 ≈10240)` 之一，并给出 successor，建议；全部 session 判定完成后总体 `V67_FEASIBILITY_MAP_COMPLETE`。全程 decoder-free，先验 `TEST` 隔离，`U/Δ8` 冻结，不引 V68 表示。

## Goal

以最短 decoder-free 路径完成**多 session 可行域地图**的预注册与机械分类，为 V68 码族/rate-adaptive 设计提供可验证的分流证据：

### 1. 按 acquisition 去重预注册最多 9 session（每类≤3 机械，不按 CE 替换）
- **去重键**：`acquisition_id`（由 `ttbin` 头/session_id 派生，含 `source_label / wall_time / acquisition_counter`），同一 `acquisition_id` 即便导出多份 `pairs.parquet` 仅计 1 session；`registry.acquisition_dedup_key = (source_label, acquisition_id)`。
- **上界**：`total_sessions ≤9`，`per_category ≤3`（category = `source_label` ∈ {`1M`,`1p5M`,`2M`} 或等价 `bw/delay` 三档；三类各 ≤3，机械按 `acquisition_time` 升序取前 3，不按 `CE/m` 优选替换）。
- **机械预注册**：registry 创建时即冻结 `session_id` 列表（`v67_data_registry.json: sessions[≤9]`），后续 `spike.py` 不得按 `CE/m` 增删替换；不足 9 允许 `3..9` 稀疏地图，但需显式 `map_sparse=true`，`overall` 仍 `FEASIBILITY_MAP_COMPLETE`（稀疏不判 `DATA_NOT_READY` 除非 <3 或单 session Stage0 失败另走 `EVIDENCE_INCOMPLETE`）。
- **可复用历史域**：复用 `v55_intake_20260828` 已有 `pairs/` 下按 acquisition 去重后的 session 目录（不跨 acquisition 拼接），禁止以 `CE/m` 事后挑 session；与 `V13/V48..V66` 零重叠键 `(source, session_id, frame_id)` 已验。

### 2. 分阶段 decoder-free 流水（TEST 不读，Stage1/Stage2 不重叠重新独立估计）
- **Stage0 — 8 frames 物化校验（per session）**：每 session 取前 8 frames（`8*256=2048 pairs`）按 `84d62779 legacy_v1` 物化校验 `dimension 1024 / bin200 / nearest / channels A1,B5 / frame anchor / U=32*U1+U2 5+5 natural / 每帧 256`，失败则该 session `EVIDENCE_INCOMPLETE`，不进入 Stage1。
- **Stage1 — CAL256 + VAL128 分类（per session，不重叠）**：`CAL 256 frames (65536 pairs) + VAL 128 frames (32768 pairs)` 互不重叠且与 Stage0 8 frames 不重叠（键 `(source,session,frame)`），`CAL` 上 `C_ab 1024×1024 → P_global → P(U1|B)/P(U2|U1,B) λ 仅 CAL 内 4-fold 择优`，`VAL` 上计量 `CE1=-E_VAL log P(U1|B), CE2=-E_VAL log P(U2|U1,B), CE_full` 链式，`m1_raw=ceil(1.3*1024*CE1/5), m2_raw=ceil(1.3*1024*CE2/5), raw_disclosure=5*(m1_raw+m2_raw)+64` **不 cap**，落盘 `λ/CE/ΔNLL/q_mass_unseen/m_raw/raw_disclosure` 供五分流。
- **Stage2 — CAL1024 + VAL256 confirmation 独立重估（per session，不重叠，重新独立估计）**：`CAL 1024 frames (262144 pairs) + VAL 256 frames (65536 pairs)` 与 Stage1 零重叠（`Stage1_key ∩ Stage2_key == ∅`），**重新独立估计**：重算 `C_ab/P_global/λ(仅新 CAL 内 4-fold)/P(U1|B)/P(U2|U1,B)/CE/m_raw/raw_disclosure`，不复用 Stage1 的 `C_ab/λ/CE`，落盘第二组 `λ2/CE2_xxx/m_raw2` 供 confirmation；若 Stage2 与 Stage1 分类不一致则以 Stage2 为准，报告 `stage_consistency` 字段。
- **TEST 不读**：任何 `TEST/EVAL` 域（如 `V65 TEST 120` / `V66 EVAL 24`）均不读 `H/CE/NLL/MAP` 统计作 `P/m/阈值` 选择，脚本内 `assert used_test_in_estimation==False`，违则 `EVIDENCE_INCOMPLETE` 范畴。

### 3. 冻结表示 U=32*U1+U2 5+5 不GE V68 表示
- **冻结**：`U =32*U1+U2, F03 5+5 natural, U1=s>>5 0..31 high, U2=s&31 low, 每帧 256, n=1024, q=1024 (10-bit)` 全只读，`src.reconciliation.run_nbldpc_demo_point legacy_v1` 原样复用。
- **不GE（不 Gray/不 V68）**：禁止引入 `Gray / V68 2+8/4+6/6+4` 等分解、禁止 `MET/protograph/SC` 新码族、禁止以 V68 码本/映射作对照门禁；`spike.py` 内 `rg "gray|V68|v68|GRAY|met|protograph"` 0 hits（大小写不敏感）且 `git diff -- src/ ==0`；脚注 `ponytail:` 标明 ceiling（若需 V68，需另起 OpenSpec）。

### 4. 码率 raw 不 cap 与五分流（每 session 独立）
- **raw 公式**：`m1_raw = ceil(1.3*1024*CE1/5)` ∈ [0,∞), `m2_raw = ceil(1.3*1024*CE2/5)`, `m_total_raw = m1_raw+m2_raw`, `raw_disclosure =5*m_total_raw+64` **不 cap**（禁止 `min(1024, ceil(...))` 伪装，显式报告 raw）。
- **五分流（优先级高→低，互斥，每 session）**：
  1. `V67_EVIDENCE_INCOMPLETE` — 物化/帧256/provenance/acquisition 去重失败或 Stage0 `8 frames` 不足/非法或 `CE 链式 |CE_full-CE1-CE2|≥1e-9`
  2. `V67_MODEL_NOT_STABLE` — `λ` 触边 `[1e-2,1e4]` 或 `ΔNLL=ValNLL-CAL_CV_NLL>0.50` 或 `val_b_context_unseen>1%` 或 `非有限` (`joint_cell_unseen` 仅描述, `H_cal` 仅入 `capacity_warning` 正交三项)
  3. `V67_CURRENT_CANDIDATE_COMPATIBLE` — `m1_raw ≤16 && m2_raw ≤ (LaneC_base+8+8)`（`LaneC_base` per source: `1M 184 / 1p5M 190 / 2M 192`，`+8+8 = +16` → `200/206/208`），且 `MODEL_NOT_STABLE` 未触发
  4. `V67_RATE_ADAPTATION` — `m1_raw/m2_raw` 超出现有 `Δ8` 家族但 `m1_raw<1024 && m2_raw<1024 && raw_disclosure< approx 10240`（需 rate-adaptive / 增量冗余）
  5. `V67_NEAR_FULL_DISCLOSURE` — `m1_raw≥1024 || m2_raw≥1024 || raw_disclosure≈10240 (≥5120 阈，视 10*1024)`（近全披露，无码率增益）
- **总体**：全部已注册 session 完成五分流后 `overall = V67_FEASIBILITY_MAP_COMPLETE`（即便含 `EVIDENCE_INCOMPLETE` 亦计完成，稀疏地图亦 complete，不另设 `FAIL` 总体）。

### 5. 本轮交付边界（四工件 + 地图报告 + 独立 review packet，decoder-free）
- 产出 `proposal/design/tasks/specs` 四工件 + `v67_data_registry.json`（acquisition 去重 ≤9，每类≤3 机械） + `scripts/v67_spike.py`（decoder-free `Stage0→Stage1→Stage2` 独立重估，`rg "decode_" 0 hits`） + `v67_spike_summary.json` + `V67_FEASIBILITY_REPORT.md` + `v67_feasibility_table.csv/.json`（表含 `session / CE1/CE2/CE_full / λ / gap_ΔNLL / unseen_q_mass / m1_raw/m2_raw/m1_family/m2_family / raw_disclosure / classification / successor`） + 控制台摘要；**禁** `decode_row_layered_fftqspa / construct_*` 调用（`rg "decode_" 0 hits` 守卫）、禁 `run_01`、禁跨方法比较、禁改 `src/` baseline、禁调 V68 码、禁以 `TEST` 调参。
- **四工件 + registry + spike + 报告表单独提交推送，返回新 Plan SHA + 候选列表 + 各分流数**。

## Non-Goals

- 不运行任何 `decode_row_layered_fftqspa / construct_H*` decoder（脚本内 `rg "decode_" 0 hits`，`rg "import.*decoder" 0 hits`）；不改 `H1/Lane C/m2/H_inc/decoder/full-tag` 任一冻结量；不引 `MET/protograph/SC` 新码族；不新增矩阵；不试新 `Δm/degree/seed`。
- 不读密封 `TEST` 的任何 `H/CE/NLL/MAP` 统计作 `P/m/阈值` 选择，违则 `EVIDENCE_INCOMPLETE`。
- 不做 `bin_width/dimension/pairing/mapping/frame anchor` 网格搜索（单点 `84d62779`）；`λ` 仅在 `[1e-2,1e4] log10 连续` 优化，不扩网格，触界即 `MODEL_NOT_STABLE`；不以 `VAL` 网格调 `+8` 档以外。
- 不宣称 `FER/阈值/SKR/晋升/安全证明`；本变更止于 `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`，不直接进入 qualification，不作跨方法 rank。
- 不改写/覆盖 `V13/V48–V66` 任何已有输出与终态（只读）；可复用旧数据仅作 `acquisition_dedup` 显式标记。
- 不以总体平均替代 per-session 分流；不以 `V25 H` 作新域门禁，门禁用 `VAL CE` + `m_raw`。
- 不创建正式 `.../v67_*/run_01` decoder 执行；正式 `V68` 需另起 `OpenSpec` + 独立 `EXECUTE_AUTH`。
- 不比较 Polar/Cascade/LDPC 方法；多 session 内地图，不作跨方法 rank。

## Scope

1. **acquisition 去重预注册 ≤9（每类≤3 机械，不按 CE 替换）**：`registry.sessions` 为按 `(source_label, acquisition_id)` 去重后按 `acquisition_time` 升序每类取前 3 的冻结列表（`1M≤3, 1p5M≤3, 2M≤3, total≤9`），`source_label` 来自 `session_id` 的 `type2_XM` 前缀或 `channel_counts.npz` provenance，`acquisition_id` 来自 `ttbin` 头或 `pairs.parquet` 的 `acquisition` 字段，`zero_overlap_verified` 键 `(source,session,frame)`，`acquisition_dedup_verified` 已验，禁止事后按 `CE/m` 替换。
2. **冻结主体与处理点零改（U=32*U1+U2 5+5 不GE）**：`n1024, q1024 (s=32*u1+u2), GF32 poly37, H1 16×1024 rank16, Lane C ordinal-2 s38310x m2 184/190/192 per source (base), H_inc Δ8 家族, decoder 90/1.0 poly37 early-stop (禁用), full-tag canonical 32*U1+U2, leak=5*(m1+m2)+64` 全只读；`84d62779 legacy_v1` 单点；不引 V68 表示。
3. **分阶段 Stage0 8 → Stage1 CAL256 VAL128 → Stage2 CAL1024 VAL256 不重叠重新独立估计 TEST不读**：Stage0 8 frames 物化；Stage1 `CAL256 (65536 pairs) + VAL128 (32768) + chain |CE_full-CE1-CE2|<1e-9 → m1_raw/m2_raw ceil → raw_disclosure 不 cap`；Stage2 `CAL1024 (262144) + VAL256 (65536)` 与 Stage1 零重叠且重新独立估计（重算 `C_ab/P_global/λ/CE/m_raw`），`Stage1_key ∩ Stage2_key ==∅` 且均与 `V13..V66` 零重叠（键 `(source,session,frame)`），`TEST` 不读已验。
4. **五分流机械分类（per session）与总体 complete**：每 session 按 `EVIDENCE_INCOMPLETE > MODEL_NOT_STABLE > CURRENT_CANDIDATE_COMPATIBLE(≤16/≤LaneC+8+8) > RATE_ADAPTATION > NEAR_FULL_DISCLOSURE(≥1024或≈10240)` 优先级互斥判定，落盘 `classification + successor`（`successor ∈ {none, v68_rate_adaptive, v68_new_representation, data_recollect}`），总体 `V67_FEASIBILITY_MAP_COMPLETE` 当全部已注册 session 已分类。
5. **四工件 + 地图报告表交付（DECODER_FREE）**：`scripts/v67_spike.py`（`rg "decode_" 0 hits`, `py_compile PASS`, 仅 `numpy/pandas/pyarrow`）输出 `v67_data_registry.json + v67_spike_summary.json + v67_feasibility_table.{csv,json} + V67_FEASIBILITY_REPORT.md`（表含 `session/CE/lambda/gap/unseen/m/raw/classification/successor` 等）+ 控制台摘要，未创建 `run_01`。
6. **守卫 R67-01~10**：见 Design §9 与 Spec §10，覆盖 `acquisition 去重 / Stage0 8 / 零重叠 / 独立重估 / TEST隔离 / U 5+5不GE / m_raw不cap / 五分流 / decoder-free / V68隔离 / 不创 run_01 / py_compile/小测试`。

## Impact Scope

- **新增（本变更）**：`openspec/changes/formal-ir-v67-multisession-feasibility-map/` 下 4 工件 `proposal.md/design.md/tasks.md/specs/spec.md` + `scripts/v67_spike.py` (`rg "decode_" 0 hits`, `py_compile PASS`, 仅 `numpy/pandas/pyarrow + ttbin_pipeline`) + 冻结注册表 `v67_data_registry.json` (acquisition 去重 ≤9，每类≤3 机械) + `v67_spike_summary.json` (每 session Stage0→Stage1→Stage2 双组 CE/m/raw) + `v67_feasibility_table.csv/.json` (每行 `session/CE1/CE2/CE_full/lambda/gap_ΔNLL/unseen_q_mass/m1_raw/m2_raw/m1_family/m2_family/raw_disclosure/classification/successor`) + `V67_FEASIBILITY_REPORT.md` + 控制台摘要。
- **只读依赖**：`v55_intake_20260828/pairs/*` 按 acquisition 去重 session 目录（多 session 源） + `v55_stratified_registry_candidate.json / v64_fresh_registry.json / v65_frozen_session_binding.json`（零重叠校验，键含 session） + `comparison_bench/outputs_comparison/v55_intake_20260828/` + `nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz` 仅对照。
- **不修改**：任何既有 `spec/代码/测试/输出`（除本目录 + `scripts/` 外）、`V38–V66` 输出、`outputs_comparison/workspace` 以外；**不改 `src/` 基线，不创建 `run_01`，零码参增量，不启动 decoder，不调 V68 码**。

## Acceptance Criteria

- [ ] `proposal/design/tasks/specs/spec.md` 齐全一致，`lifecycle PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`，`branch formal-ir-mainline` + `data 84d62779` + `predecessor V66 f4040fc1 / V64 22/24 PASS` 已绑定，显式声明 decoder-free、零 decoder、acquisition 去重 ≤9 每类≤3 机械不按 CE 替换、Stage0 8 → Stage1 CAL256 VAL128 → Stage2 CAL1024 VAL256 不重叠重新独立估计 TEST不读、冻结 `U=32*U1+U2 5+5 不GE V68`、码率 `m_raw ceil 不 cap raw_disclosure`、五分流阈与总体 `V67_FEASIBILITY_MAP_COMPLETE` 已声明，**新 Plan SHA 已推送**。
- [ ] **acquisition 去重预注册可复现（≤9，每类≤3 机械，不按 CE 替换）**：`v67_data_registry.json` 含 `acquisition_dedup_key=(source_label, acquisition_id)` 去重后 `sessions[≤9]`（`1M≤3, 1p5M≤3, 2M≤3`，按 `acquisition_time` 升序取前 3，非 `CE/m` 优选），`registry.frozen == true`，`registry.acquisition_dedup_verified == true`，`per_session {session_id, acquisition_id, source_label, provenance, frames_total, stage0_blocks, stage1_CAL/VAL_blocks, stage2_CAL/VAL_blocks}` 已验，禁止事后替换。
- [ ] **分阶段不重叠重新独立估计可复现（TEST不读）**：每 session `Stage0 8 frames (2048 pairs) 物化校验` → `Stage1 CAL256 (65536) + VAL128 (32768)` 零重叠 → `Stage2 CAL1024 (262144) + VAL256 (65536)` 与 Stage1 零重叠且重算 `C_ab/P_global/λ/CE/m_raw`（不复用 Stage1），键 `(source,session,frame)`，`Stage1_key ∩ Stage2_key == ∅` 且 `Stage1∪Stage2_key ∩ (V13..V66)_key == ∅` + 单 session 内连续，已验，`used_test_in_estimation==False` 已验。
- [ ] **冻结表示零改已验（U=32*U1+U2 5+5 不GE）**：`git diff -- src/ ==0`，`rg -i "gray|v68|met|protograph|sc_coupling" scripts/v67_spike.py 0 hits`，`U mapping` 每帧 `A==32U1+U2 && B==32V1+V2` 已验，处理点 `84d62779 legacy_v1` 单点已验。
- [ ] **码率 raw 不 cap 已验**：每 session Stage1/Stage2 均 `m1_raw=ceil(1.3*1024*CE1/5), m2_raw=ceil(1.3*1024*CE2/5), raw_disclosure=5*(m1_raw+m2_raw)+64` 显式，不 `min(1024, ...)` 截断，`grep "min(1024" 0 hits` 已验，`CE 链式 |CE_full-CE1-CE2|<1e-9` 已验，`λ` 仅 `CAL 内 4-fold` 搜索 `[1e-2,1e4] log10` 最小 `CV NLL` 已落盘。
- [ ] **五分流机械分类可复现（per session，优先级互斥）**：每 session `classification ∈ {EVIDENCE_INCOMPLETE, MODEL_NOT_STABLE, CURRENT_CANDIDATE_COMPATIBLE, RATE_ADAPTATION, NEAR_FULL_DISCLOSURE}` 按 `EVIDENCE_INCOMPLETE > MODEL_NOT_STABLE > CURRENT_CANDIDATE_COMPATIBLE(≤16/≤LaneC+8+8) > RATE_ADAPTATION > NEAR_FULL_DISCLOSURE(≥1024或≈10240)` 已判定，`CURRENT_CANDIDATE_COMPATIBLE` 需 `m1_raw≤16 && m2_raw≤LaneC_base+16 (184→200,190→206,192→208)`，`NEAR_FULL_DISCLOSURE` 需 `m1_raw≥1024 || m2_raw≥1024 || raw_disclosure≥5120 (≈10240/2)`，`successor` 已显式（`none / rate_adaptation / new_representation / recollect`），不以总体平均。
- [ ] **总体 complete 已验**：`overall = V67_FEASIBILITY_MAP_COMPLETE` 当且仅当全部已注册 `≤9` session 均已得出 `classification`（含 `EVIDENCE_INCOMPLETE` 亦计完成），落盘 `overall_feasibility_map_complete: true`，五态之外无隐藏总体。
- [ ] **四工件 + 地图报告表完整（不读 TEST）**：`v67_data_registry.json` + `v67_spike_summary.json` + `v67_feasibility_table.csv/.json`（表含 `session/CE/lambda/gap/unseen/m/raw/classification/successor` 且与 json 一致）+ `V67_FEASIBILITY_REPORT.md` 已齐，`session/CE/λ/gap/unseen/m/raw/classification/successor` 每列已回填无 b9f29173，`Stage0/Stage1/Stage2` 双组 `CE/m/raw` 已披露。
- [ ] `scripts/v67_spike.py` 为 decoder-free 可运行脚本（`rg "decode_" 0 hits`、`rg "import.*decoder" 0 hits`、`rg -i "v68|gray" 0 hits`，仅 `numpy/pandas/pyarrow`，`py_compile` PASS，`pytest -p no:cacheprovider -q` 小测试 PASS），输出 `registry + summary + table + report` + 控制台摘要，**未创建 run_01，未读 TEST 统计，λ 触界不扩搜索，m_raw 不 cap，acquisition 去重已验**。
- [ ] 已停留在 `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`，未创建任何 `.../v67_*/run_01`（`ls` 不存在已验），不比较，不碰 `V48-V66` 块外，未转 qualification，**四工件+registry+spike+报告表已单独提交推送，返回新 Plan SHA + 候选列表（≤9 session ids）+ 各分流计数**，等待独立审核（`Pre-RESULT` 独立线程复核 `HEAD/ACCEPTED_PLAN_SHA/rg 0 hits/run_01不存在/py_compile/TEST 未读/m_raw 显式/五分流/≤9 每类≤3/acquisition 去重/U 5+5不GE/V68隔离`）。

## Tasks

见 `tasks.md`（Phase A acquisition 去重预注册 ≤9 每类≤3；Phase B 冻结主体 U=32*U1+U2 5+5 不GE；Phase C Stage0 8frames 物化；Phase D Stage1 CAL256 VAL128 分类；Phase E Stage2 CAL1024 VAL256 confirmation 不重叠重新独立估计 TEST不读；Phase F 码率 raw 不 cap + 五分流 + 总体 complete；Phase G 四工件 + spike + 注册表 + 报告表；Phase H 守卫 R67-01~10 + 单独提交推送新 Plan SHA）。

## Lifecycle

`V64` 已 `22/24 full-tag PASS`；`V65` new-session `4096/512/120` 为跨 session 对照；`V66` 单 session 单源 `24+24+24=72` 自适应 `RATE_NOT_FEASIBLE`；`V67-MAP` 为**多 session (≤9) 可行域地图** decoder-free 预冻结，当前 `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`（仅 decoder-free 地图，acquisition 去重 ≤9 每类≤3 机械，Stage0 8 → Stage1 256/128 → Stage2 1024/256 不重叠重估，TEST隔离，U 5+5 不GE，m_raw 不 cap，五分流，总体 `V67_FEASIBILITY_MAP_COMPLETE`）；`V67` 本身不直接进入 qualification；任何 decoder / V68 新表示需另起 `EXECUTE_AUTH`。
