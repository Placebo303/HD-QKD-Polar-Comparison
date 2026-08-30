# OpenSpec Tasks: formal-ir-v65-new-session-channel-compatibility — V65 新 session 通道兼容性预冻结（PLAN_CANDIDATE / DECODER_FREE）

**Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — **decoder-free 新 session 兼容性验证，不调码、不运行 decoder、不读 TEST 统计，三源独立 G1-8 全过才允 V66；不足两 session → DATA_NOT_READY**
**HEAD**: `TBD` → 新 Plan SHA (branch `formal-ir-mainline`, 实施前 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline` 重核) + data SHA `84d62779` (200ps legacy_v1 nearest 1024)
**Predecessor**: `formal-ir-v64-full-symbol-verification-correction` `V64` `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` (full-tag 24-block 收缩) + `V57 channel recharacterization` 欠采样教训 (hierarchical λ 预注册)
**Method frozen**: `H1-16/Lane C m2 184/190/192(冻结容量)/H_inc1/2 Δ8+Δ8/decoder 90/1.0 poly37/full-tag canonical 32*U1+U2 单64b / H_total 200/206/208` 零改直至 V66；处理点 `d1024 bw200 nearest legacy_v1 channels A1/B5 200ps` 单点
**Boundary**: `V55 90-block` 与 `V13/V48-V64 已用 frames` 永久禁用零重叠；新 `CAL 4096 + VAL 512` 同 `CAL_SESSION`、`TEST 120` 独立 `TEST_SESSION` 两会话隔离，不跨 session 拼接，少两 session → `V65_DATA_NOT_READY`；`TEST` 仅 identity 不读统计；`λ [1e-2,1e4] 触界→MODEL_NOT_STABLE` 不扩网格；`m_i ceil(1.3*1024*H_i/5) 不 cap` 超则 `RATE_INCOMPATIBLE`；五态优先级 `EVIDENCE_INVALID > DATA_NOT_READY > MODEL_NOT_STABLE > RATE_INCOMPATIBLE > READY_FOR_V66`

## Phase A — 数据就绪预注册与零重叠校验（decoder-free，可机械校验，两会话）

- [ ] **A1 定义 CAL/VAL/TEST 帧（每源独立，新 session 两会话，显式冻结）**：每源 `CAL = CAL_SESSION[0:4096]` + `VAL = CAL_SESSION 后 512 与 CAL 零重叠` (如 `available_CAL[0:4096]` + `available_CAL[4096:4608]` 或确定性分散但同 session 内) + `TEST = TEST_SESSION[0:120]`，`F_s 取决于新 session 原始导出 pairs.parquet F`，`pairs_per_frame 256`, `CAL 1048576 pairs, VAL 131072, TEST 30720`, `blocks CAL 1024 / VAL 128 / TEST 30`，`frame_id∈[0,F_s-1]`，三源独立但算法确定性，可复现，写入 `v65_data_registry.json` (`per_source {CAL_session {id, F, selected_frame_ids[4096]}, VAL_session {id==CAL_session_id, VAL_frames[512]}, TEST_session {id, F, TEST_frames[120]}, blocks, pairs, provenance:{materialization_rule legacy_v1, session_gap, produced_at}, session_count, insufficient_marker}`)，`overall_zero_overlap_verified` 初始 `false`，`TEST` 仅 identity 预留
- [ ] **A2 零重叠与会话隔离机械校验（硬门，多重）**：脚本启动即 `assert set(CAL)∩set(VAL)==∅` per source, `assert set(CAL∪VAL)∩set(TEST)==∅`, `assert set(CAL∪VAL∪TEST)∩set(V13∪V48..V64)==∅` (exact frame_ids 来自 `v55_authoritative_registry.json + v64_fresh_registry.json + V13 sidecars`), `assert CAL_SESSION_id == VAL_SESSION_id && CAL_SESSION_id != TEST_SESSION_id` per source, `assert not is_cross_session_spliced` (single session provenance, 禁单 session 内跨 gap 硬拼 4096+120), `assert |CAL|==4096 && |VAL|==512 && |TEST|==120 && all(0<=fid<F_s)`，落盘 `v65_manifest.json: zero_overlap_proofs {cal∩val, cal∪val∩test, ∩v13v48v64, session_isolation} 全 true`，失败则 `V65_EVIDENCE_INVALID`（若属拼接）或 `V65_DATA_NOT_READY`（若属可用 session<2/帧不足）零估计
- [ ] **A3 session 数判定与 DATA_NOT_READY 门（硬优先级 2）**：枚举 `available_new_sessions = distinct(session_id where source==s && not in V13..V64)` (扫描 `PROJECT_DATA_ROOT` 新 session 导出目录)，若 `len<2` per source 则 `overall = V65_DATA_NOT_READY` 并写 `v65_data_readiness.json {per_source {available_sessions, required 2, status DATA_NOT_READY}, overall DATA_NOT_READY}` 后零估计停止，不伪造，不以旧 `pairs.parquet` 代理；若 `≥2` 则进入 B-H
- [ ] **A4 注册表落盘与帧 256 校验**：`v65_data_registry.json + v65_manifest.json` 含 `schema v65_data_v1, lifecycle PLAN_CANDIDATE, data_sha 84d62779, head TBD→新SHA, materialization_rule 200ps legacy_v1 nearest, provenance_note, created_at, command, zero_overlap_verified`；对每源 `CAL/VAL/TEST` 各帧校验 `pairs_per_frame 256` 且 `alice/bob ∈[0,1023]` 且 `F03 U1>>5 &31` 可分解，失敗則 `EVIDENCE_INVALID`；`TEST` 仅 identity 不计统计已校验 `used_test_in_estimation==False`

## Phase B — 输入合同严格复用 V56（decoder-free，strict，三源分别）

- [ ] **B1 合同明文化（逐项显式，三源分别 provenance）**：写入 `v65_manifest.json:materialization_contract {dimension 1024, bin_width 200ps, pairing nearest double-pointer bin//1024, rule legacy_v1, channels A1/B5, delay_used_ps per source, peak_center/sigma 50-150ps/p2bg/gate 200ps/threshold 40000ps/frame_start_ps/period 204800 floor_div, mapping legacy_v1, frame_len 256 A=32U1+U2 B=32V1+V2}`，三源分别 `per_source_contract {session_id, delay_used_ps, peak_center, sigma, gate, threshold, anchor, mapping, provenance_path}`，与 V56 `sidecar/build_manifest` 实测逐项一致可对照
- [ ] **B2 权威链只读复用（strict V56）**：直接复用 `src.reconciliation.run_nbldpc_demo_point._read_ttbin_timetags/_bin_indices_sorted_for_binwidth/_pairs_from_sorted_bins` 后的 `legacy_v1` symbol 物化，不重写近似版；`CAL/VAL/TEST` 三集合均按该链物化后 `frame_id=row//256, pair_idx=row%256` 切片，禁直接按 `pairs.parquet` 猜帧；`V13` 溯源失败则 `AUTHORITY_LINEAGE_INCOMPLETE → EVIDENCE_INVALID`
- [ ] **B3 帧级 256 映射校验（硬门 G1 前置）**：每帧输出 `alice[256], bob[256]` 各 `256 pairs` 四帧一块 `BLOCK 1024`，校验 `A==32U1+U2 && B==32V1+V2` 且 `U1,V1,U2,V2∈[0,31]` 且 `BLOCK 4 连续帧`，失败则 `EVIDENCE_INVALID`；`G1 authority 一致` 为此阶段全面项一致 `np.array_equal 逐项` else `G1 FAIL`

## Phase C — 单一 hierarchical 估计与 λ 搜索（decoder-free，预注册，不扩网格，禁第二 estimator）

- [ ] **C1 读 CAL 切片（4096 frames）**：`--new-session-root` 的 `alice_symbol/bob_symbol` 按 `CAL 4096` 切 `1048576 rows/源`，`F03 5+5 natural U1=>>5, U2=&31` 分解，校验 `alice/bob ∈[0,1023]` 且每帧 256 连续
- [ ] **C2 算 C_ab/P_global/Hierarchical**：每源 `C_ab = bincount2d(a_cal,b_cal) 1024×1024 int32 sum 1048576` → `N_b, P(b), P_global(a)=Σ_b C_ab/N_cal` → 对候选 `λ` 构造 `P_λ(a|b)=(C_ab+λ P_global)/(N_b+λ)`（`N_b==0 → P_global`），同时生成 `P_λ(U1|B) 32×1024` 与 `P_λ(U2|U1B)` 扁平表，落盘 `per_source {C_shape, N_cal, effective_contexts, P_global_entropy}`
- [ ] **C3 λ 4-fold CV 连续搜索（预注册 [1e-2,1e4] log10[-2,4]）**：`CAL 4096 切 4 folds 各1024 frames/262144 pairs`，对 `log10 λ ∈ [-2,4]` 连续优化目标 `Cal-CV NLL(λ)=mean_k mean_{fold_k}[-log2 P_λ^{(train)}(a|b)]`，`chosen λ* = argmin` via bounded scalar minimisation (grid 50 log + Brent refine)，记录 `search_trace {logλ_grid, CV_NLL_grid, λ*, CV_NLL*}`，校验 `λ ∈ (1e-2,1e4)` 开区间 else `λ_at_boundary=True → G2 FAIL`，**触界不扩网格**，不以 `VAL` 择优，单 hierarchical 一路为门禁，禁第二 estimator (`rg "Laplace|alpha" 0 hits` 为第二 estimator)
- [ ] **C4 熵与链式分解（Cal, λ*）**：`H_cal(A|B;λ*)=-Σ_b P_emp(b)Σ_a P_λ* log2`, `H_cal(U1|B)`, `H_cal(U2|U1B)=H-H1`，校验 `|H-H1-H2|<1e-9` else `EVIDENCE_INVALID`，落盘 `per_source {H, H1, H2, chain_delta, CV_NLL*, λ*, at_boundary}`

## Phase D — 泄漏预算与每源报告（decoder-free，m_i 不 cap 伪装，TEST 仅 identity）

- [ ] **D1 泄漏重算（source-adaptive，m_i ceil 不 cap）**：`f_target=1.3, n=1024, tag=64, log2q=5, H1=H(U1|B), H2=H(U2|U1B)` → `m1_raw = ceil(1.3*1024*H1/5)`, `m2_raw = ceil(1.3*1024*H2/5)`, `m_total=m1_raw+m2_raw`, `leak=5*m_total+64`, `f_eff=leak/(1024*H)` (含 tag)，显式报告 `m_raw` 不经 `min(16, ...)`/`min(1024,...)` 截断；若 `m1_raw>16` 或 `m2_raw>200/206/208` 则 `G6/G7 FAIL`（`RATE_INCOMPATIBLE`），**禁止 cap 伪装**（`git grep "min(16" 0 hits` 为 cap 伪装检查项）
- [ ] **D2 VAL 泛化统计（Cal λ* 下独立测）**：对 `VAL 512 frames 131072 pairs` 以 `P_λ*` 计 `Val NLL = mean_Val[-log2 P_λ*(a|b)]`, `ΔNLL=Val-CV`, `H_val` (同 λ* 熵), `MAP_acc_val=mean_Val[a==argmax P_λ*]`, `q_mass_unseen= Σ_{b∉Cal_support} P_val(b)`, `effective_contexts_cal`, `zero_cells_cal`，落盘 `per_source {Val NLL, ΔNLL, H_val, MAP, unseen, effective}`，`TEST` 不计任何统计已校验 `used_test_in_estimation==False`
- [ ] **D3 每源完整报告（不读 TEST 统计）**：已按 proposal §4 模板逐源汇总 `Cal/Val pairs/frames, λ 是否触界, H(U1|B)/H(U2|U1B)/H(A|B), CV NLL/Val NLL/ΔNLL, MAP, q_mass_unseen, effective_contexts, m1_raw/m2_raw/m_total 相对冻结容量 16/200/206/208 差额 Δm/Δleak`，`TEST` 仅附录 `session_id/frames[120]/blocks 30` identity，不含统计

## Phase E — 门禁 G1-8 独立校验（decoder-free，三源分别，预注册阈）

- [ ] **E1 G1 authority 一致**：`G1_s = (dimension==1024 && bin==200 && pairing==nearest && rule==legacy_v1 && channels⊇{1,5} && delay_used_ps==V56 && |peak-delay|<50 && sigma∈[50,150] && gate==200 && threshold==40000 && period==204800 && 每帧256 A/B映射)` per source，三源分别，已验
- [ ] **E2 G2 λ 不触界**：`G2_s = (log10 λ* ∈ (-2,4) 开区间 && not at_boundary)` per source
- [ ] **E3 G3 ΔNLL≤0.5**：`G3_s = (ΔNLL≤0.50)` bits/symbol per source
- [ ] **E4 G4 Val NLL ≤ H_cal+1.0**：`G4_s = (isfinite(Val NLL) && Val NLL ≤ H_cal+1.0)` per source
- [ ] **E5 G5 unseen ≤1%**：`G5_s = (q_mass_unseen ≤0.01)` per source
- [ ] **E6 G6 m1≤16**：`G6_s = (m1_raw≤16)` per source (raw 未 cap)
- [ ] **E7 G7 m2≤200/206/208**：`G7_s = (m2_raw ≤200 for 1M, ≤206 for 1p5M, ≤208 for 2M)` 且 `m_total_raw ≤200/206/208` 信封 per source (V65 用 `m_total 200/206/208` 直接比较，若 G6 已过则等价；但逐层校验 `m1≤16 && m_total≤200` 已验)
- [ ] **E8 G8 provenance 零重叠**：`G8_s = (CAL∩VAL==∅ && CAL∪VAL∩TEST==∅ && CAL∪VAL∪TEST∩(V13..V64)==∅ && CAL_SESSION!=TEST_SESSION && not_cross_spliced)` per source
- [ ] **E9 per source 汇总**：`PASS_s = G1..G8 全 True`，落盘 `per_source {G1..G8 booleans, PASS_s}`，三源分别，不用总体平均，已验

## Phase F — 总体五态判定与 V66 预冻结（优先级互斥）

- [ ] **F1 五态总体判定（优先级高→低，互斥，不主观）**：
  ```
  if not materialization_ok_all or frame_256_violation or cross_spliced or chain_not_closed or provenance_fabricated:
      overall = V65_EVIDENCE_INVALID
  elif n_new_sessions<2 or |CAL|!=4096 or |VAL|!=512 or |TEST|!=120 per source:
      overall = V65_DATA_NOT_READY
  elif exists s: not G2_s or not G3_s or not G4_s:
      overall = V65_MODEL_NOT_STABLE  # λ触界 或 ΔNLL>0.5 或 Val NLL逸出，不扩网格
  elif exists s: not G6_s or not G7_s:
      overall = V65_RATE_INCOMPATIBLE_WITH_FROZEN_CANDIDATE  # 不改矩阵
  elif forall s: PASS_s==True:
      overall = V65_CHANNEL_COMPATIBILITY_READY_FOR_V66  # 仅此态允许 V66
  ```
  落盘 `overall` 与 `shunt_per_source {PASS_s, 失败门编号}` 至 `v65_channel_compatibility.json:verdict`，优先级严格先到先得，已验
- [ ] **F2 仅第5态允许 V66 预冻结声明**：`READY_FOR_V66` 时报告显式声明“**允许另起 V66 走 QUALIFICATION_PLAN_READY + Pre-EXECUTE/Pre-RESULT + EXECUTE_AUTH 的 decoder TEST 90 blocks (30/source)** (与 CAL4096/VAL512/TEST120 及 V48-V64 均零重叠，未揭盲)”；其余 4 态均显式“**不允许 decoder TEST**”，`MODEL_NOT_STABLE 不扩网格 / RATE_INCOMPATIBLE 不改矩阵` 已声明
- [ ] **F3 V66 预冻结规模与门禁显式声明**：`V66 90 blocks 30/source (4×256→1024 symbols), total leak 5*m_total+64 三档 + V64 full-tag, 预算硬帽? 本预冻结仅声明 m_total 200/206/208 不变`，门禁 `70/90 overall (77.78%) 且每源 ≥20/30 (66.67%) 且 undetected_full_tag==0 且 syndrome_ok && tag_ok_full` 双验证已预注册，不在本轮执行

## Phase G — 脚本与报告交付（PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED）

- [ ] **G1 编写 `scripts/v65_data_readiness.py`** (decoder-free, 本变更目录下): `python scripts/v65_data_readiness.py [--new-session-root PROJECT_DATA_ROOT] [--v13-registry ...] [--v48-v64-registries ...] [--out v65_data_registry.json]` → session 数检测 (<2→DATA_NOT_READY) + `CAL 4096 + VAL 512 + TEST 120` 切分与三重零重叠 + `CAL_SESSION!=TEST_SESSION && not_cross_spliced` + `frame 256 A/B mapping` 校验，`rg "decode_" 0 hits` 仅 `numpy/pandas/pyarrow + ttbin_pipeline(TimeTagger optional)`，`py_compile` PASS，输出 `v65_data_registry.json + v65_data_readiness.json` + 控制台 spike 摘要，校验 `TEST 未参与` 及 `m_raw 未 cap` 硬校验在 G 阶段完成
- [ ] **G2 编写 `scripts/v65_channel_compatibility.py`** (decoder-free, 本变更目录下): `python scripts/v65_channel_compatibility.py [--cal-root ...] [--val-root ...] [--test-registry ...] [--out v65_channel_compatibility.json] [--report V65_CHANNEL_COMPATIBILITY_REPORT.md]` → `CAL C_ab/P_global → λ 4-fold log10[-2,4] 连续 → P_λ* → H/H1/H2 链式 → m_raw ceil 不 cap → P(U1|B)/P(U2|U1B) 表 → VAL NLL/ΔNLL/unseen/MAP/effective → G1-8 per source →  overall 五态优先级 → V66 预冻结声明`，`rg "decode_" 0 hits` 仅 `numpy/pandas/pyarrow`，`py_compile` PASS，不扩网格，输出 `v65_channel_compatibility.json + V65_CHANNEL_COMPATIBILITY_REPORT.md + v65_manifest.json + registries` + 控制台摘要，校验 `TEST 未参与` 及 `m_raw` 未 cap 及 `λ 触界不扩`
- [ ] **G3 撰写 `V65_CHANNEL_COMPATIBILITY_REPORT.md`**：每源 `Cal/Val pairs/frames + λ 是否触界 + H(U1|B)/H(U2|U1B)/H(A|B) + CV NLL/Val NLL/ΔNLL + MAP/q_mass/effective_contexts + m1_raw/m2_raw/m_total 相对冻结构 16/200/206/208 差额 + G1-8 明细` + 总体 `READY/DATA_NOT_READY/MODEL_NOT_STABLE/RATE_INCOMPATIBLE/EVIDENCE_INVALID + V66 90 blocks 30/src 预冻结` + `TEST identity 附录（不含统计）` + `Negative Control (V57 8192 MLE 30bits)` 章节，数据与 `json` 一致，结论不扩大为 `FER/阈值/SKR/晋升`，显式 `CAL/VAL TEST 零重叠不跨 session` + `TEST 未参与先验/阈值` + `仅第5态允 V66` + `m_i ceil 不 cap 伪装` + `λ 触界不扩`
- [ ] **G4 自检（G1-8 + 五态 + 守卫）**：`py_compile` 双脚本 PASS, `rg "decode_" 0 hits` 双脚本已验, `git diff -- src/ ==0` 且 `git diff -- comparison_bench/src/comparison_bench/formal_ir/ ==0` (未改码) 已验, 三重零重叠 + `CAL_SESSION!=TEST_SESSION` + `not_cross_spliced` 已验, `|H-H1-H2|<1e-9` 已验, `λ ∈ (1e-2,1e4)` 开区间且触界即 `MODEL_NOT_STABLE` 不扩已验 (`λ_search_trace` 落盘), `m_i  ceil` 不 cap 已验 (`m_raw` 显式), `G1-8 per source` 已报告, `overall` 互斥 `EVIDENCE_INVALID > DATA_NOT_READY > MODEL_NOT_STABLE > RATE_INCOMPATIBLE > READY` 已落盘, `TEST 未读统计` 已验 (`used_test_in_estimation==False`), `TEST identity 仅附录` 已验, `V66 90 blocks 30/src 70/90 & 20/30 undetected 0` 预冻结已声明, 报告与 json 一致
- [ ] **G5 推送新 Plan SHA 并停留 `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`**，未创建任何 `.../v65_*/run_01` 或 `.../v66_*/run_01` decoder 执行，不碰 `V48-V64` 块，未启动 V66，仅改本目录 + `scripts/`，**推送后等待独立审核**（`Pre-RESULT` 独立线程复核 `HEAD/ACCEPTED_PLAN_SHA/rg 0 hits/run_01不存在/py_compile+关键测试 PASS/TEST 未读统计/λ 预注册不调/m_i raw 显式`），`V66` 仍 `PENDING`，返回 `Plan SHA / implementation SHA / readiness spike 结果 / estimation spike 结果 / per-source G1-8 / 五态终态` 等待 `PLAN_ACCEPT`

## 本变更显式禁止

decoder 调用 (`decode_*` / `construct_*` / `sample_uniform_gf32` 等)；读密封 `TEST_SESSION` 的 `H/NLL/MAP/熵/分布` 统计或将其用于 `P(a|b)/λ/阈值` 选择；在原 `V55 90-block` 或 `V48-V64` 已用 `frame_ids` 上重跑任何先验估计；调 `H1/Lane C/Δ8/decoder 90/1.0/m2/leak/prior/H_inc/H_total/verification` 任一冻结参数或新增矩阵；**跨 session 拼接凑 4096+120**（单 session 必须各自完整）；**将 floor/round 当 ceil**；**将 `min(16, ceil(...))` cap 伪装当通过**（`m_raw` 必须显式）；**用 `VAL` 择优 `λ` 或选平滑方式**（`λ` 仅 `Cal 内 4-fold`，触界不扩）；**将不足两 session 伪判为可兼容**（应 `DATA_NOT_READY`）；**改 `src/` 基线**（`ttbin_pipeline` 只读复用，修复仅 wrapper）；宣称 LDPC 证伪或 `FER/阈值/SKR/晋升/安全证明`；创建正式 `.../v65_*/run_01` 或 `.../v66_*/run_01` decoder 执行；任意 `bin_width/dimension/pairing/mapping/frame anchor` 网格或阈网格（处理点单点，`λ` 仅 `[-2,4]` 连续）；用第二 estimator 作门禁（仅 hierarchical 一路）；`I` 总体平均替代三源分别判定；覆盖已有输出；`V55 90 / V48-V64` 永久禁用違反；**主观“显著恢复”替代 G1-8 硬阈**；**擅自启动 V66**（仅 `READY` 后另起 `EXECUTE_AUTH` 才允）。

## 验收

- proposal/design/tasks/specs 一致 HEAD `TBD→新 Plan SHA` `84d62779` lifecycle `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` 终态 5 选 1 按优先级互斥明确（`EVIDENCE_INVALID(物化/拼接) > DATA_NOT_READY(少两 session) > MODEL_NOT_STABLE(λ触界/ΔNLL>0.5) > RATE_INCOMPATIBLE(m1>16/m2>200+) > READY_FOR_V66(全 G1-8)`），显式三源分别、λ 预注册 hierarchical 唯一、`TEST` 密封仅 identity、`V66 90 30/src 70/90 & 20/30 undetected 0` 已冻结，严格复用 V56 materialization，冻结数据角色/熵与 m 公式/G1-8/五态
- 预注册 `CAL 4096 (1048576) + VAL 512 (131072) + TEST 120 (30720)` 每源独立 `CAL_SESSION!=TEST_SESSION` 不跨 session 拼接可验三重零重叠 (`CAL∩VAL==∅ && CAL∪VAL∩TEST==∅ && ∩V13..V64==∅` + session_isolation)，`frame 256 A=32U1+U2 B=32V1+V2` 每帧已验，少两 session → `DATA_NOT_READY` 不伪造，注册表已落盘，`TEST` 未读统计已验
- 合同 `dimension 1024 / bin200 / nearest legacy_v1 / channels/delay/peak/sigma/gate/threshold/frame anchor/mapping 每帧256` 三源分别 provenance 已显式落盘，与 V56 逐项一致已验，偏则 `EVIDENCE_INVALID` 已验
- 每源 `CAL` 上 `C_ab 1024×1024 → P_global → P_λ*=(C+λP_global)/(N_b+λ) → H(U1|B)/H(U2|U1B)/H 链式 |H-H1-H2|<1e-9 → m1_raw/m2_raw=ceil(1.3*1024*H_i/5) 不 cap` 已重算，`λ` 仅 `Cal 内 4-fold` `log10[-2,4] 连续` 最小 `CV NLL` 已落盘，`λ_at_boundary` 已标记触界即 `MODEL_NOT_STABLE` 不扩，已生成 `P(U1|B)/P(U2|U1B)` 表，禁第二 estimator 已验
- 每源 `Cal/Val pairs/frames, λ 触界, H(U1|B)/H(U2|U1B)/H(A|B), CV NLL/Val NLL/ΔNLL, MAP, q_mass_unseen, effective_contexts, m1_raw/m2_raw/m_total 相对凍結構 16/200/206/208 差額` 已報告，`TEST 僅 identity` 已驗，`m_i ceil` 未 cap 已驗
- Validation `G1 authority / G2 λ不触界 / G3 ΔNLL≤0.5 / G4 Val NLL≤H+1.0 / G5 unseen≤1% / G6 m1≤16 / G7 m2≤200/206/208 / G8 provenance零重叠` 已逐源判定 `PASS_s`，三源分别，不用总体平均，`overall` 互斥 `EVIDENCE_INVALID>DATA_NOT_READY>MODEL_NOT_STABLE>RATE_INCOMPATIBLE>READY` 已落盘，仅第5态允许 `V66` 且 `V66 90 30/src 70/90 & 20/30 undetected 0` 预冻结已声明
- 双脚本 `rg "decode_" 0 hits` `py_compile` PASS `λ 触界不扩` `m_raw 不 cap` `TEST 未读` 已验 报告与 json 一致 未建 `run_01` 已推新 Plan SHA `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` 仅改本目录 + `scripts/`（`src/` 零改），原 `90` 与 `V48-V64` 未碰，未启动 `V66`，推送后等待独立审核，`V66` 仍 `PENDING`
