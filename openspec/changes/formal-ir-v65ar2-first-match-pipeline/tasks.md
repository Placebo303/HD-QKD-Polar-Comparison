# OpenSpec Tasks: formal-ir-v65ar2-first-match-pipeline — V65AR2 first-match/stop-on-failure 流水线（PLAN_CANDIDATE / DECODER_FREE）

**Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — **decoder-free additive Phase R + Stage0 4+4 first-match + Stage1 256/64 + Stage2 1024/256+TEST32 seal，候选顺序与 tier 冻结，stop-on-failure 不可达，速率不 cap 分支，推送 SHA 后等待审核**
**HEAD**: `9625afb4... → 新 SHA` (branch `formal-ir-mainline`, `git fetch && git rev-parse HEAD == origin/formal-ir-mainline` 重核) + data SHA `84d62779`
**Predecessor**: `formal-ir-v65-new-session-channel-compatibility` `V65` `9625afb4 PLAN_REVISE_REQUIRED`
**Method frozen**: 候选 `162148→2500K→160254` first-match、`A/B/C tier` 冻结，Phase R 仅 `raw TTBin + routing contract` additive sidecar，Stage 样本 `4+4 / 256+64 / 1024+256+TEST32`，`m_req=ceil(1.3*1024*CE_i/5)` 不 cap 分支 `RATE_ADAPTATION_REQUIRED / FULL_DISCLOSURE_LAYER`，TEST 仅 identity
**Boundary**: 候选顺序 frozen 不按统计换、provenance tier frozen、Phase R 禁复用冲突 sidecar/改 raw/搜 pair/调 decoder、Stage0 首 PASS 即 selected、任一步 FAIL 后续 UNREACHABLE、Stage1/2 每层<1024超旧容量→RATE_ADAPTATION 层≥1024→FULL_DISCLOSURE 非候选失败、Stage2 TEST 仅 identity 不参估计

## Phase R — decoder-free metadata recovery（additive sidecar，仅候选自身 raw + contract）

- [ ] **R1 冻结候选与 tier 绑定**：写入 `v65ar2_manifest.json:candidate_order = ["162148","2500K","160254"]` 与 `per_candidate {candidate_id, provenance_tier A/B/C, raw_root, contract_path, contract_hash, raw_hash}`，`tier` 与 `candidate_id` 一一绑定，不按统计升降级，`contract_hash` 可回溯至 `acquisition_routing.yaml` 版本，落盘 `v65ar2_data_registry.json:candidate_binding`。
- [ ] **R2 additive sidecar 重建（decoder-free）**：每候选仅自 `raw/*.ttbin + contract` 重建 `sidecar_additive.json`，字段 `delay_used_ps / peak_center / sigma / gate 200 / threshold 40000 / frame_anchor / mapping legacy_v1 / channel_pair`，仅 additive 补充不覆盖 raw，不复用冲突 sidecar 字段（`rg "reuse.*sidecar|merge.*sidecar" 0 hits` 为冲突复用），`rg "decode_" 0 hits`，`raw_hash` 重算一致性校验 `raw_untouched==True` 已验。
- [ ] **R3 禁令校验**：脚本内显式 `assert not reused_conflicting_sidecar && not modified_raw && not searched_channel_pair && not called_decoder`，分别对应 `sidecar_additive.reused==False / raw_hash一致 / channel_pair==contract.channel_pair (非扫描最优) / rg "decode_" 0 hits`，违则 `V65AR2_EVIDENCE_INVALID`，已验落盘 `v65ar2_phase_r.json:guards`。
- [ ] **R4 Phase R 门禁与可达性**：每候选独立 `PHASE_R_PASS = R1..R3 全过 && sign(delay)==sign(peak) && |delay-peak|<50ps && sigma∈[50,150] && gate==200 && threshold==40000`，`PHASE_R_FAIL` 的候选标记 `Stage0 UNREACHABLE_R`，但不影响其他候选 Phase R 判定；`overall_phase_r` 至少一候选 PASS 才允许进入 Stage0，否则 `overall = V65AR2_PHASE_R_FAIL` 停留在 R。

## Phase 0 — Stage0 4+4 first-match 门禁（小样本快速筛选）

- [ ] **S0-1 定义 Stage0 帧（每候选独立，小样本）**：每候选 `CAL 4 blocks (16 frames, 4096 pairs) + VAL 4 blocks (16 frames, 4096 pairs)`，共 `8 blocks =32 frames =8192 pairs`，`frame_id∈[0,F_s-1]` 连续，`pairs_per_frame 256`，三候选独立但算法确定性，可复现，写入 `v65ar2_data_registry.json:per_candidate.stage0 {CAL_frames[16], VAL_frames[16], blocks 8, pairs 8192}`，`overall_zero_overlap_verified` 含 `CAL_key∩VAL_key==∅ && ∩(V13..V65)_key==∅ (key=(source,session,frame))`。
- [ ] **S0-2 估计与门禁（每候选独立，first-match 定序）**：按 `candidate_order` 定序逐一对 `CAL 4 blocks` 算 `C_ab 1024×1024 → P_global → λ 4-fold CV log10[-2,4] 连续 → P_λ* → H_cal描述性 + CE1/CE2/CE_full (VAL 4 blocks) 链式 |CE_full-CE1-CE2|<1e-9 → m1/m2=ceil(1.3*1024*CE_i/5) 不 cap → P(U1|B)/P(U2|U1B) 表 → VAL NLL/ΔNLL/unseen/MAP/effective → G1-8(含 G7-aux) per candidate stage0`，首个 `PASS_s0==True` 的候选即 `selected`，记录 `selected_candidate_id` 与 `selection_reason="first_match"`，后续候选 Stage0 标记 `UNREACHABLE_FIRST_MATCH` 不再评估统计优劣，已验 `selected` 非 CE 最优递补。
- [ ] **S0-3 三候选全 FAIL 分支**：若 `∀ candidate: Stage0 FAIL`（G1-5/G8 任一失败或 `m_req` 不作失败但 G 失败），则 `overall = V65AR2_STAGE0_NO_CANDIDATE`，`Stage1/2` 整体 `UNREACHABLE`，落盘 `v65ar2_pipeline_result.json:overall {status STAGE0_NO_CANDIDATE, per_candidate {G1..G8, PASS, m_req, CE, fail_gate}}`，不以亚军递补，不进入 Stage1。
- [ ] **S0-4 Stage0 报告**：每候选 Stage0 落盘 `per_candidate_stage0 {pairs/frames, λ_at_boundary, CE1/CE2/CE_full+chain_delta, CV/Val/ΔNLL, MAP/unseen/effective, m1/m2/m_total vs 16/184-192/200-224 + rate_branch (Stage0 仅 WITHIN/超阈但不分支), G1-8(G7-aux), PASS/FAIL/UNREACHABLE}`，`TEST` 不涉及，已验 `m_req` 不 cap 且 `λ` 触界不扩。

## Phase 1 — Stage1 256/64 稳定性（仅 selected）

- [ ] **S1-1 定义 Stage1 帧（仅 selected）**：仅对 `selected` 候选 `CAL 256 frames (65536 pairs, 64 blocks) + VAL 64 frames (16384 pairs, 16 blocks)`，共 `320 frames =80 blocks`，独立于 Stage0 帧重选（不复用 Stage0 的 4+4 帧，需与 Stage0 CAL/VAL 及 V13..V65 零重叠，键 `(source,session,frame)`），写入 `v65ar2_data_registry.json:selected.stage1 {CAL[256],VAL[64]}`。
- [ ] **S1-2 估计与门禁（仅 selected，独立重算）**：对 `CAL 256` 独立算 `C_ab→P_global→λ 4-fold CV [1e-2,1e4]→P_λ*→H_cal描述性+CE1/CE2/CE_full (VAL 64)链式→m1/m2=ceil(1.3*1024*CE_i/5)不 cap→P表→VAL NLL/ΔNLL/unseen/MAP/effective→G1-8(含 G7-aux)`，`G1-5/G8 FAIL → STAGE1_FAIL`，`G6/G7` 超冻结构但 `m_req<1024` 不判 FAIL 而入速率分支（Stage1 速率分支仅记录，终态以 Stage2 为准），落盘 `v65ar2_pipeline_result.json:selected.stage1`。
- [ ] **S1-3 Stop-on-failure**：`Stage1 FAIL` 则 `Stage2` 标记 `UNREACHABLE_S1`，`overall = V65AR2_STAGE1_FAIL` 按优先级落盘，不继续 Stage2，不回退重选候选，已验 `UNREACHABLE` 标记。
- [ ] **S1-4 Stage1 报告**：selected Stage1 落盘 `pairs/frames, λ/λ_at_boundary, CE1/CE2/CE_full+chain_delta, CV/Val/ΔNLL, MAP/unseen/effective, m1/m2/m_total vs 16/184-192/200-224 + rate_branch, G1-8, PASS/FAIL/UNREACHABLE`，`TEST` 不涉及。

## Phase 2 — Stage2 1024/256 + seal TEST32（仅 Stage1 PASS 的 selected，速率分支）

- [ ] **S2-1 定义 Stage2 帧与 TEST32 seal（仅 Stage1 PASS）**：仅对 `Stage1 PASS` 的 selected `CAL 1024 frames (262144 pairs, 256 blocks) + VAL 256 frames (65536 pairs, 64 blocks) + TEST32 32 frames (8192 pairs, 8 blocks) seal`，共 `1312 frames =328 blocks (+8 seal)`，独立于 Stage0/1 帧重选且三阶段 CAL/VAL/TEST32 彼此零重叠且与 V13..V65 零重叠（键 `(source,session,frame)`），`TEST32` 仅 seal identity 写入 `v65ar2_test_registry.json {selected, TEST_frames[32], blocks 8, pairs 8192, provenance, sealed_at}` 且 `v65ar2_data_registry.json:selected.stage2`，不计任何统计已校验 `used_test_in_estimation==False`。
- [ ] **S2-2 估计与门禁（主估计，独立重算）**：对 `CAL 1024` 独立算 `C_ab 1024×1024 sum 262144 → P_global → λ 4-fold CV (1024→4 folds 各256) → P_λ* → H_cal描述性 + CE1/CE2/CE_full (VAL 256) 链式 |CE_full-CE1-CE2|<1e-9 → m1_req/m2_req=ceil(1.3*1024*CE_i/5) 不 cap 显式 raw → P表 → VAL NLL/ΔNLL/unseen/MAP/effective → G1-8(含 G7-aux)`，落盘 `v65ar2_pipeline_result.json:selected.stage2 {CE, m_req_raw, m_req_branch, H, G1-8}`。
- [ ] **S2-3 速率分支（不 cap，显式分支，非候选失败）**：
  ```
  if m1_req≥1024 or m2_req≥1024: branch = FULL_DISCLOSURE_LAYER (该层需全披露)
  elif m1_req>16 or m2_req>184/190/192 or m_total_req>216/222/224 and m_i_req<1024: branch = RATE_ADAPTATION_REQUIRED (每层<1024但超旧容量)
  else: branch = WITHIN_FROZEN_BUDGET
  ```
  `branch` 显式落盘 `per_layer {m_req, branch}` 与 `overall_rate_branch`，`G6/G7` 超阈不作 `STAGE2_FAIL`，仅速率分支；`G1-5/G8` 失败才作 `STAGE2_FAIL`，已验 `m_req` 未 cap (`grep "min(16" 0 hits`) 且 `TEST32` 未参与。
- [ ] **S2-4 Stop-on-failure 与终态前置**：若 `G1-5/G8 FAIL` 则 `overall = V65AR2_STAGE2_FAIL`；否则按 S2-3 分支进入总体终态机，`TEST32` 全程 `UNREACHABLE` 若 Stage2 未达，已验 `used_test_in_estimation==False` 且 `TEST32` 不含 `H/CE/NLL`。

## 流水线终态机与脚本框架（first-match / stop-on-failure / 速率分支）

- [ ] **F1 总体终态判定（优先级互斥，first-match/stop-on-failure）**：
  ```
  if provenance_fabricated or frame_256_violation or CE_chain_not_closed or reused_conflicting_sidecar or modified_raw or searched_channel_pair:
      overall = V65AR2_EVIDENCE_INVALID
  elif not exists candidate: Phase R PASS:
      overall = V65AR2_PHASE_R_FAIL
  elif forall candidates: Stage0 FAIL:
      overall = V65AR2_STAGE0_NO_CANDIDATE
  elif selected Stage1 FAIL (G1-5/G8):
      overall = V65AR2_STAGE1_FAIL
  elif selected Stage2 FAIL (G1-5/G8):
      overall = V65AR2_STAGE2_FAIL
  elif exists layer: m_req≥1024:
      overall = V65AR2_FULL_DISCLOSURE_LAYER
  elif exists layer: m_req> frozen but <1024:
      overall = V65AR2_RATE_ADAPTATION_REQUIRED
  elif forall stages PASS && m_req within frozen:
      overall = V65AR2_READY
  ```
  落盘 `overall` 与 `per_phase {R, S0 per candidate, S1 selected, S2 selected, UNREACHABLE reason}` 至 `v65ar2_pipeline_result.json:verdict`，优先级严格先到先得，已验 `selected` 不递补、`UNREACHABLE` 语义正确。
- [ ] **F2 编写 `scripts/v65ar2_pipeline.py` 框架（decoder-free，分相 CLI）**：
  - `python scripts/v65ar2_pipeline.py --phase R --candidate 162148 --raw-root ... --contract ... --out v65ar2_phase_r.json`
  - `python scripts/v65ar2_pipeline.py --phase 0 --candidate-order 162148,2500K,160254 --tier A,B,C --data-root ... --dry-run`
  - `python scripts/v65ar2_pipeline.py --phase 1 --candidate selected --data-root ...`
  - `python scripts/v65ar2_pipeline.py --phase 2 --candidate selected --seal-test --data-root ...`
  - `python scripts/v65ar2_pipeline.py --all --dry-run  # 框架自检，不读真实 raw`
  → `Phase R additive → Stage0 4+4 first-match → Stage1 256/64 → Stage2 1024/256+TEST32 seal`，`rg "decode_" 0 hits` `rg "reuse.*sidecar|search.*channel" 0 hits` 为冲突复用/搜 pair，`py_compile` PASS，仅 `numpy/pandas/pyarrow`，任一 phase FAIL 后续标记 `UNREACHABLE` 已验。
- [ ] **F3 撰写 `V65AR2_PIPELINE_REPORT.md`**：每候选 Phase R + Stage0 明细，selected 另 Stage1/2 明细，`CE1/CE2/CE_full+chain_delta + CV/Val/ΔNLL + MAP/unseen/effective + m1/m2/m_total vs 16/184-192/200-224 + rate_branch(RATE_ADAPTATION/FULL_DISCLOSURE/WITHIN) + G1-8(含 G7-aux)`，总体 `overall 终态 (EVIDENCE_INVALID/PHASE_R_FAIL/STAGE0_NO_CANDIDATE/STAGE1_FAIL/STAGE2_FAIL/RATE_ADAPTATION/FULL_DISCLOSURE/READY)` + `UNREACHABLE` 标注 + `TEST32` 附录（仅 identity 含 `v65ar2_test_registry.json` 声明），数据与 `json` 一致，结论不扩大为 `FER/阈值/SKR/晋升`，显式 `候选顺序冻结 first-match` + `tier 冻结` + `additive 重建` + `TEST 未参与` + `m_req 不 cap`。
- [ ] **F4 自检（G1-8含 G7-aux + 终态 + 守卫 + 冻结）**：`py_compile` 脚本 PASS, `rg "decode_" 0 hits` 已验, `git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0` (未改码) 已验, 候选顺序 `162148→2500K→160254` 冻结已验 (`candidate_order` 落盘且 `rg "sort.*CE" 0 hits`), `tier A/B/C` 冻结已验, Phase R `additive` + 禁令三项已验, Stage0 `first-match` + `selected` 不递补已验, `stop-on-failure UNREACHABLE` 语义已验, `|CE_full-CE1-CE2|<1e-9` 链式已验, `λ ∈ (1e-2,1e4)` 触界即 `MODEL_NOT_STABLE` 不扩已验 (`search_trace` 落盘), `m_req ceil` 不 cap 且 `m_req≥1024→FULL_DISCLOSURE 层<1024超旧→RATE_ADAPTATION` 已验, `TEST32` 未读统计已验 (`used_test_in_estimation==False`), 报告与 json 一致, 未建 `run_01` 已验。
- [ ] **F5 推送新 implementation SHA 并停留 `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`**，未创建任何 `.../v65ar2_*/run_01` 或 `.../v66_*/run_01` decoder 执行，不碰 `V48-V65` 块，未运行真实流水线，仅改本目录 + `scripts/`，**推送后等待独立审核**（`Pre-RESULT` 独立线程复核 `HEAD/ACCEPTED_PLAN_SHA/rg 0 hits/run_01不存在/py_compile+关键测试 PASS/候选顺序冻结/TEST 未读/m_req 不 cap/UNREACHABLE 语义`），返回 `Plan SHA / implementation SHA / 框架 spike 摘要 / per-phase G1-8 / overall 终态` 等待 `PLAN_ACCEPT`。

## 本变更显式禁止

decoder 调用 (`decode_*` / `construct_*` 等)；复用冲突 sidecar；改 raw TTBin；搜/猜 channel pair；在原 `V55 90-block` 或 `V48-V65` 已用 `(source,session,frame)` 上复用帧；按 `CE/H/ΔNLL` 统计重排候选顺序或跨 tier 共享 provenance；调 `H1/Lane C/Δ8/decoder 90/1.0/m2/m_total/leak/prior/H_inc/H_total/verification` 任一冻结参数或新增矩阵；**跨阶段复用 λ/C_ab**（每阶段独立重算）；**将 `min(16, ceil)` cap 伪装当 WITHIN**（`m_req` 必须显式 raw）；**将 `FULL_DISCLOSURE_LAYER` 误判为 RATE_ADAPTATION**（≥1024 为全披露层）；**将 `RATE_ADAPTATION_REQUIRED` 误判为候选失败**（每层<1024超旧容量为分支非失败）；**将 `TEST32` 统计用于估计/阈值**（仅 identity）；**将 Stage1 FAIL 后仍进 Stage2**（UNREACHABLE）；**将 second estimator 作门禁**；宣称 LDPC 证伪或 `FER/阈值/SKR/晋升/安全证明`；创建正式 `.../v65ar2_*/run_01` 或 `.../v66_*/run_01` decoder 执行；任意 `bin_width/dimension/pairing/mapping/frame anchor` 网格或阈网格；未授 `EXECUTE_AUTH` 前运行真实流水线。

## 验收

- proposal/design/tasks/specs 一致 HEAD `9625afb4...→新 SHA` `84d62779` lifecycle `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` 终态按优先级互斥明确（`EVIDENCE_INVALID > PHASE_R_FAIL > STAGE0_NO_CANDIDATE > STAGE1_FAIL > STAGE2_FAIL > RATE_ADAPTATION_REQUIRED / FULL_DISCLOSURE_LAYER / READY`），显式 first-match 不按统计换候选、tier 冻结、Phase R additive、Stage0 4+4 首 PASS、Stage1 256/64、Stage2 1024/256+TEST32、stop-on-failure UNREACHABLE、速率不 cap 分支、TEST 仅 identity
- 候选顺序 `162148→2500K→160254` 冻结已验 (`candidate_order` 落盘且无统计重排逻辑)，`A/B/C tier` 冻结已验，Phase R 每候选 `raw TTBin + contract` additive 重建已验 (禁三项 + raw 未改 + `rg "decode_" 0 hits`)
- 流水线定序可验 first-match/stop-on-failure：Stage0 按冻结顺序逐候选，首 PASS 即 selected 不递补；Stage1 仅 selected 可达；Stage2 仅 Stage1 PASS 可达；任一步 FAIL 后续 `UNREACHABLE` 已验
- 每相 `C_ab 1024×1024 → P_global → P_λ*=(C+λP_global)/(N_b+λ) → H_cal描述性 + CE1/CE2/CE_full(VAL)链式 |CE_full-CE1-CE2|<1e-9 → m1/m2/m_total=ceil(1.3*1024*CE_i/5)不 cap` 已重算且 `m_req≥1024→FULL_DISCLOSURE 层<1024超旧→RATE_ADAPTATION` 已验，`λ` 仅 `Cal 内 4-fold` `log10[-2,4] 连续` 已落盘触界不扩，`TEST32` 未读已验
- 每相 `pairs/frames, λ触界, CE+chain_delta, CV/Val/ΔNLL, MAP/unseen/effective, m_req vs 16/184-192/200-224 + rate_branch + G1-8(G7-aux)` 已报告，`TEST32` 仅 identity 已验，`m_req ceil` 未 cap 且 `leak=5*(16+m2)+64` 一致已验
- Validation `G1 authority / G2 λ不触界 / G3 ΔNLL≤0.5 / G4 Val≤H+1.0 / G5 unseen≤1% / G6 m1≤16 / G7 m2≤200-208 / G7-aux m_total≤216-224 / G8 provenance零重叠+CE链式` 已逐相判定，候选/阶段分别，overall 互斥已落盘，速率分支与候选失败隔离已验
- 脚本 `rg "decode_" 0 hits` `py_compile` PASS `λ 触界不扩` `m_req 不 cap` `TEST 未读` `CE 链式` `UNREACHABLE` 已验 报告与 json 一致 未建 `run_01` 未运行真实流水线 已推新 SHA `PLAN_CANDIDATE / DECODER_FREE` 仅改本目录 + `scripts/`（`src/` 零改），未启动真实执行，推送后等待独立审核

