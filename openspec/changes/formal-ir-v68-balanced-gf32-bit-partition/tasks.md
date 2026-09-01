# OpenSpec Tasks: formal-ir-v68-balanced-gf32-bit-partition — GF32均衡 bit-partition 地图 (PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED)

**Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — **1024维符号 GF32两层验证冻结仅重划分10 bits，枚举252子集按升序唯一词典序 max→sum→abs→lex 选 S*，Phase A CAL-only 选 S* Phase B VAL确认报告 natural 参照，session 复用 V67 三预注册 Stage2，per-session 4分流 + 总体3态 + common审计，四工件 spike/results/table/report+test，守卫 R68-01~10，不跑decoder不构矩阵**

**HEAD**: `d6f590ac6f30deaa8b0bf6cf5c419593fc037720` + data `84d62779` (复用 V67 清理后 HEAD)

**Predecessor**: `formal-ir-v67-multisession-feasibility-map` `d6f590ac6f30deaa8b0bf6cf5c419593fc037720` `V67_FEASIBILITY_MAP_ACCEPTED` (3 sessions 均 `NEAR_FULL` natural 5+5) → `V68-BAL`

**Method frozen**: `n1024 q1024 GF32 poly37 H1 16×1024 rank16 80b U=32*U1+U2 F03 5+5 natural (仅新增 S 重标记) Lane C ordinal-2 s38310x m2 184/190/192 H_inc Δ8 decoder 90/1.0 full-tag canonical 32*U1+U2 leak 5*(m1+m2)+64` 零改；处理点 `84d62779` 单点；`S` 252 枚举

**Boundary**: 仅 `S` 重划分，不改主体；`C(10,5)=252` 升序枚举按 `T=(max,sum,abs,S_lex)` 选 `S*`，`Phase A CAL-only` 不读 VAL/TEST，`Phase B VAL` 确认 + natural 参照 `{5,6,7,8,9}`；V67 三 session Stage2 复用 `CAL1024+VAL256` 不重估计；per-session 4分流 `EVIDENCE_INCOMPLETE > MODEL_NOT_STABLE > BALANCED_FEASIBLE(m1<1024&&m2<1024&&raw<5120) > STILL_HEAVY` + 总体3态 `BALANCED_COMMON_FEASIBLE / BALANCED_PER_SESSION_ONLY / STILL_HEAVY` + common 审计 `S*_per_session + S*_common`；DECODER_FREE 四工件已验后推送新 SHA，不构矩阵不跑 decoder

## Phase A — 注册表复用与枚举前置（V67 Stage2 复用，不重估计）

- [x] **A1 复用 `v67_data_registry.json` 的 Stage2 帧集（机械，不按 CE 替换）**：读取 `openspec/changes/formal-ir-v67-multisession-feasibility-map/v67_data_registry.json` 的 `sessions[3]`（`20260123_1M_600k_0dB 1M / 20260107_PPLN_1p5M 1p5M / 20260123_2M_1p2M_0dB 2M`）的 `stage2_CAL_frame_ids[1024] (262144 pairs) + stage2_VAL_frame_ids[256] (65536 pairs)` 原样拷贝至 `v68_data_registry.json`（`schema v68_data_v1, lifecycle PLAN_CANDIDATE, head d6f590ac6f30deaa8b0bf6cf5c419593fc037720, data_sha 84d62779, reused_from v67, sessions[3], per_session {session_id, acquisition_id, source_label, provenance, stage2_CAL[1024], stage2_VAL[256], zero_overlap_verified, acquisition_dedup_verified, frozen, not_sorted_by_CE}`），校验 `total 3 && per_category 1,1,1 && acquisition_dedup_verified && zero_overlap_verified && Stage2_key ∩ (V13..V67)_key ==∅` 键 `(source,session,frame)`，禁止事后换 session。
- [x] **A2 枚举 252 子集升序生成（ponytail: itertools.combinations）**：`S_list = list(itertools.combinations(range(10),5))` 升序 252 行，校验 `len==252 && S_list[0]==(0,1,2,3,4) && S_list[-1]==(5,6,7,8,9)` 且 `C(10,5)==252`，`S_nat=(5,6,7,8,9)` 恒包含，落盘 `v68_manifest.json:enum {count 252, S_nat index, generation lex order}`。
- [x] **A3 冻结 U 重标记函数（纯比特置换，不改 s）**：实现 `bits_S(s, S) -> (u1', u2')` 其中 `u1' = Σ_{k=0..4} ((s>>S[k])&1)<<k`, `u2' = Σ_{k=0..4} ((s>>T[k])&1)<<k` with `T = sorted(B\S)`, 每帧校验 `natural S_nat 时 bits_S(s)==s>>5 && bits_T(s)==s&31`，`rg "gray|met|protograph" 0 hits`（除注释），`src/` 零改。

## Phase B — 冻结主体 1024维 GF32两层验证仅重划分（decoder-free，不构矩阵）

- [x] **B1 主体明文化（逐项显式，冻结零改）**：写入 `v68_manifest.json:frozen_body {n1024, q1024, GF32 poly37, H1 16×1024 rank16, U_natural 32*U1+U2 F03 5+5, U_permuted bits_S(S) 252种仅重标记, per_frame 256, Lane C 184/190/192, H_inc Δ8, decoder 90/1.0 poly37 disabled, full-tag canonical, leak 5*(m1+m2)+64, materialization legacy_v1}`，显式 `not Gray/not MET/protograph/SC/not H construction`，`git diff -- src/ ==0` 已验。
- [x] **B2 权威算法只读复用**：直接复用 `src.reconciliation.run_nbldpc_demo_point` 的 `legacy_v1` 物化算法不重写；`Stage2 CAL/VAL` 均按该链物化后 `frame_id=row//256` 切片，`U` 重标记仅在 `a_cal/b_cal` 的 `s` 上比特置换，不改 `pairs.parquet` 帧边界。
- [x] **B3 不构矩阵守卫**：`rg "decode_|construct_|gf_rank|nested" scripts/v68_spike.py 0 hits` 且不调用任何 `H` 构造、`rank`、`nested` 函数，`py_compile` 校验；脚注 `ponytail:` 标明 ceiling（若需后续码构造，需另起 OpenSpec）。

## Phase C — Phase A CAL-only 选 S*（252枚举 × CAL 4-fold，不读 VAL/TEST）

- [x] **C1 每 session CAL1024 上 252×(C_ab/P/λ) 估计（CAL-only）**：按 `CAL1024 (262144 pairs)` 对每 `S` 算 `C_ab 1024×1024 int32 sum 262144 → N_b/P_global → P(a|b)=(C_ab+λ P_global)/(N_b+λ)`，`λ∈[1e-2,1e4] log10` 仅 `CAL 内 4-fold`（每 fold 256 frames 65536 pairs）最小 `CV NLL` 择优，生成 `P(U1'|B) 32×1024` 与 `P(U2'|U1'B) 32×32×1024`，落盘 `per_S CAL {λ, λ_at_boundary, H_cal_cv, CV_NLL, effective_contexts}`，校验 `used_val_in_selection==False && used_test==False`，`S=252` 行每 session。
- [x] **C2 CAL-heldout CE→m_cv 排序键（升序唯一词典序）**：对每 `S` 以 `CAL` 的 held-out 折均值计 `CE1_cv=-E_{heldout} log P(U1'|B), CE2_cv=-E log P(U2'|U1',B)` → `m1_cv=ceil(1.3*1024*CE1_cv/5), m2_cv=ceil(1.3*1024*CE2_cv/5)`，`T(S)=(max(m1_cv,m2_cv), m1_cv+m2_cv, abs(m1_cv-m2_cv), S_lex)`，`S_lex=tuple(S)` 字典序，按 `T` 升序选 `S*_per_session(CAL)`，`S*_common(CAL)` 按 `T_common(S)=(max_{sess} max, max_{sess} sum, max_{sess} abs, S_lex)` 升序选，落盘 `S*_per_session[3] + S*_common + T_sorted 252`，校验 `252` 行排序稳定且 `S*` 唯一。
- [x] **C3 Natural 参照 CAL 基线（不参与择优）**：对 `S_nat=(5,6,7,8,9)` 同算法同 CAL 计 `CE1_cv_nat/CE2_cv_nat/m1_cv_nat/m2_cv_nat`，落盘 `S_nat_CAL` 供 Phase B Δ 对照。

## Phase D — Phase B VAL确认 + natural 参照（VAL256 独立度量，不重选 S*）

- [x] **D1 VAL256 上 S* 与 S_nat 双计量（VAL 确认，TEST隔离）**：对 `S*_per_session(CAL)` 与 `S*_common(CAL)` 及 `S_nat` 在 `VAL256 (65536 pairs)` 上以 `P_λ*` 计 `CE_full=-E_VAL log P(A|B), CE1=-E_VAL log P(U1'|B), CE2=-E_VAL log P(U2'|U1',B)`，校验 `|CE_full-CE1-CE2|<1e-9` 否则 `EVIDENCE_INCOMPLETE`，落盘 `VAL {CE1,CE2,CE_full,chain_delta, H_cal, ValNLL, ΔNLL, val_b_context_unseen, joint_cell_unseen, q_mass_unseen (descriptive), descriptive_diagnostics×3, capacity_warning_m1/m2/disclosure, m1_raw, m2_raw, raw_disclosure}` per `S`，`m1_raw=ceil(1.3*1024*CE1/5)` 不 cap，`m2_raw` 同，`raw=5*(m1+m2)+64`。
- [x] **D2 Natural Δ 审计**：落盘 `per_session natural_vs_balanced {ΔCE1=CE1_star-CE1_nat, ΔCE2, Δmax=max_star-max_nat, Δsum, Δabs, Δraw}`，报告 `V67 natural m1_nat 1024–1178 vs balanced m*` 显式对照。
- [x] **D3 一致性字段**：落盘 `cal_val_consistency = (S*_per_session(CAL) == argmin_{S} T_val(S))` 其中 `T_val` 为同 `T` 但用 `VAL` 上 `m_raw` 排序，若不一致以 `CAL` 为准，报告 `cal_val_consistency` 与 `VAL` 上 `S*_val` 备选。

## Phase E — per-session 4分流 + 总体3态 + common审计（优先级互斥）

- [x] **E1 Per-session 4分流（优先级互斥）**：取 `VAL` 上 `S*_per_session(CAL)` 的 `m1_raw_val/m2_raw_val/raw_val` 按 `EVIDENCE_INCOMPLETE(CE_chain/非有限) > MODEL_NOT_STABLE(λ触边/ΔNLL>0.5/val_b>1%/非有限) > BALANCED_FEASIBLE(m1<1024&&m2<1024&&raw<5120) > STILL_HEAVY` 互斥已验，`capacity_warning` 正交，`q_mass/joint/H_cal` 仅描述性，落盘 `classification + successor` per session。
- [x] **E2 总体3态（基于 common S*_common 的 VAL 度量）**：对 `S*_common(CAL)` 在 3 sessions 上的 `VAL` 度量得 `common_feasible_count = #{sess | BALANCED_FEASIBLE}`，`per_session_feasible_count = #{sess | per_session S* BALANCED_FEASIBLE}`，判定 `overall = BALANCED_COMMON_FEASIBLE if common_feasible==3 else BALANCED_PER_SESSION_ONLY if per_session_feasible≥1 else STILL_HEAVY`，落盘 `overall + common_feasible_count + per_session_feasible_count + S*_per_session[3] + S*_common + T_common_sorted`。
- [x] **E3 Common 审计表**：落盘 `audit {S*_per_session, S*_common, T_per_session, T_common, natural_T, common_feasible_count, per_session_feasible_count, cal_val_consistency[3], per_session_classification[3]}`，报告 `common 审计` 章节显式。

## Phase F — 四工件 + 审计报告交付（PLAN_CANDIDATE / DECODER_FREE）

- [x] **F1 编写 `scripts/v68_spike.py`** (decoder-free, 本变更目录下): `python scripts/v68_spike.py [--registry v68_data_registry.json] [--out v68_results.json]` → `CAL1024 252×C_ab/P/λ→m_cv→T→S* → VAL256 S*/S_nat CE/m`，`rg "decode_|construct_|gf_rank|nested" 0 hits` `rg -i "met|protograph" 0 hits` 仅 `numpy/pandas/pyarrow+itertools`，`py_compile PASS`，输出 `v68_results.json + v68_table.(csv|json)` + 控制台摘要。
- [x] **F2 执行 decoder-free 枚举回填**：运行 `scripts/v68_spike.py` 得每 session 252 行 `CE/CE1/CE2/λ/ΔNLL/unseen/m/max/sum/abs` 与 `S*_per_session/S*_common/natural/BALANCED`，落盘 `v68_results.json` 与 `v68_table.csv/.json`（CSV 行对等 `3×252 + 汇总`，含 `capacity_warning` 正交）。
- [x] **F3 撰写 `V68_BALANCED_REPORT.md`**：`per session 252 选优 + S*_per_session + S*_common + natural参照(ΔCE/Δmax/Δsum) + CAL/VAL 双组 CE/λ/ΔNLL/unseen/m/max/sum/abs/classification/successor/cal_val_consistency + overall 3态 + common审计 + map_sparse 标记 + TEST隔离 + 1024维冻结` 与 `json/csv` 一致，不扩大为 `FER/SKR`，显式 `252 枚举 + 词典序唯一 + Phase A CAL-only + Phase B VAL确认`。
- [x] **F4 自检（4分流+3态+守卫+R68-01~10）**：`py_compile` spike PASS, `rg "decode_|construct_|gf_rank|nested" 0 hits`, `rg -i "met|protograph" 0 hits`, `git diff -- src/ ==0` 未改码, V67 Stage2 复用 `3` 已验, `S 252` 枚举已验, `|CE_full-CE1-CE2|<1e-9` 已验, `T max→sum→abs→lex` 唯一已验, `Phase A CAL-only` 已验, `m_raw ceil` 不 cap `raw_disclosure` 显式已验, `4分流优先级互斥` 已验, `overall 3态+common` 已验, `TEST 未读` 已验, `overall` 已验, 报告与 json/csv 一致 **无 TBD**, **A-E 已闭合**。
- [x] **F5 小测试**：`pytest -p no:cacheprovider -q` 小测试（`test_v68_spike_small.py`）验证 `bits_S / permute / T排序唯一性 / CAL-only` 纯函数与 `TEST隔离`，`py_compile` 双 PASS。
  - ponytail: `bits_S` 为 10-bit 纯移位/掩码，不引 `numba`；`T` 排序为 `tuple` 升序最小，`O(252 log 252)` 足够。

## Phase G — 守卫 R68-01~10 + 单独提交推送新 Plan SHA

- [x] **G1 守卫 R68-01~10 落盘验证**：在 `v68_manifest.json:guards {R68-01..R68-10}` 逐项 `true`，见 Design §8 / Spec §10。
  - R68-01 冻结主体 1024维 GF32两层验证不改
  - R68-02 枚举252子集完整
  - R68-03 升序唯一词典序 max→sum→abs→lex
  - R68-04 Phase A CAL-only 选 S*
  - R68-05 Phase B VAL确认+natural参照
  - R68-06 V67三Session Stage2 复用
  - R68-07 per-session 4分流+总体3态+common审计
  - R68-08 四工件+test 完整
  - R68-09 decoder-free不构矩阵
  - R68-10 不创run_01+编译+小测试+TEST隔离
- [ ] **G2 单独提交推送四工件+registry+spike+报告表（V68 provenance deviation — 无独立 plan SHA，不借用 520b51c4）**：`git add openspec/changes/formal-ir-v68-balanced-gf32-bit-partition/ scripts/v68_spike.py v68_data_registry.json v68_results.json v68_table.csv v68_table.json V68_BALANCED_REPORT.md test_v68_spike_small.py && git commit -m "formal-ir-v68: balanced GF32 bit-partition 252 CAL-only max→sum→abs→lex S* VAL confirm V67 Stage2 reuse" && git push origin formal-ir-mainline`，返回新 `Plan SHA`（40位），记录于 `proposal/design/tasks` HEAD 占位替换，**不创建 run_01**。
- [ ] **G3 停留 `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`**，未创建任何 `.../v68_*/run_01`，未构矩阵，不比较，不碰 `V48-V67` 块外，未转 qualification，仅改本目录 + `scripts/`，**推送后等待独立审核**（`Pre-RESULT` 独立线程复核 `HEAD/ACCEPTED_PLAN_SHA/rg 0 hits/run_01不存在/py_compile/TEST 未读/m_raw 显式/252枚举/词典序唯一/4分流+3态/common审计`），返回 `Plan SHA / S*_per_session[3] / S*_common / 各分流计数 / common审计` 等待 `PLAN_ACCEPT`。

## 本变更显式禁止

decoder/矩阵构造 (`decode_*` / `construct_*` / `gf_rank` / `nested` 等)；读密封 `TEST` 的 `H/CE/NLL/MAP` 统计或将其用于 `P/m/S*` 选择；读 `VAL` 参与 `S*` 择优（`S*` 仅 `CAL`）；在原 `V55 90-block` 或 `V48-V67` 已用 `(source,session,frame)` 上重跑先验估计而不零重叠；调 `H1/Lane C/Δ8/decoder/m2/m_total/leak/prior/H_inc/H_total/verification` 任一冻结参数或新增矩阵；**跨 acquisition 拼接凑 3**；**将 floor/round 当 ceil**；**将 `min(1024, ceil(...))` cap 伪装当通过**（`m_raw` 必须显式）；**将 `+8` 外 degree/seed 网格当自适应**；**用 `VAL/TEST` 择优 `S*`**（`S*` 仅 `CAL`）；**将不足 3 伪判为 complete**（应 `EVIDENCE_INCOMPLETE`）；**将 `acquisition` 未去重多计**（必须 V67 复用）；**将 `S` 剪枝至 <252**（必须 252）；**将 `T` 换 `sum→max` 等非 max 主**（必须 `max→sum→abs→lex`）；**将 `S*_common` 按平均而非 worst max**（必须 `max_{sess} max`）；**引 MET/protograph/SC/Gray**（仅 `S` 纯重划分）；**改 `src/` 基线**；宣称 LDPC 证伪或 `FER/阈值/SKR/晋升`；创建正式 `.../v68_*/run_01`；任意 `bin_width/dimension/pairing/mapping` 网格或阈网格（处理点单点）；用第二 estimator 作门禁；覆盖已有输出；`V55 90 / V48-V67` 永久禁用違反；**主观“显著均衡”替代硬阈 `m<1024`**；**擅自调 V68 以外码**（仅 `S` 重划分）；**保留 TBD 占位不回填**。

## 验收

- proposal/design/tasks/specs 一致 `d6f590ac6f30deaa8b0bf6cf5c419593fc037720→新 Plan SHA` `84d62779` lifecycle `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` 4分流+3态按优先级互斥明确，显式 1024维冻结仅重划分10 bits、枚举252升序唯一词典序 `max→sum→abs→lex` 选 `S*`、`Phase A CAL-only` 不读 VAL/TEST `Phase B VAL确认+natural参照`、V67三Session Stage2 复用、per-session 4分流 + 总体3态 + common审计、四工件产出已声明，严格复用 V56 权威算法，冻结分段/熵-CE 与 m 公式/分流阈
- 1024维冻结仅重划分已验，`S 252` 枚举升序唯一词典序 `T max→sum→abs→lex` 已验，`Phase A CAL-only` 不读 VAL/TEST 且 `S*` 以 `CAL m_cv` 选已验，`Phase B VAL` 上 `S*/S_nat` 双计 `CE/m` 链式 `|CE_full-CE1-CE2|<1e-9` 已验，`m_raw ceil` 不 cap，`TEST` 未读已验，3 sessions 复用已验，**新 Plan SHA 已推送**
- 合同 `dimension 1024 / bin200 / nearest legacy_v1 / channels/frame anchor/mapping 每帧256` 算法一致已验，`U` 重标记 `bits_S` 每帧已验，偏则 `EVIDENCE_INCOMPLETE` 已验，`252` 已验
- 每 session `CAL 252×C_ab → P(U1'|B)/P(U2'|U1'B) λ(CAL 4-fold) → VAL CE1/CE2/CE_full 链式 → m1_raw/m2_raw ceil → T max→sum→abs→lex 选 S*` 已算且 `CAL-only` 已验，`VAL` 上 `S*/S_nat` 双计 `m_raw/raw` 且 `natural Δ` 已报告，不扩，禁第二 estimator 已验，`cal_val_consistency` 已报告
- 每 session `4分流 final_classification + successor` 已落盘，`overall 3态 + common审计 S*_per_session/S*_common/common_feasible_count` 已统计
- `252行/ S*/ S_nat / CAL/VAL 双组 CE/λ/ΔNLL/unseen/m/max/sum/abs/classification/successor/capacity_warning/descriptive` 已回填，`报告表 CSV行对等 JSON` 已验，`overall 3态` 已验
- 守卫 `R68-01~10` 已验（252枚举/唯一词典序/CAL-only/VAL确认+natural/V67复用/4分流+3态+common/四工件+test/decoder-free不构矩阵/不创run_01/py_compile/小测试+TEST隔离）
- 双脚本 `rg "decode_|construct_|gf_rank|nested" 0 hits` `rg -i "met|protograph" 0 hits` `py_compile` PASS `pytest 小测试` PASS `m_raw` 未 cap `VAL 未参与选优` `TEST 未读` `252 枚举` 已验 `capacity_warning` 正交与 `descriptive` 已落盘 报告与 json/csv 一致 未建 `run_01` 已停留 `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` 仅改本目录 + `scripts/`（`src/` 零改），未启动 decoder/矩阵，**四工件+registry+spike+报告表已单独提交推送，新 Plan SHA + S*_per_session + S*_common + 各分流数 + common审计已返回**，推送后等待独立审核
