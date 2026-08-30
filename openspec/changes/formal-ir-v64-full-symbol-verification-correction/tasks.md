# OpenSpec Tasks: formal-ir-v64-full-symbol-verification-correction — V64 全符号 verification 修正

**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **仅 plan 四工件，Phase A 未分流前禁止实现/运行 decoder，不改 V63 工件，不改纠错参数**
**HEAD**: `TBD` (branch `formal-ir-mainline`, 实施前以 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline` 重核，不一致阻塞) + data SHA `84d62779` (200ps legacy_v1 nearest 1024, q1024)
**Predecessor**: `formal-ir-v63-nbldpc-polar-shell-integration` `5602f11c` (V63 二阶段 `Δ8+Δ8` 已冻) — V64 仅改 verification 输入
**Boundary**: 每 block 1024 symbols (`4×256 frames`), `GF32 log2q=5`, `tag=64 full_symbol` 仍单 tag 仅 `total` 计一次；`H1/Lane C/H_inc/Δ/decoder 90/1.0 poly37` 全冻；泄漏 `1064→1144/1174` 不变

## Phase A — 只读归因 零 decoder 对 v63_dev_1M_0133 核查（不重跑，不改 V63）

- [ ] **A1 fetch 与 HEAD 自检（阻塞门）**：`git fetch origin && git rev-parse HEAD == origin/formal-ir-mainline` 完整 40 位重核，不一致则阻塞；记录 `HEAD/origin/implementation SHA` 至报告 `provenance`，`rg "v63_dev_1M_0133" 仅在 V63 工件内 hits` 已验，`data SHA 84d62779` 已记录，`V63 工件路径只读校验` (`v63_records.json/.csv 存在且非空`)
- [ ] **A2 Phase A 输入只读盘点（零 decoder，不改 V63）**：对 `comparison_bench/outputs_comparison/formal_ir_methods/v63_nbldpc_polar_shell/run_01/` (或 `v63_dev_*` registry 指向的) `v63_dev_1M_0133` 块执行只读 `Read` 盘点：`block_id=0133, source=1M, frame_ids[4], held_out_ordinal, pairs_count 1024, BLOCK_LENGTH 1024, sampling_mode, exact_u1, exact_l2, exact_full, syndrome_ok_l1, syndrome_ok_l2, tag_ok_l2, tag_scope=l2_only, U1_errors, U2_errors, s_hat vs s_true 可追溯`，记录 `file:line:field` 每项，`git diff -- comparison_bench/outputs_comparison/formal_ir_methods/v63* ==0` 零改已验，`rg "decode_row_layered_fftqspa" 在 Phase A 输入侧 0 hits` (仅冻结模块内 hits 已验)
- [ ] **A3 归因字段一致性校验（decoder-free 公式校验）**：校验 `exact_full == (exact_u1 && exact_l2)` 恒等式；校验 `syndrome_ok_l1 = H1*u1_hat==s1` 与 `syndrome_ok_l2 = H_L2*u2_hat==s_L2` 定义一致性；校验 `tag_ok_l2 = tag(U2)==tag_true` 的 `compute_tag_64(empty,x2) trunc64` 输入可追溯；校验 `U1_errors = count(u1_hat!=u1_true)` 与 `U2_errors` 与 `exact_u1/l2` 互洽；校验 `leak 三档 1064/1094/1104` 与 `m_total` 一致；任一字段缺失/口径矛盾 → 直接 `ATTRIBUTION_INCOMPLETE` 不重跑
- [ ] **A4 三分支分流冻结（first-match，零 decoder）**：
  ```
  if fields_missing or inconsistent_definition or tag_input_not_l2_only:
      overall = V64_ATTRIBUTION_INCOMPLETE  # 无法拆解，不重跑，记录缺失字段
  elif U1_wrong && U2_exact && syndrome_ok_l2 && tag_ok_l2:
      # exact_u1==False && exact_l2==True && syndrome_ok_l2==True && tag_ok_l2==True
      overall = V64_ATTRIBUTION_L2_TAG_INSUFFICIENT  # L2-only tag 不足以拦截 U1-only 错误 → 进入 Phase B 修正验证
  elif U2_wrong && tag_ok_l2:
      # exact_l2==False && tag_ok_l2==True
      overall = V64_ATTRIBUTION_PAUSE_INVESTIGATE_TAG_ENCODING  # 暂停，调查 tag/encoding 链路（含 H/m2/syndrome/tag_input/decoder 一致性），不进 Phase B
  else:
      overall = V64_ATTRIBUTION_INCOMPLETE  # 无法拆解，不重跑
  ```
  三分支已显式，`U1 wrong+U2 exact→进 Phase B` 与 `U2 wrong+tag_ok→暂停调查` 与 `无法拆解→ATTRIBUTION_INCOMPLETE` 互斥已验；`Phase A 零 calls` 已验 (`decoder_calls==0` 且无 `decode_*` 新增)
- [ ] **A5 归因报告预冻结（v64_attribution.json Schema）**：预冻结 `v64_attribution.json` 含 `block_id=0133, source=1M, frame_ids, exact_u1/l2/full, syndrome_ok_l1/l2, tag_ok_l2, U1_errors, U2_errors, tag_scope=l2_only, tag_input_hash, leak_actual, attribution_branch∈{L2_TAG_INSUFFICIENT, PAUSE_INVESTIGATE, INCOMPLETE}, next_action∈{enter_Phase_B, pause_investigate, stop}, decoder_calls=0, provenance`，仅 Phase A 归因通过 `L2_TAG_INSUFFICIENT` 才允许 Phase B 进入（否则 `ATTRIBUTION_INCOMPLETE` 或 `PAUSE` 停止，不伪造）

## Phase B — 45 fresh blocks 15/source 2–4 calls 总 90–180，一次 decode 双口径报告（冻结 V63 全部纠错参数，仅 verification 改 full-symbol）

- [ ] **B1 纠错参数零改冻结（V63 继承，泄漏不增）**：冻结 `H1-16 rank16 / L1APP q_i=softmax(BP_i) via H1 (TRAIN prior) / Lane C support/标签/置换/MET图 ordinal-2 s38310x m2 184/190/192 / H_inc1 8×1024 det1 / H_joint1 192/198/200 / H_inc2 8×1024 det2 / H_total 200/206/208 / decoder 90/1.0 poly37 early-stop / TRAIN-only prior / verification-only 触发 / Δ8+Δ8 / leak_base 1064/1094/1104 leak_stage1 1104/1134/1144 leak_stage2 1144/1174/1184 (+40/+80)` 全冻，不新增矩阵/标签/prior/阈值/decoder，`git diff -- comparison_bench/src/comparison_bench/formal_ir/v54* ==0` 已验
- [ ] **B2 Verification 修正冻结（唯一变量，单 64-bit tag 泄漏不增）**：冻结 `tag_scope: l2_only → full_symbol`, `tag_input: x2 (u2_hat) → s_hat = 32*u1_hat + u2_hat (0..1023)`, `compute_tag_64(empty,x2) → compute_tag_64(canonical, s_hat_packed) trunc64 复用同一 canonical`，`leak =5*m_total+64` 双校验 `m_total 184/190/192 +8/+16` 且 `stage1-base=40, stage2-stage1=40` 仍 PASS，单 tag 64b 不重复已验，`verification = syndrome_ok && tag_ok_full` 为门禁口径已验
- [ ] **B3 双口径报告冻结（一次 decode 双验证）**：冻结同一 `u1_hat/u2_hat` 解码输出并列计算 `tag_ok_l2 (=tag(U2)==tag_true_l2)` 与 `tag_ok_full (=tag(32*U1+U2)==tag_true_full)`，`accepted_l2 = syndrome_ok&&tag_ok_l2` vs `accepted_full = syndrome_ok&&tag_ok_full`，`undetected_l2 = syndrome_ok&&tag_ok_l2&&!exact_full` vs `undetected_full = syndrome_ok&&tag_ok_full&&!exact_full`，`Δ_accepted/Δ_undetected/Δ_tag_ok` per source & overall 对照表，`被拦截U1-only wrong = count(!exact_u1&&exact_l2&&tag_ok_l2&&!tag_ok_full)`，所有 exact_full 帧 `tag_ok_full==True` 恒真校验 (否则 `EVIDENCE_INVALID`)
- [ ] **B4 Fresh 规模与注册表冻结（45=15/source，零重叠）**：冻结 `S=3, B=15, total 45`, 每块 `1024 symbols (4×256 frames)`, 枚举剩余非重叠四连续窗口（`start 0..H-4 per source, H=400/554/729, base=1600/2213/2916`），过滤与已用 `V48/V50/V51/V52/V53/V54/V63`（含 `v63_smoke 9 + v63_dev 90`）重叠者得 `K2`，按 `ordinal` 排序后以 `index_j=floor(j*(K2-1)/14) j=0..14` 分散选 `15/源`，落盘 `v64_fresh_registry.json` ( authoritative, `block_id, source, frame_ids[4], held_out_ordinal_start/end, pairs_count 1024, BLOCK_LENGTH 1024, sampling_mode=deterministic_four_consecutive_frames_heldout_fresh_v64, held-out source_path, H provenance`)，若 `K2<45` 或 `per-source<15` 则 `EVIDENCE_INVALID` 停止；`frame_ids exact` 零重叠已验 (`smoke∩fresh==∅ && fresh∩V48-63==∅`)
- [ ] **B5 可重放性校验（hash 比对，decoder-free prep）**：对每块 `source_path` 的 `pairs.parquet` 执行 `load_pairs_table→normalize_pair_columns→build_frame_batch(q=1024,frame_len=1024)` 无损恢复，校验 `alice_symbol/bob_symbol ∈ [0,1024)` 且 `s = alice_symbol, u1_true=s//32, u2_true=s%32` 可分解且 `hash(s_hat)` 可追溯已验
- [ ] **B6 H 矩阵冻结校验（decoder-free）**：`reconstruct_v64_matrices` (复用 v63/v54) 对 `H1-16 rank16 + Lane C m2 184/190/192 + H_inc1 det1/H_joint1 192/198/200 + H_inc2 det2/H_total 200/206/208` 校验 `rank_total==m2+16, nested, independence==8, row≤16, col_inc≤1, E≈96, leak+40+40` 全 PASS
- [ ] **B7 预算冻结（45 fresh 硬帽180）**：冻结 `L1 45 + base45 + stage1≤45 + stage2≤45 =90–180 硬帽180 (L2 45–135)`，`per block 2–4 calls`，`verification-only` 触发已验，`base` 兼 old 不重复；`未达硬帽180` 已验
- [ ] **B8 未对齐停止**：若 `K2<45` 或 `pairing/dimension/bw` 不一致或 `H 矩阵校验失败` 或 `Phase A 非 L2_TAG_INSUFFICIENT`，则 `EVIDENCE_INVALID` 或 `ATTRIBUTION_INCOMPLETE` 停止，不伪造，不进 Phase B decode

## Phase C — 门禁五态与 layered 报告（frozen，first-match）

- [ ] **C1 主指标冻结（门禁分层，双口径）**：冻结 `exact_u1 / exact_l2 / exact_full (=exact_u1&&exact_l2) 分别计数（overall 45 + per-source 15）` + `syndrome_ok / tag_ok_l2 / tag_ok_full` + `accepted_l2/accepted_full` + `undetected_full 单独表 (syndrome_ok&&tag_ok_full&&!exact_full)` + `undetected_l2 对照` + `被拦截U1-only wrong` + `disclosure bits/block 三档 + per_source_avg[s]=leak_base[s]+40*N_stage1_full[s]/15+40*N_stage2_full[s]/15 + overall_avg=(Σ leak_base+40*N_stage1+40*N_stage2)/45 + per accepted_full = total_disclosed / accepted_full_count` + `calls/rescue(N_stage1_attempted=count(!verify_full_base), N_stage2_attempted=count(!verify_full_base&&!verify_full_stage1), rescued_stage1/2, rescue_rate= rescued/attempted)` + `runtime/throughput + stage_used 分布 + Wilson 95%`，`exact_full` 与 `accepted_full` 需分别达标
- [ ] **C2 门禁冻结（V64 PASS 四条件 + EVIDENCE_INVALID 优先）**：
  ```
  if not attribution_complete or not tag_input_full_correct or rank/nested/verification/记账/域/重叠/预算/泄漏检查失败 or not all_exact_tag_ok_full:
      overall = V64_EVIDENCE_INVALID  # 优先
  elif attribution_result == ATTRIBUTION_INCOMPLETE or attribution_not_L2_insufficient:
      overall = V64_ATTRIBUTION_INCOMPLETE  # Phase A 无法拆解，不重跑
  elif exact_full >=35/45 ∧ per_source exact_full >=10/15 ∧ undetected_full_tag==0 ∧ all exact frames tag_ok_full==True ∧ rank/nested/预算/泄漏通过:
      overall = V64_FULL_SYMBOL_VERIFICATION_PASS
  elif exact_full >0 and (undetected_full_tag!=0 or not tag_all_exact_pass):
      overall = V64_CORRECTION_WORKS_VERIFICATION_STILL_FAILS  # 纠错有信号但 full verification 仍有 undetected 或 exact tag 未全过
  elif exact_full <35/45 or per_source <10/15:
      overall = V64_CORRECTION_PERFORMANCE_FAIL
  else:
      overall = V64_EVIDENCE_INVALID
  ```
  `G1 exact_full≥35/45 overall, G2 每源≥10/15, G3 undetected_full_tag==0, G4 所有 exact 帧 tag_ok_full==True` 已显式，不因 V63 差值改阈值，`rank/nested/记账/预算` 优先于性能门禁已验
- [ ] **C3 双口径对照与 U1-only 拦截冻结**：冻结 `L2-only vs full 差异表 (Δ_accepted, Δ_undetected, Δ_tag_ok per source & overall)` + `被拦截 U1-only wrong 数量 = count(!exact_u1&&exact_l2&&tag_ok_l2&&!tag_ok_full)` + `L1/L2 exact 提升对照` + `paired delta per block base vs stage1 vs final (以 full verification 为准)`，`U1-only 拦截` 为诊断 V63 漏洞的关键对照已验
- [ ] **C4 零改校验（H/prior/decoder/增量/泄漏）**：`H1-16 rank16, Lane C m2 184/190/192, H_inc1 det1 + joint1, H_inc2 det2 + total, decoder 90/1.0 poly37, TRAIN-only, full-symbol tag 单64b, +40/+80` 全冻，不新增矩阵，不试 `Δm=4/12/16` 多档，不以 outcomes 选行，已验
- [ ] **C5 pair delta 与分层报告冻结**：冻结 `per block base vs stage1 vs final (accepted_full/exact_full) 差异 + leak delta per source + Wilson 95% per source & overall + runtime/throughput/stage_used 分布` overall+per-source，三源分别不平均已验

## Phase D — 交付与推送（PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED，普通推送后停止）

- [ ] **D1 四工件一致性自检（gate）**：`py_compile PASS`，`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0 && git diff -- openspec/changes/formal-ir-v6[0-2,3]/ ==0`（除本变更外零改），`V63 工件零改` (`git diff -- comparison_bench/outputs_comparison/formal_ir_methods/v63* ==0`) 已验，`三源 leak_without_tag/tag 不重复`已验，`GF32 5bits` 已验，不跨源平均已验，`门禁 35/45 & 10/15 & undetected_full==0` 已验，`Phase A 零 calls` 已验，`verification 单 tag 泄漏不增`已验，`HEAD==origin` 已验，`run_01` 不存在已验，`ATTRIBUTION_INCOMPLETE 时不进 Phase B` 已验
- [ ] **D2 普通推送新 Plan SHA 并停留 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`**（基于 `TBD` 绑定后新 Plan SHA），未创建任何 `run_01` decoder 执行，不碰 `V54/V63 m/leak`，`src//experiments//tools//V63` 零改，普通推送（非 force）至 `formal-ir-mainline`，推送后等待独立审核（`Pre-RESULT` 独立线程复核 `HEAD/ACCEPTED_PLAN_SHA/rg 0 hits/run_01不存在/py_compile+关键测试 PASS`），`V64` 仍 `PLAN_CANDIDATE`，返回 `Plan SHA / implementation SHA / attribution 分流 / fresh registry / 终态`，**不自动进入 Phase B fresh 执行，不实现正式 v64 模块**

## 本变更显式禁止

decoder 调用在 plan 侧新增（Phase A 零 calls 硬门禁）；改 `V63 m1/m2/leak` 或 `H1/Lane C/Δ/decoder` 冻参或新增矩阵；增第二 tag 或改 `tag 长度/重复计 tag`；改 `LDPC` 码族；重跑 V63 decoder；自创 `H_min / finite-key / composable` 公式或造 `eps_sec/eps_cor/vis/phase-error` 参数；用旧数据伪造 fresh 同域（无 `frame_ids zero overlap` 校验时伪造 `v64_fresh_registry.json`）；重复扣除 `tag 64`；将总体平均掩盖单源阈值；网格调参；把 V55 `frames×256` 非 legacy_v1 输入当 1024-block；宣称 `FER/SKR/阈值/晋升/安全证明`；创建正式 `run_01` decoder 执行；改 `src//experiments//tools//V63`；在 `ATTRIBUTION_INCOMPLETE` 时仍进入 Phase B；实现正式 v64 模块/启动 fresh decode（本轮仅 4 工件，普通推送新 Plan SHA 后停止）。

## 验收

- proposal/design/tasks/specs 一致 HEAD `TBD`→新 Plan SHA 84d62779 lifecycle PLAN_CANDIDATE EXECUTE_NOT_AUTHORIZED；Phase A 只读归因零 decoder 三分支分流已冻结，`v63_dev_1M_0133` 字段清单与 `ATTRIBUTION_INCOMPLETE 不重跑` 已验，V63 工件零改已验
- Phase B 纠错参数全冻仅 verification 改 `tag(32*U1+U2) 复用 compute_tag_64 canonical 仍单64-bit 泄漏不增` 双口径报告已验，fresh `15/source=45 blocks, 90–180 calls 硬帽180 (L2 45–135)` 零重叠已验，三档泄漏不变已验
- Phase C 门禁 `35/45 & 10/15 & undetected_full_tag==0 & 所有 exact 帧 full tag 通过 & 预算泄漏矩阵通过` 已显式，五态 `FULL_SYMBOL_VERIFICATION_PASS / CORRECTION_WORKS_VERIFICATION_STILL_FAILS / CORRECTION_PERFORMANCE_FAIL / ATTRIBUTION_INCOMPLETE / EVIDENCE_INVALID` 互斥 first-match 已验，双口径 `L2-only vs full` 差异与 `被拦截U1-only wrong` 与分层 `calls/泄漏/runtime per-source` 已冻结
- Phase D `py_compile` PASS 未建 `run_01` 未进 Phase B 执行 未重跑 V63 未改 `V54/V63` 已普通推送新 Plan SHA `PLAN_CANDIDATE/EXECUTE_NOT_AUTHORIZED` 仅改本目录（`src//experiments//tools//V63` 零改），`HEAD==origin` 已验，推送后等待独立审核，**不自动进入 Phase B fresh 执行，不实现正式 v64 模块**
