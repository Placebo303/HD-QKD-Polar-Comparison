# OpenSpec Tasks: formal-ir-v67-multisession-feasibility-map — 多 session 可行域地图 (PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED)

**Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — **acquisition 去重预注册 ≤9（每类≤3 机械不按 CE 替换），Stage0 8frames 物化 → Stage1 CAL256 VAL128 分类 → Stage2 CAL1024 VAL256 confirmation 不重叠重新独立估计 TEST不读，冻结 U=32*U1+U2 5+5 不GE V68表示，码率 m1_raw=ceil(1.3*1024*CE1/5) m2_raw同 raw_disclosure不cap，五分流 EVIDENCE_INCOMPLETE/MODEL_NOT_STABLE/CURRENT_CANDIDATE_COMPATIBLE(≤16/≤LaneC+8+8)/RATE_ADAPTATION/NEAR_FULL_DISCLOSURE(≥1024或≈10240) 总体 V67_FEASIBILITY_MAP_COMPLETE，四工件 registry+spike.py+report+表(含 session/CE/lambda/gap/unseen/m/raw/classification/successor)，守卫 R67-01~10 不创run_01 rg decoder 0 py_compile 小测试，禁止调V68码**

**HEAD**: `520b51c46e6b427f19225f69dc87602d6f0cbfb5` + data `84d62779`

**Predecessor**: `formal-ir-v66-single-segment-adaptive-nbldpc` `832e5394` + `formal-ir-v64` `22/24 PASS` → `V67-MAP`

**Method frozen**: `n1024 q1024 GF32 poly37 H1 16×1024 rank16 80b U=32*U1+U2 F03 5+5 natural (不GE) Lane C ordinal-2 s38310x m2 184/190/192 per source H_inc Δ8 家族 decoder 90/1.0 full-tag canonical 32*U1+U2 leak 5*(m1+m2)+64` 零改；处理点 `84d62779` 单点；多 session ≤9

**Boundary**: acquisition 去重 ≤9 每类≤3 机械不按 CE 替换；Stage0 8 物化；Stage1 CAL256 VAL128 分类；Stage2 CAL1024 VAL256 不重叠重新独立估计 TEST不读；U 5+5 不GE；m_raw ceil 不 cap；五分流优先级 `EVIDENCE_INCOMPLETE > MODEL_NOT_STABLE > CURRENT_CANDIDATE_COMPATIBLE(≤16/≤LaneC+8+8) > RATE_ADAPTATION > NEAR_FULL_DISCLOSURE(≥1024或≈10240)`；总体 `V67_FEASIBILITY_MAP_COMPLETE`；DECODER_FREE 四工件已验后推送新 SHA

## Phase A — acquisition 去重预注册 ≤9（每类≤3 机械，不按 CE 替换）

- [x] **A1 枚举与 acquisition 去重（机械）**：扫描 `v55_intake_20260828/pairs/*`（或 `PROJECT_DATA_ROOT` 预留新 session 根，不硬编码 `D:\`）枚举 `pairs.parquet` 目录 → 提取 `session_id` 与 `acquisition_id`（`ttbin` 头 `acquisition_counter` 或 `session_id` 中 `acquisition` 段，缺失则 `session_id` 自身）→ 按 `(source_label, acquisition_id)` 去重（同 acquisition 多份导出仅首份保留），落盘 `v67_acquisition_inventory.json` 含 `acquisition_dedup_key + provenance + acquisition_time`。
- [x] **A2 每类≤3 机械预注册（不按 CE 替换）**：按 `source_label ∈ {1M,1p5M,2M}`（由 `session_id` 前缀 `type2_XM` 或 `channel_counts.npz` provenance）分桶 → 每桶按 `acquisition_time`（`session_id` 时间戳 `20260121_184040`）升序排序 → 取前 3（`≤3`），**禁止按 `CE/m` 排序替换**，落盘 `v67_data_registry.json:sessions[≤9]`（`total≤9`，`per_category≤3`，`acquisition_dedup_verified:true`，`frozen:true`，`not_sorted_by_CE:true`），超 9 截断至 9；`total<3` 则 `EVIDENCE_INCOMPLETE` 子类 `map_sparse_insufficient`。
- [x] **A3 零重叠与 TEST 隔离预冻结**：对每已注册 session 预分配 `Stage0 8 / Stage1 CAL256 VAL128 / Stage2 CAL1024 VAL256` 的 `frame_id` 区间（连续，不重叠，键 `(source,session,frame)`），校验 `Stage0∩Stage1==∅ && Stage1∩Stage2==∅` 且 `Stage0∪Stage1∪Stage2 ∩ (V13..V66)_key ==∅`（来自 `v55_stratified_registry_candidate.json + v64_fresh_registry.json + v66_data_registry.json`），`TEST` 不分配且脚本内 `used_test==False` 已验。

## Phase B — 冻结主体 U=32*U1+U2 5+5 不GE（decoder-free，不引 V68）

- [x] **B1 主体明文化（逐项显式，冻结零改）**：写入 `v67_manifest.json:frozen_body {n1024, q1024, GF32 poly37, H1 16×1024 rank16, U=32*U1+U2 F03 5+5 natural 不GE, U1>>5/U2&31 per frame 256, Lane C ordinal-2 s38310x m2 184/190/192 per source, H_inc Δ8 family, decoder 90/1.0 poly37 early-stop (禁用), full-tag canonical 32*U1+U2, leak=5*(m1+m2)+64, materialization legacy_v1}`，显式 `not Gray/not V68 2+8/4+6/6+4/not MET/protograph/SC`，`git diff -- src/ ==0` 已验。
- [x] **B2 权威算法只读复用**：直接复用 `src.reconciliation.run_nbldpc_demo_point` 的 `legacy_v1` 物化算法不重写；`Stage0/S1/S2` 均按该链物化后 `frame_id=row//256` 切片，禁直接按 `pairs.parquet` 猜帧；`U mapping` 每帧校验 `A==32U1+U2 && B==32V1+V2`。
- [x] **B3 不GE 隔离校验**：`rg -i "gray|v68|G_ray" scripts/v67_spike.py 0 hits` 且 `rg "import.*v68" 0 hits`，`U` 每帧 `5+5` 自然已验，不引入 `Gray/2+8/4+6` 分解；脚注 `ponytail:` 标明若需 V68 另起 OpenSpec。

## Phase C — Stage0 8 frames 物化校验（per session）

- [x] **C1 每 session Stage0 8 frames 物化校验**：每已注册 session 取前 8 frames（`8*256=2048 pairs`）按 `84d62779 legacy_v1` 物化（`dimension 1024, bin200, nearest, channels A1/B5, period 204800, threshold 40000, gate 200`）→ 校验 `materialization_contract_consistent && frame 256 && alice/bob ∈[0,1023] && U1>>5 &31`，落盘 `stage0_materialization_ok`；失败则该 session `classification=EVIDENCE_INCOMPLETE` 且不进入 Stage1。
- [x] **C2 provenance 记录**：`v67_data_registry.json:per_session {provenance: {pairs_path, session_id, acquisition_id, frames_total, stage0_frame_ids[8], source_label}}` 已验，不跨 acquisition 拼接。

## Phase D — Stage1 CAL256 VAL128 分类（per session，不重叠，TEST不读）

- [x] **D1 读 S1 CAL256 切片（256 frames 65536 pairs per session）**：按 `Stage1_CAL[256]` 切 `alice_symbol/bob_symbol` 65536 rows，`F03 U1=>>5, U2=&31` 分解，校验每帧 256。
- [x] **D2 算 S1 C_ab/P_global/P(U1|B)/P(U2|U1,B) λ 择优（仅 CAL 内 4-fold，不扩网格）**：`C_ab = bincount2d(a_cal,b_cal) 1024×1024 int32 sum 65536` → `N_b, P_global(a)=Σ_b C_ab/N_cal` → 构造 `P(a|b)=(C_ab+λ P_global)/(N_b+λ)`（`N_b==0→P_global`），`λ ∈[1e-2,1e4] log10 连续` 按 `CAL 内 4-fold`（每 fold 64 frames 16384 pairs）计 `CV NLL` 最小择优，同时生成 `P(U1|B) 32×1024` 与 `P(U2|U1B) 32×32×1024`，落盘 `S1 λ, λ_at_boundary, S1 H_cal, S1 CalCV NLL`。
- [x] **D3 S1 VAL128 CE 链式与 raw m（VAL 门禁，TEST隔离）**：对 `VAL128 (32768 pairs)` 计 `CE_full=-E_VAL log2 P(A|B), CE1=-E_VAL log2 P(U1|B), CE2=-E_VAL log2 P(U2|U1,B)`，校验 `|CE_full-CE1-CE2|<1e-9` 否则 `EVIDENCE_INCOMPLETE`，落盘 `S1 CE1,CE2,CE_full,chain_delta`；随后 `m1_raw=ceil(1.3*1024*CE1/5), m2_raw=ceil(1.3*1024*CE2/5), m_total_raw=m1_raw+m2_raw, raw_disclosure=5*(m1_raw+m2_raw)+64` 显式 **不 cap**，校验 `m_raw` 未 `min(1024, ...)` 截断；落盘 `S1 m1_raw,m2_raw,raw_disclosure, H_cal, ValNLL, ΔNLL, val_b_context_unseen, joint_cell_unseen, q_mass_unseen (descriptive), descriptive_diagnostics×3 (ValNLL>Hcal+1/0.5/joint_cell_unseen>1%), capacity_warning_m1/m2/disclosure (≥1024/≥1024/≥5120 正交), effective_contexts`。
- [x] **D4 S1 初分类（五分流，不以 TEST）**：按 `EVIDENCE_INCOMPLETE > MODEL_NOT_STABLE(λ触边/ΔNLL>0.5/val_b_context_unseen>1%/非有限) > CURRENT_CANDIDATE_COMPATIBLE(≤16/≤LaneC+8+8) > RATE_ADAPTATION > NEAR_FULL_DISCLOSURE(≥1024或≈10240)` 初判 `S1_classification`，落盘 `S1_classification + S1_successor`，`TEST 未读` 已校验 `used_test==False`。

## Phase E — Stage2 CAL1024 VAL256 confirmation 不重叠重新独立估计（per session，TEST不读）

- [x] **E1 零重叠校验（S1∩S2==∅）**：校验 `S1_CAL256+VAL128 的 frame_ids ∩ S2_CAL1024+VAL256 ==∅`（键 `(source,session,frame)`），失败则 `EVIDENCE_INCOMPLETE`。
- [x] **E2 重新独立估计 S2 C_ab/P_global/λ/CE/m_raw（不复用 S1）**：对 `S2 CAL1024 (262144 pairs)` 独立重算 `C_ab 1024×1024 sum 262144 → N_b/P_global → P(a|b) λ(仅新 CAL 内 4-fold 每 fold 256 frames 65536 pairs) → P(U1|B)/P(U2|U1B)`，校验 `S2 λ 独立择优 (not reuse S1 λ)`；对 `S2 VAL256 (65536 pairs)` 计 `CE_full/CE1/CE2` 链式 `|CE_full-CE1-CE2|<1e-9` → `m1_raw2=ceil(1.3*1024*CE1_2/5), m2_raw2=ceil(1.3*1024*CE2_2/5), raw_disclosure2=5*(m1_raw2+m2_raw2)+64` 不 cap；落盘 `S2 λ2, CE1_2/CE2_2/CE_full_2, m1_raw2/m2_raw2, raw_disclosure2, ΔNLL2, val_b_context_unseen2, joint_cell_unseen2, q_mass_unseen2 (descriptive), descriptive_diagnostics2, capacity_warning_m1/m2/disclosure2 正交`。
- [x] **E3 确认分类与 stage 一致性**：按同五分流阈对 `S2 CE/m_raw2` 得 `S2_classification`（`CURRENT_CANDIDATE_COMPATIBLE` 仍 `m1_raw2≤16 && m2_raw2≤LaneC+8+8`），落盘 `S2_classification` 与 `stage_consistency = (S1_classification==S2_classification)`（不一致以 `S2` 为准），`used_test==False` 已验，禁第二 estimator。

## Phase F — 码率 raw 不 cap + 五分流 + 总体 complete（per session + overall）

- [x] **F1 五分流最终 per session（优先级互斥）**：取 `S2_classification`（若 `S2` 不可用则 `S1`）为 `final_classification`，按 `EVIDENCE_INCOMPLETE > MODEL_NOT_STABLE > CURRENT_CANDIDATE_COMPATIBLE(≤16/≤LaneC+8+8) > RATE_ADAPTATION > NEAR_FULL_DISCLOSURE(≥1024或≈10240)` 互斥已验，`m_raw` 不 cap 已验，`raw_disclosure` 显式，`LaneC_base+8+8` 按 `source_label` 映射 `1M 184→200, 1p5M 190→206, 2M 192→208` 已验。
- [x] **F2 successor 建议**：`EVIDENCE_INCOMPLETE → recollect`，`MODEL_NOT_STABLE → recollect_or_new_prior`，`CURRENT_CANDIDATE_COMPATIBLE → none (reuse)`，`RATE_ADAPTATION → v68_rate_adaptive`，`NEAR_FULL_DISCLOSURE → v68_new_representation`，落盘 `successor`。
- [x] **F3 总体 V67_FEASIBILITY_MAP_COMPLETE**：当全部 `≤9` 已注册 session 均已得出 `final_classification`（含 `EVIDENCE_INCOMPLETE` 亦计）则 `overall = V67_FEASIBILITY_MAP_COMPLETE`（`total∈[3,9] && acquisition_dedup_verified`），落盘 `overall_feasibility_map_complete: true` 与 `counts_per_classification {EVIDENCE_INCOMPLETE, MODEL_NOT_STABLE, CURRENT_CANDIDATE_COMPATIBLE, RATE_ADAPTATION, NEAR_FULL_DISCLOSURE}` + `candidate_session_list`（`COMPATIBLE` 的 session_ids）。

## Phase G — 四工件 + 地图报告表交付（PLAN_CANDIDATE / DECODER_FREE）

- [x] **G1 编写 `scripts/v67_spike.py`** (decoder-free, 本变更目录下): `python scripts/v67_spike.py [--pairs-root ...] [--registry v67_data_registry.json] [--out v67_spike_summary.json]` → 每 session `Stage0 8 → S1 CAL256/VAL128 → S2 CAL1024/VAL256 独立重算`，`rg "decode_" 0 hits` `rg -i "v68|gray" 0 hits` 仅 `numpy/pandas/pyarrow + ttbin_pipeline`，`py_compile PASS`，输出 `v67_spike_summary.json + v67_feasibility_table.(csv|json)` + 控制台摘要。
- [x] **G2 执行 decoder-free 地图回填**：运行 `scripts/v67_spike.py` 得每 session 双组 `CE/CE1/CE2/λ/ΔNLL/unseen/m_raw/raw_disclosure` 与 `S1/S2_classification/final_classification/successor/stage_consistency`，落盘 `v67_spike_summary.json` 与 `v67_feasibility_table.csv/.json`（CSV 行对等 JSON）。
- [x] **G3 撰写 `V67_FEASIBILITY_REPORT.md`**：`per session Stage0/Stage1/Stage2 双组 CE/λ/ΔNLL/unseen/m_raw/raw_disclosure/classification/successor/stage_consistency + overall counts + candidate list + map_sparse 标记 + acquisition 去重证明 + TEST隔离 + U 5+5不GE + 五分流阈` 与 `json/csv` 一致，不扩大为 `FER/SKR`，显式 `acquisition_dedup` + `TEST 未读` + `m_raw 不 cap + 五分流`。
- [x] **G4 自检（五态+守卫+R67-01~10）**：`py_compile` spike PASS, `rg "decode_" 0 hits`, `rg -i "v68|gray" 0 hits`, `git diff -- src/ ==0` 且 `git diff -- comparison_bench/src/comparison_bench/formal_ir/ ==0` (未改码), acquisition 去重 `≤9 每类≤3 不按 CE` 已验, `Stage0 8 / S1 256/128 / S2 1024/256` 不重叠重新独立估计已验, `|CE_full-CE1-CE2|<1e-9` 已验, `m_raw ceil` 不 cap `raw_disclosure` 显式已验, `五分流优先级互斥` 已验, `TEST 未读` 已验, `U 5+5不GE` 已验, `overall V67_FEASIBILITY_MAP_COMPLETE` 已验, 报告与 json/csv 一致 **无 1172b8b78b4c712d70a517b4c10565e80b7101e2**, **A-F 已闭合**。
- [x] **G5 小测试**：`pytest -p no:cacheprovider -q` 小测试（`test_v67_spike_small.py`）验证 `ceil_rate / ceil_to_family / hierarchical_P / dedup` 纯函数与 `TEST隔离`，`py_compile` 双 PASS。

## Phase H — 守卫 R67-01~10 + 单独提交推送新 Plan SHA

- [x] **H1 守卫 R67-01~10 落盘验证**：在 `v67_manifest.json:guards {R67-01..R67-10}` 逐项 `true`，见 Design §9 / Spec §10。
  - R67-01 acquisition 去重 ≤9 每类≤3 机械不按 CE 替换
  - R67-02 Stage0 8 frames 物化
  - R67-03 Stage1/Stage2 不重叠 + 历史零重叠
  - R67-04 重新独立估计 + TEST不读
  - R67-05 冻结 U=32*U1+U2 5+5 不GE V68隔离
  - R67-06 码率 raw 不 cap
  - R67-07 链式 + λ 择优
  - R67-08 五分流互斥优先级
  - R67-09 decoder-free + V68隔离
  - R67-10 不创 run_01 + 编译 + 小测试
- [x] **H2 单独提交推送四工件+registry+spike+报告表**：`git add openspec/changes/formal-ir-v67-multisession-feasibility-map/ scripts/v67_spike.py v67_data_registry.json v67_spike_summary.json v67_feasibility_table.csv v67_feasibility_table.json V67_FEASIBILITY_REPORT.md && git commit -m "formal-ir-v67: multisession feasibility map ≤9 acquisition dedup Stage0 8 S1 256/128 S2 1024/256 re-estimate TEST隔离 U 5+5 不GE m_raw 不 cap 五分流" && git push origin formal-ir-mainline`，返回新 `Plan SHA`（40位），记录于 `proposal/design/tasks` HEAD 占位替换，**不创建 run_01**。
- [x] **H3 停留 `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`**，未创建任何 `.../v67_*/run_01`，不比较，不碰 `V48-V66` 块外，未转 qualification，仅改本目录 + `scripts/`，**推送后等待独立审核**（`Pre-RESULT` 独立线程复核 `HEAD/ACCEPTED_PLAN_SHA/rg 0 hits/run_01不存在/py_compile/TEST 未读/m_raw 显式/五分流/≤9 每类≤3/acquisition 去重/U 5+5不GE/V68隔离`），返回 `Plan SHA / 冻结 session 数 / 候选列表（COMPATIBLE session_ids）/ 各分流数 {EVIDENCE/MODEL/COMPATIBLE/RATE_ADAPT/NEAR_FULL}` 等待 `PLAN_ACCEPT`。

## 本变更显式禁止

decoder 调用 (`decode_*` / `construct_*` 等)；读密封 `TEST` 的 `H/CE/NLL/MAP` 统计或将其用于 `P/m/阈值` 选择；在原 `V55 90-block` 或 `V48-V66` 已用 `(source,session,frame)` 上重跑先验估计而不零重叠；调 `H1/Lane C/Δ8/decoder/m2/m_total/leak/prior/H_inc/H_total/verification` 任一冻结参数或新增矩阵；**跨 acquisition 拼接凑 9**；**将 floor/round 当 ceil**；**将 `min(1024, ceil(...))` cap 伪装当通过**（`m_raw` 必须显式）；**将 `+8` 外 degree/seed 网格当自适应**（仅 `Δ8` 家族 `+8` 辅助对照）；**用 `TEST` 择优阈或选平滑**（`P/m` 仅 `CAL/VAL`，TEST 隔离）；**将不足 3 伪判为 complete**（应 `EVIDENCE_INCOMPLETE map_sparse_insufficient`）；**将 `acquisition` 未去重多计 session**（必须 `(source,acquisition_id)` 去重）；**将按 CE 优选替换预注册 session**（必须机械 `acquisition_time` 前 3）；**将 `U` 换 Gray/V68 5+5**（必须 `32*U1+U2` 自然）；**引 MET/protograph/SC**；**改 `src/` 基线**；宣称 LDPC 证伪或 `FER/阈值/SKR/晋升`；创建正式 `.../v67_*/run_01`；任意 `bin_width/dimension/pairing/mapping` 网格或阈网格（处理点单点）；用第二 estimator 作门禁；覆盖已有输出；`V55 90 / V48-V66` 永久禁用違反；**主观“显著恢复”替代五分流硬阈**；**擅自调 V68 码**（仅 `map` 后另起 OpenSpec 才允）；**保留 1172b8b78b4c712d70a517b4c10565e80b7101e2 占位不回填**。

## 验收

- proposal/design/tasks/specs 一致 `b7e3417f→新 Plan SHA` `84d62779` lifecycle `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` 五分流按优先级互斥明确，显式 acquisition 去重 ≤9 每类≤3 机械不按 CE 替换、Stage0 8 → Stage1 256/128 → Stage2 1024/256 不重叠重新独立估计 TEST不读、冻结 `U=32*U1+U2 5+5 不GE`、码率 `m_raw ceil 不 cap raw_disclosure`、总体 `V67_FEASIBILITY_MAP_COMPLETE`，严格复用 V56 materialization 算法，冻结分段/熵-CE 与 m 公式/五分流阈
- acquisition 去重 ≤9 每类≤3 机械，不按 CE 替换，`Stage0 8 / S1 256/128 / S2 1024/256` 不重叠重新独立估计可验（键 `(source,session,frame)`，`S1∩S2==∅ && ∩V13..V66==∅` + `S2 重算` + `TEST 未读`），`U 5+5不GE` 每帧已验，少 3 则 `EVIDENCE_INCOMPLETE` 地图，注册表已落盘（≤9），`TEST 未读` 已验，**新 Plan SHA 已推送**
- 合同 `U=32*U1+U2 / dimension 1024 / bin200 / nearest legacy_v1 / channels/frame anchor/mapping 每帧256` 算法一致已验，偏则 `EVIDENCE_INCOMPLETE` 已验，`V68/Gray` 0 hits 已验
- 每 session `S1/S2 各自 C_ab 1024×1024 → P(U1|B)/P(U2|U1B) λ(仅 CAL 内 4-fold) → VAL CE1/CE2/CE_full 链式 |CE_full-CE1-CE2|<1e-9 → m1_raw/m2_raw ceil → raw_disclosure 不 cap` 已重算且 `S2 独立重算` 已验，`m_raw` 未 cap，`m_family +8` 辅助显式，`TEST` 未参与，不扩，禁第二 estimator 已验，`stage_consistency` 已报告
- 每 session `五分流 final_classification + successor` 已落盘，总体 `V67_FEASIBILITY_MAP_COMPLETE` 且 `counts_per_classification` 已统计，`candidate_session_list` 已显式
- `Stage0/CE/λ/gap/unseen/m/raw/classification/successor/capacity_warning_m1/m2/disclosure/descriptive_diagnostics` 已回填，`报告表 CSV行对等 JSON` 已验，`overall complete` 已验
- 守卫 `R67-01~10` 已验（acquisition/Stage0/零重叠/重估/TEST隔离/U 5+5不GE/m_raw不cap/链式λ/五分流/decoder-free/V68隔离/不创 run_01/py_compile/小测试）
- 双脚本 `rg "decode_" 0 hits` `rg -i "v68|gray" 0 hits` `py_compile` PASS `pytest 小测试` PASS `m_raw` 未 cap `TEST 未读` `acquisition 去重` 已验 `capacity_warning_m1/m2/disclosure` 正交与 `descriptive_diagnostics` 已落盘 报告与 json/csv 一致 未建 `run_01` 已停留 `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` 仅改本目录 + `scripts/`（`src/` 零改），未启动 decoder/V68，**四工件+registry+spike+报告表已单独提交推送，新 Plan SHA + 候选列表 + 各分流数已返回**，推送后等待独立审核
