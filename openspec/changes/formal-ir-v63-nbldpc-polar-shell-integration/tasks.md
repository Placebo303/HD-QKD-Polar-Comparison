# OpenSpec Tasks: formal-ir-v63-nbldpc-polar-shell-integration — V63 NB-LDPC Polar 壳集成

**Lifecycle**: `PLAN_CANDIDATE / SHELL_INTEGRATION / EXECUTE_NOT_AUTHORIZED` — **仅 plan 四工件，未适配前禁止实现/运行 decoder，不改 Polar src，不继续 V61/V60**
**HEAD**: `fad33f4b935e73972b5be4d02ec7901214fa0046` → 新 Plan SHA (branch `formal-ir-mainline`, 实施前以 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline == fad33f4b...` 重核，不一致阻塞) + data SHA `84d62779` (200ps legacy_v1 nearest 1024, q1024)
**Predecessor**: `formal-ir-v54-two-stage-incremental-l2-rescue` `cb60c5dd48...` (V54 二阶段 `Δ8+Δ8` 已冻) + `formal-ir-v62` 仅参考；本变更为 V54 性能候选的**壳集成**，不改二者终态
**Boundary**: 每 block 1024 symbols (`4×256 frames`), `GF32 log2q=5`, `tag=64 L2-only` 仅 `total` 计一次；`H1/Lane C/H_inc/Δ/decoder 90/1.0 poly37` 全冻；PA 输入 `actual_disclosure_bits` (1064→1144/1174) 不 reuse Polar；新 session 需 domain_check+calibration+m1/m2 重算

## Phase A — 壳/IR 接口冻结与适配设计（不改 Polar src，comparison_bench 新增）

- [ ] **A1 fetch 与 HEAD 自检（阻塞门）**：`git fetch origin && git rev-parse HEAD == origin/formal-ir-mainline == fad33f4b935e73972b5be4d02ec7901214fa0046` 完整 40 位，不一致则阻塞；记录 `HEAD/origin/implementation SHA` 至报告 `provenance`，`rg "cb60c5dd48b37965d555e42cb664522db314c49" 0 hits` 旧 SHA 无残留（除历史记录），`data SHA 84d62779` 已验
- [ ] **A2 Polar 外壳只读盘点（只读，不改）**：对 `src/` `experiments/run_e2e_pipeline.py` `tools/` 执行 `rg "TTBin|pairing|binning|symbol|provenance|PA|leak"` 盘点可复用组件清单（`TTBin读取、通道选择、delay/pairing、symbol materialization、session/source/frame provenance、参数估计分层、verification/丢帧、PA、认证报告、Polar PIE/SKR 参数参考`），记录 `file:line:expr` 每项，`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0` 零改已验
- [ ] **A3 IR 接口冻结（reconciled_symbols/accepted/exact/泄漏/decoder_calls/stage_used）**：冻结 IR 替换接口 `Input: FrameBatch(alice_symbols,bob_symbols,dimension=1024,frame_len=1024,metadata={source,block_id,frame_ids,provenance})` → `Output: IRRunResult 扩展 {reconciled_symbols (=x2_hat per frame), accepted (=syndrome_ok&&tag_ok), rejected, exact (=exact_full), syndrome_ok, tag_ok, undetected (=syndrome_ok&&tag_ok&&!exact), actual_disclosure_bits (=leak_base 1064/1094/1104 or stage1 1104/1134/1144 or stage2 1144/1174/1184 per frame by stage_used), decoder_calls (per frame 2-4 breakdown), runtime_s, stage_used∈{base,delta8,delta16}}`，显式 `PA.leak = actual_disclosure_bits` 不复用 `Polar leak_EC`，`tag 64` 已含不重复
- [ ] **A4 NB-LDPC IR adapter 预冻结（comparison_bench 新增，不改 Polar）**：预冻结 `comparison_bench/src/comparison_bench/methods/nbldpc_shell_adapter.py` 的 `NbLdcShellIRAdapter(IRMethod)` 设计：import `v54_two_stage_incremental_l2_rescue` 的 `construct_h_inc/construct_h_joint1/construct_h_total, leak_for/leak_stage1_for/leak_stage2_for, compute_l2_tag, CallAccounting, BLOCK_WINDOWS` + `v38_architecture_triage` (Lane C) + `v35_algorithm_development::compute_tag_64`，实现 `L1-APP q_i=softmax(BP_i) → P_i(U2) → base(H_base)→verify_base→stage1(H_joint1)→verify_stage1→stage2(H_total)` 条件递进（`verification-only`），`reconciled_symbols` 为 `x2_hat`，`stage_used` 按实际阶段，`actual_disclosure_bits` 三档按 source，不新增矩阵/阈值/decoder
- [ ] **A5 Shell pipeline 预冻结（串联 TTBin→PA）**：预冻结 `comparison_bench/src/comparison_bench/pipeline/shell_integration.py` 的 `run_shell_pipeline(ttbin_root, source, block_ids) -> ShellResult` 设计：`TTBin读取→load_pairs_table→normalize_pair_columns→build_frame_batch(1024,1024)→NbLdcShellIRAdapter.run→verification/tag→leakage stats(actual_disclosure_bits per frame)→PA(leak=actual_disclosure_bits)→key length/PIE/SKR proxy 报告`，`src/experiments` 仅读其 `PA/leakage/report` 非 IR 函数，`polar_existing_bridge.py` 仅作 `POLAR_REFERENCE_PROXY` 参数来源
- [ ] **A6 真实数据二档边界冻结（同域 vs 新 session）**：冻结 `同域可直接运行: d1024 bw200 nearest legacy_v1, held-out 1600-1999/2213-2766/2916-3644, 43/45 已验 hash_equal, 剩余需 decoder-free 符号一致性校验` 与 `新 session 准入: decoder-free 信道域检查(P(B) χ² / H(A|B)漂移>0.05 bits判 out-of-domain) → 新 calibration P(U1|B) via get_l1_prior_p_u1_given_b + P(U2|B,U1) via get_l1_app_prior_l2/factorize_f03 → 重算 m_total=floor((1.3*n*H-64)/5), m1=round(m_total*H1/H_total), 不调 LDPC`，`first-match` 互斥，未对齐 `SHELL_DOMAIN_NOT_ALIGNED` 停止
- [ ] **A7 接口幂等与 PA 泄漏传递校验（decoder-free 公式校验）**：校验 `actual_disclosure_bits` 三档 `1064/1094/1104 →1104/1134/1144 →1144/1174/1184` 满足 `leak=5*m_total+64` 双校验 `m_total 184/190/192 +16/24` 且 `stage1-base=40, stage2-stage1=40`；校验 `PA 输入 = actual_disclosure_bits` 非 `Polar leak_EC`；校验 `IRRunResult` 扩展字段完整性（`reconciled_symbols/accepted/exact/undetected/actual_disclosure_bits/decoder_calls/runtime/stage_used` 齐全）

## Phase B — 同域 smoke 冻结（3/source=9 blocks，硬帽36，验证贯通）

- [ ] **B1 同域处理点与块形态冻结（单点 84d62779）**：冻结 `dimension 1024, bin_width 200ps, pairing nearest, rule legacy_v1, frame_len_symbols 1024, pairs_count 1024, BLOCK_LENGTH 1024, q=1024, log2q=5, tag 64 L2-only`，记录 `data SHA 84d62779` 语义，不改
- [ ] **B2 Smoke 规模与注册表冻结（3/source=9 blocks）**：冻结 `S=3, B=3, total 9`, 每块 `1024 symbols`, 从同域 held-out 剩余窗口（含 V54 已验 43 中的 9）分散选 `3/source`（若超集 `K>9` 则 `index_j=floor(j*(K-1)/2) j=0..2`，否则取已验），落盘 `v63_smoke_registry.json` ( authoritative, `block_id, source, frame_ids[4], held_out_ordinal_start/end, pairs_count 1024, BLOCK_LENGTH 1024, sampling_mode=deterministic_four_consecutive_frames_heldout_fresh_v63_smoke`)，禁换块
- [ ] **B3 可重放性校验（hash 比对，decoder-free）**：对每块 `source_path` 的 `pairs.parquet` 执行 `load_pairs_table→normalize_pair_columns→build_frame_batch(q=1024,frame_len=1024)` 无损恢复，校验 `alice_symbol/bob_symbol ∈ [0,1024)` 且 `n_complete == n_rows//1024 ≥3 per source` 且 `hash(alice||bob)` 与 shell 输入完全相等已验
- [ ] **B4 H 矩阵冻结校验（decoder-free）**：`reconstruct_v54_matrices` 对 `H1-16 rank16 + Lane C m2 184/190/192 + H_inc1 det1/H_joint1 192/198/200 + H_inc2 det2/H_total 200/206/208` 校验 `rank_total==m2+16, nested, independence==8, row≤16, col_inc≤1, E≈96, leak+40+40` 全 PASS
- [ ] **B5 贯通验证项冻结（shell 全链路）**：冻结 `TTBin→pairing→FrameBatch→NbLdcShellIRAdapter→verification→leakage stats(actual_disclosure_bits per frame + per accepted)→PA→proxy yield` 全链路需贯通；显式校验 `leak_actual 按 stage_used 三档计、stage_used 分布 base/delta8/delta16、decoder_calls 18-36 (per block 2-4)、runtime/throughput 可复现、proxy yield 可算`
- [ ] **B6 预算冻结（smoke 硬帽36）**：冻结 `L1 9 + base9 + stage1≤9 + stage2≤9 =18-36 硬帽36 (L2 9-27)`，`per block 2-4 calls`，`verification-only` 触发已验，`base` 兼 old 不重复
- [ ] **B7 未对齐停止**：若 `K_available<9` 或 `pairing/dimension/bw` 不一致或 `H 矩阵校验失败`，则 `SHELL_DOMAIN_NOT_ALIGNED` 停止，不伪造，不进 Phase C

## Phase C — 同域正式 development 设计与门禁（30/source=90 blocks，硬帽360）

- [ ] **C1 规模冻结（30/source=90 blocks）**：冻结 `S=3, B=30, total 90`, 每块 `1024 symbols (4×256 frames)`, 枚举剩余非重叠四连续窗口（`start 0..H-4 per source, H=400/554/729, base=1600/2213/2916`），过滤与已用 `V48/V50/V51/V52/V53/V54`（含 smoke 9）重叠者得 `K2`，按 `ordinal` 排序后以 `index_j=floor(j*(K2-1)/29) j=0..29` 分散选 `30/源`，落盘 `v63_dev_registry.json` ( authoritative, `block_id, source, frame_ids[4], held_out_ordinal_start/end, pairs_count 1024, BLOCK_LENGTH 1024, sampling_mode=deterministic_four_consecutive_frames_heldout_fresh_v63`)，若 `K2<90` 则 `SHELL_DOMAIN_NOT_ALIGNED` 停止
- [ ] **C2 三阶段协议冻结（硬帽360, verification-only）**：
  ```
  per block (90 blocks, 30/source):
    prior = TRAIN prior (shared, V25)  // 不重估
    shell: TTBin→FrameBatch (1024) → L1-APP (H1 s1 → BP → q → P(U2)) // 90 次总计，per block 1 (L1)
           base: decode_L2(H_base, P(U2), s_base) → verify_base = syndrome_ok && tag_ok ; exact_base
           if verify_base: final = base, leak = leak_base (1064/1094/1104), stage=base, used_inc1=False, used_inc2=False
           else:
             s_inc1 = H_inc1 * u2_true ; s_joint1=[s_base; s_inc1]
             stage1: decode_L2(H_joint1, P(U2), s_joint1) → verify_stage1 ; exact_stage1
             if verify_stage1: final = stage1, leak = leak_stage1 (1104/1134/1144), used_inc1=True, used_inc2=False
             else:
               s_inc2 = H_inc2 * u2_true ; s_total=[s_base; s_inc1; s_inc2]
               stage2: decode_L2(H_total, P(U2), s_total) → verify_stage2 ; exact_stage2
               final = stage2, leak = leak_stage2 (1144/1174/1184) 无论成功/失败, used_inc1=True, used_inc2=True
    PA: input = actual_disclosure_bits (leak per frame by stage_used), output = key length proxy
  budget: L1 90 + base90 + stage1≤90 + stage2≤90 =180-360 硬帽360 (L2 90-270)
  ```
  `verification-only` 触发已验，`leak_base/stage1/stage2` 三档已验，`rank_total==m2+16 nested/independence==8` 已验
- [ ] **C3 主指标冻结（门禁分层）**：冻结 `accepted (=verify pass) 与 exact_full (=exact_u1&&exact_l2) 分别计数（overall 90 + per-source 30）` + `四类 exact/detected/decoder_non_syndrome/undetected` + `undetected==0` 单独表永不并入 `accepted` + `disclosure bits/block 三档 + per_source_avg[s]=leak_base[s]+40*N_stage1[s]/30+40*N_stage2[s]/30 + overall_avg=(Σ leak_base+40*N_stage1+40*N_stage2)/90 + per accepted = total_disclosed_bits / accepted_count (为0则null)` + `calls/rescue(N_stage1_attempted=count(!verify_base), N_stage2_attempted=count(!verify_base&&!verify_stage1), rescued_stage1/stage2, rescue_rate= rescued/attempted)` + `runtime/throughput + stage_used 分布 + Wilson 95%`，`accepted` 与 `exact` 需分别达标
- [ ] **C4 门禁冻结（G1-G3'，first-match）**：
  ```
  if not shell_adapter_aligned or not alignment_metadata_complete or rank/nested/verification/记账/域检查失败:
      overall = V63_EVIDENCE_INVALID  # 优先
  elif not domain_possible (K2<90 or per_source<30 or not replayable or new_session_without_calibration):
      overall = V63_SHELL_DOMAIN_NOT_ALIGNED  # 停止
  elif nbldpc_not_yet_executed (本轮):
      overall = V63_PLAN_CANDIDATE__SHELL_INTEGRATION_DONE
  # 未来执行后（需适配 PASS + 独立 plan ACCEPT + EXECUTE_AUTH，主门禁为 accepted/exact）:
  # elif final_accepted >=70/90 ∧ per_source >=20/30 ∧ final_exact >=70/90 ∧ per_source exact >=20/30 ∧ undetected==0 ∧ rank/nested/记账通过 → V63_SHELL_DEVELOPMENT_PASS
  # elif has_signal (any exact>0 or rescued>0 or residual improved) but not PASS → V63_SHELL_CORRECTION_WORKS_BUT_NOT_PASS
  # else → V63_SHELL_NO_RETAINED_SIGNAL
  ```
  `G1 70/90 overall, G2 每源20/30, G3' undetected==0` 已显式，不因 V54 差2改阈值，`accepted` 与 `exact` 分别达标
- [ ] **C5 pair delta 与 proxy yield 冻结**：冻结 `per block base vs stage1 vs final (accepted/exact)` 差异 + `leak delta` 明细 + `Wilson 95%` per source & overall + `PIE/SKR proxy = accepted_fraction*(PIE - leak_per_block/1024)` 用 Polar 同一 shadow 参数仅排序，不作门禁
- [ ] **C6 零改校验（H/prior/decoder/增量）**：`H1-16 rank16, Lane C m2 184/190/192, H_inc1 det1 + joint1, H_inc2 det2 + total, decoder 90/1.0 poly37, TRAIN-only, L2-only tag, +40/+80` 全冻，不新增矩阵，不试 `Δm=4/12/16` 多档，不以 outcomes 选行

## Phase D — 外壳结果 proxy 标记（POLAR_REFERENCE_PROXY，不宣称 composable）

- [ ] **D1 PA 泄漏源冻结（NB 实际泄漏，不 reuse Polar）**：冻结 `PA.leak = actual_disclosure_bits per frame`（含 tag 64b，已计，不重复扣除），`leak_total = Σ per frame actual_disclosure_bits（三档按 stage_used）`，`leak_per_block = actual_disclosure_bits` 每帧明细可追溯 `stage_used`，`git diff -- src/ ==0` 语义只读 PA 组件仅改输入源
- [ ] **D2 security/PIE/SKR proxy 冻结（POLAR_REFERENCE_PROXY 仅排序）**：冻结 `PIE proxy = beta_eff_empirical * H_shannon` 与 `SKR proxy = accepted_fraction * (PIE - leak_per_block/1024)` 用 Polar 同一 `shadow` 参数（`polar_existing_bridge.py:benchmark_rows_from_polar_output` 的 `leak_EC_actual_bits, raw_ber, beta_eff_empirical` 与 `compute_beta_eff_empirical` 同源）计算，报告显式 `authority=POLAR_REFERENCE_PROXY, readiness=reference, proxy_only=true`，不宣称 `composable/finite-key/eps_sec`，泄漏分解语义不一致时 proxy 失效
- [ ] **D3 外壳报告 Schema 冻结**：冻结 `ShellResult` 报告含 `session/source/frame provenance + accepted/exact 四类 + disclosure per frame(三档) + per accepted + calls/rescue + runtime/throughput + stage_used 分布 + PA input leak 明细 + proxy PIE/SKR/key length + Wilson 95%` overall+per-source，三源分别不平均
- [ ] **D4 互斥性与伪造审计**：`assert overall in [EVIDENCE_INVALID, SHELL_DOMAIN_NOT_ALIGNED, PLAN_CANDIDATE__SHELL_INTEGRATION_DONE, SHELL_DEVELOPMENT_PASS, CORRECTION_WORKS_BUT_NOT_PASS, NO_RETAINED_SIGNAL] 且仅一态`，`old_data_fake_PE` 零验，`only_ALIGNED_then_run: assert (overall==SHELL_DOMAIN_NOT_ALIGNED) == (K_available<90 或 smoke<9)` 已验

## Phase E — 交付与推送（PLAN_CANDIDATE / SHELL_INTEGRATION / EXECUTE_NOT_AUTHORIZED，普通推送后停止）

- [ ] **E1 四工件一致性自检（gate）**：`py_compile PASS`，`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0 && git diff -- openspec/changes/formal-ir-v6[0-2]/ ==0`（除本变更外零改），三源 `leak_without_tag/tag` 不重复已验，`GF32 5bits` 已验，不跨源平均已验，`门禁 70/90 & 20/30 & undetected==0` 已验，`only_ALIGNED_then_run` 已验，`K_available` 机械校验已验，`HEAD==origin (fad33f4b)` 已验，`run_01` 不存在已验，正式壳集成未触发已验，新 session 准入门已验
- [ ] **E2 普通推送新 Plan SHA 并停留 `PLAN_CANDIDATE / SHELL_INTEGRATION / EXECUTE_NOT_AUTHORIZED`**（基于 `fad33f4b935e73972b5be4d02ec7901214fa0046`），未创建任何 `run_01` decoder 执行，不碰 `V54-V62 m/leak`，`src//experiments//tools//V54-V62` 零改，普通推送（非 force）至 `formal-ir-mainline`，推送后等待独立审核（`Pre-RESULT` 独立线程复核 `HEAD/ACCEPTED_PLAN_SHA/rg 0 hits/run_01不存在/py_compile+关键测试 PASS`），`V63` 仍 `PLAN_CANDIDATE`，返回 `Plan SHA / implementation SHA / shell registries / 终态`，**不自动进入正式壳集成执行，不实现正式 adapter/pipeline**

## 本变更显式禁止

decoder 调用在 plan 侧新增；改 `V54 m1/m2/leak` 或 `H1/Lane C/Δ/decoder` 冻参或新增矩阵；改 `LDPC` 码族；重跑 Polar IR；自创 `H_min / finite-key / composable` 公式或造 `eps_sec/eps_cor/vis/phase-error` 参数；用旧数据伪造同域（无 symbol 重放时伪造 `frame_ids`）；重复扣除 `tag 64`；将总体平均掩盖单源阈值；网格调参；把 V55 `frames×256` 非 legacy_v1 输入当 1024-block；宣称 `FER/SKR/阈值/晋升/安全证明`；创建正式 `run_01` decoder 执行；改 `src//experiments//tools//V54-V62`；将 Polar `proxy` 升级为 `composable`；在 `SHELL_DOMAIN_NOT_ALIGNED` 时仍进入正式壳集成；实现正式 adapter/pipeline/启动正式壳集成（本轮仅 4 工件，普通推送新 Plan SHA 后停止）。

## 验收

- proposal/design/tasks/specs 一致 HEAD `fad33f4b`→新 Plan SHA 84d62779 lifecycle PLAN_CANDIDATE SHELL_INTEGRATION EXECUTE_NOT_AUTHORIZED；外壳/IR 边界与 IR 接口输出 `reconciled_symbols/accepted/exact/syndrome_ok/tag_ok/undetected/actual_disclosure_bits/decoder_calls/runtime/stage_used` 已冻结，PA 读 NB 实际泄漏三档已验，终态按 `EVIDENCE_INVALID > SHELL_DOMAIN_NOT_ALIGNED > SHELL_DEVELOPMENT_PASS (>CORRECTION_WORKS... >NO_SIGNAL)` 互斥先匹配，未对齐 `SHELL_DOMAIN_NOT_ALIGNED` 立即停
- Phase A 壳可复用清单与 `comparison_bench` 新增 adapter/pipeline 路径已预冻结，`src` 只读已验，`actual_disclosure_bits` 三档 `leak=5*m_total+64` 双校验已验，`tag 64` 已含不重复已验
- Phase B `3/source=9 blocks, 18-36 calls 硬帽36 (L2 9-27)` 贯通验证已验，`H1/Lane C/Δ8+Δ8` 全冻，新 session 准入门已验
- Phase C `30/source=90 blocks, 180-360 calls 硬帽360 (L2 90-270)` 门禁 `70/90 & 20/30 & undetected==0` 已显式，`accepted` 与 `exact` 分别达标，不跨源平均已验
- Phase D `security/PIE/SKR` 沿用 Polar reference 参数标记 `POLAR_REFERENCE_PROXY` 仅排序已验，不宣称 composable 已验
- Phase E `py_compile` PASS 未建 `run_01` 未进正式壳集成 未重跑 Polar IR 未改 `V54-V62` 已普通推送新 Plan SHA `PLAN_CANDIDATE/SHELL_INTEGRATION/EXECUTE_NOT_AUTHORIZED` 仅改本目录（`src//experiments//tools//V54-V62` 零改），`HEAD==origin (fad33f4b)` 已验，推送后等待独立审核，**不自动进入正式壳集成，不实现正式 adapter/pipeline**

## R63 Revisions (PLAN_REVISION_CANDIDATE, 2026-08-30, HEAD 5602f11c)

## R63 Revisions (PLAN_REVISION_CANDIDATE, 2026-08-30, HEAD 5602f11c)
- [x] **R63-01 32*u1+u2+exact**: All four workpieces explicit s=32*u1+u2 (u1=s//32 0..31 high, u2=s%32 0..31 low), s_hat=32*u1_hat+u2_hat, exact_full=u1_hat==u1 and u2_hat==u2, reconciled_symbols for full 0..1023, not GF32-only.
- [x] **R63-02 NbLdpcShellResult not change signature**: IRRunResult signature zero change (git diff on base.py zero verifiable), new ShellResult wrapper aggregates without altering original signature, adapter returns ShellResult containing IRRunResult.
- [x] **R63-03 smoke INTEGRATION_REPLAY_SMOKE 90 fresh zero overlap**: Smoke 9 = INTEGRATION_REPLAY_SMOKE (V54-verified 43 among 3/source), Fresh 90 = INTEGRATION_FRESH_CANDIDATE (30/source=90), two registries frame_ids zero overlap verified (smoke intersect fresh = empty, both with V48-V54 used zero overlap).
- [x] **R63-04 domain gate DOMAIN_CALIBRATION_REQUIRED**: New session needs domain_check (P(B) chi2 / H(A|B)>0.05) then calibration P(U1|B)/P(U2|B,U1) then recompute m_total/m1, otherwise DOMAIN_CALIBRATION_REQUIRED blocks, same-domain 84d62779 still needs domain_check PASS but no calibration.
**R63 Lifecycle**: PLAN_REVISION_CANDIDATE / DECODER_FREE_INTEGRATION_SPIKE_COMPLETE / EXECUTE_NOT_AUTHORIZED decoder-free spike only, no run_01/real decoder/formal PA, 90-block only candidate registry.

