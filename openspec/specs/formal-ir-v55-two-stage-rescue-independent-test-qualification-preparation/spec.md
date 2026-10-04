## Historical implemented scope — formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation

This section preserves only the archived, reviewed scope named below. It does not change the archived source. Current repository AGENTS.md and reboot handoff R1–R9 take precedence. This historical merge grants no new execution, acceptance, qualification, promotion, publication, decoder work, or probe restart.

<!-- Source: openspec/changes/archive/2026-10-04-formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation-completed/specs/spec.md -->

## R1. Predecessor binding（完全冻结 V54 二阶段，已达 QUALIFICATION_PLAN_READY）

V55 SHALL 仅基于 V54 完整冻结方法（`H1-16 + syndrome-derived L1-APP + Lane C H_base 184/190/192 + H_inc1 8×1024 det1 + H_inc2 8×1024 det2 + H_joint1/H_total + decoder 90/1.0 poly37 + L2-only tag + TRAIN-only prior + verification-only rescue + 每增量+40`）规划，复用 `n=1024` 与 `m2/leak_base 1064/1094/1104` 定义及 `H_inc1/H_inc2/H_joint1/H_total` 嵌套秩，不改首遍 support/标签/prior/MET图/decoder/H_inc1/H_inc2，不新造任何矩阵，不试 `Δm=4/12/16` 除 `8+8` 外，不测新 prior/标签/阈值。V55 SHALL 冻结 intake 三源 (`1M_600k_0dB / 1p5M / 2M_1.2M_0dB` 非同分布 2026-01-21, 200ps legacy_v1, 2130/5125/5513) 的 `90-block authoritative` 注册与 G1-G7 全 PASS + 预算 `180-360 硬帽360` / 门禁 `70/90+20/30+undetected==0` / claim (independent cross-session). V55 SHALL NOT 启动正式 TEST 实现/执行，需独立 plan ACCEPT + 显式 `EXECUTE_AUTH`（绑定 `formal-ir-mainline`、未来实现 SHA + authoritative registry + data SHA `84d62779`）。

<!-- Source: openspec/changes/archive/2026-10-04-formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation-completed/specs/spec.md -->

## R2. Frozen method（完全冻结 V54 二阶段，零改，V55 不测新变量）

冻结方法 SHALL 为：`n=1024, m2=184/190/192, GF32 poly37, Lane C support/label/position_permutations, m1=16, leak_base=5*m2+80+64 →1064/1094/1104, leak_stage1=leak_base+40 →1104/1134/1144, leak_stage2=leak_base+80 →1144/1174/1184`；`H1 16×1024 rank16` 复用 `nonbinary_v31.build_matrix_packet`；`prior TRAIN` via `load_v25_channel_counts()` → `BP_i` → `q_i` → `P_i(U2)`；`decoder 90/1.0` early-stop；`verification = syndrome_ok && tag_ok` L2-only；`exact_full=exact_u1&&exact_l2` oracle。`H_inc1 det1 8×1024` per source（`GF32 poly37`, `col_degree_inc∈{0,1}`, `row≤16`, `无零行`, `rank_joint1==m2+8`）与 `H_inc2 det2 8×1024` per source（同约束, `rank_total==m2+16`）SHALL 保持嵌套 `H_base==H_joint1[:m2]`, `H_base==H_total[:m2] && H_joint1==H_total[:m2+8]`, `independence 8+8`。SHALL NOT 改 V54 任一部件；**SHALL NOT 测新矩阵/标签/prior/阈值/decoder参数**，违者 `EVIDENCE_INVALID`。

<!-- Source: openspec/changes/archive/2026-10-04-formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation-completed/specs/spec.md -->

## R4. Qualified independent TEST requirements（authoritative 90-block，已冻结）

合格独立跨 session TEST SHALL 为：
- (a) **Intake**：`1M_600k_0dB` (2026-01-23, 2130 frames, 545280 rows) / `1p5M` (2026-01-07, 5125 frames, 1312000 rows) / `2M_1p2M_0dB` (2026-01-23, 5513 frames, 1411328 rows)，`84d62779` 单点 200ps legacy_v1，非同分布 2026-01-21，三层绑定实际 acquisition，provenance `.ttbin/.1.ttbin` 同源 sha256/size/mtime、结构 `frames×256` `0..1023` 排序无缺失已验
- (b) **主样本 (authoritative)**：`B=30` 每源共 `90` blocks (360 frames)，`K=F-3=2127/5122/5510`，`all_starts=0..F-4`，`index_j=floor(j*(K-1)/29) j=0..29` 确定性分散，`gap≥4` 两两非重叠且与 V13 及 V48-V54 零重叠 per source；`v55_authoritative_registry.json` 为**唯一合法**块集，`sampling_mode=deterministic_four_consecutive_frames_independent_test_v55_authoritative`，`pairs_count=1024, BLOCK_LENGTH=1024`，**禁换块/禁重采样/禁跨源混用** (自 authoritative 起)
- (c) **生成**：`python workspace/v55_intake_20260828/v55_decoder_free_intake.py` (calls `_read_ttbin_timetags` A1/B5 → `_bin_indices_sorted_for_binwidth` 200 → `_pairs_from_sorted_bins` 1024 nearest)，`sidecar_meta.json` 记录 `materialize_params` 與 `checks` (no_decoder/no_padding/no_resampling/no_cross_session)，输出 `sidecars/a_eff.npy|b_eff.npy` + `pairs/pairs.parquet` (parquet rows = frames×256)
V55 本轮 SHALL 仅冻结 authoritative 90-block，不执行采样重选；已 freeze frame_ids/ordinal。

<!-- Source: openspec/changes/archive/2026-10-04-formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation-completed/specs/spec.md -->

## R6. Leakage and budget — 三阶段（已冻结，180-360 硬帽360）

Tag SHALL 为 `compute_tag_64(empty_uint8,x2)` L2-only。泄漏 SHALL 冻结：`leak_base=5*m2+80+64`；`leak_stage1=leak_base+40`；`leak_stage2=leak_base+80`。每块条件泄漏：`verify_base` 通过则 `leak_base`，否则 `verify_stage1` 通过则 `leak_stage1`，否则 `leak_stage2`（成功与最终失败同）。预算 SHALL 为 `L1 90 + base L2 90 + stage1 0–90 + stage2 0–90 =180–360 硬帽360 (L2 90–270)`，`base` 兼 old 不重复；每块 `L1 1+base 1+stage1≤1+stage2≤1` (L2 1-3)。`per_source_avg[s]=leak_base[s]+40×N_stage1[s]/30+40×N_stage2[s]/30`，`coverage_avg=(Σ leak_base+40×N_stage1_total+40×N_stage2_total)/90`。此预算已 freeze 为 authoritative 90-block。

<!-- Source: openspec/changes/archive/2026-10-04-formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation-completed/specs/spec.md -->

## R7. Three-pass conditional protocol（已冻结，verification-only，二阶段嵌套，authoritative）

每块 (authoritative 90, 30/source) SHALL 执行：`base = decode(H_base, P(U2), s_base)` → `verify_base`；若通过则停，`leak=leak_base`；否则 `stage1 = decode(H_joint1, P(U2), s_joint1)` → `verify_stage1`；若通过则停，`leak=leak_stage1`；否则 `stage2 = decode(H_total, P(U2), s_total)` → `verify_stage2`，`leak=leak_stage2` 无论成功/失败。`exact_*` oracle 仅统计，触发仅 verification。**主判完整 base→Δ8→Δ16 (base→Δ16)**，`stage1` 仅分层报告不取代最终。每块 `L1 1+base1+stage1≤1+stage2≤1`，总 `180-360` 硬帽360。

<!-- Source: openspec/changes/archive/2026-10-04-formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation-completed/specs/spec.md -->

## R8. Primary gate — 预注册门禁与终态（含 QUALIFICATION_PLAN_READY）

Gate SHALL 为 (authoritative 90-block)：

- `QUALIFICATION_PLAN_READY` 已达成 (G1-G7 全 PASS, authoritative 90-block 已冻)，等待独立 plan ACCEPT + EXECUTE_AUTH 后方可执行
- 若完整性/守卫/秩/嵌套/重叠/记账失败 → `V55_EVIDENCE_INVALID` 优先
- 否则若 `coverage final_exact_full ≥70/90 (77.8%)` ∧ 每源 `final_exact_full ≥20/30 (66.7%)` ∧ `undetected==0` 全局 ∧ `rank/nested/verification/记账` 通过 → `V55_INDEPENDENT_TEST_PASS` (仅称 `independent cross-session qualification evidence`，三层绑定实际 acquisition，非同分布 2026-01-21)
- 否则若完整性通过但未过门禁 → `V55_INDEPENDENT_TEST_FAIL`

`base/stage1` 仅分层报告，**最终以 `base→Δ16` 主判**，`stage1` 中间报告 SHALL NOT 取代最终；`Wilson 95%`/`rescue_rate`/`runtime`/`leakage` 仅报告不作门禁（按源分层 + coverage）。`V55_INDEPENDENT_TEST_PASS` SHALL NOT 被描述为 FER/SKR/阈值/安全/资格/晋升证据，不宣称同分布复现。

<!-- Source: openspec/changes/archive/2026-10-04-formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation-completed/specs/spec.md -->

## R9. Reporting promises — SHALL（explicit，三阶段，authoritative 独立跨 session TEST）

若未来获独立 plan ACCEPT + EXECUTE_AUTH 并执行 90-block authoritative TEST，Summary SHALL 按源与 coverage 显式包含：`base_exact_full_count` 与 `verify_base` 分别、`stage1_exact_full_count` 与 `verify_stage1` 分别、`final_exact_full_count` 与 `verify_final` 分别（门禁仅用 `final` 的 `70/90` 与 `20/30` 累计量，`base`/`stage1` 仅分层报告）、`stage1_rescued/stage2_rescued`、`N_stage1_attempted=count(!verify_base)` 与 `N_stage2_attempted=count(!verify_base&&!verify_stage1)`、`rescue_rate_stage1/stage2` per source、泄漏三档与 `per_source_avg/coverage_avg`、`Wilson 95%` per source & coverage、`total_disclosed_bits` 与 `disclosure_per_final_exact_block`（为0则null）、`joint1_rank/total_rank/nested/independence`、`reclassified 四类/undetected`（全局）、`paired base vs stage1 vs final` per block、`iterations/runtime/residual`。Claim SHALL 限为 independent cross-session qualification evidence，三层绑定 (`1M_600k_0dB / 1p5M / 2M_1.2M_0dB` + `84d62779` 处理点 + `v55_authoritative_registry.json` 90-block)，非 FER/SKR/promotion，不宣称同分布复现。

<!-- Source: openspec/changes/archive/2026-10-04-formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation-completed/specs/spec.md -->

## R11. Integrity, guard ordering, seed registry, and execution deviation prevention（已冻结，QUALIFICATION_PLAN_READY）

Runner SHALL 三层：Tier0 拒绝（默认拒绝、`--execution-authorized --authorized-target-sha` 与 `HEAD==origin/formal-ir-mainline==未来实现SHA` + authoritative registry `84d62779` + data SHA、`SCOPED dirty` 四文件 `v55模块/v55 CLI/v38/v35`、G1-G7 需 `QUALIFICATION_PLAN_READY` 已达成、输出根已存在）、Tier1 预检失败（G1-G7 全检已 PASS + `H_base rank/support` + `H_inc1/H_inc2 rank/nested/independence/row≤16/col≤1/E≈96/leak` per source）、Tier2 中途异常保留 raw partial。执行偏差防复发：SHALL NOT 使用 600s 外部 timeout（建议≥3600s或不设）、若返回 `session_id/cell_id` SHALL 只轮询同一进程、SHALL NOT 重启新 session、中断保留 raw partial 不聚合不自动重跑。Compact intake 已执行 Tier1 的 decoder-free 分支且零 decoder calls。

<!-- Source: openspec/changes/archive/2026-10-04-formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation-completed/specs/spec.md -->

## R12. Workload and stop rules（frozen authoritative 90, 180-360）

总预算 SHALL 为 `90` 块三阶段条件：`L1 90` 共享 + `base L2 90`+`stage1 L2 ≤90`(条件)+`stage2 L2 ≤90`(条件)= 总 `180-360` 硬帽360 (`L2 90-270`)。P0 轮 SHALL NOT 执行任何 decoder call，已达 `QUALIFICATION_PLAN_READY` 等待独立 plan review。独立跨 session TEST 确认规模，门禁 `70/90 ∧ 20/30 ∧ undetected==0` 且主判 `base→Δ16` 已冻结，`base/stage1` 仅分层报告。

<!-- Source: openspec/changes/archive/2026-10-04-formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation-completed/specs/spec.md -->

## R13. Records preservation（预冻结，未来执行，authoritative 90）

每解码 SHALL 一条记录；`base` `90`条，`stage1` 至多`90`条（条件 `!verify_base`），`stage2` 至多`90`条（条件 `!verify_after_stage1`）。总 `L2` 记录 `90-270` 条，总调用 `180-360` 硬帽360。Schema 含 `stratum/source(1M_600k_0dB/1p5M/2M_1p2M_0dB)/arm∈{base,stage1,stage2}/pass_index/used_inc1/used_inc2/matrix_id∈{base,joint1,total}/h1_matrix_id/frame_ids[4]/held_out_ordinal/sampling_mode(authoritative)/max_iter 90/damping 1.0/errors_initial/final/exact_u1/exact_l2/exact_full/syndrome_ok/tag_ok/tag_scope/reclassified/target_tag/candidate_tag/iterations/bp_posterior_entropy/mean_abs_diff/leak_total/status/runtime`。Prior 仅 `TRAIN`。

<!-- Source: openspec/changes/archive/2026-10-04-formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation-completed/specs/spec.md -->

## R14. Claim boundary（关键判断，已收紧，独立跨 session）

结果仅支持 `n=1024 m2=184/190/192 Δm=8+8` 上 `H_total=[H_base;H_inc1;H_inc2] 嵌套增量` 在 authoritative `90-block` 独立跨 session TEST（每源 `30` 共90，4帧=1024 pairs，`deterministic_four_consecutive_frames_independent_test_v55_authoritative` 经 `K-1` 分散 `index_j=floor(j*(K-1)/29)` 选择，`gap≥4`，与 V13 零重叠，frame_ids 已冻）在 `180-360` calls 上的有界二阶段 rescue 归因（首遍与二阶段冻结 Lane C 原 support/标签/prior/MET图不改，`90/1.0 poly37, leak_base 1064/1094/1104, leak_stage1+40, leak_stage2+80, per_source_avg/coverage_avg`，G1-G7 已 PASS，门禁 `70/90 ∧ 20/30 ∧ undetected==0` 仅用 `final` 的 authoritative 累积且主判 `base→Δ16`，`base/stage1` 仅分层报告），`exact_full` oracle 不经 tag；均非 FER 全集/阈值/SKR/安全/资格/外推至多 session 的证据；独立跨 session TEST 确认规模，通过仍仅独立跨 session 资格确认（绑定 `1M_600k_0dB F2130 / 1p5M F5125 / 2M_1p2M_0dB F5513` 三次实际 acquisition、`84d62779` 200ps 单点、`v55_authoritative_registry.json` 90-block 三层），**不宣称复现 2026-01-21 同分布**，PASS 仅 `independent cross-session qualification evidence`。

<!-- Source: openspec/changes/archive/2026-10-04-formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation-completed/specs/spec.md -->

## R15. Lifecycle（已达 QUALIFICATION_PLAN_READY，等待独立 review）

本变更 lifecycle SHALL 为 `QUALIFICATION_PLAN_READY / EXECUTE_NOT_AUTHORIZED`，已由 `intake_compact_evidence.md` + `v55_authoritative_registry.json` (authoritative 90-block) + `G1-G7 全 PASS` 达成；`implementation_started=false`, `production_outputs_created=false`, `formal_execution_authorized=false`。SHALL NOT 执行 decoder 或创建 `run_01`，SHALL NOT 自授 `EXECUTE_AUTH`，**SHALL 在推送后停留 `QUALIFICATION_PLAN_READY` 等待独立 plan review** (申请人与执行人分离)。
