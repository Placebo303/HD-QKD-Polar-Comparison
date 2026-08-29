# OpenSpec Proposal: formal-ir-v63-nbldpc-polar-shell-integration

**Status**: `PLAN_CANDIDATE / SHELL_INTEGRATION / EXECUTE_NOT_AUTHORIZED` — 仅产出壳集成计划四工件，不实现/不执行 decoder，不创建 run_01，等待独立复审与显式授权
**Domain**: Formal IR / Polar pipeline 外壳保留 + NB-LDPC IR 模块替换（shell integration）
**Change ID**: `formal-ir-v63-nbldpc-polar-shell-integration`
**Cycle ID**: `V63P0` (nbldpc-polar-shell-integration), predecessor `formal-ir-v54-two-stage-incremental-l2-rescue` (`cb60c5dd48b...`, `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`) + `formal-ir-v62-nbldpc-polar-reference-benchmark` (`6a3b873e` 仅参考对比，不改其终态)
**Branch**: `formal-ir-mainline`
**HEAD**: `fad33f4b935e73972b5be4d02ec7901214fa0046` (实施前以 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline == fad33f4b...` 40位重核，不一致阻塞；本次推送新 Plan SHA)
**Data SHA**: `84d62779` (`84d62779603e62de50ded5182ed65b65d3dc6084`, `d=1024 bw=200ps pairing=nearest rule=legacy_v1` 冻结处理点，同 V54 同域；Polar 侧以机械提取为准)
**Lifecycle**: `PLAN_CANDIDATE / SHELL_INTEGRATION / EXECUTE_NOT_AUTHORIZED` — 本轮止于 plan 四工件，未集成前禁止实现/执行 IR 替换与正式 run

> ponytail lite: 本变更仅 4 OpenSpec 工件（proposal/design/tasks/specs），零新增 decoder/矩阵/依赖（`numpy/pandas/pyarrow` 已装）；laziest alternative: 若 Phase A 适配接口未对齐 `IRRunResult` 语义，则直接落盘 `SHELL_ADAPTER_NOT_ALIGNED` 停止，不伪造 reconciled_symbols/泄漏。

> **研究目标**：保留 Polar pipeline 外壳（TTBin→timing/pairing/binning→1024 symbols→参数估计/分层→verification/tag→泄漏统计→PA→key length/PIE/SKR 报告）的**非 IR 部分**，将 **IR 模块替换为 NB-LDPC**（V54 冻结 `H1-16+Lane C+Δ8+Δ8` 二阶段），验证在真实数据上端到端贯通并以 NB-LDPC 实际泄漏驱动 PA，评估同域 development 性能与 proxy 产钥。

## Goal

保留 Polar 外壳，IR 替换为 NB-LDPC，完成壳集成并在同域真实数据上以可信泄漏驱动端到端测量：

1. **外壳保留、IR 替换**：流水线 `TTBin读取→通道选择/timing→delay/pairing→symbol materialization(1024 symbols)→参数估计/分层→[替换] NB-LDPC reconciliation(H1-16+L1-APP+Lane C+Δ8+Δ8 冻结)→verification/tag(L2-only 64b)→泄漏统计→PA→key length/PIE/SKR 报告`；所有非 IR 壳组件直接复用 Polar pipeline（只读），IR 接口输出替换为 `reconciled_symbols / accepted / rejected / exact / syndrome_ok / tag_ok / undetected / actual_disclosure_bits / decoder_calls / runtime_s / stage_used∈{base,delta8,delta16}`；PA 必须按帧实际阶段取 `base 1064/1094/1104, stage1 1104/1134/1144, stage2 1144/1174/1184` (per source)，不得沿用 `Polar leak_EC`。
2. **可复用清单（只读复用，不改 Polar baseline/src）**：`TTBin读取、通道选择、delay/pairing、symbol materialization、session/source/frame provenance、参数估计分层、verification/丢帧、PA、认证开销报告、Polar PIE/SKR 参数参考`；IR 适配层新增于 `comparison_bench/`，`src/experiments/tools` 冻结只读。
3. **真实数据边界（二档，first-match）**：`1) 与 V54 同域真实数据可直接运行（已验证 43/45 可重放，剩余需 decoder-free 校验后纳入）`；`2) 新 session 需 decoder-free 信道域检查 + 新 calibration P(U1|B)/P(U2|B,U1) + 重算 m1/m2 后才可运行，不调 LDPC`（调参即 `EVIDENCE_INVALID`）。
4. **Phase A 接口适配**：`comparison_bench` 新增 NB-LDPC IR adapter：输入 materialized `FrameBatch(Alice/Bob symbols, dimension=1024, frame_len=1024)`，输出统一 `IRRunResult` 扩展（含 per-frame `reconciled_symbols/accepted/exact/syndrome_ok/tag_ok/undetected` 与 `actual_disclosure_bits/decoder_calls/runtime/stage_used`），Polar baseline/src 只读，PA 读取 NB 实际泄漏。
5. **Phase B 同域 smoke（9 blocks）**：`3/source 共 9 blocks`，`H1-16+Lane C+Δ8+Δ8` 完全冻结，验证贯通（TTBin→PA 全链路、泄漏按实际阶段计、PA 产钥流程可复现），预算 `18-36 calls`（每块 `2-4 = L1 1 + base 1 + §1≤1 + §2≤1`，硬帽 36）。
6. **Phase C 同域正式 development run（90 blocks）**：`30/source 共 90 blocks`，预算 `180-360 calls`（每块 2-4，硬帽 360），门禁 `final≥70/90 overall 且每源≥20/30 且 undetected==0`，输出 `纠错成功/泄漏分布/runtime/proxy yield` 分层报告（overall + per-source）。
7. **Phase D 外壳结果**：安全/PIE/SKR 沿用 Polar reference 参数作 `shadow proxy`，标记 `POLAR_REFERENCE_PROXY`，不宣称 composable/有限密钥证明；仅描述性，不作门禁。

**报告承诺（shall）**：proposal/design/tasks/specs 显式承诺 — 若未来执行配对壳集成，最终报告 SHALL 按 `overall + per-source` 分别包含 `accepted/exact 四类( exact/detected/decoder_non_syndrome/undetected) + disclosure bits/block 三档分布(actual_disclosure_bits per frame + per accepted) + calls/rescue(N_stage1/N_stage2/rescue_rate) + runtime/throughput + stage_used 分布(base/delta8/delta16) + PA 输入泄漏明细 + proxy PIE/SKR/key length`；门禁仅用 `accepted/exact + undetected==0`，secondary 仅描述性；泄漏分解不一致时跨方法对比失效。

## Non-Goals

- 不改 `H1-16 / L1-APP(TRAIN prior via V25 channel_counts.npz) / Lane C support/标签/置换/MET图 ordinal-2 s38310x m2 184/190/192 / H_inc1 8×1024 det1 / H_joint1 192/198/200 / H_inc2 8×1024 det2 / H_total 200/206/208 / decoder 90/1.0 poly37 early-stop / L2-only tag compute_tag_64(empty,x2) / TRAIN-only prior / verification-only +40/+80 / leak 1064→1144/1174 1184` 任一冻结量；不新增矩阵/标签/prior/阈值/decoder 参数，新增即 `EVIDENCE_INVALID`。
- 不修改 `src/ experiments/ tools/` 任何文件（冻结基线只读；`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0` 语义）；不重跑 Polar IR（Polar 仅作 reference 参数来源，shell 外壳复用其非 IR 组件）。
- 不重估先验（`V25 channel_counts.npz` 只读）；新 session 未通过 decoder-free 域检查 + 新 calibration + m1/m2 重算前禁止运行；不以 outcomes 调 LDPC 码率/矩阵。
- 不创建正式 `comparison_bench/outputs_comparison/formal_ir_methods/v63_*/run_01` 或执行 decoder（本轮仅 plan 四工件，`py_compile PASS`，`rg "decode_"` 仅在冻结模块内，SP未新增 decoder）。
- 不继续 `V61/V60` 数值、有限密钥网格、或 V55 `frames×256` 非 `1024-block legacy_v1` 输入；不改 `V38–V62` 既有输出与终态。
- 不做 `FER/阈值/资格/晋升/安全证明` 的扩大陈述；tag 仍 L2-only `≈2^-64` 工程近似；`POLAR_REFERENCE_PROXY` 不升级为 composable。
- 不伪造同域：无相同 `1024-block legacy_v1` 可重放时直接 `SHELL_DOMAIN_NOT_ALIGNED` 停止，不以 `SER/vis` 代理冒充。

## Scope

1. **冻结 NB-LDPC 方法（完全冻结，零改，V54 complete）**：`n=1024, m2 184/190/192, GF32 poly37, H1 16×1024 rank16 80b, L1-APP q_i=softmax(BP_i) via BP_i=decode_row_layered_fftqspa(H1,p_i,s1).bp_posterior_beliefs (TRAIN prior), Lane C ordinal-2, H_inc1 8×1024 det1 + H_joint1 192/198/200, H_inc2 8×1024 det2 + H_total 200/206/208, decoder 90/1.0 poly37 early-stop, verification tag_scope=l2_only compute_tag_64(empty,x2) trunc64 syndrome_ok&&tag_ok, leak_base 1064/1094/1104 leak_stage1 1104/1134/1144 leak_stage2 1144/1174/1184 (+40/+80), TRAIN-only, verification-only 触发`。`exact_full=exact_u1&&exact_l2` oracle 隔离，`undetected` 单独。
2. **外壳保留/IR 替换（shell integration）**：
   - **保留**：`TTBin读取、通道选择、delay/pairing、symbol materialization(1024 symbols)、session/source/frame provenance、参数估计分层、verification/丢帧、PA、认证报告、Polar PIE/SKR 参数参考` — 均只读复用 Polar pipeline 壳（`src/` + `experiments/run_e2e_pipeline.py` 的非 IR 段 + `comparison_bench/io`）。
   - **替换**：IR 段替换为 `comparison_bench/src/comparison_bench/methods/nbldpc_shell_adapter.py`（新），输入 `FrameBatch(alice_symbols,bob_symbols,dimension=1024,frame_len=1024,metadata={source,block_id,frame_ids,provenance})`，输出统一 `IRRunResult` 扩展：`reconciled_symbols, accepted(verify pass), rejected, exact, syndrome_ok, tag_ok, undetected(syndrome_ok&&tag_ok&&!exact), actual_disclosure_bits(per frame leak_base/stage1/stage2), decoder_calls(per frame 2-4, breakdown L1/base/stage1/stage2), runtime_s, stage_used∈{base,delta8,delta16}`；PA 读取 `actual_disclosure_bits`，不得读 Polar `leak_EC`。
3. **真实数据边界（first-match，互斥）**：
   - **同域可直接运行**：`dimension 1024, bin_width 200ps, pairing nearest, rule legacy_v1, frame_len 1024, source 1M/1p5M/2M held-out 1600-1999/2213-2766/2916-3644` 同 V54 已验 `43/45` 可重放（剩余 2 块需 decoder-free 符号一致性校验后纳入）；TRAIN isolation 保持（`split_manifest 60/20/20` 边界不破）。
   - **新 session 准入**：`decoder-free 信道域检查（统计 P(B), H(A|B) 漂移 >阈值则判 out-of-domain）→ 新 calibration P(U1|B) via get_l1_prior_p_u1_given_b + P(U2|B,U1) via get_l1_app_prior_l2 / factorize_f03 → 重算 m1/m2(total) = floor((1.3*n*H -64)/5) 等价` 后才可运行；期间**不调 LDPC**（矩阵/decoder/Δm 仍冻），否则 `EVIDENCE_INVALID`。
4. **Phase A 接口适配（comparison_bench 新增，不改 Polar src）**：
   - 新增 `comparison_bench/src/comparison_bench/methods/nbldpc_shell_adapter.py`：`class NbLdcShellIRAdapter(IRMethod): run(batch: FrameBatch, source: str) -> IRRunResult` 组合 V54 冻结方法（import `v54_two_stage_incremental_l2_rescue` 的 `construct_h_* / leak_for / compute_l2_tag / CallAccounting` + `v38_architecture_triage` + `v35_algorithm_development`），`reconciled_symbols = x2_hat` per frame，`accepted = syndrome_ok&&tag_ok`，`exact = exact_full`，`undetected` 单独，`actual_disclosure_bits = leak_base/stage1/stage2` 按实际 stage，`stage_used = base(0)/delta8(1)/delta16(2)`，`decoder_calls = 2-4 per block`。
   - `comparison_bench/src/comparison_bench/pipeline/shell_integration.py`（新）：`run_shell_pipeline(ttbin_root, source, block_ids) -> ShellResult`串联 `TTBin→pairing→FrameBatch→NbLdcShellIRAdapter→verification→leakage stats→PA(输入 NB 实际泄漏)→report`，Polar `src/experiments` 仅读其 `PA/leakage/report` 非 IR 函数。
5. **Phase B 同域 smoke（3/source=9 blocks，硬帽36）**：从同域 held-out 剩余窗口分散选 `3/source`（`index_j=floor(j*(K-1)/2) j=0..2` 若超集更大，否则取已验 43 中的 9），`H1-16+Lane C+Δ8+Δ8` 全冻，验证 `TTBin→PA 全链路、泄漏按实际阶段计、stage_used 分布、decoder_calls 18-36、runtime/throughput 可复现、PA 产钥 proxy 可算`；`exact/accepted` 分别计数，`undetected` 隔离。
6. **Phase C 同域正式 development run（30/source=90 blocks，硬帽360，门禁 frozen）**：
   - **规模**：`30/source=90 blocks`，每块 `1024 symbols (4×256 frames)`，从剩余非重叠窗口 `S2` 按 `index_j=floor(j*(K2-1)/29) j=0..29` 分散选（若 `K2<90` 则判 `SHELL_DOMAIN_NOT_ALIGNED` 停止，不伪造）。
   - **预算**：`L1 90 + base90 + stage1≤90 + stage2≤90 =180-360 硬帽360 (L2 90-270)`，`per block 2-4 calls`，`base` 兼 old 不重复，`verification-only` 触发。
   - **门禁（G1-G3' frozen）**：`G1 final_accepted≥70/90 overall (77.78%) ∧ G2 每源≥20/30 (66.7%) ∧ G3' undetected==0`；`EVIDENCE_INVALID` 优先（rank/nested/verification/记账/域检查失败）。
   - **输出**：`纠错成功(accepted/exact per source & overall + 四类) / 泄漏分布(三档 per_source_avg + overall_avg + per accepted) / runtime/throughput / stage_used 分布 / proxy yield(用 Polar shadow 参数仅排序)`。
7. **Phase D 外壳结果（security/PIE/SKR proxy，POLAR_REFERENCE_PROXY）**：`security/PIE/SKR` 沿用 Polar reference 参数（`polar_existing_bridge.py:benchmark_rows_from_polar_output` 的 `leak_EC_actual_bits, raw_ber, beta_eff_empirical` 对应公式 `PIE = beta*H(q), SKR proxy = accepted_fraction*(PIE - leak_per_block/n)`），标记 `authority=POLAR_REFERENCE_PROXY, readiness=reference, proxy_only=true`，不宣称 `composable`/`eps_sec/eps_cor/vis/phase-error` 有限密钥证明；泄漏分解语义不一致时该次 proxy 失效。
8. **Lifecycle 冻结**：本轮 `PLAN_CANDIDATE / SHELL_INTEGRATION / EXECUTE_NOT_AUTHORIZED`，`implementation_started=false`，任何 `NB-LDPC` 正式实现/执行需 `Phase A 适配通过 + 独立 plan ACCEPT + 显式 EXECUTE_AUTH 绑定到精确实现 SHA + shell registry`；不启动正式执行；本轮仅四工件。

## Impact Scope

- **新增（本轮）**：`openspec/changes/formal-ir-v63-nbldpc-polar-shell-integration/` 四工件（`proposal.md, design.md, tasks.md, specs/spec.md`）— 仅计划，不含代码/输出。
- **未来实现（本轮不创建，仅预冻结接口）**：`comparison_bench/src/comparison_bench/methods/nbldpc_shell_adapter.py`（IR adapter，组合 V54 冻结方法，输出统一 IRRunResult 扩展）+ `comparison_bench/src/comparison_bench/pipeline/shell_integration.py`（壳集成 pipeline，串联 TTBin→PA，PA 读 NB 实际泄漏）+ `scripts/execute_v63_shell_smoke.py` + `scripts/execute_v63_shell_development.py`；均直接 import `v54_two_stage_incremental_l2_rescue` + `v38_architecture_triage` + `v35_algorithm_development::compute_tag_64`，**仅当适配通过 + 独立 plan ACCEPT + EXECUTE_AUTH 后才允许创建**。
- **只读依赖**：`comparison_bench/src/comparison_bench/io/pairs_loader.py` (`load_pairs_table/normalize_pair_columns`)+`dataset_builder.py`(`build_frame_batch`)+`polar_existing_bridge.py`(`benchmark_rows_from_polar_output`)、V31 H1、V25 `channel_counts.npz`、`src/reconciliation/` 壳组件（仅读 PA/report 非 IR）、`comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816` held-out 池。
- **不修改**：任何既有 spec/代码/测试/输出、`V38–V62` 输出、`outputs_comparison`/`workspace`/`AGENT_PROJECT_MEMORY.md`/`docs/decision-log.md` 以外；不改 `src/experiments/tools` 冻结基线；不创建正式 `run_01` 输出。

## Acceptance Criteria

- [ ] 四工件齐全一致且 lifecycle 为 `PLAN_CANDIDATE / SHELL_INTEGRATION / EXECUTE_NOT_AUTHORIZED`，plan HEAD 绑定 `fad33f4b` 前缀（重核 40位），`branch formal-ir-mainline`，`data SHA 84d62779` (`d=1024 bw=200 pairing=nearest legacy_v1`) 已记录，`implementation_started=false`，`production_outputs_created=false`，明确“适配未通过前不得实现/运行 decoder，不改 Polar src，不继续 V61/V60，等待 shell 适配 + 独立 review”。
- [ ] 外壳/IR 边界已冻结：保留清单（TTBin/通道/delay/pairing/materialization/provenance/参估分层/verification/PA/报告）与替换清单（IR 接口输出 `reconciled_symbols/accepted/rejected/exact/syndrome_ok/tag_ok/undetected/actual_disclosure_bits/decoder_calls/runtime/stage_used`）已显式，且 PA 泄漏源为 NB 实际 `base1064/1094/1104 stage1 1104/1134/1144 stage2 1144/1174/1184` 每帧按实际阶段计，已禁 Polar leak_EC 重用。
- [ ] 真实数据二档边界已冻结：同域可直接运行（`43/45` 已验，剩余需 decoder-free 符号一致性校验）与新 session 准入（decoder-free 域检查 + 新 calibration P(U1|B)/P(U2|B,U1) + 重算 m1/m2，不调 LDPC）已显式，`first-match` 互斥。
- [ ] Phase A 适配可机械校验：`FrameBatch(1024,1024)` 输入 → `IRRunResult` 扩展输出 Schema 已冻结，`comparison_bench` 新增 adapter/pipeline 路径已预冻结，Polar `src` 只读已验（`git diff -- src/ ==0`），PA 读 NB 泄漏已验。
- [ ] Phase B smoke 已冻结：`3/source=9 blocks`，`H1-16+Lane C+Δ8+Δ8` 全冻，贯通验证项（TTBin→PA 全链、泄漏三档、stage_used、decoder_calls 18-36、runtime/throughput、proxy yield）已列，`18-36 calls 硬帽36 (L2 9-27)` 已验。
- [ ] Phase C development 已冻结：`30/source=90 blocks`，`180-360 calls 硬帽360 (L2 90-270)`，门禁 `final≥70/90 且每源≥20/30 且 undetected==0` 已显式，不因 V54 差2改阈值，输出 `纠错/泄漏/runtime/proxy yield` 分层已列。
- [ ] Phase D proxy 已冻结：`security/PIE/SKR` 沿用 Polar reference 参数标记 `POLAR_REFERENCE_PROXY`，不宣称 composable/有限密钥证明，泄漏语义不一致时失效已验。
- [ ] 本轮产出边界已冻结：仅四工件，**禁 production module/CLI/tests/正式 output root/执行 decoder/自授 EXECUTE_AUTH**；`py_compile PASS`，`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0 && git diff -- openspec/changes/formal-ir-v6[0-2]/ ==0`（除本变更外零改），`run_01` 不存在已验。
- [ ] 已推送并停在 `PLAN_CANDIDATE / SHELL_INTEGRATION / EXECUTE_NOT_AUTHORIZED` 等待独立 plan review。

## Tasks

见 `tasks.md`（Phase A 壳/IR 接口冻结与适配设计；Phase B 同域 smoke 9-block 冻结；Phase C 90-block development 设计与门禁；Phase D 外壳结果 proxy 标记；显式禁止清单与域门禁）。

## Lifecycle

前代 `formal-ir-v54-two-stage-incremental-l2-rescue` (`cb60c5dd48...`, `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`) 与 `formal-ir-v62-nbldpc-polar-reference-benchmark` (`6a3b873e`, `PLAN_CANDIDATE`) 共存；V63 当前 `PLAN_CANDIDATE / SHELL_INTEGRATION / EXECUTE_NOT_AUTHORIZED`（HEAD `fad33f4b`, branch `formal-ir-mainline`, data SHA `84d62779`），止于 plan 四工件，适配未通过前禁止实现/执行；实现候选止于 `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`；任何正式壳集成执行需显式用户 `EXECUTE_AUTH` 绑定到精确未来实现 SHA + `v63_shell_registry.json`；本轮仅四工件。

## R63 Revisions (PLAN_REVISION_CANDIDATE, 2026-08-30, HEAD 5602f11c)

**R63 Lifecycle**: PLAN_REVISION_CANDIDATE / DECODER_FREE_INTEGRATION_SPIKE_COMPLETE / EXECUTE_NOT_AUTHORIZED revision of 5602f11c, decoder-free spike only, no real decoder/run_01.
- **R63-01 32*u1+u2+exact**: Full symbol s in [0,1023] (10 bits, q=1024) factorizes as s = 32*u1 + u2 where u1 = s // 32 (high 5 bits 0..31) and u2 = s % 32 (low 5 bits 0..31). GF32 symbols are 5-bit sub-symbols. Reconstruction s_hat = 32*u1_hat + u2_hat. Exact condition exact_full = (u1_hat==u1_true and u2_hat==u2_true); exact_u1/exact_l2 separately reported. reconciled_symbols are full 10-bit symbols 0..1023 reconstructed via 32*u1+u2, not GF32-only.
- **R63-02 NbLdpcShellResult not change signature**: Existing IRRunResult signature frozen (comparison_bench/src/comparison_bench/methods/base.py) zero mutation. New wrapper NbLdpcShellResult/ShellResult aggregates per-frame IRRunResult plus shell metadata without altering IRRunResult fields. Adapter returns ShellResult containing IRRunResult unchanged.
- **R63-03 smoke INTEGRATION_REPLAY_SMOKE 90 fresh zero overlap**: Smoke registry = INTEGRATION_REPLAY_SMOKE 9 blocks (3/source, authoritative v63_smoke_registry.json), existing V54-verified held-out replay (43/45). Fresh candidate registry = INTEGRATION_FRESH_CANDIDATE 90 blocks (30/source=90, authoritative v63_dev_registry.json), deterministic index_j=floor(j*(K2-1)/29) from remaining non-overlapping windows. Zero overlap verified: smoke intersect fresh = empty, both intersect (V48..V54) = empty (frame_ids exact). Fresh registry is candidate only, DECODE_FORBIDDEN not executed.
- **R63-04 domain gate DOMAIN_CALIBRATION_REQUIRED**: New session gate: decoder-free domain_check (P(B) chi2 / H(A|B) drift >0.05 bits -> out-of-domain) then calibration P(U1|B) via get_l1_prior_p_u1_given_b + P(U2|B,U1) via get_l1_app_prior_l2/factorize_f03 then m_total=floor((1.3*n*H-64)/5), m1=round(m_total*H1/H_total) recomputed. Without PASS, DOMAIN_CALIBRATION_REQUIRED blocks execution. Same-domain V54 data (84d62779) bypasses calibration but still requires domain_check PASS.

