# OpenSpec Proposal: formal-ir-v64-full-symbol-verification-correction

**Status**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — 仅产出计划四工件，不实现/不执行 decoder，不创建 run_01，等待独立复审与显式授权
**Domain**: Formal IR / NB-LDPC verification semantics correction (L2-only → full-symbol)
**Change ID**: `formal-ir-v64-full-symbol-verification-correction`
**Cycle ID**: `V64P0` (full-symbol-verification-correction), predecessor `formal-ir-v63-nbldpc-polar-shell-integration` (HEAD `5602f11c` revision, `PLAN_CANDIDATE / DECODER_FREE_INTEGRATION_SPIKE_COMPLETE / EXECUTE_NOT_AUTHORIZED`)
**Branch**: `formal-ir-mainline`
**HEAD**: `TBD` (实施前以 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline` 40位重核，不一致阻塞；本次推送新 Plan SHA 后停止)
**Data SHA**: `84d62779` (`84d62779603e62de50ded5182ed65b65d3dc6084`, `d=1024 bw=200ps pairing=nearest rule=legacy_v1` 同 V54/V63 单点；fresh 45 blocks 仍同域该处理点)
**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — 本轮止于 plan 四工件，不改 V63 工件，不运行 decoder

> ponytail lite: 本变更仅 4 OpenSpec 工件（proposal/design/tasks/specs），零新增 decoder/矩阵/依赖（`numpy/pandas/pyarrow` 已装）；laziest alternative: 若 Phase A 无法拆解归因，直接落盘 `ATTRIBUTION_INCOMPLETE` 停止，不伪造重跑。

> **研究目标**：在完全冻结 V63 纠错参数的前提下，修正 verification 从 `tag(U2)` L2-only 到 `tag(32*U1+U2)` 全符号的工程语义缺陷；Phase A 对 `v63_dev_1M_0133` 做零 decoder 只读归因分流，Phase B 以 45 fresh blocks (15/source) 一次 decode 双口径对照验证修正是否生效，并以冻结门禁判定五态终态。

## Goal

在不改 V63 纠错能力、不增泄漏的前提下，完成 verification 语义修正的计划冻结与判定框架：

1. **Phase A 只读归因（零 decoder，不重跑）**：对单块 `v63_dev_1M_0133` 的已落盘产物做只读核查 `exact_u1 / exact_l2 / syndrome_ok_l1 / syndrome_ok_l2 / tag_ok_l2 / U1_errors / U2_errors`，按以下 first-match 分流 — `U1 wrong + U2 exact → L2-only tag 不足以拦截 U1-only 错误，进入 Phase B 修正`；`U2 wrong + tag_ok_l2 → 暂停，调查 tag/encoding 链路（含矩阵/decoder/tag 输入一致性）`；`无法拆解（字段缺失/口径不一致/矛盾）→ ATTRIBUTION_INCOMPLETE 不重跑`。Phase A 不调用任何 decoder，不新增泄漏/矩阵/先验，不改 V63 工件。

2. **Phase B 修正验证（45 fresh blocks，15/source，2–4 calls/block 总 90–180）**：冻结 V63 全部纠错参数 `H1-16 / L1APP (Lane C) / TRAIN prior via V25 channel_counts.npz / decoder 90/1.0 poly37 early-stop / Lane C support/标签/置换/MET图 ordinal-2 s38310x m2 184/190/192 / H_inc1 8×1024 det1 / H_joint1 192/198/200 / H_inc2 8×1024 det2 / H_total 200/206/208 / 泄漏 base 1064/1094/1104 stage1 1104/1134/1144 stage2 1144/1174/1184 (+40/+80)` 零改，**仅 verification 从 `tag(U2)=compute_tag_64(empty,x2)` 改为 `tag(32*U1+U2)=compute_tag_64(canonical, 32*u1_hat+u2_hat)`，复用 `comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py::compute_tag_64` canonical 仍单 64-bit tag，泄漏不增**。一次 decode 双口径报告：同一解码输出同时计算 `tag_ok_l2` (L2-only) 与 `tag_ok_full` (full-symbol) 作对照，门禁以 `full` 为准。

3. **门禁 V64 PASS 冻结**（需同时满足，否则非 PASS）：
   - `exact_full == (exact_u1 && exact_l2) >=35/45 overall 且每源 >=10/15`
   - `undetected_full_tag == count(syndrome_ok && tag_ok_full && !exact_full) == 0`
   - `所有 exact_full 帧的 full tag 必通过` (exact → tag_ok_full 恒真，否则 EVIDENCE_INVALID)
   - `预算 90–180 hard cap / 泄漏三档矩阵 (rank_total==m2+16, nested, independence==8, row≤16, col_inc≤1, leak=5*m_total+64 双校验)` 全 PASS
   - 同时报告 `L2-only vs full 差异`、`被拦截 U1-only wrong 数量 (exact_u1==False && exact_l2==True && tag_ok_full==False 计数)`、`分层 calls/泄漏/runtime per-source` (overall + per-source)。

4. **终态五选一互斥**（first-match）：
   - `FULL_SYMBOL_VERIFICATION_PASS` (满足全部 PASS 条件)
   - `CORRECTION_WORKS_VERIFICATION_STILL_FAILS` (纠错有信号但 full verification 未全过)
   - `CORRECTION_PERFORMANCE_FAIL` (性能未达 35/45 或 per-source 10/15)
   - `ATTRIBUTION_INCOMPLETE` (Phase A 无法拆解或 Phase B 前置归因缺失)
   - `EVIDENCE_INVALID` (rank/nested/verification/记账/域/预算/泄漏/重叠 失败优先)

**报告承诺（shall）**：proposal/design/tasks/specs 显式承诺 — 若未来执行 Phase B，最终报告 SHALL 按 `overall + per-source` 分别包含 `exact_u1 / exact_l2 / exact_full 三计数 + syndrome_ok/tag_ok_l2/tag_ok_full 三验证 + undetected_full_tag 单独表 + disclosure bits/block 三档分布(actual_disclosure_bits per frame + per accepted) + L2-only vs full 差异对照表 + 被拦截 U1-only wrong 数量 + calls/rescue(N_stage1/N_stage2/rescue_rate) + runtime/throughput + stage_used 分布(base/delta8/delta16) + PA 输入泄漏明细 + full tag 输入可追溯性`；门禁仅用 `exact_full + undetected_full_tag==0`，secondary 仅描述性；泄漏分解不一致时跨方法对比失效。

## Non-Goals

- 不改 V63 任何纠错参数：`H1-16 / L1APP / Lane C support/标签/置换/MET图 ordinal-2 s38310x m2 184/190/192 / H_inc1 det1 / H_joint1 / H_inc2 det2 / H_total / decoder 90/1.0 poly37 / TRAIN prior / 泄漏 1064→1144/1174 1184` 任一量，新增即 `EVIDENCE_INVALID`；不新增矩阵/标签/prior/阈值/decoder 候选。
- 不增泄漏：`tag` 仍单 64-bit trunc64，仅改输入从 `x2` 到 `32*u1+u2`，`leak=5*m_total+64` 公式不变，`+40/+80` 不变；不重复计 tag，不做第二 tag。
- 不重跑 V63 `v63_dev_1M_0133` 的 decoder：Phase A 仅只读已落盘 `v63_records.json/.csv + v63_summary.json + v63_shell_registry.json` 产物，零 calls；Phase B 用 fresh 45 blocks 独立运行，不覆盖 V63 输出。
- 不修改 `src/ experiments/ tools/` 任何文件（冻结基线只读；`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0` 语义）；不改 `comparison_bench` 已有纠错模块签名，仅新增 verification 输入封装。
- 不创建正式 `comparison_bench/outputs_comparison/formal_ir_methods/v64_*/run_01` 或执行 decoder（本轮仅 plan 四工件，`py_compile PASS`，`rg "decode_"` 仅在冻结模块内，SP 未新增 decoder）。
- 不继续 `V61/V60` 数值、有限密钥网格、或 V55 `frames×256` 非 `1024-block legacy_v1` 输入；不改 `V38–V64` 既有输出与终态（V63 工件只读）。
- 不做 `FER/阈值/资格/晋升/安全证明` 的扩大陈述；`tag` 仍 `≈2^-64` 工程近似；不宣称 composable/有限密钥证明。
- 不伪造 fresh 域：无相同 `1024-block legacy_v1` 可重放时直接判 `EVIDENCE_INVALID` 或 `ATTRIBUTION_INCOMPLETE` 停止，不以 `SER/vis` 代理冒充。

## Scope

1. **冻结 NB-LDPC 纠错方法（完全冻结，零改，V63 complete 继承 V54）**：`n=1024, m2 184/190/192, GF32 poly37, H1 16×1024 rank16 80b, L1-APP q_i=softmax(BP_i) via BP_i=decode_row_layered_fftqspa(H1,p_i,s1).bp_posterior_beliefs (TRAIN prior), Lane C ordinal-2, H_inc1 8×1024 det1 + H_joint1 192/198/200, H_inc2 8×1024 det2 + H_total 200/206/208, decoder 90/1.0 poly37 early-stop, 泄漏 base 1064/1094/1104 stage1 1104/1134/1144 stage2 1144/1174/1184 (+40/+80), TRAIN-only, verification-only 触发`。`exact_full=exact_u1&&exact_l2` oracle 隔离，`undetected` 单独；V64 仅改 verification 输入。

2. **Verification 修正（唯一变量）**：
   - **Before (V63)**：`tag_scope=l2_only, tag_input=x2 (u2_hat 1024 symbols), compute_tag_64(empty_uint8, x2) trunc64, verify = syndrome_ok && tag_ok_l2`
   - **After (V64)**：`tag_scope=full_symbol, tag_input=32*u1_hat+u2_hat (full 1024 symbols 0..1023, 10-bit s_hat), compute_tag_64(canonical, s_hat_packed) trunc64, verify_full = syndrome_ok && tag_ok_full`，复用 `compute_tag_64` canonical 仍单 64-bit tag，`leak` 不变
   - **双口径报告**：同一 `u1_hat/u2_hat` 解码输出同时计算 `tag_ok_l2` 与 `tag_ok_full`，对照表记录 `Δ = tag_ok_l2 - tag_ok_full` 与 `被拦截 U1-only wrong = count(!exact_u1 && exact_l2 && !tag_ok_full && tag_ok_l2)` 等

3. **Phase A 只读归因（decoder-free，零 calls）**：
   - **输入**：`comparison_bench/outputs_comparison/formal_ir_methods/v63_nbldpc_polar_shell/run_01/` (或 `v63_dev_*`) 下 `v63_dev_1M_0133` 单块的已落盘 records/summary/registry（含 `exact_u1, exact_l2, exact_full, syndrome_ok_l1, syndrome_ok_l2, tag_ok_l2, U1_errors, U2_errors, s_hat vs s_true` 等字段）
   - **核查项**：`exact_u1/l2/full, syndrome_ok_l1/l2, tag_ok_l2, U1_errors (=count(u1_hat!=u1_true)), U2_errors, tag_input 指向, leak 三档一致性`
   - **分流**：
     ```
     if fields_missing or inconsistent_definition:
         → ATTRIBUTION_INCOMPLETE (not rerun, stop before Phase B, record missing fields)
     elif U1_wrong && U2_exact && tag_ok_l2 && syndrome_ok_l2:
         → L2-only tag 不足以拦截 U1-only 错误 → 进入 Phase B 修正验证
     elif U2_wrong && tag_ok_l2:
         → 暂停，调查 tag/encoding 链路 (H/m2/syndrome/tag_input/decoder 一致性)，不进 Phase B
     else:
         → 无法拆解 → ATTRIBUTION_INCOMPLETE 不重跑
     ```

4. **Phase B 修正验证（45 fresh blocks，15/source，2–4 calls/block 总 90–180）**：
   - **规模**：`15/source=45 blocks`，每块 `1024 symbols (4×256 frames)`，从同域 held-out 剩余非重叠窗口 `S2` 按 `index_j=floor(j*(K2-1)/14) j=0..14` 分散选（若 `K2<45` 或 `per-source<15` 则 `EVIDENCE_INVALID` 停止，不伪造），与 `V48–V63` 已用 `frame_ids` 零重叠（`frame_ids exact` 校验），`v64_fresh_registry.json` authoritative，`sampling_mode=deterministic_four_consecutive_frames_heldout_fresh_v64`
   - **预算**：`L1 45 + base45 + stage1≤45 + stage2≤45 =90–180 硬帽180 (L2 45–135)`，`per block 2–4 calls`，`base` 兼 old 不重复，`verification-only` 触发，`leak` 三档不变
   - **协议**：与 V63 三阶段相同，仅 `verify` 输入改为 `full_symbol`；同一 `s_hat` 双口径 `tag_ok_l2` vs `tag_ok_full` 对照记录，`undetected_full_tag` 以 `full` 为准
   - **一次 decode 双口径**：每 L2 call 的 `syndrome_ok` 相同，`tag_ok_l2` 与 `tag_ok_full` 并列计算，`accepted_full = syndrome_ok && tag_ok_full` 为门禁口径

5. **Phase C 门禁与终态（frozen，first-match）**：
   - **门禁 V64 PASS** 需同时：`exact_full ≥35/45 overall ∧ 每源 ≥10/15 ∧ undetected_full_tag==0 ∧ 所有 exact_full 帧 tag_ok_full==True ∧ 预算 90–180 hard cap ∧ 泄漏/矩阵 rank/nested/independence 全 PASS`
   - **预注册终态**（见 Goal §4 五选一，`EVIDENCE_INVALID` 优先，`ATTRIBUTION_INCOMPLETE` 次之）
   - **输出**：`exact_u1/exact_l2/exact_full 分别计数(overall+per-source) + 三验证对照 + undetected_full 单独表 + disclosure 三档 per_source_avg + L2-vs-full 差异表 + U1-only 拦截数 + calls/rescue + runtime + stage_used 分布 + Wilson 95%`

6. **Lifecycle 冻结**：本轮 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`，`implementation_started=false`，任何 fresh decode 实现/执行需 `Phase A 归因分流通过 + 独立 plan ACCEPT + 显式 EXECUTE_AUTH 绑定到精确实现 SHA + v64_fresh_registry.json`；本轮仅四工件。

## Impact Scope

- **新增（本轮）**：`openspec/changes/formal-ir-v64-full-symbol-verification-correction/` 四工件（`proposal.md, design.md, tasks.md, specs/spec.md`）— 仅计划，不含代码/输出。
- **未来实现（本轮不创建，仅预冻结接口）**：`comparison_bench/src/comparison_bench/formal_ir/v64_full_symbol_verification.py`（仅改 verification 输入为 `32*u1+u2`，复用 `compute_tag_64`，其余 import V54/V63 冻结方法）+ `comparison_bench/src/comparison_bench/methods/nbldpc_shell_adapter.py` 的 verification 封装补丁 + `scripts/execute_v64_attribution.py` (Phase A 只读) + `scripts/execute_v64_fresh_verify.py` (Phase B fresh)；均直接 import `v54_two_stage_incremental_l2_rescue` + `v38_architecture_triage` + `v35_algorithm_development::compute_tag_64`，**仅当 Phase A 分流通过 + 独立 plan ACCEPT + EXECUTE_AUTH 后才允许创建**。
- **只读依赖**：`comparison_bench/outputs_comparison/formal_ir_methods/v63_nbldpc_polar_shell/run_01/` (Phase A 输入) + `comparison_bench/src/comparison_bench/formal_ir/v63_nbldpc_polar_shell.py` 等 V63 冻结模块 + `v35_algorithm_development.py::compute_tag_64` + `V25 channel_counts.npz` + `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816` held-out 池
- **不修改**：任何既有 spec/代码/测试/输出、`V38–V63` 输出、`outputs_comparison`/`workspace`/`AGENT_PROJECT_MEMORY.md`/`docs/decision-log.md` 以外；不改 `src/experiments/tools` 冻结基线；不创建正式 `run_01` 输出；**V63 工件只读，V64 不覆写 V63 任何文件**。

## Acceptance Criteria

- [ ] 四工件齐全一致且 lifecycle 为 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`，plan HEAD 前缀已记录（重核 40位），`branch formal-ir-mainline`，`data SHA 84d62779` (`d=1024 bw=200 pairing=nearest legacy_v1`) 已记录，`implementation_started=false`，`production_outputs_created=false`，明确“Phase A 未分流前不得实现/运行 Phase B decoder，不改 V63 工件，不改纠错参数，等待独立 review”。
- [ ] Phase A 只读归因已冻结：`v63_dev_1M_0133` 输入路径/字段清单(`exact_u1/l2, syndrome_ok_l1/l2, tag_ok_l2, U1/U2 errors`)已显式，三分支分流 `U1 wrong+U2 exact→进 Phase B / U2 wrong+tag_ok→暂停调查 / 无法拆解→ATTRIBUTION_INCOMPLETE 不重跑` 已显式，且 `零 decoder, 只读, 不覆写 V63` 已验。
- [ ] Phase B 修正语义已冻结：纠错参数 `H1-16/L1APP/Lane C/Δ8+Δ8 TRAIN prior 90/1.0 泄漏` 全冻文字已验，verification 唯一变量 `tag(U2) → tag(32*U1+U2) 复用 compute_tag_64 canonical 仍单64-bit 泄漏不增` 已显式，双口径 `L2-only vs full` 对照已冻结。
- [ ] Phase B 规模与预算已冻结：`15/source=45 blocks, 2–4 calls/block, 总 90–180 硬帽180 (L2 45–135)`，`index_j=floor(j*(K2-1)/14)` 分散，`K2≥45` 且 `frame_ids zero overlap` 与 `V48–V63` 已验，三档泄漏 `1064/1094/1104 →1104/1134/1144 →1144/1174/1184` 不变已验。
- [ ] 门禁已冻结：`exact_full≥35/45 且每源≥10/15 且 undetected_full_tag==0 且所有 exact 帧 full tag 通过且预算泄漏矩阵通过` 已显式，五态 `FULL_SYMBOL_VERIFICATION_PASS / CORRECTION_WORKS_VERIFICATION_STILL_FAILS / CORRECTION_PERFORMANCE_FAIL / ATTRIBUTION_INCOMPLETE / EVIDENCE_INVALID` 互斥 first-match 已验。
- [ ] 报告承诺已冻结：`L2-only vs full 差异表 + 被拦截 U1-only wrong 数量 + 分层 calls/泄漏/runtime per-source + Wilson 95% + undetected 单独表` 已显式，且 `exact_u1/exact_l2/exact_full 分别计数` 已验。
- [ ] 本轮产出边界已冻结：仅四工件，**禁 production module/CLI/tests/正式 output root/执行 decoder/自授 EXECUTE_AUTH**；`py_compile PASS`，`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0 && git diff -- openspec/changes/formal-ir-v6[0-2,3]/ ==0`（除本变更外零改），`run_01` 不存在已验。
- [ ] 已推送并停在 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` 等待独立 plan review，未改 V63 工件，未运行 decoder。

## Tasks

见 `tasks.md`（Phase A 只读归因零 decoder 三分支分流；Phase B 45 fresh 冻结与 verification 修正；门禁五态与双口径报告；交付与推送）。

## Lifecycle

前代 `formal-ir-v63-nbldpc-polar-shell-integration` (`5602f11c`, `PLAN_CANDIDATE / DECODER_FREE_INTEGRATION_SPIKE_COMPLETE / EXECUTE_NOT_AUTHORIZED`) 与 `formal-ir-v54-two-stage-incremental-l2-rescue` (`cb60c5dd48...`) 共存；V64 当前 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`（branch `formal-ir-mainline`, data SHA `84d62779`），止于 plan 四工件，Phase A 未分流前禁止实现/执行；实现候选止于 `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`；任何 fresh 执行需显式用户 `EXECUTE_AUTH` 绑定到精确未来实现 SHA + `v64_fresh_registry.json`；本轮仅四工件。
