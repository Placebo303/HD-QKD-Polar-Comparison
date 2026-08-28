# OpenSpec Proposal: formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation

**Status**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **仅规划与数据就绪资格准备，不实现新方法，不执行 decoder，不创建正式 TEST run_01。等待独立复审与数据就绪裁决。**
**Domain**: Formal IR / V55 独立 TEST 资格准备（V54 二阶段 rescue 的独立采集验证资格门）
**Change ID**: `formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation`
**Cycle ID**: `V55P0`
**Predecessor**: `formal-ir-v54-two-stage-incremental-l2-rescue` (plan HEAD `bf5dd1686049156540328bac264296b17fee546c`, branch `formal-ir-mainline`), **本变更 plan HEAD** `efd34ef318014e1d0505605062057b042e2180eb` (branch `formal-ir-mainline`)
**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`, `implementation_started=false`, `production_outputs_created=false`, `formal_execution_authorized=false`, `data_ready=false` (待 decoder-free 5号门实测)
**V54 history**: V54 二阶段 `H1-16 + L1-APP + Lane C + m2 184/190/192 + H_inc1 8 + H_inc2 8 + base→Δ8→Δ16 verification-only + decoder 90/1.0 poly37 + TRAIN-only prior + L2-only 64-bit tag + 每增量+40` 已冻结为唯一性能候选；V55 **不测任何新矩阵/标签/prior/阈值/decoder参数**，仅准备其独立 TEST 资格。

> ponytail lite: 本轮仅四 OpenSpec 工件 + 可选 decoder-free 数据清单脚本/报告；更懒路径是零新增文档直接宣告 HOLD 剩余帧可用，需独立评审确认“ HOLD 已污染不可复用、必须新采集 session”这一裁决是否值得新增数据采集成本。

## Goal

在**完全冻结 V54 二阶段性能候选**的前提下，回答资格准备的唯一问题：

> **V54 冻结方法是否已具备进入独立 TEST 的“数据就绪”资格？若否，缺什么数据才算准备好？若是，如何以确定性、可复现、decoder-free 的方式冻结 90-block 独立 TEST 注册表并预注册门禁与预算，使后续正式 TEST 一次通过即可判定 `V55_INDEPENDENT_TEST_PASS`？**

1. **方法完全冻结（零改）**：`H1-16 (V31-H1-QC rank16) + L1-APP syndrome-derived BP_i via H1 (TRAIN prior) + Lane C support/标签/置换/MET图 (ordinal-2 s38310x) + m2 184(1M)/190(1p5M)/192(2M) + H_inc1 8×1024 det1 (Seed 600001-3) + H_inc2 8×1024 det2 (Seed 600004-6) + H_base(m2)/H_joint1(m2+8)/H_total(m2+16) 嵌套 rank m2/m2+8/m2+16 + decoder 90/1.0 poly37 early-stop + TRAIN-only prior (V25 channel_counts.npz) + L2-only 64-bit tag `compute_tag_64(empty,x2)` + verification-only 触发 (`syndrome_ok && tag_ok` 才增量) + 每增量 +40 bits (`leak_base 1064/1094/1104 → stage1 1104/1134/1144 → stage2 1144/1174/1184`)**。V55 **不测新矩阵/标签/prior/阈值/decoder ITA**，任何新矩阵即判 `EVIDENCE_INVALID`。

2. **数据裁决（当前定性）**：V13 `60/20/20 (TRAIN/VAL/HOLD)` 中 **HOLD 已被 V48-V54 多轮开发使用**（V48 45块 + V50 15 + V51 15 + V52 15 + V53 45 + V54 45 = 180块待定，含 V48-V54 已用 135-180 区间），**即使 HOLD 仍有未译码剩余帧，也不得改称为独立 TEST**（开发污染不可逆）。P0 必须**搜索/登记另一独立采集 session**（与 `2026-01-21 V13` 不同日期/采集），若搜索后**无可用新 session**，则本变更终态为 **`V55_DATA_NOT_READY`（非失败，需新数据）**，**不得创建 production runner / tests / 正式 output root，不得用 HOLD 冒充 TEST，不得模拟 TEST 数据**。

3. **合格 TEST 要求（建议，非本轮执行）**：建议每源（1M/1p5M/2M）**各一个与 2026-01-21 V13 不同的独立采集 session**，每源 **≥120 frames（建议≥160）**，每帧 **256 pairs**（32B 每符号 ×8？以现有 `pairs.parquet` 每帧 256 行计），每块 **4 连续帧 =1024 pairs (`BLOCK_LENGTH=1024`)**，**不进入 prior 训练/方法选择/阈值调优**，**冻结前不得看解码结果**（先冻结注册表，再译码）。主样本冻结为 **30 blocks/source 共 90 blocks 360 frames 确定性分散非重叠四帧窗口**，**禁换块/禁重采样/禁跨源混用**。

4. **数据就绪门（仅 decoder-free，本轮唯一可实测门）**：以下 7 项全过才 `V55_QUALIFICATION_PLAN_READY`，否则 `V55_DATA_NOT_READY`：
   - (G1) 新 session 文件可读（parquet/csv 可 open，行数=frames×256）
   - (G2) provenance 完整（三源明确标识、采集日期≠2026-01-21、session_id/采集参数/文件哈希可追溯）
   - (G3) 三源明确且互异（1M/1p5M/2M 各一 session，延迟 `±50ps` 等元数据一致）
   - (G4) 每帧 256 pairs、每块 1024 pairs 形态校验
   - (G5) 与 V13 全部帧 **及 V48-V54 已用 held-out 180 区间帧完全独立**（frame_id/全局偏移零重叠，per source 机械校验）
   - (G6) V25 prior 只读（`channel_counts.npz` 形态校验，不读新 TEST 做训练）
   - (G7) 冻结 90-block registry（30/源，分散 `index_j=floor(j*(K2-1)/29)` 或等价确定性分散，两两非重叠 gap≥4，可机械校验）
   全过才可进入后续正式 TEST 规划；不过则停留 `DATA_NOT_READY`，不进入 decoder。

5. **后续正式 TEST 预算（预冻结，不在本轮执行）**：`L1 90 + base L2 90 + stage1 0-90 + stage2 0-90 = 180-360 calls 硬帽 360`，其中 `L2 90-270`。`base` 兼 `old Lane C` 语义，同一次译码不重复计费；`stage1` 仅对 `!verify_base` 者，`stage2` 仅对 `!verify_base && !verify_stage1` 者。

6. **预注册门禁（预冻结，不在本轮执行）**：`overall exact_full ≥70/90 (77.8%) 且每源 ≥20/30 (66.7%) 且 undetected==0 且 rank/nested/verification/记账通过`，**base/stage1 仅诊断**，最终以 **`base→Δ16`（即 `final = base + stage1_rescued + stage2_rescued`，`leak_final` 为 `leak_base / leak_base+40 / leak_base+80` 三档条件）为主判**，`stage1` 中间报告不取代最终；`Wilson 区间 / rescue_rate / runtime / 泄漏` 仅报告不作门禁。**四终态**：`V55_INDEPENDENT_TEST_PASS` / `V55_INDEPENDENT_TEST_FAIL` / `V55_EVIDENCE_INVALID`，另有 **非失败终态 `V55_DATA_NOT_READY`**（数据缺失时）。

7. **本轮止于 PLAN**：只产出四 OpenSpec 工件 + 可选 decoder-free 数据清单脚本及报告（`check_v55_data_readiness.py` + `data_readiness_report.md`），**禁 production module/CLI/tests/正式 output root/用 HOLD 冒充 TEST/模拟 TEST/执行 decoder/自授 PLAN_ACCEPTED**。关键判断已写入 claim boundary：**算法主线已足够好，当前 blocker 是独立 TEST 数据缺失，而非方法本身**。

**报告承诺（shall）**：proposal/design/tasks/specs 显式承诺 — 若未来数据就绪并执行正式 TEST，最终报告 SHALL 包含 `base/stage1/final` 三层 `exact_full` 与 `verify` 分别计数、`rescue_rate_stage1/stage2`、`per_source 20/30`、`undetected`、`rank/nested`、`Wilson 95%`、`runtime/iterations/residual`、`leakage` 三档分布，门禁仅用 `final` 累计量；`V55_DATA_NOT_READY` 时报告 SHALL 仅含数据清单与缺口分析，不含任何 decoder 结果。

## Non-Goals

- 不改冻结方法任一部件：`H1-16`、`L1-APP BP_i`、`Lane C` support/标签/置换/先验/MET图、`m2 184/190/192`、`H_inc1 det1`/`H_inc2 det2`/`H_joint1/H_total` 嵌套秩、`decoder 90/1.0 poly37`、`TRAIN-only prior`、`L2-only tag`、`verification-only`、`+40/80` 泄漏公式。**不测新矩阵/标签/prior/阈值/decoder参数**，新增即 `EVIDENCE_INVALID`。
- 不以 V13 HOLD 剩余帧冒充独立 TEST；不将 VAL/HOLD 重新标记为 TEST；不因 HOLD 还有未译码帧而放宽独立性要求。
- 不做新采集执行（本变更不产生新数据文件，仅登记与校验）；不做人工模拟 TEST 数据（`np.random` 合成的 pairs 禁止计入 90-block 注册表）。
- 不运行 decoder（本轮所有校验为 decoder-free）；不创建 `comparison_bench/outputs_comparison/formal_ir_methods/v55_*/run_01` 等正式输出；不写 production `comparison_bench/src/comparison_bench/formal_ir/v55_*.py` 模块与 CLI。
- 不做 `FER/阈值/SKR/安全/资格/晋升` 的扩大陈述；tag 仍 L2-only `≈2^-64` 工程近似；不宣称信息论安全界。
- 不改写/覆盖 `V38–V54` 任何已有输出与终态（只读）；本规划轮不修改 `AGENT_PROJECT_MEMORY.md / docs/decision-log.md`（仅在 `docs/decision-log.md` 预留 V55 条目占位，不写入终态）。
- 不自授 `PLAN_ACCEPTED`；任何实现/执行需独立 plan ACCEPT + 显式 `EXECUTE_AUTH`（绑定 `efd34ef...`）。

## Scope

1. **冻结方法（完全冻结，零改，V54 complete）**：`n=1024, m2=184/190/192, GF32 poly37, H1 16×1024 rank16 80b, L1-APP q_i=softmax(BP_i) via BP_i=decode_row_layered_fftqspa(H1,p_i,s1).bp_posterior_beliefs (TRAIN prior channel_counts.npz), Lane C ordinal-2, H_inc1 8×1024 det1 + H_joint1 192/198/200, H_inc2 8×1024 det2 + H_total 200/206/208, decoder 90/1.0 early-stop, verification tag_scope=l2_only compute_tag_64(empty,x2) trunc64 syndrome_ok&&tag_ok, leak_base 1064/1094/1104 leak_stage1+40 leak_stage2+80`。`exact_full=exact_u1&&exact_l2` oracle 仅统计，触发仅 verification。

2. **二阶段增量（唯一已冻变量，V55 不新增）**：`H_inc1 8×1024` 与 `H_inc2 8×1024` per source 已冻（Seed 600001-6, row≤16 col_inc≤1 无零行 E≈96, rank_joint1==m2+8 rank_total==m2+16 nested/independence 8+8）。V55 **不新增第三张增量**，不试 `Δm=4/12/16` 之外多档，不引入备选矩阵选择优。

3. **独立 TEST 样本（冻结注册算法，排除 V13 与 V48-V54）**：
   - 建议每源各一独立 session（≠2026-01-21 V13），每源 ≥120 frames 建议≥160，每帧 256 pairs，每块 4 连续帧 1024 pairs，不入 prior/方法选择，冻结前不看解码结果。
   - 主样本：`30 blocks/source ×3 =90 blocks, 360 frames`，于新 session 内枚举 `all_starts=0..F-4`（F=每源总帧数），过滤与已用区间重叠者得 `S2` 按 ordinal 排序 `K=|S2|`，以 `index_j=floor(j*(K-1)/29) j=0..29` 确定性分散选择 30/源，验证两两非重叠 gap≥4 且与 V13 及 V48-V54 零重叠。
   - 建议 block IDs `395xxx` 延续但真实以 `frame_ids[4]` 为准，`sampling_mode=deterministic_four_consecutive_frames_independent_test_v55`，`pairs_count=1024, BLOCK_LENGTH=1024`。

4. **数据就绪门（本轮唯一实测，decoder-free）**：G1 文件可读、G2 provenance完整、G3 三源明确、G4 256/frame 1024/block、G5 与 V13 及 V48-V54 完全独立、G6 V25 prior只读、G7 冻结 90-block registry。全过 → `V55_QUALIFICATION_PLAN_READY`，否则 `V55_DATA_NOT_READY`（非失败，需新数据）。

5. **预算（预冻结）**：`L1 90 + base 90 + stage1 0-90 + stage2 0-90 =180-360 硬帽360 (L2 90-270)`，`base` 兼 old 不重复；`per block 2-4 calls`。

6. **门禁与四终态（预冻结）**：`G1 overall≥70/90, G2 每源≥20/30, G3 undetected==0, G4 rank/nested/verification/记账` 均过 → `V55_INDEPENDENT_TEST_PASS`；否则 `FAIL`；完整性/守卫失败 → `EVIDENCE_INVALID`；数据缺失 → `DATA_NOT_READY`（非失败）。`base/stage1` 仅诊断，最终以 `base→Δ16` 主判，`stage1` 报告不取代最终；`Wilson (95%)/rescue_rate/runtime/leakage` 仅报告。

7. **Lifecycle 冻结**：`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`，`implementation_started=false`，任何实现/执行（含数据就绪后的正式 TEST）需独立 plan ACCEPT + 显式 `EXECUTE_AUTH` 绑定到精确实现 SHA（plan 引用 `efd34ef...`）；不启动下一阶段；本轮仅四工件+decoder-free 清单脚本/报告。

## Impact Scope

- **新增（本轮）**：`openspec/changes/formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation/` 四工件（`proposal.md, design.md, tasks.md, specs/spec.md`）+ 可选 `check_v55_data_readiness.py`（decoder-free 数据清单脚本）+ `data_readiness_report.md`（decoder-free 报告，含 G1-G7逐项结果与 `V55_DATA_NOT_READY` 缺口分析）。
- **未来实现（本轮不创建，仅预冻结接口）**：`comparison_bench/src/comparison_bench/formal_ir/v55_two_stage_rescue_independent_test.py`（仅组合 V54 冻结方法+90-block 独立 TEST 注册表+三阶段条件 runner，不新增 decoder）+ `scripts/execute_v55_independent_test.py`；均直接 import `v38_architecture_triage` (Lane C) 与 `v35_algorithm_development::compute_tag_64`，**仅当 `V55_QUALIFICATION_PLAN_READY` 后才允许创建**。
- **只读依赖**：`v38_architecture_triage.py` (Lane C 常量/构造器)、`v35_algorithm_development.py` (tag/Field)、`nonbinary_v31.py` (H1)、`load_v25_channel_counts()` (TRAIN prior)、V13 `split_manifest.json` 与已用 `frame_ids` 清单（V48-V54 135-180 区间）、新 session 待登记清单（外部采集目录）。
- **不修改**：任何既有 spec/代码/测试/输出、`V38–V54` 输出、`outputs_comparison`/`workspace`/`AGENT_PROJECT_MEMORY.md`/`docs/decision-log.md` 以外；不 import `v50/v51/v52/v53/v54` 模块作生产解码；不创建正式 TEST `run_01` 输出。

## Acceptance Criteria

- [ ] 四工件齐全一致且 lifecycle 为 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`，plan HEAD 绑定 `efd34ef318014e1d0505605062057b042e2180eb`，`implementation_started=false`，`production_outputs_created=false`，明确“不实现不执行不创建 run_01，等待独立评审与数据就绪裁决；严格 decoder-free”。
- [ ] 方法完全冻结可机械校验：`H1-16 rank16`、`L1-APP BP`、`Lane C m2 184/190/192 support/标签/置换` 零改、`H_inc1 8×1024 det1 / H_joint1 192/198/200`、`H_inc2 8×1024 det2 / H_total 200/206/208`、`decoder 90/1.0 poly37`、`leak_base 1064/1094/1104 leak_stage1+40 leak_stage2+80`、`tag L2-only`、`TRAIN-only`、`verification-only`、`Δm=8+8` 唯一且禁止新造第二张外候选；V55 **不测新矩阵/标签/prior/阈值** 已显式冻结。
- [ ] 数据裁决可机械校验：`HOLD 已污染` 结论写入 proposal/design/spec，`V48-V54 已用区间 135-180` 清单可追溯，即使 HOLD 剩余帧未译码也不得改称 TEST；P0 登记新 session 的搜索路径与 `V55_DATA_NOT_READY` 非失败语义已冻结。
- [ ] 合格 TEST 要求冻结：每源各一独立 session（≠2026-01-21 V13）、每源≥120 frames 建议≥160、每帧256 pairs、每块4连续帧1024 pairs、不入 prior/方法选择、冻结前不看解码结果、主样本 `30/源共90块360帧` 确定性分散非重叠四帧窗口、禁换块已写入 design/spec。
- [ ] 数据就绪门冻结：G1-G7 7项 decoder-free 检查（文件可读、provenance完整、三源明确、256/frame 1024/block、与V13及V48-V54完全独立、V25 prior只读、冻结90-block registry）全过才 `V55_QUALIFICATION_PLAN_READY` 否则 `V55_DATA_NOT_READY`，脚本零 decoder 调用，失败非零退出。
- [ ] 预算冻结：`L1 90 + base90 + stage1 0-90 + stage2 0-90 =180-360 硬帽360 (L2 90-270)`，`base`兼old不重复，每块 `L1 1+base 1+stage1≤1+stage2≤1`。
- [ ] 预注册门禁冻结：`overall≥70/90 且每源≥20/30 且 undetected==0 且 rank/nested/verification/记账` 均过才 `PASS`，否则 `FAIL`，完整性失败 `EVIDENCE_INVALID`，数据缺失 `DATA_NOT_READY`；`base/stage1` 仅诊断，最终以 `base→Δ16` 主判，`stage1` 不取代最终；`Wilson/rescue/runtime/泄漏` 仅报告。
- [ ] 本轮产出边界冻结：仅四工件+可选 decoder-free 清单脚本/报告，**禁 production module/CLI/tests/正式output root/用HOLD冒充/模拟TEST/执行decoder/自授PLAN_ACCEPTED**；claim boundary 写入“算法主线已足够好，blocker是独立TEST数据缺失”。
- [ ] 可选脚本/报告（如创建）为 decoder-free：仅文件/形态/独立性/registry 检查，零 `import decoder`，零 `decode_*` 调用，`sys.exit(1)` 于任一 G 门失败，报告含逐项 PASS/FAIL 与缺口分析。

## Tasks

见 `tasks.md`（Phase A 冻结 V54 方法零改；Phase B 数据裁决与新 session 搜索；Phase C 独立 TEST 90-block 注册算法冻结；Phase D 数据就绪门 G1-G7 decoder-free 校验；Phase E 预算/门禁/四终态预注册；Phase F 本轮四工件+清单脚本/报告交付；Phase G 需 DATA_READY + EXECUTE_AUTH 的至多 90块三阶段条件执行 180-360 calls；显式禁止清单）。

## Lifecycle

前代 `formal-ir-v54-two-stage-incremental-l2-rescue` (plan HEAD `bf5dd168...`, branch `formal-ir-mainline`，`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`)；V55 当前 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`（HEAD `efd34ef318014e1d0505605062057b042e2180eb`，branch `formal-ir-mainline`），保持不实现不执行、等待独立复审与数据就绪裁决；实现候选止于 `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`；任何执行需显式用户 `EXECUTE_AUTH` 绑定到精确未来实现 SHA；数据就绪后 `V55_QUALIFICATION_PLAN_READY` 方可进入正式 TEST 详细规划与执行，否则 `V55_DATA_NOT_READY`（非失败，需新数据）。本轮仅四工件+decoder-free 清单脚本/报告，方法冻结不变，仅数据资格为 blocker。
