# Delta Specification: formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation

**Cycle**: `V55P0`
**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **仅规划与数据就绪资格准备，不实现新方法，不执行 decoder，不创建 run_01。等待独立复审与数据就绪裁决。**
**Predecessor**: `formal-ir-v54-two-stage-incremental-l2-rescue` (branch `formal-ir-mainline` plan HEAD `bf5dd1686049156540328bac264296b17fee546c`)
**Mechanism id**: `two_stage_rescue_independent_test_qualification_preparation_v55_stratified`
**Tag source**: `v35:compute_tag_64(empty,x2)` (`empty=np.empty(0,dtype=np.uint8)`, `hex[:16]` trunc64, `tag_scope=l2_only`)
**HEAD**: `efd34ef318014e1d0505605062057b042e2180eb`（实现冻结时重绑至未来 implementation SHA）
**H1 provenance**: `V31-H1-QC-16×1024 rank16 80b`
**Candidate**: `H_base Lane C ordinal-2 (m2=184/190/192) + H_inc1 det1 8×1024 + H_inc2 det2 8×1024, H_joint1 m2+8, H_total m2+16, GF32 poly37, row≤16 nested rank m2/m2+8/m2+16`（V54 冻结，V55 零新增）
**V54 history**: `V54 PLAN_CANDIDATE` 二阶段 45块 held-out 未执行 decoder，其结论不作 V55 门禁依据；V55 **不测新矩阵/标签/prior/阈值**
**Stratified revision**: 本次修订将固定 `90=3×30` 总注册改为按物理条件分层、每主要 stratum 相同块数 `B=15 或 30` 平衡、`S×B` 比例预算与分层门禁；`D_target={1M,1p5M,2M}` 为资格目标域；不足 strata 仅 exploratory

## R1. Predecessor binding（完全冻结 V54 二阶段，仅准备分层独立 TEST 资格）

V55 SHALL 仅基于 V54 完整冻结方法（`H1-16 + syndrome-derived L1-APP + Lane C H_base 184/190/192 + H_inc1 8×1024 det1 + H_inc2 8×1024 det2 + H_joint1/H_total + decoder 90/1.0 poly37 + L2-only tag + TRAIN-only prior + verification-only rescue + 每增量+40`）规划，复用 `n=1024` 与 `m2/leak_base 1064/1094/1104` 定义及 `H_inc1/H_inc2/H_joint1/H_total` 嵌套秩，不改首遍 support/标签/prior/MET图/decoder/H_inc1/H_inc2，不新造任何矩阵，不试 `Δm=4/12/16` 除 `8+8` 外，不测新 prior/标签/阈值。V55 SHALL 冻结分层独立 TEST 的 `S×B` 注册算法与分层 `G1-G7` 数据就绪门 + 分层预算/门禁/四终态预注册。V55 SHALL NOT 启动正式 TEST 实现/执行，需独立 plan ACCEPT + 显式 `EXECUTE_AUTH`（绑定 `formal-ir-mainline`、未来实现 SHA，plan 引用 `efd34ef...`）且目标域 `G1-G7` 已为 `V55_QUALIFICATION_PLAN_READY`。HOLD 已污染裁决与 `V55_DATA_NOT_READY` 分层非失败语义 SHALL 写入本 spec。

## R2. Frozen method（完全冻结 V54 二阶段，零改，V55 不测新变量）

冻结方法 SHALL 为：`n=1024, m2=184/190/192, GF32 poly37, Lane C support/label/position_permutations, m1=16, leak_base=5*m2+80+64 →1064/1094/1104, leak_stage1=leak_base+40 →1104/1134/1144, leak_stage2=leak_base+80 →1144/1174/1184`；`H1 16×1024 rank16` 复用 `nonbinary_v31.build_matrix_packet`；`prior TRAIN` via `load_v25_channel_counts()` → `BP_i` → `q_i` → `P_i(U2)`；`decoder 90/1.0` early-stop；`verification = syndrome_ok && tag_ok` L2-only；`exact_full=exact_u1&&exact_l2` oracle。`H_inc1 det1 8×1024` per source（`GF32 poly37`, `col_degree_inc∈{0,1}`, `row≤16`, `无零行`, `rank_joint1==m2+8`）与 `H_inc2 det2 8×1024` per source（同约束, `rank_total==m2+16`）SHALL 保持嵌套 `H_base==H_joint1[:m2]`, `H_base==H_total[:m2] && H_joint1==H_total[:m2+8]`, `independence 8+8`。SHALL NOT 改 V54 任一部件；**SHALL NOT 测新矩阵/标签/prior/阈值/decoder参数**，违者 `EVIDENCE_INVALID`。

## R3. HOLD adjudication（当前定性，不可逆）

V13 `split_manifest 60/20/20` 的 HOLD (`H=400/554/729, base=1600/2213/2916`) SHALL 被裁决为**已污染**：已被 `V48 45 + V50 15 + V51 15 + V52 15 + V53 45 + V54 45 =180块` 开发使用（已用 `frame_ids` 540-720 帧可追溯），**即使 HOLD 仍有剩余窗口 `K2≈135/260/461` 未译码，也不得改称为独立 TEST**。V55 SHALL 登记已用区间清单 per source 并机械校验零重叠；**SHALL NOT** 将 VAL/HOLD 重新标记为 TEST，**SHALL NOT** 因剩余帧未译码而放宽独立性要求。P0 SHALL 搜索/登记另一独立采集 session 集合（与 `2026-01-21` V13 不同日期，按物理条件分层形成库存），若无则终态 `V55_DATA_NOT_READY`（分层，非失败，需新数据），**不得创建 production runner/tests/正式 output root，不得用 HOLD 冒充，不得模拟 TEST 数据**。

## R4. Qualified independent TEST requirements（分层，预冻结）

合格独立 TEST SHALL 满足（分层）：
- (a) **库存**：先列 `available_independent_datasets` — 所有可用的其他独立数据集及其物理条件（采集日期/地点/器件/延迟±50ps/功率/率/信道参数/文件哈希），按物理条件分 strata，形成库存表。
- (b) **目标域声明**：`D_target = {1M, 1p5M, 2M}` 三主 stratum 为资格目标域（需在 design 中冻结声明）；超出目标域的新物理条件为 exploratory stratum，不计入门禁。
- (c) 每主 stratum 各一独立 session，日期≠`2026-01-21`，每 stratum **≥120 frames（建议≥160）**，每帧 **256 pairs**，每块 **4 连续帧 =1024 pairs (`BLOCK_LENGTH=1024`)**，`sampling_mode=deterministic_four_consecutive_frames_independent_test_v55_stratified`。
- (d) 新 session **不入 prior 训练**（V25 `channel_counts.npz` 仍 TRAIN-only）、**不入方法选择**、**冻结前不看解码结果**。
- (e) 主样本 **每主 stratum `B=15 或 30` blocks 平衡**，`S=|D_target|` 时共 `S×B` blocks（`S=3→45 或 90`），于新 session 每 stratum 内枚举 `all_starts=0..F-4` 得 `S2` 按 ordinal 排序 `K=|S2|≥B`，以 `index_j=floor(j*(K-1)/(B-1)) j=0..B-1` 确定性分散选 B/ stratum，两两非重叠 gap≥4 且与 V13 及 V48-V54 零重叠 per stratum；`K<B` 则该 stratum `G7_FAIL`，仅 exploratory，不强行凑 `S×B`。
- (f) 建议 block IDs 按 stratum 延续（如 `B=30` 时 `396001-030/396101-130/396201-230`）仅标识，真实以 `frame_ids[4]=[global_offset+start .. global_offset+start+3]` 为准，**禁换块/禁重采样/禁跨源混用**。
V55 本轮 SHALL 仅冻结分层算法，不执行采样；不足 strata 仅 exploratory。

## R5. Data readiness gate G1-G7（本轮唯一实测，decoder-free，分层）

V55 数据就绪门 SHALL 为仅 decoder-free 的 7 项检查**按 strata 扩展**，**零 decoder 调用**，任一目标域 stratum 失败 `sys.exit(1)`：

- **G1 文件可读**：每 stratum 新 session `pairs.parquet`/`pairs.csv` 可 open，行数 = frames×256，列合法（per stratum）。
- **G2 provenance 完整**：各 stratum session_id、采集日期≠2026-01-21、采集参数（延迟±50ps/功率/率/地点/器件）、文件哈希/行数可追溯（per stratum）。
- **G3 各 stratum 明确**：`D_target` 各 stratum 各一 session，互异且与 V13 对应物理条件一一对应；exploratory strata 额外列出（全局+per stratum）。
- **G4 形态**：每 stratum 每帧 256 pairs，每块 4 连续帧 1024 pairs，`BLOCK_LENGTH=1024`（per stratum）。
- **G5 独立性**：新 session 各 stratum 全部帧与 V13 全部帧及 V48-V54 已用 540-720 帧零重叠，per stratum 机械校验（全局 frame_id/哈希零重叠）。
- **G6 V25 prior 只读**：`channel_counts.npz` 形态校验，不读新 TEST 做训练，`load_v25_channel_counts()` 可 import（全局一次）。
- **G7 冻结 per-stratum registry**：每目标域 stratum `K≥B`，`index_j` 分散选 B/ stratum，两两非重叠 gap≥4，与 V13 及 V48-V54 零重叠，可机械校验；`K<B` 则该 stratum `G7_FAIL → DATA_NOT_READY`（partial）。

目标域全 strata 过 → `V55_QUALIFICATION_PLAN_READY`；任一目标域 stratum 不过 → `V55_DATA_NOT_READY`（分层，非失败，需新数据，partial 允许），**不过则 SHALL NOT 创建 production runner/tests/正式 output root**。G1-G7 的分层 decoder-free 检查 SHALL 由 `check_v55_data_readiness.py` 实现（先库存清单，再按 strata 逐项）。

## R6. Leakage and budget — 三阶段（预冻结，分层成比例）

Tag SHALL 为 `compute_tag_64(empty_uint8,x2)` L2-only。泄漏 SHALL 冻结：`leak_base=5*m2+80+64`；`leak_stage1=leak_base+40`；`leak_stage2=leak_base+80`。每块条件泄漏：`verify_base` 通过则 `leak_base`，否则 `verify_stage1` 通过则 `leak_stage1`，否则 `leak_stage2`（成功与最终失败同）。预算 SHALL 为 `L1 S×B + base L2 S×B + stage1 0–S×B + stage2 0–S×B =2SB–4SB 硬帽 (L2 SB–3SB)`，`base` 兼 old 不重复；每块 `L1 1+base 1+stage1≤1+stage2≤1` (L2 1-3)。`per_stratum_avg[s]=leak_base[s]+40×N_stage1[s]/B+40×N_stage2[s]/B`，`coverage_avg=(Σ leak_base+40×N_stage1_total+40×N_stage2_total)/(S×B)`。`S=3,B=15 → 90-180 (L2 45-135)`；`S=3,B=30 → 180-360 (L2 90-270)`。

## R7. Three-pass conditional protocol（预冻结，verification-only，二阶段嵌套，分层）

每块（per stratum, 共 S×B）SHALL 执行：`base = decode(H_base, P(U2), s_base)` → `verify_base`；若通过则停，`leak=leak_base`；否则 `stage1 = decode(H_joint1, P(U2), s_joint1)` → `verify_stage1`；若通过则停，`leak=leak_stage1`；否则 `stage2 = decode(H_total, P(U2), s_total)` → `verify_stage2`，`leak=leak_stage2` 无论成功/失败。`exact_*` oracle 仅统计，触发仅 verification。每块 `L1 1+base1+stage1≤1+stage2≤1`，总 `2SB–4SB` 硬帽。

## R8. Primary gate — 预注册门禁与终态（含分层 DATA_NOT_READY）

Gate SHALL 为（分层）：
- 若任一目标域 stratum `G1-G7` 不过 → `V55_DATA_NOT_READY`（分层，非失败，需新数据，partial 允许），**不进入 decoder**；exploratory strata 的 `G7_FAIL` 仅该 stratum exploratory，不阻塞全局。
- 否则若完整性/守卫/秩/嵌套/重叠/记账失败 → `V55_EVIDENCE_INVALID` 优先。
- 否则若 `per_stratum final_exact_full ≥ (B==30?20:10)/B` 每目标域 stratum 均满足 ∧ `coverage_exact_full ≥ ceil(0.778×S×B)`（`S=3,B=30→70/90`；`S=3,B=15→35/45`） ∧ `undetected==0` 全局 ∧ `rank/nested/verification/记账` 通过 → `V55_INDEPENDENT_TEST_PASS`。
- 否则若完整性通过但未过门禁 → `V55_INDEPENDENT_TEST_FAIL`。

`base/stage1` 仅诊断，**最终以 `base→Δ16` 主判**，`stage1` 报告 SHALL NOT 取代最终；`Wilson 95%`/`rescue_rate`/`runtime`/`leakage` 仅报告不作门禁（按 strata）。`V55_DATA_NOT_READY` SHALL NOT 被描述为失败；不足 strata 不计入门禁分母，仅 exploratory。

## R9. Reporting promises — SHALL（explicit，三阶段，分层独立 TEST）

若未来目标域 `V55_QUALIFICATION_PLAN_READY` 并执行正式 TEST，Summary SHALL 按 strata 显式包含（per stratum 与 coverage-domain `S×B`）：`base_exact_full_count` 与 `verify_base` 分别、`stage1_exact_full_count` 与 `verify_stage1` 分别、`final_exact_full_count` 与 `verify_final` 分别（门禁仅用 `final` 的 per-stratum 与 coverage 累计量）、`stage1_rescued/stage2_rescued`、`N_stage1_attempted=count(!verify_base)` 与 `N_stage2_attempted=count(!verify_base&&!verify_stage1)`、`rescue_rate_stage1/stage2` per stratum、`per_stratum` 分层、泄漏三档与 `per_stratum_avg/coverage_avg`、`Wilson 95%` per stratum & coverage、`total_disclosed_bits` 与 `disclosure_per_final_exact_block`（为0则null）、`joint1_rank/total_rank/nested/independence`、`reclassified 四类/undetected`（全局）、`paired base vs stage1 vs final` per block、`iterations/runtime/residual`。Exploratory strata SHALL 单独章节，不计入门禁。`V55_DATA_NOT_READY`（含 partial）时报告 SHALL 仅含分层数据清单与缺口分析，不含任何 decoder 结果。

## R10. Outputs — minimal fixed set（本轮仅分层清单报告，未来执行才有正式输出）

本轮 SHALL 仅产出（decoder-free，分层）：
- `openspec/changes/formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation/check_v55_data_readiness.py`（分层 G1-G7 逐 stratum，零 decoder，先库存清单）
- `openspec/changes/formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation/data_readiness_report.md`（逐 stratum PASS/FAIL 与分层缺口分析，含 `D_target` 覆盖声明与所需新数据规格按 strata）

未来目标域 `V55_QUALIFICATION_PLAN_READY` 后授权写出 SHALL 仅为：`v55_records.json/.csv`（`SB-3SB` L2行）、`v55_summary.json`（分层）、`v55_invalid_notice.json`（失败时）、`v55_data_readiness.json`（分层 `G1-G7` 逐 stratum），隔离于 `.../v55_two_stage_rescue_independent_test/run_01/`，fail-closed，CSV/JSON 行对等，禁写 NPZ。**本轮 SHALL NOT 创建 `.../v55_*/run_01`。**

## R11. Integrity, guard ordering, seed registry, and execution deviation prevention（预冻结，分层）

Runner SHALL 三层：Tier0 拒绝（默认拒绝、`--execution-authorized --authorized-target-sha` 与 `HEAD==origin/formal-ir-mainline==未来实现SHA`（plan 引用 `efd34ef...`）、`SCOPED dirty` 四文件 `v55模块/v55 CLI/v38/v35`、目标域分层 `G1-G7` 未过即拒 `V55_DATA_NOT_READY`（partial 按 strata）、输出根已存在）、Tier1 预检失败（分层 `G1-G7` 全检 + `H_base rank/support` + `H_inc1/H_inc2 rank/nested/independence/row≤16/col≤1/E≈96/leak` per stratum）、Tier2 中途异常保留 raw partial。执行偏差防复发：SHALL NOT 使用 600s 外部 timeout（建议≥3600s或不设）、若返回 `session_id/cell_id` SHALL 只轮询同一进程、SHALL NOT 重启新 session、中断保留 raw partial 不聚合不自动重跑。P0 清单脚本 SHALL 仅执行 Tier1 的 decoder-free 分层分支（write-free）且零 decoder calls；任一目标域 gate 失败 SHALL `sys.exit(1)` 按 strata 报告。

## R12. Workload and stop rules（frozen fresh `S×B`, `2SB-4SB`，分层）

总预算 SHALL 为 `S×B` 块三阶段条件：`L1 S×B` 共享 + `base L2 S×B`+`stage1 L2 ≤S×B`(条件)+`stage2 L2 ≤S×B`(条件)= 总 `2SB-4SB` 硬帽 (`L2 SB-3SB`)。`S=3,B=30 → 180-360 硬帽360`；`S=3,B=15 → 90-180 硬帽180`。P0 轮 SHALL NOT 执行任何 decoder call。分层独立 TEST 确认规模，门禁 `per-stratum 10/15或20/30 ∧ coverage 35/45或70/90 ∧ undetected==0` 不因 V54 结论改阈值。`V55_DATA_NOT_READY`（含 partial）时 SHALL 停止于资格准备，不进入 `2SB-4SB` 执行。

## R13. Records preservation（预冻结，未来执行，分层）

每解码 SHALL 一条记录；`base` `S×B`条，`stage1` 至多`S×B`条（条件 `!verify_base`），`stage2` 至多`S×B`条（条件 `!verify_after_stage1`）。总 `L2` 记录 `SB-3SB` 条，总调用 `2SB-4SB` 硬帽。Schema 含 `stratum/source/arm∈{base,stage1,stage2}/pass_index/used_inc1/used_inc2/matrix_id∈{base,joint1,total}/h1_matrix_id/frame_ids[4]/held_out_ordinal/sampling_mode(max SB)/max_iter 90/damping 1.0/errors_initial/final/exact_u1/exact_l2/exact_full/syndrome_ok/tag_ok/tag_scope/reclassified/target_tag/candidate_tag/iterations/bp_posterior_entropy/mean_abs_diff/leak_total/status/runtime`。Prior 仅 `TRAIN`。

## R14. Claim boundary（关键判断，分层）

结果仅支持 `n=1024 m2=184/190/192 Δm=8+8` 上 `H_total=[H_base;H_inc1;H_inc2] 嵌套增量` 在分层 `S×B` 独立 TEST 块（每目标域 stratum `B=15 或 30` 平衡，4帧=1024 pairs，`deterministic_four_consecutive_frames_independent_test_v55_stratified` 经 `K-1` 分散 `index_j=floor(j*(K-1)/(B-1))` 选择，与 V13 及 V48-V54 零重叠，两两非重叠）在 `2SB-4SB` calls 上的有界二阶段 rescue 归因（首遍与二阶段冻结 Lane C 原 support/标签/prior/MET图不改，`90/1.0 poly37, leak_base 1064/1094/1104, leak_stage1+40, leak_stage2+80, per_stratum_avg/coverage_avg`，分层 `G1-G7` 数据就绪前置，门禁 `per-stratum 10/15或20/30 ∧ coverage 35/45或70/90 ∧ undetected==0` 仅用 `final` 的分层累积），`exact_full` oracle 不经 tag；均非 FER 全集/阈值/SKR/安全/资格外推至多 session 的证据；分层独立 TEST 确认规模，通过仍仅分层独立 TEST 在目标域上的确认；**关键判断：算法主线（V54 二阶段）在 held-out 上已足够好，当前 blocker 是独立 TEST 数据缺失（分层），而非方法需再调参**；`V55_DATA_NOT_READY`（含 partial）为合法非失败终态，需新采集数据。

## R15. Lifecycle（本轮止于 PLAN_CANDIDATE，分层）

本变更 lifecycle SHALL 保持 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` 直至独立 plan ACCEPT；P0 先产四工件分层修订 + `check_v55_data_readiness.py` (分层 G1-G7 decoder-free，含库存清单) + `data_readiness_report.md`（分层，含 `V55_DATA_NOT_READY` 分层缺口与所需新数据规格按 strata），`implementation_started=false`, `production_outputs_created=false`。SHALL NOT 执行 decoder 或创建 `run_01`，SHALL NOT 自授 `PLAN_ACCEPTED`，**SHALL 在推送后停留 `PLAN_CANDIDATE`**。
