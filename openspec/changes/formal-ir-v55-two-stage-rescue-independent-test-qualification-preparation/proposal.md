# OpenSpec Proposal: formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation

**Status**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **仅规划与数据就绪资格准备，不实现新方法，不执行 decoder，不创建正式 TEST run_01。等待独立复审与数据就绪裁决。**
**Domain**: Formal IR / V55 独立 TEST 资格准备（V54 二阶段 rescue 的独立采集验证资格门，分层 strata 修订版）
**Change ID**: `formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation`
**Cycle ID**: `V55P0`
**Predecessor**: `formal-ir-v54-two-stage-incremental-l2-rescue` (plan HEAD `bf5dd1686049156540328bac264296b17fee546c`, branch `formal-ir-mainline`), **本变更 plan HEAD** `efd34ef318014e1d0505605062057b042e2180eb` (branch `formal-ir-mainline`) — 本次分层修订保持同一 plan HEAD 绑定与 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`，仅重构 TEST 注册为分层方案
**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`, `implementation_started=false`, `production_outputs_created=false`, `formal_execution_authorized=false`, `data_ready=false` (待 decoder-free 分层 G1-G7 实测；预期仍 `V55_DATA_NOT_READY` 因尚无新数据)
**V54 history**: V54 二阶段 `H1-16 + L1-APP + Lane C + m2 184/190/192 + H_inc1 8 + H_inc2 8 + base→Δ8→Δ16 verification-only + decoder 90/1.0 poly37 + TRAIN-only prior + L2-only 64-bit tag + 每增量+40` 已冻结为唯一性能候选；V55 **不测任何新矩阵/标签/prior/阈值/decoder参数**，仅准备其独立 TEST 资格。

> ponytail lite: 本轮仅四 OpenSpec 工件 + 可选 decoder-free 数据清单脚本/报告；更懒路径是零新增文档直接宣告 HOLD 剩余帧可用，需独立评审确认“ HOLD 已污染不可复用、必须新采集 session”这一裁决是否值得新增数据采集成本。

## Goal

在**完全冻结 V54 二阶段性能候选**的前提下，回答资格准备的唯一问题：

> **V54 冻结方法是否已具备进入独立 TEST 的“数据就绪”资格？若否，缺什么数据才算准备好？若是，如何以确定性、可复现、decoder-free 的方式冻结分层独立 TEST 注册表并预注册门禁与预算，使后续正式 TEST 一次通过即可判定 `V55_INDEPENDENT_TEST_PASS`？**

1. **方法完全冻结（零改）**：`H1-16 (V31-H1-QC rank16) + L1-APP syndrome-derived BP_i via H1 (TRAIN prior) + Lane C support/标签/置换/MET图 (ordinal-2 s38310x) + m2 184(1M)/190(1p5M)/192(2M) + H_inc1 8×1024 det1 (Seed 600001-3) + H_inc2 8×1024 det2 (Seed 600004-6) + H_base(m2)/H_joint1(m2+8)/H_total(m2+16) 嵌套 rank m2/m2+8/m2+16 + decoder 90/1.0 poly37 early-stop + TRAIN-only prior (V25 channel_counts.npz) + L2-only 64-bit tag `compute_tag_64(empty,x2)` + verification-only 触发 (`syndrome_ok && tag_ok` 才增量) + 每增量 +40 bits (`leak_base 1064/1094/1104 → stage1 1104/1134/1144 → stage2 1144/1174/1184`)**。V55 **不测新矩阵/标签/prior/阈值/decoder ITA**，任何新矩阵即判 `EVIDENCE_INVALID`。

2. **数据裁决（当前定性）**：V13 `60/20/20 (TRAIN/VAL/HOLD)` 中 **HOLD 已被 V48-V54 多轮开发使用**（V48 45块 + V50 15 + V51 15 + V52 15 + V53 45 + V54 45 = 180块待定，含 V48-V54 已用 135-180 区间），**即使 HOLD 仍有未译码剩余帧，也不得改称为独立 TEST**（开发污染不可逆）。P0 必须**搜索/登记另一独立采集 session 集合**（与 `2026-01-21 V13` 不同日期/采集），若搜索后**无可用新 session**，则本变更终态为 **`V55_DATA_NOT_READY`（非失败，需新数据，分层）**，**不得创建 production runner / tests / 正式 output root，不得用 HOLD 冒充 TEST，不得模拟 TEST 数据**。

3. **合格 TEST 要求（分层 stratum，建议，非本轮执行）**：
   - **先清单**：列出所有可用的其他独立数据集及其物理条件（采集日期/地点/器件/信道参数：延迟 ±50ps、功率/率 1M/1p5M/2M、光纤/衰减、温度等 provenance 字段），形成 `available_independent_datasets` 库存。
   - **分层**：按物理条件分 strata，不混成一个总分。主 strata 为与 V13 对应的物理条件类型（当前目标域 `1M / 1p5M / 2M` 各一 stratum；若未来出现新地点/器件/信道参数，则新增 exploratory stratum）。
   - **每 stratum 独立**：每 stratum 建议 **≥120 frames（建议≥160）**，每帧 **256 pairs**，每块 **4 连续帧 =1024 pairs (`BLOCK_LENGTH=1024`)**，**不进入 prior 训练/方法选择/阈值调优**，**冻结前不得看解码结果**。
   - **平衡预注册**：每个主要条件预注册**相同数量 blocks** — 建议每 stratum **15 或 30**，保持平衡（例如 `3 strata ×15 =45 blocks / 180 frames` 或 `3×30=90/360`；`K/index_j` 分散算法同前，仅 `need` 改为 per-stratum）。禁止混用不同块数的非平衡注册。
   - **预算成比例**：`90-360` 概念按 strata 成比例 — 每 stratum 15 块则总 `L1 45+base45+stage1≤45+stage2≤45=90-180`，每 stratum 30 块则 `90+90+≤90+≤90=180-360`；一般 `N_strata ×B` 块对应 `2NB – 4NB` calls 硬帽。
   - **数据不足处理**：数据不足的条件只做 exploratory generalization，不强行凑 90 blocks。`G7` 冻结 registry 改为按 strata 最小块数，允许部分 strata `DATA_NOT_READY`（partial），仅足量 strata 进入 qualification，其余仅探索性报告。

4. **数据就绪门（仅 decoder-free，本轮唯一可实测门，分层扩展）**：以下 7 项按 strata 扩展，全足量 strata 过才 `V55_QUALIFICATION_PLAN_READY`，否则按 strata 判 `V55_DATA_NOT_READY`（partial 允许）：
   - (G1) 新 session 文件可读（parquet/csv 可 open，行数=frames×256）— per stratum
   - (G2) provenance 完整（三源/各 stratum 明确标识、采集日期≠2026-01-21、session_id/采集参数/文件哈希可追溯）— per stratum
   - (G3) 各 stratum 明确且互异（每物理条件各一 session，延迟等元数据一致）— 全局+per stratum
   - (G4) 每帧 256 pairs、每块 1024 pairs 形态校验 — per stratum
   - (G5) 与 V13 全部帧 **及 V48-V54 已用帧完全独立**（frame_id/全局偏移零重叠，per stratum 机械校验）
   - (G6) V25 prior 只读（`channel_counts.npz` 形态校验，不读新 TEST 做训练）— 全局一次
   - (G7) 冻结 per-stratum registry（每主要 stratum `need=15 或 30` 分散 `index_j=floor(j*(K-1)/(need-1))`，两两非重叠 gap≥4，可机械校验；`K<need` 则该 stratum `G7_FAIL → DATA_NOT_READY` 但不阻塞其他 stratum 的 exploratory）
   全足量 strata 过（覆盖目标域）才可进入后续正式 TEST 规划；不过则停留 `DATA_NOT_READY`，不进入 decoder；部分 strata READY 时仅对 READY strata 报告 exact/泄漏/rescue，资格判定需覆盖目标域。

5. **后续正式 TEST 预算（预冻结，不在本轮执行，分层成比例）**：以 `B ∈{15,30}` 为 per-stratum 块数、`S` 为目标域 strata 数（当前 `S=3`）：`L1 S×B + base S×B + stage1 0–S×B + stage2 0–S×B = 2SB – 4SB` 硬帽（`L2 SB–3SB`）。例如 `S=3,B=15 → 90-180 (L2 45-135)`；`S=3,B=30 → 180-360 (L2 90-270)`。`base` 兼 `old Lane C` 语义，同一次译码不重复计费；`stage1` 仅对 `!verify_base` 者，`stage2` 仅对 `!verify_base && !verify_stage1` 者。单 stratum 预算 `B + B + ≤B + ≤B = 2B-4B`。

6. **预注册门禁（预冻结，不在本轮执行，分层判定）**：
   - **主要报告**：各条件（per stratum）分别报告 `exact_full`、`verify`、`rescue_rate_stage1/2`、泄漏三档与 `per_stratum_avg`；不混成单一总分作首要结论。
   - **资格判定**：只有覆盖**目标运行域**（需在 design 中声明目标域为哪些 strata 组合；当前冻结目标域 `D_target = {1M, 1p5M, 2M}` 三 stratum 全覆盖）时才判 qualification。门禁改为按 strata 或覆盖域判定：
     - per-stratum 门禁（B=30 时 `≥20/30 (66.7%)`，B=15 时 `≥10/15 (66.7%)`）每目标域 stratum 均需满足；
     - coverage-domain 门禁：`overall_exact_full ≥ ceil(0.778×S×B)`（即 `70/90` 按比例：`35/45` 当 `S=3,B=15`；`70/90` 当 `S=3,B=30`）；
     - 且 **undetected==0 全局**（仍 0，任一 stratum 出现即 FAIL）且 `rank/nested/verification/记账` 通过。
   - `base/stage1` 仅诊断，最终以 **`base→Δ16`（即 `final`）为主判**，`stage1` 中间报告不取代最终；`Wilson 区间 / rescue_rate / runtime / 泄漏` 仅报告不作门禁。
   - **终态**：`V55_INDEPENDENT_TEST_PASS` / `V55_INDEPENDENT_TEST_FAIL` / `V55_EVIDENCE_INVALID`，另有 **非失败终态 `V55_DATA_NOT_READY`（分层，per stratum 或全局）**。
   - 数据不足的条件仅 exploratory，不计入 qualification 分母，不强行凑足 `S×B`。

7. **本轮止于 PLAN**：只产出四 OpenSpec 工件 + 可选 decoder-free 数据清单脚本及报告（`check_v55_data_readiness.py` + `data_readiness_report.md`，均已分层化），**禁 production module/CLI/tests/正式 output root/用 HOLD 冒充 TEST/模拟 TEST/执行 decoder/自授 PLAN_ACCEPTED**。关键判断已写入 claim boundary：**算法主线已足够好，当前 blocker 是独立 TEST 数据缺失（分层视角），而非方法本身**。

**报告承诺（shall）**：proposal/design/tasks/specs 显式承诺 — 若未来数据就绪并执行正式 TEST，最终报告 SHALL 按 strata 分别包含 `base/stage1/final` 三层 `exact_full` 与 `verify` 分别计数、`rescue_rate_stage1/stage2`、`per_stratum` 门禁明细、`undetected`、`rank/nested`、`Wilson 95%`、`runtime/iterations/residual`、`leakage` 三档分布，门禁仅用 `final` 的 per-stratum 与 coverage-domain 累计量；`V55_DATA_NOT_READY`（含 partial）时报告 SHALL 仅含分层数据清单与缺口分析，不含任何 decoder 结果。

## Non-Goals

- 不改冻结方法任一部件：`H1-16`、`L1-APP BP_i`、`Lane C` support/标签/置换/先验/MET图、`m2 184/190/192`、`H_inc1 det1`/`H_inc2 det2`/`H_joint1/H_total` 嵌套秩、`decoder 90/1.0 poly37`、`TRAIN-only prior`、`L2-only tag`、`verification-only`、`+40/80` 泄漏公式。**不测新矩阵/标签/prior/阈值/decoder参数**，新增即 `EVIDENCE_INVALID`。
- 不以 V13 HOLD 剩余帧冒充独立 TEST；不将 VAL/HOLD 重新标记为 TEST；不因 HOLD 还有未译码帧而放宽独立性要求。
- 不做新采集执行（本变更不产生新数据文件，仅登记与校验）；不做人工模拟 TEST 数据（`np.random` 合成的 pairs 禁止计入任何 stratum 注册表）。
- 不运行 decoder（本轮所有校验为 decoder-free，含分层 G1-G7）；不创建 `comparison_bench/outputs_comparison/formal_ir_methods/v55_*/run_01` 等正式输出；不写 production `comparison_bench/src/comparison_bench/formal_ir/v55_*.py` 模块与 CLI。
- 不做 `FER/阈值/SKR/安全/资格/晋升` 的扩大陈述；tag 仍 L2-only `≈2^-64` 工程近似；不宣称信息论安全界。
- 不改写/覆盖 `V38–V54` 任何已有输出与终态（只读）；本规划轮不修改 `AGENT_PROJECT_MEMORY.md / docs/decision-log.md`（仅在 `docs/decision-log.md` 预留 V55 条目占位，不写入终态）。
- 不自授 `PLAN_ACCEPTED`；任何实现/执行需独立 plan ACCEPT + 显式 `EXECUTE_AUTH`（绑定 `efd34ef...`）。
- 不将不足数据的 strata 强行凑足 `S×B` 去混算总分；不足 strata 仅 exploratory，不纳入 qualification 判定。

## Scope

1. **冻结方法（完全冻结，零改，V54 complete）**：`n=1024, m2=184/190/192, GF32 poly37, H1 16×1024 rank16 80b, L1-APP q_i=softmax(BP_i) via BP_i=decode_row_layered_fftqspa(H1,p_i,s1).bp_posterior_beliefs (TRAIN prior channel_counts.npz), Lane C ordinal-2, H_inc1 8×1024 det1 + H_joint1 192/198/200, H_inc2 8×1024 det2 + H_total 200/206/208, decoder 90/1.0 early-stop, verification tag_scope=l2_only compute_tag_64(empty,x2) trunc64 syndrome_ok&&tag_ok, leak_base 1064/1094/1104 leak_stage1+40 leak_stage2+80`。`exact_full=exact_u1&&exact_l2` oracle 仅统计，触发仅 verification。

2. **二阶段增量（唯一已冻变量，V55 不新增）**：`H_inc1 8×1024` 与 `H_inc2 8×1024` per source 已冻（Seed 600001-6, row≤16 col_inc≤1 无零行 E≈96, rank_joint1==m2+8 rank_total==m2+16 nested/independence 8+8）。V55 **不新增第三张增量**，不试 `Δm=4/12/16` 之外多档，不引入备选矩阵选择优。

3. **独立 TEST 样本（分层冻结注册算法，排除 V13 与 V48-V54）**：
   - **清单**：先枚举 `PROJECT_DATA_ROOT` / `comparison_bench/configs/` / 外部目录中所有可用的其他独立数据集，记录每数据集的 `session_id / 采集日期 / 地点 / 器件 / 延迟±50ps / 功率/率 / 信道参数 / 文件哈希`，形成 `available_independent_datasets` 库存（decoder-free）。
   - **分层**：按物理条件分 strata（当前目标域 `D_target={1M,1p5M,2M}` 三 strata；新增物理条件按 strata 扩展），不混成单一总分。
   - 建议每 stratum 各一独立 session（≠2026-01-21 V13），每 stratum **≥120 frames 建议≥160**，每帧 256 pairs，每块 4 连续帧 1024 pairs，不入 prior/方法选择，冻结前不看解码结果。
   - 主样本：**每主要 stratum `B=15 或 30` blocks**（平衡），`S=3` 时共 `45 或 90 blocks`（`180 或 360 frames`），于新 session 内枚举 `all_starts=0..F-4`（F=每 stratum 总帧数），过滤与已用区间重叠者得 `S2` 按 ordinal 排序 `K=|S2|`，以 `index_j=floor(j*(K-1)/(need-1)) j=0..need-1` 确定性分散选择 `need=B` 块/ stratum，验证两两非重叠 gap≥4 且与 V13 及 V48-V54 零重叠。
   - 建议 block IDs 按 stratum 延续（如 `396001-030 / 396101-130 / 396201-230` 当 B=30；`397001-015` 等当 B=15）但真实以 `frame_ids[4]` 为准，`sampling_mode=deterministic_four_consecutive_frames_independent_test_v55_stratified`，`pairs_count=1024, BLOCK_LENGTH=1024`。
   - 数据不足的 stratum 仅 exploratory，不强行凑 `S×B`；`G7` 按 strata 最小块数判定，允许部分 strata `DATA_NOT_READY`。

4. **数据就绪门（本轮唯一实测，decoder-free，分层）**：G1 文件可读、G2 provenance完整、G3 各 stratum 明确、G4 256/frame 1024/block、G5 与 V13 及 V48-V54 完全独立、G6 V25 prior只读、G7 冻结 per-stratum registry — **按 strata 扩展**。全目标域 strata 过 → `V55_QUALIFICATION_PLAN_READY`，否则 `V55_DATA_NOT_READY`（分层，含 partial），不过则停留 `DATA_NOT_READY`，不进入 decoder；部分 READY strata 仅作 exploration 报告。

5. **预算（预冻结，分层成比例）**：`S` strata × `B` 块/ stratum 时 `L1 S×B + base S×B + stage1 0–S×B + stage2 0–S×B =2SB–4SB 硬帽`（`L2 SB–3SB`），`base` 兼 old 不重复，每块 `L1 1+base 1+stage1≤1+stage2≤1`。`S=3,B=15 → 90-180`；`S=3,B=30 → 180-360`。

6. **门禁与终态（预冻结，分层）**：`per-stratum ≥10/15 (B=15) 或 ≥20/30 (B=30) ∧ coverage-domain ≥35/45 或 ≥70/90 ∧ undetected==0 ∧ rank/nested/verification/记账` 均过 → `V55_INDEPENDENT_TEST_PASS`；否则 `FAIL`；完整性/守卫失败 → `EVIDENCE_INVALID`；数据缺失/partial → `DATA_NOT_READY`（非失败）。`base/stage1` 仅诊断，最终以 `base→Δ16` 主判，`stage1` 报告不取代最终；`Wilson (95%)/rescue_rate/runtime/leakage` 仅报告。

7. **Lifecycle 冻结**：`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`，`implementation_started=false`，任何实现/执行（含数据就绪后的正式 TEST）需独立 plan ACCEPT + 显式 `EXECUTE_AUTH` 绑定到精确实现 SHA（plan 引用 `efd34ef...`）；不启动下一阶段；本轮仅四工件+decoder-free 清单脚本/报告（分层化）。

## Impact Scope

- **新增（本轮，分层修订）**：`openspec/changes/formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation/` 四工件（`proposal.md, design.md, tasks.md, specs/spec.md`）分层化修订 + 可选 `check_v55_data_readiness.py`（decoder-free 分层 G1-G7）+ `data_readiness_report.md`（decoder-free 分层报告，含按 strata G1-G7逐项结果与 `V55_DATA_NOT_READY` 分层缺口分析）。
- **未来实现（本轮不创建，仅预冻结接口）**：`comparison_bench/src/comparison_bench/formal_ir/v55_two_stage_rescue_independent_test.py`（仅组合 V54 冻结方法+分层独立 TEST 注册表+三阶段条件 runner，不新增 decoder）+ `scripts/execute_v55_independent_test.py`；均直接 import `v38_architecture_triage` (Lane C) 与 `v35_algorithm_development::compute_tag_64`，**仅当 `V55_QUALIFICATION_PLAN_READY`（目标域全 READY）后才允许创建**。
- **只读依赖**：`v38_architecture_triage.py` (Lane C 常量/构造器)、`v35_algorithm_development.py` (tag/Field)、`nonbinary_v31.py` (H1)、`load_v25_channel_counts()` (TRAIN prior)、V13 `split_manifest.json` 与已用 `frame_ids` 清单（V48-V54 135-180 区间）、新 session 待登记清单（外部采集目录，按物理条件分层）。
- **不修改**：任何既有 spec/代码/测试/输出、`V38–V54` 输出、`outputs_comparison`/`workspace`/`AGENT_PROJECT_MEMORY.md`/`docs/decision-log.md` 以外；不 import `v50/v51/v52/v53/v54` 模块作生产解码；不创建正式 TEST `run_01` 输出。

## Acceptance Criteria

- [ ] 四工件齐全一致且 lifecycle 为 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`，plan HEAD 绑定 `efd34ef318014e1d0505605062057b042e2180eb`，`implementation_started=false`，`production_outputs_created=false`，明确“不实现不执行不创建 run_01，等待独立评审与数据就绪裁决；严格 decoder-free；分层方案已冻结”。
- [ ] 方法完全冻结可机械校验：`H1-16 rank16`、`L1-APP BP`、`Lane C m2 184/190/192 support/标签/置换` 零改、`H_inc1 8×1024 det1 / H_joint1 192/198/200`、`H_inc2 8×1024 det2 / H_total 200/206/208`、`decoder 90/1.0 poly37`、`leak_base 1064/1094/1104 leak_stage1+40 leak_stage2+80`、`tag L2-only`、`TRAIN-only`、`verification-only`、`Δm=8+8` 唯一且禁止新造第二张外候选；V55 **不测新矩阵/标签/prior/阈值** 已显式冻结。
- [ ] 数据裁决可机械校验：`HOLD 已污染` 结论写入 proposal/design/spec，`V48-V54 已用区间 135-180` 清单可追溯，即使 HOLD 剩余帧未译码也不得改称 TEST；P0 登记新 session 的搜索路径与 `V55_DATA_NOT_READY` 分层非失败语义已冻结。
- [ ] 合格 TEST 要求分层冻结：先列可用独立数据集及其物理条件库存，再按物理条件分 strata（目标域 `D_target={1M,1p5M,2M}`），每主要 stratum 相同块数 `B=15 或 30` 平衡、每 stratum ≥120 frames 建议≥160、每帧256 pairs、每块4连续帧1024 pairs、不入 prior/方法选择、冻结前不看解码结果、主样本 `S×B` 分散非重叠四帧窗口、禁换块已写入 design/spec；数据不足 strata 仅 exploratory 不强行凑 `S×B`。
- [ ] 数据就绪门分层冻结：G1-G7 7项 decoder-free 检查按 strata 扩展（文件可读、provenance完整、三源/strata明确、256/frame 1024/block、与V13及V48-V54完全独立、V25 prior只读、冻结 per-stratum registry 含 `B=15/30` 分散与 `K≥B`），全目标域 strata 过才 `V55_QUALIFICATION_PLAN_READY` 否则 `V55_DATA_NOT_READY`（允许 partial），脚本零 decoder 调用，失败非零退出且按 strata 报告。
- [ ] 预算分层冻结：`S×B` 块时 `L1 SB + base SB + stage1 0–SB + stage2 0–SB =2SB–4SB 硬帽`（`L2 SB–3SB`），`base`兼old不重复，每块 `L1 1+base1+stage1≤1+stage2≤1`；`S=3,B=15→90-180`、`S=3,B=30→180-360`。
- [ ] 预注册门禁分层冻结：`per-stratum ≥10/15 或 20/30 ∧ coverage-domain ≥35/45 或 70/90 ∧ undetected==0 ∧ rank/nested/verification/记账` 均过才 `PASS`，否则 `FAIL`，完整性失败 `EVIDENCE_INVALID`，数据缺失/partial `DATA_NOT_READY`；`base/stage1` 仅诊断，最终以 `base→Δ16` 主判，`stage1` 不取代最终；`Wilson/rescue/runtime/leakage` 仅报告；不足 strata 不计入分母。
- [ ] 本轮产出边界冻结：仅四工件+可选 decoder-free 清单脚本/报告（分层化），**禁 production module/CLI/tests/正式output root/用HOLD冒充/模拟TEST/执行decoder/自授PLAN_ACCEPTED**；claim boundary 写入“算法主线已足够好，blocker是独立TEST数据缺失（分层）”。
- [ ] 可选脚本/报告（如创建）为 decoder-free 分层：仅文件/形态/独立性/registry 检查按 strata，零 `import decoder`，零 `decode_*` 调用，`sys.exit(1)` 于任一目标域 G 门失败，报告含逐 strata PASS/FAIL 与缺口分析；预期重跑仍 `V55_DATA_NOT_READY`（因尚无新数据）。

## Tasks

见 `tasks.md`（Phase A 冻结 V54 方法零改；Phase B 数据裁决与分层新 session 清单搜索；Phase C 分层独立 TEST `S×B` 注册算法冻结；Phase D 分层数据就绪门 G1-G7 decoder-free 校验；Phase E 分层预算/门禁/终态预注册；Phase F 本轮四工件+分层清单脚本/报告交付；Phase G 需 DATA_READY（目标域全 READY）+ EXECUTE_AUTH 的至多 `S×B` 块三阶段条件执行 `2SB–4SB` calls；显式禁止清单）。

## Lifecycle

前代 `formal-ir-v54-two-stage-incremental-l2-rescue` (plan HEAD `bf5dd168...`, branch `formal-ir-mainline`，`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`)；V55 当前 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`（HEAD `efd34ef318014e1d0505605062057b042e2180eb`，branch `formal-ir-mainline`），保持不实现不执行、等待独立复审与数据就绪裁决；分层修订后仍保持 `PLAN_CANDIDATE` 不自授 ACCEPT；实现候选止于 `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`；任何执行需显式用户 `EXECUTE_AUTH` 绑定到精确未来实现 SHA；数据就绪后 `V55_QUALIFICATION_PLAN_READY`（目标域全 READY）方可进入正式 TEST 详细规划与执行，否则 `V55_DATA_NOT_READY`（分层，partial 允许，非失败，需新数据）。本轮仅四工件+decoder-free 分层清单脚本/报告，方法冻结不变，仅数据资格为 blocker。
