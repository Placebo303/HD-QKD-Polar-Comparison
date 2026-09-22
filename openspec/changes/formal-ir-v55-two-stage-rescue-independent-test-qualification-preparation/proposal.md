# OpenSpec Proposal: formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation

**Status**: `QUALIFICATION_PLAN_READY / EXECUTE_NOT_AUTHORIZED` — **intake 3/3 READY 已固化、registry 90块 authoritative 已冻结、G1-G7 全部 PASS；仅等待独立 plan review，不实现 runner，不执行 decoder，不创建正式 TEST run_01。**
**Domain**: Formal IR / V55 独立跨 session TEST 资格 (V54 二阶段 rescue 的独立采集验证资格门，authoritative 90-block)
**Change ID**: `formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation`
**Cycle ID**: `V55P0`
**Predecessor**: `formal-ir-v54-two-stage-incremental-l2-rescue` (plan HEAD `bf5dd1686049156540328bac264296b17fee546c`, branch `formal-ir-mainline`), **本变更 plan HEAD** `efd34ef318014e1d0505605062057b042e2180eb` (branch `formal-ir-mainline`) — intake 已绑定 **data SHA** `84d62779603e62de50ded5182ed65b65d3dc6084` (semantics `d=1024 bw=200 pairing=nearest rule=legacy_v1`)
**Lifecycle**: `QUALIFICATION_PLAN_READY / EXECUTE_NOT_AUTHORIZED`, `implementation_started=false`, `production_outputs_created=false`, `formal_execution_authorized=false`, `data_ready=true` (decoder-free G1-G7 按 authoritative registry 全 PASS，见 `intake_compact_evidence.md` + `v55_authoritative_registry.json`)
**V54 history**: V54 二阶段 `H1-16 + L1-APP + Lane C + m2 184/190/192 + H_inc1 8 + H_inc2 8 + base→Δ8→Δ16 verification-only + decoder 90/1.0 poly37 + TRAIN-only prior + L2-only 64-bit tag + 每增量+40` 已冻结为唯一性能候选；V55 **不测任何新矩阵/标签/prior/阈值/decoder参数**，仅用 V54 冻结方法对新 intake 独立跨 session TEST 做资格判定。

> ponytail lite: 本轮仅四 OpenSpec 工件 + 紧凑 intake 证据 (report + authoritative registry)；已达最简，不新增 runner/decoder。

## Goal

在**完全冻结 V54 二阶段性能候选**的前提下，完成 V55 独立跨 session TEST 的资格准备并冻结至 `QUALIFICATION_PLAN_READY`：

> **V54 冻结方法是否已具备进入独立 TEST 的“数据就绪”资格？是 — intake 3/3 READY (1M 2130 / 1p5M 5125 / 2M 5513 frames，均 200ps legacy_v1) 已通过 G1-G7 全部 PASS，90-block authoritative registry (30/source 共90，`index_j=floor(j*(K-1)/(need-1))` gap≥4) 已冻结，预算/门禁/claim 已预注册，后续正式 TEST 一次通过即可判定 `V55_INDEPENDENT_TEST_PASS/FAIL` (independent cross-session qualification evidence，非 FER/SKR/promotion)。**

1. **方法完全冻结（零改）**：`H1-16 (V31-H1-QC rank16) + L1-APP syndrome-derived BP_i via H1 (TRAIN prior) + Lane C support/标签/置换/MET图 (ordinal-2 s38310x) + m2 184(1M)/190(1p5M)/192(2M) + H_inc1 8×1024 det1 (Seed 600001-3) + H_inc2 8×1024 det2 (Seed 600004-6) + H_base(m2)/H_joint1(m2+8)/H_total(m2+16) 嵌套 rank m2/m2+8/m2+16 + decoder 90/1.0 poly37 early-stop + TRAIN-only prior (V25 channel_counts.npz) + L2-only 64-bit tag `compute_tag_64(empty,x2)` + verification-only 触发 (`syndrome_ok && tag_ok` 才增量) + 每增量 +40 bits (`leak_base 1064/1094/1104 → stage1 1104/1134/1144 → stage2 1144/1174/1184`)**。V55 **不测新矩阵/标签/prior/阈值/decoder ITA**，任何新矩阵即判 `EVIDENCE_INVALID`。

2. **数据就绪 (已达成，G1-G7 全 PASS)**：intake 三源已验证
   - **Session 冻结**：`20260123_1M_600k_0dB` (F=2130) / `20260107_PPLN_1p5M` (F=5125) / `20260123_2M_1p2M_0dB` (F=5513)，日期 `2026-01-23 / 2026-01-07 / 2026-01-23`，**与 2026-01-21 V13 非同分布 (non-iid)**，三层绑定实际 acquisition，仅称独立跨 session 证据
   - **处理点**：`dimension 1024, bin_width 200ps, pairing nearest, rule legacy_v1, channels A1/B5` (**单点**，`84d62779` semantics)
   - **Provenance**：每源 `.ttbin` + `.1.ttbin` 同源 (记录 sha256/size/mtime，FileReader auto-merge，fully materialize then judge，无 padding/resampling/cross-session stitching)
   - **结构统计**：每源 `frames×256 == rows` (545280/1312000/1411328), 符号 `0..1023` 范围, 排序 `frame_id 0..F-1 × pair_idx 0..255` 连续无缺失 (见 `intake_compact_evidence.md` §3)
   - **Registry**：`v55_authoritative_registry.json` **唯一 authoritative**，`30/source 共90`，`K=F-3` (2127/5122/5510), `index_j=floor(j*(K-1)/29)` 分散，`gap≥4` 两两非重叠，`frame_ids[4]` 已 freeze `held_out_ordinal_start/end`，**之后禁换块/禁重采样**
   - 大型 sidecar/pairs 不进 Git，报告已记录生成命令 `python workspace/v55_intake_20260828/v55_decoder_free_intake.py`、输出路径 `comparison_bench/outputs_comparison/v55_intake_20260828/sidecars|pairs`、行数与重建方法 (`_read_ttbin_timetags -> _bin_indices_sorted_for_binwidth -> _pairs_from_sorted_bins`)

3. **合格 TEST 规模冻结**：`S=3 strata × B=30 =90 blocks` (360 frames)，`S×B×4` frames，于每源 `all_starts=0..F-4` 得 `K=F-3`，`index_j` 分散选 `B=30`，验证 `gap≥4`，平衡常量块数；不足不凑，当前已足。

4. **数据就绪门 (decoder-free，分层，G1-G7 全 PASS)**：
   - (G1) 文件可读 per stratum — PASS (parquet 行数 = frames×256 已验)
   - (G2) provenance 完整 per stratum — PASS (.ttbin/.1.ttbin 双文件 hash 可追溯)
   - (G3) 各 stratum 明确 — PASS (D_target={1M,1p5M,2M} 各一 session，标签冻结)
   - (G4) 每帧 256 pairs / 每块 1024 pairs 形态 — PASS (256/frame 1024/block, monotic frame_id×pair_idx)
   - (G5) 与 V13 及 V48-V54 已用帧完全独立 — PASS (不同采集日期/独立 session，零重叠)
   - (G6) V25 prior 只读 — PASS (channel_counts.npz 形态校验，不读新 TEST 做训练)
   - (G7) 冻结 authoritative registry — PASS (每源 K≥B，index_j 分散，gap≥4，可机械校验)
   全 PASS ⇒ `QUALIFICATION_PLAN_READY`；任一 FAIL 则 `DATA_NOT_READY` (当前已 READY)

5. **预算冻结 (180-360 硬帽360)**：`S=3,B=30` 时 `L1 90 + base 90 + stage1 ≤90 + stage2 ≤90 =180-360 硬帽360 (L2 90-270)`，`base` 兼 old 不重复，每块 `L1 1+base1+stage1≤1+stage2≤1`；一般 `2SB-4SB` 硬帽，但本 TEST 已 freeze 为 90 块。

6. **预注册门禁冻结 (主判完整 base→Δ8→Δ16)**：
   - **覆盖门禁**：`overall exact_full ≥70/90` (77.8%)
   - **分源门禁**：每源 `≥20/30` (66.7%)
   - **安全门**：`undetected==0` 全局 (任一 stratum 出现即 FAIL) 且 `rank/nested/verification/记账` 通过
   - **主判**：完整 `base→Δ8→Δ16` (即 `final` base→Δ16)，`base` 仅分层诊断、`stage1 (Δ8)` 仅分层报告，不作主判替代；`Wilson 区间 / rescue_rate / runtime / 泄漏` 仅报告不作门禁
   - 终态：`V55_INDEPENDENT_TEST_PASS` / `V55_INDEPENDENT_TEST_FAIL` / `V55_EVIDENCE_INVALID`，PASS 仅称 `independent cross-session qualification evidence`，非 FER/SKR/阈值/安全/资格/晋升

7. **本轮止于 QUALIFICATION_PLAN_READY**：只修订四 OpenSpec 工件至 READY + 紧凑 intake 证据 (本目录 `intake_compact_evidence.md` + `v55_authoritative_registry.json` 原 `v55_stratified_registry_candidate.json` 提升为 authoritative)，**禁 production module/CLI/tests/正式 output root/执行 decoder/自授 EXECUTE_AUTH**，等待独立 plan review。

**报告承诺（shall）**：proposal/design/tasks/specs 显式承诺 — 若未来执行正式 TEST，最终报告 SHALL 按 strata 分别包含 `base/stage1/final` 三层 `exact_full` 与 `verify` 分别计数、`rescue_rate_stage1/stage2`、`per_stratum` 门禁明细、`undetected`、`rank/nested`、`Wilson 95%`、`runtime/iterations/residual`、`leakage` 三档分布，门禁仅用 `final` 的 `70/90` 与 `20/30` 累计量；`base/stage1` 仅分层报告。

## Non-Goals

- 不改冻结方法任一部件：`H1-16`、`L1-APP BP_i`、`Lane C` support/标签/置换/先验/MET图、`m2 184/190/192`、`H_inc1 det1`/`H_inc2 det2`/`H_joint1/H_total` 嵌套秩、`decoder 90/1.0 poly37`、`TRAIN-only prior`、`L2-only tag`、`verification-only`、`+40/80` 泄漏公式。**不测新矩阵/标签/prior/阈值/decoder参数**，新增即 `EVIDENCE_INVALID`。
- 不以 V13 HOLD 剩余帧冒充独立 TEST；不将 VAL/HOLD 重新标记为 TEST；不因 HOLD 还有未译码帧而放宽独立性要求。
- 不做新采集执行（本变更不产生新数据文件，仅登记与校验）；不做人工模拟 TEST 数据（`np.random` 合成的 pairs 禁止计入任何 stratum 注册表）。
- 不运行 decoder（本轮所有校验为 decoder-free，G1-G7 已 PASS 且 P1-P3 仍 PASS）；不创建 `comparison_bench/outputs_comparison/formal_ir_methods/v55_*/run_01` 等正式输出；不写 production `comparison_bench/src/comparison_bench/formal_ir/v55_*.py` 模块与 CLI。
- 不做 `FER/阈值/SKR/安全/资格/晋升` 的扩大陈述；tag 仍 L2-only `≈2^-64` 工程近似；不宣称信息论安全界；不宣称复现 2026-01-21 同分布。
- 不改写/覆盖 `V38–V54` 任何已有输出与终态（只读）；本规划轮不修改 `AGENT_PROJECT_MEMORY.md / docs/decision-log.md`（仅在 `docs/decision-log.md` 预留 V55 条目占位，不写入终态）。
- 不自授 `EXECUTE_AUTH`；任何执行需独立 plan ACCEPT + 显式 `EXECUTE_AUTH`（绑定 `efd34ef...` 与 authoritative registry）。
- 不将块数改作非平衡；已 freeze `30/source` 共90，**禁换块**。

## Scope

1. **冻结方法（完全冻结，零改，V54 complete）**：`n=1024, m2=184/190/192, GF32 poly37, H1 16×1024 rank16 80b, L1-APP q_i=softmax(BP_i) via BP_i=decode_row_layered_fftqspa(H1,p_i,s1).bp_posterior_beliefs (TRAIN prior channel_counts.npz), Lane C ordinal-2, H_inc1 8×1024 det1 + H_joint1 192/198/200, H_inc2 8×1024 det2 + H_total 200/206/208, decoder 90/1.0 early-stop, verification tag_scope=l2_only compute_tag_64(empty,x2) trunc64 syndrome_ok&&tag_ok, leak_base 1064/1094/1104 leak_stage1+40 leak_stage2+80`。`exact_full=exact_u1&&exact_l2` oracle 仅统计，触发仅 verification。

2. **二阶段增量（唯一已冻变量，V55 不新增）**：`H_inc1 8×1024` 与 `H_inc2 8×1024` per source 已冻（Seed 600001-6, row≤16 col_inc≤1 无零行 E≈96, rank_joint1==m2+8 rank_total==m2+16 nested/independence 8+8）。V55 **不新增第三张增量**，不试 `Δm=4/12/16` 之外多档，不引入备选矩阵选择优。

3. **独立 TEST 样本（authoritative 90-block，冻结）**：
   - **Session 冻结**：`20260123_1M_600k_0dB` (F=2130) / `20260107_PPLN_1p5M` (F=5125) / `20260123_2M_1p2M_0dB` (F=5513)，标签 `1M_600k_0dB / 1p5M / 2M_1.2M_0dB`，**非同分布 2026-01-21**，独立跨 session TEST，三层绑定实际 acquisition
   - **处理点**：`d=1024 bw=200ps pairing=nearest rule=legacy_v1` (84d62779), 单点
   - **主样本**：每源 `B=30` 共 `90 blocks` (360 frames)，于 `all_starts=0..F-4` (K=F-3) 得 `K=2127/5122/5510`，`index_j=floor(j*(K-1)/29) j=0..29` 确定性分散，验证两两非重叠 `gap≥4` 且与 V13 及 V48-V54 零重叠
   - **标识**：`v55_authoritative_registry.json` 为唯一合法块集，`sampling_mode=deterministic_four_consecutive_frames_independent_test_v55_authoritative`，`pairs_count=1024, BLOCK_LENGTH=1024`，**禁换块/禁重采样**
   - 大型 sidecar/pairs 保留在 `comparison_bench/outputs_comparison/v55_intake_20260828/` (parquet 545280/1312000/1411328 行) 不进 Git，compact evidence 记录重建方法

4. **数据就绪门（本轮已 PASS，decoder-free，分层）**：G1 文件可读、G2 provenance完整、G3 各 stratum 明确、G4 256/frame 1024/block、G5 与 V13 及 V48-V54 完全独立、G6 V25 prior只读、G7 冻结 authoritative registry — **全 PASS**，已达 `QUALIFICATION_PLAN_READY`，停在 `EXECUTE_NOT_AUTHORIZED` 等待独立 review。

5. **预算（已冻结，180-360 硬帽360）**：`90 块` 时 `L1 90 + base 90 + stage1 0–90 + stage2 0–90 =180–360 硬帽360 (L2 90–270)`，`base` 兼 old 不重复，每块 `L1 1+base1+stage1≤1+stage2≤1`。

6. **门禁与终态（已冻结）**：`coverage ≥70/90 ∧ per-source ≥20/30 ∧ undetected==0 ∧ rank/nested/verification/记账` 均过 → `V55_INDEPENDENT_TEST_PASS` (仅称 independent cross-session qualification evidence)；否则 `FAIL`；完整性/守卫失败 → `EVIDENCE_INVALID`；`base/stage1` 仅分层报告，最终以 `base→Δ16` 主判，`stage1` 报告不取代最终；`Wilson/rescue/runtime/leakage` 仅报告；不扩大为 FER/SKR/promotion，不宣称同分布复现。

7. **Lifecycle 冻结**：`QUALIFICATION_PLAN_READY / EXECUTE_NOT_AUTHORIZED`，`implementation_started=false`，任何执行需独立 plan ACCEPT + 显式 `EXECUTE_AUTH` 绑定到精确实现 SHA（plan 引用 `efd34ef...` 与 authoritative registry）；本轮仅四工件+compact intake 证据，方法冻结不变，等待独立 plan review。

## Impact Scope

- **新增/修订（本轮）**：`openspec/changes/formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation/` 四工件修订至 `QUALIFICATION_PLAN_READY` + `intake_compact_evidence.md` (紧凑 intake 证据, 含 provenance/结构统计/生成命令/路径/行数/重建方法) + `v55_authoritative_registry.json` (唯一 authoritative 90-block, 30/source, frame_ids/ordinal frozen, ban block switch)；原 `data_readiness_report.md` 保留为历史候记，`data_readiness_result.json` 更新为 READY
- **未来实现（本轮不创建，仅预冻结接口）**：`comparison_bench/src/comparison_bench/formal_ir/v55_two_stage_rescue_independent_test.py`（仅组合 V54 冻结方法+authoritative 90-block+三阶段条件 runner，不新增 decoder）+ `scripts/execute_v55_independent_test.py`；均直接 import `v38_architecture_triage` (Lane C) 与 `v35_algorithm_development::compute_tag_64`，**仅当独立 plan ACCEPT + EXECUTE_AUTH 后才允许创建**
- **只读依赖**：`v38_architecture_triage.py` (Lane C 常量/构造器)、`v35_algorithm_development.py` (tag/Field)、`nonbinary_v31.py` (H1)、`load_v25_channel_counts()` (TRAIN prior)、`comparison_bench/outputs_comparison/v55_intake_20260828/` (intake sidecars/pairs，已验证结构)、authoritative registry
- **不修改**：任何既有 spec/代码/测试/输出、`V38–V54` 输出、`outputs_comparison`/`workspace`/`AGENT_PROJECT_MEMORY.md`/`docs/decision-log.md` 以外；不 import `v50/v51/v52/v53/v54` 模块作生产解码；不创建正式 TEST `run_01` 输出

## Acceptance Criteria

- [ ] 四工件齐全一致且 lifecycle 为 `QUALIFICATION_PLAN_READY / EXECUTE_NOT_AUTHORIZED`，plan HEAD 绑定 `efd34ef318014e1d0505605062057b042e2180eb`，data SHA `84d62779` (200ps legacy_v1) 已记录，`implementation_started=false`，`production_outputs_created=false`，明确“不实现不执行不创建 run_01，等待独立 plan review；严格 decoder-free；authoritative 90-block 已冻结”
- [ ] 方法完全冻结可机械校验：`H1-16 rank16`、`L1-APP BP`、`Lane C m2 184/190/192 support/标签/置换` 零改、`H_inc1 8×1024 det1 / H_joint1 192/198/200`、`H_inc2 8×1024 det2 / H_total 200/206/208`、`decoder 90/1.0 poly37`、`leak_base 1064/1094/1104 leak_stage1+40 leak_stage2+80`、`tag L2-only`、`TRAIN-only`、`verification-only`、`Δm=8+8` 唯一且禁止新造第二张外候选
- [ ] Intake 紧凑证据已提交：`intake_compact_evidence.md` 含三源 `.ttbin/.1.ttbin` 同源 provenance (sha256/size)、结构统计 `frames×256` (545280/1312000/1411328) `0..1023` 范围 排序无缺失、生成命令 `python workspace/v55_intake_20260828/v55_decoder_free_intake.py` 路径 `comparison_bench/outputs_comparison/v55_intake_20260828/sidecars|pairs` 行数 重建方法 `_read_ttbin_timetags->...`；大型 sidecar/pairs 未进 Git 但可重建
- [ ] Registry authoritative 已冻结：`v55_authoritative_registry.json` 为唯一合法 90-block (30/source, K=2127/5122/5510, index_j floor 分散, gap≥4, frame_ids/ordinal frozen, sampling_mode authoritative, 禁换块)，candidate 已提升为 authoritative
- [ ] 数据就绪门已 PASS：G1-G7 7项 decoder-free 按 strata 全 PASS，冻结标签 `1M_600k_0dB / 1p5M / 2M_1.2M_0dB` 非同分布 2026-01-21、200ps 单点、90块 frame_ids/ordinal；脚本零 decoder 调用
- [ ] 预算已冻结：`90 块` 时 `L1 90+base90+stage1≤90+stage2≤90=180-360 硬帽360 (L2 90-270)`，`base`兼old不重复
- [ ] 预注册门禁已冻结：`coverage ≥70/90 ∧ per-source ≥20/30 ∧ undetected==0 ∧ rank/nested/verification/记账` 均过才 `PASS`，否则 `FAIL`，完整性失败 `EVIDENCE_INVALID`；`base` 与 `stage1` 仅分层报告，最终以 `base→Δ16` 主判，`stage1` 不取代最终；`Wilson/rescue/runtime/leakage` 仅报告；PASS 仅称 independent cross-session qualification evidence，不扩大为 FER/SKR/promotion，不宣称同分布复现
- [ ] 本轮产出边界已冻结：仅四工件+compact intake 证据 + authoritative registry，**禁 production module/CLI/tests/正式output root/执行decoder/自授EXECUTE_AUTH**；decoder-free P1-P3 仍 PASS
- [ ] 已推送并停在 `QUALIFICATION_PLAN_READY / EXECUTE_NOT_AUTHORIZED` 等待独立 plan review

## Tasks

见 `tasks.md`（Phase A 冻结 V54 方法零改；Phase B intake 3/3 READY 紧凑证据固化；Phase C authoritative 90-block 冻结；Phase D G1-G7 decoder-free 全 PASS；Phase E 预算/门禁/claim 冻结；Phase F 本轮四工件+compact 证据交付至 QUALIFICATION_PLAN_READY；Phase G 需独立 plan ACCEPT + EXECUTE_AUTH 的 90 块三阶段条件执行 180-360 calls；显式禁止清单）。

## Lifecycle

前代 `formal-ir-v54-two-stage-incremental-l2-rescue` (plan HEAD `bf5dd168...`, branch `formal-ir-mainline`，`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`)；V55 当前 `QUALIFICATION_PLAN_READY / EXECUTE_NOT_AUTHORIZED`（HEAD `efd34ef318014e1d0505605062057b042e2180eb`，branch `formal-ir-mainline`，data SHA `84d62779` 200ps legacy_v1），intake 3/3 READY + G1-G7 全 PASS + authoritative 90-block 已冻，等待独立 plan review；实现候选止于 `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`；任何执行需显式用户 `EXECUTE_AUTH` 绑定到精确未来实现 SHA + authoritative registry；本轮仅四工件+compact intake 证据，方法冻结不变，推后停在 `QUALIFICATION_PLAN_READY`。
