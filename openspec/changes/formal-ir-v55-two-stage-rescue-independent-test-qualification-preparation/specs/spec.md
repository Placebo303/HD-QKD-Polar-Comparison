# Delta Specification: formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation

**Cycle**: `V55P0`
**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **仅规划与数据就绪资格准备，不实现新方法，不执行 decoder，不创建 run_01。等待独立复审与数据就绪裁决。**
**Predecessor**: `formal-ir-v54-two-stage-incremental-l2-rescue` (branch `formal-ir-mainline` plan HEAD `bf5dd1686049156540328bac264296b17fee546c`)
**Mechanism id**: `two_stage_rescue_independent_test_qualification_preparation_v55`
**Tag source**: `v35:compute_tag_64(empty,x2)` (`empty=np.empty(0,dtype=np.uint8)`, `hex[:16]` trunc64, `tag_scope=l2_only`)
**HEAD**: `efd34ef318014e1d0505605062057b042e2180eb`（实现冻结时重绑至未来 implementation SHA）
**H1 provenance**: `V31-H1-QC-16×1024 rank16 80b`
**Candidate**: `H_base Lane C ordinal-2 (m2=184/190/192) + H_inc1 det1 8×1024 + H_inc2 det2 8×1024, H_joint1 m2+8, H_total m2+16, GF32 poly37, row≤16 nested rank m2/m2+8/m2+16`（V54 冻结，V55 零新增）
**V54 history**: `V54 PLAN_CANDIDATE` 二阶段 45块 held-out 未执行 decoder，其结论不作 V55 门禁依据；V55 **不测新矩阵/标签/prior/阈值**

## R1. Predecessor binding（完全冻结 V54 二阶段，仅准备独立 TEST 资格）

V55 SHALL 仅基于 V54 完整冻结方法（`H1-16 + syndrome-derived L1-APP + Lane C H_base 184/190/192 + H_inc1 8×1024 det1 + H_inc2 8×1024 det2 + H_joint1/H_total + decoder 90/1.0 poly37 + L2-only tag + TRAIN-only prior + verification-only rescue + 每增量+40`）规划，复用 `n=1024` 与 `m2/leak_base 1064/1094/1104` 定义及 `H_inc1/H_inc2/H_joint1/H_total` 嵌套秩，不改首遍 support/标签/prior/MET图/decoder/H_inc1/H_inc2，不新造任何矩阵，不试 `Δm=4/12/16` 除 `8+8` 外，不测新 prior/标签/阈值。V55 SHALL 冻结独立 TEST 的 90-block 注册算法与 `G1-G7` 数据就绪门 + 预算/门禁/四终态预注册。V55 SHALL NOT 启动正式 TEST 实现/执行，需独立 plan ACCEPT + 显式 `EXECUTE_AUTH`（绑定 `formal-ir-mainline`、未来实现 SHA，plan 引用 `efd34ef...`）且 `G1-G7` 已为 `V55_QUALIFICATION_PLAN_READY`。HOLD 已污染裁决与 `V55_DATA_NOT_READY` 非失败语义 SHALL 写入本 spec。

## R2. Frozen method（完全冻结 V54 二阶段，零改，V55 不测新变量）

冻结方法 SHALL 为：`n=1024, m2=184/190/192, GF32 poly37, Lane C support/label/position_permutations, m1=16, leak_base=5*m2+80+64 →1064/1094/1104, leak_stage1=leak_base+40 →1104/1134/1144, leak_stage2=leak_base+80 →1144/1174/1184`；`H1 16×1024 rank16` 复用 `nonbinary_v31.build_matrix_packet`；`prior TRAIN` via `load_v25_channel_counts()` → `BP_i` → `q_i` → `P_i(U2)`；`decoder 90/1.0` early-stop；`verification = syndrome_ok && tag_ok` L2-only；`exact_full=exact_u1&&exact_l2` oracle。`H_inc1 det1 8×1024` per source（`GF32 poly37`, `col_degree_inc∈{0,1}`, `row≤16`, `无零行`, `rank_joint1==m2+8`）与 `H_inc2 det2 8×1024` per source（同约束, `rank_total==m2+16`）SHALL 保持嵌套 `H_base==H_joint1[:m2]`, `H_base==H_total[:m2] && H_joint1==H_total[:m2+8]`, `independence 8+8`。SHALL NOT 改 V54 任一部件；**SHALL NOT 测新矩阵/标签/prior/阈值/decoder参数**，违者 `EVIDENCE_INVALID`。

## R3. HOLD adjudication（当前定性，不可逆）

V13 `split_manifest 60/20/20` 的 HOLD (`H=400/554/729, base=1600/2213/2916`) SHALL 被裁决为**已污染**：已被 `V48 45 + V50 15 + V51 15 + V52 15 + V53 45 + V54 45 =180块` 开发使用（已用 `frame_ids` 540-720 帧可追溯），**即使 HOLD 仍有剩余窗口 `K2≈135/260/461` 未译码，也不得改称为独立 TEST**。V55 SHALL 登记已用区间清单 per source 并机械校验零重叠；**SHALL NOT** 将 VAL/HOLD 重新标记为 TEST，**SHALL NOT** 因剩余帧未译码而放宽独立性要求。P0 SHALL 搜索/登记另一独立采集 session（与 `2026-01-21` V13 不同日期），若无则终态 `V55_DATA_NOT_READY`（非失败，需新数据），**不得创建 production runner/tests/正式 output root，不得用 HOLD 冒充，不得模拟 TEST 数据**。

## R4. Qualified independent TEST requirements（建议，预冻结）

合格独立 TEST SHALL 满足：
- (a) 1M/1p5M/2M 各一独立 session，日期≠`2026-01-21`，每源 **≥120 frames（建议≥160）**，每帧 **256 pairs**，每块 **4 连续帧 =1024 pairs (`BLOCK_LENGTH=1024`)**，`sampling_mode=deterministic_four_consecutive_frames_independent_test_v55`。
- (b) 新 session **不入 prior 训练**（V25 `channel_counts.npz` 仍 TRAIN-only）、**不入方法选择**、**冻结前不看解码结果**。
- (c) 主样本 **30 blocks/source ×3 =90 blocks, 360 frames**，于新 session 内枚举 `all_starts=0..F-4` 得 `S2` 按 ordinal 排序 `K=|S2|≥30`，以 `index_j=floor(j*(K-1)/29) j=0..29` 确定性分散选 30/源，两两非重叠 gap≥4 且与 V13 及 V48-V54 零重叠 per source；`K<30` 则 `G7_FAIL`。
- (d) 建议 block IDs `396001-030/396101-130/396201-230` 仅标识，真实以 `frame_ids[4]=[global_offset+start .. global_offset+start+3]` 为准，**禁换块/禁重采样/禁跨源混用**。
V55 本轮 SHALL 仅冻结算法，不执行采样。

## R5. Data readiness gate G1-G7（本轮唯一实测，decoder-free）

V55 数据就绪门 SHALL 为仅 decoder-free 的 7 项检查，**零 decoder 调用**，任一失败 `sys.exit(1)`：

- **G1 文件可读**：新 session `pairs.parquet`/`pairs.csv` 可 open，行数 = frames×256，列合法。
- **G2 provenance 完整**：三源 session_id、采集日期≠2026-01-21、采集参数（延迟±50ps 等）、文件哈希/行数可追溯。
- **G3 三源明确**：1M/1p5M/2M 各一 session，互异且与 V13 三源一一对应。
- **G4 形态**：每帧 256 pairs，每块 4 连续帧 1024 pairs，`BLOCK_LENGTH=1024`。
- **G5 独立性**：新 session 全部帧与 V13 全部帧及 V48-V54 已用 540-720 帧零重叠，per source 机械校验（全局 frame_id/哈希零重叠）。
- **G6 V25 prior 只读**：`channel_counts.npz` 形态校验，不读新 TEST 做训练，`load_v25_channel_counts()` 可 import。
- **G7 冻结 90-block registry**：`K≥30`，`index_j` 分散选 30/源，两两非重叠 gap≥4，与 V13 及 V48-V54 零重叠，可机械校验。

全过 → `V55_QUALIFICATION_PLAN_READY`；任一不过 → `V55_DATA_NOT_READY`（非失败，需新数据），**不过则 SHALL NOT 创建 production runner/tests/正式 output root**。G1-G7 的 decoder-free 检查 SHALL 由 `check_v55_data_readiness.py` 实现。

## R6. Leakage and budget — 三阶段（预冻结）

Tag SHALL 为 `compute_tag_64(empty_uint8,x2)` L2-only。泄漏 SHALL 冻结：`leak_base=5*m2+80+64`；`leak_stage1=leak_base+40`；`leak_stage2=leak_base+80`。每块条件泄漏：`verify_base` 通过则 `leak_base`，否则 `verify_stage1` 通过则 `leak_stage1`，否则 `leak_stage2`（成功与最终失败同）。预算 SHALL 为 `L1 90 + base L2 90 + stage1 0-90 + stage2 0-90 =180-360 硬帽360 (L2 90-270)`，`base` 兼 old 不重复；每块 `L1 1+base 1+stage1≤1+stage2≤1` (L2 1-3)。`per_source_avg[s]=leak_base[s]+40×N_stage1[s]/30+40×N_stage2[s]/30`，`overall_avg=(Σ leak_base+40×N_stage1_total+40×N_stage2_total)/90`。

## R7. Three-pass conditional protocol（预冻结，verification-only，二阶段嵌套）

每块 SHALL 执行：`base = decode(H_base, P(U2), s_base)` → `verify_base`；若通过则停，`leak=leak_base`；否则 `stage1 = decode(H_joint1, P(U2), s_joint1)` → `verify_stage1`；若通过则停，`leak=leak_stage1`；否则 `stage2 = decode(H_total, P(U2), s_total)` → `verify_stage2`，`leak=leak_stage2` 无论成功/失败。`exact_*` oracle 仅统计，触发仅 verification。每块 `L1 1+base1+stage1≤1+stage2≤1`，总 `180-360` 硬帽360。

## R8. Primary gate — 预注册门禁与四终态（含 DATA_NOT_READY）

Gate SHALL 为：
- 若 `G1-G7` 任一不过 → `V55_DATA_NOT_READY`（非失败，需新数据），**不进入 decoder**。
- 否则若完整性/守卫/秩/嵌套/重叠/记账失败 → `V55_EVIDENCE_INVALID` 优先。
- 否则若 `final_exact_full ≥70/90 (77.8%) ∧ 每源≥20/30 (66.7%) ∧ undetected==0 ∧ rank/nested/verification/记账通过` → `V55_INDEPENDENT_TEST_PASS`。
- 否则若完整性通过但未过门禁 → `V55_INDEPENDENT_TEST_FAIL`。

`base/stage1` 仅诊断，**最终以 `base→Δ16` 主判**，`stage1` 报告 SHALL NOT 取代最终；`Wilson 95%`/`rescue_rate`/`runtime`/`leakage` 仅报告不作门禁。`V55_DATA_NOT_READY` SHALL NOT 被描述为失败。

## R9. Reporting promises — SHALL（explicit，三阶段，独立 TEST）

若未来 `V55_QUALIFICATION_PLAN_READY` 并执行正式 TEST，Summary SHALL 显式包含（overall 与 per-source 1M/1p5M/2M）：`base_exact_full_count` 与 `verify_base` 分别、`stage1_exact_full_count` 与 `verify_stage1` 分别、`final_exact_full_count` 与 `verify_final` 分别（门禁仅用 `final` 累计量）、`stage1_rescued/stage2_rescued`、`N_stage1_attempted=count(!verify_base)` 与 `N_stage2_attempted=count(!verify_base&&!verify_stage1)`、`rescue_rate_stage1/stage2`、`per_source` 分层、泄漏三档与 `per_source_avg/overall_avg`、`Wilson 95%`、`total_disclosed_bits` 与 `disclosure_per_final_exact_block`（为0则null）、`joint1_rank/total_rank/nested/independence`、`reclassified 四类/undetected`、`paired base vs stage1 vs final` per block、`iterations/runtime/residual`。`V55_DATA_NOT_READY` 时报告 SHALL 仅含数据清单与缺口分析，不含任何 decoder 结果。

## R10. Outputs — minimal fixed set（本轮仅清单报告，未来执行才有正式输出）

本轮 SHALL 仅产出（decoder-free）：
- `openspec/changes/formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation/check_v55_data_readiness.py`（G1-G7 逐项，零 decoder）
- `openspec/changes/formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation/data_readiness_report.md`（逐项 PASS/FAIL 与缺口分析，含 `V55_DATA_NOT_READY` 缺口与所需新数据规格）

未来 `V55_QUALIFICATION_PLAN_READY` 后授权写出 SHALL 仅为：`v55_records.json/.csv`（90-270 L2行）、`v55_summary.json`、`v55_invalid_notice.json`（失败时）、`v55_data_readiness.json`（G1-G7 逐项），隔离于 `.../v55_two_stage_rescue_independent_test/run_01/`，fail-closed，CSV/JSON 行对等，禁写 NPZ。**本轮 SHALL NOT 创建 `.../v55_*/run_01`。**

## R11. Integrity, guard ordering, seed registry, and execution deviation prevention（预冻结）

Runner SHALL 三层：Tier0 拒绝（默认拒绝、`--execution-authorized --authorized-target-sha` 与 `HEAD==origin/formal-ir-mainline==未来实现SHA`（plan 引用 `efd34ef...`）、`SCOPED dirty` 四文件 `v55模块/v55 CLI/v38/v35`、`G1-G7` 未过即拒 `V55_DATA_NOT_READY`、输出根已存在）、Tier1 预检失败（`G1-G7` 全检 + `H_base rank/support` + `H_inc1/H_inc2 rank/nested/independence/row≤16/col≤1/E≈96/leak`）、Tier2 中途异常保留 raw partial。执行偏差防复发：SHALL NOT 使用 600s 外部 timeout（建议≥3600s或不设）、若返回 `session_id/cell_id` SHALL 只轮询同一进程、SHALL NOT 重启新 session、中断保留 raw partial 不聚合不自动重跑。P0 清单脚本 SHALL 仅执行 Tier1 的 decoder-free 分支（write-free）且零 decoder calls；任一 gate 失败 SHALL `sys.exit(1)`。

## R12. Workload and stop rules（frozen fresh 90, 180-360）

总预算 SHALL 为 `90` 块三阶段条件：`L1 90` 共享 + `base L2 90`+`stage1 L2 ≤90`(条件)+`stage2 L2 ≤90`(条件)= 总 `180-360` 硬帽360 (`L2 90-270`)。P0 轮 SHALL NOT 执行任何 decoder call。`90块独立 TEST 确认规模`，门禁 `70/90 & 20/30 & undetected==0` 不因 V54 结论改阈值。`V55_DATA_NOT_READY` 时 SHALL 停止于资格准备，不进入 `180-360` 执行。

## R13. Records preservation（预冻结，未来执行）

每解码 SHALL 一条记录；`base` 90条，`stage1` 至多90条（条件 `!verify_base`），`stage2` 至多90条（条件 `!verify_after_stage1`）。总 `L2` 记录 `90-270` 条，总调用 `180-360` 硬帽360。Schema 含 `arm∈{base,stage1,stage2}/pass_index/used_inc1/used_inc2/matrix_id∈{base,joint1,total}/h1_matrix_id/frame_ids[4]/held_out_ordinal/sampling_mode/max_iter 90/damping 1.0/errors_initial/final/exact_u1/exact_l2/exact_full/syndrome_ok/tag_ok/tag_scope/reclassified/target_tag/candidate_tag/iterations/bp_posterior_entropy/mean_abs_diff/leak_total/status/runtime`。Prior 仅 `TRAIN`。

## R14. Claim boundary（关键判断）

结果仅支持 `n=1024 m2=184/190/192 Δm=8+8` 上 `H_total=[H_base;H_inc1;H_inc2] 嵌套增量` 在 `90` 独立 TEST 块（每源30，4帧=1024 pairs，`deterministic_four_consecutive_frames_independent_test_v55` 经 `K-1` 分散 `index_j=floor(j*(K-1)/29)` 选择，与 V13 及 V48-V54 零重叠，两两非重叠）在 `180-360` calls 上的有界二阶段 rescue 归因（首遍与二阶段冻结 Lane C 原 support/标签/prior/MET图不改，`90/1.0 poly37, leak_base 1064/1094/1104, leak_stage1+40, leak_stage2+80, per_source_avg/overall_avg`，`G1-G7` 数据就绪前置，门禁 `70/90 & 20/30 & undetected==0` 仅用 `final`），`exact_full` oracle 不经 tag；均非 FER 全集/阈值/SKR/安全/资格外推至多 session 的证据；`90块独立 TEST 确认规模`，通过仍仅独立 TEST 确认；**关键判断：算法主线（V54 二阶段）在 held-out 上已足够好，当前 blocker 是独立 TEST 数据缺失，而非方法需再调参**；`V55_DATA_NOT_READY` 为合法非失败终态，需新采集数据。

## R15. Lifecycle（本轮止于 PLAN_CANDIDATE）

本变更 lifecycle SHALL 保持 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` 直至独立 plan ACCEPT；P0 先产四工件 + `check_v55_data_readiness.py` (G1-G7 decoder-free) + `data_readiness_report.md`（含 `V55_DATA_NOT_READY` 缺口与所需新数据规格），`implementation_started=false`, `production_outputs_created=false`。SHALL NOT 执行 decoder 或创建 `run_01`，SHALL NOT 自授 `PLAN_ACCEPTED`，**SHALL 在推送后停留 `PLAN_CANDIDATE`**。
