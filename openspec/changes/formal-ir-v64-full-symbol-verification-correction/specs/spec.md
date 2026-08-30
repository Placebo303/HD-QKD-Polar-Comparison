# OpenSpec Spec: formal-ir-v64-full-symbol-verification-correction

**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — 仅 plan 四工件，Phase A 未分流前禁止实现/运行 decoder，不改 V63 工件
**Change**: `formal-ir-v64-full-symbol-verification-correction` (`V64P0`, branch `formal-ir-mainline`, HEAD `TBD`, data SHA `84d62779`)
**Predecessor**: `formal-ir-v63-nbldpc-polar-shell-integration` (`5602f11c`, V63 二阶段 `Δ8+Δ8` 壳集成) — V64 仅改 verification 输入

## 1. 变更类型与生命周期

- **Type**: `VERIFICATION_CORRECTION` — NB-LDPC verification 语义修正（L2-only `tag(U2)` → full-symbol `tag(32*U1+U2)`），Phase A 只读归因 0 calls + Phase B 45 fresh 15/source 一次 decode 双口径仪器化对照（同次保存、不增 calls/泄漏），非 formal qualification/promotion/安全证明。
- **Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — 本轮止于 plan 四工件，**Phase A 归因记录完成（含 ATTRIBUTION_INCOMPLETE 的 fresh instrumentation 声明）后方可实现**，`DECODE_FORBIDDEN` 直至实现后授权前保持；正式 `run_01` 创建需独立 plan ACCEPT + EXECUTE_AUTH。
- **Branch**: `formal-ir-mainline`；`HEAD` `TBD` 实施前 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline` 重核，不一致阻塞；本次推送新 Plan SHA 后停止。
- **Data SHA**: `84d62779` (`84d62779603e62de50ded5182ed65b65d3dc6084`, `d=1024 bw=200 pairing=nearest rule=legacy_v1`) — 同域单点；fresh 45 仍该处理点零重叠。

## 2. 冻结方法（纠错完全冻结，仅 verification 输入修正）

### 2.1 纠错不变量（V63 完全冻结，V64 零改）

- `n =1024 symbols/block` (`4×256 frames`), `q =1024 (10-bit s=32*u1+u2, u1=s//32 0..31 high, u2=s%32 0..31 low)`, `log2 q =5 per plane`, `GF32 poly=37 (0b100101)`, `tag =64 bits/block 仍单 tag 仅 total 计一次`。
- `H1 = V31-H1-QC 16×1024 rank16 80b` 母矩阵；`L1-APP`: `p_i(u1)=P(U1|B_i) → BP_i=decode_row_layered_fftqspa(H1,p_i,s1).bp_posterior_beliefs → q_i=softmax(BP_i) → P_i(U2)=Σ q_i P(U2|B,u1)` (TRAIN prior `channel_counts.npz` via `load_v25_channel_counts()` 只读，不重估)。
- `Lane C` ordinal-2 `s38310x`：`m2 =184 (1M) /190 (1p5M) /192 (2M)`，`support/标签/置换/MET图` 全冻。
- `H_inc1 8×1024 det1` + `H_joint1 192/198/200×1024` nested；`H_inc2 8×1024 det2` + `H_total 200/206/208×1024` nested；`rank_joint1==m2+8`, `rank_total==m2+16`, `independence_1==8`, `independence_2==8`, `row≤16`, `col_inc≤1`, `E≈96`。
- `decoder`: `decode_row_layered_fftqspa` `max_iter=90, damping 1.0, early-stop`；`rescue 触发 = verification-only`。
- `leak`: `leak_base=5*m2+5*16+64 →1064/1094/1104`, `leak_stage1=leak_base+40 →1104/1134/1144`, `leak_stage2=leak_base+80 →1144/1174/1184` (`tag` 已含，不重复扣除，V64 不变)。
- `prior = TRAIN-only`，evaluation blocks 来自冻结 held-out (非 TRAIN)。

### 2.2 Verification 修正（V64 唯一变量，泄漏不增，单 tag 仪器化不变性）

- **Before (V63)**: `tag_scope=l2_only, tag_input=x2 (u2_hat[1024]), compute_tag_64(empty_uint8, x2) trunc64, verify_l2 = syndrome_ok && tag_ok_l2`
- **After (V64)**: `tag_scope=full_symbol, tag_input=s_hat=32*u1_hat+u2_hat (full 1024 symbols 0..1023), compute_tag_64(canonical, s_hat_packed) trunc64 复用同一 canonical, verify_full = syndrome_ok && tag_ok_full`
- **泄漏与 calls 不变**：`leak=5*m_total+64` 双校验 `m_total 184/190/192 +8/+16` 且 `stage1-base=40, stage2-stage1=40`；单 64-bit tag 仍仅 `total` 计一次，不因输入从 5-bit 扩到 10-bit 而增；**同次 decode 同时计算 L2-only 与 full tag 仍只计一个 64-bit tag，不增 calls/泄漏**。
- **双口径仪器化报告**：同一 `u1_hat/u2_hat` 解码输出**同次**并列计算 `tag_ok_l2` 与 `tag_ok_full` 且**同时保存** `exact_u1/l2/full、syndrome_ok_l1/l2、tag_ok_l2/tag_ok_full、errors_u1/u2、old/new accepted、stage/calls/leak`，`accepted_l2/accepted_full` 与 `undetected_l2/undetected_full` 对照，`Δ_accepted/Δ_undetected` 与 `被拦截U1-only wrong = count(!exact_u1&&exact_l2&&tag_ok_l2&&!tag_ok_full)` 诊断 L2-only 漏洞；**Phase B 不预设根因**。
- **s_hat 打包**：`s_hat = 32*u1_hat + u2_hat ∈ [0,1023]` 按 `compute_tag_64` canonical MSB-first 打包（与 V63 `x2` 打包一致路径，仅输入源扩大），seed 仍 64-bit Toeplitz，输出仍 64-bit trunc。
- **fresh 解释边界**：`U1 wrong+U2 exact+old accept+full reject→确认 verification-scope`；`U2 wrong+tag_ok→停止转 tag/canonical investigation`；`无 discordance→仅 full-tag performance signal，不得称已解释 V63 v63_dev_1M_0133`。
- **禁止**：第二 tag、重复计 tag、改 `m_total`、改 tag 长度、改 `m1/m2`、新增矩阵/阈值/decoder、双算计两次 tag/leak/calls。

### 2.3 外壳与 IR 接口（V64 继承 V63，不改）

- `FrameBatch(dataset_id, alice_symbols: np.ndarray[1024,1024), bob_symbols: np.ndarray[1024,1024), dimension=1024, frame_len_symbols=1024, metadata={source, block_id, frame_ids[4], held_out_ordinal_start/end, pairs_count, sampling_mode, session_id, provenance})` via `load_pairs_table→normalize→build_frame_batch`.
- `reconciled_symbols = 32*u1_hat+u2_hat (full s_hat 0..1023)` per frame；`IRRunResult` 签名不变，`ShellResult` 包装 `IRRunResult` 不改其字段。

### 2.4 禁止

- 禁改任一纠错冻结量、新增矩阵/标签/`prior`/阈值/`decoder`、试 `Δm=4/12/16` 多档、引入第二候选择优、用 outcomes 选行、调 `row_degree` 上限；违者 `EVIDENCE_INVALID`。
- 禁增泄漏（第二 tag / 重复计 tag / 改 `m_total` / 双算计两次 tag/leak/calls）；禁改 `src/experiments/tools` 任何文件（只读复用）；禁把 `L2-only` 冒充 `full-symbol`。
- 禁重估先验；禁跨域假同域；**禁在 `ATTRIBUTION_INCOMPLETE` 时直接沿用旧假设不经 fresh 仪器化而继续**（仅允许 `ATTRIBUTION_INCOMPLETE → Phase B fresh instrumentation confirmation（不预设根因、单 tag、同次保存）` 路径）；禁在 fresh 无 discordance 时宣称已解释 `v63_dev_1M_0133`。
- 未创建正式 `run_01` 前禁 `decode_*` 新增在 plan 侧（Phase A 零 calls，`DECODE_FORBIDDEN` 直至授权）。

## 3. Phase A — 只读归因 零 decoder 对 v63_dev_1M_0133（first-match 分流，不重跑）

### 3.1 输入与只读语义

- **输入路径**：`comparison_bench/outputs_comparison/formal_ir_methods/v63_nbldpc_polar_shell/run_01/` 下 `v63_dev_1M_0133` 块（`source=1M`），含 `v63_records.json/.csv` + `v63_summary.json` + `v63_shell_registry.json`。
- **只读**：仅 `Read` 已落盘 JSON/CSV，不调用 `decode_*`，不读 `pairs.parquet` 重解码，不写任何输出，不改 V63 目录；`decoder_calls==0` 硬校验。
- **核查字段**：`exact_u1 (=u1_hat==u1_true)`, `exact_l2 (=u2_hat==u2_true)`, `exact_full (=exact_u1&&exact_l2)`, `syndrome_ok_l1 (=H1*u1_hat==s1)`, `syndrome_ok_l2 (=H_L2*u2_hat==s_L2)`, `tag_ok_l2 (=tag_l2==tag_true_l2)`, `U1_errors, U2_errors, tag_scope, tag_input_hash, leak_actual`。

### 3.2 一致性校验

- `exact_full == (exact_u1 && exact_l2)` 恒等式；`syndrome_ok_l1/l2` 与 `H1/H_L2` 定义一致；`tag_ok_l2` 可追溯至 `compute_tag_64(empty,x2)`；`U1/U2_errors` 与 `exact_u1/l2` 互洽；`leak` 与 `m_total` 一致；任一缺失/矛盾 → `ATTRIBUTION_INCOMPLETE`。

### 3.3 三分支分流（first-match，最小修订新增 ATTRIBUTION_INCOMPLETE→fresh instrumentation 路径）

```
if fields_missing or inconsistent_definition or tag_scope != l2_only:
    branch = ATTRIBUTION_INCOMPLETE  # 无法拆解，不重跑 v63_dev_1M_0133，记录缺失字段；允许进入 Phase B fresh instrumentation confirmation（不预设根因，需仪器化声明）
elif U1_wrong && U2_exact && syndrome_ok_l2 && tag_ok_l2:
    branch = L2_TAG_INSUFFICIENT  # U1 wrong + U2 exact → L2-only tag 不足 → 进入 Phase B（verification-scope 待 fresh 确认）
elif U2_wrong && tag_ok_l2:
    branch = PAUSE_INVESTIGATE_TAG_ENCODING  # U2 wrong + tag_ok → 暂停调查 tag/encoding 链路，不进 Phase B
else:
    branch = ATTRIBUTION_INCOMPLETE  # 无法拆解，不重跑，但允许 fresh instrumentation（同第一分支）
```

- `L2_TAG_INSUFFICIENT` 与 `ATTRIBUTION_INCOMPLETE（fresh instrumentation）` 均允许进入 Phase B fresh instrumentation，但**后者不预设根因**且 `DECODE_FORBIDDEN` 保持至授权；`PAUSE_INVESTIGATE` 停止不进 Phase B；`ATTRIBUTION_INCOMPLETE` 不重跑 v63_dev_1M_0133、不猜测其根因；**直接继续沿用 U1 wrong+U2 exact 假设而不经 fresh 仪器化则违冻结分流**。

## 4. Phase B — 45 fresh blocks 15/source 一次 decode 双口径仪器化报告（2–4 calls/block 总 90–180，不预设根因，单 tag）

### 4.1 处理点单点冻结

- `84d62779` 语义：`dimension 1024, bin_width 200ps, pairing nearest, rule legacy_v1, channels A1/B5, frame_len 1024, pairs 1024, BLOCK_LENGTH 1024` — 单点。

### 4.2 规模与注册表

- `S=3, B=15, total 45`, 每块 `1024 symbols`；若 held-out 超集 `K>45` 则 `index_j=floor(j*(K-1)/14) j=0..14` 分散选 `15/source`，否则 `EVIDENCE_INVALID`。
- `v64_fresh_registry.json` (authoritative): `block_id, source(1M/1p5M/2M), frame_ids[4], held_out_ordinal_start/end, pairs_count 1024, BLOCK_LENGTH 1024, sampling_mode=deterministic_four_consecutive_frames_heldout_fresh_v64, held-out source_path, H provenance`。
- `frame_ids exact` 零重叠：`fresh ∩ V48–V63 ==∅` (含 `v63_smoke 9 + v63_dev 90`)，`fresh ∩ smoke ==∅`，`git diff` 可验；禁换块。
- `K2≥45` 且 `per-source≥15` 才合法，否则 `EVIDENCE_INVALID`。

### 4.3 三阶段协议（硬帽180, verification-only, 仅 full 口径触发，不预设根因，单 tag 仪器化）

```
per block (45 blocks, 15/source):
  prior = TRAIN prior (shared)
  L1: H1 s1 → BP → q → P(U2)  // 45 次总计，per block 1 (L1)
  base: decode_L2(H_base(m2), P(U2), s_base) → 同次保存 exact_u1/l2/full、syndrome_ok_l1/l2、tag_ok_l2+tag_ok_full双算、errors_u1/u2、old/new accepted、stage/calls/leak → verify_full_base = syndrome_ok && tag_ok_full ; verify_l2_base = syndrome_ok && tag_ok_l2 (双算仍单 64b tag 不增 calls/泄漏)
         if verify_full_base: final = base, leak = leak_base, stage=base
         else:
           s_inc1 = H_inc1*u2_true ; s_joint1=[s_base; s_inc1]
           stage1: decode_L2(H_joint1, P(U2), s_joint1) → 同次保存 exact_u1/l2/full、syndrome_ok_l1/l2、tag_ok_l2+tag_ok_full双算、errors_u1/u2、old/new accepted、stage/calls/leak → verify_full_stage1
           if verify_full_stage1: final = stage1, leak = leak_stage1
           else:
             s_inc2 = H_inc2*u2_true ; s_total=[s_base; s_inc1; s_inc2]
             stage2: decode_L2(H_total, P(U2), s_total) → 同次保存 exact_u1/l2/full、syndrome_ok_l1/l2、tag_ok_l2+tag_ok_full双算、errors_u1/u2、old/new accepted、stage/calls/leak → verify_full_stage2
             final = stage2, leak = leak_stage2
  record: exact_u1/l2/full, syndrome_ok_l1/l2, tag_ok_l2/tag_ok_full, errors_u1/u2, old/new accepted, stage/calls/leak, delta_tag_ok, intercepted_u1_only, same_decode_single_tag (不增开销断言)
budget: L1 45 + base45 + stage1≤45 + stage2≤45 =90–180 硬帽180 (L2 45–135)
leak: leak_base 1064/1094/1104, stage1 1104/1134/1144, stage2 1144/1174/1184 (tag 已含，不重复，双算不增泄漏)
fresh interpretation: U1 wrong+U2 exact+old accept+full reject → 确认 verification-scope；U2 wrong+tag_ok → 转 tag/canonical investigation；无 discordance → 仅 full-tag performance signal
```

- `rank_total==m2+16 nested/independence==8 row≤16` 已验；`leak_base/stage1/stage2` 三档已验；`base` 兼 old 不重复；**双口径为同次 decode 纯计算对照，不增 decoder_calls/泄漏**。
- 仅 `Phase A 归因记录完成（含 ATTRIBUTION_INCOMPLETE 的 fresh instrumentation 声明）+ 独立 plan ACCEPT + EXECUTE_AUTH` 后才允许创建正式实现并执行；`DECODE_FORBIDDEN` 直至授权。

### 4.4 预算

- `L1 45 + base45 + stage1≤45 + stage2≤45 =90–180 硬帽180 (L2 45–135)`，`per block 2–4 calls`。

## 5. Phase C — 门禁与终态（first-match，五选一，full 口径）

### 5.1 计数与分层（同次保存，单 tag 仪器化）

- `exact_full = exact_u1&&exact_l2` 与 `accepted_full = syndrome_ok&&tag_ok_full` 分别计数（overall 45 + per-source 15）；每 block **同次 decode 同时保存** `exact_u1/l2/full、syndrome_ok_l1/l2、tag_ok_l2/tag_ok_full、errors_u1/u2、old/new accepted、stage/calls/leak`；`undetected_full = syndrome_ok&&tag_ok_full&&!exact_full` 单独表；`undetected_l2` 仅对照；`disclosure` 三档按实际 `stage_used` (以 full verification 触发计)；`calls/rescue` 按 `!verify_full_base` / `!verify_full_base&&!verify_full_stage1` 分母（以 full 口径计）；`被拦截U1-only wrong` 单独计数；**双算仍单 64b tag 不增 calls/泄漏**。
- 各源各自 `base/stage1/final (accepted_full vs exact_full 分别 + L2-vs-full Δ + 同次保存字段)` 与 `leakage/rescue_rate/runtime/stage_used/被拦截U1-only` 分别报告；`base/stage1` 仅分层报告不作主判；门禁仅 `final` full 口径。

### 5.2 预注册终态（first-match，互斥，ATTRIBUTION_INCOMPLETE fresh 仪器化修订）

```
if rank/nested/verification/记账/域/重叠/预算/泄漏/all_exact_tag_ok_full/tag_input_full_correct 检查失败:
    overall = V64_EVIDENCE_INVALID  # 优先（不因 attribution 绕过）
elif attribution_result == ATTRIBUTION_INCOMPLETE and fresh_instrumentation_not_yet_executed:
    overall = V64_PLAN_CANDIDATE__ATTRIBUTION_INCOMPLETE_FRESH_INSTRUMENTATION_DESIGN_DONE  # 仅 plan，允许 fresh 仪器化（DECODE_FORBIDDEN）
elif exact_full >=35/45 ∧ per_source exact_full >=10/15 ∧ undetected_full_tag==0 ∧ all exact frames tag_ok_full==True ∧ rank/nested/预算/泄漏通过
       → V64_FULL_SYMBOL_VERIFICATION_PASS  # 若 attribution==INCOMPLETE 且 fresh 无 old vs new discordance，则 claim 限为 full-tag performance signal，不得称已解释 v63_dev_1M_0133
elif fresh shows U2_wrong && tag_ok_full (exact_l2==False && tag_ok_full==True):
       → V64_PAUSE_TAG_CANONICAL_INVESTIGATION  # 停止转 tag/canonical investigation，不判 PASS
elif exact_full >0 and (undetected_full_tag!=0 or not all_exact_tag_ok_full):
       → V64_CORRECTION_WORKS_VERIFICATION_STILL_FAILS  # 纠错有信号但 full verification 仍有 undetected/漏拦截
elif exact_full <35/45 or per_source <10/15:
       → V64_CORRECTION_PERFORMANCE_FAIL
else → V64_EVIDENCE_INVALID
```

- `PASS` 需 `overall exact_full≥35/45 (77.78%)` 且 `per-source ≥10/15 (66.7%)` 且 `undetected_full_tag==0` 且 `所有 exact_full 帧 tag_ok_full==True` 且 `rank/nested/verification/记账/域/预算/泄漏` 通过；`exact_full` 与 `accepted_full` 分别达标（禁相等假定）；**ATTRIBUTION_INCOMPLETE 下的 fresh PASS 若无 discordance 仅为 performance signal**。
- `PAUSE_TAG_CANONICAL_INVESTIGATION`: fresh 出现 `U2 wrong+tag_ok`（含 `tag_ok_full`）时进入，不判 PASS/FAIL，转 tag/canonical 调查。
- `CORRECTION_WORKS_VERIFICATION_STILL_FAILS`: `exact_full>0` 但 `undetected_full!=0` 或 `exact tag 未全过`。
- `CORRECTION_PERFORMANCE_FAIL`: `exact_full<35/45` 或 `per-source<10/15`。
- `ATTRIBUTION_INCOMPLETE`: Phase A 无法拆解/字段缺失/口径矛盾，不重跑 v63_dev_1M_0133；**但允许 fresh instrumentation confirmation（不预设根因，同次保存、单 tag）**。
- `EVIDENCE_INVALID` 优先于所有性能终态。

### 5.3 双口径仪器化对照与拦截数

- `L2-only vs full 差异表`: `Δ_accepted, Δ_undetected, Δ_tag_ok` per source & overall（基于同次保存的 `tag_ok_l2/tag_ok_full`）；`被拦截U1-only wrong` 数量 `=count(!exact_u1&&exact_l2&&tag_ok_l2&&!tag_ok_full)`（需 `old accept && full reject`）为确认 verification-scope 的 fresh 仪器化核心对照；若 `U2 wrong+tag_ok` 则计数转 `tag/canonical investigation`；若无 discordance 则仅 `full-tag performance signal`。
- `Wilson 95%` per source & overall 仅报告，不作门禁。

## 6. 与 V63/V54 衔接与守卫

- `V63` 工件只读，不覆写 `comparison_bench/outputs_comparison/formal_ir_methods/v63*` 任何文件；`V64` fresh registry 与 `V48–V63` 已用 `frame_ids` 零重叠可验。
- `V54` 二阶段 `Δ8+Δ8` 为本纠错唯一臂；不改 `V54 registry` 与终态，不继续 `V54 run_01`。
- 守卫：`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0 && git diff -- openspec/changes/formal-ir-v6[0-2,3]/ ==0` (除本变更外零改)，`py_compile PASS`，`HEAD==origin` 已验，`run_01` 不存在，Phase A 零 calls 已验，verification 单 tag 同次保存不增 calls/泄漏已验，`DECODE_FORBIDDEN` 保持已验。
- 本轮仅 plan 四工件，不创建正式输出；任何 fresh decode 需 `Phase A 归因记录完成（含 ATTRIBUTION_INCOMPLETE 的 fresh instrumentation 声明）+ 独立 plan ACCEPT + EXECUTE_AUTH`。

## 7. 证据写出（预冻结，未来执行）

- 固定增量根（decoder 前建，fail-closed）：`comparison_bench/outputs_comparison/formal_ir_methods/v64_full_symbol_verification/run_attribution/` (Phase A 0 calls) 与 `/run_fresh_45/` (Phase B 45-block)。
- 文件：`v64_attribution.json` (Phase A, 0 calls) + `v64_records.json/.csv` (Phase B `45–135` L2行；总 calls `90–180` 硬帽180)、`v64_summary.json`（分层含双口径对照与 U1-only 拦截）、`v64_fresh_registry.json` (authoritative 45)、`v64_invalid_notice.json` (失败时)、`v64_data_readiness.json` (G1-G5)。CSV/JSON 行对等；禁写 NPZ。本轮仅冻结计划，不创建输出。
